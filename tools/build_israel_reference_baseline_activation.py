from __future__ import annotations

import argparse
import json
import sys
import uuid
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.supabase_client import get_supabase_client  # noqa: E402
from use_cases.reference_material_readiness import (  # noqa: E402
    CatalogPriceCandidate,
    ReferenceMaterial,
    ReferenceOffer,
    derive_complete_catalog_candidates,
)


BASELINE_NAMESPACE = uuid.UUID("c488f968-37cd-4711-b6c2-9b75fb687516")
EXPECTED_MATERIAL_COUNT = 280


def _decimal(value) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def load_production_candidates() -> tuple[CatalogPriceCandidate, ...]:
    client = get_supabase_client()
    material_rows = (
        client.table("reference_materials")
        .select("material_id,department,category_code,base_unit,specifications")
        .eq("active", True)
        .execute()
        .data
    )
    offer_rows = (
        client.table("market_material_offers")
        .select(
            "market_offer_id,material_id,market_code,source_id,source_currency,"
            "price_scope,vat_mode,normalized_price_ex_vat,normalized_unit,"
            "status,region,confidence,source_price,source_unit,package_quantity,"
            "conversion_basis"
        )
        .eq("market_code", "IL")
        .execute()
        .data
    )
    materials = tuple(
        ReferenceMaterial(
            material_id=row["material_id"],
            department=row["department"],
            category_code=row["category_code"],
            base_unit=row["base_unit"],
            specifications=row.get("specifications") or {},
        )
        for row in material_rows
    )
    offers = tuple(
        ReferenceOffer(
            offer_id=row["market_offer_id"],
            material_id=row["material_id"],
            market_code=row["market_code"],
            source_id=row["source_id"],
            currency=row["source_currency"],
            price_scope=row["price_scope"],
            vat_mode=row["vat_mode"],
            normalized_price_ex_vat=_decimal(row["normalized_price_ex_vat"]),
            normalized_unit=row["normalized_unit"],
            status=row["status"],
            region=row.get("region"),
            confidence=_decimal(row["confidence"]),
            source_price=_decimal(row["source_price"]),
            source_unit=row["source_unit"],
            package_quantity=_decimal(row["package_quantity"]),
            conversion_basis=row.get("conversion_basis") or {},
        )
        for row in offer_rows
    )
    candidates = derive_complete_catalog_candidates(materials=materials, offers=offers)
    offer_scopes = {row.offer_id: row.price_scope for row in offers}
    for candidate in candidates:
        incompatible = tuple(
            offer_id
            for offer_id in candidate.offer_ids
            if offer_scopes.get(offer_id) != candidate.price_scope
        )
        if incompatible:
            raise ValueError(
                f"Candidate {candidate.material_id} has incompatible evidence: "
                f"{incompatible}"
            )
    return candidates


def build_payload(candidates: tuple[CatalogPriceCandidate, ...]) -> list[dict]:
    if len(candidates) != EXPECTED_MATERIAL_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MATERIAL_COUNT} candidates, got {len(candidates)}"
        )
    if len({row.material_id for row in candidates}) != len(candidates):
        raise ValueError("Candidate material ids must be unique")
    if any(not row.offer_ids for row in candidates):
        raise ValueError("Every active baseline must retain evidence offer ids")

    return [
        {
            "baseline_id": str(
                uuid.uuid5(
                    BASELINE_NAMESPACE,
                    f"IL:v1:{row.material_id}:{row.unit}:{row.price_scope}",
                )
            ),
            "material_id": row.material_id,
            "price_low": str(row.price_low),
            "price_typical": str(row.price_typical),
            "price_high": str(row.price_high),
            "unit": row.unit,
            "currency": row.currency,
            "price_scope": row.price_scope,
            "methodology": f"tier={row.tier}; {row.methodology}",
            "confidence": str(row.confidence),
            "offer_ids": list(row.offer_ids),
        }
        for row in candidates
    ]


