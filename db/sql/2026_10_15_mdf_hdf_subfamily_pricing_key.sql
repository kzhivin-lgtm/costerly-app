-- MDF and HDF remain one Family.  `board_type` distinguishes their two
-- price-bearing subfamilies before thickness, without moving or deleting
-- any existing Israel Reference position.
--
-- Run before 2026_10_15_apply_approved_default_positions_part_1.sql.

begin;

-- A Family may have exactly one schema-primary attribute.  Board type is now
-- that primary attribute, while thickness remains required and is the second
-- part of this Family's Pricing Key.
update public.reference_material_family_attributes attribute
set attribute_role = 'secondary',
    required = true,
    sort_order = 20
from public.reference_material_families family
where attribute.family_id = family.family_id
  and family.family_code = 'mdf_hdf'
  and attribute.attribute_code = 'thickness';

insert into public.reference_material_family_attributes (
    family_id, attribute_code, attribute_name, attribute_role, value_type, required, sort_order
)
select family.family_id, 'board_type', 'Board type', 'primary', 'enum', true, 10
from public.reference_material_families family
where family.family_code = 'mdf_hdf'
on conflict (family_id, attribute_code) do update set
    attribute_name = excluded.attribute_name,
    attribute_role = excluded.attribute_role,
    value_type = excluded.value_type,
    required = excluded.required,
    sort_order = excluded.sort_order;

update public.reference_material_family_pricing_policies policy
set pricing_key_attribute_codes = array['board_type', 'thickness']::text[],
    updated_at = now()
from public.reference_material_families family
where policy.family_id = family.family_id
  and family.family_code = 'mdf_hdf'
  and policy.active;

-- Every active position is already named either "MDF, ..." or "HDF, ...".
-- Do not guess from thickness: HDF and MDF can share the same thickness.
insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id,
       model.family_id,
       'board_type',
       to_jsonb(case
           when model.canonical_name like 'MDF, %' then 'mdf'
           when model.canonical_name like 'HDF, %' then 'hdf'
       end)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code = 'mdf_hdf'
  and model.active
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

do $$
declare
    active_count integer;
    classified_count integer;
    unexpected_count integer;
begin
    select count(*) into active_count
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    where family.family_code = 'mdf_hdf' and model.active;

    select count(*) into classified_count
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    join public.reference_material_model_attribute_values board_type
      on board_type.material_model_id = model.material_model_id
     and board_type.attribute_code = 'board_type'
    where family.family_code = 'mdf_hdf'
      and model.active
      and board_type.attribute_value #>> '{}' in ('mdf', 'hdf');

    select count(*) into unexpected_count
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    where family.family_code = 'mdf_hdf'
      and model.active
      and model.canonical_name not like 'MDF, %'
      and model.canonical_name not like 'HDF, %';

    if unexpected_count <> 0 then
        raise exception 'MDF/HDF has % active models without an MDF or HDF canonical prefix', unexpected_count;
    end if;
    if classified_count <> active_count then
        raise exception 'Expected % classified MDF/HDF models, found %', active_count, classified_count;
    end if;
end $$;

commit;
