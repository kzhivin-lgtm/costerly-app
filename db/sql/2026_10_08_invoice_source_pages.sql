-- 3.16.7: one invoice source may consist of arbitrary files received in any order.
-- The existing company_price_sources fields continue to represent the first page
-- for backward compatibility; this table is the complete immutable page ledger.

create table if not exists public.company_price_source_pages (
    source_page_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    source_id uuid not null references public.company_price_sources(source_id) on delete cascade,
    source_name text not null check (length(trim(source_name)) between 1 and 500),
    source_kind text not null check (source_kind in ('file', 'url')),
    source_url text,
    storage_path text,
    mime_type text,
    source_sha256 text,
    received_at timestamptz not null default now(),
    created_by uuid not null,
    unique (company_id, source_sha256)
);

create index if not exists company_price_source_pages_source_received_idx
    on public.company_price_source_pages(source_id, received_at);

alter table public.company_price_source_rows
    add column if not exists source_page_id uuid
    references public.company_price_source_pages(source_page_id) on delete cascade;

create index if not exists company_price_source_rows_page_idx
    on public.company_price_source_rows(source_page_id, source_row_number);

alter table public.company_price_source_pages enable row level security;

drop policy if exists company_price_source_pages_owner_all on public.company_price_source_pages;
create policy company_price_source_pages_owner_all on public.company_price_source_pages
for all to authenticated
using (
    exists (
        select 1 from public.company_members m
        where m.company_id = company_price_source_pages.company_id
          and m.user_id = (select auth.uid())
          and m.role = 'owner'
    )
)
with check (
    exists (
        select 1 from public.company_members m
        where m.company_id = company_price_source_pages.company_id
          and m.user_id = (select auth.uid())
          and m.role = 'owner'
    )
);
