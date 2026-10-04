"""Deterministic, asynchronous object-preview production after Detection."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence
from datetime import UTC, datetime

from agents.detection_page_images import render_detection_pdf_pages
from db.repositories import insert_agent_usage_event, update_rfq_detected_object
from use_cases.estimation_artifacts import persist_preview_artifact
from use_cases.evidence_preview import crop_ocr_region_to_webp


def _source_pages(file_name: str, file_bytes: bytes, page_images: Sequence[bytes] | None) -> list[bytes]:
    if page_images:
        return list(page_images)
    if Path(file_name).suffix.lower() == ".pdf":
        return render_detection_pdf_pages(file_bytes)[0]
    if Path(file_name).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        return [file_bytes]
    return []


def _preview_target(item: Mapping[str, Any]) -> tuple[int, dict[str, Any]] | None:
    for ref in item.get("evidence_page_refs") or []:
        if not isinstance(ref, Mapping) or not isinstance(ref.get("preview_bbox"), Mapping):
            continue
        try:
            page_number = int(ref.get("page_number"))
        except (TypeError, ValueError):
            continue
        if page_number > 0:
            return page_number, dict(ref["preview_bbox"])
    return None


def normalize_preview_bbox(
    bbox: Mapping[str, Any],
    page_dimensions: Mapping[str, Any],
) -> dict[str, float]:
    """Return a crop box in the persisted OCR pixel coordinate system.

    Detection is told to emit OCR pixel coordinates, but visual models can
    occasionally return page fractions instead. A box entirely within 0..1
    is unambiguously fractional and must be expanded before crop creation and
    persistence. All other valid boxes remain unchanged.
    """
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    try:
        normalized = {key: float(bbox[key]) for key in keys}
        width = float(page_dimensions["width"])
        height = float(page_dimensions["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("preview bbox and OCR dimensions must be numeric") from exc

    if width <= 0 or height <= 0:
        raise ValueError("OCR page dimensions must be positive")

    if all(0 <= value <= 1 for value in normalized.values()):
        return {
            "top_left_x": normalized["top_left_x"] * width,
            "top_left_y": normalized["top_left_y"] * height,
            "bottom_right_x": normalized["bottom_right_x"] * width,
            "bottom_right_y": normalized["bottom_right_y"] * height,
        }
    return normalized


def create_detection_previews(
    *, client: Any, company_id: str, run_id: str, file_name: str, file_bytes: bytes,
    objects: Sequence[Mapping[str, Any]], ocr_package: Mapping[str, Any],
    page_images: Sequence[bytes] | None = None,
) -> dict[str, Any]:
    """Persist one isolated crop per object without blocking first File Review."""
    started_at = datetime.now(UTC).isoformat()
    started = perf_counter()
    pages = _source_pages(file_name, file_bytes, page_images)
    ocr_pages = {
        int(row["page_number"]): row
        for row in ocr_package.get("pages") or []
        if isinstance(row, Mapping) and row.get("page_number")
    }
    created = 0
    skipped: dict[str, str] = {}
    for object_row in objects:
        object_id = str(object_row.get("object_id") or "")
        target = _preview_target(object_row)
        if not object_id or not target:
            if object_id:
                skipped[object_id] = "preview_bbox_missing"
            continue
        page_number, bbox = target
        page = ocr_pages.get(page_number)
        if not page or page_number > len(pages):
            skipped[object_id] = "preview_page_unavailable"
            continue
        try:
            bbox = normalize_preview_bbox(bbox, page.get("dimensions") or {})
            preview = crop_ocr_region_to_webp(
                page_image=pages[page_number - 1],
                page_dimensions=page.get("dimensions") or {},
                bbox=bbox,
            )
            artifact = persist_preview_artifact(
                client=client, company_id=company_id, run_id=run_id,
                object_id=object_id, page_number=page_number, webp_bytes=preview,
            )
            refs = [dict(ref) for ref in object_row.get("evidence_page_refs") or []]
            for ref in refs:
                if int(ref.get("page_number") or 0) == page_number and ref.get("preview_bbox"):
                    ref["preview_bbox"] = bbox
                    ref["preview_ref"] = artifact.storage_ref
                    break
            update_rfq_detected_object(
                client, run_id=run_id, object_id=object_id,
                values={"evidence_page_refs": refs},
            )
            created += 1
        except Exception as exc:
            skipped[object_id] = type(exc).__name__
    result = {
        "status": "succeeded" if not skipped else "partial",
        "created": created,
        "skipped": skipped,
        "duration_seconds": round(perf_counter() - started, 3),
    }
    try:
        insert_agent_usage_event(client, {
            "company_id": company_id, "run_id": run_id, "file_name": file_name,
            "object_id": None, "object_name": None, "agent_name": "preview",
            "operation": "detection_object_previews", "model": "deterministic",
            "prompt_version": "preview_bbox_v1", "input_tokens": 0, "output_tokens": 0,
            "input_cost_usd": None, "output_cost_usd": None, "total_cost_usd": None,
            "status": result["status"], "duration_seconds": result["duration_seconds"],
            "started_at": started_at, "finished_at": datetime.now(UTC).isoformat(),
            "raw_usage": {"created": created, "skipped": skipped},
        })
    except Exception as exc:
        print(f"[Preview] Could not persist preview timing: {exc}")
    return result
