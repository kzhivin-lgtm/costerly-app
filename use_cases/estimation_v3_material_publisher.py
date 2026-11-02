"""Publish material demands only. Labor, manufacturing and overhead are disabled."""

from __future__ import annotations

from typing import Any, Mapping

from agents.estimation_v3_material_facts_agent import ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION
from agents.estimation_v4_1_material_facts_agent import ESTIMATION_V4_2_MATERIAL_FACTS_AGENT_VERSION
from db.repositories import (
    fetch_estimation_fact_result,
    replace_rfq_estimate_lines_for_object,
    update_rfq_object_estimate_progress,
    update_rfq_object_estimate_totals,
)
from use_cases.estimation_v3_material_contract import (
    validate_material_facts_v3,
    validate_material_facts_v4_2,
)
from use_cases.estimation_object_to_estimate_runtime import ESTIMATION_APPROXIMATE_BOM_AGENT_VERSION


def publish_estimation_v3_material_object(
    *, client: Any, estimate_id: str, input_row: Mapping[str, Any],
    allowed_material_families: set[str],
) -> dict[str, Any]:
    """Persist net material norms. Material Engine allocates costs afterwards."""
    input_id = str(input_row.get("input_id") or "")
    object_id = str(input_row.get("object_id") or "")
    fact_result = fetch_estimation_fact_result(
        client, input_id=input_id, agent_version=ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION,
    )
    if not fact_result:
        raise RuntimeError("V3 material facts are missing after extraction")
    facts = validate_material_facts_v3(
        dict(fact_result.get("facts_payload") or {}),
        allowed_material_families=allowed_material_families,
    )
    object_quantity = float(facts["quantity"])
    lines = []
    for index, material in enumerate(facts["materials"], start=1):
        total_quantity = material.get("quantity")
        lines.append({
            "estimate_id": estimate_id,
            "object_id": object_id,
            "company_id": str(facts["company_id"]),
            "line_id": f"{object_id}_material_{index:04d}",
            "section": "material",
            "group_name": "Materials",
            "item_name": str(material["source_name"]),
            "catalog_match_query": str(material["family"]),
            "unit": material.get("unit"),
            "unit_cost": None,
            "quantity": (float(total_quantity) / object_quantity) if total_quantity is not None else None,
            "cost": None,
            "source": "estimation_v3_material_facts",
            "sort_order": index * 10,
            "needs_price": True,
            "needs_review": True,
            "confidence": None,
            "quantity_basis": "per_finished_item",
            "notes": "Material identified. Awaiting deterministic Material Plan.",
            "raw_agent_json": {
                "facts": dict(material),
                "v3_contract": facts["contract_version"],
                "review_items": facts["review_items"],
            },
        })
    replace_rfq_estimate_lines_for_object(
        client, estimate_id=estimate_id, object_id=object_id, lines=lines,
    )
    update_rfq_object_estimate_totals(
        client, estimate_id=estimate_id, object_id=object_id,
        self_cost_ex_vat=None, vat_amount=None, self_cost_total=None,
    )
    update_rfq_object_estimate_progress(
        client, estimate_id=estimate_id, object_id=object_id,
        status="review_required", progress_percent=100,
        progress_label="materials_pending_plan",
    )
    return {"status": "review_required", "material_line_count": len(lines)}


def publish_estimation_v4_1_material_object(
    *, client: Any, estimate_id: str, input_row: Mapping[str, Any],
    allowed_material_families: set[str],
) -> dict[str, Any]:
    """Publish V4.2's stable material-demand shape without changing costing."""
    input_id = str(input_row.get("input_id") or "")
    object_id = str(input_row.get("object_id") or "")
    fact_result = fetch_estimation_fact_result(
        client, input_id=input_id, agent_version=ESTIMATION_V4_2_MATERIAL_FACTS_AGENT_VERSION,
    )
    if not fact_result:
        raise RuntimeError("V4.2 material facts are missing after extraction")
    facts = validate_material_facts_v4_2(
        dict(fact_result.get("facts_payload") or {}), allowed_material_families=allowed_material_families,
    )
    object_quantity = float(facts["quantity"])
    lines = []
    for index, material in enumerate(facts["materials"], start=1):
        total_quantity = material.get("quantity")
        lines.append({
            "estimate_id": estimate_id, "object_id": object_id, "company_id": str(facts["company_id"]),
            "line_id": f"{object_id}_material_{index:04d}", "section": "material", "group_name": "Materials",
            "item_name": str(material["source_name"]), "catalog_match_query": str(material["family"]),
            "unit": material.get("unit"), "unit_cost": None,
            "quantity": (float(total_quantity) / object_quantity) if total_quantity is not None else None,
            "cost": None, "source": "estimation_v4_2_material_facts", "sort_order": index * 10,
            "needs_price": True, "needs_review": True, "confidence": None, "quantity_basis": "per_finished_item",
            "notes": "Material identified from bounded source evidence. Awaiting deterministic Material Plan.",
            "raw_agent_json": {
                "facts": dict(material), "v4_2_contract": facts["contract_version"],
                "review_items": facts["review_items"],
            },
        })
    replace_rfq_estimate_lines_for_object(client, estimate_id=estimate_id, object_id=object_id, lines=lines)
    update_rfq_object_estimate_totals(
        client, estimate_id=estimate_id, object_id=object_id,
        self_cost_ex_vat=None, vat_amount=None, self_cost_total=None,
    )
    update_rfq_object_estimate_progress(
        client, estimate_id=estimate_id, object_id=object_id,
        status="review_required", progress_percent=100, progress_label="materials_pending_plan",
    )
    return {"status": "review_required", "material_line_count": len(lines)}


