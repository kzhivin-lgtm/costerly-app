from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_PAGE_IMAGE_DPI = 96
DEFAULT_PAGE_IMAGE_QUALITY = 75
DEFAULT_PAGE_IMAGE_WORKERS = 4
DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES = 30_000_000
ANTHROPIC_MAX_IMAGES_PER_REQUEST = 100
ANTHROPIC_MULTI_IMAGE_MAX_DIMENSION = 2_000
REGISTRY_MAX_IMAGES = 100
REGISTRY_REGIONS_PER_PAGE = 3
REGISTRY_CONTENT_AWARE_MAX_EXTRA_REGIONS = 15


def estimated_inline_pdf_bytes(file_bytes: bytes) -> int:
    return 4 * ((len(file_bytes) + 2) // 3)


def inline_pdf_request_max_bytes() -> int:
    raw_value = os.getenv(
        "DETECTION_INLINE_PDF_REQUEST_MAX_BYTES",
        str(DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES),
    )
    try:
        return max(1, int(raw_value))
    except (TypeError, ValueError):
        return DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES


def should_use_detection_page_images(*, file_name: str, file_bytes: bytes) -> bool:
    return (
        Path(file_name).suffix.lower() == ".pdf"
        and estimated_inline_pdf_bytes(file_bytes) >= inline_pdf_request_max_bytes()
    )


def _natural_page_number(path: Path) -> int:
    match = re.search(r"-(\d+)$", path.stem)
    if not match:
        raise RuntimeError(f"Unexpected rendered page name: {path.name}")
    return int(match.group(1))


def _render_with_pdftoppm(file_bytes: bytes, *, dpi: int) -> list[bytes]:
    executable = shutil.which("pdftoppm")
    if not executable:
        raise ModuleNotFoundError("pdftoppm is unavailable")
    with tempfile.TemporaryDirectory(prefix="costerly-detection-jpeg-") as directory:
        temp_dir = Path(directory)
        source_path = temp_dir / "source.pdf"
        output_prefix = temp_dir / "page"
        source_path.write_bytes(file_bytes)
        subprocess.run(
            [executable, "-r", str(dpi), "-jpeg", str(source_path), str(output_prefix)],
            check=True,
            capture_output=True,
        )
        paths = sorted(temp_dir.glob("page-*.jpg"), key=_natural_page_number)
        return [path.read_bytes() for path in paths]


def _render_with_pymupdf(
    file_bytes: bytes,
    *,
    dpi: int,
    quality: int,
    workers: int,
) -> list[bytes]:
    import pymupdf

    document = pymupdf.open(stream=file_bytes, filetype="pdf")
    try:
        page_count = len(document)
    finally:
        document.close()

    def render_page(page_index: int) -> bytes:
        worker_document = pymupdf.open(stream=file_bytes, filetype="pdf")
        try:
            page = worker_document.load_page(page_index)
            longest_points = max(float(page.rect.width), float(page.rect.height))
            target_dpi = max(
                1,
                int(min(float(dpi), ANTHROPIC_MULTI_IMAGE_MAX_DIMENSION * 72.0 / longest_points)),
            )
            pixmap = page.get_pixmap(dpi=target_dpi, alpha=False)
            try:
                return pixmap.tobytes("jpg", jpg_quality=quality)
            except TypeError:
                return pixmap.tobytes("jpg")
        finally:
            worker_document.close()

    with ThreadPoolExecutor(max_workers=max(1, min(workers, page_count))) as executor:
        return list(executor.map(render_page, range(page_count)))


def render_detection_pdf_pages(
    file_bytes: bytes,
    *,
    dpi: int = DEFAULT_PAGE_IMAGE_DPI,
    quality: int = DEFAULT_PAGE_IMAGE_QUALITY,
    workers: int = DEFAULT_PAGE_IMAGE_WORKERS,
) -> tuple[list[bytes], dict[str, Any]]:
    if not file_bytes:
        raise ValueError("Cannot render an empty PDF")
    started = time.perf_counter()
    renderer = "pymupdf"
    try:
        pages = _render_with_pymupdf(
            file_bytes,
            dpi=dpi,
            quality=quality,
            workers=workers,
        )
    except (ImportError, ModuleNotFoundError):
        renderer = "pdftoppm"
        pages = _render_with_pdftoppm(file_bytes, dpi=dpi)
    if not pages:
        raise RuntimeError("PDF contains no renderable pages")
    if len(pages) > ANTHROPIC_MAX_IMAGES_PER_REQUEST:
        raise RuntimeError("PDFs over 100 pages require a separate large-package route")
    return pages, {
        "route": "jpeg_pages_96dpi",
        "renderer": renderer,
        "dpi": dpi,
        "quality": quality,
        "page_count": len(pages),
        "source_bytes": len(file_bytes),
        "estimated_inline_pdf_bytes": estimated_inline_pdf_bytes(file_bytes),
        "rendered_bytes_total": sum(len(page) for page in pages),
        "render_seconds": round(time.perf_counter() - started, 6),
    }


def build_detection_registry_regions(
    page_images: list[bytes],
    *,
    max_images: int = REGISTRY_MAX_IMAGES,
) -> list[dict[str, Any]]:
    """Add stable large visual zones so Haiku can inspect dense drawing sheets."""
    if not page_images:
        return []
    from PIL import Image
    from io import BytesIO

    regions: list[dict[str, Any]] = []
    available_regions = max(0, max_images - len(page_images))
    pages_with_regions = available_regions // REGISTRY_REGIONS_PER_PAGE
    for page_number, page_bytes in enumerate(page_images[:pages_with_regions], start=1):
        with Image.open(BytesIO(page_bytes)) as image:
            width, height = image.size
            crops = (
                ("upper_left", (0, 0, width // 2, height // 2)),
                ("upper_right", (width // 2, 0, width, height // 2)),
                ("lower", (0, height // 2, width, height)),
            )
            for region, box in crops:
                output = BytesIO()
                image.crop(box).save(output, format="JPEG", quality=85)
                regions.append({
                    "page_number": page_number,
                    "region": region,
                    "bytes": output.getvalue(),
                })
    extra_capacity = min(
        max(0, max_images - len(page_images) - len(regions)),
        REGISTRY_CONTENT_AWARE_MAX_EXTRA_REGIONS,
    )
    for page_number, page_bytes in enumerate(page_images, start=1):
        if extra_capacity < 5:
            break
        focused = _build_contextual_drawing_regions(
            page_bytes, page_number=page_number, max_regions=extra_capacity
        )
        regions.extend(focused)
        extra_capacity -= len(focused)
    return regions


def _build_contextual_drawing_regions(
    page_bytes: bytes,
    *,
    page_number: int,
    max_regions: int,
) -> list[dict[str, Any]]:
    """Add a title-block context crop and three drawing islands as one package.

    This is only visual input shaping. It never declares object boundaries. A
    title block is included with every focused package, so isolated geometry
    never loses the source sheet's author-assigned code.
    """
    if max_regions < 5:
        return []
    from io import BytesIO
    from PIL import Image

    with Image.open(BytesIO(page_bytes)) as source:
        image = source.convert("RGB")
    width, height = image.size
    if width < 400 or height < 400:
        return []
    ink = np.asarray(image.convert("L")) < 235
    ink = ink.copy()
    ink[:, np.mean(ink, axis=0) > 0.75] = False
    ink[np.mean(ink, axis=1) > 0.75, :] = False
    margin_x = max(8, int(width * 0.015))
    margin_y = max(8, int(height * 0.015))
    side_width = max(margin_x + 1, int(width * 0.24))
    rows = slice(margin_y, height - margin_y)

    def side_score(left: bool) -> float:
        side = (
            ink[rows, margin_x:side_width]
            if left else ink[rows, width - side_width:width - margin_x]
        )
        return float(np.mean(np.mean(side, axis=1) > 0.025))

    left_score, right_score = side_score(True), side_score(False)
    if left_score >= 0.45 and left_score >= right_score * 1.10:
        title_left, field_left, field_right = True, side_width, width - margin_x
    elif right_score >= 0.45 and right_score >= left_score * 1.10:
        title_left, field_left, field_right = False, margin_x, width - side_width
    else:
        return []
    if field_right - field_left < width * 0.45:
        return []

    row_density = ink[margin_y:height - margin_y, field_left:field_right].mean(axis=1)
    active = np.convolve(row_density, np.ones(11) / 11, mode="same") > 0.006
    bands: list[tuple[int, int]] = []
    start: int | None = None
    for offset, is_active in enumerate(active):
        if is_active and start is None:
            start = offset + margin_y
        elif not is_active and start is not None:
            end = offset - 1 + margin_y
            if end - start >= max(18, int(height * 0.012)):
                bands.append((start, end))
            start = None
    if start is not None:
        bands.append((start, height - margin_y - 1))
    merged: list[tuple[int, int]] = []
    for top, bottom in bands:
        if merged and top - merged[-1][1] <= int(height * 0.035):
            merged[-1] = (merged[-1][0], bottom)
        else:
            merged.append((top, bottom))
    if len(merged) < 3:
        return []
    selected = sorted(merged, key=lambda band: band[1] - band[0], reverse=True)[:3]
    selected.sort()
    if selected[-1][1] - selected[0][0] < int(height * 0.40):
        return []

    padding_x, padding_y = max(12, int(width * 0.025)), max(12, int(height * 0.02))
    output: list[dict[str, Any]] = []

    def append_crop(label: str, box: tuple[int, int, int, int]) -> None:
        encoded = BytesIO()
        image.crop(box).save(encoded, format="JPEG", quality=88)
        output.append({"page_number": page_number, "region": label, "bytes": encoded.getvalue()})

    title_box = (
        (margin_x, margin_y, side_width, height - margin_y)
        if title_left else (width - side_width, margin_y, width - margin_x, height - margin_y)
    )
    append_crop("sheet_context", title_box)
    field_top = max(margin_y, selected[0][0] - padding_y)
    field_bottom = min(height - margin_y, selected[-1][1] + padding_y)
    append_crop("drawing_field", (field_left, field_top, field_right, field_bottom))
    for index, (top, bottom) in enumerate(selected, start=1):
        band = ink[top:bottom + 1, field_left:field_right]
        columns = np.flatnonzero(np.mean(band, axis=0) > 0.004)
        if not len(columns):
            return []
        left = max(field_left, field_left + int(columns[0]) - padding_x)
        right = min(field_right, field_left + int(columns[-1]) + padding_x + 1)
        append_crop(
            f"drawing_island_{index}",
            (left, max(margin_y, top - padding_y), right, min(height - margin_y, bottom + padding_y)),
        )
    return output
