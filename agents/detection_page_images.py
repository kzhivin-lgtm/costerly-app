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
_LOCAL_OCR_MAX_ITEMS = 24
_LOCAL_OCR_MAX_CHARS = 4_000


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


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bbox(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, dict):
        return None
    coordinates = tuple(
        _number(value.get(key))
        for key in (
            "top_left_x",
            "top_left_y",
            "bottom_right_x",
            "bottom_right_y",
        )
    )
    if any(coordinate is None for coordinate in coordinates):
        return None
    left, top, right, bottom = coordinates
    if right <= left or bottom <= top:
        return None
    return left, top, right, bottom


def _page_dimensions(page: dict[str, Any], fallback: tuple[int, int]) -> tuple[float, float]:
    dimensions = page.get("dimensions") if isinstance(page, dict) else None
    if not isinstance(dimensions, dict):
        return float(fallback[0]), float(fallback[1])
    width = _number(dimensions.get("width"))
    height = _number(dimensions.get("height"))
    if width is None or height is None or width <= 0 or height <= 0:
        return float(fallback[0]), float(fallback[1])
    return width, height


def _expand_bbox(
    bbox: tuple[float, float, float, float],
    *,
    page_width: float,
    page_height: float,
) -> tuple[float, float, float, float]:
    """Keep enough surrounding dimensions and captions without swallowing a sheet."""
    left, top, right, bottom = bbox
    margin_x = min(page_width * 0.08, max(page_width * 0.02, (right - left) * 0.12))
    # Drawing captions and scale notes normally sit below an elevation. Give
    # that side enough room to retain a nearby caption, but stop well before a
    # distant sheet title block can be pulled into the same context.
    margin_top = min(page_height * 0.08, max(page_height * 0.02, (bottom - top) * 0.12))
    margin_bottom = min(page_height * 0.14, max(page_height * 0.06, (bottom - top) * 0.32))
    return (
        max(0.0, left - margin_x),
        max(0.0, top - margin_top),
        min(page_width, right + margin_x),
        min(page_height, bottom + margin_bottom),
    )


