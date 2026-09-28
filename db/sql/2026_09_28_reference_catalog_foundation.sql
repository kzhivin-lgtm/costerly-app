-- 3.15.1 Multi-market reference catalog foundation.
-- Global identities are separate from country-specific prices, terminology,
-- labor assumptions, and operation standards. Israel is the first market.
-- This migration deliberately seeds no unsupported price or time values.

create table if not exists public.reference_markets (
    market_code text primary key check (market_code ~ '^[A-Z]{2}$'),
    market_name text not null check (length(trim(market_name)) between 1 and 120),
    default_currency text not null check (default_currency ~ '^[A-Z]{3}$'),
    default_language_code text not null check (
        default_language_code ~ '^[a-z]{2}(-[A-Z]{2})?$'
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

insert into public.reference_markets (
    market_code, market_name, default_currency, default_language_code
) values ('IL', 'Israel', 'ILS', 'he-IL')
on conflict (market_code) do update set
    market_name = excluded.market_name,
    default_currency = excluded.default_currency,
    default_language_code = excluded.default_language_code,
    active = true,
    updated_at = now();

alter table public.companies
    add column if not exists estimation_market_code text not null default 'IL';

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'companies_estimation_market_code_fk'
    ) then
        alter table public.companies
            add constraint companies_estimation_market_code_fk
            foreign key (estimation_market_code)
            references public.reference_markets(market_code);
    end if;
end $$;

create table if not exists public.reference_sources (
    source_id uuid primary key default gen_random_uuid(),
    market_code text not null references public.reference_markets(market_code),
    source_type text not null check (source_type in (
        'official', 'supplier', 'manufacturer', 'retailer', 'industry',
        'research', 'platform_observation'
    )),
    source_channel text not null default 'other' constraint reference_sources_source_channel_check check (source_channel in (
        'manufacturer', 'importer_distributor', 'trade_supplier',
        'specialist_retailer', 'diy_retail', 'marketplace',
        'public_procurement', 'other'
    )),
    source_name text not null check (length(trim(source_name)) between 1 and 240),
    source_url text not null check (length(trim(source_url)) between 1 and 2000),
    source_date date not null,
    retrieved_at timestamptz not null default now(),
    language_code text,
    region text,
    evidence jsonb not null default '{}'::jsonb check (
        jsonb_typeof(evidence) = 'object'
    ),
    created_at timestamptz not null default now(),
    unique (source_id, market_code)
);

alter table public.reference_sources
    add column if not exists source_channel text not null default 'other';

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'reference_sources_source_channel_check'
          and conrelid = 'public.reference_sources'::regclass
    ) then
        alter table public.reference_sources
            add constraint reference_sources_source_channel_check
            check (source_channel in (
                'manufacturer', 'importer_distributor', 'trade_supplier',
                'specialist_retailer', 'diy_retail', 'marketplace',
                'public_procurement', 'other'
            ));
    end if;
end $$;

create table if not exists public.reference_material_categories (
    category_code text primary key check (
        length(category_code) between 1 and 120
        and category_code = lower(category_code)
        and category_code !~ '[^a-z0-9_]'
    ),
    category_name text not null check (length(trim(category_name)) between 1 and 160),
    department text not null check (department in (
        'wood', 'metal', 'glass_stone_plastic', 'coating', 'hardware',
        'consumable', 'packaging'
    )),
    parent_category_code text references public.reference_material_categories(category_code),
    active boolean not null default true,
    sort_order integer not null default 0
);

