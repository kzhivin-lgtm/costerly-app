-- Owner-approved physical formats for every active Israel Reference listing.
-- Run WITHOUT RLS.
begin;

create temporary table _format_seed (
    family_code text primary key,
    supply_format_code text not null,
    purchase_unit text not null,
    purchasable_dimensions jsonb not null
) on commit drop;

insert into _format_seed values
    ('fibreboard_hardboard', 'default_2440x1220', 'sheet',
        '{"length_mm":2440,"width_mm":1220,"format_source":"owner_approved_catalog_default"}'),
    ('particleboard', 'default_2440x1220', 'sheet',
        '{"length_mm":2440,"width_mm":1220,"format_source":"owner_approved_catalog_default"}'),
    ('solid_surface', 'default_3658x760', 'sheet',
        '{"length_mm":3658,"width_mm":760,"format_source":"owner_approved_catalog_default"}');

insert into public.reference_market_material_supply_formats (
    market_material_listing_id, supply_format_code, purchase_unit,
    purchasable_dimensions, minimum_purchase_quantity, active
)
select listing.market_material_listing_id, seed.supply_format_code, seed.purchase_unit,
       seed.purchasable_dimensions, 1, true
from _format_seed seed
join public.reference_material_families family
  on family.family_code = seed.family_code and family.active
join public.reference_material_models model
  on model.family_id = family.family_id and model.active
join public.reference_market_material_listings listing
  on listing.material_model_id = model.material_model_id
 and listing.market_code = 'IL' and listing.active
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
    from _format_seed seed
    join public.reference_material_families family on family.family_code = seed.family_code and family.active
    join public.reference_material_models model on model.family_id = family.family_id and model.active
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id and listing.market_code = 'IL' and listing.active
    left join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = seed.supply_format_code and format.active
    where format.supply_format_id is null;
    if missing_formats <> 0 then
        raise exception 'Board and solid-surface formats missing: %', missing_formats;
    end if;
end $$;

commit;
