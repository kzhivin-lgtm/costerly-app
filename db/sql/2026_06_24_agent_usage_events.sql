-- Agent usage ledger for cost-efficiency tracking.
-- Apply manually in Supabase SQL editor before enabling usage writes in production.

create table if not exists public.agent_usage_events (
    id uuid primary key default gen_random_uuid(),
    company_id text not null,
    run_id text,
    file_name text,
    object_id text,
    object_name text,
    agent_name text not null,
    operation text not null,
    model text not null,
    prompt_version text,
    input_tokens integer not null default 0,
    output_tokens integer not null default 0,
    total_tokens integer generated always as (input_tokens + output_tokens) stored,
    input_cost_usd numeric(12, 6),
    output_cost_usd numeric(12, 6),
    total_cost_usd numeric(12, 6),
    currency text not null default 'USD',
    status text not null default 'succeeded',
    error_message text,
    started_at timestamptz,
    finished_at timestamptz,
    raw_usage jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),

    constraint agent_usage_events_status_check
        check (status in ('succeeded', 'failed'))
);

create index if not exists agent_usage_events_run_id_idx
    on public.agent_usage_events (run_id);

create index if not exists agent_usage_events_file_name_idx
    on public.agent_usage_events (file_name);

create index if not exists agent_usage_events_object_id_idx
    on public.agent_usage_events (object_id);

create index if not exists agent_usage_events_object_name_idx
    on public.agent_usage_events (object_name);

create index if not exists agent_usage_events_agent_name_idx
    on public.agent_usage_events (agent_name);

create index if not exists agent_usage_events_created_at_idx
    on public.agent_usage_events (created_at desc);

alter table public.agent_usage_events enable row level security;

-- The Streamlit app writes through SUPABASE_SERVICE_ROLE_KEY, which bypasses RLS.
-- Add read policies later only for authenticated dashboards/admin tools.


-- If the table already existed before human-readable fields were added, run-safe migration.
alter table public.agent_usage_events
    add column if not exists file_name text,
    add column if not exists object_name text;

create index if not exists agent_usage_events_file_name_idx
    on public.agent_usage_events (file_name);

create index if not exists agent_usage_events_object_name_idx
    on public.agent_usage_events (object_name);
