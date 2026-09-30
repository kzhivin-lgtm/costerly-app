"""Shadow Detection-to-Estimation v2 handoff after File Review edits."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from agents.detection_page_images import render_detection_pdf_pages
from db.repositories import insert_estimation_object_input
from use_cases.estimation_artifacts import persist_preview_artifact
from use_cases.estimation_evidence import build_estimation_input_v2, resolve_anchor_bbox
from use_cases.estimation_originals import StoredOriginal
from use_cases.evidence_preview import crop_ocr_region_to_webp


def _render_pages(file_name: str, file_bytes: bytes) -> list[bytes]:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return render_detection_pdf_pages(file_bytes)[0]
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return [file_bytes]
    return []


def persist_estimation_v2_shadow_inputs(
    *, client: Any, run: Mapping[str, Any], objects: Sequence[Mapping[str, Any]],
    ignored_object_ids: set[str], file_name: str, file_bytes: bytes,
    ocr_event_id: str, ocr_package: Mapping[str, Any], original: StoredOriginal,
    versions: Mapping[str, str],
) -> dict[str, Any]:
    """Persist valid object revisions; skip unsafe objects without breaking legacy flow."""
    pages = _render_pages(file_name, file_bytes)
    ocr_pages = {int(row["page_number"]): row for row in ocr_package.get("pages") or [] if row.get("page_number")}
    created: list[str] = []
    created_inputs: list[dict[str, Any]] = []
    skipped: dict[str, str] = {}
    for item in objects:
        object_id = str(item.get("object_id") or "")
        if not object_id or object_id in ignored_object_ids:
            continue
        resolved = None
        for anchor in item.get("evidence_anchors") or []:
            resolved = resolve_anchor_bbox(anchor=anchor, ocr_package=ocr_package)
            if resolved:
                break
        exact_ocr_anchor = resolved is not None
        if not resolved:
            for page_ref in item.get("evidence_page_refs") or []:
                try:
                    page_number = int(page_ref.get("page_number"))
                except (AttributeError, TypeError, ValueError):
                    continue
                ocr_page = ocr_pages.get(page_number)
                dimensions = (ocr_page or {}).get("dimensions") or {}
                width = dimensions.get("width")
                height = dimensions.get("height")
                if page_number <= len(pages) and width and height:
                    resolved = {
                        "page_number": page_number,
                        "text": "",
                        "bbox": {
                            "top_left_x": 0,
                            "top_left_y": 0,
                            "bottom_right_x": width,
                            "bottom_right_y": height,
                        },
                    }
                    break
        if not resolved:
            skipped[object_id] = "evidence_page_not_resolved"
            continue
        page_number = int(resolved["page_number"])
        ocr_page = ocr_pages.get(page_number)
        if not ocr_page or page_number > len(pages):
            skipped[object_id] = "evidence_page_not_renderable"
            continue
        preview = crop_ocr_region_to_webp(
            page_image=pages[page_number - 1],
            page_dimensions=ocr_page.get("dimensions") or {},
            bbox=resolved["bbox"],
        )
        artifact = persist_preview_artifact(
            client=client, company_id=str(run["company_id"]), run_id=str(run["run_id"]),
            object_id=object_id, page_number=page_number, webp_bytes=preview,
        )
        bounded_ocr_package = ocr_package
        if not exact_ocr_anchor:
            bounded_ocr_package = {
                **dict(ocr_package),
                "evidence": {
                    **dict(ocr_package.get("evidence") or {}),
                    "text_blocks": [],
                },
            }
        payload = build_estimation_input_v2(
            run=run, detected_object=item, ocr_event_id=ocr_event_id,
            ocr_package=bounded_ocr_package,
            evidence_artifacts=(artifact,), versions=versions,
        )
        labels = {int(ref["page_number"]): str(ref.get("source_label") or ref["page_number"])
                  for ref in item.get("evidence_page_refs") or []}
        input_id = insert_estimation_object_input(
            client, run_id=str(run["run_id"]), company_id=str(run["company_id"]),
            object_id=object_id, original_file_ref=original.storage_ref,
            original_content_sha256=original.content_sha256,
            original_mime_type=original.mime_type, original_size_bytes=original.size_bytes,
            ocr_event_id=ocr_event_id, input_payload=payload,
            artifacts=[{"page_number": page_number, "source_label": labels.get(page_number, str(page_number)),
                        "artifact_kind": artifact.artifact_kind, "storage_ref": artifact.storage_ref}],
        )
        created.append(input_id)
        created_inputs.append({
            "input_id": input_id,
            "object_input_revision": 1,
            "input_payload": payload,
        })
    return {
        "created_input_ids": created,
        "created_inputs": created_inputs,
        "skipped": skipped,
    }
