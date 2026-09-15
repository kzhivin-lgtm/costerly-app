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


DEFAULT_PAGE_IMAGE_DPI = 96
DEFAULT_PAGE_IMAGE_QUALITY = 75
DEFAULT_PAGE_IMAGE_WORKERS = 4
DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES = 30_000_000
ANTHROPIC_MAX_IMAGES_PER_REQUEST = 100
ANTHROPIC_MULTI_IMAGE_MAX_DIMENSION = 2_000


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
