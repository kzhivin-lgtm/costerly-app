-- 3.17.4.1 Furniture metal-profile Pricing Key correction.
--
-- Architectural evidence for furniture commonly gives the section, for
-- example 20 x 20 mm, but not wall thickness.  For tube and formed profile
-- families an absent wall is a manufacturing default of 1.5 mm.  It is
-- secondary provenance when supplied and must never block price resolution.
-- Flat bar is intentionally excluded: its physical thickness is part of the
-- cross section rather than a tube wall and remains price-bearing.

begin;

update public.reference_material_family_pricing_policies policy
set pricing_key_attribute_codes = array_remove(
        policy.pricing_key_attribute_codes,
        'wall_thickness'
    ),
    updated_at = now()
from public.reference_material_families family
where family.family_id = policy.family_id
  and family.family_code in ('metal_tube', 'metal_profile_angle_channel')
  and policy.active = true;

do $$
begin
    if exists (
        select 1
        from public.reference_material_family_pricing_policies policy
        join public.reference_material_families family on family.family_id = policy.family_id
        where family.family_code in ('metal_tube', 'metal_profile_angle_channel')
          and 'wall_thickness' = any(policy.pricing_key_attribute_codes)
    ) then
        raise exception 'Furniture tube/profile Pricing Keys must not require wall_thickness';
    end if;
end $$;

commit;
