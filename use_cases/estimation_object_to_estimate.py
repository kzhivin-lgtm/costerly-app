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
_UNIT_NORMALISATION_MIN_IMPLAUSIBLE_MM = 50_000
_UNIT_NORMALISATION_MAX_IMPLAUSIBLE_MM = 500_000


def _normalised_phrase(value: Any) -> str:
    return " ".join(str(value or "").casefold().replace("_", " ").split())


def _is_formica(claim: Mapping[str, Any]) -> bool:
    return "formica" in _normalised_phrase(claim.get("source_name")) or "formica" in _normalised_phrase(claim.get("family"))


def _is_paint(claim: Mapping[str, Any]) -> bool:
    source = _normalised_phrase(claim.get("source_name"))
    family = _normalised_phrase(claim.get("family"))
    return any(token in source or token in family for token in ("paint", "nirlat", "lacquer", "stain", "color"))


def _formica_specification(specification: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only ordinary LDSP attributes when Formica is intentionally simplified."""
    result: dict[str, Any] = {}
    for key in ("thickness_mm", "thickness", "decor", "colour", "color"):
        value = specification.get(key)
        if value not in (None, "", [], {}):
            result[key] = value
    return result


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


def _needs_unitless_centimetre_normalisation(
    claims: Mapping[str, Mapping[str, Any] | None],
) -> bool:
    """Detect the model's 100x unitless-drawing conversion error conservatively.

    The source values remain cited. The conversion itself is recorded as a
    named construction assumption because a unitless drawing cannot prove it.
    Requiring two implausible cabinet axes prevents a single large legitimate
    installation dimension from being silently rescaled.
    """
    values = [
        _positive(claim.get("value"))
        for claim in claims.values()
        if claim is not None
    ]
    implausible = [
        value for value in values
        if value is not None
        and _UNIT_NORMALISATION_MIN_IMPLAUSIBLE_MM <= value <= _UNIT_NORMALISATION_MAX_IMPLAUSIBLE_MM
    ]
    return len(implausible) >= 2


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

    selected_dimension_claims = {
        axis: _best_claim(dimensions_claims, expected_key=axis, allowed_refs=allowed_refs)
        for axis in _DEFAULT_DIMENSIONS_MM
    }
    normalise_unitless_centimetres = _needs_unitless_centimetre_normalisation(selected_dimension_claims)
    if normalise_unitless_centimetres:
        assumptions.append("unitless_technical_drawing_centimetre_interpretation")

    dimensions = {}
    for axis, (default_value, default_rule) in _DEFAULT_DIMENSIONS_MM.items():
        claim = selected_dimension_claims[axis]
        if claim is None:
            assumptions.append(default_rule)
            dimensions[axis] = {"value_mm": default_value, "basis": "assumption", "evidence_refs": [], "assumption_rule": default_rule}
        else:
            value_mm = float(claim["value"])
            if normalise_unitless_centimetres and value_mm >= _UNIT_NORMALISATION_MIN_IMPLAUSIBLE_MM:
                value_mm /= 100
            dimensions[axis] = {"value_mm": value_mm, "basis": "evidence", "evidence_refs": list(claim["evidence_refs"]), "assumption_rule": None}

    counts = {}
    for name, (default_value, default_rule) in _DEFAULT_COUNTS.items():
        claim = _best_claim(count_claims, expected_key=name, allowed_refs=allowed_refs)
        if claim is None or int(float(claim["value"])) != float(claim["value"]):
            assumptions.append(default_rule)
            counts[name] = {"value": default_value, "basis": "assumption", "evidence_refs": [], "assumption_rule": default_rule}
        else:
            counts[name] = {"value": int(float(claim["value"])), "basis": "evidence", "evidence_refs": list(claim["evidence_refs"]), "assumption_rule": None}

    roles = []
    seen_structural_roles: set[str] = set()
    seen_auxiliary_roles: set[tuple[str, str, str]] = set()
    for claim in extraction.get("material_roles") or []:
        if not isinstance(claim, Mapping):
            continue
        role = str(claim.get("role") or "")
        refs = claim.get("evidence_refs")
        if role not in {"visible_facade", "internal_carcass", "backing", "finish", "hardware"}:
            continue
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref in allowed_refs for ref in refs):
            continue
        if not isinstance(claim.get("source_name"), str) or not claim["source_name"]:
            continue
        if not isinstance(claim.get("family"), str) or not claim["family"]:
            continue
        family = str(claim["family"])
        specification = dict(claim.get("specification") or {})
        if _is_formica(claim):
            family = "melamine_faced_particleboard"
            specification = _formica_specification(specification)
            if "formica_as_melamine_faced_particleboard" not in assumptions:
                assumptions.append("formica_as_melamine_faced_particleboard")
        if _is_paint(claim):
            if role != "finish" and "paint_is_finish_not_board" not in assumptions:
                assumptions.append("paint_is_finish_not_board")
            role = "finish"
            family = "paint_lacquer_stain"
            # A board specification accidentally attached to a paint name is
            # not a paint purchase specification.
            specification = {
                key: value for key, value in specification.items()
                if key in {"colour", "color", "finish", "paint_type"}
            }
        if role in {"visible_facade", "internal_carcass", "backing"}:
            if role in seen_structural_roles:
                continue
            seen_structural_roles.add(role)
        else:
            auxiliary_key = (role, _normalised_phrase(claim["source_name"]), family)
            if auxiliary_key in seen_auxiliary_roles:
                continue
            seen_auxiliary_roles.add(auxiliary_key)
        roles.append({
            "role": role, "source_name": claim["source_name"], "family": family,
            "specification": specification,
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
