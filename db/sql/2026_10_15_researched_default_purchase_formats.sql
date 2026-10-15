-- Research-backed purchase formats for approved default positions.
--
-- This migration does not invent supplier facts.  It supplies a deterministic
-- default format only where the pricing/default policy requires one.
-- Sources recorded in the catalog decision:
--   * brass / copper: stocked 1000 x 2000 mm sheets
--   * engineered quartz: 3050 x 1440 mm standard slab
--   * solid surface (Corian class): 12 x 760 x 3658 mm standard sheet
-- Natural stone is intentionally a calculation unit of 1 m², as approved,
-- not a claim that suppliers sell only 1000 x 1000 mm slabs.

begin;

-- Make room for the research-backed Corian-class default before adding it.
-- This also makes the migration safe if a later seed had already selected a
-- different Solid Surface default.
update public.reference_material_family_supply_formats format
set is_default = false,
    updated_at = now()
from public.reference_material_families family
where format.family_id = family.family_id
  and family.family_code = 'solid_surface'
  and format.active
  and format.is_default;

-- Keep the global family registry capable of validating the research-backed
-- Corian-class sheet.  It is an allowed format, not a supplier-specific one.
insert into public.reference_material_family_supply_formats (
    family_id, purchasable_dimensions, is_default, active
)
select family.family_id,
       '{"length_mm":3658,"width_mm":760}'::jsonb,
       true,
       true
from public.reference_material_families family
where family.family_code = 'solid_surface'
on conflict (family_id, purchasable_dimensions) do update
set is_default = true,
    active = true,
    updated_at = now();

create temporary table _default_format_seed (
    family_code text not null,
    lookup_specifications jsonb not null,
    supply_format_code text not null,
    purchase_unit text not null,
    purchasable_dimensions jsonb not null,
    primary key (family_code, supply_format_code)
) on commit drop;

insert into _default_format_seed (
    family_code,
    lookup_specifications,
    supply_format_code,
    purchase_unit,
    purchasable_dimensions
) values
    ('sheet_metal', '{"metal_type":"carbon steel","thickness":1.5}',
        'default_3000x1500_carbon_steel', 'sheet',
        '{"length_mm":3000,"width_mm":1500,"format_source":"approved_catalog_default"}'),
    ('sheet_metal', '{"metal_type":"stainless steel","thickness":1.5}',
        'default_3000x1500_stainless_steel', 'sheet',
        '{"length_mm":3000,"width_mm":1500,"format_source":"approved_catalog_default"}'),
    ('sheet_metal', '{"metal_type":"aluminium","thickness":1.5}',
        'default_3000x1500_aluminium', 'sheet',
        '{"length_mm":3000,"width_mm":1500,"format_source":"approved_catalog_default"}'),
    ('sheet_metal', '{"metal_type":"copper","thickness":1.5}',
        'default_2000x1000_copper', 'sheet',
        '{"length_mm":2000,"width_mm":1000,"format_source":"industry_reference_default"}'),
    ('sheet_metal', '{"metal_type":"brass","thickness":1.5}',
        'default_2000x1000_brass', 'sheet',
        '{"length_mm":2000,"width_mm":1000,"format_source":"industry_reference_default"}'),
    ('engineered_quartz_mineral_hybrid', '{"thickness":20}',
        'default_3050x1440', 'slab',
        '{"length_mm":3050,"width_mm":1440,"format_source":"industry_reference_default"}'),
    ('solid_surface', '{"thickness":12}',
        'default_3658x760', 'sheet',
        '{"length_mm":3658,"width_mm":760,"format_source":"industry_reference_default"}'),
    ('natural_stone_slab', '{"stone_type":"marble","thickness":20}',
        'calculation_unit_1m2', 'm2',
        '{"length_mm":1000,"width_mm":1000,"format_source":"approved_calculation_unit"}');

