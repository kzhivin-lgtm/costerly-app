-- 3.17.3.6.  A normal raw MDF 20 mm Israel Reference position.
-- Its prices are explicitly the active standard raw MDF 19 mm prices plus 10%.

begin;

insert into public.reference_materials (
    material_id, material_code, department, category_code, canonical_name,
    base_unit, specifications, active
)
select
    '67b25123-b693-4ed4-9e89-8a155a71880f'::uuid,
    'gcm_v1_mdf_standard_standard_mdf_raw_20_mm',
    source_material.department,
    source_material.category_code,
    'MDF, 20 mm, Standard, raw',
    source_material.base_unit,
    jsonb_build_object(
        'catalog_origin', 'approved_catalog_extension',
        'source_model_code', 'gcm_v1_mdf_standard_standard_mdf_raw_19_mm',
        'price_adjustment_percent', 10
    ),
    true
from public.reference_materials source_material
join public.reference_material_models source_model
  on source_model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_19_mm'
join public.reference_market_material_legacy_mappings source_mapping
  on source_mapping.material_model_id = source_model.material_model_id
 and source_mapping.market_code = 'IL'
 and source_mapping.classification_status = 'mapped'
where source_material.material_id = source_mapping.legacy_material_id
on conflict (material_code) do update set
    canonical_name = excluded.canonical_name,
    base_unit = excluded.base_unit,
    specifications = excluded.specifications,
    active = true,
    updated_at = now();

insert into public.reference_material_models (
    material_model_id, family_id, material_model_code, canonical_name, active
)
select
    'd71997a6-ce00-4e61-83ca-5b4b1b786bd8'::uuid,
    source_model.family_id,
    'gcm_v1_mdf_standard_standard_mdf_raw_20_mm',
    'MDF, 20 mm, Standard, raw',
    true
from public.reference_material_models source_model
where source_model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_19_mm'
on conflict (material_model_code) do update set
    family_id = excluded.family_id,
    canonical_name = excluded.canonical_name,
    active = true,
    updated_at = now();

insert into public.reference_market_material_listings (
    market_material_listing_id, market_code, material_model_id, listing_code,
    canonical_market_name, availability_status, active
)
select
    '79ac2fa4-ef81-4d87-b192-258a2e1aa620'::uuid,
    'IL', model.material_model_id, 'il_gcm_mdf_standard_raw_20',
    'MDF, 20 mm, Standard, raw', 'common', true
from public.reference_material_models model
where model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_20_mm'
on conflict (market_code, listing_code) do update set
    material_model_id = excluded.material_model_id,
    canonical_market_name = excluded.canonical_market_name,
    availability_status = excluded.availability_status,
    active = true,
    updated_at = now();

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id, model.family_id, value.attribute_code, value.attribute_value
from public.reference_material_models model
cross join (
    values
        ('board_type'::text, to_jsonb('mdf'::text)),
        ('surface'::text, to_jsonb('raw'::text)),
        ('thickness'::text, to_jsonb(20.0))
) as value(attribute_code, attribute_value)
where model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_20_mm'
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

insert into public.reference_market_material_supply_formats (
    supply_format_id, market_material_listing_id, supply_format_code,
    purchase_unit, purchasable_dimensions, minimum_purchase_quantity, active
)
select
    '4b1ce4c0-480c-404a-8664-dfcbb2a9ff31'::uuid,
    target_listing.market_material_listing_id,
    source_format.supply_format_code,
    source_format.purchase_unit,
    source_format.purchasable_dimensions,
    source_format.minimum_purchase_quantity,
    true
from public.reference_market_material_listings target_listing
join public.reference_material_models target_model
  on target_model.material_model_id = target_listing.material_model_id
join public.reference_material_models source_model
  on source_model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_19_mm'
join public.reference_market_material_listings source_listing
  on source_listing.market_code = 'IL'
 and source_listing.material_model_id = source_model.material_model_id
join public.reference_market_material_supply_formats source_format
  on source_format.market_material_listing_id = source_listing.market_material_listing_id
 and source_format.active
where target_listing.market_code = 'IL'
  and target_model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_20_mm'
on conflict (market_material_listing_id, supply_format_code) do update set
    purchase_unit = excluded.purchase_unit,
    purchasable_dimensions = excluded.purchasable_dimensions,
    minimum_purchase_quantity = excluded.minimum_purchase_quantity,
    active = true,
    updated_at = now();

