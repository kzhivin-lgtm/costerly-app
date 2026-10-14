-- Correct nine early experimental Global Models whose saved names prove that
-- their original MDF Family was wrong.  No price, Israel Listing, raw source
-- evidence or attribute value is discarded.  Attribute and legacy-mapping
-- rows are temporarily reconstructed only because their composite foreign
-- keys include Family.

begin;

create temporary table _experimental_family_fix (
    material_model_code text primary key,
    target_family_code text not null
) on commit drop;

insert into _experimental_family_fix (material_model_code, target_family_code) values
    ('gcm_v1_exp_hardboard_raw_3_2', 'fibreboard_hardboard'),
    ('gcm_v1_exp_laminated_solid_oak_20', 'timber_solid_wood_panel'),
    ('gcm_v1_exp_laminated_solid_oak_40', 'timber_solid_wood_panel'),
    ('gcm_v1_exp_laminated_solid_pine_18', 'timber_solid_wood_panel'),
    ('gcm_v1_exp_laminated_solid_pine_28', 'timber_solid_wood_panel'),
    ('gcm_v1_exp_mdf_laminate_17', 'faced_mdf'),
    ('gcm_v1_exp_melamine_17', 'melamine_faced_particleboard'),
    ('gcm_v1_exp_melamine_27', 'melamine_faced_particleboard');

create temporary table _experimental_model_snapshot on commit drop as
select model.material_model_id,
       model.material_model_code,
       family.family_id as target_family_id,
       fix.target_family_code
from _experimental_family_fix fix
join public.reference_material_models model
  on model.material_model_code = fix.material_model_code
 and model.active
join public.reference_material_families family
  on family.family_code = fix.target_family_code
 and family.active;

-- Thickness is a secondary fact for solid timber, not part of its species
-- Pricing Key.  The four source-backed records already carry it, so make the
-- Family schema able to retain that fact rather than dropping or inventing it.
insert into public.reference_material_family_attributes (
    family_id, attribute_code, attribute_name, attribute_role, value_type,
    required, sort_order
)
select family_id, 'thickness', 'Thickness', 'secondary', 'number', false, 20
from public.reference_material_families
where family_code = 'timber_solid_wood_panel'
on conflict (family_id, attribute_code) do nothing;

create temporary table _experimental_attribute_snapshot on commit drop as
select value.material_model_id,
       snapshot.target_family_id,
       value.attribute_code,
       value.attribute_value
from public.reference_material_model_attribute_values value
join _experimental_model_snapshot snapshot
  on snapshot.material_model_id = value.material_model_id;

create temporary table _experimental_mapping_snapshot on commit drop as
select mapping.legacy_material_id,
       mapping.market_code,
       snapshot.target_family_id,
       mapping.material_model_id,
       mapping.market_material_listing_id,
       mapping.classification_status,
       mapping.classification_basis,
       mapping.classification_evidence,
       mapping.created_at,
       mapping.updated_at
from public.reference_market_material_legacy_mappings mapping
join _experimental_model_snapshot snapshot
  on snapshot.material_model_id = mapping.material_model_id;

-- Composite foreign keys require the old Family-bearing children to be
-- temporarily removed.  Their full values are restored below, unchanged.
delete from public.reference_market_material_legacy_mappings mapping
using _experimental_model_snapshot snapshot
where mapping.material_model_id = snapshot.material_model_id;

delete from public.reference_material_model_attribute_values value
using _experimental_model_snapshot snapshot
where value.material_model_id = snapshot.material_model_id;

update public.reference_material_models model
set family_id = snapshot.target_family_id,
    updated_at = now()
from _experimental_model_snapshot snapshot
where model.material_model_id = snapshot.material_model_id;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select material_model_id, target_family_id, attribute_code, attribute_value
from _experimental_attribute_snapshot;

-- The source text proves the species for these four solid-timber panels.  It
-- becomes the Family Pricing Key; their existing thickness remains a proven
-- secondary attribute and is retained above.
insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select snapshot.material_model_id,
       snapshot.target_family_id,
       'species',
       to_jsonb(case
           when snapshot.material_model_code like '%_oak_%' then 'oak'
           else 'pine'
       end)
from _experimental_model_snapshot snapshot
where snapshot.target_family_code = 'timber_solid_wood_panel'
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

insert into public.reference_market_material_legacy_mappings (
    legacy_material_id, market_code, family_id, material_model_id,
    market_material_listing_id, classification_status, classification_basis,
    classification_evidence, created_at, updated_at
)
select legacy_material_id,
       market_code,
       target_family_id,
       material_model_id,
       market_material_listing_id,
       classification_status,
       classification_basis,
       classification_evidence || jsonb_build_object(
           'normalization_rule', 'experimental_family_corrected_from_saved_name'
       ),
       created_at,
       now()
from _experimental_mapping_snapshot;

do $$
declare
    expected_count integer := 9;
    corrected_count integer;
    mismatches integer;
    timber_missing_species integer;
begin
    select count(*) into corrected_count from _experimental_model_snapshot;
    if corrected_count <> expected_count then
        raise exception 'Expected % experimental models to correct, found %', expected_count, corrected_count;
    end if;

    select count(*) into mismatches
    from _experimental_model_snapshot snapshot
    join public.reference_material_models model
      on model.material_model_id = snapshot.material_model_id
    where model.family_id <> snapshot.target_family_id;
    if mismatches <> 0 then
        raise exception 'Experimental Family correction left % mismatched models', mismatches;
    end if;

    select count(*) into timber_missing_species
    from _experimental_model_snapshot snapshot
    left join public.reference_material_model_attribute_values value
      on value.material_model_id = snapshot.material_model_id
     and value.attribute_code = 'species'
    where snapshot.target_family_code = 'timber_solid_wood_panel'
      and value.material_model_id is null;
    if timber_missing_species <> 0 then
        raise exception 'Solid-timber correction left % models without species', timber_missing_species;
    end if;
end $$;

commit;
