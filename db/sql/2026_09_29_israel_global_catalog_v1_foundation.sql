-- 3.15.4 Israel Global Catalog V1 foundation.
-- Separates the approved market price model from evidence-backed baselines.
-- This migration creates no catalog data and does not switch production reads.

begin;

create table if not exists public.reference_catalog_versions (
    catalog_version text primary key check (
        length(trim(catalog_version)) between 1 and 120
    ),
    market_code text not null references public.reference_markets(market_code),
    catalog_name text not null check (length(trim(catalog_name)) between 1 and 240),
    catalog_fingerprint text not null check (
        length(trim(catalog_fingerprint)) between 1 and 200
    ),
    status text not null check (status in ('candidate', 'active', 'retired')),
    activated_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint reference_catalog_versions_activation_check check (
        status <> 'active' or activated_at is not null
    )
);

create unique index if not exists reference_catalog_versions_one_active_market_idx
    on public.reference_catalog_versions(market_code)
    where status = 'active';

create table if not exists public.market_material_model_prices (
    model_price_id uuid primary key default gen_random_uuid(),
    material_id uuid not null references public.reference_materials(material_id),
    market_code text not null references public.reference_markets(market_code),
    catalog_version text not null references public.reference_catalog_versions(catalog_version),
    price_low numeric(18, 6) not null check (price_low >= 0),
    price_typical numeric(18, 6) not null check (price_typical >= 0),
    price_high numeric(18, 6) not null check (price_high >= 0),
    unit text not null check (length(trim(unit)) between 1 and 80),
    currency text not null check (currency ~ '^[A-Z]{3}$'),
    price_scope text not null check (price_scope in (
        'material_only', 'cut_to_size', 'fabricated_component', 'retail_package'
    )),
    pricing_method text not null check (pricing_method in (
        'derived_from_israel_curve', 'derived_from_israel_anchor',
        'modeled_from_israel_anchor', 'modeled_fallback'
    )),
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    anchor_count integer not null default 0 check (anchor_count >= 0),
    formula_description text not null check (length(trim(formula_description)) between 1 and 4000),
    model_metadata jsonb not null default '{}'::jsonb check (
        jsonb_typeof(model_metadata) = 'object'
    ),
    effective_from date not null,
    effective_to date,
    status text not null check (status in ('candidate', 'active', 'retired')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint market_material_model_prices_range_check check (
        price_low <= price_typical and price_typical <= price_high
    ),
    constraint market_material_model_prices_effective_check check (
        effective_to is null or effective_from <= effective_to
    ),
    unique (material_id, market_code, catalog_version)
);

create unique index if not exists market_material_model_prices_one_active_idx
    on public.market_material_model_prices(material_id, market_code)
    where status = 'active';

create index if not exists market_material_model_prices_lookup_idx
    on public.market_material_model_prices(
        market_code, material_id, status, effective_from desc
    );

alter table public.reference_catalog_versions enable row level security;
alter table public.market_material_model_prices enable row level security;

revoke all on public.reference_catalog_versions from public, anon, authenticated;
revoke all on public.market_material_model_prices from public, anon, authenticated;
grant all on public.reference_catalog_versions to service_role;
grant all on public.market_material_model_prices to service_role;

commit;
