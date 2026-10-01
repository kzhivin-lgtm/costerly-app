"""Adapter from the universal Estimation plan to the Labor calculator."""

from __future__ import annotations

from typing import Any, Mapping

from use_cases.estimation_v2_composition import OBJECT_FACTS_CONTRACT_VERSION


LABOR_INPUT_CONTRACT_VERSION = "labor_input_v2"


def build_labor_input(facts: Mapping[str, Any]) -> dict[str, Any]:
    if facts.get("contract_version") != OBJECT_FACTS_CONTRACT_VERSION:
        raise ValueError(f"Labor adapter requires {OBJECT_FACTS_CONTRACT_VERSION}")
    materials = facts.get("materials")
    operations = facts.get("labor_operations")
    if not isinstance(materials, list):
        materials = []
    if not isinstance(operations, list) or not operations:
        raise ValueError("Labor adapter requires a fabrication operation plan")
    return {
        "contract_version": LABOR_INPUT_CONTRACT_VERSION,
        "object_id": facts.get("object_id"),
        "quantity": facts.get("quantity"),
        "dimensions_mm": dict(facts.get("dimensions_mm") or {}),
        "materials": [dict(row) for row in materials if isinstance(row, Mapping)],
        "labor_operations": [dict(row) for row in operations if isinstance(row, Mapping)],
        "source_facts": list(facts.get("source_facts") or []),
    }
