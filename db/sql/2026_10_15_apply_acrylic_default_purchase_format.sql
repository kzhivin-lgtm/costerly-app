-- Owner-approved catalog policy: every active Israel acrylic PMMA position
-- uses 2400 x 1220 mm as its Engine purchase format until supplier-specific
-- listing formats are curated.  This is a catalog default, not source proof.
-- Run WITHOUT RLS.

begin;

insert into public.reference_market_material_supply_formats (
    market_material_listing_id,
    supply_format_code,
    purchase_unit,
    purchasable_dimensions,
    minimum_purchase_quantity,
    active
)
select listing.market_material_listing_id,
       'default_2400x1220',
       'sheet',
       '{"length_mm":2400,"width_mm":1220,"format_source":"owner_approved_catalog_default"}'::jsonb,
       1,
       true
from public.reference_material_families family
join public.reference_material_models model
  on model.family_id = family.family_id and model.active
join public.reference_market_material_listings listing
  on listing.material_model_id = model.material_model_id
 and listing.market_code = 'IL' and listing.active
where family.family_code = 'acrylic_pmma'
on conflict (market_material_listing_id, supply_format_code) do update
set purchase_unit = excluded.purchase_unit,
    purchasable_dimensions = excluded.purchasable_dimensions,
    minimum_purchase_quantity = excluded.minimum_purchase_quantity,
    active = true,
    updated_at = now();

do $$
declare
    missing_formats integer;
begin
    select count(*) into missing_formats
    from public.reference_material_families family
    join public.reference_material_models model
      on model.family_id = family.family_id and model.active
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    left join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = 'default_2400x1220'
     and format.active
    where family.family_code = 'acrylic_pmma'
      and format.supply_format_id is null;
    if missing_formats <> 0 then
        raise exception 'Every active acrylic listing must have default_2400x1220, missing %', missing_formats;
    end if;
end $$;

commit;
