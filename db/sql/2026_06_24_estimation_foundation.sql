-- Estimation foundation tables.
-- Detection only finds objects. Estimation creates object-level work items,
-- then later stores agent-produced material/labor/overhead lines separately
-- from deterministic calculation totals.

create table if not exists public.rfq_estimates (
    estimate_id text primary key,
    run_id text not null references public.rfq_runs(run_id) on delete cascade,
    company_id text not null,
    status text not null default 'pending',
    currency text not null default 'ILS',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint rfq_estimates_status_check check (status in ('pending', 'running', 'completed', 'failed'))
);

create index if not exists rfq_estimates_run_id_idx
    on public.rfq_estimates(run_id);

create table if not exists public.rfq_object_estimates (
    estimate_id text not null references public.rfq_estimates(estimate_id) on delete cascade,
    run_id text not null references public.rfq_runs(run_id) on delete cascade,
    company_id text not null,
    object_id text not null,
    object_name text not null,
    quantity numeric not null default 1,
    status text not null default 'pending',
    self_cost_ex_vat numeric(14, 2),
    vat_amount numeric(14, 2),
    self_cost_total numeric(14, 2),
    approved boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (estimate_id, object_id),
    constraint rfq_object_estimates_status_check check (status in ('pending', 'running', 'completed', 'failed'))
);

create index if not exists rfq_object_estimates_run_id_idx
    on public.rfq_object_estimates(run_id);

create table if not exists public.rfq_estimate_lines (
    estimate_id text not null references public.rfq_estimates(estimate_id) on delete cascade,
    object_id text not null,
    line_id text not null,
    company_id text not null,
    section text not null,
    group_name text not null,
    item_name text not null,
    unit text,
    unit_cost numeric(14, 4),
    quantity numeric(14, 4),
    role text,
    hours numeric(14, 4),
    rate numeric(14, 4),
    monthly_cost numeric(14, 4),
    allocation_basis text,
    cost numeric(14, 2),
    source text not null default 'estimation_agent',
    sort_order integer not null default 0,
    raw_agent_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (estimate_id, line_id),
    constraint rfq_estimate_lines_section_check check (section in ('material', 'labor', 'overhead'))
);

create index if not exists rfq_estimate_lines_object_idx
    on public.rfq_estimate_lines(estimate_id, object_id, section, sort_order);

alter table public.rfq_estimates enable row level security;
alter table public.rfq_object_estimates enable row level security;
alter table public.rfq_estimate_lines enable row level security;
