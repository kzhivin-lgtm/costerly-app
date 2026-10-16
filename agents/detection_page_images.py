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
ASSEMBLY_CORRESPONDENCE_MAX_PAIRWISE_REPRESENTATIONS = 12
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


def _build_detection_spatial_components(page_images: list[bytes]) -> list[dict[str, Any]]:
    """Find large disconnected ink components and retain their exact coarse masks.

    A bounding box is only navigation metadata.  It cannot itself isolate a
    drawing figure because two independent L-shaped figures may have
    overlapping rectangular envelopes.  The mask remains internal until crop
    rendering, where it prevents ink from a neighbouring component leaking
    into that component's representation.
    """
    if not page_images:
        return []
    from PIL import Image, ImageFilter

    grid_width, grid_height = ASSEMBLY_CANDIDATE_GRID_SIZE
    page_left, page_top, page_right, page_bottom = ASSEMBLY_CANDIDATE_PAGE_BOUNDS
    components: list[dict[str, Any]] = []
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
            components.append({
                "page_number": page_number,
                "bbox": {
                    "left": round((crop_left + min_x / grid_width * (crop_right - crop_left)) / source_width, 4),
                    "top": round((crop_top + min_y / grid_height * (crop_bottom - crop_top)) / source_height, 4),
                    "right": round((crop_left + (max_x + 1) / grid_width * (crop_right - crop_left)) / source_width, 4),
                    "bottom": round((crop_top + (max_y + 1) / grid_height * (crop_bottom - crop_top)) / source_height, 4),
                },
                "ink_cell_count": cell_count,
                "grid_cells": tuple(queue),
                "source_size": (source_width, source_height),
                "source_crop": (crop_left, crop_top, crop_right, crop_bottom),
            })
    return components


def build_detection_spatial_candidates(page_images: list[bytes]) -> list[dict[str, Any]]:
    """Find large disconnected drawing clusters without assigning semantics."""
    return [
        {
            "page_number": component["page_number"],
            "bbox": component["bbox"],
            "ink_cell_count": component["ink_cell_count"],
        }
        for component in _build_detection_spatial_components(page_images)
    ]


def _component_source_mask(component: dict[str, Any]):
    """Return a source-sized mask containing only this coarse ink component."""
    from PIL import Image

    source_width, source_height = component["source_size"]
    crop_left, crop_top, crop_right, crop_bottom = component["source_crop"]
    grid_width, grid_height = ASSEMBLY_CANDIDATE_GRID_SIZE
    grid_mask = Image.new("L", (grid_width, grid_height), 0)
    for cell_index in component["grid_cells"]:
        grid_mask.putpixel((cell_index % grid_width, cell_index // grid_width), 255)
    crop_mask = grid_mask.resize(
        (crop_right - crop_left, crop_bottom - crop_top),
        Image.Resampling.NEAREST,
    )
    source_mask = Image.new("L", (source_width, source_height), 0)
    source_mask.paste(crop_mask, (crop_left, crop_top))
    return source_mask


def _masked_component_page_map(
    image,
    components: list[dict[str, Any]],
) -> bytes:
    """Render a title-strip-free map containing only detected figure ink.

    It lets the correspondence model see that figures occupy different places
    on a page, without exposing the full title block or letting nearby source
    ink become part of another figure crop.
    """
    from PIL import Image, ImageDraw

    page_left, page_top, page_right, page_bottom = ASSEMBLY_CANDIDATE_PAGE_BOUNDS
    width, height = image.size
    masked_page = Image.new("RGB", image.size, "white")
    for component in components:
        masked_page.paste(image, mask=_component_source_mask(component))

    draw = ImageDraw.Draw(masked_page)
    for index, component in enumerate(components, start=1):
        bbox = component["bbox"]
        left = int(width * bbox["left"])
        top = int(height * bbox["top"])
        right = int(width * bbox["right"])
        bottom = int(height * bbox["bottom"])
        draw.rectangle((left, top, right, bottom), outline=(192, 0, 0), width=2)
        draw.text(
            (left + 4, top + 4),
            str(component.get("representation_id") or f"figure-{index}"),
            fill=(192, 0, 0),
        )

    output = BytesIO()
    masked_page.crop((
        int(width * page_left),
        int(height * page_top),
        int(width * page_right),
        int(height * page_bottom),
    )).save(output, format="JPEG", quality=85)
    return output.getvalue()


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
    components = _build_detection_spatial_components(page_images)
    if (
        len(components) < 2
        or len(components) > max_images
        or len(components) > ASSEMBLY_CORRESPONDENCE_MAX_PAIRWISE_REPRESENTATIONS
    ):
        return []
    from PIL import Image

    for index, component in enumerate(components, start=1):
        component["representation_id"] = f"representation-{index:03d}"
    regions: list[dict[str, Any]] = []
    components_by_page: dict[int, list[dict[str, Any]]] = {}
    for component in components:
        components_by_page.setdefault(component["page_number"], []).append(component)
    page_maps: dict[int, bytes] = {}
    for page_number, page_components in components_by_page.items():
        with Image.open(BytesIO(page_images[page_number - 1])) as image:
            page_maps[page_number] = _masked_component_page_map(
                image.convert("RGB"), page_components,
            )

    first_region_on_page: set[int] = set()
    for component in components:
        page_number = component["page_number"]
        bbox = component["bbox"]
        with Image.open(BytesIO(page_images[page_number - 1])) as image:
            width, height = image.size
            padding = 0.025
            left = max(0.0, float(bbox["left"]) - padding)
            top = max(0.0, float(bbox["top"]) - padding)
            right = min(1.0, float(bbox["right"]) + padding)
            bottom = min(1.0, float(bbox["bottom"]) + padding)
            isolated = Image.new("RGB", image.size, "white")
            isolated.paste(image.convert("RGB"), mask=_component_source_mask(component))
            crop = isolated.crop((
                int(width * left), int(height * top),
                max(int(width * right), int(width * left) + 1),
                max(int(height * bottom), int(height * top) + 1),
            ))
            output = BytesIO()
            crop.save(output, format="JPEG", quality=85)
        region = {
            "representation_id": component["representation_id"],
            "page_number": page_number,
            "bbox": bbox,
            "bytes": output.getvalue(),
        }
        if page_number not in first_region_on_page:
            region["page_map_bytes"] = page_maps[page_number]
            first_region_on_page.add(page_number)
        regions.append(region)
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
