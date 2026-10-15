-- Final batch of already owner-approved calculation formats.
-- Run WITHOUT RLS. Safe after earlier individual migrations.
begin;

create temporary table _format_seed (
    family_code text primary key,
    supply_format_code text not null,
    purchase_unit text not null,
    purchasable_dimensions jsonb not null
) on commit drop;

insert into _format_seed values
    ('natural_stone_slab', 'calculation_unit_1m2', 'm2',
        '{"length_mm":1000,"width_mm":1000,"format_source":"owner_approved_calculation_unit"}'),
    ('timber_solid_wood_panel', 'calculation_unit_1m2', 'm2',
        '{"length_mm":1000,"width_mm":1000,"format_source":"owner_approved_calculation_unit"}');

-- Natural stone: all active types use the approved 1 m² costing segment.
insert into public.reference_market_material_supply_formats (
    market_material_listing_id, supply_format_code, purchase_unit, purchasable_dimensions, minimum_purchase_quantity, active
)
select listing.market_material_listing_id, seed.supply_format_code, seed.purchase_unit,
       seed.purchasable_dimensions, 1, true
from _format_seed seed
join public.reference_material_families family on family.family_code = seed.family_code and family.active
join public.reference_material_models model on model.family_id = family.family_id and model.active
join public.reference_market_material_listings listing
  on listing.material_model_id = model.material_model_id and listing.market_code = 'IL' and listing.active
where seed.family_code = 'natural_stone_slab'
   or exists (
       select 1 from public.reference_market_material_legacy_mappings mapping
       join public.market_material_model_prices price
         on price.material_id = mapping.legacy_material_id and price.market_code = 'IL'
        and price.status = 'active' and price.price_scope = 'material_only'
        and price.price_typical > 0 and lower(price.unit) in ('m2', 'm²')
       where mapping.material_model_id = model.material_model_id
         and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
   )
on conflict (market_material_listing_id, supply_format_code) do update
set purchase_unit = excluded.purchase_unit,
    purchasable_dimensions = excluded.purchasable_dimensions,
    minimum_purchase_quantity = excluded.minimum_purchase_quantity,
    active = true,
    updated_at = now();

commit;
