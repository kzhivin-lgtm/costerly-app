"""Detection-to-Estimation v2 handoff after File Review edits."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from agents.detection_page_images import render_detection_pdf_pages
from db.repositories import insert_estimation_object_input, next_estimation_object_input_revision
from use_cases.estimation_artifacts import persist_page_artifact, persist_preview_artifact
from use_cases.estimation_evidence import EvidenceArtifact
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


def persist_estimation_v2_inputs(
    *, client: Any, run: Mapping[str, Any], objects: Sequence[Mapping[str, Any]],
    ignored_object_ids: set[str], file_name: str, file_bytes: bytes,
    ocr_event_id: str, ocr_package: Mapping[str, Any], original: StoredOriginal,
    versions: Mapping[str, str],
) -> dict[str, Any]:
    """Persist one immutable input revision for each estimable object."""
    # Preview worker normally completed before Estimation. Full selected pages
    # still need immutable artifacts: a crop alone cannot prove cabinet blocks,
    # hardware or fabrication details to Estimation.
    needs_source_pages = any(
        str(item.get("object_id") or "") not in ignored_object_ids
        for item in objects
    )
    pages = _render_pages(file_name, file_bytes) if needs_source_pages else []
    ocr_pages = {int(row["page_number"]): row for row in ocr_package.get("pages") or [] if row.get("page_number")}
    created: list[str] = []
    created_inputs: list[dict[str, Any]] = []
    skipped: dict[str, str] = {}
    for item in objects:
        object_id = str(item.get("object_id") or "")
        if not object_id or object_id in ignored_object_ids:
            continue
        resolved = None
        existing_preview = next(
            (
                EvidenceArtifact(
                    storage_ref=str(ref["preview_ref"]),
                    page_number=int(ref["page_number"]),
                    artifact_kind="preview",
                )
                for ref in item.get("evidence_page_refs") or []
                if isinstance(ref, Mapping) and ref.get("preview_ref")
            ),
            None,
        )
        if existing_preview:
            artifact = existing_preview
            page_number = artifact.page_number
            exact_ocr_anchor = True
            resolved = {"page_number": page_number, "text": "", "bbox": {}}
        else:
            artifact = None
        # vNext supplies an object-region bbox. It is the only contract that
        # guarantees an isolated preview rather than a crop around a label.
        for page_ref in item.get("evidence_page_refs") or []:
            if artifact:
                break
            bbox = page_ref.get("preview_bbox") if isinstance(page_ref, Mapping) else None
            if isinstance(bbox, Mapping):
                try:
                    page_number = int(page_ref.get("page_number"))
                except (TypeError, ValueError):
                    continue
                if page_number > 0:
                    resolved = {"page_number": page_number, "text": "", "bbox": dict(bbox)}
                    break
        for anchor in item.get("evidence_anchors") or []:
            if resolved:
                break
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
        if not ocr_page or (not artifact and page_number > len(pages)):
            skipped[object_id] = "evidence_page_not_renderable"
            continue
        if not artifact:
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
        page_artifacts: list[EvidenceArtifact] = []
        for page_ref in item.get("evidence_page_refs") or []:
            try:
                evidence_page_number = int(page_ref.get("page_number"))
            except (AttributeError, TypeError, ValueError):
                continue
            if evidence_page_number < 1 or evidence_page_number > len(pages):
                continue
            page_artifacts.append(persist_page_artifact(
                client=client, company_id=str(run["company_id"]), run_id=str(run["run_id"]),
                object_id=object_id, page_number=evidence_page_number,
                page_bytes=pages[evidence_page_number - 1],
            ))
        if len(page_artifacts) != len({
            int(ref["page_number"]) for ref in item.get("evidence_page_refs") or []
            if isinstance(ref, Mapping) and str(ref.get("page_number") or "").isdigit()
        }):
            skipped[object_id] = "evidence_page_not_renderable"
            continue
        payload = build_estimation_input_v2(
            run=run, detected_object=item, ocr_event_id=ocr_event_id,
            ocr_package=bounded_ocr_package,
            evidence_artifacts=(artifact, *page_artifacts), versions=versions,
        )
        labels = {int(ref["page_number"]): str(ref.get("source_label") or ref["page_number"])
                  for ref in item.get("evidence_page_refs") or []}
        revision = next_estimation_object_input_revision(
            client, run_id=str(run["run_id"]), object_id=object_id
        )
        input_id = insert_estimation_object_input(
            client, run_id=str(run["run_id"]), company_id=str(run["company_id"]),
            object_id=object_id, original_file_ref=original.storage_ref,
            original_content_sha256=original.content_sha256,
            original_mime_type=original.mime_type, original_size_bytes=original.size_bytes,
            ocr_event_id=ocr_event_id, input_payload=payload,
            object_input_revision=revision,
            artifacts=[
                {"page_number": evidence.page_number, "source_label": labels.get(evidence.page_number, str(evidence.page_number)),
                 "artifact_kind": evidence.artifact_kind, "storage_ref": evidence.storage_ref}
                for evidence in (artifact, *page_artifacts)
            ],
        )
        created.append(input_id)
        created_inputs.append({
            "input_id": input_id,
            "object_id": object_id,
            "object_input_revision": revision,
            "input_payload": payload,
        })
    return {
        "created_input_ids": created,
        "created_inputs": created_inputs,
        "skipped": skipped,
    }
