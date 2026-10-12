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

-- These are deliberately small, verified baseline variants, not a claim that
-- every market format is already covered. A one-sided source dimension may be
-- completed only when it matches exactly one active variant in this registry.
with seed(family_code, dimensions, is_default) as (
    values
        ('mdf_hdf', '{"length_mm": 2400, "width_mm": 1220}'::jsonb, true),
        ('plywood', '{"length_mm": 2400, "width_mm": 1220}'::jsonb, true),
        ('plywood', '{"length_mm": 3000, "width_mm": 1500}'::jsonb, false),
        ('plywood', '{"length_mm": 1520, "width_mm": 1520}'::jsonb, false),
        ('sheet_metal', '{"length_mm": 3000, "width_mm": 1500}'::jsonb, false),
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
