-- Preserve source attributes, while adding the atomic Pricing-Key values used
-- by Resolver. Run WITHOUT RLS.
begin;

-- The original compound source attributes remain intact. Add the atomic,
-- secondary attributes that the approved Pricing Keys address directly.
insert into public.reference_material_family_attributes (
    family_id, attribute_code, attribute_name, attribute_role, value_type, required, sort_order
)
select family.family_id, seed.attribute_code, seed.attribute_name,
       'secondary', 'dimension', false, seed.sort_order
from (values
    ('edge_banding', 'width', 'Width', 81),
    ('edge_banding', 'thickness', 'Thickness', 82),
    ('metal_flat_bar', 'width', 'Width', 81),
    ('metal_flat_bar', 'thickness', 'Thickness', 82),
    ('hardware_drawer_slide', 'length', 'Length', 81)
) as seed(family_code, attribute_code, attribute_name, sort_order)
join public.reference_material_families family on family.family_code = seed.family_code
on conflict (family_id, attribute_code) do update
set attribute_name = excluded.attribute_name,
    attribute_role = excluded.attribute_role,
    value_type = excluded.value_type,
    required = excluded.required,
    sort_order = excluded.sort_order;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select attribute.material_model_id, attribute.family_id, 'width',
       attribute.attribute_value -> 'width_mm'
from public.reference_material_model_attribute_values attribute
join public.reference_material_families family on family.family_id = attribute.family_id
where family.family_code in ('edge_banding', 'metal_flat_bar')
  and attribute.attribute_code = 'width_thickness'
  and attribute.attribute_value ? 'width_mm'
on conflict (material_model_id, attribute_code) do update
set attribute_value = excluded.attribute_value, family_id = excluded.family_id;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select attribute.material_model_id, attribute.family_id, 'thickness',
       attribute.attribute_value -> 'thickness_mm'
from public.reference_material_model_attribute_values attribute
join public.reference_material_families family on family.family_id = attribute.family_id
where family.family_code in ('edge_banding', 'metal_flat_bar')
  and attribute.attribute_code = 'width_thickness'
  and attribute.attribute_value ? 'thickness_mm'
on conflict (material_model_id, attribute_code) do update
set attribute_value = excluded.attribute_value, family_id = excluded.family_id;

insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select attribute.material_model_id, attribute.family_id, 'length', attribute.attribute_value
from public.reference_material_model_attribute_values attribute
join public.reference_material_families family on family.family_id = attribute.family_id
where family.family_code = 'hardware_drawer_slide'
  and attribute.attribute_code = 'nominal_length'
on conflict (material_model_id, attribute_code) do update
set attribute_value = excluded.attribute_value, family_id = excluded.family_id;

commit;