def _scale_bbox(
    bbox: tuple[float, float, float, float],
    *,
    source_size: tuple[float, float],
    target_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    source_width, source_height = source_size
    target_width, target_height = target_size
    left, top, right, bottom = bbox
    scaled = (
        int(left / source_width * target_width),
        int(top / source_height * target_height),
        int(right / source_width * target_width),
        int(bottom / source_height * target_height),
    )
    return (
        max(0, min(target_width - 1, scaled[0])),
        max(0, min(target_height - 1, scaled[1])),
        max(1, min(target_width, scaled[2])),
        max(1, min(target_height, scaled[3])),
    )


def _intersection_area(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> float:
    return max(0.0, min(left[2], right[2]) - max(left[0], right[0])) * max(
        0.0, min(left[3], right[3]) - max(left[1], right[1])
    )


def _format_bbox(bbox: tuple[float, float, float, float]) -> str:
    return ",".join(str(int(value)) if value.is_integer() else str(round(value, 2)) for value in bbox)


def _local_ocr_context(
    ocr_package: dict[str, Any] | None,
    *,
    page_number: int,
    source_bbox: tuple[float, float, float, float],
) -> tuple[str, int]:
    """Return only OCR that spatially belongs to one enlarged drawing crop.

    Registry previously received arbitrary page quadrants followed by one global
    OCR dump. On a dense sheet that let a revision-table heading describe a
    remote elevation. This intentionally does not interpret OCR. It only binds
    literal text to its own crop by geometric overlap.
    """
    evidence = (ocr_package or {}).get("evidence")
    if not isinstance(evidence, dict):
        return "", 0

    local_items: list[tuple[str, str, tuple[float, float, float, float]]] = []
    seen: set[tuple[str, str, tuple[float, float, float, float]]] = set()
    for kind in ("text_blocks", "literal_items"):
        for item in evidence.get(kind) or []:
            if not isinstance(item, dict):
                continue
            try:
                item_page = int(item.get("page_number"))
            except (TypeError, ValueError):
                continue
            if item_page != page_number:
                continue
            item_bbox = _bbox(item.get("bbox") if kind == "text_blocks" else item.get("source_image_bbox"))
            text = " ".join(str(item.get("text") or "").split())
            if not item_bbox or not text or _intersection_area(source_bbox, item_bbox) <= 0:
                continue
            label = str(item.get("block_type") or "text") if kind == "text_blocks" else str(item.get("category") or "literal")
            record = (label, text, item_bbox)
            if record in seen:
                continue
            seen.add(record)
            local_items.append(record)

    if not local_items:
        return "", 0
    local_items.sort(key=lambda item: (item[2][1], item[2][0], item[0], item[1]))
    lines = [
        "LOCAL OCR FOR THE IMMEDIATELY PRECEDING REGION ONLY. "
        "Each item overlaps this crop or its narrow surrounding margin. "
        "Do not treat it as an object boundary.",
    ]
    for label, text, item_bbox in local_items[:_LOCAL_OCR_MAX_ITEMS]:
        lines.append(f'- {label} B={_format_bbox(item_bbox)} {text!r}')
    context = "\n".join(lines)
    if len(context) > _LOCAL_OCR_MAX_CHARS:
        context = context[:_LOCAL_OCR_MAX_CHARS].rstrip() + "\n[local OCR truncated]"
    return context, min(len(local_items), _LOCAL_OCR_MAX_ITEMS)


def _ocr_visual_crops(
    page: dict[str, Any] | None,
    *,
    page_number: int,
    page_size: tuple[int, int],
    ocr_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(page, dict):
        return []
    source_width, source_height = _page_dimensions(page, page_size)
    min_area = source_width * source_height * 0.002
    candidates: list[tuple[float, str, tuple[float, float, float, float]]] = []
    for position, image in enumerate(page.get("images") or [], start=1):
        if not isinstance(image, dict):
            continue
        bbox = _bbox(image)
        if not bbox:
            continue
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if area < min_area:
            continue
        identifier = str(image.get("id") or f"image-{position}")
        candidates.append((area, identifier, bbox))

    selected: list[dict[str, Any]] = []
    for _, identifier, bbox in sorted(candidates, key=lambda item: (-item[0], item[1])):
        # OCR can return one enclosing image plus a near-duplicate child. Keep
        # the larger depiction once, rather than spending a crop slot twice.
        if any(
            _intersection_area(bbox, previous["source_bbox"])
            / min(
                (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]),
                (previous["source_bbox"][2] - previous["source_bbox"][0])
                * (previous["source_bbox"][3] - previous["source_bbox"][1]),
            )
            >= 0.9
            for previous in selected
        ):
            continue
        crop_bbox = _expand_bbox(
            bbox,
            page_width=source_width,
            page_height=source_height,
        )
        local_context, local_count = _local_ocr_context(
            ocr_package,
            page_number=page_number,
            source_bbox=crop_bbox,
        )
        selected.append({
            "region": f"ocr_visual_{identifier}",
            "source_bbox": crop_bbox,
            "source_image_id": identifier,
            "local_ocr_context": local_context,
            "local_ocr_item_count": local_count,
        })
        if len(selected) == REGISTRY_REGIONS_PER_PAGE:
            break
    return selected


def build_detection_registry_regions(
    page_images: list[bytes],
    *,
    ocr_package: dict[str, Any] | None = None,
    max_images: int = REGISTRY_MAX_IMAGES,
) -> list[dict[str, Any]]:
    """Add OCR-grounded drawing crops, falling back to stable page zones.

    Every crop stays inside the existing Registry image budget. OCR regions are
    a grounding aid only, not a source of object boundaries.
    """
    if not page_images:
        return []
    from PIL import Image

    ocr_pages = {
        int(page.get("page_number")): page
        for page in (ocr_package or {}).get("pages") or []
        if isinstance(page, dict) and isinstance(page.get("page_number"), int)
    }
    regions: list[dict[str, Any]] = []
    available_regions = max(0, max_images - len(page_images))
    pages_with_regions = available_regions // REGISTRY_REGIONS_PER_PAGE
    for page_number, page_bytes in enumerate(page_images[:pages_with_regions], start=1):
        with Image.open(BytesIO(page_bytes)) as image:
            width, height = image.size
            crops = _ocr_visual_crops(
                ocr_pages.get(page_number),
                page_number=page_number,
                page_size=(width, height),
                ocr_package=ocr_package,
            )
            if not crops:
                crops = [
                    {"region": "upper_left", "target_bbox": (0, 0, width // 2, height // 2)},
                    {"region": "upper_right", "target_bbox": (width // 2, 0, width, height // 2)},
                    {"region": "lower", "target_bbox": (0, height // 2, width, height)},
                ]
            for crop in crops:
                target_bbox = crop.get("target_bbox")
                if target_bbox is None:
                    target_bbox = _scale_bbox(
                        crop["source_bbox"],
                        source_size=_page_dimensions(ocr_pages.get(page_number) or {}, (width, height)),
                        target_size=(width, height),
                    )
                left, top, right, bottom = target_bbox
                if right <= left or bottom <= top:
                    continue
                output = BytesIO()
                image.crop(target_bbox).save(output, format="JPEG", quality=85)
                regions.append({
                    "page_number": page_number,
                    "region": crop["region"],
                    "bytes": output.getvalue(),
                    **{
                        key: value
                        for key, value in crop.items()
                        if key not in {"target_bbox"}
                    },
                })
    return regions
