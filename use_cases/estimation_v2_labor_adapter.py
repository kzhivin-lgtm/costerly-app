"""Bounded adapter from validated Estimation v2 facts to Labor Engine input."""

from __future__ import annotations

from typing import Any, Mapping

from use_cases.estimation_v2_composition import OBJECT_FACTS_CONTRACT_VERSION


LABOR_INPUT_CONTRACT_VERSION = "labor_input_v1"


def build_labor_input_v1(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Translate validated ready facts without inventing operations or drivers."""
    if facts.get("contract_version") != OBJECT_FACTS_CONTRACT_VERSION:
        raise ValueError("Labor adapter requires estimation_object_facts_v1")
    if facts.get("status") != "ready":
        raise ValueError("Labor adapter requires ready Object Facts")
    template = facts.get("template")
    if not isinstance(template, Mapping) or not template.get("code"):
        raise ValueError("Labor adapter requires a resolved construction template")
    dimensions = facts.get("dimensions_mm")
    materials = facts.get("materials")
    features = facts.get("features")
    if not isinstance(dimensions, Mapping):
        raise ValueError("Labor adapter requires dimensions_mm")
    if not isinstance(materials, list) or not materials:
        raise ValueError("Labor adapter requires material requirements")
    if not isinstance(features, Mapping):
        raise ValueError("Labor adapter requires features")

    return {
        "contract_version": LABOR_INPUT_CONTRACT_VERSION,
        "object_id": facts.get("object_id"),
        "quantity": facts.get("quantity"),
        "template_code": template["code"],
        "template_confidence": template.get("confidence"),
        "dimensions_mm": dict(dimensions),
        "materials": [
            {
                "requirement_id": material.get("requirement_id"),
                "family": material.get("family"),
                "specification": dict(material.get("specification") or {}),
                "quantity": material.get("quantity"),
                "unit": material.get("unit"),
                "evidence_refs": list(material.get("evidence_refs") or []),
            }
            for material in materials
            if isinstance(material, Mapping)
        ],
        "features": dict(features),
        "construction_profile": str(
            features.get("construction_profile") or "panel_screw_standard"
        ),
        "source_facts": list(facts.get("source_facts") or []),
    }
