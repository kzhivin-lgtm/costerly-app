-- 3.7.1 Company Price Sources.
-- Additive, repeat-safe storage for private supplier sources, extracted rows,
-- company-private material identities, and versioned offers. Existing public
-- materials rows and the current pricing resolver are intentionally untouched.

create table if not exists public.company_suppliers (
    supplier_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    supplier_name text not null check (length(trim(supplier_name)) between 1 and 240),
    normalized_name text not null check (length(trim(normalized_name)) between 1 and 240),
    country_code text,
    categories text[] not null default '{}',
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (company_id, normalized_name)
);

create table if not exists public.company_price_sources (
    source_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    supplier_id uuid references public.company_suppliers(supplier_id),
    category text not null check (length(trim(category)) between 1 and 100),
    source_kind text not null check (source_kind in ('file', 'url')),
    source_name text not null check (length(trim(source_name)) between 1 and 500),
    source_url text,
    storage_path text,
    mime_type text,
    source_sha256 text,
    document_type text,
    document_date date,
    currency text,
    vat_mode text check (vat_mode is null or vat_mode in ('included', 'excluded', 'mixed', 'unknown')),
    status text not null default 'processing'
        check (status in ('processing', 'ready', 'partial', 'failed', 'archived')),
    processing_summary jsonb not null default '{}'::jsonb,
    error_message text,
    created_by uuid not null,
    processed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists company_price_sources_company_created_idx
    on public.company_price_sources(company_id, created_at desc);

create table if not exists public.company_material_items (
    company_material_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    category text not null,
    canonical_name text not null check (length(trim(canonical_name)) between 1 and 500),
    normalized_name text not null check (length(trim(normalized_name)) between 1 and 500),
    preferred_unit text,
    specifications jsonb not null default '{}'::jsonb,
    country_code text,
    status text not null default 'private' check (status in ('private', 'country_candidate', 'archived')),
    created_from_source_id uuid references public.company_price_sources(source_id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (company_id, category, normalized_name)
);

create table if not exists public.company_price_source_rows (
    row_id uuid primary key default gen_random_uuid(),
    source_id uuid not null references public.company_price_sources(source_id) on delete cascade,
    company_id text not null references public.companies(company_id),
    source_row_number integer not null,
    raw_description text,
    raw_sku text,
    raw_price numeric(16, 4),
    raw_currency text,
    raw_unit text,
    raw_package_quantity numeric(16, 4),
    raw_quantity numeric(16, 4),
    raw_line_total numeric(16, 4),
    raw_vat_included boolean,
    normalized_name text,
    normalized_price numeric(16, 4),
    purchase_unit text,
    calculation_unit text,
    conversion_factor numeric(18, 8),
    normalized_unit text,
    conversion_basis jsonb not null default '{}'::jsonb,
    company_material_id uuid references public.company_material_items(company_material_id),
    result_status text not null check (result_status in ('updated', 'new', 'unresolved', 'excluded')),
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    reason_codes text[] not null default '{}',
    evidence jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (source_id, source_row_number)
);

create index if not exists company_price_source_rows_source_idx
    on public.company_price_source_rows(source_id, source_row_number);

create table if not exists public.company_material_offers (
    offer_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    company_material_id uuid not null references public.company_material_items(company_material_id),
    supplier_id uuid references public.company_suppliers(supplier_id),
    source_id uuid not null references public.company_price_sources(source_id),
    source_row_id uuid not null references public.company_price_source_rows(row_id),
    supplier_sku text,
    source_price numeric(16, 4) not null check (source_price >= 0),
    source_unit text not null,
    purchase_unit text not null,
    calculation_unit text not null,
    conversion_factor numeric(18, 8) not null check (conversion_factor > 0),
    normalized_price numeric(16, 4) not null check (normalized_price >= 0),
    normalized_unit text not null,
    currency text not null,
    vat_included boolean,
    valid_from date,
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    status text not null default 'active' check (status in ('active', 'superseded', 'unresolved', 'archived')),
    created_at timestamptz not null default now()
);

create index if not exists company_material_offers_active_idx
    on public.company_material_offers(company_id, company_material_id, status, created_at desc);

alter table public.company_suppliers enable row level security;
alter table public.company_price_sources enable row level security;
alter table public.company_material_items enable row level security;
alter table public.company_price_source_rows enable row level security;
alter table public.company_material_offers enable row level security;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'company_suppliers',
        'company_price_sources',
        'company_material_items',
        'company_price_source_rows',
        'company_material_offers'
    ]
    loop
        if not exists (
            select 1
            from pg_policies
            where schemaname = 'public'
              and tablename = table_name
              and policyname = table_name || '_owner_all'
        ) then
            execute format(
                'create policy %I on public.%I for all to authenticated using '
                || '(exists (select 1 from public.company_members m where m.company_id = %I.company_id '
                || 'and m.user_id = (select auth.uid()) and m.role = ''owner'')) with check '
                || '(exists (select 1 from public.company_members m where m.company_id = %I.company_id '
                || 'and m.user_id = (select auth.uid()) and m.role = ''owner''))',
                table_name || '_owner_all', table_name, table_name, table_name
            );
        end if;
        execute format('revoke all on public.%I from anon', table_name);
        execute format('grant select, insert, update, delete on public.%I to authenticated', table_name);
    end loop;
end $$;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'company-price-sources',
    'company-price-sources',
    false,
    52428800,
    array[
        'application/pdf',
        'text/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/html',
        'image/jpeg',
        'image/png'
    ]::text[]
)
on conflict (id) do nothing;
