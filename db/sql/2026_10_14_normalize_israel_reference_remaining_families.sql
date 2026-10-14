-- Israel Reference normalization, stage 4.
--
-- Completes the remaining seven Families.  Four use their existing Israel
-- source rows and existing active prices.  The final three have no source row
-- at all, so their price rows are explicitly marked modeled_fallback with
-- documented public-market evidence.  They are not supplier evidence.

begin;

-- Existing source rows with an explicit name are moved into their exact
-- Family.  Missing Pricing-Key facts receive the owner-approved default only
-- after Family is proven.
create temporary table _remaining_source_targets on commit drop as
select material.material_id,
       material.material_code,
       material.canonical_name as source_name,
       mapping.market_code,
       family.family_id,
       family.family_code,
       case
           when material.canonical_name ilike '%foil%' then
               'Decorative film, 1220 mm, ' || material.canonical_name
           when material.canonical_name ilike '%flat bar%' then
               'Metal flat bar, ' || case
                   when material.canonical_name ilike 'Stainless steel%' then 'stainless steel'
                   when material.canonical_name ilike 'Aluminium%' then 'aluminium'
                   when material.canonical_name ilike 'Brass%' then 'brass'
                   when material.canonical_name ilike 'Copper%' then 'copper'
                   else 'carbon steel'
               end || ', 30 × 1.5 mm, ' || material.canonical_name
           when material.canonical_name ilike '%round bar%' then
               'Metal round bar, ' || case
                   when material.canonical_name ilike 'Stainless steel%' then 'stainless steel'
                   when material.canonical_name ilike 'Aluminium%' then 'aluminium'
                   when material.canonical_name ilike 'Brass%' then 'brass'
                   when material.canonical_name ilike 'Copper%' then 'copper'
                   else 'carbon steel'
               end || ', Ø10 mm, ' || material.canonical_name
           else
               'Sheet metal, ' || case
                   when material.canonical_name ilike 'Stainless steel%' then 'stainless steel'
                   when material.canonical_name ilike 'Aluminium%' then 'aluminium'
                   when material.canonical_name ilike 'Brass%' then 'brass'
                   when material.canonical_name ilike 'Copper%' then 'copper'
                   else 'carbon steel'
               end || ', 1.5 mm, ' || material.canonical_name
       end as canonical_name
from public.reference_materials material
join public.reference_market_material_legacy_mappings mapping
  on mapping.legacy_material_id = material.material_id
 and mapping.market_code = 'IL'
 and mapping.classification_status = 'review_required'
join public.reference_material_families family on family.family_code = case
    when material.canonical_name ilike '%foil%' then 'decorative_film_foil'
    when material.department = 'metal' and material.canonical_name ilike '%flat bar%' then 'metal_flat_bar'
    when material.department = 'metal' and material.canonical_name ilike '%round bar%' then 'metal_round_bar_rod_wire'
    when material.department = 'metal' and (
        material.canonical_name ilike '%sheet%'
        or material.canonical_name ilike '%plate%'
    ) then 'sheet_metal'
end
where material.active
  and (
      material.canonical_name ilike '%foil%'
      or (material.department = 'metal' and (
          material.canonical_name ilike '%flat bar%'
          or material.canonical_name ilike '%round bar%'
          or material.canonical_name ilike '%sheet%'
          or material.canonical_name ilike '%plate%'
      ))
  );

insert into public.reference_material_models (
    family_id, material_model_code, canonical_name, active
)
select target.family_id, 'il_' || target.material_code, target.canonical_name, true
from _remaining_source_targets target
on conflict (material_model_code) do update set
    family_id = excluded.family_id,
    canonical_name = excluded.canonical_name,
    active = true,
    updated_at = now();

insert into public.reference_market_material_listings (
    market_code, material_model_id, listing_code, canonical_market_name,
    availability_status, active
)
select target.market_code,
       model.material_model_id,
       'il_' || target.material_code,
       target.canonical_name,
       'common',
       true
from _remaining_source_targets target
join public.reference_material_models model
  on model.material_model_code = 'il_' || target.material_code
on conflict (market_code, listing_code) do update set
    material_model_id = excluded.material_model_id,
    canonical_market_name = excluded.canonical_market_name,
    active = true,
    updated_at = now();

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id, target.family_id, attribute_code, attribute_value
from _remaining_source_targets target
join public.reference_material_models model
  on model.material_model_code = 'il_' || target.material_code
