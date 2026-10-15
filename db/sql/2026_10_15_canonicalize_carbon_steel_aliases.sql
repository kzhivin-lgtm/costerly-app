-- Shared Pricing Key aliases for ordinary carbon steel.
-- Applies to every active Family whose Pricing Key includes metal_type.
-- No catalog price, position, offer or default is changed.

begin;

with value_alias_seed (language_code, alias_text) as (
    values
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
select family.family_id, 'metal_type', 'carbon steel', seed.language_code,
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

-- A supplied cross-section narrows the tube Family. If metal type is omitted,
-- use the approved carbon-steel baseline for that exact cross-section, rather
-- than trying to force the round-tube baseline onto a square tube.
create temporary table _metal_tube_square_20_default on commit drop as
with model_specifications as (
    select value.material_model_id,
           jsonb_object_agg(value.attribute_code, value.attribute_value) as specifications
    from public.reference_material_model_attribute_values value
    group by value.material_model_id
), ranked as (
    select model.material_model_id as reference_position_id,
           row_number() over (
               order by price.price_typical asc, model.material_model_code asc
           ) as candidate_rank
    from public.reference_material_families family
    join public.reference_material_models model
      on model.family_id = family.family_id and model.active
    join model_specifications specifications
      on specifications.material_model_id = model.material_model_id
     and specifications.specifications @> '{"section_profile":"square_tube_20x20","metal_type":"carbon steel"}'::jsonb
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    join public.reference_market_material_legacy_mappings mapping
      on mapping.material_model_id = model.material_model_id
     and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
    join public.market_material_model_prices price
      on price.material_id = mapping.legacy_material_id
     and price.market_code = 'IL' and price.status = 'active'
     and price.price_scope = 'material_only' and price.price_typical > 0
    where family.family_code = 'metal_tube' and family.active
)
select reference_position_id
from ranked
where candidate_rank = 1;

do $$
begin
    if (select count(*) from _metal_tube_square_20_default) <> 1 then
        raise exception 'Expected one active Israel Reference default for carbon-steel square tube 20x20';
    end if;
end $$;

insert into public.reference_material_family_default_variants (
    family_id, reference_position_id, default_specifications,
    applicability_specifications, priority, active
)
select family.family_id, chosen.reference_position_id,
       '{"metal_type":"carbon steel"}'::jsonb,
       '{"section_profile":"square_tube_20x20"}'::jsonb,
       11, true
from _metal_tube_square_20_default chosen
join public.reference_material_families family
  on family.family_code = 'metal_tube' and family.active
on conflict (family_id, priority) do update set
    reference_position_id = excluded.reference_position_id,
    default_specifications = excluded.default_specifications,
    applicability_specifications = excluded.applicability_specifications,
    active = true,
    updated_at = now();

commit;
