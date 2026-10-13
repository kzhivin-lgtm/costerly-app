"""Immutable, material-only contract for Estimation V3.

This contract deliberately stops before pricing, purchasing, labor, overhead,
manufacturing, VAT and sale price. Those are deterministic downstream stages.
"""

from __future__ import annotations

from typing import Any, AbstractSet, Mapping


MATERIAL_FACTS_V3_VERSION = "estimation_material_facts_v3"
SPECIFICATION_KEYS = frozenset({
    "thickness_mm", "width_mm", "height_mm", "length_mm", "diameter_mm",
    "wall_thickness_mm", "profile_section", "species", "grade", "alloy",
    "metal_type", "temper", "finish", "surface", "color", "coating",
    "density_class", "fire_rating", "moisture_resistance", "supplier_sku",
})
COMPACT_PART_KEYS = ("id", "m", "q", "l", "w", "r")
_TOP_LEVEL_KEYS = frozenset({
    "contract_version", "input_id", "object_input_revision", "run_id",
    "company_id", "object_id", "object_name", "quantity", "status",
    "dimensions_mm", "materials", "parts", "review_items", "primary_preview_ref",
})
_FORBIDDEN_TERMS = frozenset({
    "price", "cost", "rate", "hour", "labor", "operation", "machine",
    "overhead", "vat", "markup", "sale", "route",
})
_VALID_UNITS = frozenset({"m²", "m", "mm", "kg", "l", "sheet", "piece"})


def _number(value: Any, *, positive: bool = False) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if not positive or number > 0 else None


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_name = str(key).casefold()
            if any(term in key_name for term in _FORBIDDEN_TERMS):
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _require_evidence(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(ref, str) and ref for ref in value):
        raise ValueError(f"{name} must contain one or more evidence refs")
    return list(value)


def validate_material_facts_v3(
    facts: Mapping[str, Any], *, allowed_material_families: AbstractSet[str],
) -> dict[str, Any]:
    """Validate the sole Agent-owned boundary of Estimation V3."""
    normalized = dict(_require_mapping(facts, "facts"))
    unknown = set(normalized) - _TOP_LEVEL_KEYS
    if unknown:
        raise ValueError(f"V3 material facts contain unsupported fields: {sorted(unknown)}")
    if normalized.get("contract_version") != MATERIAL_FACTS_V3_VERSION:
        raise ValueError("V3 material facts have an unsupported contract version")
    if _contains_forbidden_key(normalized):
        raise ValueError("V3 material facts must not contain pricing or production outputs")
    for field in ("input_id", "run_id", "company_id", "object_id", "object_name", "primary_preview_ref"):
        if not isinstance(normalized.get(field), str) or not normalized[field]:
            raise ValueError(f"V3 material facts require {field}")
    if not isinstance(normalized.get("object_input_revision"), int) or normalized["object_input_revision"] < 1:
        raise ValueError("V3 material facts require a positive object_input_revision")
    if _number(normalized.get("quantity"), positive=True) is None:
        raise ValueError("V3 material facts require a positive object quantity")
    if normalized.get("status") not in {"ready", "review_required", "failed"}:
        raise ValueError("V3 material facts have an unsupported status")

    dimensions = _require_mapping(normalized.get("dimensions_mm"), "dimensions_mm")
    if set(dimensions) - {"width", "depth", "height"}:
        raise ValueError("dimensions_mm contains unsupported values")
    normalized["dimensions_mm"] = {
        key: _number(dimensions.get(key), positive=True) for key in ("width", "depth", "height")
    }

    materials = normalized.get("materials")
    if not isinstance(materials, list):
        raise ValueError("materials must be a list")
    known_material_ids: set[str] = set()
    for index, raw in enumerate(materials, start=1):
        material = _require_mapping(raw, f"materials[{index}]")
        required = {"requirement_id", "source_name", "family", "specification", "quantity", "unit", "evidence_refs"}
        if set(material) != required:
            raise ValueError(f"materials[{index}] has an invalid shape")
        requirement_id = material.get("requirement_id")
        if not isinstance(requirement_id, str) or not requirement_id or requirement_id in known_material_ids:
            raise ValueError(f"materials[{index}] has an invalid requirement_id")
        known_material_ids.add(requirement_id)
        if not isinstance(material.get("source_name"), str) or not material["source_name"]:
            raise ValueError(f"materials[{index}] has no source_name")
        if material.get("family") not in allowed_material_families:
            raise ValueError(f"materials[{index}] family is not supported")
        if _number(material.get("quantity"), positive=True) is None:
            raise ValueError(f"materials[{index}] must have a positive quantity")
        if material.get("unit") not in _VALID_UNITS:
            raise ValueError(f"materials[{index}] unit is not supported")
        specification = _require_mapping(material.get("specification"), f"materials[{index}].specification")
        if set(specification) - SPECIFICATION_KEYS:
            raise ValueError(f"materials[{index}] specification contains unsupported fields")
        _require_evidence(material.get("evidence_refs"), f"materials[{index}].evidence_refs")

    parts = normalized.get("parts")
    if not isinstance(parts, list):
        raise ValueError("parts must be a list")
    part_ids: set[str] = set()
    for index, raw in enumerate(parts, start=1):
        part = _require_mapping(raw, f"parts[{index}]")
        required = {"part_id", "material_requirement_id", "quantity", "length_mm", "width_mm", "rotation_allowed", "evidence_refs"}
        if set(part) != required:
            raise ValueError(f"parts[{index}] has an invalid shape")
        part_id = part.get("part_id")
        if not isinstance(part_id, str) or not part_id or part_id in part_ids:
            raise ValueError(f"parts[{index}] has an invalid part_id")
        part_ids.add(part_id)
        if part.get("material_requirement_id") not in known_material_ids:
            raise ValueError(f"parts[{index}] refers to an unknown material")
        for dimension in ("quantity", "length_mm", "width_mm"):
            if _number(part.get(dimension), positive=True) is None:
                raise ValueError(f"parts[{index}] {dimension} must be positive")
        if not isinstance(part.get("rotation_allowed"), bool):
            raise ValueError(f"parts[{index}] rotation_allowed must be boolean")
        _require_evidence(part.get("evidence_refs"), f"parts[{index}].evidence_refs")

    reviews = normalized.get("review_items")
    if not isinstance(reviews, list):
        raise ValueError("review_items must be a list")
    for index, raw in enumerate(reviews, start=1):
        review = _require_mapping(raw, f"review_items[{index}]")
        if set(review) != {"code", "severity", "path", "message", "evidence_refs"}:
            raise ValueError(f"review_items[{index}] has an invalid shape")
        if review.get("severity") not in {"warning", "blocking"}:
            raise ValueError(f"review_items[{index}] severity is invalid")
        if not all(isinstance(review.get(key), str) and review[key] for key in ("code", "path", "message")):
            raise ValueError(f"review_items[{index}] is incomplete")
        _require_evidence(review.get("evidence_refs"), f"review_items[{index}].evidence_refs")

    if normalized["status"] == "ready" and (not materials or any(item.get("severity") == "blocking" for item in reviews)):
        raise ValueError("ready V3 material facts require complete, non-blocking material demands")
    return normalized
