-- Israel Reference normalization, stage 1.
--
-- This migration changes only the canonical catalog chain:
-- Family -> model -> Israel listing -> existing Israel price row -> purchase format.
-- It preserves legacy source evidence and its price rows.  It does not invent
-- a source price, and it does not use the retired pricing-identity bridge.

begin;

-- Furniture profiles are priced by metal and section.  A missing wall is the
-- approved 1.5 mm manufacturing default, not a missing Pricing Key fact.
update public.reference_material_family_pricing_policies policy
set pricing_key_attribute_codes = array_remove(policy.pricing_key_attribute_codes, 'wall_thickness'),
    updated_at = now()
from public.reference_material_families family
where family.family_id = policy.family_id
  and family.family_code in ('metal_tube', 'metal_profile_angle_channel')
  and policy.active;

-- Three historical rows were placed under MDF solely by an earlier backfill.
-- Their own canonical text says Plywood, so correct the family in both the
-- model and its source-evidence mapping.
create temporary table _plywood_family_fix on commit drop as
select mapping.legacy_material_id, mapping.market_code, mapping.material_model_id,
       mapping.market_material_listing_id, mapping.classification_evidence
from public.reference_market_material_legacy_mappings mapping
join public.reference_material_models model on model.material_model_id = mapping.material_model_id
join public.reference_material_families family on family.family_id = model.family_id
where mapping.classification_status = 'mapped'
  and family.family_code = 'mdf_hdf'
  and model.canonical_name ilike 'Plywood%';

delete from public.reference_market_material_legacy_mappings mapping
using _plywood_family_fix fix
where mapping.legacy_material_id = fix.legacy_material_id;

delete from public.reference_material_model_attribute_values value
using _plywood_family_fix fix
where value.material_model_id = fix.material_model_id;

update public.reference_material_models model
set family_id = family.family_id,
    updated_at = now()
from public.reference_material_families family
where family.family_code = 'plywood'
  and model.material_model_id in (select material_model_id from _plywood_family_fix);

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id, model.family_id, 'thickness',
       to_jsonb((regexp_match(model.canonical_name, '([0-9]+(?:[.][0-9]+)?) mm'))[1]::numeric)
from public.reference_material_models model
where model.material_model_id in (select material_model_id from _plywood_family_fix)
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

insert into public.reference_market_material_legacy_mappings (
    legacy_material_id, market_code, family_id, material_model_id,
    market_material_listing_id, classification_status, classification_basis,
    classification_evidence
)
select fix.legacy_material_id, fix.market_code, family.family_id, fix.material_model_id,
       fix.market_material_listing_id, 'mapped', 'deterministic_rule',
       fix.classification_evidence || jsonb_build_object(
           'normalization_rule', 'canonical_name_prefix_plywood'
       )
from _plywood_family_fix fix
join public.reference_material_families family on family.family_code = 'plywood';

-- Existing generic furniture-system records carry enough explicit text to
-- split them into their real hardware family.  No price or source text changes.
create temporary table _hardware_family_fix on commit drop as
with hardware_family_rules(pattern, family_code) as (
    values
        ('%cabinet leg%', 'hardware_leg_caster'),
        ('%caster%', 'hardware_leg_caster'),
        ('%drawer box%', 'hardware_drawer_system'),
        ('%lift-up%', 'hardware_lift_system'),
        ('%lift mechanism%', 'hardware_lift_system'),
        ('%sliding door%', 'hardware_door_system'),
        ('%pocket door%', 'hardware_door_system'),
        ('%folding door%', 'hardware_door_system'),
        ('%handle%', 'hardware_handle'),
        ('%lock%', 'hardware_lock_latch'),
        ('%latch%', 'hardware_lock_latch'),
        ('%magnetic catch%', 'hardware_lock_latch'),
        ('%wardrobe rail%', 'hardware_storage_system'),
        ('%pull-out basket%', 'hardware_storage_system'),
        ('%corner carousel%', 'hardware_storage_system'),
        ('%shelf support%', 'hardware_mounting_part'),
        ('%plinth profile%', 'hardware_mounting_part')
), targets as (
    select model.material_model_id, target_family.family_id
    from public.reference_material_models model
    join public.reference_material_families current_family on current_family.family_id = model.family_id
    join hardware_family_rules rule on model.canonical_name ilike rule.pattern
    join public.reference_material_families target_family on target_family.family_code = rule.family_code
    where current_family.family_code = 'hardware_furniture_system'
)
select mapping.legacy_material_id, mapping.market_code, mapping.material_model_id,
       mapping.market_material_listing_id, mapping.classification_evidence,
       targets.family_id
from public.reference_market_material_legacy_mappings mapping
join targets on targets.material_model_id = mapping.material_model_id;

delete from public.reference_market_material_legacy_mappings mapping
using _hardware_family_fix fix
where mapping.legacy_material_id = fix.legacy_material_id;

delete from public.reference_material_model_attribute_values value
using _hardware_family_fix fix
where value.material_model_id = fix.material_model_id;

update public.reference_material_models model
set family_id = fix.family_id,
    updated_at = now()
from _hardware_family_fix fix
where model.material_model_id = fix.material_model_id;

-- Recreate the source mappings after the model family update.  The legacy row
-- remains the immutable price/evidence anchor for the listing.
insert into public.reference_market_material_legacy_mappings (
    legacy_material_id, market_code, family_id, material_model_id,
    market_material_listing_id, classification_status, classification_basis,
    classification_evidence
)
select fix.legacy_material_id, fix.market_code, fix.family_id,
       fix.material_model_id, fix.market_material_listing_id,
       'mapped', 'deterministic_rule',
       fix.classification_evidence || jsonb_build_object(
           'normalization_rule', 'explicit_hardware_name'
       )
from _hardware_family_fix fix;

do $$
begin
    if exists (
        select 1
        from public.reference_material_family_pricing_policies policy
        join public.reference_material_families family on family.family_id = policy.family_id
        where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
          and 'wall_thickness' = any(policy.pricing_key_attribute_codes)
    ) then
        raise exception 'Furniture profile Pricing Keys must not require wall thickness';
    end if;

    if exists (
        select 1
        from public.reference_material_models model
        join public.reference_material_families family on family.family_id = model.family_id
        where family.family_code = 'mdf_hdf'
          and model.canonical_name ilike 'Plywood%'
    ) then
        raise exception 'Plywood rows remain incorrectly assigned to MDF';
    end if;

    if exists (
        select 1
        from _hardware_family_fix fix
        left join public.market_material_model_prices price
          on price.material_id = fix.legacy_material_id
         and price.market_code = 'IL'
         and price.status = 'active'
        where price.model_price_id is null
    ) then
        raise exception 'A reclassified hardware listing lost its active Israel price row';
    end if;
end $$;

commit;