def publish_estimation_approximate_bom_object(
    *, client: Any, estimate_id: str, input_row: Mapping[str, Any],
) -> dict[str, Any]:
    """Publish deterministic BOM material demands before project-wide costing."""
    input_id = str(input_row.get("input_id") or "")
    object_id = str(input_row.get("object_id") or "")
    fact_result = fetch_estimation_fact_result(
        client, input_id=input_id, agent_version=ESTIMATION_APPROXIMATE_BOM_AGENT_VERSION,
    )
    facts = dict((fact_result or {}).get("facts_payload") or {})
    if facts.get("contract_version") != "estimation_approximate_bom_v1":
        raise RuntimeError("approximate BOM is missing after composition")
    lines = []
    for index, material in enumerate(facts.get("materials") or [], start=1):
        if not isinstance(material, Mapping):
            continue
        lines.append({
            "estimate_id": estimate_id, "object_id": object_id, "company_id": str(facts["company_id"]),
            "line_id": f"{object_id}_material_{index:04d}", "section": "material", "group_name": "Materials",
            "item_name": str(material.get("source_name") or material.get("family") or "Material"),
            "catalog_match_query": str(material.get("family") or ""), "unit": None, "unit_cost": None,
            "quantity": None, "cost": None, "source": "estimation_approximate_bom_v1",
            "sort_order": index * 10, "needs_price": True, "needs_review": False, "confidence": None,
            "quantity_basis": "per_finished_item",
            "notes": "Approximate deterministic BOM. Awaiting estimate-wide Material Plan.",
            "raw_agent_json": {"facts": dict(material), "bom_contract": facts["contract_version"], "assumptions": facts.get("assumptions") or []},
        })
    if not lines:
        raise RuntimeError("approximate BOM has no material demands")
    replace_rfq_estimate_lines_for_object(client, estimate_id=estimate_id, object_id=object_id, lines=lines)
    update_rfq_object_estimate_totals(
        client, estimate_id=estimate_id, object_id=object_id,
        self_cost_ex_vat=None, vat_amount=None, self_cost_total=None,
    )
    update_rfq_object_estimate_progress(
        client, estimate_id=estimate_id, object_id=object_id,
        status="running", progress_percent=70, progress_label="approximate_bom_ready",
    )
    return {"status": "ready", "material_line_count": len(lines)}


def publish_estimation_assembly_bom_object(
    *, client: Any, estimate_id: str, input_row: Mapping[str, Any], agent_version: str,
) -> dict[str, Any]:
    """Publish V4.12 assembly-first demand lines before project-wide costing."""
    input_id = str(input_row.get("input_id") or "")
    object_id = str(input_row.get("object_id") or "")
    fact_result = fetch_estimation_fact_result(client, input_id=input_id, agent_version=agent_version)
    facts = dict((fact_result or {}).get("facts_payload") or {})
    if facts.get("contract_version") != "estimation_assembly_bom_v1":
        raise RuntimeError("assembly-first BOM is missing after composition")
    lines = []
    for index, material in enumerate(facts.get("materials") or [], start=1):
        if not isinstance(material, Mapping):
            continue
        lines.append({
            "estimate_id": estimate_id, "object_id": object_id, "company_id": str(facts["company_id"]),
            "line_id": f"{object_id}_material_{index:04d}", "section": "material", "group_name": "Materials",
            "item_name": str(material.get("source_name") or material.get("family") or "Material"),
            "catalog_match_query": str(material.get("family") or ""), "unit": None, "unit_cost": None,
            "quantity": None, "cost": None, "source": agent_version,
            "sort_order": index * 10, "needs_price": True, "needs_review": False, "confidence": None,
            "quantity_basis": "per_finished_item",
            "notes": "Structural approximate BOM. Awaiting estimate-wide Material Plan.",
            "raw_agent_json": {
                "facts": dict(material), "bom_contract": facts["contract_version"],
                "assemblies": facts.get("assemblies") or [], "assumptions": facts.get("assumptions") or [],
            },
        })
    if not lines:
        raise RuntimeError("assembly-first BOM has no material demands")
    replace_rfq_estimate_lines_for_object(client, estimate_id=estimate_id, object_id=object_id, lines=lines)
    update_rfq_object_estimate_totals(
        client, estimate_id=estimate_id, object_id=object_id,
        self_cost_ex_vat=None, vat_amount=None, self_cost_total=None,
    )
    update_rfq_object_estimate_progress(
        client, estimate_id=estimate_id, object_id=object_id,
        status="running", progress_percent=70, progress_label="assembly_bom_ready",
    )
    return {"status": "ready", "material_line_count": len(lines)}
