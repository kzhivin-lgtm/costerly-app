-- 3.17.2.10, stage 2 correction.
-- Keep only the physical dimensions of a purchasable supplier offer. Unit,
-- quantity minimum and provenance remain respectively in the existing offer
-- unit fields and immutable source evidence; they do not need parallel fields.

begin;

drop index if exists public.company_material_offers_active_supply_format_idx;

alter table public.company_price_source_rows
    drop constraint if exists company_price_source_rows_supply_format_code_check,
    drop constraint if exists company_price_source_rows_format_basis_check,
    drop constraint if exists company_price_source_rows_minimum_purchase_quantity_check,
    drop column if exists supply_format_code,
    drop column if exists purchasable_dimensions,
    drop column if exists minimum_purchase_quantity,
    drop column if exists format_basis;

alter table public.company_material_offers
    drop constraint if exists company_material_offers_supply_format_code_check,
    drop constraint if exists company_material_offers_format_basis_check,
    drop constraint if exists company_material_offers_minimum_purchase_quantity_check,
    drop column if exists supply_format_code,
    drop column if exists minimum_purchase_quantity,
    drop column if exists format_basis;

create table if not exists public.reference_material_family_supply_formats (
    supply_format_id uuid primary key default gen_random_uuid(),
    family_id uuid not null references public.reference_material_families(family_id)
        on delete cascade,
    purchasable_dimensions jsonb not null,
    is_default boolean not null default false,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint reference_material_family_supply_formats_dimensions_object_check
        check (jsonb_typeof(purchasable_dimensions) = 'object')
);

create unique index if not exists reference_material_family_supply_formats_unique_idx
    on public.reference_material_family_supply_formats(family_id, purchasable_dimensions);

create unique index if not exists reference_material_family_supply_formats_one_default_idx
    on public.reference_material_family_supply_formats(family_id)
    where is_default and active;

