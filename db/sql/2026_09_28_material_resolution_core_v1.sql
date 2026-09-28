-- 3.15.3 Shared Material Resolution Core foundation.
-- Adds versioning, company aliases, identity candidates, immutable resolution
-- events, and the Price Source linkage fields. It does not reprocess or link
-- existing rows and does not expose private company evidence globally.

begin;

create table if not exists public.material_resolver_versions (
    resolver_version text primary key check (
        length(trim(resolver_version)) between 1 and 100
    ),
    market_code text not null references public.reference_markets(market_code),
    algorithm_version text not null check (
        length(trim(algorithm_version)) between 1 and 100
    ),
    catalog_fingerprint text not null check (
        length(trim(catalog_fingerprint)) between 1 and 200
    ),
    status text not null check (status in ('candidate', 'active', 'retired')),
    activated_at timestamptz,
    created_at timestamptz not null default now(),
    constraint material_resolver_versions_activation_check check (
        status <> 'active' or activated_at is not null
    )
);

create unique index if not exists material_resolver_versions_one_active_idx
    on public.material_resolver_versions(market_code)
    where status = 'active';

insert into public.material_resolver_versions (
    resolver_version, market_code, algorithm_version, catalog_fingerprint,
    status, activated_at
) values (
    'material_identity_v1', 'IL', 'deterministic_v1',
    'IL:reference_materials:280:aliases:851:2026-09-28',
    'active', now()
)
on conflict (resolver_version) do update set
    algorithm_version = excluded.algorithm_version,
    catalog_fingerprint = excluded.catalog_fingerprint,
    status = excluded.status,
    activated_at = coalesce(
        public.material_resolver_versions.activated_at,
        excluded.activated_at
    );

create table if not exists public.company_material_aliases (
    alias_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    material_id uuid not null references public.reference_materials(material_id),
    supplier_id uuid references public.company_suppliers(supplier_id),
    alias_text text not null check (length(trim(alias_text)) between 1 and 500),
    resolver_key text not null check (length(trim(resolver_key)) between 1 and 500),
    source_row_id uuid references public.company_price_source_rows(row_id),
    confirmed_by uuid references auth.users(id),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists company_material_aliases_identity_uidx
    on public.company_material_aliases (
        company_id, coalesce(supplier_id::text, ''), resolver_key
    ) where active;

create index if not exists company_material_aliases_lookup_idx
    on public.company_material_aliases (
        company_id, resolver_key, active
    );

create table if not exists public.material_identity_candidates (
    candidate_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    market_code text not null references public.reference_markets(market_code),
    company_material_id uuid not null
        references public.company_material_items(company_material_id),
    source_row_id uuid references public.company_price_source_rows(row_id),
    source_phrase text not null check (length(trim(source_phrase)) between 1 and 1000),
    normalized_phrase text not null check (
        length(trim(normalized_phrase)) between 1 and 500
    ),
    supplier_id uuid references public.company_suppliers(supplier_id),
    supplier_sku text,
    proposed_category text,
    extracted_specifications jsonb not null default '{}'::jsonb check (
        jsonb_typeof(extracted_specifications) = 'object'
    ),
    candidate_materials jsonb not null default '[]'::jsonb check (
        jsonb_typeof(candidate_materials) = 'array'
        and jsonb_array_length(candidate_materials) <= 5
    ),
    resolution_route text not null check (
        length(trim(resolution_route)) between 1 and 100
    ),
    confidence_dimensions jsonb not null default '{}'::jsonb check (
        jsonb_typeof(confidence_dimensions) = 'object'
    ),
    resolver_version text not null
        references public.material_resolver_versions(resolver_version),
    status text not null default 'pending' check (
        status in ('pending', 'resolved', 'rejected', 'new_reference')
    ),
    selected_material_id uuid references public.reference_materials(material_id),
    reviewed_by uuid references auth.users(id),
    reviewed_at timestamptz,
    decision_notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint material_identity_candidates_review_check check (
        status = 'pending'
        or (reviewed_by is not null and reviewed_at is not null)
    ),
    constraint material_identity_candidates_selection_check check (
        status <> 'resolved' or selected_material_id is not null
    )
);

create index if not exists material_identity_candidates_review_idx
    on public.material_identity_candidates (
        market_code, status, created_at
    );

create index if not exists material_identity_candidates_company_idx
    on public.material_identity_candidates (
        company_id, status, created_at desc
    );

create table if not exists public.material_identity_resolution_events (
    resolution_event_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    market_code text not null references public.reference_markets(market_code),
    company_material_id uuid
        references public.company_material_items(company_material_id),
    source_row_id uuid references public.company_price_source_rows(row_id),
    candidate_id uuid references public.material_identity_candidates(candidate_id),
    selected_material_id uuid references public.reference_materials(material_id),
    resolution_status text not null check (
        resolution_status in (
            'resolved', 'shortlist', 'new_identity_or_needs_review'
        )
    ),
    resolution_route text not null check (
        length(trim(resolution_route)) between 1 and 100
    ),
    normalized_input jsonb not null check (
        jsonb_typeof(normalized_input) = 'object'
    ),
    candidate_materials jsonb not null default '[]'::jsonb check (
        jsonb_typeof(candidate_materials) = 'array'
        and jsonb_array_length(candidate_materials) <= 5
    ),
    confidence_dimensions jsonb not null default '{}'::jsonb check (
        jsonb_typeof(confidence_dimensions) = 'object'
    ),
    resolver_version text not null
        references public.material_resolver_versions(resolver_version),
    created_at timestamptz not null default now()
);

create index if not exists material_identity_resolution_events_source_idx
    on public.material_identity_resolution_events (
        company_id, source_row_id, created_at desc
    );

alter table public.company_price_source_rows
    add column if not exists reference_material_id uuid
    references public.reference_materials(material_id),
    add column if not exists identity_candidate_id uuid
    references public.material_identity_candidates(candidate_id),
    add column if not exists identity_route text,
    add column if not exists identity_confidence numeric(5, 2),
    add column if not exists conversion_confidence numeric(5, 2),
    add column if not exists eligibility_confidence numeric(5, 2),
    add column if not exists resolver_version text
    references public.material_resolver_versions(resolver_version);

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'company_price_source_rows_identity_confidence_check'
          and conrelid = 'public.company_price_source_rows'::regclass
    ) then
        alter table public.company_price_source_rows
            add constraint company_price_source_rows_identity_confidence_check
            check (identity_confidence between 0 and 100);
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'company_price_source_rows_conversion_confidence_check'
          and conrelid = 'public.company_price_source_rows'::regclass
    ) then
        alter table public.company_price_source_rows
            add constraint company_price_source_rows_conversion_confidence_check
            check (conversion_confidence between 0 and 100);
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'company_price_source_rows_eligibility_confidence_check'
          and conrelid = 'public.company_price_source_rows'::regclass
    ) then
        alter table public.company_price_source_rows
            add constraint company_price_source_rows_eligibility_confidence_check
            check (eligibility_confidence between 0 and 100);
    end if;
