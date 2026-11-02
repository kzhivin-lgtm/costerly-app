"""Mandatory, auditable price fallback for an unresolved material demand.

This contract holds a short user-visible rationale, not private model
reasoning.  An assumption can be weak, but it may never make an estimate
material line unpriced.
"""

from __future__ import annotations

from typing import Any, Mapping


ASSUMPTION_PRICE_V1 = "estimation_assumption_price_v1"
_BASIS_KINDS = frozenset({
    "israel_listing", "global_listing_projected_to_israel",
    "analogous_material", "estimator_allowance",
})
_UNITS = frozenset({"sheet", "piece", "m²", "m", "kg", "l", "set"})


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _nonnegative_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def validate_assumption_price_v1(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a complete A price that can enter project purchasing.

    Final project estimates are in ILS. A Global source may be retained in
    ``source_candidates``, but its projection must already yield a final ILS
    amount before this value is accepted by Material Engine orchestration.
    """
    if not isinstance(value, Mapping):
        raise ValueError("assumption price must be an object")
    required = {
        "contract_version", "material_requirement_id", "amount", "currency",
        "unit", "confidence", "basis_kind", "rationale", "source_candidates",
    }
    if set(value) != required:
        raise ValueError("assumption price has unsupported fields")
    if value.get("contract_version") != ASSUMPTION_PRICE_V1:
        raise ValueError("assumption price has unsupported contract version")
    if not isinstance(value.get("material_requirement_id"), str) or not value["material_requirement_id"]:
        raise ValueError("assumption price requires material_requirement_id")
    amount = _positive_number(value.get("amount"))
    if amount is None:
        raise ValueError("assumption price amount must be positive")
    if value.get("currency") != "ILS":
        raise ValueError("assumption price must be normalized to ILS")
    if value.get("unit") not in _UNITS:
        raise ValueError("assumption price has unsupported unit")
    confidence = _nonnegative_number(value.get("confidence"))
    if confidence is None or confidence > 100:
        raise ValueError("assumption price confidence must be in 0..100")
    if value.get("basis_kind") not in _BASIS_KINDS:
        raise ValueError("assumption price has unsupported basis_kind")
    rationale = value.get("rationale")
    if not isinstance(rationale, list) or not rationale or not all(isinstance(item, str) and item for item in rationale):
        raise ValueError("assumption price requires a non-empty reviewable rationale")
    sources = value.get("source_candidates")
    if not isinstance(sources, list) or not all(isinstance(item, Mapping) for item in sources):
        raise ValueError("assumption price source_candidates must be a list")
    if value["basis_kind"] == "estimator_allowance" and sources:
        raise ValueError("estimator allowance may not claim external source candidates")
    if value["basis_kind"] != "estimator_allowance" and not sources:
        raise ValueError("sourced assumption price requires source candidates")
    return {
        **dict(value), "amount": amount, "confidence": confidence,
        "rationale": list(rationale), "source_candidates": [dict(item) for item in sources],
    }