create table if not exists public.reference_materials (
    material_id uuid primary key default gen_random_uuid(),
    material_code text not null unique check (
        length(material_code) between 1 and 140
        and material_code = lower(material_code)
        and material_code !~ '[^a-z0-9_]'
    ),
    department text not null check (department in (
        'wood', 'metal', 'glass_stone_plastic', 'coating', 'hardware',
        'consumable', 'packaging'
    )),
    category_code text not null references public.reference_material_categories(category_code),
    canonical_name text not null check (length(trim(canonical_name)) between 1 and 500),
    base_unit text not null check (length(trim(base_unit)) between 1 and 80),
    specifications jsonb not null default '{}'::jsonb check (
        jsonb_typeof(specifications) = 'object'
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.market_material_profiles (
    market_profile_id uuid primary key default gen_random_uuid(),
    material_id uuid not null references public.reference_materials(material_id),
    market_code text not null references public.reference_markets(market_code),
    market_name text not null check (length(trim(market_name)) between 1 and 500),
    language_code text not null,
    local_specifications jsonb not null default '{}'::jsonb check (
        jsonb_typeof(local_specifications) = 'object'
    ),
    availability_status text not null default 'common' check (
        availability_status in ('common', 'limited', 'special_order', 'unavailable')
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (material_id, market_code, language_code)
);

create or replace function public.normalize_reference_material_alias(value text)
returns text
language sql
immutable
strict
set search_path = public
as $$
    select lower(trim(regexp_replace(value, '[[:space:]]+', ' ', 'g')))
$$;

create table if not exists public.reference_material_aliases (
    alias_id uuid primary key default gen_random_uuid(),
    material_id uuid not null references public.reference_materials(material_id)
        on delete cascade,
    market_code text not null references public.reference_markets(market_code),
    language_code text not null check (length(trim(language_code)) between 2 and 20),
    alias_text text not null check (length(trim(alias_text)) between 1 and 500),
    alias_key text not null check (
        length(trim(alias_key)) between 1 and 500
        and alias_key = public.normalize_reference_material_alias(alias_text)
    ),
    alias_kind text not null check (alias_kind in (
        'canonical', 'market_name', 'supplier_listing', 'technical_code',
        'synonym'
    )),
    source_id uuid,
    supplier_name text,
    exact_identity boolean not null default false,
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint reference_material_aliases_source_market_fk
        foreign key (source_id, market_code)
        references public.reference_sources(source_id, market_code),
    unique (material_id, market_code, language_code, alias_key)
);

create index if not exists reference_material_aliases_lookup_idx
    on public.reference_material_aliases (
        market_code, alias_key, active, confidence desc
    );

create index if not exists reference_material_aliases_material_idx
    on public.reference_material_aliases (material_id, market_code)
    where active;

create table if not exists public.market_material_offers (
    market_offer_id uuid primary key default gen_random_uuid(),
    material_id uuid not null references public.reference_materials(material_id),
    market_code text not null references public.reference_markets(market_code),
    source_id uuid not null,
    supplier_name text not null check (length(trim(supplier_name)) between 1 and 240),
    supplier_sku text,
    source_price numeric(18, 6) not null check (source_price >= 0),
    source_currency text not null check (source_currency ~ '^[A-Z]{3}$'),
    source_unit text not null check (length(trim(source_unit)) between 1 and 80),
    price_scope text not null check (price_scope in (
        'material_only', 'cut_to_size', 'fabricated_component', 'retail_package'
    )),
    included_services text[] not null default '{}',
    delivery_included boolean,
    package_quantity numeric(18, 6) check (package_quantity is null or package_quantity > 0),
    minimum_order_quantity numeric(18, 6) check (
        minimum_order_quantity is null or minimum_order_quantity >= 0
    ),
    vat_mode text not null check (vat_mode in ('included', 'excluded', 'exempt', 'unknown')),
    normalized_price_ex_vat numeric(18, 6),
    normalized_unit text,
    conversion_basis jsonb not null default '{}'::jsonb check (
        jsonb_typeof(conversion_basis) = 'object'
    ),
    region text,
    valid_from date,
    valid_to date,
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    status text not null default 'candidate' check (
        status in ('candidate', 'reviewed', 'active', 'archived')
    ),
    created_at timestamptz not null default now(),
    constraint market_material_offers_source_market_fk
        foreign key (source_id, market_code)
        references public.reference_sources(source_id, market_code),
    constraint market_material_offers_normalized_pair_check check (
        (normalized_price_ex_vat is null or normalized_price_ex_vat >= 0)
        and (normalized_unit is null or length(trim(normalized_unit)) > 0)
        and (normalized_price_ex_vat is null or normalized_unit is not null)
    ),
    constraint market_material_offers_validity_check check (
        valid_to is null or valid_from is null or valid_from <= valid_to
    ),
    unique (market_offer_id, market_code, price_scope)
);

create index if not exists market_material_offers_lookup_idx
    on public.market_material_offers (
        market_code, material_id, status, valid_from desc, created_at desc
    );

create table if not exists public.market_material_baselines (
    baseline_id uuid primary key default gen_random_uuid(),
    material_id uuid not null references public.reference_materials(material_id),
    market_code text not null references public.reference_markets(market_code),
    region text,
    price_low numeric(18, 6) not null check (price_low >= 0),
    price_typical numeric(18, 6) not null check (price_typical >= 0),
    price_high numeric(18, 6) not null check (price_high >= 0),
    unit text not null check (length(trim(unit)) between 1 and 80),
    currency text not null check (currency ~ '^[A-Z]{3}$'),
    price_scope text not null check (price_scope in (
        'material_only', 'cut_to_size', 'fabricated_component', 'retail_package'
    )),
    vat_mode text not null default 'excluded' check (vat_mode = 'excluded'),
    methodology text not null check (length(trim(methodology)) between 1 and 2000),
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    status text not null default 'candidate' check (
        status in ('candidate', 'reviewed', 'active', 'archived')
    ),
    version integer not null default 1 check (version > 0),
    supersedes_baseline_id uuid references public.market_material_baselines(baseline_id),
    effective_from date not null,
    effective_to date,
    approved_by uuid references auth.users(id),
    approved_at timestamptz,
    created_at timestamptz not null default now(),
    constraint market_material_baselines_range_check check (
        price_low <= price_typical and price_typical <= price_high
    ),
    constraint market_material_baselines_effective_check check (
        effective_to is null or effective_from <= effective_to
    ),
    constraint market_material_baselines_approval_check check (
        status <> 'active' or (approved_by is not null and approved_at is not null)
    ),
    unique (baseline_id, market_code, price_scope)
);

create table if not exists public.market_material_baseline_evidence (
    baseline_id uuid not null,
    market_offer_id uuid not null,
    market_code text not null references public.reference_markets(market_code),
    price_scope text not null,
    primary key (baseline_id, market_offer_id),
    constraint market_material_baseline_evidence_baseline_fk
        foreign key (baseline_id, market_code, price_scope)
        references public.market_material_baselines(baseline_id, market_code, price_scope)
        on delete cascade,
    constraint market_material_baseline_evidence_offer_fk
        foreign key (market_offer_id, market_code, price_scope)
        references public.market_material_offers(market_offer_id, market_code, price_scope)
);

create or replace function public.require_market_material_baseline_evidence()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    if new.status = 'active' and not exists (
        select 1
        from public.market_material_baseline_evidence e
        where e.baseline_id = new.baseline_id
          and e.market_code = new.market_code
    ) then
        raise exception 'An active material baseline requires same-market same-scope offer evidence';
    end if;
    return new;
end;
$$;

drop trigger if exists market_material_baseline_evidence_guard
    on public.market_material_baselines;
create trigger market_material_baseline_evidence_guard
before insert or update of status on public.market_material_baselines
for each row execute function public.require_market_material_baseline_evidence();

create unique index if not exists market_material_baselines_active_scope_uidx
    on public.market_material_baselines (
        material_id, market_code, coalesce(region, ''), unit, currency,
        price_scope
    ) where status = 'active';

create table if not exists public.reference_labor_roles (
    role_code text primary key check (
        length(role_code) between 1 and 100
        and role_code = lower(role_code)
        and role_code !~ '[^a-z0-9_]'
    ),
    role_name text not null check (length(trim(role_name)) between 1 and 160),
    department text not null check (department in (
        'wood', 'metal', 'coating', 'installation', 'general'
    )),
    company_position_code text,
    company_match_policy text not null default 'none' check (
        company_match_policy in ('exact', 'requires_confirmation', 'none')
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    constraint reference_labor_roles_company_match_check check (
        (company_match_policy = 'none' and company_position_code is null)
        or
        (company_match_policy <> 'none' and company_position_code is not null)
    )
);

create table if not exists public.reference_operation_drivers (
    driver_code text primary key check (
        length(driver_code) between 1 and 120
        and driver_code = lower(driver_code)
        and driver_code !~ '[^a-z0-9_]'
    ),
    driver_name text not null check (length(trim(driver_name)) between 1 and 160),
    unit text not null check (length(trim(unit)) between 1 and 80),
    quantity_type text not null check (quantity_type in (
        'count', 'length', 'area', 'weight', 'volume'
    )),
    description text not null check (length(trim(description)) between 1 and 1000),
    active boolean not null default true,
    sort_order integer not null default 0
);

create table if not exists public.reference_operations (
    operation_id uuid primary key default gen_random_uuid(),
    operation_code text not null unique check (
        length(operation_code) between 1 and 140
        and operation_code = lower(operation_code)
        and operation_code !~ '[^a-z0-9_]'
    ),
    department text not null check (department in (
        'preproduction', 'wood', 'metal', 'glass_stone_plastic', 'coating',
        'assembly', 'installation', 'packaging', 'logistics'
    )),
    operation_name text not null check (length(trim(operation_name)) between 1 and 240),
    description text not null check (length(trim(description)) between 1 and 2000),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.market_operation_models (
    operation_model_id uuid primary key default gen_random_uuid(),
    operation_id uuid not null references public.reference_operations(operation_id),
    market_code text not null references public.reference_markets(market_code),
    source_id uuid not null,
    region text,
    material_family text,
    machine_code text,
    qualifiers jsonb not null default '{}'::jsonb check (
        jsonb_typeof(qualifiers) = 'object'
    ),
    formula_version text not null default 'operation_time_v1',
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    status text not null default 'candidate' check (
        status in ('candidate', 'reviewed', 'active', 'archived')
    ),
    version integer not null default 1 check (version > 0),
    supersedes_operation_model_id uuid references public.market_operation_models(operation_model_id),
    effective_from date not null,
    effective_to date,
    approved_by uuid references auth.users(id),
    approved_at timestamptz,
    created_at timestamptz not null default now(),
    constraint market_operation_models_source_market_fk
        foreign key (source_id, market_code)
        references public.reference_sources(source_id, market_code),
    constraint market_operation_models_effective_check check (
        effective_to is null or effective_from <= effective_to
    ),
    constraint market_operation_models_approval_check check (
        status <> 'active' or (approved_by is not null and approved_at is not null)
    )
);

create table if not exists public.market_operation_time_components (
    component_id uuid primary key default gen_random_uuid(),
    operation_model_id uuid not null references public.market_operation_models(operation_model_id)
        on delete cascade,
    component_code text not null check (
        length(component_code) between 1 and 120
        and component_code = lower(component_code)
        and component_code !~ '[^a-z0-9_]'
    ),
    component_type text not null check (component_type in (
        'setup', 'throughput', 'auxiliary', 'minimum_batch'
    )),
    driver_code text references public.reference_operation_drivers(driver_code),
    driver_unit text,
    value_low numeric(18, 6) not null check (value_low >= 0),
    value_typical numeric(18, 6) not null check (value_typical >= 0),
    value_high numeric(18, 6) not null check (value_high >= 0),
    value_unit text not null check (value_unit in (
        'labor_minutes', 'labor_minutes_per_unit', 'units_per_hour'
    )),
    role_code text references public.reference_labor_roles(role_code),
    crew_size numeric(6, 2) not null default 1 check (crew_size > 0),
    sort_order integer not null default 0,
    created_at timestamptz not null default now(),
    unique (operation_model_id, component_code),
    constraint market_operation_time_components_range_check check (
        value_low <= value_typical and value_typical <= value_high
    ),
    constraint market_operation_time_components_driver_check check (
        (component_type in ('setup', 'minimum_batch') and driver_code is null and driver_unit is null)
        or
        (component_type in ('throughput', 'auxiliary') and driver_code is not null and driver_unit is not null)
    )
);

create table if not exists public.reference_operation_roles (
    operation_id uuid not null references public.reference_operations(operation_id),
    role_code text not null references public.reference_labor_roles(role_code),
    capability_level text not null check (capability_level in (
        'primary', 'qualified', 'assistant'
    )),
    primary key (operation_id, role_code)
);

create table if not exists public.reference_operation_driver_options (
    operation_id uuid not null references public.reference_operations(operation_id),
    driver_code text not null references public.reference_operation_drivers(driver_code),
    driver_purpose text not null check (driver_purpose in (
        'primary', 'secondary', 'evidence'
    )),
    primary key (operation_id, driver_code)
);

alter table public.company_material_items
    add column if not exists reference_material_id uuid
    references public.reference_materials(material_id);

create index if not exists company_material_items_reference_idx
    on public.company_material_items(company_id, reference_material_id)
    where reference_material_id is not null;

create index if not exists market_operation_models_lookup_idx
    on public.market_operation_models (
        market_code, operation_id, status, effective_from desc, version desc
    );

alter table public.reference_markets enable row level security;
alter table public.reference_sources enable row level security;
alter table public.reference_materials enable row level security;
alter table public.reference_material_categories enable row level security;
alter table public.market_material_profiles enable row level security;
alter table public.reference_material_aliases enable row level security;
alter table public.market_material_offers enable row level security;
alter table public.market_material_baselines enable row level security;
alter table public.market_material_baseline_evidence enable row level security;
alter table public.reference_labor_roles enable row level security;
alter table public.reference_operation_drivers enable row level security;
alter table public.reference_operations enable row level security;
alter table public.market_operation_models enable row level security;
alter table public.market_operation_time_components enable row level security;
alter table public.reference_operation_roles enable row level security;
alter table public.reference_operation_driver_options enable row level security;

revoke all on public.reference_markets from public, anon, authenticated;
revoke all on public.reference_sources from public, anon, authenticated;
revoke all on public.reference_materials from public, anon, authenticated;
revoke all on public.reference_material_categories from public, anon, authenticated;
revoke all on public.market_material_profiles from public, anon, authenticated;
revoke all on public.reference_material_aliases from public, anon, authenticated;
revoke all on public.market_material_offers from public, anon, authenticated;
revoke all on public.market_material_baselines from public, anon, authenticated;
revoke all on public.market_material_baseline_evidence from public, anon, authenticated;
revoke all on public.reference_labor_roles from public, anon, authenticated;
revoke all on public.reference_operation_drivers from public, anon, authenticated;
revoke all on public.reference_operations from public, anon, authenticated;
revoke all on public.market_operation_models from public, anon, authenticated;
revoke all on public.market_operation_time_components from public, anon, authenticated;
revoke all on public.reference_operation_roles from public, anon, authenticated;
revoke all on public.reference_operation_driver_options from public, anon, authenticated;

grant all on public.reference_markets to service_role;
grant all on public.reference_sources to service_role;
grant all on public.reference_materials to service_role;
grant all on public.reference_material_categories to service_role;
grant all on public.market_material_profiles to service_role;
grant all on public.reference_material_aliases to service_role;
grant all on public.market_material_offers to service_role;
grant all on public.market_material_baselines to service_role;
grant all on public.market_material_baseline_evidence to service_role;
grant all on public.reference_labor_roles to service_role;
grant all on public.reference_operation_drivers to service_role;
grant all on public.reference_operations to service_role;
grant all on public.market_operation_models to service_role;
grant all on public.market_operation_time_components to service_role;
grant all on public.reference_operation_roles to service_role;
grant all on public.reference_operation_driver_options to service_role;
