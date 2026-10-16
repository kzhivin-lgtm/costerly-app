from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import Any


DEFAULT_PAGE_IMAGE_DPI = 96
DEFAULT_PAGE_IMAGE_QUALITY = 75
DEFAULT_PAGE_IMAGE_WORKERS = 4
DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES = 30_000_000
ANTHROPIC_MAX_IMAGES_PER_REQUEST = 100
ANTHROPIC_MULTI_IMAGE_MAX_DIMENSION = 2_000
REGISTRY_MAX_IMAGES = 100
REGISTRY_REGIONS_PER_PAGE = 3
SPATIAL_CANDIDATE_GRID_SIZE = (280, 198)
SPATIAL_CANDIDATE_INK_THRESHOLD = 220
SPATIAL_CANDIDATE_MIN_GRID_VALUE = 4
SPATIAL_CANDIDATE_MIN_CELLS = 120
SPATIAL_CANDIDATE_MIN_WIDTH = 0.20
SPATIAL_CANDIDATE_MIN_HEIGHT = 0.16
SPATIAL_CANDIDATE_MIN_AREA = 0.04
# Exclude sheet margins and the usual lower title-block strip.  This is only
# an attention map for drawing content, never an object segmentation result.
SPATIAL_CANDIDATE_PAGE_BOUNDS = (0.05, 0.08, 0.95, 0.80)


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
    """Locate large disconnected drawing clusters without assigning meaning.

    The result is deliberately limited to pixel geometry.  It does not know
    whether a cluster is a product, a component, another projection, or a
    drawing detail.  Its purpose is to give the visual model an explicit crop
    it must account for before it locks commercial-object boundaries.
    """
    if not page_images:
        return []
    from PIL import Image, ImageFilter

    grid_width, grid_height = SPATIAL_CANDIDATE_GRID_SIZE
    page_left, page_top, page_right, page_bottom = SPATIAL_CANDIDATE_PAGE_BOUNDS
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
                lambda value: 255 if value < SPATIAL_CANDIDATE_INK_THRESHOLD else 0
            )
            coarse = (
                ink.resize((grid_width, grid_height), Image.Resampling.BOX)
                .point(lambda value: 255 if value >= SPATIAL_CANDIDATE_MIN_GRID_VALUE else 0)
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
                for next_x, next_y in (
                    (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                ):
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
                cell_count < SPATIAL_CANDIDATE_MIN_CELLS
                or width < SPATIAL_CANDIDATE_MIN_WIDTH
                or height < SPATIAL_CANDIDATE_MIN_HEIGHT
                or width * height < SPATIAL_CANDIDATE_MIN_AREA
            ):
                continue
            component_index += 1
            candidates.append({
                "island_id": f"island-{page_number:03d}-{component_index:02d}",
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


def _crop_box_from_normalized_bbox(
    *,
    width: int,
    height: int,
    bbox: dict[str, float],
    padding: float = 0.025,
) -> tuple[int, int, int, int]:
    left = max(0.0, float(bbox["left"]) - padding)
    top = max(0.0, float(bbox["top"]) - padding)
    right = min(1.0, float(bbox["right"]) + padding)
    bottom = min(1.0, float(bbox["bottom"]) + padding)
    return (
        int(width * left), int(height * top),
        max(int(width * right), int(width * left) + 1),
        max(int(height * bottom), int(height * top) + 1),
    )


def _append_region(
    regions: list[dict[str, Any]],
    *,
    page_number: int,
    region: str,
    image: Any,
    box: tuple[int, int, int, int],
    island: dict[str, Any] | None = None,
) -> None:
    output = BytesIO()
    image.crop(box).save(output, format="JPEG", quality=85)
    payload: dict[str, Any] = {
        "page_number": page_number,
        "region": region,
        "bytes": output.getvalue(),
    }
    if island is not None:
        payload["island_id"] = island["island_id"]
        payload["bbox"] = island["bbox"]
    regions.append(payload)


def build_detection_registry_regions(
    page_images: list[bytes],
    *,
    max_images: int = REGISTRY_MAX_IMAGES,
) -> list[dict[str, Any]]:
    """Add attention crops without increasing the image-package ceiling.

    Large disconnected clusters on a page are passed as labelled island crops
    before generic quadrants.  A crop is an attention target, not a product
    decision.  The usual lower-right title block is also exposed separately so
    project or drawing metadata is not mistaken for a local object anchor.
    """
    if not page_images:
        return []
    from PIL import Image

    available_regions = max(0, max_images - len(page_images))
    if not available_regions:
        return []

    candidates_by_page: dict[int, list[dict[str, Any]]] = {}
    for candidate in build_detection_spatial_candidates(page_images):
        candidates_by_page.setdefault(candidate["page_number"], []).append(candidate)

    # A lone large cluster adds little boundary information.  Preserve only
    # pages with competing large clusters, and keep each page's set intact.
    island_sets = [
        candidates_by_page[page_number]
        for page_number in sorted(candidates_by_page)
        if len(candidates_by_page[page_number]) >= 2
    ]
    selected_islands: list[dict[str, Any]] = []
    for island_set in island_sets:
        if len(selected_islands) + len(island_set) > available_regions:
            break
        selected_islands.extend(island_set)

    regions: list[dict[str, Any]] = []
    selected_by_page: dict[int, list[dict[str, Any]]] = {}
    for island in selected_islands:
        selected_by_page.setdefault(island["page_number"], []).append(island)

    for page_number, page_bytes in enumerate(page_images, start=1):
        if page_number not in selected_by_page:
            continue
        with Image.open(BytesIO(page_bytes)) as image:
            width, height = image.size
            for island in selected_by_page[page_number]:
                _append_region(
                    regions,
                    page_number=page_number,
                    region=f"visual_island:{island['island_id']}",
                    image=image,
                    box=_crop_box_from_normalized_bbox(
                        width=width, height=height, bbox=island["bbox"],
                    ),
                    island=island,
                )

    # Title blocks often carry project and drawing metadata.  They are not
    # object evidence by default.  Eight pages cover short drawing sets such
    # as Adda while retaining room for islands and normal inspection crops.
    title_block_limit = min(8, len(page_images), available_regions - len(regions))
    for page_number, page_bytes in enumerate(page_images[:title_block_limit], start=1):
        with Image.open(BytesIO(page_bytes)) as image:
            width, height = image.size
            _append_region(
                regions,
                page_number=page_number,
                region="lower_right_title_block",
                image=image,
                box=(int(width * 0.62), int(height * 0.72), width, height),
            )

    remaining = available_regions - len(regions)
    if not remaining:
        return regions
    pages_with_regions = remaining // REGISTRY_REGIONS_PER_PAGE
    for page_number, page_bytes in enumerate(page_images[:pages_with_regions], start=1):
        with Image.open(BytesIO(page_bytes)) as image:
            width, height = image.size
            crops = (
                ("upper_left", (0, 0, width // 2, height // 2)),
                ("upper_right", (width // 2, 0, width, height // 2)),
                ("lower", (0, height // 2, width, height)),
            )
            for region, box in crops:
                if len(regions) >= available_regions:
                    return regions
                _append_region(
                    regions,
                    page_number=page_number,
                    region=region,
                    image=image,
                    box=box,
                )
    return regions
