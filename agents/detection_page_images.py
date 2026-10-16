from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from io import BytesIO
from typing import Any


DEFAULT_PAGE_IMAGE_DPI = 96
DEFAULT_PAGE_IMAGE_QUALITY = 75
DEFAULT_PAGE_IMAGE_WORKERS = 4
DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES = 30_000_000
ANTHROPIC_MAX_IMAGES_PER_REQUEST = 100
ANTHROPIC_MULTI_IMAGE_MAX_DIMENSION = 2_000
REGISTRY_MAX_IMAGES = 100
REGISTRY_REGIONS_PER_PAGE = 3
ASSEMBLY_CORRESPONDENCE_MAX_IMAGES = 100
ASSEMBLY_CANDIDATE_GRID_SIZE = (280, 198)
ASSEMBLY_CANDIDATE_INK_THRESHOLD = 220
ASSEMBLY_CANDIDATE_MIN_GRID_VALUE = 4
ASSEMBLY_CANDIDATE_MIN_CELLS = 120
ASSEMBLY_CANDIDATE_MIN_WIDTH = 0.20
ASSEMBLY_CANDIDATE_MIN_HEIGHT = 0.16
ASSEMBLY_CANDIDATE_MIN_AREA = 0.04
# Exclude sheet margins and the conventional lower title-block strip. These
# are attention targets, never Detection object boundaries.
ASSEMBLY_CANDIDATE_PAGE_BOUNDS = (0.05, 0.08, 0.95, 0.80)


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


def build_detection_spatial_candidates(page_images: list[bytes]) -> list[dict[str, Any]]:
    """Find large disconnected drawing clusters without assigning semantics."""
    if not page_images:
        return []
    from PIL import Image, ImageFilter

    grid_width, grid_height = ASSEMBLY_CANDIDATE_GRID_SIZE
    page_left, page_top, page_right, page_bottom = ASSEMBLY_CANDIDATE_PAGE_BOUNDS
    candidates: list[dict[str, Any]] = []
    for page_number, page_bytes in enumerate(page_images, start=1):
        with Image.open(BytesIO(page_bytes)) as image:
            grayscale = image.convert("L")
            source_width, source_height = grayscale.size
            crop_left = int(source_width * page_left)
            crop_top = int(source_height * page_top)
            crop_right = int(source_width * page_right)
            crop_bottom = int(source_height * page_bottom)
            cropped = grayscale.crop((crop_left, crop_top, crop_right, crop_bottom))
            ink = cropped.point(
                lambda value: 255 if value < ASSEMBLY_CANDIDATE_INK_THRESHOLD else 0
            )
            coarse = (
                ink.resize((grid_width, grid_height), Image.Resampling.BOX)
                .point(lambda value: 255 if value >= ASSEMBLY_CANDIDATE_MIN_GRID_VALUE else 0)
                .filter(ImageFilter.MaxFilter(3))
            )

        pixels = coarse.tobytes()
        visited = bytearray(len(pixels))
        component_index = 0
        for start_index, value in enumerate(pixels):
            if not value or visited[start_index]:
                continue
            queue = [start_index]
            visited[start_index] = 1
            x_values: list[int] = []
            y_values: list[int] = []
            for current_index in queue:
                x = current_index % grid_width
                y = current_index // grid_width
                x_values.append(x)
                y_values.append(y)
                for next_x, next_y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not (0 <= next_x < grid_width and 0 <= next_y < grid_height):
                        continue
                    next_index = next_y * grid_width + next_x
                    if pixels[next_index] and not visited[next_index]:
                        visited[next_index] = 1
                        queue.append(next_index)

            cell_count = len(queue)
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            width = (max_x - min_x + 1) / grid_width
            height = (max_y - min_y + 1) / grid_height
            if (
                cell_count < ASSEMBLY_CANDIDATE_MIN_CELLS
                or width < ASSEMBLY_CANDIDATE_MIN_WIDTH
                or height < ASSEMBLY_CANDIDATE_MIN_HEIGHT
                or width * height < ASSEMBLY_CANDIDATE_MIN_AREA
            ):
                continue
            component_index += 1
            candidates.append({
                "page_number": page_number,
                "bbox": {
                    "left": round((crop_left + min_x / grid_width * (crop_right - crop_left)) / source_width, 4),
                    "top": round((crop_top + min_y / grid_height * (crop_bottom - crop_top)) / source_height, 4),
                    "right": round((crop_left + (max_x + 1) / grid_width * (crop_right - crop_left)) / source_width, 4),
                    "bottom": round((crop_top + (max_y + 1) / grid_height * (crop_bottom - crop_top)) / source_height, 4),
                },
                "ink_cell_count": cell_count,
            })
    return candidates


def build_detection_assembly_correspondence_regions(
    page_images: list[bytes],
    *,
    max_images: int = ASSEMBLY_CORRESPONDENCE_MAX_IMAGES,
) -> list[dict[str, Any]]:
    """Return all usable isolated representations for one correspondence pass.

    A page with one drawing cluster cannot distinguish a split boundary. More
    than the provider's image ceiling is intentionally left on the accepted
    path rather than truncating an incomplete physical partition.
    """
    candidates = build_detection_spatial_candidates(page_images)
    if len(candidates) < 2 or len(candidates) > max_images:
        return []
    from PIL import Image

    regions: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        page_number = candidate["page_number"]
        bbox = candidate["bbox"]
        with Image.open(BytesIO(page_images[page_number - 1])) as image:
            width, height = image.size
            padding = 0.025
            left = max(0.0, float(bbox["left"]) - padding)
            top = max(0.0, float(bbox["top"]) - padding)
            right = min(1.0, float(bbox["right"]) + padding)
            bottom = min(1.0, float(bbox["bottom"]) + padding)
            crop = image.crop((
                int(width * left), int(height * top),
                max(int(width * right), int(width * left) + 1),
                max(int(height * bottom), int(height * top) + 1),
            ))
            output = BytesIO()
            crop.save(output, format="JPEG", quality=85)
        regions.append({
            "representation_id": f"representation-{index:03d}",
            "page_number": page_number,
            "bbox": bbox,
            "bytes": output.getvalue(),
        })
    return regions


def build_detection_registry_regions(
    page_images: list[bytes],
    *,
    max_images: int = REGISTRY_MAX_IMAGES,
) -> list[dict[str, Any]]:
    """Add stable large visual zones so Haiku can inspect dense drawing sheets."""
    if not page_images:
        return []
    from PIL import Image

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
    return regions
