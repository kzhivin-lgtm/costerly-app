-- Owner decision: every natural-stone Israel Reference position is calculated
-- as a 1 m² segment. This is a costing unit, not a claim about quarry slabs.
-- Run WITHOUT RLS.
begin;

insert into public.reference_market_material_supply_formats (
    market_material_listing_id, supply_format_code, purchase_unit,
    purchasable_dimensions, minimum_purchase_quantity, active
)
select listing.market_material_listing_id,
       'calculation_unit_1m2',
       'm2',
       '{"length_mm":1000,"width_mm":1000,"format_source":"owner_approved_calculation_unit"}'::jsonb,
       1,
       true
from public.reference_material_families family
join public.reference_material_models model on model.family_id = family.family_id and model.active
join public.reference_market_material_listings listing
  on listing.material_model_id = model.material_model_id and listing.market_code = 'IL' and listing.active
where family.family_code = 'natural_stone_slab'
on conflict (market_material_listing_id, supply_format_code) do update
set purchase_unit = excluded.purchase_unit,
    purchasable_dimensions = excluded.purchasable_dimensions,
    minimum_purchase_quantity = excluded.minimum_purchase_quantity,
    active = true,
    updated_at = now();

do $$
declare missing_formats integer;
begin
    select count(*) into missing_formats
    from public.reference_material_families family
    join public.reference_material_models model on model.family_id = family.family_id and model.active
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id and listing.market_code = 'IL' and listing.active
    left join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = 'calculation_unit_1m2' and format.active
    where family.family_code = 'natural_stone_slab'
      and format.supply_format_id is null;
    if missing_formats <> 0 then
        raise exception 'Natural-stone calculation units missing: %', missing_formats;
    end if;
end $$;

commit;
