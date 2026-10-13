"""Publish material demands only. Labor, manufacturing and overhead are disabled."""

from __future__ import annotations

from typing import Any, Mapping

from agents.estimation_v3_material_facts_agent import ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION
from db.repositories import (
    fetch_estimation_fact_result,
    replace_rfq_estimate_lines_for_object,
    update_rfq_object_estimate_progress,
    update_rfq_object_estimate_totals,
)
from use_cases.estimation_v3_material_contract import validate_material_facts_v3


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
