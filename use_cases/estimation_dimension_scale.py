"""Bounded physical-scale guard for unitless Estimation drawings.

The guard is deliberately narrower than a CAD unit detector.  It examines only
OCR dimension literals already present in the immutable Dimension Graph and
locks centimetres when treating those readings as millimetres would make a
furniture object implausibly small.  Explicit source units always win.
"""

from __future__ import annotations

from typing import Any, Mapping


DIMENSION_SCALE_GATE_V1 = "estimation_dimension_scale_gate_v1"
_FURNITURE_CANDIDATE_MIN = 40.0
_FURNITURE_CANDIDATE_MAX = 400.0
_MIN_WITNESS_COUNT = 3


def build_dimension_scale_gate(*, dimension_graph: Mapping[str, Any]) -> dict[str, Any]:
    """Return an auditable unit constraint, or no constraint when evidence is weak.

    A naked numeric OCR token is never enough.  The constraint is emitted only
    for a unitless object with three or more dimension candidates in the
    bounded furniture range.  It is a product safety policy, not a claim that
    the source printed centimetres.
    """
    dimensions = [
        item for item in dimension_graph.get("dimension_numbers") or []
        if isinstance(item, Mapping)
    ]
    printed_units = sorted({
        str(item.get("printed_unit") or "").casefold()
        for item in dimensions
        if str(item.get("printed_unit") or "").casefold() in {"mm", "cm", "m"}
    })
    witnesses = sorted(
        (
            item for item in dimensions
            if not item.get("printed_unit")
            and _FURNITURE_CANDIDATE_MIN <= float(item.get("numeric_value") or 0) <= _FURNITURE_CANDIDATE_MAX
            and item.get("evidence_refs")
        ),
        key=lambda item: (-float(item.get("numeric_value") or 0), str(item.get("dimension_id") or "")),
    )
    decision: dict[str, Any] | None = None
    if not printed_units and len(witnesses) >= _MIN_WITNESS_COUNT:
        selected = witnesses[: min(len(witnesses), 8)]
        decision = {
            "required_unit": "cm",
            "basis": "unitless_furniture_scale_guard",
            "evidence_refs": [
                str(ref)
                for item in selected
                for ref in item.get("evidence_refs") or []
                if str(ref)
            ],
            "candidate_values": [float(item["numeric_value"]) for item in selected],
            "reason": (
                "Unitless furniture-scale readings would produce a sub-400 mm "
                "object in millimetres; centimetres preserve a plausible physical scale."
            ),
        }
    return {
        "contract_version": DIMENSION_SCALE_GATE_V1,
        "dimension_graph_contract": str(dimension_graph.get("contract_version") or ""),
        "printed_units": printed_units,
        "decision": decision,
    }
