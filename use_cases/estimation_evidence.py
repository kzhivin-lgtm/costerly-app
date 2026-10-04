"""Build the immutable Detection-to-Estimation evidence handoff.

The builder is intentionally storage-agnostic. Detection creates the private
artifacts while it still has the uploaded document in memory; this module only
records their immutable references with the already-produced OCR evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from use_cases.material_identity_resolution import normalize_material_phrase


ESTIMATION_INPUT_CONTRACT_VERSION = "estimation_input_v2"
@dataclass(frozen=True)
class EvidenceArtifact:
    storage_ref: str
    page_number: int
    artifact_kind: str


def resolve_anchor_bbox(
    *,
    anchor: Mapping[str, Any],
    ocr_package: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return one exact OCR bbox, never a nearest-text approximation."""
    try:
        page_number = int(anchor.get("page_number"))
    except (TypeError, ValueError):
        return None
    text = normalize_material_phrase(anchor.get("text"))
    if page_number < 1 or not text:
        return None
    matches = [
        block
        for block in (ocr_package.get("evidence") or {}).get("text_blocks") or []
        if isinstance(block, Mapping)
        and block.get("page_number") == page_number
        and normalize_material_phrase(block.get("text")) == text
        and isinstance(block.get("bbox"), Mapping)
    ]
    if len(matches) != 1:
        return None
    bbox = dict(matches[0]["bbox"])
    required = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    if any(bbox.get(key) is None for key in required):
        return None
    return {"page_number": page_number, "text": str(matches[0]["text"]), "bbox": bbox}


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
        if item.get("roles"):
            row["roles"] = [str(role) for role in item["roles"]]
        if isinstance(item.get("preview_bbox"), Mapping):
            row["preview_bbox"] = dict(item["preview_bbox"])
        result.append(row)
    return tuple(sorted(result, key=lambda item: (item["page_number"], item["source_label"])))


def _artifact_payload(artifacts: Sequence[EvidenceArtifact], page_numbers: tuple[int, ...]) -> tuple[dict[str, Any], ...]:
    result = []
    for artifact in artifacts:
        if artifact.page_number not in page_numbers:
            continue
        if not artifact.storage_ref.startswith("storage://rfq-estimation-evidence/"):
            raise ValueError("evidence artifact must be in the private evidence bucket")
        if artifact.artifact_kind not in {"preview", "page", "region"}:
            raise ValueError("unsupported evidence artifact kind")
        result.append(
            {
                "storage_ref": artifact.storage_ref,
                "page_number": artifact.page_number,
                "artifact_kind": artifact.artifact_kind,
            }
        )
    return tuple(sorted(result, key=lambda item: (item["artifact_kind"], item["page_number"], item["storage_ref"])))


def build_estimation_input_v2(
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
    previews = [artifact for artifact in artifacts if artifact["artifact_kind"] == "preview"]
    if len(previews) != 1:
        raise ValueError("exactly one source-derived preview artifact is required")
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
            "dimensions": dict(detected_object.get("dimensions_json") or {}),
            "detected_materials": str(detected_object.get("detected_materials") or ""),
            "notes": str(detected_object.get("notes") or ""),
            "evidence_pages": list(page_refs),
        },
        "evidence": {
            "ocr_blocks": blocks,
            "artifacts": list(artifacts),
            "primary_preview_ref": previews[0]["storage_ref"],
        },
        "versions": {key: str(value) for key, value in versions.items()},
    }
