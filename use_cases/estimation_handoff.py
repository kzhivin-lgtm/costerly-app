"""Immutable V4 Detection-to-Estimation evidence handoff after File Review edits."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from agents.detection_page_images import render_detection_pdf_pages
from db.repositories import insert_estimation_object_input, next_estimation_object_input_revision
from use_cases.estimation_artifacts import persist_page_artifact
from use_cases.estimation_evidence import EvidenceArtifact, build_estimation_input
from use_cases.estimation_originals import StoredOriginal


def _render_pages(file_name: str, file_bytes: bytes) -> list[bytes]:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf": return render_detection_pdf_pages(file_bytes)[0]
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}: return [file_bytes]
    return []


def _object_pages(item: Mapping[str, Any]) -> tuple[int, ...]:
    pages: set[int] = set()
    for ref in item.get("evidence_page_refs") or []:
        try: page = int(ref.get("page_number"))
        except (AttributeError, TypeError, ValueError): continue
        if page > 0: pages.add(page)
    return tuple(sorted(pages))


def persist_estimation_inputs(
    *, client: Any, run: Mapping[str, Any], objects: Sequence[Mapping[str, Any]],
    ignored_object_ids: set[str], file_name: str, file_bytes: bytes,
    ocr_event_id: str, ocr_package: Mapping[str, Any], original: StoredOriginal,
    versions: Mapping[str, str],
) -> dict[str, Any]:
    """Persist full cited pages and raw OCR, never a Detection crop or narrative."""
    estimable = [item for item in objects if str(item.get("object_id") or "") not in ignored_object_ids]
    pages = _render_pages(file_name, file_bytes) if estimable else []
    created, created_inputs, skipped = [], [], {}
    for item in estimable:
        object_id = str(item.get("object_id") or "")
        selected_pages = _object_pages(item)
        if not object_id or not selected_pages:
            skipped[object_id or "unknown"] = "evidence_pages_missing"; continue
        if any(page > len(pages) for page in selected_pages):
            skipped[object_id] = "evidence_page_not_renderable"; continue
        artifacts = [persist_page_artifact(
            client=client, company_id=str(run["company_id"]), run_id=str(run["run_id"]),
            object_id=object_id, page_number=page, page_bytes=pages[page - 1],
        ) for page in selected_pages]
        payload = build_estimation_input(
            run=run, detected_object=item, ocr_event_id=ocr_event_id,
            ocr_package=ocr_package, evidence_artifacts=artifacts, versions=versions,
        )
        labels = {int(ref["page_number"]): str(ref.get("source_label") or ref["page_number"])
                  for ref in item.get("evidence_page_refs") or [] if isinstance(ref, Mapping)}
        revision = next_estimation_object_input_revision(client, run_id=str(run["run_id"]), object_id=object_id)
        input_id = insert_estimation_object_input(
            client, run_id=str(run["run_id"]), company_id=str(run["company_id"]), object_id=object_id,
            original_file_ref=original.storage_ref, original_content_sha256=original.content_sha256,
            original_mime_type=original.mime_type, original_size_bytes=original.size_bytes,
            ocr_event_id=ocr_event_id, input_payload=payload, object_input_revision=revision,
            artifacts=[{"page_number": evidence.page_number, "source_label": labels.get(evidence.page_number, str(evidence.page_number)), "artifact_kind": "page", "storage_ref": evidence.storage_ref} for evidence in artifacts],
        )
        created.append(input_id)
        created_inputs.append({"input_id": input_id, "object_id": object_id, "object_input_revision": revision, "input_payload": payload})
    return {"created_input_ids": created, "created_inputs": created_inputs, "skipped": skipped}
