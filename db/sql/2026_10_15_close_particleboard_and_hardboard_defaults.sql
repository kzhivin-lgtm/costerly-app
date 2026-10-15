-- Approved static defaults for the final two operational sheet Families.
-- Run WITHOUT RLS: this changes existing server-side tables and creates only
-- temporary tables. No permanent client-accessible table is created.

begin;

create temporary table _approved_sheet_defaults (
    family_code text primary key,
    material_model_code text not null,
    default_specifications jsonb not null,
    supply_format_code text not null,
    purchasable_dimensions jsonb not null
) on commit drop;

insert into _approved_sheet_defaults (
    family_code,
    material_model_code,
    default_specifications,
    supply_format_code,
    purchasable_dimensions
) values
    ('particleboard', 'gcm_v1_pb_p2_p2_furniture_grade_particleboard_raw_16_mm',
        '{"thickness":16}'::jsonb, 'default_2440x1220',
        '{"length_mm":2440,"width_mm":1220,"format_source":"approved_catalog_default"}'::jsonb),
    ('fibreboard_hardboard', 'gcm_v1_fb_hardboard_hardboard_standard_3_mm',
        '{"thickness":3}'::jsonb, 'default_2440x1220',
        '{"length_mm":2440,"width_mm":1220,"format_source":"approved_catalog_default"}'::jsonb);

create temporary table _selected_sheet_defaults on commit drop as
select seed.family_code,
       family.family_id,
       model.material_model_id as reference_position_id,
       seed.default_specifications,
       seed.supply_format_code,
       seed.purchasable_dimensions
from _approved_sheet_defaults seed
join public.reference_material_families family
  on family.family_code = seed.family_code and family.active
join public.reference_material_models model
  on model.family_id = family.family_id
 and model.material_model_code = seed.material_model_code
 and model.active
join public.reference_market_material_listings listing
  on listing.material_model_id = model.material_model_id
 and listing.market_code = 'IL' and listing.active
join public.reference_market_material_legacy_mappings mapping
  on mapping.material_model_id = model.material_model_id
 and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
join public.market_material_model_prices price
  on price.material_id = mapping.legacy_material_id
 and price.market_code = 'IL' and price.status = 'active'
 and price.price_scope = 'material_only' and price.price_typical > 0;

do $$
declare
    selected_count integer;
begin
    select count(*) into selected_count from _selected_sheet_defaults;
    if selected_count <> 2 then
        raise exception 'Expected 2 approved default positions, found %', selected_count;
    end if;
end $$;

insert into public.reference_material_family_default_variants (
    family_id, reference_position_id, default_specifications,
    applicability_specifications, priority, active
)
select family_id, reference_position_id, default_specifications,
       '{}'::jsonb, 10, true
from _selected_sheet_defaults
on conflict (family_id, priority) do update set
    reference_position_id = excluded.reference_position_id,
    default_specifications = excluded.default_specifications,
    applicability_specifications = excluded.applicability_specifications,
    active = true,
    updated_at = now();

insert into public.reference_market_material_supply_formats (
    market_material_listing_id, supply_format_code, purchase_unit,
    purchasable_dimensions, minimum_purchase_quantity, active
)
select listing.market_material_listing_id,
       selected.supply_format_code,
       'sheet',
       selected.purchasable_dimensions,
       1,
       true
from _selected_sheet_defaults selected
join public.reference_market_material_listings listing
  on listing.material_model_id = selected.reference_position_id
 and listing.market_code = 'IL' and listing.active
on conflict (market_material_listing_id, supply_format_code) do update set
    purchase_unit = excluded.purchase_unit,
    purchasable_dimensions = excluded.purchasable_dimensions,
    minimum_purchase_quantity = excluded.minimum_purchase_quantity,
    active = true,
    updated_at = now();

do $$
declare
    incomplete_count integer;
begin
    select count(*) into incomplete_count
    from _selected_sheet_defaults selected
    left join public.reference_material_family_default_variants variant
      on variant.family_id = selected.family_id
     and variant.reference_position_id = selected.reference_position_id
     and variant.priority = 10 and variant.active
    left join public.reference_market_material_listings listing
      on listing.material_model_id = selected.reference_position_id
     and listing.market_code = 'IL' and listing.active
    left join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = selected.supply_format_code and format.active
    where variant.default_variant_id is null
       or format.supply_format_id is null;
    if incomplete_count <> 0 then
        raise exception 'Approved particleboard or hardboard default is incomplete: %', incomplete_count;
    end if;
end $$;

commit;
