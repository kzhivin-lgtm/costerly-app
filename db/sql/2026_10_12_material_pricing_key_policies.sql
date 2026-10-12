-- 3.17.2.10a Material Pricing Key registry.
--
-- A family attribute contract answers which facts are permitted to describe a
-- material. This registry separately states the minimum facts that make a
-- company offer estimable. It does not alter legacy rows, Israel listings or
-- Company Price Catalog offers.

begin;

create table if not exists public.reference_material_family_pricing_policies (
    family_id uuid primary key
        references public.reference_material_families(family_id) on delete cascade,
    pricing_key_attribute_codes text[] not null default '{}'::text[],
    purchase_format_policy text not null default 'not_required' check (
        purchase_format_policy in (
            'not_required',
            'required',
            'standard_sheet_2400x1220'
        )
    ),
    default_purchasable_dimensions jsonb not null default '{}'::jsonb check (
        jsonb_typeof(default_purchasable_dimensions) = 'object'
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (
        (purchase_format_policy <> 'standard_sheet_2400x1220'
            and default_purchasable_dimensions = '{}'::jsonb)
        or (
            purchase_format_policy = 'standard_sheet_2400x1220'
            and default_purchasable_dimensions ? 'length_mm'
            and default_purchasable_dimensions ? 'width_mm'
        )
    )
);

-- Wall thickness was accepted as price-bearing for tubes and formed profiles
-- but the original V2 generic-metal secondary template did not persist it.
with missing_contract_attributes (family_code, attribute_code, attribute_name, value_type) as (
    values
        ('metal_tube', 'wall_thickness', 'Wall thickness', 'dimension'),
        ('metal_profile_angle_channel', 'wall_thickness', 'Wall thickness', 'dimension')
)
insert into public.reference_material_family_attributes (
    family_id, attribute_code, attribute_name, attribute_role, value_type, required, sort_order
)
select family.family_id, seed.attribute_code, seed.attribute_name,
       'secondary', seed.value_type, false, 35
from missing_contract_attributes seed
join public.reference_material_families family using (family_code)
on conflict (family_id, attribute_code) do update set
    attribute_name = excluded.attribute_name,
    attribute_role = excluded.attribute_role,
    value_type = excluded.value_type,
    sort_order = excluded.sort_order;

with policy_seed (
    family_code,
    pricing_key_attribute_codes,
    purchase_format_policy,
    default_purchasable_dimensions
) as (
    values
        ('mdf_hdf', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('faced_mdf', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('particleboard', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('melamine_faced_particleboard', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('plywood', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('plywood_special', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('osb', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('fibreboard_hardboard', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('lightweight_sandwich_panel', array['thickness'], 'standard_sheet_2400x1220', '{"length_mm":2400,"width_mm":1220}'::jsonb),
        ('hpl_cpl', array['thickness'], 'required', '{}'::jsonb),
        ('compact_laminate', array['thickness'], 'required', '{}'::jsonb),
        ('wood_veneer', array['species'], 'required', '{}'::jsonb),
        ('edge_banding', array['width_thickness'], 'not_required', '{}'::jsonb),
        ('decorative_film_foil', array['width'], 'not_required', '{}'::jsonb),
        ('timber_solid_wood_panel', array['species', 'dimensions'], 'required', '{}'::jsonb),
        ('sheet_metal', array['thickness', 'metal_type'], 'required', '{}'::jsonb),
        ('metal_tube', array['section_profile', 'metal_type', 'wall_thickness'], 'required', '{}'::jsonb),
        ('metal_profile_angle_channel', array['section_profile', 'metal_type', 'wall_thickness'], 'required', '{}'::jsonb),
        ('metal_flat_bar', array['width_thickness', 'metal_type'], 'required', '{}'::jsonb),
        ('metal_round_bar_rod_wire', array['diameter', 'metal_type'], 'required', '{}'::jsonb),
        ('glass', array['thickness'], 'required', '{}'::jsonb),
        ('mirror', array['thickness'], 'required', '{}'::jsonb),
        ('acrylic_pmma', array['thickness'], 'required', '{}'::jsonb),
        ('polycarbonate_petg_pvc_abs', array['thickness'], 'required', '{}'::jsonb),
        ('sheet_plastic', array['thickness'], 'required', '{}'::jsonb),
        ('vinyl_film', array['width'], 'not_required', '{}'::jsonb),
        ('aluminium_composite_panel', array['thickness'], 'required', '{}'::jsonb),
        ('composite_sandwich_panel', array['thickness'], 'required', '{}'::jsonb),
        ('natural_stone_slab', array['thickness', 'stone_type'], 'required', '{}'::jsonb),
        ('engineered_quartz_mineral_hybrid', array['thickness'], 'required', '{}'::jsonb),
        ('sintered_ultra_compact_surface', array['thickness'], 'required', '{}'::jsonb),
        ('porcelain_ceramic_slab', array['thickness'], 'required', '{}'::jsonb),
        ('solid_surface', array['thickness'], 'required', '{}'::jsonb),
        ('terrazzo_engineered_agglomerate', array['thickness'], 'required', '{}'::jsonb),
        ('paint_lacquer_stain', array['coating_system'], 'not_required', '{}'::jsonb),
        ('primer', array['coating_system'], 'not_required', '{}'::jsonb),
        ('powder_coating', array['coating_system'], 'not_required', '{}'::jsonb),
        ('filler_hardener_thinner', array['chemistry_product_type'], 'not_required', '{}'::jsonb),
        ('hardware_hinge', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_drawer_slide', array['nominal_length'], 'not_required', '{}'::jsonb),
        ('hardware_connector', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_fastener', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_mounting_part', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_handle', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_leg_caster', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_lift_system', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_lock_latch', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_drawer_system', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_storage_system', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_door_system', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_furniture_system', array[]::text[], 'not_required', '{}'::jsonb),
        ('hardware_electrical_component', array[]::text[], 'not_required', '{}'::jsonb),
        ('purchased_fabricated_component', array['component_type'], 'not_required', '{}'::jsonb),
        ('packaging_material', array['packaging_type'], 'not_required', '{}'::jsonb)
)
insert into public.reference_material_family_pricing_policies (
    family_id,
    pricing_key_attribute_codes,
    purchase_format_policy,
    default_purchasable_dimensions,
    active
)
select
    family.family_id,
    seed.pricing_key_attribute_codes,
    seed.purchase_format_policy,
    seed.default_purchasable_dimensions,
    true
from policy_seed seed
join public.reference_material_families family using (family_code)
on conflict (family_id) do update set
    pricing_key_attribute_codes = excluded.pricing_key_attribute_codes,
    purchase_format_policy = excluded.purchase_format_policy,
    default_purchasable_dimensions = excluded.default_purchasable_dimensions,
    active = true,
    updated_at = now();

do $$
begin
    if exists (
        select 1
        from public.reference_material_family_pricing_policies policy
        join public.reference_material_families family on family.family_id = policy.family_id
        cross join lateral unnest(policy.pricing_key_attribute_codes) attribute(attribute_code)
        left join public.reference_material_family_attributes family_attribute
            on family_attribute.family_id = family.family_id
            and family_attribute.attribute_code = attribute.attribute_code
        where family_attribute.family_id is null
    ) then
        raise exception 'Pricing Key references an attribute outside its family contract';
    end if;

    if (select count(*) from public.reference_material_family_pricing_policies where active) <>
       (select count(*) from public.reference_material_families where active) then
        raise exception 'Every active material family must have one Pricing Key policy';
    end if;
end $$;

alter table public.reference_material_family_pricing_policies enable row level security;

revoke all on public.reference_material_family_pricing_policies
from public, anon, authenticated;

grant all on public.reference_material_family_pricing_policies to service_role;

commit;
