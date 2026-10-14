-- 3.17.1.4 Shared aliases for material interpretation.
--
-- This is the single persistent source for aliases used to establish a
-- material Family and Pricing Key facts from incoming text. It deliberately
-- does not point at a price, purchase format or Company Catalog item.

begin;

create table if not exists public.reference_material_family_aliases (
    family_alias_id uuid primary key default gen_random_uuid(),
    family_id uuid not null references public.reference_material_families(family_id)
        on delete cascade,
    language_code text not null check (length(trim(language_code)) between 2 and 20),
    alias_text text not null check (length(trim(alias_text)) between 1 and 240),
    alias_key text not null check (
        alias_key = public.normalize_reference_material_alias(alias_text)
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (family_id, alias_key)
);

-- A spelling may honestly denote more than one Family.  Those terms are kept
-- in the catalog and marked below instead of being silently assigned to the
-- first Family that happened to be seeded.  Only unambiguous aliases may
-- select a Family automatically.
create index if not exists reference_material_family_aliases_active_key_idx
    on public.reference_material_family_aliases (alias_key)
    where active;

create table if not exists public.reference_material_family_ambiguous_aliases (
    ambiguous_alias_id uuid primary key default gen_random_uuid(),
    alias_key text not null unique check (length(trim(alias_key)) between 1 and 240),
    alias_text text not null check (length(trim(alias_text)) between 1 and 240),
    language_code text not null check (length(trim(language_code)) between 2 and 20),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.reference_material_family_ambiguous_alias_candidates (
    ambiguous_alias_id uuid not null
        references public.reference_material_family_ambiguous_aliases(ambiguous_alias_id)
        on delete cascade,
    family_id uuid not null references public.reference_material_families(family_id)
        on delete cascade,
    primary key (ambiguous_alias_id, family_id)
);

create table if not exists public.reference_material_pricing_key_aliases (
    pricing_key_alias_id uuid primary key default gen_random_uuid(),
    family_id uuid not null references public.reference_material_families(family_id)
        on delete cascade,
    fact_field text not null check (
        fact_field = lower(fact_field) and fact_field !~ '[^a-z0-9_]'
    ),
    language_code text not null check (length(trim(language_code)) between 2 and 20),
    alias_text text not null check (length(trim(alias_text)) between 1 and 240),
    alias_key text not null check (
        alias_key = public.normalize_reference_material_alias(alias_text)
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (family_id, fact_field, alias_key)
);

create index if not exists reference_material_pricing_key_aliases_lookup_idx
    on public.reference_material_pricing_key_aliases (family_id, fact_field, alias_key)
    where active;

create table if not exists public.reference_material_pricing_key_value_aliases (
    pricing_key_value_alias_id uuid primary key default gen_random_uuid(),
    family_id uuid not null references public.reference_material_families(family_id)
        on delete cascade,
    fact_field text not null check (
        fact_field = lower(fact_field) and fact_field !~ '[^a-z0-9_]'
    ),
    canonical_value text not null check (length(trim(canonical_value)) between 1 and 240),
    language_code text not null check (length(trim(language_code)) between 2 and 20),
    alias_text text not null check (length(trim(alias_text)) between 1 and 240),
    alias_key text not null check (
        alias_key = public.normalize_reference_material_alias(alias_text)
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (family_id, fact_field, canonical_value, alias_key)
);

create index if not exists reference_material_pricing_key_value_aliases_lookup_idx
    on public.reference_material_pricing_key_value_aliases (family_id, fact_field, alias_key)
    where active;

create table if not exists public.reference_measurement_unit_aliases (
    measurement_unit_alias_id uuid primary key default gen_random_uuid(),
    -- ``unit_code`` is the canonical calculation unit.  A source spelling
    -- such as ``cm`` can therefore normalize to ``mm`` with factor 10, and
    -- an imperial spelling is handled by the same deterministic path.
    unit_code text not null check (length(trim(unit_code)) between 1 and 40),
    dimension_code text not null check (dimension_code in (
        'length', 'area', 'volume', 'mass', 'count', 'package', 'other'
    )),
    conversion_factor numeric(20, 10) not null check (conversion_factor > 0),
    language_code text not null check (length(trim(language_code)) between 2 and 20),
    alias_text text not null check (length(trim(alias_text)) between 1 and 80),
    alias_key text not null check (
        alias_key = public.normalize_reference_material_alias(alias_text)
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (unit_code, alias_key)
);

create index if not exists reference_measurement_unit_aliases_active_key_idx
    on public.reference_measurement_unit_aliases (alias_key)
    where active;

create table if not exists public.reference_operation_aliases (
    operation_alias_id uuid primary key default gen_random_uuid(),
    operation_id uuid not null references public.reference_operations(operation_id)
        on delete cascade,
    language_code text not null check (length(trim(language_code)) between 2 and 20),
    alias_text text not null check (length(trim(alias_text)) between 1 and 240),
    alias_key text not null check (
        alias_key = public.normalize_reference_material_alias(alias_text)
    ),
    -- A service-only phrase can move a source row out of material intake.
    -- A general operation phrase remains ordinary evidence until the agent has
    -- independently classified the row as a service.
    service_only boolean not null default false,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (operation_id, alias_key)
);

create index if not exists reference_operation_aliases_active_key_idx
    on public.reference_operation_aliases (alias_key)
    where active;

alter table public.reference_material_family_aliases enable row level security;
alter table public.reference_material_family_ambiguous_aliases enable row level security;
alter table public.reference_material_family_ambiguous_alias_candidates enable row level security;
alter table public.reference_material_pricing_key_aliases enable row level security;
alter table public.reference_material_pricing_key_value_aliases enable row level security;
alter table public.reference_measurement_unit_aliases enable row level security;
alter table public.reference_operation_aliases enable row level security;

revoke all on public.reference_material_family_aliases,
    public.reference_material_family_ambiguous_aliases,
    public.reference_material_family_ambiguous_alias_candidates,
    public.reference_material_pricing_key_aliases,
    public.reference_material_pricing_key_value_aliases,
    public.reference_measurement_unit_aliases,
    public.reference_operation_aliases
from public, anon, authenticated;

grant all on public.reference_material_family_aliases,
    public.reference_material_family_ambiguous_aliases,
    public.reference_material_family_ambiguous_alias_candidates,
    public.reference_material_pricing_key_aliases,
    public.reference_material_pricing_key_value_aliases,
    public.reference_measurement_unit_aliases,
    public.reference_operation_aliases
to service_role;

commit;
