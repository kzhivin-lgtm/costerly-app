-- Durable, opaque browser routes for RFQ workflow screens.
-- Tokens reduce URL noise only. Server-side company checks remain mandatory.

create table if not exists public.rfq_workflow_routes (
    route_key text primary key,
    route_token text not null unique,
    company_id text not null,
    scope text not null check (scope in ('run', 'estimate', 'object')),
    run_id text not null references public.rfq_runs(run_id) on delete cascade,
    estimate_id text references public.rfq_estimates(estimate_id) on delete cascade,
    object_id text,
    created_at timestamptz not null default now(),
    constraint rfq_workflow_routes_scope_context_check check (
        (scope = 'run' and estimate_id is null and object_id is null)
        or (scope = 'estimate' and estimate_id is not null and object_id is null)
        or (scope = 'object' and estimate_id is not null and object_id is not null)
    )
);

create index if not exists rfq_workflow_routes_company_token_idx
    on public.rfq_workflow_routes(company_id, route_token);

alter table public.rfq_workflow_routes enable row level security;
