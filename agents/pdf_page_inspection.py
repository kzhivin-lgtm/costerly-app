"""Passive per-page inspection of native PDF structure and rendered coverage.

The inspection is deliberately evidence-only.  It exposes what the PDF makes
available before Detection decides what a drawing depicts.  In particular, a
Form XObject, a vector cluster, or an image placement is never an object.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from io import BytesIO
import multiprocessing
import re
import time
from typing import Any


PDF_PAGE_INSPECTION_CONTRACT_VERSION = "pdf_page_inspection_v1"
_TEXT_LAYER_SPARSE_MAX_SPANS = 3
# ``get_cdrawings()`` materializes every path item. Large construction sheets
# can contain hundreds of thousands of them, so detail extraction is bounded
# by the uncompressed page content stream, not by an after-the-fact list size.
_VECTOR_DETAIL_CONTENT_BYTES_LIMIT = 500_000
_VECTOR_CLUSTER_DRAWING_LIMIT = 1_500
_FORM_XOBJECT_INVENTORY_LIMIT = 64
_VECTOR_PATH_START_RE = re.compile(rb"(?<![A-Za-z])(?:m|re)(?![A-Za-z])")
_PROFILE_KEYS = (
    "page_number",
    "representation",
    "text_layer",
    "structural_anchors",
    "coordinate_evidence",
    "eligible_mechanisms",
    "page_size_points",
    "rendered_page",
    "raw_metrics",
    "sources",
)


def _rect_bbox(rect: object) -> dict[str, float] | None:
    try:
        left, top, right, bottom = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
    except (AttributeError, TypeError, ValueError):
        return None
    if right <= left or bottom <= top:
        return None
    return {
        "top_left_x": round(left, 6),
        "top_left_y": round(top, 6),
        "bottom_right_x": round(right, 6),
        "bottom_right_y": round(bottom, 6),
    }


def _area_ratio(rectangles: list[dict[str, float]], *, width: float, height: float) -> float:
    """Return a bounded, overlap-tolerant coverage estimate.

    Exact polygon union is unnecessary for a page profile.  Summing placement
    rectangles and capping at the page area makes the metric cheap and keeps
    it explicitly raw, rather than pretending it is object coverage.
    """
    page_area = width * height
    if page_area <= 0:
        return 0.0
    total = sum(
        max(0.0, box["bottom_right_x"] - box["top_left_x"])
        * max(0.0, box["bottom_right_y"] - box["top_left_y"])
        for box in rectangles
    )
    return round(min(1.0, total / page_area), 6)


def _text_layer(span_count: int) -> str:
    if span_count <= 0:
        return "absent"
    if span_count <= _TEXT_LAYER_SPARSE_MAX_SPANS:
        return "sparse"
    return "substantive"


def _profile_classification(
    *,
    text_span_count: int,
    image_placement_count: int,
    form_xobject_count: int,
    has_vector: bool,
) -> tuple[str, str, str, list[str]]:
    has_raster = image_placement_count > 0
    has_vector = form_xobject_count > 0 or has_vector
    has_text = text_span_count > 0
    if has_raster and has_vector:
        representation = "mixed"
    elif has_raster:
        representation = "raster"
    elif has_vector:
        representation = "vector"
    elif has_text:
        representation = "text_only"
    else:
        representation = "empty"

    anchor_kinds = [
        kind
        for kind, present in (
            ("image", has_raster),
            ("form", form_xobject_count > 0),
            ("vector", has_vector),
        )
        if present
    ]
    structural_anchors = (
        "none" if not anchor_kinds
        else anchor_kinds[0] if len(anchor_kinds) == 1
        else "several"
    )
    coordinate_evidence = (
        "absent" if not has_text
        else "partial" if text_span_count <= _TEXT_LAYER_SPARSE_MAX_SPANS
        else "usable"
    )
    mechanisms = ["ocr", "visual_detection"]
    if has_text:
        mechanisms.append("text_fusion")
    if has_raster or form_xobject_count:
        mechanisms.append("native_anchor_recall")
    if has_vector:
        mechanisms.append("vector_cluster_recall")
    return representation, structural_anchors, coordinate_evidence, mechanisms


def _native_text_blocks_for_page(page: Any, *, page_number: int, dpi: int) -> list[dict[str, Any]]:
    import fitz

    scale = dpi / 72
    blocks: list[dict[str, Any]] = []
    for source_block in page.get_text("dict").get("blocks") or []:
        for line in source_block.get("lines") or []:
            for span in line.get("spans") or []:
                text = str(span.get("text") or "").strip()
                source_bbox = span.get("bbox")
                if not text or not isinstance(source_bbox, (list, tuple)) or len(source_bbox) != 4:
                    continue
                rendered_bbox = fitz.Rect(source_bbox) * page.rotation_matrix
                blocks.append({
                    "page_number": page_number,
                    "text": text,
                    "bbox": {
                        "top_left_x": round(rendered_bbox.x0 * scale),
                        "top_left_y": round(rendered_bbox.y0 * scale),
                        "bottom_right_x": round(rendered_bbox.x1 * scale),
                        "bottom_right_y": round(rendered_bbox.y1 * scale),
                    },
                })
    return blocks


def _native_image_regions_for_page(page: Any, *, page_number: int, dpi: int) -> list[dict[str, Any]]:
    scale = dpi / 72
    rotated_page = page.rect * page.rotation_matrix
    seen_placements: set[tuple[int, float, float, float, float]] = set()
    regions: list[dict[str, Any]] = []
    for image_index, image in enumerate(page.get_images(full=True), start=1):
        xref = int(image[0])
        image_width = int(image[2])
        image_height = int(image[3])
        for placement_index, source_rect in enumerate(
            page.get_image_rects(xref, transform=False), start=1,
        ):
            rendered_rect = source_rect * page.rotation_matrix
            if rendered_rect.width <= 0 or rendered_rect.height <= 0:
                continue
            placement_key = (
                xref,
                round(rendered_rect.x0, 6), round(rendered_rect.y0, 6),
                round(rendered_rect.x1, 6), round(rendered_rect.y1, 6),
            )
            if placement_key in seen_placements:
                continue
            seen_placements.add(placement_key)
            regions.append({
                "graphic_id": (
                    f"NPIG-P{page_number:03d}-X{xref}-I{image_index:03d}-R{placement_index:03d}"
                ),
                "page_number": page_number,
                "bbox": {
                    "top_left_x": round(rendered_rect.x0 * scale),
                    "top_left_y": round(rendered_rect.y0 * scale),
                    "bottom_right_x": round(rendered_rect.x1 * scale),
                    "bottom_right_y": round(rendered_rect.y1 * scale),
                },
                "source_bbox_points": {
                    "top_left_x": round(rendered_rect.x0, 6),
                    "top_left_y": round(rendered_rect.y0, 6),
                    "bottom_right_x": round(rendered_rect.x1, 6),
                    "bottom_right_y": round(rendered_rect.y1, 6),
                },
                "source_page_width_points": round(rotated_page.width, 6),
                "source_page_height_points": round(rotated_page.height, 6),
                "image_width": image_width,
                "image_height": image_height,
            })
    return regions


def _form_xobject_inventory(raw_xobjects: list[Any]) -> tuple[list[dict[str, Any]], int]:
    """Return a bounded inventory of Form XObject placements, not objects."""
    inventory: list[dict[str, Any]] = []
    for position, xobject in enumerate(raw_xobjects[:_FORM_XOBJECT_INVENTORY_LIMIT], start=1):
        if not isinstance(xobject, (tuple, list)):
            continue
        entry: dict[str, Any] = {"position": position}
        if xobject:
            entry["xref"] = xobject[0]
        if len(xobject) > 1:
            entry["name"] = str(xobject[1])
        if len(xobject) > 2:
            entry["invoker_xref"] = xobject[2]
        if len(xobject) > 3 and (bbox := _rect_bbox(xobject[3])) is not None:
            entry["bbox_points"] = bbox
        inventory.append(entry)
    return inventory, max(0, len(raw_xobjects) - len(inventory))


def inspect_native_pdf_pages(
    file_bytes: bytes,
    *,
    dpi: int,
) -> dict[str, Any]:
    """Inspect every PDF page once and return only compact structural facts."""
    try:
        import fitz
    except (ImportError, ModuleNotFoundError) as exc:
        return {
            "contract_version": PDF_PAGE_INSPECTION_CONTRACT_VERSION,
            "text_blocks": [],
            "graphic_regions": [],
            "page_profiles": [],
            "sources": {"status": "unavailable", "error": str(exc)},
        }

    started = time.perf_counter()
    source_seconds = {"native_text": 0.0, "image_xobjects": 0.0, "form_xobjects": 0.0, "vector_summary": 0.0}
    text_blocks: list[dict[str, Any]] = []
    graphic_regions: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        return {
            "contract_version": PDF_PAGE_INSPECTION_CONTRACT_VERSION,
            "text_blocks": [],
            "graphic_regions": [],
            "page_profiles": [],
            "sources": {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "extraction_seconds": round(time.perf_counter() - started, 6),
            },
        }
    try:
        for page_index, page in enumerate(document, start=1):
            page_rect = page.rect * page.rotation_matrix
            page_width, page_height = float(page_rect.width), float(page_rect.height)

            page_sources: dict[str, dict[str, Any]] = {}
            started_source = time.perf_counter()
            try:
                page_text_blocks = _native_text_blocks_for_page(
                    page, page_number=page_index, dpi=dpi,
                )
                page_sources["native_text"] = {"status": "succeeded"}
            except Exception as exc:
                page_text_blocks = []
                page_sources["native_text"] = {
                    "status": "failed", "error": f"{type(exc).__name__}: {exc}",
                }
            text_seconds = time.perf_counter() - started_source
            source_seconds["native_text"] += text_seconds
            page_sources["native_text"]["seconds"] = round(text_seconds, 6)

            started_source = time.perf_counter()
            try:
                page_graphics = _native_image_regions_for_page(
                    page, page_number=page_index, dpi=dpi,
                )
                image_info_count = len(page.get_image_info())
                page_sources["image_xobjects"] = {"status": "succeeded"}
            except Exception as exc:
                page_graphics = []
                image_info_count = 0
                page_sources["image_xobjects"] = {
                    "status": "failed", "error": f"{type(exc).__name__}: {exc}",
                }
            image_seconds = time.perf_counter() - started_source
            source_seconds["image_xobjects"] += image_seconds
            page_sources["image_xobjects"]["seconds"] = round(image_seconds, 6)

            started_source = time.perf_counter()
            try:
                raw_xobjects = page.get_xobjects()
                form_inventory, form_inventory_truncated_count = _form_xobject_inventory(raw_xobjects)
                page_sources["form_xobjects"] = {"status": "succeeded"}
            except Exception as exc:
                raw_xobjects = []
                form_inventory = []
                form_inventory_truncated_count = 0
                page_sources["form_xobjects"] = {
                    "status": "failed", "error": f"{type(exc).__name__}: {exc}",
                }
            form_seconds = time.perf_counter() - started_source
            source_seconds["form_xobjects"] += form_seconds
            page_sources["form_xobjects"]["seconds"] = round(form_seconds, 6)

            started_source = time.perf_counter()
            content_stream = b""
            vector_stream_error: str | None = None
            try:
                content_stream = b"".join(
                    document.xref_stream(xref) for xref in page.get_contents()
                )
            except Exception as exc:
                # The remaining sources stay useful if a malformed content
                # stream cannot be inspected.
                vector_stream_error = f"{type(exc).__name__}: {exc}"
            approximate_path_count = len(_VECTOR_PATH_START_RE.findall(content_stream))
            drawings: list[dict[str, Any]] = []
            drawing_boxes: list[dict[str, float]] = []
            vector_item_count: int | None = approximate_path_count
            vector_path_count: int | None = None
            cluster_count: int | None = None
            if len(content_stream) <= _VECTOR_DETAIL_CONTENT_BYTES_LIMIT:
                try:
                    drawings = page.get_cdrawings()
                    drawing_boxes = [
                        box for drawing in drawings
                        if (box := _rect_bbox(drawing.get("rect")))
                    ]
                    vector_path_count = len(drawings)
                    vector_item_count = sum(
                        len(drawing.get("items") or []) for drawing in drawings
                    )
                    if drawings and len(drawings) <= _VECTOR_CLUSTER_DRAWING_LIMIT:
                        try:
                            # cluster_drawings accepts get_drawings() output,
                            # not the compact cdrawings representation.
                            cluster_count = len(page.cluster_drawings())
                            cluster_status = "succeeded"
                        except Exception as exc:  # version-dependent optional detail
                            cluster_status = f"failed:{type(exc).__name__}"
                    elif drawings:
                        cluster_status = "skipped_path_limit"
                    else:
                        cluster_status = "not_needed"
                    vector_status = "exact"
                except Exception as exc:
                    cluster_status = f"failed:{type(exc).__name__}"
                    vector_status = "approximate_after_detail_failure"
            else:
                cluster_status = "skipped_content_stream_limit"
                vector_status = "approximate_content_stream"
            vector_seconds = time.perf_counter() - started_source
            source_seconds["vector_summary"] += vector_seconds
            page_sources["vector_summary"] = {
                "status": "failed" if vector_stream_error else "succeeded",
                "seconds": round(vector_seconds, 6),
            }
            if vector_stream_error:
                page_sources["vector_summary"]["error"] = vector_stream_error

            representation, anchors, coordinate_evidence, mechanisms = _profile_classification(
                text_span_count=len(page_text_blocks),
                image_placement_count=len(page_graphics),
                form_xobject_count=len(raw_xobjects),
                has_vector=bool(vector_path_count or approximate_path_count),
            )
            profiles.append({
                "page_number": page_index,
                "representation": representation,
                "text_layer": _text_layer(len(page_text_blocks)),
                "structural_anchors": anchors,
                "coordinate_evidence": coordinate_evidence,
                "eligible_mechanisms": mechanisms,
                "page_size_points": {
                    "width": round(page_width, 6), "height": round(page_height, 6),
                },
                "rendered_page": {"status": "pending"},
                "raw_metrics": {
                    "native_text_span_count": len(page_text_blocks),
                    "image_xobject_placement_count": len(page_graphics),
                    "image_info_count": image_info_count,
                    "image_placement_area_ratio": _area_ratio(
                        [region["source_bbox_points"] for region in page_graphics],
                        width=page_width, height=page_height,
                    ),
                    "form_xobject_count": len(raw_xobjects),
                    "form_xobject_inventory": form_inventory,
                    "form_xobject_inventory_truncated_count": form_inventory_truncated_count,
                    "vector_path_count": vector_path_count,
                    "vector_primitive_count": vector_item_count,
                    "vector_path_count_estimate": approximate_path_count,
                    "vector_content_stream_bytes": len(content_stream),
                    "vector_summary_status": vector_status,
                    "vector_cluster_count": cluster_count,
                    "vector_cluster_status": cluster_status,
                    "vector_path_area_ratio": (
                        _area_ratio(drawing_boxes, width=page_width, height=page_height)
                        if vector_status == "exact" else None
                    ),
                },
                "sources": page_sources,
            })
            text_blocks.extend(page_text_blocks)
            graphic_regions.extend(page_graphics)
    finally:
        document.close()

    return {
        "contract_version": PDF_PAGE_INSPECTION_CONTRACT_VERSION,
        "text_blocks": text_blocks,
        "graphic_regions": graphic_regions,
        "page_profiles": profiles,
        "sources": {
            "status": "succeeded",
            "extraction_seconds": round(time.perf_counter() - started, 6),
            "timings_seconds": {key: round(value, 6) for key, value in source_seconds.items()},
        },
    }


def measure_rendered_page_visual_coverage(page_bytes: bytes) -> dict[str, Any]:
    """Measure raw non-background coverage from an already rendered page.

    This never renders a second PDF page.  A dominant quantized colour is only
    an estimate of the page background and is reported as such.
    """
    try:
        from PIL import Image

        image = Image.open(BytesIO(page_bytes)).convert("RGB")
        image.thumbnail((512, 512))
        pixels = list(image.get_flattened_data())
        if not pixels:
            raise ValueError("empty rendered image")
        buckets = Counter((red // 16, green // 16, blue // 16) for red, green, blue in pixels)
        dominant = buckets.most_common(1)[0][0]
        background = tuple(channel * 16 + 8 for channel in dominant)
        occupied = sum(
            abs(red - background[0]) + abs(green - background[1]) + abs(blue - background[2]) > 48
            for red, green, blue in pixels
        )
        return {
            "status": "succeeded",
            "width": image.width,
            "height": image.height,
            "sample_pixel_count": len(pixels),
            "dominant_background_rgb": list(background),
            "occupied_area_ratio": round(occupied / len(pixels), 6),
        }
    except Exception as exc:
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def attach_rendered_page_measurements(
    page_profiles: list[dict[str, Any]],
    rendered_pages: dict[int, bytes],
) -> list[dict[str, Any]]:
    """Attach visual measurements by physical page number, without rerendering."""
    attached: list[dict[str, Any]] = []
    for profile in page_profiles:
        if not isinstance(profile, dict):
            continue
        result = deepcopy(profile)
        page_number = result.get("page_number")
        if isinstance(page_number, int) and page_number in rendered_pages:
            result["rendered_page"] = measure_rendered_page_visual_coverage(
                rendered_pages[page_number]
            )
        else:
            result["rendered_page"] = {"status": "unavailable"}
        attached.append(result)
    return attached


def compact_page_profile_audit(ocr_package: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return the passive page profile passed through Fusion diagnostics.

    No Registry prompt, candidate region, route, object boundary or quantity
    consumes this audit in V6.1.  Keeping it compact makes a finished run
    inspectable without loading its full provider ledger.
    """
    evidence = (ocr_package or {}).get("evidence") or {}
    profiles = evidence.get("page_profiles") or []
    return [
        {key: deepcopy(profile[key]) for key in _PROFILE_KEYS if key in profile}
        for profile in profiles
        if isinstance(profile, dict) and isinstance(profile.get("page_number"), int)
    ]