cross join lateral (
    select 'width'::text as attribute_code, to_jsonb(1220::numeric) as attribute_value
    where target.family_code = 'decorative_film_foil'
    union all
    select 'width_thickness', jsonb_build_object('width_mm', 30, 'thickness_mm', 1.5)
    where target.family_code = 'metal_flat_bar'
    union all
    select 'diameter', to_jsonb(10::numeric)
    where target.family_code = 'metal_round_bar_rod_wire'
    union all
    select 'thickness', to_jsonb(1.5::numeric)
    where target.family_code = 'sheet_metal'
    union all
    select 'metal_type', to_jsonb(case
        when target.source_name ilike 'Stainless steel%' then 'stainless steel'
        when target.source_name ilike 'Aluminium%' then 'aluminium'
        when target.source_name ilike 'Brass%' then 'brass'
        when target.source_name ilike 'Copper%' then 'copper'
        else 'carbon steel'
    end)
    where target.family_code in ('metal_flat_bar', 'metal_round_bar_rod_wire', 'sheet_metal')
) attributes
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

update public.reference_market_material_legacy_mappings mapping
set family_id = target.family_id,
    material_model_id = model.material_model_id,
    market_material_listing_id = listing.market_material_listing_id,
    classification_status = 'mapped',
    classification_basis = 'deterministic_rule',
    classification_evidence = mapping.classification_evidence || jsonb_build_object(
        'normalization_rule', 'explicit_source_name_with_approved_default_key',
        'target_family', target.family_code
    ),
    updated_at = now()
from _remaining_source_targets target
join public.reference_material_models model
  on model.material_model_code = 'il_' || target.material_code
join public.reference_market_material_listings listing
  on listing.market_code = target.market_code
 and listing.material_model_id = model.material_model_id
where mapping.legacy_material_id = target.material_id;

-- Three missing market baselines.  Each position and price is deliberately
-- labelled modeled_fallback because there is no Israel supplier source row.
create temporary table _modeled_baselines (
    material_code text primary key,
    family_code text not null,
    department text not null,
    canonical_name text not null,
    base_unit text not null,
    price_low numeric not null,
    price_typical numeric not null,
    price_high numeric not null,
    source_url text not null,
    source_note text not null,
    attributes jsonb not null
) on commit drop;

insert into _modeled_baselines values
    (
        'il_modeled_aluminium_composite_panel_4mm',
        'aluminium_composite_panel', 'metal',
        'Aluminium composite panel, 4 mm', 'm2',
        250, 300, 350,
        'https://www.alumi.co.il/%D7%9E%D7%94-%D7%96%D7%94-%D7%90%D7%9C%D7%95%D7%A7%D7%95%D7%91%D7%95%D7%A0%D7%93',
        'Public Israel market range for 4 mm Alucobond, 2026; material-only proxy.',
        '{"thickness": 4}'::jsonb
    ),
    (
        'il_modeled_terrazzo_20mm',
        'terrazzo_engineered_agglomerate', 'glass_stone_plastic',
        'Terrazzo, 20 mm', 'm2',
        180, 255, 400,
        'https://www.tivron.co.il/prices',
        'Public Israel terrazzo material market point, 2026; broad range retained because source does not state 20 mm slab specification.',
        '{"thickness": 20}'::jsonb
    ),
    (
        'il_modeled_vinyl_film_1220mm',
        'vinyl_film', 'wood',
        'Vinyl film, 1220 mm', 'm2',
        36, 45.15, 60,
        'https://madbekot-kir.co.il/product/%D7%95%D7%99%D7%A0%D7%99%D7%9C-%D7%97%D7%99%D7%AA%D7%95%D7%9A-%D7%90%D7%99%D7%A9%D7%99/',
        'Derived from public 65 ILS per linear metre retail listing at 1220 mm width, converted to estimated VAT-exclusive square-metre basis.',
        '{"width": 1220}'::jsonb
    );

insert into public.reference_materials (
    material_code, department, category_code, canonical_name, base_unit,
    specifications, active
)
select baseline.material_code,
       baseline.department,
       (
           select template.category_code
           from public.reference_materials template
           where template.active
             and template.department = baseline.department
           order by template.material_code
           limit 1
       ),
       baseline.canonical_name,
       baseline.base_unit,
       jsonb_build_object(
           'catalog_origin', 'modeled_market_baseline',
           'source_url', baseline.source_url,
           'source_note', baseline.source_note
       ),
       true
from _modeled_baselines baseline
on conflict (material_code) do update set
    canonical_name = excluded.canonical_name,
    base_unit = excluded.base_unit,
    specifications = excluded.specifications,
    active = true,
    updated_at = now();

