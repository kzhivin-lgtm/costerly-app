"""Deterministically link processed Price Source rows to Israel Reference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from use_cases.material_identity_resolution import (
    build_material_identity_index,
    resolve_material_identity,
)


_REFERENCE_DEPARTMENTS = {
    "Wood Sheets": ("wood",),
    "Solid Wood": ("wood",),
    "Wood Supplies": ("hardware", "consumable"),
    "Hardware": ("hardware",),
    "Glass": ("glass_stone_plastic",),
    "Plastics & Composites": ("glass_stone_plastic",),
    "Stone": ("stone",),
    "Metal Sheets": ("metal",),
    "Metal Profiles": ("metal",),
    "Metal Supplies": ("metal", "hardware", "consumable"),
    "Paints & Coatings": ("coating",),
    "Coating Supplies": ("coating", "consumable"),
}


@dataclass(frozen=True)
class PriceSourceReferenceLinkSummary:
    examined: int = 0
    linked: int = 0
    unresolved: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "examined": self.examined,
            "linked": self.linked,
            "unresolved": self.unresolved,
        }


def resolve_price_source_reference_links(
    client: Any,
    *,
    company_id: str,
    source_id: str,
    market_code: str = "IL",
) -> PriceSourceReferenceLinkSummary:
    """Link one imported source to matching Israel Reference materials.

    It is deliberately additive.  An unresolved row remains a valid company
    offer with a blue status, and an existing confirmed link is preserved.
    """
    rows = (
        client.table("company_price_source_rows")
        .select(
            "row_id,company_material_id,raw_description,normalized_name,evidence,"
            "reference_material_id"
        )
        .eq("company_id", company_id)
        .eq("source_id", source_id)
        .in_("result_status", ["new", "updated", "unchanged"])
        .execute()
        .data
        or []
    )
    material_ids = sorted({
        str(row.get("company_material_id") or "")
        for row in rows
        if row.get("company_material_id")
    })
    if not material_ids:
        return PriceSourceReferenceLinkSummary()

    company_materials = (
        client.table("company_material_items")
        .select("company_material_id,category,specifications,reference_material_id")
        .eq("company_id", company_id)
        .in_("company_material_id", material_ids)
        .execute()
        .data
        or []
    )
    company_by_id = {
        str(row.get("company_material_id") or ""): row
        for row in company_materials
    }
    reference_materials = (
        client.table("reference_materials")
        .select(
            "material_id,department,category_code,canonical_name,base_unit,"
            "specifications,active"
        )
        .eq("active", True)
        .execute()
        .data
        or []
    )
    reference_aliases = (
        client.table("reference_material_aliases")
        .select("material_id,market_code,alias_text,exact_identity,confidence,active")
        .eq("market_code", market_code)
        .eq("active", True)
        .execute()
        .data
        or []
    )
    index = build_material_identity_index(
        reference_materials,
        reference_aliases,
        market_code,
    )
    examined = linked = unresolved = 0
    for row in rows:
        company_material_id = str(row.get("company_material_id") or "")
        company_material = company_by_id.get(company_material_id)
        if not company_material:
            continue
        existing_link = str(
            row.get("reference_material_id")
            or company_material.get("reference_material_id")
            or ""
        ).strip()
        if existing_link:
            continue
        evidence = row.get("evidence")
        evidence = evidence if isinstance(evidence, Mapping) else {}
        specifications = {
            key: value
            for key, value in {
                **(evidence.get("identity_attributes") or {}),
                **(company_material.get("specifications") or {}),
            }.items()
            if value not in (None, "", 0, 0.0, [])
        }
        phrase = str(row.get("normalized_name") or row.get("raw_description") or "").strip()
        if not phrase:
            continue
        family = str(
            (company_material.get("specifications") or {}).get("material_family")
            or evidence.get("material_family")
            or ""
        ).strip()
        category = str(
            evidence.get("material_type")
            or company_material.get("category")
            or ""
        ).strip()
        resolution = resolve_material_identity(
            phrase=phrase,
            alternate_phrases=tuple(
                value
                for value in (
                    str(row.get("raw_description") or "").strip(),
                    family,
                )
                if value and value != phrase
            ),
            market_code=market_code,
            materials=reference_materials,
            reference_aliases=reference_aliases,
            specifications=specifications,
            material_family=family or None,
            candidate_departments=_REFERENCE_DEPARTMENTS.get(category, ()),
            material_identity_index=index,
        )
        examined += 1
        reference_material_id = str(resolution.selected_material_id or "").strip()
        if resolution.status != "resolved" or not reference_material_id:
            unresolved += 1
            continue
        client.table("company_material_items").update(
            {"reference_material_id": reference_material_id}
        ).eq("company_id", company_id).eq(
            "company_material_id", company_material_id
        ).is_("reference_material_id", "null").execute()
        client.table("company_price_source_rows").update(
            {
                "reference_material_id": reference_material_id,
                "identity_route": resolution.route,
                "identity_confidence": 100,
            }
        ).eq("row_id", row["row_id"]).execute()
        linked += 1
    return PriceSourceReferenceLinkSummary(
        examined=examined,
        linked=linked,
        unresolved=unresolved,
    )
