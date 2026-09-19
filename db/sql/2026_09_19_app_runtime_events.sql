-- Production observability foundation v1.
-- Apply manually in Supabase before deploying application-side event writes.
-- Service-role writes only. No browser or authenticated-user policy is added.

create table if not exists public.app_runtime_events (
    event_id uuid primary key default gen_random_uuid(),
    occurred_at timestamptz not null,
    received_at timestamptz not null default now(),
    schema_version text not null,
    build_version text not null,
    source text not null,
    trace_id uuid not null,
    session_id uuid,
    run_id uuid,
    event_name text not null,
    screen text,
    status text not null default 'ok',
    elapsed_ms numeric(14, 3),
    duration_ms numeric(14, 3),
    metadata jsonb not null default '{}'::jsonb,
    constraint app_runtime_events_source_check
        check (source in ('browser', 'server')),
    constraint app_runtime_events_status_check
        check (status in ('ok', 'error', 'timeout', 'dropped', 'unknown')),
    constraint app_runtime_events_metadata_object_check
        check (jsonb_typeof(metadata) = 'object')
);

create index if not exists app_runtime_events_trace_idx
    on public.app_runtime_events (trace_id, occurred_at);

create index if not exists app_runtime_events_recent_idx
    on public.app_runtime_events (occurred_at desc);

create index if not exists app_runtime_events_name_idx
    on public.app_runtime_events (event_name, occurred_at desc);

alter table public.app_runtime_events enable row level security;

comment on table public.app_runtime_events is
    'Non-blocking browser and server runtime timing events. Contains no credentials, email, file names, or RFQ content.';
