-- Current editable pricing overrides for Objects Estimation.
-- This stores only the latest working value per estimate/object/field.
-- Apply manually in Supabase SQL editor before enabling persistent pricing overrides.

create table if not exists public.rfq_estimate_pricing_overrides (
    estimate_id text not null references public.rfq_estimates(estimate_id) on delete cascade,
    object_key text not null,
    field text not null,
    value numeric(14, 2) not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (estimate_id, object_key, field),
    constraint rfq_estimate_pricing_overrides_field_check
        check (field in ('sale_price_unit'))
);

create index if not exists rfq_estimate_pricing_overrides_estimate_idx
    on public.rfq_estimate_pricing_overrides(estimate_id);

alter table public.rfq_estimate_pricing_overrides enable row level security;

drop policy if exists rfq_estimate_pricing_overrides_anon_select
    on public.rfq_estimate_pricing_overrides;
drop policy if exists rfq_estimate_pricing_overrides_anon_insert
    on public.rfq_estimate_pricing_overrides;
drop policy if exists rfq_estimate_pricing_overrides_anon_update
    on public.rfq_estimate_pricing_overrides;

create policy rfq_estimate_pricing_overrides_anon_select
    on public.rfq_estimate_pricing_overrides
    for select
    to anon
    using (true);

create policy rfq_estimate_pricing_overrides_anon_insert
    on public.rfq_estimate_pricing_overrides
    for insert
    to anon
    with check (true);

create policy rfq_estimate_pricing_overrides_anon_update
    on public.rfq_estimate_pricing_overrides
    for update
    to anon
    using (true)
    with check (true);

grant select, insert, update on public.rfq_estimate_pricing_overrides to anon;
