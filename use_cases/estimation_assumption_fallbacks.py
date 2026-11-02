"""Persist non-blocking material-price assumptions as Staff research work."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from db.repositories import (
    create_or_update_catalog_gap_job,
    fetch_active_estimate_case_assumptions,
    insert_catalog_gap_job_occurrence,
    insert_estimate_case_assumption,
    update_estimate_case_assumption,
)


def _gap_kind(reason_code: str) -> str:
    if reason_code == "material_pricing_key_incomplete":
        return "material_identity"
    if reason_code == "no_company_or_israel_candidate":
        return "material_supply"
    return "price_source"


def _gap_fingerprint(*, gap_type: str, material: Mapping[str, Any]) -> str:
    canonical = {
        "gap_type": gap_type,
        "market_code": "IL",
        "source_name": str(material.get("source_name") or "").strip().casefold(),
        "family": str(material.get("material_family") or "").strip().casefold(),
        "specification": dict(material.get("specification") or {}),
    }
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _existing_by_requirement(rows: list[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        chosen = row.get("chosen_assumption") or {}
        if not isinstance(chosen, Mapping):
            continue
        requirement_id = str(chosen.get("material_requirement_id") or "")
        object_id = str(row.get("object_id") or "")
        if object_id and requirement_id:
            result[(object_id, requirement_id)] = row
    return result


def persist_material_assumption_fallbacks(
    *, client: Any, estimate_id: str, company_id: str,
    facts_by_object: Mapping[str, Mapping[str, Any]], plan_snapshot: Mapping[str, Any],
) -> int:
    """Create or update the private C/I/A follow-up for every priced A line.

    This does not change the customer-visible estimate or gate its result. A
    subsequent plan rebuild updates the same case assumption for the same
    object requirement, while the catalog job remains globally deduplicated.
    """
    fallbacks = [
        dict(row) for row in plan_snapshot.get("assumption_fallbacks") or []
        if isinstance(row, Mapping) and str(row.get("object_id") or "")
        and str(row.get("material_requirement_id") or "")
    ]
    existing = _existing_by_requirement(fetch_active_estimate_case_assumptions(client, estimate_id=estimate_id))
    cost_by_requirement = {
        (str(row.get("object_id") or ""), str(row.get("material_requirement_id") or "")): row.get("cost_ex_vat")
        for row in plan_snapshot.get("object_material_costs") or []
        if isinstance(row, Mapping)
    }
    persisted = 0
    for fallback in fallbacks:
        object_id = str(fallback["object_id"])
        requirement_id = str(fallback["material_requirement_id"])
        reason_code = str(fallback.get("reason_code") or "")
        gap_type = _gap_kind(reason_code)
        fingerprint = _gap_fingerprint(gap_type=gap_type, material=fallback)
        source_name = str(fallback.get("source_name") or fallback.get("material_family") or "Material").strip()
        statement = f"{source_name} ({fallback.get('material_family') or 'material'})"[:2000]
        gap_job_id = create_or_update_catalog_gap_job(
            client,
            gap_fingerprint=fingerprint,
            gap_type=gap_type,
            market_code="IL",
            normalized_statement=statement,
            route_critical_attributes={
                "material_family": fallback.get("material_family"),
                "specification": dict(fallback.get("specification") or {}),
                "selection_key": fallback.get("selection_key"),
            },
        )
        assumption_price = dict(fallback.get("assumption_price") or {})
        chosen = {
            "material_requirement_id": requirement_id,
            "source_name": source_name,
            "material_family": fallback.get("material_family"),
            "specification": dict(fallback.get("specification") or {}),
            "reason_code": reason_code,
            "selection_key": fallback.get("selection_key"),
            "assumption_price": assumption_price,
        }
        impact = {
            "material_cost_ex_vat": cost_by_requirement.get((object_id, requirement_id)),
            "quantity_per_item": fallback.get("quantity_per_item"),
            "unit": fallback.get("unit"),
        }
        fact_result_id = str((facts_by_object.get(object_id) or {}).get("fact_result_id") or "") or None
        current = existing.get((object_id, requirement_id))
        if current:
            update_estimate_case_assumption(
                client,
                assumption_id=str(current["assumption_id"]),
                gap_job_id=gap_job_id,
                fact_result_id=fact_result_id,
                chosen_assumption=chosen,
                research_sources=list(assumption_price.get("source_candidates") or []),
                calculation_impact=impact,
                confidence=float(assumption_price.get("confidence") or 0),
            )
        else:
            assumption_id = insert_estimate_case_assumption(
                client,
                estimate_id=estimate_id,
                object_id=object_id,
                company_id=company_id,
                fact_result_id=fact_result_id,
                gap_job_id=gap_job_id,
                assumption_kind=gap_type,
                chosen_assumption=chosen,
                research_sources=list(assumption_price.get("source_candidates") or []),
                calculation_impact=impact,
                confidence=float(assumption_price.get("confidence") or 0),
            )
            insert_catalog_gap_job_occurrence(
                client, gap_job_id=gap_job_id, assumption_id=assumption_id, company_id=company_id,
            )
        persisted += 1
    return persisted