end $$;

alter table public.company_material_offers
    add column if not exists price_scope text not null default 'material_only',
    add column if not exists included_services text[] not null default '{}',
    add column if not exists identity_confidence numeric(5, 2),
    add column if not exists conversion_confidence numeric(5, 2),
    add column if not exists eligibility_confidence numeric(5, 2);

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'company_material_offers_price_scope_check'
          and conrelid = 'public.company_material_offers'::regclass
    ) then
        alter table public.company_material_offers
            add constraint company_material_offers_price_scope_check check (
                price_scope in (
                    'material_only', 'cut_to_size',
                    'fabricated_component', 'retail_package'
                )
            );
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'company_material_offers_identity_confidence_check'
          and conrelid = 'public.company_material_offers'::regclass
    ) then
        alter table public.company_material_offers
            add constraint company_material_offers_identity_confidence_check
            check (identity_confidence between 0 and 100);
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'company_material_offers_conversion_confidence_check'
          and conrelid = 'public.company_material_offers'::regclass
    ) then
        alter table public.company_material_offers
            add constraint company_material_offers_conversion_confidence_check
            check (conversion_confidence between 0 and 100);
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'company_material_offers_eligibility_confidence_check'
          and conrelid = 'public.company_material_offers'::regclass
    ) then
        alter table public.company_material_offers
            add constraint company_material_offers_eligibility_confidence_check
            check (eligibility_confidence between 0 and 100);
    end if;
end $$;

alter table public.material_resolver_versions enable row level security;
alter table public.company_material_aliases enable row level security;
alter table public.material_identity_candidates enable row level security;
alter table public.material_identity_resolution_events enable row level security;

revoke all on public.material_resolver_versions from public, anon, authenticated;
revoke all on public.company_material_aliases from public, anon, authenticated;
revoke all on public.material_identity_candidates from public, anon, authenticated;
revoke all on public.material_identity_resolution_events from public, anon, authenticated;

grant all on public.material_resolver_versions to service_role;
grant all on public.company_material_aliases to service_role;
grant all on public.material_identity_candidates to service_role;
grant all on public.material_identity_resolution_events to service_role;

commit;

select
    to_regclass('public.material_resolver_versions') as resolver_versions,
    to_regclass('public.company_material_aliases') as company_aliases,
    to_regclass('public.material_identity_candidates') as identity_candidates,
    to_regclass('public.material_identity_resolution_events') as resolution_events;
