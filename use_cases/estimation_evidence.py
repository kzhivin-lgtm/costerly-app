"""Build the immutable Detection-to-Estimation evidence handoff.

The builder is intentionally storage-agnostic. Detection creates the private
artifacts while it still has the uploaded document in memory; this module only
records their immutable references with the already-produced OCR evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

ESTIMATION_INPUT_CONTRACT_VERSION = "estimation_input_v4"
@dataclass(frozen=True)
class EvidenceArtifact:
    storage_ref: str
    page_number: int
    artifact_kind: str


def _legacy_pages(value: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(value, (list, tuple, set)):
        raw_values = value
    else:
        raw_values = str(value or "").replace(";", ",").split(",")
    pages: set[int] = set()
    for raw in raw_values:
        try:
            page = int(str(raw).strip())
        except (TypeError, ValueError):
            continue
        if page > 0:
            pages.add(page)
    return tuple({"page_number": page, "source_label": str(page)} for page in sorted(pages))


def _page_refs(detected_object: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    explicit = detected_object.get("evidence_page_refs")
    if explicit is None:
        return _legacy_pages(detected_object.get("evidence_pages"))
    if not isinstance(explicit, (list, tuple)):
        raise ValueError("evidence_page_refs must be a list")
    result: list[dict[str, Any]] = []
    for item in explicit:
        if not isinstance(item, Mapping):
            raise ValueError("evidence_page_refs entries must be objects")
        try:
            page_number = int(item.get("page_number"))
        except (TypeError, ValueError) as exc:
            raise ValueError("evidence_page_refs page_number must be numeric") from exc
        if page_number < 1:
            raise ValueError("evidence_page_refs page_number must be positive")
        row = {
            "page_number": page_number,
            "source_label": str(item.get("source_label") or page_number),
        }
        result.append(row)
    return tuple(sorted(result, key=lambda item: (item["page_number"], item["source_label"])))


def _artifact_payload(artifacts: Sequence[EvidenceArtifact], page_numbers: tuple[int, ...]) -> tuple[dict[str, Any], ...]:
    result = []
    for artifact in artifacts:
        if artifact.page_number not in page_numbers:
            continue
        if not artifact.storage_ref.startswith("storage://rfq-estimation-evidence/"):
            raise ValueError("evidence artifact must be in the private evidence bucket")
        if artifact.artifact_kind != "page":
            raise ValueError("unsupported evidence artifact kind")
        result.append(
            {
                "storage_ref": artifact.storage_ref,
                "page_number": artifact.page_number,
                "artifact_kind": artifact.artifact_kind,
            }
        )
    return tuple(sorted(result, key=lambda item: (item["artifact_kind"], item["page_number"], item["storage_ref"])))


def build_estimation_input(
    *,
    run: Mapping[str, Any],
    detected_object: Mapping[str, Any],
    ocr_event_id: str,
    ocr_package: Mapping[str, Any],
    evidence_artifacts: Sequence[EvidenceArtifact],
    versions: Mapping[str, str],
) -> dict[str, Any]:
    """Freeze only approved object facts and their already-derived evidence."""

    run_id = str(run.get("run_id") or "").strip()
    company_id = str(run.get("company_id") or detected_object.get("company_id") or "").strip()
    object_id = str(detected_object.get("object_id") or "").strip()
    if not run_id or not company_id or not object_id:
        raise ValueError("run_id, company_id and object_id are required")
    if not str(ocr_event_id or "").strip():
        raise ValueError("ocr_event_id is required")
    page_refs = _page_refs(detected_object)
    if not page_refs:
        raise ValueError("object evidence must contain at least one physical page reference")
    pages = tuple(ref["page_number"] for ref in page_refs)
    evidence = dict(ocr_package.get("evidence") or {})
    blocks = []
    for block_index, block in enumerate(evidence.get("text_blocks") or [], start=1):
        if not isinstance(block, Mapping) or block.get("page_number") not in pages:
            continue
        page_number = int(block["page_number"])
        blocks.append({
            **dict(block),
            "block_ref": f"ocr:{ocr_event_id}:p{page_number}:b{block_index:04d}",
        })
    artifacts = _artifact_payload(evidence_artifacts, pages)
    if not artifacts:
        raise ValueError("at least one full source-page artifact is required")
    return {
        "contract_version": ESTIMATION_INPUT_CONTRACT_VERSION,
        "run_id": run_id,
        "company_id": company_id,
        "document": {
            "file_name": str(run.get("file_name") or ""),
            "ocr_event_id": str(ocr_event_id),
            "ocr_contract_version": str(ocr_package.get("contract_version") or ""),
        },
        "object": {
            "object_id": object_id,
            "object_name": str(detected_object.get("object_name") or ""),
            "quantity": detected_object.get("quantity"),
            "quantity_explicit": bool(detected_object.get("quantity_explicit")),
            "review_required": bool(detected_object.get("review_required")),
            "evidence_pages": list(page_refs),
        },
        "evidence": {
            "ocr_blocks": blocks,
            "artifacts": list(artifacts),
        },
        "versions": {key: str(value) for key, value in versions.items()},
    }
