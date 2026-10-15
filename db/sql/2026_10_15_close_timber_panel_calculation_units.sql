-- Owner decision: solid-timber panel positions priced by m² use a 1 m²
-- calculation segment. Timber priced by m³ is deliberately excluded here.
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
where family.family_code = 'timber_solid_wood_panel'
  and exists (
      select 1
      from public.reference_market_material_legacy_mappings mapping
      join public.market_material_model_prices price
        on price.material_id = mapping.legacy_material_id
       and price.market_code = 'IL' and price.status = 'active'
       and price.price_scope = 'material_only' and price.price_typical > 0
       and lower(price.unit) in ('m2', 'm²')
      where mapping.material_model_id = model.material_model_id
        and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
  )
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
    where family.family_code = 'timber_solid_wood_panel'
      and exists (
          select 1 from public.reference_market_material_legacy_mappings mapping
          join public.market_material_model_prices price
            on price.material_id = mapping.legacy_material_id
           and price.market_code = 'IL' and price.status = 'active'
           and price.price_scope = 'material_only' and price.price_typical > 0
           and lower(price.unit) in ('m2', 'm²')
          where mapping.material_model_id = model.material_model_id
            and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
      )
      and not exists (
          select 1 from public.reference_market_material_supply_formats format
          where format.market_material_listing_id = listing.market_material_listing_id
            and format.supply_format_code = 'calculation_unit_1m2' and format.active
      );
    if missing_formats <> 0 then
        raise exception 'Timber panel calculation units missing: %', missing_formats;
    end if;
end $$;

commit;
