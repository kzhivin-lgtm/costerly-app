-- Correct the former automatic 2400 x 1220 fallback.
-- The approved purchase format for particleboard and standard hardboard is
-- 2440 x 1220.  Run WITHOUT RLS: this updates existing rows only.

begin;

update public.reference_material_family_pricing_policies policy
set default_purchasable_dimensions = '{"length_mm":2440,"width_mm":1220}'::jsonb,
    updated_at = now()
from public.reference_material_families family
where policy.family_id = family.family_id
  and family.family_code in ('particleboard', 'fibreboard_hardboard')
  and policy.purchase_format_policy = 'standard_sheet_2400x1220';

update public.reference_market_material_supply_formats format
set active = false,
    updated_at = now()
from public.reference_market_material_listings listing
join public.reference_material_models model on model.material_model_id = listing.material_model_id
join public.reference_material_families family on family.family_id = model.family_id
where format.market_material_listing_id = listing.market_material_listing_id
  and listing.market_code = 'IL'
  and family.family_code in ('particleboard', 'fibreboard_hardboard')
  and format.supply_format_code = 'standard_2400x1220'
  and format.purchasable_dimensions =
      '{"length_mm":2400,"width_mm":1220,"format_source":"approved_catalog_default"}'::jsonb
  and format.active;

do $$
declare
    unresolved_count integer;
begin
    select count(*) into unresolved_count
    from public.reference_material_family_default_variants variant
    join public.reference_material_families family on family.family_id = variant.family_id
    join public.reference_market_material_listings listing
      on listing.material_model_id = variant.reference_position_id
     and listing.market_code = 'IL' and listing.active
    left join public.reference_market_material_supply_formats approved
      on approved.market_material_listing_id = listing.market_material_listing_id
     and approved.supply_format_code = 'default_2440x1220'
     and approved.active
    left join public.reference_market_material_supply_formats obsolete
      on obsolete.market_material_listing_id = listing.market_material_listing_id
     and obsolete.supply_format_code = 'standard_2400x1220'
     and obsolete.active
    where family.family_code in ('particleboard', 'fibreboard_hardboard')
      and variant.priority = 10 and variant.active
      and (approved.supply_format_id is null or obsolete.supply_format_id is not null);
    if unresolved_count <> 0 then
        raise exception 'Particleboard/hardboard default format correction incomplete: %', unresolved_count;
    end if;
end $$;

commit;
