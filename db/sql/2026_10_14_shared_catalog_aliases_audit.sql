-- 3.17.1.4 Read-only acceptance audit for the shared alias catalog.
-- Run only after the schema and all four seeds have completed successfully.

-- Inventory used for the release checkpoint.
select 'family_aliases' as scope, count(*) as active_rows
from public.reference_material_family_aliases where active
union all
select 'ambiguous_family_aliases', count(*)
from public.reference_material_family_ambiguous_aliases where active
union all
select 'ambiguous_family_candidates', count(*)
from public.reference_material_family_ambiguous_alias_candidates
union all
select 'pricing_key_labels', count(*)
from public.reference_material_pricing_key_aliases where active
union all
select 'pricing_key_values', count(*)
from public.reference_material_pricing_key_value_aliases where active
union all
select 'measurement_units', count(*)
from public.reference_measurement_unit_aliases where active
union all
select 'operation_aliases', count(*)
from public.reference_operation_aliases where active
union all
select 'brand_aliases', count(*)
from public.reference_brand_aliases where active
union all
select 'product_system_aliases', count(*)
from public.reference_brand_product_system_aliases where active
order by scope;

-- Every active Family must be understandable in each supported input language.
select family.family_code,
       array_agg(distinct alias.language_code order by alias.language_code) as languages
from public.reference_material_families family
left join public.reference_material_family_aliases alias
  on alias.family_id = family.family_id and alias.active
where family.active
group by family.family_id, family.family_code
having not array['en', 'he', 'ru'] <@ coalesce(array_agg(distinct alias.language_code), array[]::text[])
order by family.family_code;

-- A non-ambiguous source spelling may never select more than one Family.
select alias.alias_key, count(distinct alias.family_id) as family_count
from public.reference_material_family_aliases alias
left join public.reference_material_family_ambiguous_aliases ambiguous
  on ambiguous.alias_key = alias.alias_key and ambiguous.active
where alias.active and ambiguous.ambiguous_alias_id is null
group by alias.alias_key
having count(distinct alias.family_id) > 1
order by alias.alias_key;

-- Pricing Key aliases must be permitted by the Family policy.
select alias.pricing_key_alias_id, family.family_code, alias.fact_field
from public.reference_material_pricing_key_aliases alias
join public.reference_material_families family on family.family_id = alias.family_id
left join public.reference_material_family_pricing_policies policy
  on policy.family_id = alias.family_id and policy.active
where alias.active
  and not exists (
      select 1
      from unnest(coalesce(policy.pricing_key_attribute_codes, array[]::text[])) code
      where (alias.fact_field = 'thickness_mm' and code = 'thickness')
         or (alias.fact_field = 'profile_section' and code = 'section_profile')
         or (alias.fact_field = 'metal_type' and code = 'metal_type')
         or (alias.fact_field = 'coating_system' and code = 'coating_system')
         or (alias.fact_field = 'stone_type' and code = 'stone_type')
         or (alias.fact_field in ('width_mm', 'length_mm', 'depth_mm', 'diameter_mm')
             and code in ('dimensions', 'width', 'width_thickness', 'nominal_length', 'diameter'))
         or (alias.fact_field = 'species' and code = 'species')
         or (alias.fact_field = 'chemistry_product_type' and code = 'chemistry_product_type')
         or (alias.fact_field = 'component_type' and code = 'component_type')
         or (alias.fact_field = 'packaging_type' and code = 'packaging_type')
  )
order by family.family_code, alias.fact_field;