def _isolated_native_page_inspection_worker(
    file_bytes: bytes, dpi: int, connection: Any,
) -> None:
    try:
        connection.send(("ok", inspect_native_pdf_pages(file_bytes, dpi=dpi)))
    except Exception as exc:  # pragma: no cover - child-process containment
        connection.send(("error", str(exc)))
    finally:
        connection.close()


def _failed_isolated_inspection(error: str) -> dict[str, Any]:
    return {
        "sources": {"status": "failed", "error": error},
        "text_blocks": [], "graphic_regions": [], "page_profiles": [],
    }


@dataclass
class NativePdfPageInspectionJob:
    """An already-started isolated PDF traversal.

    The child owns PyMuPDF's vector traversal. The parent can render and send
    pages to OCR while this work is in flight, then collect one bounded result.
    """

    process: Any
    receive: Any

    def collect(self, *, timeout_seconds: float = 45.0) -> dict[str, Any]:
        try:
            if not self.receive.poll(timeout_seconds):
                self.process.terminate()
                return _failed_isolated_inspection("inspection timeout")
            try:
                status, payload = self.receive.recv()
            except EOFError:
                return _failed_isolated_inspection(
                    "inspection worker exited without a result",
                )
        finally:
            self.receive.close()
            self.process.join(timeout=2)
        if status == "ok":
            return payload
        return _failed_isolated_inspection(str(payload))


def start_native_pdf_pages_isolated(
    file_bytes: bytes, *, dpi: int,
) -> NativePdfPageInspectionJob:
    """Start a PyMuPDF inspection before renderer threads are created."""
    context = multiprocessing.get_context("fork")
    receive, send = context.Pipe(duplex=False)
    process = context.Process(
        target=_isolated_native_page_inspection_worker,
        args=(file_bytes, dpi, send),
    )
    process.start()
    send.close()
    return NativePdfPageInspectionJob(process=process, receive=receive)


def inspect_native_pdf_pages_isolated(
    file_bytes: bytes, *, dpi: int,
) -> dict[str, Any]:
    """Contain PyMuPDF vector parsing away from threaded page rendering."""
    return start_native_pdf_pages_isolated(file_bytes, dpi=dpi).collect()
