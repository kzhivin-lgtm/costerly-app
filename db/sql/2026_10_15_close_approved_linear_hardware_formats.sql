-- Owner-approved hardware purchasing units and linear stock formats.
--
-- The price values below are already the approved price for one item where
-- their previous source unit was mistakenly recorded as metre.  This does
-- not derive an item price from a length.  It corrects that stored unit.
-- Purchased fabricated components are intentionally out of scope.
-- Run WITHOUT RLS.

begin;

create temporary table _price_unit_correction (
    canonical_name text primary key,
    family_code text not null,
    corrected_unit text not null
) on commit drop;

insert into _price_unit_correction values
    ('Profile handle', 'hardware_handle', 'ea'),
    ('Wardrobe rail', 'hardware_storage_system', 'ea'),
    ('Piano hinge, heavy-duty', 'hardware_hinge', 'ea'),
    ('Piano hinge, light-duty', 'hardware_hinge', 'ea'),
    ('Piano hinge, medium-duty', 'hardware_hinge', 'ea');

update public.market_material_model_prices price
set unit = correction.corrected_unit,
    updated_at = now()
from _price_unit_correction correction
join public.reference_material_families family
  on family.family_code = correction.family_code and family.active
join public.reference_material_models model
  on model.family_id = family.family_id
 and model.canonical_name = correction.canonical_name
join public.reference_market_material_legacy_mappings mapping
  on mapping.material_model_id = model.material_model_id
 and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
where price.material_id = mapping.legacy_material_id
  and price.market_code = 'IL'
  and price.status = 'active'
  and price.currency = 'ILS'
  and price.unit = 'm';

create temporary table _linear_format_seed (
    canonical_name text primary key,
    family_code text not null,
    supply_format_code text not null,
    length_mm integer not null
) on commit drop;

insert into _linear_format_seed values
    -- Cable is calculated and purchased in one-metre increments.
    ('Cable and low-voltage wiring allowance', 'hardware_electrical_component',
        'calculation_unit_1000mm', 1000),
    -- LED strips are purchased as five-metre spools.
    ('COB LED strip', 'hardware_electrical_component', 'spool_5000mm', 5000),
    ('LED strip high output', 'hardware_electrical_component', 'spool_5000mm', 5000),
    ('LED strip standard output', 'hardware_electrical_component', 'spool_5000mm', 5000),
    -- Lighting profiles and their diffusers are purchased in two-metre stock.
    ('LED aluminium profile recessed', 'hardware_electrical_component',
        'stock_2000mm', 2000),
    ('LED aluminium profile surface-mounted', 'hardware_electrical_component',
        'stock_2000mm', 2000),
    ('LED diffuser', 'hardware_electrical_component', 'stock_2000mm', 2000);

insert into public.reference_market_material_supply_formats (
    market_material_listing_id, supply_format_code, purchase_unit,
    purchasable_dimensions, minimum_purchase_quantity, active
)
select listing.market_material_listing_id,
       seed.supply_format_code,
       'linear_stock',
       jsonb_build_object(
           'length_mm', seed.length_mm,
           'format_source', 'owner_approved_catalog_default'
       ),
       1,
       true
from _linear_format_seed seed
join public.reference_material_families family
  on family.family_code = seed.family_code and family.active
join public.reference_material_models model
  on model.family_id = family.family_id
 and model.canonical_name = seed.canonical_name and model.active
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
declare
    corrected_count integer;
    format_count integer;
    pine_sheet_count integer;
begin
    select count(*) into corrected_count
    from _price_unit_correction correction
    join public.reference_material_families family
      on family.family_code = correction.family_code and family.active
    join public.reference_material_models model
      on model.family_id = family.family_id
     and model.canonical_name = correction.canonical_name
    join public.reference_market_material_legacy_mappings mapping
      on mapping.material_model_id = model.material_model_id
     and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
    join public.market_material_model_prices price
      on price.material_id = mapping.legacy_material_id
     and price.market_code = 'IL' and price.status = 'active'
     and price.currency = 'ILS' and price.unit = correction.corrected_unit;
    if corrected_count <> 5 then
        raise exception 'Expected 5 corrected per-item hardware prices, found %', corrected_count;
    end if;

    select count(*) into format_count
    from _linear_format_seed seed
    join public.reference_material_families family
      on family.family_code = seed.family_code and family.active
    join public.reference_material_models model
      on model.family_id = family.family_id
     and model.canonical_name = seed.canonical_name
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = seed.supply_format_code and format.active;
    if format_count <> 7 then
        raise exception 'Expected 7 approved linear hardware formats, found %', format_count;
    end if;

    select count(*) into pine_sheet_count
    from public.reference_material_models model
    join public.reference_material_families family
      on family.family_id = model.family_id
     and family.family_code = 'timber_solid_wood_panel'
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = 'standard_2400x1220' and format.active
     and format.purchasable_dimensions @> '{"length_mm":2400,"width_mm":1220}'::jsonb
    where model.canonical_name in (
        'Solid timber panel, Pine, 18 mm, edge-glued',
        'Solid timber panel, Pine, 28 mm, edge-glued'
    );
    if pine_sheet_count <> 2 then
        raise exception 'Expected two confirmed Pine 2400x1220 sheet formats, found %', pine_sheet_count;
    end if;
end $$;

commit;
