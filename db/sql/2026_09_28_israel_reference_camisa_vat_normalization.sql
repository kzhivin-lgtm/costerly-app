-- 3.15.2 Camisa candidate-offer normalization.
--
-- Evidence boundary:
-- 1. Camisa's terms identify the site as a consumer online store, make every
--    purchase subject to Israel's Consumer Protection Law, and state that the
--    site does not make wholesale sales.
-- 2. Israel's Consumer Protection Law requires a consumer-facing displayed
--    total price to include VAT and other mandatory taxes.
-- 3. Camisa's product pages identify the sheet dimensions used below, while
--    delivery is charged separately.
--
-- Camisa does not state the VAT treatment in an explicit supplier sentence.
-- The VAT classification is therefore a legally supported inference, retained
-- in provenance and assigned lower confidence than direct supplier evidence.
-- Evidence retrieved 2026-09-28:
-- https://www.camisa.co.il/%D7%9E%D7%93%D7%99%D7%A0%D7%99%D7%95%D7%AA-%D7%A4%D7%A8%D7%98%D7%99%D7%95%D7%AA/
-- https://www.gov.il/BlobFolder/dynamiccollectorresultitem/9139-05-18/he/9139-05-18.pdf
--
-- This migration corrects candidate evidence only. It does not review or
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
      and o.supplier_name = 'Camisa'
      and s.source_url like 'https://www.camisa.co.il/%';

    if total_count <> 21 then
        raise exception
            'Camisa normalization expected 21 total candidates, found %',
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
              and o.normalized_unit = 'sqm'
              and o.conversion_basis ->> 'vat_evidence_type'
                    = 'legal_inference'
        )
      into pending_count, normalized_count
    from public.market_material_offers o
    join public.reference_sources s
      on s.source_id = o.source_id
     and s.market_code = o.market_code
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.supplier_name = 'Camisa'
      and s.source_url like 'https://www.camisa.co.il/%';

    if pending_count + normalized_count <> 21 then
        raise exception
            'Camisa normalization found an unexpected partial state: % pending, % normalized',
            pending_count,
            normalized_count;
    end if;

    select count(*)
      into invalid_count
    from public.market_material_offers o
    join public.reference_sources s
      on s.source_id = o.source_id
     and s.market_code = o.market_code
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.vat_mode = 'unknown'
      and o.normalized_price_ex_vat is null
      and o.supplier_name = 'Camisa'
      and s.source_url like 'https://www.camisa.co.il/%'
      and (
          not (o.conversion_basis ? 'sheet_area_sqm')
          or (o.conversion_basis ->> 'sheet_area_sqm')::numeric <= 0
      );

    if invalid_count <> 0 then
        raise exception
            'Camisa normalization found % candidates without valid sheet area',
            invalid_count;
    end if;
end $$;

update public.reference_sources
set evidence = evidence || jsonb_build_object(
    'vat_mode', 'included',
    'vat_rate', 0.18,
    'vat_evidence_type', 'legal_inference',
    'supplier_terms_url',
        'https://www.camisa.co.il/%D7%9E%D7%93%D7%99%D7%A0%D7%99%D7%95%D7%AA-%D7%A4%D7%A8%D7%98%D7%99%D7%95%D7%AA/',
    'supplier_terms_evidence',
        'Consumer online sales subject to Consumer Protection Law; no wholesale sales',
    'legal_evidence_url',
        'https://www.gov.il/BlobFolder/dynamiccollectorresultitem/9139-05-18/he/9139-05-18.pdf',
    'legal_evidence',
        'Displayed consumer total price includes VAT and mandatory taxes',
    'vat_evidence_retrieved_on', '2026-09-28',
    'delivery_excluded', true
)
where market_code = 'IL'
  and source_url like 'https://www.camisa.co.il/%';

with camisa_candidates as (
    select
        o.market_offer_id,
        m.base_unit,
        (o.conversion_basis ->> 'sheet_area_sqm')::numeric
            as normalized_quantity
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
      and o.supplier_name = 'Camisa'
      and s.source_url like 'https://www.camisa.co.il/%'
      and m.base_unit = 'sqm'
)
update public.market_material_offers o
set
    vat_mode = 'included',
    normalized_price_ex_vat = round(
        o.source_price / 1.18 / c.normalized_quantity,
        6
    ),
    normalized_unit = c.base_unit,
    confidence = least(coalesce(o.confidence, 68), 68),
    conversion_basis = (
        o.conversion_basis - 'normalization_blocked_by'
    ) || jsonb_build_object(
        'vat_rate', 0.18,
        'vat_evidence_type', 'legal_inference',
        'vat_mode_source',
            'Camisa consumer terms plus Israel total-price requirement',
        'vat_evidence_retrieved_on', '2026-09-28',
        'normalized_quantity', c.normalized_quantity,
        'normalization_formula',
            'source_price / 1.18 / sheet_area_sqm'
    )
from camisa_candidates c
where c.market_offer_id = o.market_offer_id
  and c.normalized_quantity > 0;

commit;