-- The registry is intentionally open, not a closed claim about every supplier.
-- These are documented market candidate formats. A one-sided source dimension
-- may be completed only when it matches exactly one active variant; otherwise
-- it remains incomplete until source evidence or an admin addition resolves it.
with seed(family_code, dimensions, is_default) as (
    values
        ('mdf_hdf', '{"length_mm": 2400, "width_mm": 1220}'::jsonb, true),
        ('mdf_hdf', '{"length_mm": 2750, "width_mm": 1220}'::jsonb, false),
        ('mdf_hdf', '{"length_mm": 2150, "width_mm": 900}'::jsonb, false),
        ('mdf_hdf', '{"length_mm": 2800, "width_mm": 2070}'::jsonb, false),
        ('mdf_hdf', '{"length_mm": 3050, "width_mm": 1220}'::jsonb, false),
        ('mdf_hdf', '{"length_mm": 3050, "width_mm": 1300}'::jsonb, false),
        ('faced_mdf', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('faced_mdf', '{"length_mm": 2800, "width_mm": 1300}'::jsonb, false),
        ('faced_mdf', '{"length_mm": 2800, "width_mm": 2070}'::jsonb, false),
        ('faced_mdf', '{"length_mm": 3050, "width_mm": 1220}'::jsonb, false),
        ('particleboard', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('particleboard', '{"length_mm": 2500, "width_mm": 1250}'::jsonb, false),
        ('particleboard', '{"length_mm": 2800, "width_mm": 2070}'::jsonb, false),
        ('particleboard', '{"length_mm": 3050, "width_mm": 1250}'::jsonb, false),
        ('particleboard', '{"length_mm": 3050, "width_mm": 1310}'::jsonb, false),
        ('melamine_faced_particleboard', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('melamine_faced_particleboard', '{"length_mm": 2800, "width_mm": 2070}'::jsonb, false),
        ('plywood', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('plywood', '{"length_mm": 2500, "width_mm": 1220}'::jsonb, false),
        ('plywood', '{"length_mm": 2745, "width_mm": 1220}'::jsonb, false),
        ('plywood', '{"length_mm": 2750, "width_mm": 1220}'::jsonb, false),
        ('plywood', '{"length_mm": 3000, "width_mm": 1220}'::jsonb, false),
        ('plywood', '{"length_mm": 3050, "width_mm": 1220}'::jsonb, false),
        ('plywood', '{"length_mm": 3340, "width_mm": 1220}'::jsonb, false),
        ('plywood', '{"length_mm": 3660, "width_mm": 1220}'::jsonb, false),
        ('plywood', '{"length_mm": 2440, "width_mm": 1250}'::jsonb, false),
        ('plywood', '{"length_mm": 2500, "width_mm": 1250}'::jsonb, false),
        ('plywood', '{"length_mm": 2745, "width_mm": 1250}'::jsonb, false),
        ('plywood', '{"length_mm": 2750, "width_mm": 1250}'::jsonb, false),
        ('plywood', '{"length_mm": 3000, "width_mm": 1250}'::jsonb, false),
        ('plywood', '{"length_mm": 3050, "width_mm": 1250}'::jsonb, false),
        ('plywood', '{"length_mm": 3340, "width_mm": 1250}'::jsonb, false),
        ('plywood', '{"length_mm": 3660, "width_mm": 1250}'::jsonb, false),
        ('plywood', '{"length_mm": 1525, "width_mm": 1525}'::jsonb, false),
        ('plywood', '{"length_mm": 2440, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 2500, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 2745, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 2750, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 3000, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 3050, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 3340, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 3660, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 2440, "width_mm": 1525}'::jsonb, false),
        ('plywood', '{"length_mm": 2500, "width_mm": 1525}'::jsonb, false),
        ('plywood', '{"length_mm": 3000, "width_mm": 1525}'::jsonb, false),
        ('plywood', '{"length_mm": 3050, "width_mm": 1525}'::jsonb, false),
        ('plywood_special', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('plywood_special', '{"length_mm": 3050, "width_mm": 1525}'::jsonb, false),
        ('osb', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('osb', '{"length_mm": 2500, "width_mm": 1250}'::jsonb, false),
        ('fibreboard_hardboard', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('fibreboard_hardboard', '{"length_mm": 2800, "width_mm": 2070}'::jsonb, false),
        ('hpl_cpl', '{"length_mm": 3050, "width_mm": 1310}'::jsonb, true),
        ('hpl_cpl', '{"length_mm": 2800, "width_mm": 2070}'::jsonb, false),
        ('hpl_cpl', '{"length_mm": 2790, "width_mm": 2060}'::jsonb, false),
        ('hpl_cpl', '{"length_mm": 2150, "width_mm": 950}'::jsonb, false),
        ('hpl_cpl', '{"length_mm": 2150, "width_mm": 1020}'::jsonb, false),
        ('compact_laminate', '{"length_mm": 2790, "width_mm": 2060}'::jsonb, true),
        ('lightweight_sandwich_panel', '{"length_mm": 2800, "width_mm": 2070}'::jsonb, true),
        ('acrylic_pmma', '{"length_mm": 2000, "width_mm": 1000}'::jsonb, false),
        ('acrylic_pmma', '{"length_mm": 1830, "width_mm": 1220}'::jsonb, false),
        ('acrylic_pmma', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('acrylic_pmma', '{"length_mm": 2440, "width_mm": 1830}'::jsonb, false),
        ('acrylic_pmma', '{"length_mm": 2450, "width_mm": 1250}'::jsonb, false),
        ('acrylic_pmma', '{"length_mm": 3050, "width_mm": 2030}'::jsonb, false),
        ('acrylic_pmma', '{"length_mm": 3050, "width_mm": 2050}'::jsonb, false),
        ('polycarbonate_petg_pvc_abs', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('polycarbonate_petg_pvc_abs', '{"length_mm": 3050, "width_mm": 2050}'::jsonb, false),
        ('sheet_plastic', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('sheet_plastic', '{"length_mm": 3050, "width_mm": 2050}'::jsonb, false),
        ('aluminium_composite_panel', '{"length_mm": 2440, "width_mm": 1220}'::jsonb, true),
        ('aluminium_composite_panel', '{"length_mm": 3050, "width_mm": 1500}'::jsonb, false),
        ('composite_sandwich_panel', '{"length_mm": 3000, "width_mm": 1250}'::jsonb, false),
        ('composite_sandwich_panel', '{"length_mm": 3000, "width_mm": 1500}'::jsonb, false),
        ('glass', '{"length_mm": 3210, "width_mm": 2250}'::jsonb, false),
        ('glass', '{"length_mm": 3210, "width_mm": 2550}'::jsonb, false),
        ('glass', '{"length_mm": 6000, "width_mm": 3210}'::jsonb, false),
        ('solid_surface', '{"length_mm": 2490, "width_mm": 760}'::jsonb, false),
        ('solid_surface', '{"length_mm": 2490, "width_mm": 930}'::jsonb, false),
        ('solid_surface', '{"length_mm": 3660, "width_mm": 930}'::jsonb, false),
        ('solid_surface', '{"length_mm": 3660, "width_mm": 1220}'::jsonb, false),
        ('solid_surface', '{"length_mm": 3660, "width_mm": 1370}'::jsonb, false),
        ('solid_surface', '{"length_mm": 3660, "width_mm": 1525}'::jsonb, false),
        ('engineered_quartz_mineral_hybrid', '{"length_mm": 3050, "width_mm": 1440}'::jsonb, false),
        ('engineered_quartz_mineral_hybrid', '{"length_mm": 3340, "width_mm": 1640}'::jsonb, false),
        ('sintered_ultra_compact_surface', '{"length_mm": 2600, "width_mm": 1000}'::jsonb, false),
        ('sintered_ultra_compact_surface', '{"length_mm": 3200, "width_mm": 1440}'::jsonb, false),
        ('sintered_ultra_compact_surface', '{"length_mm": 3200, "width_mm": 1500}'::jsonb, false),
        ('sintered_ultra_compact_surface', '{"length_mm": 3200, "width_mm": 1600}'::jsonb, false),
        ('sintered_ultra_compact_surface', '{"length_mm": 3300, "width_mm": 1630}'::jsonb, false),
        ('sintered_ultra_compact_surface', '{"length_mm": 3600, "width_mm": 1200}'::jsonb, false),
        ('porcelain_ceramic_slab', '{"length_mm": 3200, "width_mm": 1600}'::jsonb, false),
        ('sheet_metal', '{"length_mm": 2000, "width_mm": 1000}'::jsonb, false),
        ('sheet_metal', '{"length_mm": 2500, "width_mm": 1250}'::jsonb, false),
        ('sheet_metal', '{"length_mm": 3000, "width_mm": 1250}'::jsonb, false),
        ('sheet_metal', '{"length_mm": 3000, "width_mm": 1500}'::jsonb, false),
        ('sheet_metal', '{"length_mm": 4000, "width_mm": 2000}'::jsonb, false),
        ('sheet_metal', '{"length_mm": 6000, "width_mm": 2000}'::jsonb, false),
        ('metal_tube', '{"length_mm": 6000}'::jsonb, true),
        ('metal_profile_angle_channel', '{"length_mm": 6000}'::jsonb, true),
        ('metal_round_bar_rod_wire', '{"length_mm": 6000}'::jsonb, true)
)
insert into public.reference_material_family_supply_formats (
    family_id, purchasable_dimensions, is_default
)
select family.family_id, seed.dimensions, seed.is_default
from seed
join public.reference_material_families family on family.code = seed.family_code
on conflict (family_id, purchasable_dimensions) do update
set is_default = excluded.is_default,
    active = true,
    updated_at = now();

alter table public.reference_material_family_supply_formats enable row level security;
revoke all on public.reference_material_family_supply_formats from public, anon, authenticated;
grant all on public.reference_material_family_supply_formats to service_role;

commit;
