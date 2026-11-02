"""Bounded construction brief between evidence and approximate BOM.

The brief is deliberately not a production drawing.  It keeps cited facts
separate from a small, versioned list of construction assumptions so a rough
architectural sketch can still become an auditable material estimate.
"""

from __future__ import annotations

from typing import Any, Mapping


OBJECT_TO_ESTIMATE_V1 = "estimation_object_to_estimate_v1"

_OBJECT_KINDS = frozenset({"wardrobe", "cabinet"})
_DIMENSION_NAMES = frozenset({"width", "depth", "height"})
_COUNT_NAMES = frozenset({"bay_count", "door_count", "shelf_count_per_bay"})
_MATERIAL_ROLES = frozenset({"visible_facade", "internal_carcass", "backing", "finish", "hardware"})
_ASSUMPTION_RULES = frozenset({
    "default_carcass_thickness_18mm",
    "default_backing_thickness_3mm",
    "default_single_shelf_per_bay",
    "derived_equal_bay_width",
    "derived_equal_door_width",
    "default_internal_melamine_faced_particleboard",
    "default_backing_hardboard",
    "default_visible_facade_mdf",
})
_FORBIDDEN_TERMS = frozenset({
    "price", "cost", "rate", "hour", "labor", "operation", "machine",
    "overhead", "vat", "markup", "sale", "route",
})


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            any(term in str(key).casefold() for term in _FORBIDDEN_TERMS)
            or _contains_forbidden_key(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def _evidence_refs(value: Any, *, name: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(ref, str) and ref for ref in value):
        raise ValueError(f"{name} requires one or more evidence refs")
    return list(value)


def _measurement(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"value_mm", "basis", "evidence_refs", "assumption_rule"}:
        raise ValueError(f"{name} has an invalid shape")
    number = _positive_number(value.get("value_mm"))
    if number is None:
        raise ValueError(f"{name}.value_mm must be positive")
    basis = value.get("basis")
    if basis == "evidence":
        if value.get("assumption_rule") is not None:
            raise ValueError(f"{name} evidence may not carry an assumption rule")
        return {"value_mm": number, "basis": basis, "evidence_refs": _evidence_refs(value.get("evidence_refs"), name=name), "assumption_rule": None}
    if basis == "assumption":
        rule = value.get("assumption_rule")
        if rule not in _ASSUMPTION_RULES:
            raise ValueError(f"{name} uses an unsupported assumption rule")
        if value.get("evidence_refs") not in ([], None):
            raise ValueError(f"{name} assumption may not claim evidence refs")
        return {"value_mm": number, "basis": basis, "evidence_refs": [], "assumption_rule": rule}
    raise ValueError(f"{name}.basis is unsupported")


def _count(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"value", "basis", "evidence_refs", "assumption_rule"}:
        raise ValueError(f"{name} has an invalid shape")
    number = _positive_number(value.get("value"))
    if number is None or int(number) != number:
        raise ValueError(f"{name}.value must be a positive integer")
    normalized = _measurement(
        {"value_mm": number, "basis": value.get("basis"), "evidence_refs": value.get("evidence_refs"), "assumption_rule": value.get("assumption_rule")},
        name=name,
    )
    return {"value": int(number), **{key: normalized[key] for key in ("basis", "evidence_refs", "assumption_rule")}}


def validate_object_to_estimate_v1(brief: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a cited, material-only construction brief."""
    if not isinstance(brief, Mapping):
        raise ValueError("object-to-estimate brief must be an object")
    if _contains_forbidden_key(brief):
        raise ValueError("object-to-estimate brief must not contain pricing or production outputs")
    required = {
        "contract_version", "input_id", "object_input_revision", "run_id", "company_id",
        "object_id", "object_name", "quantity", "status", "object_kind", "dimensions_mm",
        "counts", "material_roles", "assumptions", "review_items", "primary_preview_ref",
    }
    if set(brief) != required:
        raise ValueError("object-to-estimate brief has unsupported fields")
    if brief.get("contract_version") != OBJECT_TO_ESTIMATE_V1:
        raise ValueError("object-to-estimate brief has unsupported contract version")
    for key in ("input_id", "run_id", "company_id", "object_id", "object_name", "primary_preview_ref"):
        if not isinstance(brief.get(key), str) or not brief[key]:
            raise ValueError(f"object-to-estimate brief requires {key}")
    if not isinstance(brief.get("object_input_revision"), int) or brief["object_input_revision"] < 1:
        raise ValueError("object-to-estimate brief requires a positive object_input_revision")
    if _positive_number(brief.get("quantity")) is None:
        raise ValueError("object-to-estimate brief requires a positive quantity")
    if brief.get("status") not in {"ready", "review_required", "failed"}:
        raise ValueError("object-to-estimate brief has unsupported status")
    if brief.get("object_kind") not in _OBJECT_KINDS:
        raise ValueError("object-to-estimate brief has unsupported object_kind")

    dimensions = brief.get("dimensions_mm")
    if not isinstance(dimensions, Mapping) or set(dimensions) != _DIMENSION_NAMES:
        raise ValueError("dimensions_mm must contain width, depth and height")
    normalized_dimensions = {name: _measurement(dimensions[name], name=f"dimensions_mm.{name}") for name in sorted(_DIMENSION_NAMES)}

    counts = brief.get("counts")
    if not isinstance(counts, Mapping) or set(counts) - _COUNT_NAMES:
        raise ValueError("counts contains unsupported values")
    normalized_counts = {name: _count(value, name=f"counts.{name}") for name, value in sorted(counts.items())}

    roles = brief.get("material_roles")
    if not isinstance(roles, list):
        raise ValueError("material_roles must be a list")
    normalized_roles = []
    seen_roles: set[str] = set()
    for index, value in enumerate(roles, start=1):
        if not isinstance(value, Mapping) or set(value) != {"role", "source_name", "family", "specification", "evidence_refs"}:
            raise ValueError(f"material_roles[{index}] has an invalid shape")
        role = value.get("role")
        if role not in _MATERIAL_ROLES or role in seen_roles:
            raise ValueError(f"material_roles[{index}] has an invalid role")
        seen_roles.add(role)
        if not isinstance(value.get("source_name"), str) or not value["source_name"]:
            raise ValueError(f"material_roles[{index}] requires source_name")
        if not isinstance(value.get("family"), str) or not value["family"]:
            raise ValueError(f"material_roles[{index}] requires family")
        if not isinstance(value.get("specification"), Mapping):
            raise ValueError(f"material_roles[{index}] requires specification")
        normalized_roles.append({
            "role": role, "source_name": value["source_name"], "family": value["family"],
            "specification": dict(value["specification"]),
            "evidence_refs": _evidence_refs(value.get("evidence_refs"), name=f"material_roles[{index}]"),
        })

    assumptions = brief.get("assumptions")
    if not isinstance(assumptions, list) or not all(isinstance(rule, str) and rule in _ASSUMPTION_RULES for rule in assumptions):
        raise ValueError("assumptions contains an unsupported rule")
    if len(set(assumptions)) != len(assumptions):
        raise ValueError("assumptions must not repeat a rule")

    reviews = brief.get("review_items")
    if not isinstance(reviews, list):
        raise ValueError("review_items must be a list")
    for index, value in enumerate(reviews, start=1):
        if not isinstance(value, Mapping) or set(value) != {"code", "severity", "path", "message", "evidence_refs"}:
            raise ValueError(f"review_items[{index}] has an invalid shape")
        if value.get("severity") not in {"warning", "blocking"}:
            raise ValueError(f"review_items[{index}] has an invalid severity")
        if not all(isinstance(value.get(key), str) and value[key] for key in ("code", "path", "message")):
            raise ValueError(f"review_items[{index}] is incomplete")
        _evidence_refs(value.get("evidence_refs"), name=f"review_items[{index}]")

    if brief["status"] == "ready" and any(review.get("severity") == "blocking" for review in reviews):
        raise ValueError("ready object-to-estimate brief may not have blocking review items")
    return {
        **dict(brief), "quantity": _positive_number(brief["quantity"]),
        "dimensions_mm": normalized_dimensions, "counts": normalized_counts,
        "material_roles": normalized_roles, "assumptions": list(assumptions),
        "review_items": [dict(item) for item in reviews],
    }
