from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import logging
from typing import Any, Mapping, Sequence
from uuid import uuid4

from use_cases.material_identity_resolution import (
    MaterialIdentityResolution,
    normalize_material_phrase,
    resolve_material_identity,
)
from use_cases.material_pricing_identity_resolution import (
    PricingIdentityResolution,
    resolve_material_pricing_identity,
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

logger = logging.getLogger(__name__)


REFERENCE_INDEX_PAGE_SIZE = 1_000


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


def _candidate_payload(
    resolution: MaterialIdentityResolution,
    materials_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "material_id": candidate.material_id,
            "canonical_name": str(
                (materials_by_id.get(candidate.material_id) or {}).get("canonical_name") or ""
            ),
            "category_code": str(
                (materials_by_id.get(candidate.material_id) or {}).get("category_code") or ""
            ),
            "specifications": dict(
                (materials_by_id.get(candidate.material_id) or {}).get("specifications") or {}
            ),
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


def _select_all(query: Any, *, page_size: int = REFERENCE_INDEX_PAGE_SIZE) -> list[dict[str, Any]]:
    """Read every row from a PostgREST query, not just its default first page."""
    rows: list[dict[str, Any]] = []
    start = 0
    while True:
        page = query.range(start, start + page_size - 1).execute().data or []
        rows.extend(page)
        if len(page) < page_size:
            return rows
        start += page_size


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
    all_materials = _select_all(
        client.table("reference_materials")
        .select(
            "material_id,department,category_code,canonical_name,base_unit,"
            "specifications,active"
        )
        .eq("active", True)
    )
    catalog_v1_materials = [
        row
        for row in all_materials
        if (row.get("specifications") or {}).get("catalog_version")
        == "israel_global_catalog_v1"
    ]
    resolver_version = str(versions[0]["resolver_version"])
    pricing_identities: list[dict[str, Any]] = []
    if resolver_version == "material_identity_v3":
        pricing_identities = _select_all(
            client.table("reference_material_pricing_identities")
            .select(
                "pricing_identity_id,market_code,department,canonical_name,base_unit,"
                "price_attributes,status"
            )
            .eq("market_code", market_code)
            .eq("status", "active")
        )
    return {
        "resolver_version": resolver_version,
        # Do not let an incomplete multi-part data import change production
        # matching. Catalog V1 becomes the resolver universe only when V2 is
        # explicitly active in the final migration part.
        "materials": (
            catalog_v1_materials
            if resolver_version in {"material_identity_v2", "material_identity_v3"}
            and catalog_v1_materials
            else all_materials
        ),
        "reference_aliases": _select_all(
            client.table("reference_material_aliases")
            .select(
                "material_id,market_code,alias_text,exact_identity,confidence,active"
            )
            .eq("market_code", market_code)
            .eq("active", True)
        ),
        "company_aliases": _select_all(
            client.table("company_material_aliases")
            .select("material_id,supplier_id,alias_text,resolver_key,active")
            .eq("company_id", company_id)
            .eq("active", True)
        ),
        "market_offers": _select_all(
            client.table("market_material_offers")
            .select("material_id,market_code,supplier_name,supplier_sku,status")
            .eq("market_code", market_code)
            .neq("status", "archived")
        ),
        "pricing_identities": pricing_identities,
    }


def _pricing_specifications(
    *,
    material_family: str,
    extracted_specifications: Mapping[str, Any],
) -> dict[str, Any]:
    """Translate source evidence into the small set of price-bearing axes."""
    result = dict(extracted_specifications)
    surface = normalize_material_phrase(result.get("surface"))
    construction_by_surface = {
        "raw": "raw",
        "exposed": "raw",
        "unfinished": "raw",
        "veneer": "veneer_faced",
        "veneered": "veneer_faced",
        "formica": "plastic_laminate_faced",
        "hpl": "plastic_laminate_faced",
        "plastic": "plastic_laminate_faced",
        "butcher block": "laminated",
    }
    if surface in construction_by_surface:
        result["construction"] = construction_by_surface[surface]
    elif any(token in surface for token in ("formica", "hpl", "plastic")):
        result["construction"] = "plastic_laminate_faced"
    elif "white lacquer" in normalize_material_phrase(result.get("coating")):
        result["construction"] = "plastic_laminate_faced"
    elif (
        "plywood" in normalize_material_phrase(material_family)
        and not surface
        and not normalize_material_phrase(result.get("coating"))
        and not normalize_material_phrase(result.get("construction"))
    ):
        result["construction"] = "raw"
    if normalize_material_phrase(material_family) == "melamine":
        result["construction"] = "melamine_faced"
    if normalize_material_phrase(material_family) in {
        "solid timber laminated",
        "solid timber lami",
        "solid timber butcher block",
        "butcher block panel",
    }:
        result["construction"] = "laminated"
    return result


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
    identity_agent=None,
) -> PriceSourceIdentityBatch:
    """Resolve active Price Source rows without repeating source extraction."""

    market = str(market_code or "").strip().upper()
    index = _load_resolution_index(client, company_id=company_id, market_code=market)
    resolver_version = index["resolver_version"]
    reference_material_by_id = {
        str(item["material_id"]): item for item in index["materials"]
    }

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
                "company_material_id,reference_material_id,pricing_identity_id,category,canonical_name,"
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
    source_row_ids = [str(row["row_id"]) for row in rows]
    pending_candidates = (
        client.table("material_identity_candidates")
        .select("candidate_id,source_row_id")
        .eq("company_id", company_id)
        .eq("status", "pending")
        .in_("source_row_id", source_row_ids)
        .execute()
    ).data or []
    pending_by_source_row = {
        str(candidate["source_row_id"]): str(candidate["candidate_id"])
        for candidate in pending_candidates
    }

    examined = resolved = shortlisted = needs_review = unchanged = 0
    new_candidates: list[dict[str, Any]] = []
    source_rows_to_update: list[dict[str, Any]] = []
    resolution_events: list[dict[str, Any]] = []
    resolved_offer_rows_by_confidence: dict[float, list[str]] = {}
    agent_requests: list[dict[str, Any]] = []
    agent_contexts: dict[str, dict[str, Any]] = {}
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
        evidence = row.get("evidence") or {}
        phrase = str(
            row.get("normalized_name")
            or row.get("raw_description")
            or company_material.get("canonical_name")
            or ""
        ).strip()
        alternate_phrases = tuple(
            value
            for value in (
                str(row.get("raw_description") or "").strip(),
                str(evidence.get("material_family") or "").strip(),
            )
            if value and normalize_material_phrase(value) != normalize_material_phrase(phrase)
        )
        extracted_specifications = {
            key: value
            for key, value in {
                **(company_material.get("specifications") or {}),
                **(evidence.get("identity_attributes") or {}),
            }.items()
            if value not in (None, "", 0, 0.0, [])
        }
        material_family = str(evidence.get("material_family") or "")
        existing_pricing_identity_id = str(
            company_material.get("pricing_identity_id") or ""
        )
        pricing_resolution = PricingIdentityResolution(status="needs_review")
        if existing_pricing_identity_id:
            pricing_resolution = PricingIdentityResolution(
                status="resolved",
                selected_pricing_identity_id=existing_pricing_identity_id,
            )
        elif index["pricing_identities"]:
            pricing_resolution = resolve_material_pricing_identity(
                material_family=material_family,
                specifications=_pricing_specifications(
                    material_family=material_family,
                    extracted_specifications=extracted_specifications,
                ),
                market_code=market,
                pricing_identities=index["pricing_identities"],
            )
        pricing_identity_id = str(
            pricing_resolution.selected_pricing_identity_id or ""
        )
        pricing_candidates = [
            {
                "pricing_identity_id": candidate.pricing_identity_id,
                "score": _score(candidate.score),
                "matched_price_attributes": list(candidate.matched_price_attributes),
            }
            for candidate in pricing_resolution.candidates
        ]
        pricing_resolved = bool(pricing_identity_id)
        if pricing_resolved and not existing_pricing_identity_id:
            linked_rows = client.table("company_material_items").update(
                {"pricing_identity_id": pricing_identity_id}
            ).eq("company_id", company_id).eq(
                "company_material_id", company_material_id
            ).is_("pricing_identity_id", "null").execute().data or []
            if not linked_rows:
                current_rows = (
                    client.table("company_material_items")
                    .select("pricing_identity_id")
                    .eq("company_id", company_id)
                    .eq("company_material_id", company_material_id)
                    .limit(1)
                    .execute()
                ).data or []
                if str((current_rows[0] if current_rows else {}).get("pricing_identity_id") or "") != pricing_identity_id:
                    raise RuntimeError("Company material pricing identity changed during resolution")
            company_material["pricing_identity_id"] = pricing_identity_id
        existing_reference_id = str(company_material.get("reference_material_id") or "")
        reference_material_id: str | None = existing_reference_id or None
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
                evidence.get("material_type")
                or company_material.get("category")
                or ""
            )
            resolution = resolve_material_identity(
                phrase=phrase,
                alternate_phrases=alternate_phrases,
                market_code=market,
                materials=index["materials"],
                reference_aliases=index["reference_aliases"],
                company_aliases=index["company_aliases"],
                market_offers=index["market_offers"],
                supplier_name=supplier_name,
                supplier_id=supplier_id,
                supplier_sku=str(row.get("raw_sku") or "") or None,
                specifications=extracted_specifications,
                material_family=material_family or None,
                candidate_departments=PRICE_SOURCE_REFERENCE_DEPARTMENTS.get(
                    material_type, ()
                ),
            )

        candidates = _candidate_payload(resolution, reference_material_by_id)
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
        if pricing_resolved or resolution.status == "resolved":
            resolved += 1
        else:
            reference_material_id = None
            candidate_payload = {
                "company_id": company_id,
                "market_code": market,
                "company_material_id": company_material_id,
                "source_row_id": source_row_id,
                "source_phrase": phrase,
                "normalized_phrase": resolution.normalized_phrase,
                "supplier_id": supplier_id,
                "supplier_sku": row.get("raw_sku"),
                "proposed_category": evidence.get("material_type"),
                "extracted_specifications": extracted_specifications,
                "candidate_materials": candidates,
                "candidate_pricing_identities": pricing_candidates,
                "resolution_route": resolution.route,
                "confidence_dimensions": {"identity": identity_confidence},
                "resolver_version": resolver_version,
            }
            candidate_id = pending_by_source_row.get(source_row_id)
            if candidate_id:
                client.table("material_identity_candidates").update(
                    candidate_payload
                ).eq("candidate_id", candidate_id).execute()
            else:
                candidate_id = str(uuid4())
                new_candidates.append(
                    {"candidate_id": candidate_id, **candidate_payload}
                )
            if pricing_resolution.status == "shortlist" or resolution.status == "shortlist":
                shortlisted += 1
            else:
                needs_review += 1

        source_row_update = {
                **row,
                "reference_material_id": reference_material_id,
                "pricing_identity_id": pricing_identity_id or None,
                "identity_candidate_id": candidate_id,
                "identity_route": resolution.route,
                "identity_confidence": identity_confidence,
                "resolver_version": resolver_version,
            }
        source_rows_to_update.append(source_row_update)
        if pricing_resolved or resolution.status == "resolved":
            resolved_offer_rows_by_confidence.setdefault(
                identity_confidence, []
            ).append(source_row_id)
        resolution_event = {
                "company_id": company_id,
                "market_code": market,
                "company_material_id": company_material_id,
                "source_row_id": source_row_id,
                "candidate_id": candidate_id,
                "selected_material_id": reference_material_id,
                "selected_pricing_identity_id": pricing_identity_id or None,
                "resolution_status": resolution.status,
                "resolution_route": resolution.route,
                "normalized_input": {
                    "phrase": resolution.normalized_phrase,
                    "alternate_phrases": list(alternate_phrases),
                    "specifications": extracted_specifications,
                    "supplier_id": supplier_id,
                    "supplier_sku": row.get("raw_sku"),
                },
                "candidate_materials": candidates,
                "candidate_pricing_identities": pricing_candidates,
                "confidence_dimensions": {"identity": identity_confidence},
                "resolver_version": resolver_version,
            }
        resolution_events.append(resolution_event)
        if not pricing_resolved and resolution.status != "resolved" and not pending_by_source_row.get(source_row_id):
            agent_requests.append(
                {
                    "source_row_id": source_row_id,
                    "raw_description": str(row.get("raw_description") or ""),
                    "normalized_name": str(row.get("normalized_name") or ""),
                    "material_family": str(evidence.get("material_family") or ""),
                    "material_type": str(evidence.get("material_type") or ""),
                    "identity_attributes": extracted_specifications,
                    "supplier_sku": str(row.get("raw_sku") or ""),
                    "candidates": candidates,
                }
            )
            agent_contexts[source_row_id] = {
                "company_material_id": company_material_id,
                "candidate_id": candidate_id,
                "source_update": source_row_update,
                "event": resolution_event,
                "prior_status": resolution.status,
            }

    if identity_agent and agent_requests:
        try:
            decisions = identity_agent(agent_requests[:60])
        except Exception:
            logger.exception("Bounded material identity agent failed; retaining review candidates")
            decisions = []
        for decision in decisions:
            source_row_id = str(decision.get("source_row_id") or "")
            context = agent_contexts.get(source_row_id)
            if not context:
                continue
            decision_name = str(decision.get("decision") or "")
            confidence = float(decision.get("confidence") or 0)
            selected_material_id = str(decision.get("selected_material_id") or "")
            event = context["event"]
            source_update = context["source_update"]
            event["normalized_input"]["agent_decision"] = decision_name
            event["normalized_input"]["agent_reason"] = str(decision.get("reason") or "")
            event["confidence_dimensions"]["identity_agent"] = confidence
            source_update["identity_confidence"] = confidence
            if decision_name == "link_existing" and confidence >= 90 and selected_material_id:
                company_material_id = context["company_material_id"]
                linked_rows = client.table("company_material_items").update(
                    {"reference_material_id": selected_material_id}
                ).eq("company_id", company_id).eq(
                    "company_material_id", company_material_id
                ).is_("reference_material_id", "null").execute().data or []
                if not linked_rows:
                    continue
                candidate_id = context["candidate_id"]
                new_candidates[:] = [
                    row for row in new_candidates
                    if str(row.get("candidate_id")) != str(candidate_id)
                ]
                source_update.update(
                    {
                        "reference_material_id": selected_material_id,
                        "identity_candidate_id": None,
                        "identity_route": "identity_agent_link_existing",
                    }
                )
                event.update(
                    {
                        "candidate_id": None,
                        "selected_material_id": selected_material_id,
                        "resolution_status": "resolved",
                        "resolution_route": "identity_agent_link_existing",
                    }
                )
                if context["prior_status"] == "shortlist":
                    shortlisted -= 1
                else:
                    needs_review -= 1
                resolved += 1
                resolved_offer_rows_by_confidence.setdefault(confidence, []).append(
                    source_row_id
                )
            else:
                route = f"identity_agent_{decision_name or 'unresolved'}"
                source_update["identity_route"] = route
                event["resolution_route"] = route
                for candidate in new_candidates:
                    if str(candidate.get("candidate_id")) == str(context["candidate_id"]):
                        candidate["resolution_route"] = route
                        candidate["confidence_dimensions"] = {
                            "identity": source_update["identity_confidence"],
                            "identity_agent": confidence,
                        }
                        break
                if decision_name == "operation_service" and confidence >= 90:
                    source_update["result_status"] = "excluded"
                    source_update["reason_codes"] = sorted(
                        set(source_update.get("reason_codes") or [])
                        | {"operation_service_not_material"}
                    )
                    client.table("company_material_offers").update(
                        {"status": "unresolved"}
                    ).eq("company_id", company_id).eq(
                        "source_row_id", source_row_id
                    ).execute()

    if new_candidates:
        client.table("material_identity_candidates").insert(new_candidates).execute()
    if source_rows_to_update:
        client.table("company_price_source_rows").upsert(
            source_rows_to_update,
            on_conflict="row_id",
        ).execute()
    for confidence, resolved_source_row_ids in resolved_offer_rows_by_confidence.items():
        client.table("company_material_offers").update(
            {"identity_confidence": confidence}
        ).eq("company_id", company_id).in_(
            "source_row_id", resolved_source_row_ids
        ).execute()
    if resolution_events:
        client.table("material_identity_resolution_events").insert(
            resolution_events
        ).execute()

    return PriceSourceIdentityBatch(
        examined=examined,
        resolved=resolved,
        shortlisted=shortlisted,
        new_identity_or_needs_review=needs_review,
        unchanged=unchanged,
    )
