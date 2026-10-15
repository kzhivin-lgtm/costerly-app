-- Consolidate raw MDF, HDF and faced MDF into one material Family.
--
-- Prerequisite: 2026_10_15_mdf_hdf_subfamily_pricing_key.sql.
-- Run this before 2026_10_15_apply_approved_default_positions_part_1.sql.
--
-- No source evidence, Israel listing, price or purchase format is deleted.

begin;

insert into public.reference_material_family_attributes (
    family_id, attribute_code, attribute_name, attribute_role, value_type, required, sort_order
)
select family.family_id, 'surface', 'Surface type', 'secondary', 'enum', true, 15
from public.reference_material_families family
where family.family_code = 'mdf_hdf'
on conflict (family_id, attribute_code) do update set
    attribute_name = excluded.attribute_name,
    attribute_role = excluded.attribute_role,
    value_type = excluded.value_type,
    required = excluded.required,
    sort_order = excluded.sort_order;

update public.reference_material_family_pricing_policies policy
set pricing_key_attribute_codes = array['board_type', 'surface', 'thickness']::text[],
    updated_at = now()
from public.reference_material_families family
where policy.family_id = family.family_id
  and family.family_code = 'mdf_hdf'
  and policy.active;

-- Child rows carry a composite FK that includes Family. Save and restore them
-- around the model move instead of losing their relation to source evidence.
create temporary table _faced_mdf_attributes on commit drop as
select value.material_model_id, value.attribute_code, value.attribute_value
from public.reference_material_model_attribute_values value
join public.reference_material_models model on model.material_model_id = value.material_model_id
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code = 'faced_mdf';

create temporary table _faced_mdf_mappings on commit drop as
select mapping.legacy_material_id, mapping.market_code, mapping.material_model_id,
       mapping.market_material_listing_id, mapping.classification_status,
       mapping.classification_basis, mapping.classification_evidence
from public.reference_market_material_legacy_mappings mapping
join public.reference_material_models model on model.material_model_id = mapping.material_model_id
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code = 'faced_mdf';

delete from public.reference_market_material_legacy_mappings mapping
using _faced_mdf_mappings saved
where mapping.legacy_material_id = saved.legacy_material_id;

delete from public.reference_material_model_attribute_values value
using _faced_mdf_attributes saved
where value.material_model_id = saved.material_model_id;

update public.reference_material_models model
set family_id = target.family_id,
    updated_at = now()
from public.reference_material_families source,
     public.reference_material_families target
where source.family_code = 'faced_mdf'
  and target.family_code = 'mdf_hdf'
  and model.family_id = source.family_id;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select saved.material_model_id, target.family_id, saved.attribute_code, saved.attribute_value
from _faced_mdf_attributes saved
join public.reference_material_families target on target.family_code = 'mdf_hdf';

insert into public.reference_market_material_legacy_mappings (
    legacy_material_id, market_code, family_id, material_model_id,
    market_material_listing_id, classification_status, classification_basis,
    classification_evidence
)
select saved.legacy_material_id, saved.market_code, target.family_id,
       saved.material_model_id, saved.market_material_listing_id,
       saved.classification_status, saved.classification_basis,
       saved.classification_evidence
from _faced_mdf_mappings saved
join public.reference_material_families target on target.family_code = 'mdf_hdf';

-- Existing faced defaults, if any, now belong to the unified Family too. Move
-- a colliding legacy priority aside; the approved defaults seed that follows
-- this migration owns priorities 10, 20, 30 and 40.
update public.reference_material_family_default_variants variant
set priority = variant.priority + 1000,
    updated_at = now()
from public.reference_material_families source,
     public.reference_material_families target,
     public.reference_material_family_default_variants target_variant
where source.family_code = 'faced_mdf'
  and target.family_code = 'mdf_hdf'
  and variant.family_id = source.family_id
  and target_variant.family_id = target.family_id
  and target_variant.priority = variant.priority;

update public.reference_material_family_default_variants variant
set family_id = target.family_id,
    updated_at = now()