def render_activation_sql(payload: list[dict]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"""-- 3.15.2 Activate the first complete Israel material-price baseline.
-- Generated from production candidate evidence. Idempotent for this exact v1
-- payload. It refuses to replace any different active Israel baseline.

begin;

create temporary table _israel_baseline_payload on commit drop as
select *
from jsonb_to_recordset($payload${payload_json}$payload$::jsonb) as x(
    baseline_id uuid,
    material_id uuid,
    price_low numeric,
    price_typical numeric,
    price_high numeric,
    unit text,
    currency text,
    price_scope text,
    methodology text,
    confidence numeric,
    offer_ids jsonb
);

do $$
declare
    payload_count integer;
    approver uuid;
begin
    select count(*) into payload_count from _israel_baseline_payload;
    if payload_count <> {EXPECTED_MATERIAL_COUNT} then
        raise exception 'Expected {EXPECTED_MATERIAL_COUNT} baseline rows, got %',
            payload_count;
    end if;

    if exists (
        select material_id
        from _israel_baseline_payload
        group by material_id
        having count(*) <> 1
    ) then
        raise exception 'Each material must have exactly one v1 baseline';
    end if;

    select user_id into approver
    from public.platform_staff
    where active and role = 'platform_admin'
    order by user_id
    limit 1;
    if approver is null then
        raise exception 'An active platform_admin is required to approve baselines';
    end if;

    if exists (
        select 1
        from public.market_material_baselines b
        where b.market_code = 'IL'
          and b.status = 'active'
          and not exists (
              select 1 from _israel_baseline_payload p
              where p.baseline_id = b.baseline_id
          )
    ) then
        raise exception 'A different active Israel baseline already exists';
    end if;

    if exists (
        select 1
        from _israel_baseline_payload p
        cross join lateral jsonb_array_elements_text(p.offer_ids) evidence(offer_id)
        left join public.market_material_offers o
          on o.market_offer_id = evidence.offer_id::uuid
         and o.market_code = 'IL'
         and o.price_scope = p.price_scope
        where o.market_offer_id is null
    ) then
        raise exception 'Baseline evidence is missing or has an incompatible scope';
    end if;
end $$;

insert into public.market_material_baselines as existing (
    baseline_id, material_id, market_code, region,
    price_low, price_typical, price_high, unit, currency, price_scope,
    vat_mode, methodology, confidence, status, version, effective_from
)
select
    baseline_id, material_id, 'IL', null,
    price_low, price_typical, price_high, unit, currency, price_scope,
    'excluded', methodology, confidence, 'candidate', 1, current_date
from _israel_baseline_payload
on conflict (baseline_id) do nothing;

insert into public.market_material_baseline_evidence (
    baseline_id, market_offer_id, market_code, price_scope
)
select
    p.baseline_id, evidence.offer_id::uuid, 'IL', p.price_scope
from _israel_baseline_payload p
cross join lateral jsonb_array_elements_text(p.offer_ids) evidence(offer_id)
on conflict (baseline_id, market_offer_id) do nothing;

update public.market_material_baselines b
set status = 'active',
    approved_by = approver.user_id,
    approved_at = now(),
    effective_from = least(b.effective_from, current_date),
    effective_to = null
from (
    select user_id
    from public.platform_staff
    where active and role = 'platform_admin'
    order by user_id
    limit 1
) approver
where exists (
    select 1 from _israel_baseline_payload p
    where p.baseline_id = b.baseline_id
)
and b.status <> 'active';

do $$
declare
    active_count integer;
begin
    select count(*) into active_count
    from public.market_material_baselines b
    where b.market_code = 'IL'
      and b.status = 'active'
      and exists (
          select 1 from _israel_baseline_payload p
          where p.baseline_id = b.baseline_id
      );
    if active_count <> {EXPECTED_MATERIAL_COUNT} then
        raise exception 'Expected {EXPECTED_MATERIAL_COUNT} active baselines, got %',
            active_count;
    end if;
end $$;

commit;

select
    count(*) filter (where status = 'active') as active_baselines,
    count(distinct material_id) filter (where status = 'active')
        as active_materials,
    min(confidence) filter (where status = 'active') as min_confidence,
    max(confidence) filter (where status = 'active') as max_confidence
from public.market_material_baselines
where market_code = 'IL';
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = build_payload(load_production_candidates())
    args.output.write_text(render_activation_sql(payload))
    print(f"wrote {len(payload)} baselines to {args.output}")


if __name__ == "__main__":
    main()
