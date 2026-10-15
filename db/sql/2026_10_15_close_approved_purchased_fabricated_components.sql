-- Owner-approved closure of the remaining purchased fabricated components.
-- Removed components are retained historically, but made inactive so neither
-- Price Source nor Resolver can select them. Run WITHOUT RLS.

begin;

create temporary table _retired_component (
    canonical_name text primary key
) on commit drop;

insert into _retired_component values
    ('Cane webbing'),
    ('Furniture linoleum worktop panel'),
    ('Magnetic whiteboard panel');

update public.reference_market_material_listings listing
set active = false,
    updated_at = now()
from public.reference_material_models model,
     public.reference_material_families family,
     _retired_component retired
where listing.material_model_id = model.material_model_id
  and listing.market_code = 'IL'
  and family.family_id = model.family_id
  and family.family_code = 'purchased_fabricated_component'
  and retired.canonical_name = model.canonical_name
  and listing.active;

update public.reference_material_models model
set active = false,
    updated_at = now()
from public.reference_material_families family,
     _retired_component retired
where model.family_id = family.family_id
  and family.family_code = 'purchased_fabricated_component'
  and retired.canonical_name = model.canonical_name
  and model.active;

-- These price values are owner-confirmed prices of one complete component,
-- not area prices requiring a unit conversion.
create temporary table _set_component (
    canonical_name text primary key
) on commit drop;

insert into _set_component values
    ('Aluminium frame glass door'),
    ('Ready-made cabinet door economy'),
    ('Ready-made cabinet door premium');

update public.market_material_model_prices price
set unit = 'set',
    updated_at = now()
from public.reference_material_models model
join public.reference_material_families family
  on family.family_id = model.family_id
join public.reference_market_material_legacy_mappings mapping
  on mapping.material_model_id = model.material_model_id
 and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
join _set_component component
  on component.canonical_name = model.canonical_name
where price.material_id = mapping.legacy_material_id
  and price.market_code = 'IL'
  and price.status = 'active'
  and price.currency = 'ILS'
  and family.family_code = 'purchased_fabricated_component';

create temporary table _one_m2_component (
    canonical_name text primary key
) on commit drop;

insert into _one_m2_component values
    ('Acoustic felt panel'),
    ('Decorative metal mesh panel'),
    ('Natural rattan sheet'),
    ('Synthetic rattan sheet');

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
from _one_m2_component component
join public.reference_material_models model
  on model.canonical_name = component.canonical_name and model.active
join public.reference_material_families family
  on family.family_id = model.family_id
 and family.family_code = 'purchased_fabricated_component'
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
    retired_count integer;
    set_count integer;
    format_count integer;
begin
    select count(*) into retired_count
    from _retired_component retired
    join public.reference_material_models model on model.canonical_name = retired.canonical_name
    join public.reference_material_families family
      on family.family_id = model.family_id
     and family.family_code = 'purchased_fabricated_component'
    where not model.active;
    if retired_count <> 3 then
        raise exception 'Expected three retired fabricated components, found %', retired_count;
    end if;

    select count(*) into set_count
    from _set_component component
    join public.reference_material_models model on model.canonical_name = component.canonical_name
    join public.reference_material_families family
      on family.family_id = model.family_id
     and family.family_code = 'purchased_fabricated_component'
    join public.reference_market_material_legacy_mappings mapping
      on mapping.material_model_id = model.material_model_id
     and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
    join public.market_material_model_prices price
      on price.material_id = mapping.legacy_material_id
     and price.market_code = 'IL' and price.status = 'active' and price.unit = 'set';
    if set_count <> 3 then
        raise exception 'Expected three fabricated components priced per set, found %', set_count;
    end if;

    select count(*) into format_count
    from _one_m2_component component
    join public.reference_material_models model on model.canonical_name = component.canonical_name
    join public.reference_material_families family
      on family.family_id = model.family_id
     and family.family_code = 'purchased_fabricated_component'
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = 'calculation_unit_1m2' and format.active
     and format.purchasable_dimensions @> '{"length_mm":1000,"width_mm":1000}'::jsonb;
    if format_count <> 4 then
        raise exception 'Expected four fabricated 1m2 calculation formats, found %', format_count;
    end if;
end $$;

commit;
