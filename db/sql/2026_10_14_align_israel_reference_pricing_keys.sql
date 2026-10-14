-- Israel Reference: apply approved Pricing Key rules.
-- Prerequisite: 2026_10_14_correct_israel_reference_experimental_families.sql.
-- This migration changes neither source evidence, price nor purchase format.

begin;

-- Faced MDF is priced by thickness and type of facing.  `primary` is a
-- one-per-Family schema field, not the Pricing Key itself, so thickness keeps
-- that role.  Surface is required, remains secondary, and is the second
-- Pricing Key attribute.
update public.reference_material_family_attributes attribute
set required = true,
    attribute_role = 'secondary',
    value_type = 'enum',
    sort_order = 20
from public.reference_material_families family
where attribute.family_id = family.family_id
  and family.family_code = 'faced_mdf'
  and attribute.attribute_code = 'surface';

update public.reference_material_family_pricing_policies policy
set pricing_key_attribute_codes = array['thickness', 'surface']::text[],
    updated_at = now()
from public.reference_material_families family
where policy.family_id = family.family_id
  and family.family_code = 'faced_mdf'
  and policy.active;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id,
       model.family_id,
       'surface',
       to_jsonb((case
           when model.material_model_code like 'gcm_v1_mdf_faced_acrylic%' then 'acrylic'
           when model.material_model_code like 'gcm_v1_mdf_faced_hpl_one_side%' then 'hpl_one_sided'
           when model.material_model_code like 'gcm_v1_mdf_faced_hpl_two_sides%' then 'hpl_two_sided'
           when model.material_model_code like 'gcm_v1_mdf_faced_lacquered_one_side%' then 'lacquered_one_sided'
           when model.material_model_code like 'gcm_v1_mdf_faced_lacquered_two_sides%' then 'lacquered_two_sided'
           when model.material_model_code like 'gcm_v1_mdf_faced_melamine_one_side%' then 'melamine_one_sided'
           when model.material_model_code like 'gcm_v1_mdf_faced_melamine_two_sides%' then 'melamine_two_sided'
           when model.material_model_code like 'gcm_v1_mdf_faced_pet%' then 'pet'
           when model.material_model_code like 'gcm_v1_mdf_faced_veneer_one_side%' then 'veneer_one_sided'
           when model.material_model_code like 'gcm_v1_mdf_faced_veneer_two_sides%' then 'veneer_two_sided'
           when model.material_model_code = 'gcm_v1_exp_mdf_laminate_17' then 'laminated'
       end)::text)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code = 'faced_mdf'
  and model.active
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

-- Two Pricing Keys for tubes and formed profiles remain exactly as agreed:
-- section_profile (shape plus size) + metal_type.  Do not introduce a third
-- cross-section field.  Existing channel and beam rows have no proved size,
-- so their existing section_profile is retained unchanged.
update public.reference_material_model_attribute_values attribute
set attribute_value = to_jsonb((case attribute.attribute_value #>> '{}'
    when 'square_tube' then 'square_tube_20x20'
    when 'rectangular_tube' then 'rectangular_tube_40x20'
    when 'round_tube' then 'round_tube_d20'
    when 'angle' then 'angle_30x30'
    else attribute.attribute_value #>> '{}'
end)::text)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where attribute.material_model_id = model.material_model_id
  and attribute.family_id = model.family_id
  and family.family_code in ('metal_tube', 'metal_profile_angle_channel')
  and attribute.attribute_code = 'section_profile';

-- Brass was explicit in the saved source name but missing from the normalized
-- key.  Backfill only those missing material-type values.
insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id,
       model.family_id,
       'metal_type',
       to_jsonb('brass'::text)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
left join public.reference_material_model_attribute_values attribute
  on attribute.material_model_id = model.material_model_id
 and attribute.attribute_code = 'metal_type'
where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
  and model.canonical_name ilike 'Brass CuZn37%'
  and attribute.material_model_id is null
on conflict (material_model_id, attribute_code) do nothing;

-- Alloy and finish are proven secondary attributes, not Pricing Keys.  They
-- keep individually catalogued rows explainable and prevent different grades
-- or surface finishes from being silently collapsed into one display name.
insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id,
       model.family_id,
       'alloy',
       to_jsonb((substring(
           model.canonical_name from
           '^(?:Aluminium|Brass|Carbon steel|Copper|Galvanized steel|Stainless steel)[[:space:]]+([^,]+),'
       ))::text)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
  and model.canonical_name ~* '^(Aluminium|Brass|Carbon steel|Copper|Galvanized steel|Stainless steel)[[:space:]]+[^,]+,'
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id,
       model.family_id,
       'finish',
       to_jsonb((case
           when model.canonical_name ilike '%anodized' then 'anodized'
           when model.canonical_name ilike '%mill finish' then 'mill_finish'
           when model.canonical_name ilike '%powder-coat ready' then 'powder_coat_ready'
           when model.canonical_name ilike '%brushed' then 'brushed'
           when model.canonical_name ilike '%mirror polished' then 'mirror_polished'
       end)::text)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
  and model.canonical_name ~* '(anodized|mill finish|powder-coat ready|brushed|mirror polished)$'
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

do $$
declare
    missing_faced_mdf_surface integer;
    missing_metal_key integer;
    brass_missing integer;
    metal_secondary_missing integer;
begin
    select count(*) into missing_faced_mdf_surface
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    left join public.reference_material_model_attribute_values surface
      on surface.material_model_id = model.material_model_id
     and surface.attribute_code = 'surface'
    where family.family_code = 'faced_mdf'
      and model.active
      and surface.material_model_id is null;
    if missing_faced_mdf_surface <> 0 then
        raise exception 'Faced MDF has % models without its source-proved surface attribute', missing_faced_mdf_surface;
    end if;

    select count(*) into missing_metal_key
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    left join public.reference_material_model_attribute_values profile
      on profile.material_model_id = model.material_model_id
     and profile.attribute_code = 'section_profile'
    left join public.reference_material_model_attribute_values metal
      on metal.material_model_id = model.material_model_id
     and metal.attribute_code = 'metal_type'
    where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
      and model.active
      and (profile.material_model_id is null or metal.material_model_id is null);
    if missing_metal_key <> 0 then
        raise exception 'Metal profile/tube has % models without a Pricing Key', missing_metal_key;
    end if;

    select count(*) into brass_missing
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    left join public.reference_material_model_attribute_values metal
      on metal.material_model_id = model.material_model_id
     and metal.attribute_code = 'metal_type'
    where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
      and model.canonical_name ilike 'Brass CuZn37%'
      and metal.attribute_value <> to_jsonb('brass'::text);
    if brass_missing <> 0 then
        raise exception 'Brass backfill failed for % metal models', brass_missing;
    end if;

    select count(*) into metal_secondary_missing
    from public.reference_material_models model
    join public.reference_material_families family on family.family_id = model.family_id
    left join public.reference_material_model_attribute_values alloy
      on alloy.material_model_id = model.material_model_id
     and alloy.attribute_code = 'alloy'
    left join public.reference_material_model_attribute_values finish
      on finish.material_model_id = model.material_model_id
     and finish.attribute_code = 'finish'
    where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
      and model.active
      and (alloy.material_model_id is null or finish.material_model_id is null);
    if metal_secondary_missing <> 0 then
        raise exception 'Metal profile/tube has % models without alloy or finish', metal_secondary_missing;
    end if;
end $$;

commit;
