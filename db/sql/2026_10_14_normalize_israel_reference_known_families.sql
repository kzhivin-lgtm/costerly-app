-- Israel Reference normalization, stage 3.
--
-- Moves only models whose own canonical text identifies a more precise Family.
-- Existing Israel price rows and immutable source evidence remain unchanged.

begin;

-- Solid timber is bought and priced by volume.  Dimensions describe the
-- purchased stock but do not split its material price class.
update public.reference_material_family_pricing_policies policy
set pricing_key_attribute_codes = array['species']::text[],
    updated_at = now()
from public.reference_material_families family
where family.family_id = policy.family_id
  and family.family_code = 'timber_solid_wood_panel'
  and policy.active;

-- These rows were created under broad source buckets despite their canonical
-- names already stating their exact Family.  Aluminium honeycomb is excluded:
-- it is not silently equated to aluminium composite panel.
create temporary table _known_family_reclass on commit drop as
select mapping.legacy_material_id,
       mapping.market_code,
       mapping.material_model_id,
       mapping.market_material_listing_id,
       mapping.classification_evidence,
       target_family.family_id as target_family_id,
       target_family.family_code as target_family_code
from public.reference_market_material_legacy_mappings mapping
join public.reference_material_models model on model.material_model_id = mapping.material_model_id
join public.reference_material_families current_family on current_family.family_id = model.family_id
join lateral (
    select case
        when current_family.family_code = 'sheet_plastic'
             and model.canonical_name ~* '^(Cast|Extruded) acrylic sheet,'
            then 'acrylic_pmma'
        when current_family.family_code = 'sheet_plastic'
             and model.canonical_name ~* '^(Polycarbonate|PETG|PVC rigid|PVC foam|ABS) (sheet|board),'
            then 'polycarbonate_petg_pvc_abs'
        when current_family.family_code = 'lightweight_sandwich_panel'
             and model.canonical_name ~* '^(Foam-core|Balsa-core) sandwich panel,'
            then 'composite_sandwich_panel'
    end as family_code
) rule on rule.family_code is not null
join public.reference_material_families target_family on target_family.family_code = rule.family_code
where mapping.market_code = 'IL'
  and mapping.classification_status = 'mapped';

delete from public.reference_market_material_legacy_mappings mapping
using _known_family_reclass fix
where mapping.legacy_material_id = fix.legacy_material_id;

delete from public.reference_material_model_attribute_values value
using _known_family_reclass fix
where value.material_model_id = fix.material_model_id;

update public.reference_material_models model
set family_id = fix.target_family_id,
    updated_at = now()
from _known_family_reclass fix
where model.material_model_id = fix.material_model_id;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id,
       fix.target_family_id,
       'thickness',
       to_jsonb((regexp_match(model.canonical_name, '([0-9]+(?:[.][0-9]+)?) mm'))[1]::numeric)
from _known_family_reclass fix
join public.reference_material_models model on model.material_model_id = fix.material_model_id
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

insert into public.reference_market_material_legacy_mappings (
    legacy_material_id, market_code, family_id, material_model_id,
    market_material_listing_id, classification_status, classification_basis,
    classification_evidence
)
select fix.legacy_material_id,
       fix.market_code,
       fix.target_family_id,
       fix.material_model_id,
       fix.market_material_listing_id,
       'mapped',
       'deterministic_rule',
       fix.classification_evidence || jsonb_build_object(
           'normalization_rule', 'explicit_canonical_family_name',
           'target_family', fix.target_family_code
       )
from _known_family_reclass fix;

do $$
begin
    if exists (
        select 1
        from public.reference_material_family_pricing_policies policy
        join public.reference_material_families family on family.family_id = policy.family_id
        where family.family_code = 'timber_solid_wood_panel'
          and policy.pricing_key_attribute_codes <> array['species']::text[]
    ) then
        raise exception 'Solid timber Pricing Key must be species only';
    end if;

    if exists (
        select 1
        from _known_family_reclass fix
        left join public.market_material_model_prices price
          on price.material_id = fix.legacy_material_id
         and price.market_code = 'IL'
         and price.status = 'active'
        where price.model_price_id is null
    ) then
        raise exception 'A reclassified Israel listing lost its active price';
    end if;
end $$;

commit;