insert into public.reference_market_material_legacy_mappings (
    legacy_mapping_id, legacy_material_id, market_code, family_id,
    material_model_id, market_material_listing_id, classification_status,
    classification_basis, classification_evidence
)
select
    '24dae264-3520-4831-a1d2-ef24fd13b192'::uuid,
    material.material_id, 'IL', model.family_id, model.material_model_id,
    listing.market_material_listing_id, 'mapped', 'catalog_seed',
    jsonb_build_object(
        'source_model_code', 'gcm_v1_mdf_standard_standard_mdf_raw_19_mm',
        'price_adjustment_percent', 10
    )
from public.reference_materials material
join public.reference_material_models model
  on model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_20_mm'
join public.reference_market_material_listings listing
  on listing.market_code = 'IL' and listing.material_model_id = model.material_model_id
where material.material_code = 'gcm_v1_mdf_standard_standard_mdf_raw_20_mm'
on conflict (legacy_material_id) do update set
    family_id = excluded.family_id,
    material_model_id = excluded.material_model_id,
    market_material_listing_id = excluded.market_material_listing_id,
    classification_status = excluded.classification_status,
    classification_basis = excluded.classification_basis,
    classification_evidence = excluded.classification_evidence,
    updated_at = now();

insert into public.market_material_model_prices (
    model_price_id, material_id, market_code, catalog_version,
    price_low, price_typical, price_high, unit, currency, price_scope,
    pricing_method, confidence, anchor_count, formula_description,
    model_metadata, effective_from, effective_to, status
)
select
    '1e7ede0b-c502-468e-9792-02144819f5ca'::uuid,
    target_material.material_id, source_price.market_code, source_price.catalog_version,
    round(source_price.price_low * 1.10, 6),
    round(source_price.price_typical * 1.10, 6),
    round(source_price.price_high * 1.10, 6),
    source_price.unit, source_price.currency, source_price.price_scope,
    source_price.pricing_method, source_price.confidence, source_price.anchor_count,
    'Standard raw MDF 20 mm: active standard raw MDF 19 mm Israel Reference price plus 10%.',
    source_price.model_metadata || jsonb_build_object(
        'source_model_code', 'gcm_v1_mdf_standard_standard_mdf_raw_19_mm',
        'price_adjustment_percent', 10
    ),
    source_price.effective_from, null, 'active'
from public.reference_materials target_material
join public.reference_material_models source_model
  on source_model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_19_mm'
join public.reference_market_material_legacy_mappings source_mapping
  on source_mapping.material_model_id = source_model.material_model_id
 and source_mapping.market_code = 'IL'
 and source_mapping.classification_status = 'mapped'
join public.market_material_model_prices source_price
  on source_price.material_id = source_mapping.legacy_material_id
 and source_price.market_code = 'IL'
 and source_price.status = 'active'
where target_material.material_code = 'gcm_v1_mdf_standard_standard_mdf_raw_20_mm'
on conflict (material_id, market_code, catalog_version) do update set
    price_low = excluded.price_low,
    price_typical = excluded.price_typical,
    price_high = excluded.price_high,
    unit = excluded.unit,
    currency = excluded.currency,
    price_scope = excluded.price_scope,
    pricing_method = excluded.pricing_method,
    confidence = excluded.confidence,
    anchor_count = excluded.anchor_count,
    formula_description = excluded.formula_description,
    model_metadata = excluded.model_metadata,
    effective_from = excluded.effective_from,
    effective_to = null,
    status = 'active',
    updated_at = now();

do $$
begin
    if not exists (
        select 1
        from public.reference_material_models model
        join public.reference_material_model_attribute_values board_type
          on board_type.material_model_id = model.material_model_id
         and board_type.attribute_code = 'board_type'
         and board_type.attribute_value = '"mdf"'::jsonb
        join public.reference_material_model_attribute_values surface
          on surface.material_model_id = model.material_model_id
         and surface.attribute_code = 'surface'
         and surface.attribute_value = '"raw"'::jsonb
        join public.reference_material_model_attribute_values thickness
          on thickness.material_model_id = model.material_model_id
         and thickness.attribute_code = 'thickness'
         and thickness.attribute_value = '20.0'::jsonb
        join public.reference_market_material_listings listing
          on listing.material_model_id = model.material_model_id
         and listing.market_code = 'IL' and listing.active
        join public.reference_market_material_supply_formats supply
          on supply.market_material_listing_id = listing.market_material_listing_id
         and supply.active
        join public.reference_market_material_legacy_mappings mapping
          on mapping.material_model_id = model.material_model_id
         and mapping.classification_status = 'mapped'
        join public.market_material_model_prices price
          on price.material_id = mapping.legacy_material_id
         and price.market_code = 'IL' and price.status = 'active'
        where model.material_model_code = 'gcm_v1_mdf_standard_standard_mdf_raw_20_mm'
    ) then
        raise exception 'Israel Reference raw MDF 20 mm is incomplete';
    end if;
end $$;

commit;
