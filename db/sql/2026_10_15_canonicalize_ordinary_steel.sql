-- Ordinary construction steel is canonically "steel".
-- Carbon, mild, regular and standard steel are intake aliases only.
-- Stainless steel and aluminium are intentionally not affected.

begin;

update public.reference_material_model_attribute_values
set attribute_value = '"steel"'::jsonb
where attribute_code = 'metal_type'
  and attribute_value #>> '{}' in ('carbon steel', 'mild steel', 'regular steel', 'standard steel');

update public.reference_material_models
set canonical_name = regexp_replace(canonical_name, '(?i)(carbon|mild|regular|standard)[[:space:]-]+steel', 'Steel', 'g'),
    updated_at = now()
where canonical_name ~* '(carbon|mild|regular|standard)[[:space:]-]+steel';

update public.company_material_items
set specifications = jsonb_set(specifications, '{metal_type}', '"steel"'::jsonb, true),
    canonical_name = regexp_replace(canonical_name, '(?i)(carbon|mild|regular|standard)[[:space:]-]+steel', 'Steel', 'g'),
    normalized_name = regexp_replace(normalized_name, '(?i)(carbon|mild|regular|standard)[[:space:]-]+steel', 'steel', 'g'),
    updated_at = now()
where specifications ->> 'metal_type' in ('carbon steel', 'mild steel', 'regular steel', 'standard steel')
   or canonical_name ~* '(carbon|mild|regular|standard)[[:space:]-]+steel'
   or normalized_name ~* '(carbon|mild|regular|standard)[[:space:]-]+steel';

-- Retire the old canonical value before recreating the same vocabulary under
-- "steel".  Aliases remain data, not a competing material catalog.
update public.reference_material_pricing_key_value_aliases
set active = false, updated_at = now()
where fact_field = 'metal_type'
  and canonical_value in ('carbon steel', 'mild steel', 'regular steel', 'standard steel');

with value_alias_seed (language_code, alias_text) as ( values
    ('en', 'steel'),
    ('en', 'regular steel'),
    ('en', 'standard steel'),
    ('en', 'carbon steel'),
    ('en', 'mild steel'),
    ('ru', 'сталь'),
    ('ru', 'обычная сталь'),
    ('ru', 'стандартная сталь'),
    ('ru', 'углеродистая сталь'),
    ('ru', 'конструкционная сталь'),
    ('he', 'פלדה'),
    ('he', 'פלדה רגילה'),
    ('he', 'פלדה סטנדרטית'),
    ('he', 'פלדת פחמן'),
    ('he', 'פלדה פחמנית')
)
insert into public.reference_material_pricing_key_value_aliases (
    family_id, fact_field, canonical_value, language_code, alias_text, alias_key, active
)
select family.family_id, 'metal_type', 'steel', seed.language_code,
       seed.alias_text, public.normalize_reference_material_alias(seed.alias_text), true
from value_alias_seed seed
join public.reference_material_families family on family.active
join public.reference_material_family_pricing_policies policy
  on policy.family_id = family.family_id
 and policy.active
 and 'metal_type' = any(policy.pricing_key_attribute_codes)
on conflict (family_id, fact_field, canonical_value, alias_key) do update set
    language_code = excluded.language_code,
    alias_text = excluded.alias_text,
    active = true,
    updated_at = now();

commit;
