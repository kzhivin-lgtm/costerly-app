-- 3.15.5 Material pricing identities.
--
-- A detailed reference material records what the physical item is. A pricing
-- identity records the deliberately broader class used by estimation. It
-- ignores decorative wording such as colour, decor, supplier naming, and SKU,
-- but retains every attribute that changes the price class.
--
-- This migration is additive. It creates no identities, moves no existing
-- prices, and does not activate a new resolver. The seed must be reviewed and
-- loaded before production reads are switched.

begin;

create table if not exists public.reference_material_pricing_identities (
    pricing_identity_id uuid primary key default gen_random_uuid(),
    market_code text not null references public.reference_markets(market_code),
    pricing_identity_code text not null check (
        length(trim(pricing_identity_code)) between 1 and 180
        and pricing_identity_code = lower(pricing_identity_code)
        and pricing_identity_code !~ '[^a-z0-9_]'
    ),
    department text not null check (department in (
        'wood', 'metal', 'glass_stone_plastic', 'coating', 'hardware',
        'consumable', 'packaging'
    )),
    canonical_name text not null check (length(trim(canonical_name)) between 1 and 500),
    canonical_name_he text,
    base_unit text not null check (length(trim(base_unit)) between 1 and 80),
    price_attributes jsonb not null default '{}'::jsonb check (
        jsonb_typeof(price_attributes) = 'object'
    ),
    ignored_variation_fields text[] not null default array[
        'colour', 'color', 'decor', 'pattern', 'supplier_sku',
        'supplier_name', 'marketing_name'
    ]::text[],
    status text not null default 'candidate' check (
        status in ('candidate', 'active', 'retired')
    ),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (market_code, pricing_identity_code)
);

create index if not exists reference_material_pricing_identities_lookup_idx
    on public.reference_material_pricing_identities (
        market_code, department, status, base_unit
    );

create table if not exists public.reference_material_pricing_identity_members (
    pricing_identity_id uuid not null
        references public.reference_material_pricing_identities(pricing_identity_id)
        on delete cascade,
    material_id uuid not null references public.reference_materials(material_id)
        on delete cascade,
    membership_basis text not null check (
        membership_basis in ('exact_price_class', 'reviewed_variant')
    ),
    created_at timestamptz not null default now(),
    primary key (pricing_identity_id, material_id)
);

create index if not exists reference_material_pricing_identity_members_material_idx
    on public.reference_material_pricing_identity_members (material_id);

create table if not exists public.market_material_pricing_identity_prices (
    pricing_identity_price_id uuid primary key default gen_random_uuid(),
    pricing_identity_id uuid not null
        references public.reference_material_pricing_identities(pricing_identity_id),
    catalog_version text not null
        references public.reference_catalog_versions(catalog_version),
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
    source_material_id uuid references public.reference_materials(material_id),
    formula_description text not null check (length(trim(formula_description)) between 1 and 4000),
    model_metadata jsonb not null default '{}'::jsonb check (
        jsonb_typeof(model_metadata) = 'object'
    ),
    effective_from date not null,
    effective_to date,
    status text not null default 'candidate' check (
        status in ('candidate', 'active', 'retired')
    ),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint market_material_pricing_identity_prices_range_check check (
        price_low <= price_typical and price_typical <= price_high
    ),
    constraint market_material_pricing_identity_prices_effective_check check (
        effective_to is null or effective_from <= effective_to
    ),
    unique (pricing_identity_id, catalog_version)
);

create unique index if not exists market_material_pricing_identity_prices_one_active_idx
    on public.market_material_pricing_identity_prices(pricing_identity_id)
    where status = 'active';

create index if not exists market_material_pricing_identity_prices_lookup_idx
    on public.market_material_pricing_identity_prices(
        pricing_identity_id, status, effective_from desc
    );

alter table public.company_material_items
    add column if not exists pricing_identity_id uuid
    references public.reference_material_pricing_identities(pricing_identity_id);

create index if not exists company_material_items_pricing_identity_idx
    on public.company_material_items(company_id, pricing_identity_id)
    where pricing_identity_id is not null;

alter table public.company_price_source_rows
    add column if not exists pricing_identity_id uuid
    references public.reference_material_pricing_identities(pricing_identity_id);

alter table public.material_identity_candidates
    add column if not exists selected_pricing_identity_id uuid
    references public.reference_material_pricing_identities(pricing_identity_id),
    add column if not exists candidate_pricing_identities jsonb
    not null default '[]'::jsonb check (
        jsonb_typeof(candidate_pricing_identities) = 'array'
        and jsonb_array_length(candidate_pricing_identities) <= 5
    );

alter table public.material_identity_resolution_events
    add column if not exists selected_pricing_identity_id uuid
    references public.reference_material_pricing_identities(pricing_identity_id),
    add column if not exists candidate_pricing_identities jsonb
    not null default '[]'::jsonb check (
        jsonb_typeof(candidate_pricing_identities) = 'array'
        and jsonb_array_length(candidate_pricing_identities) <= 5
    );

alter table public.reference_material_pricing_identities enable row level security;
alter table public.reference_material_pricing_identity_members enable row level security;
alter table public.market_material_pricing_identity_prices enable row level security;

revoke all on public.reference_material_pricing_identities from public, anon, authenticated;
revoke all on public.reference_material_pricing_identity_members from public, anon, authenticated;
revoke all on public.market_material_pricing_identity_prices from public, anon, authenticated;

grant all on public.reference_material_pricing_identities to service_role;
grant all on public.reference_material_pricing_identity_members to service_role;
grant all on public.market_material_pricing_identity_prices to service_role;

commit;
