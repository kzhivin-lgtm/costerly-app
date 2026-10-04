"""Derive object-specific evidence from the one already completed OCR pass.

No provider call occurs here.  The original document OCR has already returned
coordinate-bearing text blocks and image annotations.  This worker merely
selects items that geometrically belong to the locked object's preview bbox.
"""

from __future__ import annotations

from concurrent.futures import Future
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Mapping

from db.repositories import (
    fetch_rfq_detected_objects,
    insert_agent_usage_event,
    update_rfq_detected_object,
)
from use_cases.detection_previews import normalize_preview_bbox
from use_cases.estimation_artifacts import persist_object_scoped_ocr_artifact


OBJECT_SCOPED_OCR_VERSION = "object_scoped_ocr_v1"


def _bbox(value: Mapping[str, Any]) -> tuple[float, float, float, float] | None:
    try:
        left = float(value["top_left_x"])
        top = float(value["top_left_y"])
        right = float(value["bottom_right_x"])
        bottom = float(value["bottom_right_y"])
    except (KeyError, TypeError, ValueError):
        return None
    if left >= right or top >= bottom:
        return None
    return left, top, right, bottom


def _intersects(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> bool:
    return max(left[0], right[0]) < min(left[2], right[2]) and max(left[1], right[1]) < min(left[3], right[3])


def _inside(inner: tuple[float, float, float, float], outer: tuple[float, float, float, float]) -> bool:
    return outer[0] <= inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def _preview_target(item: Mapping[str, Any]) -> tuple[int, dict[str, Any], int] | None:
    for ref_index, ref in enumerate(item.get("evidence_page_refs") or []):
        if not isinstance(ref, Mapping) or not isinstance(ref.get("preview_bbox"), Mapping):
            continue
        try:
            page_number = int(ref.get("page_number"))
        except (TypeError, ValueError):
            continue
        if page_number > 0:
            return page_number, dict(ref["preview_bbox"]), ref_index
    return None


def build_object_scoped_ocr_evidence(
    *, object_id: str, page_number: int, preview_bbox: Mapping[str, Any],
    page_dimensions: Mapping[str, Any], ocr_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Select literal OCR evidence by geometry only, with no semantic inference.

    Text blocks intersecting the object crop are retained.  Image annotations
    lack per-token boxes, so they are retained only when their complete source
    image lies inside the crop.  This conservative rule prevents a full-sheet
    annotation from leaking neighboring objects into the evidence pack.
    """
    normalized_bbox = normalize_preview_bbox(preview_bbox, page_dimensions)
    object_box = _bbox(normalized_bbox)
    if object_box is None:
        raise ValueError("object preview bbox is invalid")
    text_blocks = []
    for block in ocr_evidence.get("text_blocks") or []:
        if not isinstance(block, Mapping) or int(block.get("page_number") or 0) != page_number:
            continue
        block_box = _bbox(block.get("bbox") or {})
        if block_box and _intersects(block_box, object_box):
            text_blocks.append(dict(block))
    literal_items = []
    for item in ocr_evidence.get("literal_items") or []:
        if not isinstance(item, Mapping) or int(item.get("page_number") or 0) != page_number:
            continue
        image_box = _bbox(item.get("source_image_bbox") or {})
        if image_box and _inside(image_box, object_box):
            literal_items.append(dict(item))
    return {
        "contract_version": OBJECT_SCOPED_OCR_VERSION,
        "object_id": object_id,
        "source_page_number": page_number,
        "source_bbox": normalized_bbox,
        "selection_rule": "intersecting_text_blocks_and_fully_contained_image_annotations",
        "text_blocks": text_blocks,
        "literal_items": literal_items,
    }


def create_object_scoped_ocr_evidence(
    *, client: Any, company_id: str, run_id: str, file_name: str,
    ocr_package: Mapping[str, Any], preview_future: Future[Any] | None = None,
) -> dict[str, Any]:
    """Persist derived evidence only after Preview has finished its JSON update.

    Waiting occurs in this background worker, never in Processing or File
    Review.  It serializes writes to ``evidence_page_refs`` so object OCR can
    neither overwrite a preview ref nor be overwritten by Preview itself.
    """
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    created = 0
    skipped: dict[str, str] = {}
    try:
        if preview_future is not None:
            try:
                preview_future.result()
            except Exception:
                # A missing preview does not invalidate the locked bbox.
                pass
        pages = {
            int(page["page_number"]): page for page in ocr_package.get("pages") or []
            if isinstance(page, Mapping) and page.get("page_number")
        }
        evidence = ocr_package.get("evidence") or {}
        for object_row in fetch_rfq_detected_objects(client, run_id):
            object_id = str(object_row.get("object_id") or "")
            target = _preview_target(object_row)
            if not object_id or not target:
                if object_id:
                    skipped[object_id] = "preview_bbox_missing"
                continue
            page_number, preview_bbox, ref_index = target
            page = pages.get(page_number)
            if not page:
                skipped[object_id] = "ocr_page_unavailable"
                continue
            try:
                scoped = build_object_scoped_ocr_evidence(
                    object_id=object_id, page_number=page_number,
                    preview_bbox=preview_bbox, page_dimensions=page.get("dimensions") or {},
                    ocr_evidence=evidence,
                )
                storage_ref = persist_object_scoped_ocr_artifact(
                    client=client, company_id=company_id, run_id=run_id,
                    object_id=object_id, page_number=page_number, ocr_evidence=scoped,
                )
                refs = [dict(ref) for ref in object_row.get("evidence_page_refs") or []]
                refs[ref_index]["object_ocr_ref"] = storage_ref
                refs[ref_index]["object_ocr_source_bbox"] = scoped["source_bbox"]
                update_rfq_detected_object(
                    client, run_id=run_id, object_id=object_id,
                    values={"evidence_page_refs": refs},
                )
                created += 1
            except Exception as exc:
                skipped[object_id] = type(exc).__name__
        status = "succeeded" if not skipped else "partial"
    except Exception as exc:
        status = "failed"
        skipped["run"] = type(exc).__name__
    duration_seconds = round(perf_counter() - started, 3)
    result = {"status": status, "created": created, "skipped": skipped, "duration_seconds": duration_seconds}
    try:
        insert_agent_usage_event(client, {
            "company_id": company_id, "run_id": run_id, "file_name": file_name,
            "object_id": None, "object_name": None, "agent_name": "object_ocr",
            "operation": "detection_object_scoped_ocr", "model": "deterministic",
            "prompt_version": OBJECT_SCOPED_OCR_VERSION, "input_tokens": 0, "output_tokens": 0,
            "input_cost_usd": None, "output_cost_usd": None, "total_cost_usd": None,
            "status": status, "duration_seconds": duration_seconds,
            "started_at": started_at, "finished_at": datetime.now(UTC).isoformat(),
            # Never copy private OCR text into the observability ledger.
            "raw_usage": {"created": created, "skipped": skipped},
        })
    except Exception as exc:
        print(f"[Object OCR] Could not persist worker timing: {exc}")
    return result
