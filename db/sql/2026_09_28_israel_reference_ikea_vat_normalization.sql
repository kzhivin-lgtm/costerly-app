-- 3.15.2 IKEA Israel candidate-offer normalization.
-- IKEA Israel's own terms state that prices displayed on the website include
-- VAT when applicable. Delivery and assembly are separate services.
-- Evidence retrieved 2026-09-28:
-- https://www.ikea.com/il/he/customer-service/terms-conditions/
--
-- Three decorative mirror offers remain blocked because their thickness is
-- not stated. This migration corrects eight candidate prices only. It does not
-- review or activate an offer or create a market baseline.

begin;

do $$
declare
    total_count integer;
    pending_count integer;
    normalized_count integer;
    excluded_mirror_count integer;
    invalid_count integer;
begin
    select count(*)
      into total_count
    from public.market_material_offers o
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.supplier_name = 'IKEA Israel';

    if total_count <> 11 then
        raise exception
            'IKEA normalization expected 11 total candidates, found %',
            total_count;
    end if;

    select
        count(*) filter (
            where o.vat_mode = 'unknown'
              and o.normalized_price_ex_vat is null
              and coalesce(
                    o.conversion_basis ->> 'normalization_blocked_by', ''
                  ) not like '%mirror thickness%'
        ),
        count(*) filter (
            where o.vat_mode = 'included'
              and o.normalized_price_ex_vat is not null
              and o.conversion_basis ->> 'vat_mode_source'
                    = 'IKEA Israel website terms'
        ),
        count(*) filter (
            where coalesce(
                    o.conversion_basis ->> 'normalization_blocked_by', ''
                  ) like '%mirror thickness%'
        )
      into pending_count, normalized_count, excluded_mirror_count
    from public.market_material_offers o
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.supplier_name = 'IKEA Israel';

    if pending_count + normalized_count <> 8
       or excluded_mirror_count <> 3 then
        raise exception
            'IKEA normalization found unexpected state: % pending, % normalized, % mirrors',
            pending_count,
            normalized_count,
            excluded_mirror_count;
    end if;

    with ikea_candidates as (
        select
            o.market_offer_id,
            case
                when m.base_unit = 'l'
                 and o.conversion_basis ? 'net_volume_l'
                    then (o.conversion_basis ->> 'net_volume_l')::numeric
                when m.base_unit = 'set' then 1::numeric
                else o.package_quantity
            end as normalized_quantity
        from public.market_material_offers o
        join public.reference_materials m
          on m.material_id = o.material_id
        where o.market_code = 'IL'
          and o.status = 'candidate'
          and o.vat_mode = 'unknown'
          and o.normalized_price_ex_vat is null
          and o.supplier_name = 'IKEA Israel'
          and coalesce(
                o.conversion_basis ->> 'normalization_blocked_by', ''
              ) not like '%mirror thickness%'
    )
    select count(*)
      into invalid_count
    from ikea_candidates
    where normalized_quantity is null or normalized_quantity <= 0;

    if invalid_count <> 0 then
        raise exception
            'IKEA normalization found % candidates without valid quantity',
            invalid_count;
    end if;
end $$;

update public.reference_sources
set evidence = evidence || jsonb_build_object(
    'vat_mode', 'included',
    'vat_rate', 0.18,
    'vat_evidence_type', 'direct_supplier_terms',
    'vat_evidence_url',
        'https://www.ikea.com/il/he/customer-service/terms-conditions/',
    'vat_evidence',
        'Website prices include VAT when applicable',
    'vat_evidence_retrieved_on', '2026-09-28',
    'delivery_and_assembly_separate', true
)
where market_code = 'IL'
  and source_url like 'https://www.ikea.com/il/he/%';

with ikea_candidates as (
    select
        o.market_offer_id,
        m.base_unit,
        case
            when m.base_unit = 'l'
             and o.conversion_basis ? 'net_volume_l'
                then (o.conversion_basis ->> 'net_volume_l')::numeric
            when m.base_unit = 'set' then 1::numeric
            else o.package_quantity
        end as normalized_quantity
    from public.market_material_offers o
    join public.reference_materials m
      on m.material_id = o.material_id
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.vat_mode = 'unknown'
      and o.normalized_price_ex_vat is null
      and o.supplier_name = 'IKEA Israel'
      and coalesce(
            o.conversion_basis ->> 'normalization_blocked_by', ''
          ) not like '%mirror thickness%'
)
update public.market_material_offers o
set
    vat_mode = 'included',
    normalized_price_ex_vat = round(
        o.source_price / 1.18 / c.normalized_quantity,
        6
    ),
    normalized_unit = c.base_unit,
    conversion_basis = (
        o.conversion_basis - 'normalization_blocked_by'
    ) || jsonb_build_object(
        'vat_rate', 0.18,
        'vat_evidence_type', 'direct_supplier_terms',
        'vat_mode_source', 'IKEA Israel website terms',
        'vat_evidence_retrieved_on', '2026-09-28',
        'normalized_quantity', c.normalized_quantity,
        'normalization_formula',
            'source_price / 1.18 / normalized_quantity'
    )
from ikea_candidates c
where c.market_offer_id = o.market_offer_id
  and c.normalized_quantity > 0;

commit;
