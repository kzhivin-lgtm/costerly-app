-- 3.17.1.4 follow-up coverage added after the initial shared-alias import.
-- Safe to run after the original four shared-alias scripts.

begin;

with family_alias_seed (family_code, language_code, alias_text) as ( values
    ('timber_solid_wood_panel', 'en', 'solid oak panel')
)
insert into public.reference_material_family_aliases (
    family_id, language_code, alias_text, alias_key, active
)
select family.family_id, seed.language_code, seed.alias_text,
       public.normalize_reference_material_alias(seed.alias_text), true
from family_alias_seed seed
join public.reference_material_families family using (family_code)
on conflict (family_id, alias_key) do update set
    language_code = excluded.language_code,
    alias_text = excluded.alias_text,
    active = true,
    updated_at = now();

with value_alias_seed (fact_field, canonical_value, language_code, alias_text) as ( values
    ('metal_type', 'stainless steel 304', 'en', 'stainless steel 304'),
    ('metal_type', 'stainless steel 304', 'en', 'aisi 304'),
    ('coating_system', 'powder coating', 'en', 'powder coating')
), field_policy_map (fact_field, pricing_key_attribute_code) as ( values
    ('metal_type', 'metal_type'),
    ('coating_system', 'coating_system')
)
insert into public.reference_material_pricing_key_value_aliases (
    family_id, fact_field, canonical_value, language_code, alias_text, alias_key, active
)
select family.family_id, seed.fact_field, seed.canonical_value, seed.language_code,
       seed.alias_text, public.normalize_reference_material_alias(seed.alias_text), true
from value_alias_seed seed
join field_policy_map map using (fact_field)
join public.reference_material_families family on family.active
join public.reference_material_family_pricing_policies policy
  on policy.family_id = family.family_id
 and policy.active
 and map.pricing_key_attribute_code = any(policy.pricing_key_attribute_codes)
on conflict (family_id, fact_field, canonical_value, alias_key) do update set
    language_code = excluded.language_code,
    alias_text = excluded.alias_text,
    active = true,
    updated_at = now();

with unit_alias_seed (unit_code, dimension_code, conversion_factor, language_code, alias_text) as ( values
    ('piece', 'count', 1, 'he', 'יח')
)
insert into public.reference_measurement_unit_aliases (
    unit_code, dimension_code, conversion_factor, language_code, alias_text, alias_key, active
)
select seed.unit_code, seed.dimension_code, seed.conversion_factor, seed.language_code,
       seed.alias_text, public.normalize_reference_material_alias(seed.alias_text), true
from unit_alias_seed seed
on conflict (unit_code, alias_key) do update set
    dimension_code = excluded.dimension_code,
    conversion_factor = excluded.conversion_factor,
    language_code = excluded.language_code,
    alias_text = excluded.alias_text,
    active = true,
    updated_at = now();

-- These spellings genuinely describe more than one Family. They may be kept
-- as catalog vocabulary, but direct Price Source matching must not select one
-- of their owners by order. The resolver gets a review case instead.
with ambiguous_seed (language_code, alias_text) as ( values
    ('en', 'bolt'), ('en', 'hdf'), ('en', 'honeycomb panel'),
    ('en', 'latch'), ('en', 'ldsp'), ('en', 'marine plywood'),
    ('en', 'melamine board'), ('en', 'sandwich panel'), ('en', 'stain'),
    ('ru', 'сотовая панель'), ('ru', 'сэндвич панель'), ('ru', 'хдф'),
    ('he', 'בייץ'), ('he', 'לביד ימי'), ('he', 'לוח מלמין'),
    ('he', 'לוח סנדוויץ')
)
insert into public.reference_material_family_ambiguous_aliases (
    language_code, alias_text, alias_key, active
)
select seed.language_code, seed.alias_text,
       public.normalize_reference_material_alias(seed.alias_text), true
from ambiguous_seed seed
on conflict (alias_key) do update set
    language_code = excluded.language_code,
    alias_text = excluded.alias_text,
    active = true,
    updated_at = now();

with candidate_seed (alias_text, family_code) as ( values
    ('bolt', 'hardware_connector'), ('bolt', 'hardware_fastener'),
    ('hdf', 'fibreboard_hardboard'), ('hdf', 'mdf_hdf'),
    ('honeycomb panel', 'composite_sandwich_panel'), ('honeycomb panel', 'lightweight_sandwich_panel'),
    ('latch', 'hardware_lock_latch'), ('latch', 'hardware_mounting_part'),
    ('ldsp', 'melamine_faced_particleboard'), ('ldsp', 'particleboard'),
    ('marine plywood', 'plywood'), ('marine plywood', 'plywood_special'),
    ('melamine board', 'melamine_faced_particleboard'), ('melamine board', 'particleboard'),
    ('sandwich panel', 'composite_sandwich_panel'), ('sandwich panel', 'lightweight_sandwich_panel'),
    ('stain', 'filler_hardener_thinner'), ('stain', 'paint_lacquer_stain'),
    ('сотовая панель', 'composite_sandwich_panel'), ('сотовая панель', 'lightweight_sandwich_panel'),
    ('сэндвич панель', 'composite_sandwich_panel'), ('сэндвич панель', 'lightweight_sandwich_panel'),
    ('хдф', 'fibreboard_hardboard'), ('хдф', 'mdf_hdf'),
    ('בייץ', 'filler_hardener_thinner'), ('בייץ', 'paint_lacquer_stain'),
    ('לביד ימי', 'plywood'), ('לביד ימי', 'plywood_special'),
    ('לוח מלמין', 'melamine_faced_particleboard'), ('לוח מלמין', 'particleboard'),
    ('לוח סנדוויץ', 'composite_sandwich_panel'), ('לוח סנדוויץ', 'lightweight_sandwich_panel')
)
insert into public.reference_material_family_ambiguous_alias_candidates (
    ambiguous_alias_id, family_id
)
select ambiguous.ambiguous_alias_id, family.family_id
from candidate_seed seed
join public.reference_material_family_ambiguous_aliases ambiguous
  on ambiguous.alias_key = public.normalize_reference_material_alias(seed.alias_text)
join public.reference_material_families family using (family_code)
on conflict do nothing;

commit;
