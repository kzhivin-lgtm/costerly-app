-- 3.15.2 A.R. Sharpening candidate-offer normalization.
--
-- The supplier site supports online purchase, shipping, cancellation, and
-- returns under Israel's Consumer Protection Law. Israeli consumer-facing
-- total-price rules require displayed prices to include VAT. The supplier does
-- not state VAT inclusion directly, so this remains a legal inference and the
-- normalized-offer confidence is capped at 60.
-- Evidence retrieved 2026-09-28:
-- https://www.ar-aia.co.il/pages/51861-%D7%9E%D7%93%D7%99%D7%A0%D7%99%D7%95%D7%AA-%D7%A4%D7%A8%D7%98%D7%99%D7%95%D7%AA
-- https://www.gov.il/BlobFolder/dynamiccollectorresultitem/9139-05-18/he/9139-05-18.pdf
--
-- This migration corrects 14 candidate prices only. It does not review or
-- activate an offer or create a market baseline.

begin;

do $$
declare
    total_count integer;
    pending_count integer;
    normalized_count integer;
    invalid_count integer;
begin
    select count(*)
      into total_count
    from public.market_material_offers o
    join public.reference_sources s
      on s.source_id = o.source_id
     and s.market_code = o.market_code
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.supplier_name in ('A.R. Sharpening', 'AR Sharpening')
      and s.source_url like 'https://www.ar-aia.co.il/%';

    if total_count <> 14 then
        raise exception
            'A.R. Sharpening normalization expected 14 candidates, found %',
            total_count;
    end if;

    select
        count(*) filter (
            where o.vat_mode = 'unknown'
              and o.normalized_price_ex_vat is null
        ),
        count(*) filter (
            where o.vat_mode = 'included'
              and o.normalized_price_ex_vat is not null
              and o.conversion_basis ->> 'vat_mode_source'
                    = 'A.R. Sharpening consumer terms plus Israel total-price requirement'
        )
      into pending_count, normalized_count
    from public.market_material_offers o
    join public.reference_sources s
      on s.source_id = o.source_id
     and s.market_code = o.market_code
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.supplier_name in ('A.R. Sharpening', 'AR Sharpening')
      and s.source_url like 'https://www.ar-aia.co.il/%';

    if pending_count + normalized_count <> 14 then
        raise exception
            'A.R. Sharpening normalization found unexpected state: % pending, % normalized',
            pending_count,
            normalized_count;
    end if;

    with candidates as (
        select
            o.market_offer_id,
            case
                when m.base_unit = 'kg'
                 and o.conversion_basis ? 'net_weight_kg'
                    then (o.conversion_basis ->> 'net_weight_kg')::numeric
                when m.base_unit = 'ea' then o.package_quantity
                else null::numeric
            end as normalized_quantity
        from public.market_material_offers o
        join public.reference_materials m
          on m.material_id = o.material_id
        join public.reference_sources s
          on s.source_id = o.source_id
         and s.market_code = o.market_code
        where o.market_code = 'IL'
          and o.status = 'candidate'
          and o.vat_mode = 'unknown'
          and o.normalized_price_ex_vat is null
          and o.supplier_name in ('A.R. Sharpening', 'AR Sharpening')
          and s.source_url like 'https://www.ar-aia.co.il/%'
    )
    select count(*)
      into invalid_count
    from candidates
    where normalized_quantity is null or normalized_quantity <= 0;

    if invalid_count <> 0 then
        raise exception
            'A.R. Sharpening normalization found % invalid quantities',
            invalid_count;
    end if;
end $$;

update public.reference_sources
set evidence = evidence || jsonb_build_object(
    'vat_mode', 'included',
    'vat_rate', 0.18,
    'vat_evidence_type', 'legal_inference',
    'supplier_terms_url',
        'https://www.ar-aia.co.il/pages/51861-%D7%9E%D7%93%D7%99%D7%A0%D7%99%D7%95%D7%AA-%D7%A4%D7%A8%D7%98%D7%99%D7%95%D7%AA',
    'supplier_terms_evidence',
        'Online sales, shipping, cancellation, and returns under Consumer Protection Law',
    'legal_evidence_url',
        'https://www.gov.il/BlobFolder/dynamiccollectorresultitem/9139-05-18/he/9139-05-18.pdf',
    'vat_evidence_retrieved_on', '2026-09-28'
)
where market_code = 'IL'
  and source_url like 'https://www.ar-aia.co.il/%';

with candidates as (
    select
        o.market_offer_id,
        m.base_unit,
        case
            when m.base_unit = 'kg'
             and o.conversion_basis ? 'net_weight_kg'
                then (o.conversion_basis ->> 'net_weight_kg')::numeric
            when m.base_unit = 'ea' then o.package_quantity
            else null::numeric
        end as normalized_quantity
    from public.market_material_offers o
    join public.reference_materials m
      on m.material_id = o.material_id
    join public.reference_sources s
      on s.source_id = o.source_id
     and s.market_code = o.market_code
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.vat_mode = 'unknown'
      and o.normalized_price_ex_vat is null
      and o.supplier_name in ('A.R. Sharpening', 'AR Sharpening')
      and s.source_url like 'https://www.ar-aia.co.il/%'
)
update public.market_material_offers o
set
    vat_mode = 'included',
    normalized_price_ex_vat = round(
        o.source_price / 1.18 / c.normalized_quantity,
        6
    ),
    normalized_unit = c.base_unit,
    confidence = least(coalesce(o.confidence, 60), 60),
    conversion_basis = (
        o.conversion_basis - 'normalization_blocked_by'
    ) || jsonb_build_object(
        'vat_rate', 0.18,
        'vat_evidence_type', 'legal_inference',
        'vat_mode_source',
            'A.R. Sharpening consumer terms plus Israel total-price requirement',
        'vat_evidence_retrieved_on', '2026-09-28',
        'normalized_quantity', c.normalized_quantity,
        'normalization_formula',
            'source_price / 1.18 / normalized_quantity'
    )
from candidates c
where c.market_offer_id = o.market_offer_id
  and c.normalized_quantity > 0;

commit;
