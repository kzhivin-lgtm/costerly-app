-- Israel Reference normalization, stage 2.
--
-- Completes facts which are already explicit in the canonical position text,
-- corrects price scope for purchasable hardware, and adds the owner-approved
-- 2400 x 1220 mm default format only to families whose policy states exactly
-- that standard.  It changes neither numeric prices nor source evidence.

begin;

-- Hardware is bought as a discrete product or package.  The existing numeric
-- Israel prices stay untouched.  Only their operational scope is corrected.
update public.market_material_model_prices price
set price_scope = 'retail_package',
    updated_at = now()
from public.reference_market_material_legacy_mappings mapping
join public.reference_material_families family on family.family_id = mapping.family_id
where price.material_id = mapping.legacy_material_id
  and price.market_code = 'IL'
  and price.status = 'active'
  and family.family_code like 'hardware_%'
  and price.price_scope <> 'retail_package';

-- The names explicitly state the metal.  Wall thickness is deliberately not
-- inserted because it is secondary and defaults to 1.5 mm when omitted.
insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id, model.family_id, 'metal_type',
       to_jsonb(case
           when model.canonical_name ilike '%stainless%' then 'stainless steel'
           when model.canonical_name ilike '%galvanized%' then 'carbon steel'
           when model.canonical_name ilike '%aluminium%' then 'aluminium'
           when model.canonical_name ilike '%carbon steel%' then 'carbon steel'
       end)
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
  and model.active
  and (
      model.canonical_name ilike '%stainless%'
      or model.canonical_name ilike '%galvanized%'
      or model.canonical_name ilike '%aluminium%'
      or model.canonical_name ilike '%carbon steel%'
  )
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

-- Natural stone type is also explicit in the canonical position name.
insert into public.reference_material_model_attribute_values (
    material_model_id, family_id, attribute_code, attribute_value
)
select model.material_model_id, model.family_id, 'stone_type',
       to_jsonb(lower((regexp_match(
           model.canonical_name,
           '^(Granite|Marble|Quartzite|Limestone|Travertine)'
       ))[1]))
from public.reference_material_models model
join public.reference_material_families family on family.family_id = model.family_id
where family.family_code = 'natural_stone_slab'
  and model.active
  and model.canonical_name ~ '^(Granite|Marble|Quartzite|Limestone|Travertine)'
on conflict (material_model_id, attribute_code) do update set
    family_id = excluded.family_id,
    attribute_value = excluded.attribute_value;

-- The only automatic sheet format approved by policy is 2400 x 1220 mm.
-- It is stored as a selectable catalog default, not as a claim about supplier
-- source text.  Families with a different or "required" format remain open.
insert into public.reference_market_material_supply_formats (
    market_material_listing_id, supply_format_code, purchase_unit,
    purchasable_dimensions, minimum_purchase_quantity, active
)
select listing.market_material_listing_id,
       'standard_2400x1220',
       'sheet',
       jsonb_build_object(
           'length_mm', 2400,
           'width_mm', 1220,
           'format_source', 'approved_catalog_default'
       ),
       1,
       true
from public.reference_market_material_listings listing
join public.reference_material_models model on model.material_model_id = listing.material_model_id
join public.reference_material_families family on family.family_id = model.family_id
join public.reference_material_family_pricing_policies policy
  on policy.family_id = family.family_id and policy.active
where listing.market_code = 'IL'
  and listing.active
  and policy.purchase_format_policy = 'standard_sheet_2400x1220'
on conflict (market_material_listing_id, supply_format_code) do update set
    purchase_unit = excluded.purchase_unit,
    purchasable_dimensions = excluded.purchasable_dimensions,
    minimum_purchase_quantity = excluded.minimum_purchase_quantity,
    active = true,
    updated_at = now();

-- Reject a partial migration before commit.
do $$
begin
    if exists (
        select 1
        from public.market_material_model_prices price
        join public.reference_market_material_legacy_mappings mapping
          on mapping.legacy_material_id = price.material_id
        join public.reference_material_families family on family.family_id = mapping.family_id
        where price.market_code = 'IL'
          and price.status = 'active'
          and family.family_code like 'hardware_%'
          and price.price_scope <> 'retail_package'
    ) then
        raise exception 'Active hardware price remains outside retail package scope';
    end if;

    if exists (
        select 1
        from public.reference_market_material_listings listing
        join public.reference_material_models model on model.material_model_id = listing.material_model_id
        join public.reference_material_families family on family.family_id = model.family_id
        join public.reference_material_family_pricing_policies policy
          on policy.family_id = family.family_id and policy.active
        left join public.reference_market_material_supply_formats supply
          on supply.market_material_listing_id = listing.market_material_listing_id
         and supply.active
        where listing.market_code = 'IL'
          and listing.active
          and policy.purchase_format_policy = 'standard_sheet_2400x1220'
          and supply.supply_format_id is null
    ) then
        raise exception 'An approved standard-sheet listing has no purchase format';
    end if;
end $$;

commit;
