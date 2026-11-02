"""Build a safe Object-to-Estimate brief from immutable evidence claims."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from use_cases.estimation_object_to_estimate_contract import (
    OBJECT_TO_ESTIMATE_V1,
    validate_object_to_estimate_v1,
)


_DEFAULT_DIMENSIONS_MM = {
    "width": (1000, "default_cabinet_width_1000mm"),
    "depth": (600, "default_cabinet_depth_600mm"),
    "height": (2000, "default_cabinet_height_2000mm"),
}
_DEFAULT_COUNTS = {
    "bay_count": (1, "default_single_bay"),
    "door_count": (1, "default_single_door"),
    "shelf_count_per_bay": (1, "default_single_shelf_per_bay"),
}


def _positive(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _confidence(value: Any) -> float:
    number = _positive(value)
    return min(number or 0.0, 100.0)


def _allowed_refs(payload: Mapping[str, Any]) -> set[str]:
    evidence = payload.get("evidence") or {}
    return {
        str(item.get("storage_ref") or item.get("block_ref") or "")
        for kind in ("artifacts", "ocr_blocks", "ocr_literal_items")
        for item in evidence.get(kind) or []
        if isinstance(item, Mapping) and str(item.get("storage_ref") or item.get("block_ref") or "")
    }


def _best_claim(
    claims: Sequence[Mapping[str, Any]], *, expected_key: str, allowed_refs: set[str],
) -> Mapping[str, Any] | None:
    valid = []
    for claim in claims:
        if not isinstance(claim, Mapping) or claim.get("key") != expected_key:
            continue
        refs = claim.get("evidence_refs")
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref in allowed_refs for ref in refs):
            continue
        if _positive(claim.get("value")) is None:
            continue
        valid.append(claim)
    return max(valid, key=lambda claim: (_confidence(claim.get("confidence")), tuple(claim.get("evidence_refs") or ()))) if valid else None


def build_object_to_estimate_brief(
    *, input_row: Mapping[str, Any], extraction: Mapping[str, Any],
) -> dict[str, Any]:
    """Select cited geometry or explicit defaults, then validate the brief.

    ``extraction`` is a model result after page-level evidence validation. The
    builder is deterministic and never turns a missing claim into a cited fact.
    """
    payload = input_row.get("input_payload") or {}
    if not isinstance(payload, Mapping) or payload.get("contract_version") != "estimation_input_v4":
        raise ValueError("object-to-estimate requires an immutable estimation_input_v4 input")
    object_payload = payload.get("object") or {}
    allowed_refs = _allowed_refs(payload)
    if not allowed_refs:
        raise ValueError("object-to-estimate input has no evidence references")
    dimensions_claims = extraction.get("dimensions") or []
    count_claims = extraction.get("counts") or []
    extraction_kind = str(extraction.get("object_kind") or "").strip().casefold()
    object_kind = extraction_kind if extraction_kind in {"wardrobe", "cabinet"} else "cabinet"
    assumptions: list[str] = []
    if object_kind != extraction_kind:
        assumptions.append("default_cabinet_archetype")

    dimensions = {}
    for axis, (default_value, default_rule) in _DEFAULT_DIMENSIONS_MM.items():
        claim = _best_claim(dimensions_claims, expected_key=axis, allowed_refs=allowed_refs)
        if claim is None:
            assumptions.append(default_rule)
            dimensions[axis] = {"value_mm": default_value, "basis": "assumption", "evidence_refs": [], "assumption_rule": default_rule}
        else:
            dimensions[axis] = {"value_mm": claim["value"], "basis": "evidence", "evidence_refs": list(claim["evidence_refs"]), "assumption_rule": None}

    counts = {}
    for name, (default_value, default_rule) in _DEFAULT_COUNTS.items():
        claim = _best_claim(count_claims, expected_key=name, allowed_refs=allowed_refs)
        if claim is None or int(float(claim["value"])) != float(claim["value"]):
            assumptions.append(default_rule)
            counts[name] = {"value": default_value, "basis": "assumption", "evidence_refs": [], "assumption_rule": default_rule}
        else:
            counts[name] = {"value": int(float(claim["value"])), "basis": "evidence", "evidence_refs": list(claim["evidence_refs"]), "assumption_rule": None}

    roles = []
    seen_roles: set[str] = set()
    for claim in extraction.get("material_roles") or []:
        if not isinstance(claim, Mapping):
            continue
        role = str(claim.get("role") or "")
        refs = claim.get("evidence_refs")
        if role in seen_roles or role not in {"visible_facade", "internal_carcass", "backing", "finish", "hardware"}:
            continue
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref in allowed_refs for ref in refs):
            continue
        if not isinstance(claim.get("source_name"), str) or not claim["source_name"]:
            continue
        if not isinstance(claim.get("family"), str) or not claim["family"]:
            continue
        seen_roles.add(role)
        roles.append({
            "role": role, "source_name": claim["source_name"], "family": claim["family"],
            "specification": dict(claim.get("specification") or {}),
            "quantity": claim.get("quantity"), "unit": claim.get("unit"),
            "evidence_refs": list(refs),
        })
    preview_refs = sorted(ref for ref in allowed_refs if ref.startswith("storage://"))
    if not preview_refs:
        raise ValueError("object-to-estimate input has no full-page artifact")
    brief = {
        "contract_version": OBJECT_TO_ESTIMATE_V1, "input_id": str(input_row["input_id"]),
        "object_input_revision": int(input_row.get("object_input_revision") or 1),
        "run_id": str(payload["run_id"]), "company_id": str(payload["company_id"]),
        "object_id": str(object_payload["object_id"]), "object_name": str(object_payload.get("object_name") or "Object"),
        "quantity": object_payload.get("quantity") or 1, "status": "ready", "object_kind": object_kind,
        "dimensions_mm": dimensions, "counts": counts, "material_roles": roles,
        "assumptions": list(dict.fromkeys(assumptions)), "primary_preview_ref": preview_refs[0],
    }
    return validate_object_to_estimate_v1(brief)
