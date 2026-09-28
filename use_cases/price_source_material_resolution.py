from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

from use_cases.material_identity_resolution import (
    MaterialIdentityResolution,
    normalize_material_phrase,
    resolve_material_identity,
)


PRICE_SOURCE_REFERENCE_DEPARTMENTS = {
    "Wood Sheets": ("wood",),
    "Solid Wood": ("wood",),
    "Wood Supplies": ("hardware", "consumable"),
    "Glass": ("glass_stone_plastic",),
    "Metal Sheets": ("metal",),
    "Metal Profiles": ("metal",),
    "Metal Supplies": ("metal", "hardware", "consumable"),
    "Metal": ("metal",),
    "Paints & Coatings": ("coating",),
    "Coating Supplies": ("coating", "consumable"),
}


@dataclass(frozen=True)
class PriceSourceIdentityBatch:
    examined: int = 0
    resolved: int = 0
    shortlisted: int = 0
    new_identity_or_needs_review: int = 0
    unchanged: int = 0

    def as_summary(self) -> dict[str, int]:
        return asdict(self)


def _score(value: Decimal | int | float | str | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _candidate_payload(resolution: MaterialIdentityResolution) -> list[dict[str, Any]]:
    return [
        {
            "material_id": candidate.material_id,
            "score": _score(candidate.score),
            "route": candidate.route,
            "matched_alias": candidate.matched_alias,
        }
        for candidate in resolution.candidates
    ]


def _identity_confidence(resolution: MaterialIdentityResolution) -> float:
    if resolution.status == "resolved":
        if resolution.route == "compatible_hard_attributes":
            return 95.0
        return 100.0
    if resolution.candidates:
        return _score(resolution.candidates[0].score)
    return 0.0


def _load_resolution_index(
    client: Any,
    *,
    company_id: str,
    market_code: str,
) -> dict[str, Any]:
    versions = (
        client.table("material_resolver_versions")
        .select("resolver_version")
        .eq("market_code", market_code)
        .eq("status", "active")
        .limit(1)
        .execute()
    ).data or []
    if not versions:
        raise RuntimeError(f"No active material resolver for market {market_code}")
    return {
        "resolver_version": str(versions[0]["resolver_version"]),
        "materials": (
            client.table("reference_materials")
            .select(
                "material_id,department,category_code,canonical_name,base_unit,"
                "specifications,active"
            )
            .eq("active", True)
            .execute()
        ).data or [],
        "reference_aliases": (
            client.table("reference_material_aliases")
            .select(
                "material_id,market_code,alias_text,exact_identity,confidence,active"
            )
            .eq("market_code", market_code)
            .eq("active", True)
            .execute()
        ).data or [],
        "company_aliases": (
            client.table("company_material_aliases")
            .select("material_id,supplier_id,alias_text,resolver_key,active")
            .eq("company_id", company_id)
            .eq("active", True)
            .execute()
        ).data or [],
        "market_offers": (
            client.table("market_material_offers")
            .select("material_id,market_code,supplier_name,supplier_sku,status")
            .eq("market_code", market_code)
            .neq("status", "archived")
            .execute()
        ).data or [],
    }


def _source_supplier_maps(
    client: Any,
    *,
    company_id: str,
) -> tuple[dict[str, Mapping[str, Any]], dict[str, str]]:
    sources = (
        client.table("company_price_sources")
        .select("source_id,supplier_id")
        .eq("company_id", company_id)
        .execute()
    ).data or []
    suppliers = (
        client.table("company_suppliers")
        .select("supplier_id,supplier_name")
        .eq("company_id", company_id)
        .execute()
    ).data or []
    return (
        {str(row["source_id"]): row for row in sources},
        {str(row["supplier_id"]): str(row.get("supplier_name") or "") for row in suppliers},
    )


def resolve_price_source_material_identities(
    client: Any,
    *,
    company_id: str,
    source_id: str | None = None,
    row_id: str | None = None,
    market_code: str = "IL",
    force: bool = False,
) -> PriceSourceIdentityBatch:
    """Resolve active Price Source rows without repeating source extraction."""

    market = str(market_code or "").strip().upper()
    index = _load_resolution_index(client, company_id=company_id, market_code=market)
    resolver_version = index["resolver_version"]

    row_query = (
        client.table("company_price_source_rows")
        .select("*")
        .eq("company_id", company_id)
        .in_("result_status", ["new", "updated"])
    )
    if source_id:
        row_query = row_query.eq("source_id", source_id)
    if row_id:
        row_query = row_query.eq("row_id", row_id)
    rows = row_query.execute().data or []
    if not rows:
        return PriceSourceIdentityBatch()

    company_material_ids = sorted(
        {str(row.get("company_material_id")) for row in rows if row.get("company_material_id")}
    )
    materials = []
    if company_material_ids:
        materials = (
            client.table("company_material_items")
            .select(
                "company_material_id,reference_material_id,category,canonical_name,"
                "specifications,status"
            )
            .eq("company_id", company_id)
            .in_("company_material_id", company_material_ids)
            .execute()
        ).data or []
    material_by_id = {str(row["company_material_id"]): row for row in materials}
    source_by_id, supplier_name_by_id = _source_supplier_maps(
        client, company_id=company_id
    )

    prior_events = (
        client.table("material_identity_resolution_events")
        .select("source_row_id,resolver_version")
        .eq("company_id", company_id)
        .eq("resolver_version", resolver_version)
        .execute()
    ).data or []
    processed_rows = {
        str(event.get("source_row_id"))
        for event in prior_events
        if event.get("source_row_id")
    }

    examined = resolved = shortlisted = needs_review = unchanged = 0
    for row in rows:
        source_row_id = str(row["row_id"])
        if not force and source_row_id in processed_rows:
            unchanged += 1
            continue
        company_material_id = str(row.get("company_material_id") or "")
        company_material = material_by_id.get(company_material_id)
        if not company_material:
            continue
        examined += 1
        source = source_by_id.get(str(row.get("source_id") or ""), {})
        supplier_id = str(source.get("supplier_id") or "") or None
        supplier_name = supplier_name_by_id.get(str(supplier_id or ""), "")
        phrase = str(
            row.get("normalized_name")
            or row.get("raw_description")
            or company_material.get("canonical_name")
            or ""
        ).strip()
        existing_reference_id = str(company_material.get("reference_material_id") or "")
        if existing_reference_id:
            resolution = MaterialIdentityResolution(
                status="resolved",
                route="existing_company_material_link",
                normalized_phrase=normalize_material_phrase(phrase),
                selected_material_id=existing_reference_id,
                resolver_version=resolver_version,
            )
        else:
            material_type = str(
                (row.get("evidence") or {}).get("material_type")
                or company_material.get("category")
                or ""
            )
            resolution = resolve_material_identity(
                phrase=phrase,
                market_code=market,
                materials=index["materials"],
                reference_aliases=index["reference_aliases"],
                company_aliases=index["company_aliases"],
                market_offers=index["market_offers"],
                supplier_name=supplier_name,
                supplier_id=supplier_id,
                supplier_sku=str(row.get("raw_sku") or "") or None,
                specifications=company_material.get("specifications") or {},
                candidate_departments=PRICE_SOURCE_REFERENCE_DEPARTMENTS.get(
                    material_type, ()
                ),
            )

        candidates = _candidate_payload(resolution)
        identity_confidence = _identity_confidence(resolution)
        candidate_id = None
        if resolution.status == "resolved":
            reference_material_id = str(resolution.selected_material_id)
            if not existing_reference_id:
                linked_rows = client.table("company_material_items").update(
                    {"reference_material_id": reference_material_id}
                ).eq("company_id", company_id).eq(
                    "company_material_id", company_material_id
                ).is_("reference_material_id", "null").execute().data or []
                if not linked_rows:
                    current_rows = (
                        client.table("company_material_items")
                        .select("reference_material_id")
                        .eq("company_id", company_id)
                        .eq("company_material_id", company_material_id)
                        .limit(1)
                        .execute()
                    ).data or []
                    current_reference_id = str(
                        (current_rows[0] if current_rows else {}).get(
                            "reference_material_id"
                        )
                        or ""
                    )
                    if current_reference_id != reference_material_id:
                        raise RuntimeError(
                            "Company material identity changed during resolution"
                        )
                company_material["reference_material_id"] = reference_material_id
            resolved += 1
        else:
            reference_material_id = None
            pending_query = (
                client.table("material_identity_candidates")
                .select("candidate_id")
                .eq("company_id", company_id)
                .eq("source_row_id", source_row_id)
                .eq("status", "pending")
                .limit(1)
                .execute()
            ).data or []
            candidate_payload = {
                "company_id": company_id,
                "market_code": market,
                "company_material_id": company_material_id,
                "source_row_id": source_row_id,
                "source_phrase": phrase,
                "normalized_phrase": resolution.normalized_phrase,
                "supplier_id": supplier_id,
                "supplier_sku": row.get("raw_sku"),
                "proposed_category": (row.get("evidence") or {}).get("material_type"),
                "extracted_specifications": company_material.get("specifications") or {},
                "candidate_materials": candidates,
                "resolution_route": resolution.route,
                "confidence_dimensions": {"identity": identity_confidence},
                "resolver_version": resolver_version,
            }
            if pending_query:
                candidate_id = str(pending_query[0]["candidate_id"])
                client.table("material_identity_candidates").update(
                    candidate_payload
                ).eq("candidate_id", candidate_id).execute()
            else:
                inserted = client.table("material_identity_candidates").insert(
                    candidate_payload
                ).execute().data or []
                candidate_id = str(inserted[0]["candidate_id"])
            if resolution.status == "shortlist":
                shortlisted += 1
            else:
                needs_review += 1

        row_update = {
            "reference_material_id": reference_material_id,
            "identity_candidate_id": candidate_id,
            "identity_route": resolution.route,
            "identity_confidence": identity_confidence,
            "resolver_version": resolver_version,
        }
        client.table("company_price_source_rows").update(row_update).eq(
            "company_id", company_id
        ).eq("row_id", source_row_id).execute()
        client.table("company_material_offers").update(
            {"identity_confidence": identity_confidence}
        ).eq("company_id", company_id).eq("source_row_id", source_row_id).execute()
        client.table("material_identity_resolution_events").insert(
            {
                "company_id": company_id,
                "market_code": market,
                "company_material_id": company_material_id,
                "source_row_id": source_row_id,
                "candidate_id": candidate_id,
                "selected_material_id": reference_material_id,
                "resolution_status": resolution.status,
                "resolution_route": resolution.route,
                "normalized_input": {
                    "phrase": resolution.normalized_phrase,
                    "supplier_id": supplier_id,
                    "supplier_sku": row.get("raw_sku"),
                },
                "candidate_materials": candidates,
                "confidence_dimensions": {"identity": identity_confidence},
                "resolver_version": resolver_version,
            }
        ).execute()

    return PriceSourceIdentityBatch(
        examined=examined,
        resolved=resolved,
        shortlisted=shortlisted,
        new_identity_or_needs_review=needs_review,
        unchanged=unchanged,
    )