-- Apply a format only to matching Israel Reference positions.  A real
-- supplier-specific format can coexist under another format code later.
insert into public.reference_market_material_supply_formats (
    market_material_listing_id,
    supply_format_code,
    purchase_unit,
    purchasable_dimensions,
    minimum_purchase_quantity,
    active
)
select listing.market_material_listing_id,
       seed.supply_format_code,
       seed.purchase_unit,
       seed.purchasable_dimensions,
       1,
       true
from _default_format_seed seed
join public.reference_material_families family
  on family.family_code = seed.family_code and family.active
join public.reference_material_models model
  on model.family_id = family.family_id and model.active
join lateral (
    select jsonb_object_agg(value.attribute_code, value.attribute_value) as specifications
    from public.reference_material_model_attribute_values value
    where value.material_model_id = model.material_model_id
) attributes on attributes.specifications @> seed.lookup_specifications
join public.reference_market_material_listings listing
  on listing.material_model_id = model.material_model_id
 and listing.market_code = 'IL'
 and listing.active
on conflict (market_material_listing_id, supply_format_code) do update
set purchase_unit = excluded.purchase_unit,
    purchasable_dimensions = excluded.purchasable_dimensions,
    minimum_purchase_quantity = excluded.minimum_purchase_quantity,
    active = true,
    updated_at = now();

-- Change the Solid Surface default from the former unverified 6 mm choice to
-- a 12 mm Israel position with an active material-only price.
with candidates as (
    select model.material_model_id,
           row_number() over (
               order by price.price_typical asc, model.material_model_code asc
           ) as candidate_rank
    from public.reference_material_families family
    join public.reference_material_models model
      on model.family_id = family.family_id and model.active
    join lateral (
        select jsonb_object_agg(value.attribute_code, value.attribute_value) as specifications
        from public.reference_material_model_attribute_values value
        where value.material_model_id = model.material_model_id
    ) attributes on attributes.specifications @> '{"thickness":12}'::jsonb
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    join public.reference_market_material_legacy_mappings mapping
      on mapping.material_model_id = model.material_model_id
     and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
    join public.market_material_model_prices price
      on price.material_id = mapping.legacy_material_id
     and price.market_code = 'IL' and price.status = 'active'
     and price.price_scope = 'material_only' and price.price_typical > 0
    where family.family_code = 'solid_surface'
)
update public.reference_material_family_default_variants variant
set reference_position_id = candidate.material_model_id,
    default_specifications = '{"thickness":12}'::jsonb,
    updated_at = now()
from candidates candidate
join public.reference_material_families family
  on family.family_code = 'solid_surface'
where variant.family_id = family.family_id
  and variant.priority = 10
  and candidate.candidate_rank = 1;

do $$
declare
    missing_formats integer;
    solid_default_thickness numeric;
begin
    select count(*) into missing_formats
    from _default_format_seed seed
    join public.reference_material_families family
      on family.family_code = seed.family_code
    join public.reference_material_models model
      on model.family_id = family.family_id and model.active
    join lateral (
        select jsonb_object_agg(value.attribute_code, value.attribute_value) as specifications
        from public.reference_material_model_attribute_values value
        where value.material_model_id = model.material_model_id
    ) attributes on attributes.specifications @> seed.lookup_specifications
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    left join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = seed.supply_format_code
     and format.active
    where format.supply_format_id is null;

    if missing_formats <> 0 then
        raise exception 'Expected researched default formats for every matching Israel position, missing %', missing_formats;
    end if;

    select (attributes.specifications ->> 'thickness')::numeric
      into solid_default_thickness
    from public.reference_material_family_default_variants variant
    join public.reference_material_families family on family.family_id = variant.family_id
    join lateral (
        select jsonb_object_agg(value.attribute_code, value.attribute_value) as specifications
        from public.reference_material_model_attribute_values value
        where value.material_model_id = variant.reference_position_id
    ) attributes on true
    where family.family_code = 'solid_surface'
      and variant.priority = 10
      and variant.active;

    if solid_default_thickness is distinct from 12 then
        raise exception 'Solid Surface default must resolve to a 12 mm Israel position, found %', solid_default_thickness;
    end if;
end $$;

commit;
