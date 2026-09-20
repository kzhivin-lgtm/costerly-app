-- Additive follow-up for databases that already ran
-- 2026_09_20_company_price_sources.sql before unit normalization was expanded.

alter table public.company_price_source_rows
    add column if not exists purchase_unit text,
    add column if not exists calculation_unit text,
    add column if not exists conversion_factor numeric(18, 8);

alter table public.company_material_offers
    add column if not exists purchase_unit text,
    add column if not exists calculation_unit text,
    add column if not exists conversion_factor numeric(18, 8);