from public.reference_material_families source,
     public.reference_material_families target
where source.family_code = 'faced_mdf'
  and target.family_code = 'mdf_hdf'
  and variant.family_id = source.family_id;

-- Move shared family aliases, retaining just one copy where the target already
-- owns exactly the same normalised alias.
delete from public.reference_material_family_aliases source_alias
using public.reference_material_families source,
      public.reference_material_families target,
      public.reference_material_family_aliases target_alias
where source.family_code = 'faced_mdf'
  and target.family_code = 'mdf_hdf'
  and source_alias.family_id = source.family_id
  and target_alias.family_id = target.family_id
  and target_alias.alias_key = source_alias.alias_key;

update public.reference_material_family_aliases alias
set family_id = target.family_id,
    updated_at = now()
from public.reference_material_families source,
     public.reference_material_families target
where source.family_code = 'faced_mdf'
  and target.family_code = 'mdf_hdf'
  and alias.family_id = source.family_id;

delete from public.reference_material_family_ambiguous_alias_candidates candidate
using public.reference_material_families source,
      public.reference_material_families target,
      public.reference_material_family_ambiguous_alias_candidates target_candidate
where source.family_code = 'faced_mdf'
  and target.family_code = 'mdf_hdf'
  and candidate.family_id = source.family_id
  and target_candidate.ambiguous_alias_id = candidate.ambiguous_alias_id
  and target_candidate.family_id = target.family_id;

update public.reference_material_family_ambiguous_alias_candidates candidate
set family_id = target.family_id
from public.reference_material_families source,
     public.reference_material_families target
where source.family_code = 'faced_mdf'
  and target.family_code = 'mdf_hdf'
  and candidate.family_id = source.family_id;

-- Fill the complete three-part key. Raw models get raw surface; moved faced
-- models retain their existing source-proved surface value.
insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id,
       model.family_id,
       'board_type',
       to_jsonb(case
           when model.canonical_name like 'HDF, %' then 'hdf'
           when model.canonical_name like 'MDF, %' then 'mdf'
       end)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code = 'mdf_hdf'
  and model.active
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id, model.family_id, 'surface', to_jsonb('raw'::text)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code = 'mdf_hdf'
  and model.active
  and (model.canonical_name ilike 'MDF, %, raw'
       or model.canonical_name ilike 'HDF, %, raw')
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

update public.reference_material_family_pricing_policies policy
set active = false,
    updated_at = now()
from public.reference_material_families family
where policy.family_id = family.family_id
  and family.family_code = 'faced_mdf';

update public.reference_material_families
set active = false,
    updated_at = now()
where family_code = 'faced_mdf';

do $$
declare
    active_count integer;
    complete_key_count integer;
begin
    select count(*) into active_count
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    where family.family_code = 'mdf_hdf' and model.active;

    select count(*) into complete_key_count
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    join public.reference_material_model_attribute_values board_type
      on board_type.material_model_id = model.material_model_id
     and board_type.attribute_code = 'board_type'
    join public.reference_material_model_attribute_values surface
      on surface.material_model_id = model.material_model_id
     and surface.attribute_code = 'surface'
    join public.reference_material_model_attribute_values thickness
      on thickness.material_model_id = model.material_model_id
     and thickness.attribute_code = 'thickness'
    where family.family_code = 'mdf_hdf'
      and model.active
      and board_type.attribute_value #>> '{}' in ('mdf', 'hdf')
      and surface.attribute_value #>> '{}' <> '';

    if complete_key_count <> active_count then
        raise exception 'Expected % MDF/HDF models with a complete three-part Pricing Key, found %', active_count, complete_key_count;
    end if;
    if exists (
        select 1 from public.reference_material_models model
        join public.reference_material_families family on family.family_id = model.family_id
        where family.family_code = 'faced_mdf' and model.active
    ) then
        raise exception 'Faced MDF still has active models after consolidation';
    end if;
end $$;

commit;
