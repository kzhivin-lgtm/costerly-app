-- 3.17.2.10, stage 2: a supplier offer owns its purchasable physical format.
-- A company material may have multiple supplier offers with distinct sheet
-- dimensions, package minima or prices. Never store these facts on the shared
-- company material identity.

alter table public.company_price_source_rows
    add column if not exists supply_format_code text,
    add column if not exists purchasable_dimensions jsonb not null default '{}'::jsonb,
    add column if not exists minimum_purchase_quantity numeric(16, 4) not null default 1,
    add column if not exists format_basis text not null default 'unknown';

alter table public.company_material_offers
    add column if not exists supply_format_code text,
    add column if not exists purchasable_dimensions jsonb not null default '{}'::jsonb,
    add column if not exists minimum_purchase_quantity numeric(16, 4) not null default 1,
    add column if not exists format_basis text not null default 'unknown';

do $$
begin
    if not exists (
        select 1 from pg_constraint where conname = 'company_price_source_rows_supply_format_code_check'
    ) then
        alter table public.company_price_source_rows
            add constraint company_price_source_rows_supply_format_code_check
            check (supply_format_code is null or supply_format_code in (
                'sheet', 'linear_stock', 'piece', 'set', 'roll', 'area', 'mass', 'unknown'
            ));
    end if;
    if not exists (
        select 1 from pg_constraint where conname = 'company_price_source_rows_format_basis_check'
    ) then
        alter table public.company_price_source_rows
            add constraint company_price_source_rows_format_basis_check
            check (format_basis in (
                'explicit', 'inferred_standard_width', 'standard_default',
                'not_applicable', 'incomplete', 'unknown'
            ));
    end if;
    if not exists (
        select 1 from pg_constraint where conname = 'company_material_offers_supply_format_code_check'
    ) then
        alter table public.company_material_offers
            add constraint company_material_offers_supply_format_code_check
            check (supply_format_code is null or supply_format_code in (
                'sheet', 'linear_stock', 'piece', 'set', 'roll', 'area', 'mass', 'unknown'
            ));
    end if;
    if not exists (
        select 1 from pg_constraint where conname = 'company_material_offers_format_basis_check'
    ) then
        alter table public.company_material_offers
            add constraint company_material_offers_format_basis_check
            check (format_basis in (
                'explicit', 'inferred_standard_width', 'standard_default',
                'not_applicable', 'incomplete', 'unknown'
            ));
    end if;
end $$;

alter table public.company_price_source_rows
    drop constraint if exists company_price_source_rows_minimum_purchase_quantity_check,
    add constraint company_price_source_rows_minimum_purchase_quantity_check
    check (minimum_purchase_quantity > 0);

alter table public.company_material_offers
    drop constraint if exists company_material_offers_minimum_purchase_quantity_check,
    add constraint company_material_offers_minimum_purchase_quantity_check
    check (minimum_purchase_quantity > 0);

create index if not exists company_material_offers_active_supply_format_idx
    on public.company_material_offers(company_id, status, supply_format_code, format_basis);

-- Both existing tables already have RLS enabled. This migration adds columns
-- only, and neither creates a new public relation nor changes any policy.
