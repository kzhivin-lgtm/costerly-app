-- 3.14.1 company CNC estimate-level feedback foundation.
-- The active route remains exclusive: in-house when CNC is available in the
-- company, subcontractor when it is not. An untouched level 3 is not an event.

create table if not exists public.company_cnc_estimate_level_events (
    event_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    user_id uuid references auth.users(id) on delete set null,
    route text not null check (route in ('in_house', 'subcontractor')),
    previous_level smallint not null check (previous_level between 1 and 5),
    previous_level_explicit boolean not null,
    selected_level smallint not null check (selected_level between 1 and 5),
    source text not null default 'machinery_setting' check (
        source = 'machinery_setting'
    ),
    occurred_at timestamptz not null default now()
);

create index if not exists company_cnc_estimate_level_events_company_time_idx
    on public.company_cnc_estimate_level_events (
        company_id, occurred_at desc
    );

create index if not exists company_cnc_estimate_level_events_route_time_idx
    on public.company_cnc_estimate_level_events (
        route, occurred_at desc
    );

alter table public.company_cnc_estimate_level_events enable row level security;

revoke all on public.company_cnc_estimate_level_events
    from public, anon, authenticated;
grant all on public.company_cnc_estimate_level_events to service_role;

comment on table public.company_cnc_estimate_level_events is
    'Explicit CNC estimate-level changes only; contains no estimate cost or customer content.';
