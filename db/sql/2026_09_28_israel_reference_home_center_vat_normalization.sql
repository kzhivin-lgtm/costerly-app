-- 3.15.2 Home Center candidate-offer normalization.
-- Home Center website terms, section 65, state that all website prices include
-- VAT and exclude delivery, installation, and other additions.
-- Evidence retrieved 2026-09-28:
-- https://www.homecenter.co.il/pages/%D7%AA%D7%A7%D7%A0%D7%95%D7%9F-%D7%90%D7%AA%D7%A8
--
-- This migration corrects candidate evidence only. It does not review or
-- activate an offer or create a market baseline.

begin;

update public.reference_sources
set evidence = evidence || jsonb_build_object(
    'vat_mode', 'included',
    'vat_rate', 0.18,
    'vat_evidence_url',
        'https://www.homecenter.co.il/pages/%D7%AA%D7%A7%D7%A0%D7%95%D7%9F-%D7%90%D7%AA%D7%A8',
    'vat_evidence_section', 'Website terms section 65',
    'vat_evidence_retrieved_on', '2026-09-28',
    'delivery_and_installation_excluded', true
)
where market_code = 'IL'
  and source_url like 'https://www.homecenter.co.il/%';

with home_center_candidates as (
    select
        o.market_offer_id,
        m.base_unit,
        case
            when m.base_unit = 'l'
             and o.conversion_basis ? 'net_volume_l'
                then (o.conversion_basis ->> 'net_volume_l')::numeric
            when m.base_unit = 'kg'
             and o.conversion_basis ? 'net_weight_kg'
                then (o.conversion_basis ->> 'net_weight_kg')::numeric
            else o.package_quantity
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
      and o.supplier_name = 'Home Center'
      and s.source_url like 'https://www.homecenter.co.il/%'
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
        'vat_mode_source', 'Home Center website terms section 65',
        'vat_evidence_retrieved_on', '2026-09-28',
        'normalized_quantity', c.normalized_quantity,
        'normalization_formula',
            'source_price / 1.18 / normalized_quantity'
    )
from home_center_candidates c
where c.market_offer_id = o.market_offer_id
  and c.normalized_quantity is not null
  and c.normalized_quantity > 0;

commit;