insert into public.reference_material_models (
    family_id, material_model_code, canonical_name, active
)
select family.family_id, baseline.material_code, baseline.canonical_name, true
from _modeled_baselines baseline
join public.reference_material_families family on family.family_code = baseline.family_code
on conflict (material_model_code) do update set
    family_id = excluded.family_id,
    canonical_name = excluded.canonical_name,
    active = true,
    updated_at = now();

insert into public.reference_market_material_listings (
    market_code, material_model_id, listing_code, canonical_market_name,
    availability_status, active
)
select 'IL', model.material_model_id, baseline.material_code,
       baseline.canonical_name, 'common', true
from _modeled_baselines baseline
join public.reference_material_models model on model.material_model_code = baseline.material_code
on conflict (market_code, listing_code) do update set
    material_model_id = excluded.material_model_id,
    canonical_market_name = excluded.canonical_market_name,
    active = true,
    updated_at = now();

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id, family.family_id, attribute.key, attribute.value
from _modeled_baselines baseline
join public.reference_material_families family on family.family_code = baseline.family_code
join public.reference_material_models model on model.material_model_code = baseline.material_code
cross join lateral jsonb_each(baseline.attributes) attribute
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

insert into public.reference_market_material_legacy_mappings (
    legacy_material_id, market_code, family_id, material_model_id,
    market_material_listing_id, classification_status, classification_basis,
    classification_evidence
)
select material.material_id, 'IL', family.family_id, model.material_model_id,
       listing.market_material_listing_id, 'mapped', 'catalog_seed',
       jsonb_build_object(
           'catalog_origin', 'modeled_market_baseline',
           'source_url', baseline.source_url,
           'source_note', baseline.source_note
       )
from _modeled_baselines baseline
join public.reference_materials material on material.material_code = baseline.material_code
join public.reference_material_families family on family.family_code = baseline.family_code
join public.reference_material_models model on model.material_model_code = baseline.material_code
join public.reference_market_material_listings listing
  on listing.market_code = 'IL' and listing.material_model_id = model.material_model_id
on conflict (legacy_material_id) do update set
    family_id = excluded.family_id,
    material_model_id = excluded.material_model_id,
    market_material_listing_id = excluded.market_material_listing_id,
    classification_status = excluded.classification_status,
    classification_basis = excluded.classification_basis,
    classification_evidence = excluded.classification_evidence,
    updated_at = now();

insert into public.market_material_model_prices (
    material_id, market_code, catalog_version,
    price_low, price_typical, price_high, unit, currency, price_scope,
    pricing_method, confidence, anchor_count, formula_description,
    model_metadata, effective_from, status
)
select material.material_id,
       'IL',
       (
           select catalog_version
           from public.reference_catalog_versions
           where market_code = 'IL' and status = 'active'
           limit 1
       ),
       baseline.price_low, baseline.price_typical, baseline.price_high,
       baseline.base_unit, 'ILS', 'material_only',
       'modeled_fallback', 25, 1,
       baseline.source_note,
       jsonb_build_object(
           'catalog_origin', 'modeled_market_baseline',
           'source_url', baseline.source_url,
           'explicitly_not_supplier_evidence', true
       ),
       current_date, 'active'
from _modeled_baselines baseline
join public.reference_materials material on material.material_code = baseline.material_code
on conflict (material_id, market_code, catalog_version) do update set
    price_low = excluded.price_low,
    price_typical = excluded.price_typical,
    price_high = excluded.price_high,
    unit = excluded.unit,
    price_scope = excluded.price_scope,
    pricing_method = excluded.pricing_method,
    confidence = excluded.confidence,
    formula_description = excluded.formula_description,
    model_metadata = excluded.model_metadata,
    effective_from = excluded.effective_from,
    effective_to = null,
    status = 'active',
    updated_at = now();

do $$
begin
    if exists (
        select 1 from public.reference_material_families family
        left join public.reference_material_models model
          on model.family_id = family.family_id and model.active
        where family.family_code in (
            'decorative_film_foil', 'sheet_metal', 'metal_flat_bar',
            'metal_round_bar_rod_wire', 'aluminium_composite_panel',
            'terrazzo_engineered_agglomerate', 'vinyl_film'
        )
        group by family.family_code
        having count(model.material_model_id) = 0
    ) then
        raise exception 'A remaining Family has no canonical Israel position';
    end if;

    if exists (
        select 1
        from _remaining_source_targets target
        left join public.market_material_model_prices price
          on price.material_id = target.material_id
         and price.market_code = 'IL'
         and price.status = 'active'
        where price.model_price_id is null
    ) then
        raise exception 'An evidence-backed normalized position lost its active price';
    end if;
end $$;

commit;
