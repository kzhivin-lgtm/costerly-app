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

create unique index if not exists reference_material_family_aliases_active_key_idx
    on public.reference_material_family_aliases (alias_key)
    where active;

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
    unit_code text not null check (unit_code in ('mm', 'm', 'sqm', 'kg', 'l', 'piece', 'set', 'sheet', 'roll')),
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

create unique index if not exists reference_measurement_unit_aliases_active_key_idx
    on public.reference_measurement_unit_aliases (alias_key)
    where active;

alter table public.reference_material_family_aliases enable row level security;
alter table public.reference_material_pricing_key_aliases enable row level security;
alter table public.reference_material_pricing_key_value_aliases enable row level security;
alter table public.reference_measurement_unit_aliases enable row level security;

revoke all on public.reference_material_family_aliases,
    public.reference_material_pricing_key_aliases,
    public.reference_material_pricing_key_value_aliases,
    public.reference_measurement_unit_aliases
from public, anon, authenticated;

grant all on public.reference_material_family_aliases,
    public.reference_material_pricing_key_aliases,
    public.reference_material_pricing_key_value_aliases,
    public.reference_measurement_unit_aliases
to service_role;

commit;
