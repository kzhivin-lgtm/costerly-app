-- Platform Admin dashboard foundation.
-- Apply before deploying the application code that reads the Admin screen.
-- Customer users receive no direct access to these tables or the aggregate RPC.

create table if not exists public.platform_staff (
    user_id uuid primary key references auth.users(id) on delete cascade,
    role text not null check (role in ('platform_admin', 'platform_viewer')),
    active boolean not null default true,
    created_by uuid references auth.users(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.platform_company_accounts (
    company_id text primary key references public.companies(company_id) on delete cascade,
    account_stage text not null default 'pilot'
        check (account_stage in ('test', 'pilot', 'paid')),
    internal_note text,
    updated_by uuid references auth.users(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.product_usage_events (
    event_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id) on delete cascade,
    user_id uuid references auth.users(id) on delete set null,
    event_name text not null check (event_name in (
        'authenticated_daily_activity',
        'rfq_uploaded',
        'detection_completed',
        'estimation_started',
        'estimation_completed',
        'price_source_processed',
        'proposal_pdf_generated'
    )),
    entity_fingerprint text,
    is_repeat boolean not null default false,
    occurred_at timestamptz not null default now(),
    activity_date date not null default current_date,
    metadata jsonb not null default '{}'::jsonb,
    constraint product_usage_events_metadata_object_check
        check (jsonb_typeof(metadata) = 'object')
);

create table if not exists public.platform_admin_audit_events (
    audit_id uuid primary key default gen_random_uuid(),
    platform_user_id uuid not null references auth.users(id) on delete cascade,
    company_id text references public.companies(company_id) on delete set null,
    action text not null,
    occurred_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb,
    constraint platform_admin_audit_metadata_object_check
        check (jsonb_typeof(metadata) = 'object')
);

create index if not exists platform_staff_active_idx
    on public.platform_staff (active, role);
create index if not exists product_usage_events_company_time_idx
    on public.product_usage_events (company_id, occurred_at desc);
create index if not exists product_usage_events_company_name_time_idx
    on public.product_usage_events (company_id, event_name, occurred_at desc);
create index if not exists product_usage_events_repeat_idx
    on public.product_usage_events (company_id, event_name, entity_fingerprint)
    where entity_fingerprint is not null;
create unique index if not exists product_usage_events_daily_activity_idx
    on public.product_usage_events (company_id, user_id, event_name, activity_date)
    where event_name = 'authenticated_daily_activity' and user_id is not null;
create index if not exists platform_admin_audit_recent_idx
    on public.platform_admin_audit_events (platform_user_id, occurred_at desc);
create index if not exists agent_usage_events_company_agent_time_idx
    on public.agent_usage_events (company_id, agent_name, created_at desc);

alter table public.platform_staff enable row level security;
alter table public.platform_company_accounts enable row level security;
alter table public.product_usage_events enable row level security;
alter table public.platform_admin_audit_events enable row level security;

revoke all on public.platform_staff from public, anon, authenticated;
revoke all on public.platform_company_accounts from public, anon, authenticated;
revoke all on public.product_usage_events from public, anon, authenticated;
revoke all on public.platform_admin_audit_events from public, anon, authenticated;
grant all on public.platform_staff to service_role;
grant all on public.platform_company_accounts to service_role;
grant all on public.product_usage_events to service_role;
grant all on public.platform_admin_audit_events to service_role;

create or replace function public.record_product_usage_event(
    p_company_id text,
    p_user_id uuid,
    p_event_name text,
    p_entity_fingerprint text default null,
    p_metadata jsonb default '{}'::jsonb
) returns table(event_id uuid, is_repeat boolean)
language plpgsql
security definer
set search_path = public
as $$
declare
    v_repeat boolean := false;
    v_event_id uuid;
begin
    if p_user_id is not null and not exists (
        select 1 from public.company_members m
        where m.user_id = p_user_id and m.company_id = p_company_id
    ) then
        raise exception 'Product event user is not a member of this company';
    end if;

    if p_event_name = 'authenticated_daily_activity' then
        insert into public.product_usage_events (
            company_id, user_id, event_name, metadata
        ) values (
            p_company_id, p_user_id, p_event_name, coalesce(p_metadata, '{}'::jsonb)
        )
        on conflict (company_id, user_id, event_name, activity_date)
            where event_name = 'authenticated_daily_activity' and user_id is not null
        do update set occurred_at = excluded.occurred_at
        returning product_usage_events.event_id into v_event_id;
    else
        if p_event_name = 'rfq_uploaded' and p_entity_fingerprint is not null then
            select exists (
                select 1 from public.product_usage_events e
                where e.company_id = p_company_id
                  and e.event_name = 'rfq_uploaded'
                  and e.entity_fingerprint = p_entity_fingerprint
            ) into v_repeat;
        end if;

        insert into public.product_usage_events (
            company_id, user_id, event_name, entity_fingerprint, is_repeat, metadata
        ) values (
            p_company_id,
            p_user_id,
            p_event_name,
            p_entity_fingerprint,
            v_repeat,
            coalesce(p_metadata, '{}'::jsonb)
        ) returning product_usage_events.event_id into v_event_id;
    end if;

    return query select v_event_id, v_repeat;
end;
$$;

revoke all on function public.record_product_usage_event(text, uuid, text, text, jsonb)
    from public, anon, authenticated;
grant execute on function public.record_product_usage_event(text, uuid, text, text, jsonb)
    to service_role;

create or replace function public.platform_admin_company_dashboard(
    p_requesting_user_id uuid,
    p_days integer default 30
) returns table (
    company_id text,
    company_name text,
    account_stage text,
    users_count bigint,
    active_days_7 bigint,
    active_days_30 bigint,
    files_uploaded bigint,
    files_reuploaded bigint,
    detection_runs bigint,
    detection_cost_usd numeric,
    detection_unpriced_events bigint,
    estimation_calls bigint,
    estimation_cost_usd numeric,
    estimation_unpriced_events bigint,
    price_source_runs bigint,
    price_source_cost_usd numeric,
    price_source_unpriced_events bigint,
    pdfs_generated bigint,
    total_ai_cost_usd numeric,
    total_unpriced_events bigint,
    failed_agent_events bigint
)
language plpgsql
security definer
set search_path = public
as $$
begin
    if coalesce(p_days, 30) not in (0, 7, 30, 90) then
        raise exception 'Unsupported Admin dashboard period' using errcode = '22023';
    end if;

    if not exists (
        select 1 from public.platform_staff s
        where s.user_id = p_requesting_user_id
          and s.active
          and s.role in ('platform_admin', 'platform_viewer')
    ) then
        raise exception 'Platform Admin access is required' using errcode = '42501';
    end if;

    return query
    with metric_window as (
        select case
            when coalesce(p_days, 30) <= 0 then '-infinity'::timestamptz
            else now() - make_interval(days => p_days)
        end as starts_at
    ),
    member_counts as (
        select m.company_id, count(*)::bigint as users_count
        from public.company_members m
        group by m.company_id
    ),
    activity as (
        select
            e.company_id,
            count(distinct e.activity_date) filter (
                where e.event_name = 'authenticated_daily_activity'
                  and e.occurred_at >= now() - interval '7 days'
            )::bigint as active_days_7,
            count(distinct e.activity_date) filter (
                where e.event_name = 'authenticated_daily_activity'
                  and e.occurred_at >= now() - interval '30 days'
            )::bigint as active_days_30,
            count(*) filter (
                where e.event_name = 'rfq_uploaded'
                  and e.occurred_at >= (select starts_at from metric_window)
            )::bigint as files_uploaded,
            min(e.occurred_at) filter (
                where e.event_name = 'rfq_uploaded'
            ) as first_recorded_upload_at,
            count(*) filter (
                where e.event_name = 'rfq_uploaded'
                  and e.is_repeat
                  and e.occurred_at >= (select starts_at from metric_window)
            )::bigint as files_reuploaded,
            count(*) filter (
                where e.event_name = 'proposal_pdf_generated'
                  and e.occurred_at >= (select starts_at from metric_window)
            )::bigint as pdfs_generated
        from public.product_usage_events e
        group by e.company_id
    ),
    rfq_runs_normalized as (
        select
            r.company_id,
            case
                when r.created_at ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}[ T]'
                    then r.created_at::timestamptz
                else null
            end as created_at_ts
        from public.rfq_runs r
    ),
    file_counts as (
        select r.company_id, count(*)::bigint as legacy_files_uploaded
        from rfq_runs_normalized r
        left join activity ac on ac.company_id = r.company_id
        where (
              coalesce(p_days, 30) <= 0
              or r.created_at_ts >= (select starts_at from metric_window)
          )
          and (
              ac.first_recorded_upload_at is null
              or r.created_at_ts is null
              or r.created_at_ts < ac.first_recorded_upload_at
          )
        group by r.company_id
    ),
    agent_counts as (
        select
            a.company_id,
            count(distinct a.run_id) filter (
                where a.agent_name = 'detection'
            )::bigint as detection_runs,
            coalesce(sum(a.total_cost_usd) filter (
                where a.agent_name in ('ocr', 'detection', 'naming')
            ), 0)::numeric as detection_cost_usd,
            count(*) filter (
                where a.agent_name in ('ocr', 'detection', 'naming')
                  and a.total_cost_usd is null
            )::bigint as detection_unpriced_events,
            count(*) filter (
                where a.agent_name = 'estimation'
            )::bigint as estimation_calls,
            coalesce(sum(a.total_cost_usd) filter (
                where a.agent_name = 'estimation'
            ), 0)::numeric as estimation_cost_usd,
            count(*) filter (
                where a.agent_name = 'estimation'
                  and a.total_cost_usd is null
            )::bigint as estimation_unpriced_events,
            count(*) filter (
                where a.agent_name = 'price_source'
            )::bigint as price_source_runs,
            coalesce(sum(a.total_cost_usd) filter (
                where a.agent_name = 'price_source'
            ), 0)::numeric as price_source_cost_usd,
            count(*) filter (
                where a.agent_name = 'price_source'
                  and a.total_cost_usd is null
            )::bigint as price_source_unpriced_events,
            coalesce(sum(a.total_cost_usd) filter (
                where a.agent_name in ('ocr', 'detection', 'naming', 'estimation', 'price_source')
            ), 0)::numeric as total_ai_cost_usd,
            count(*) filter (
                where a.agent_name in ('ocr', 'detection', 'naming', 'estimation', 'price_source')
                  and a.total_cost_usd is null
            )::bigint as total_unpriced_events,
            count(*) filter (
                where a.agent_name in ('ocr', 'detection', 'naming', 'estimation', 'price_source')
                  and a.status = 'failed'
            )::bigint as failed_agent_events
        from public.agent_usage_events a
        where a.created_at >= (select starts_at from metric_window)
        group by a.company_id
    )
    select
        c.company_id::text,
        c.company_name::text,
        coalesce(p.account_stage, 'pilot')::text,
        coalesce(m.users_count, 0)::bigint,
        coalesce(ac.active_days_7, 0)::bigint,
        coalesce(ac.active_days_30, 0)::bigint,
        (
            coalesce(ac.files_uploaded, 0)
            + coalesce(f.legacy_files_uploaded, 0)
        )::bigint,
        coalesce(ac.files_reuploaded, 0)::bigint,
        coalesce(ag.detection_runs, 0)::bigint,
        coalesce(ag.detection_cost_usd, 0)::numeric,
        coalesce(ag.detection_unpriced_events, 0)::bigint,
        coalesce(ag.estimation_calls, 0)::bigint,
        coalesce(ag.estimation_cost_usd, 0)::numeric,
        coalesce(ag.estimation_unpriced_events, 0)::bigint,
        coalesce(ag.price_source_runs, 0)::bigint,
        coalesce(ag.price_source_cost_usd, 0)::numeric,
        coalesce(ag.price_source_unpriced_events, 0)::bigint,
        coalesce(ac.pdfs_generated, 0)::bigint,
        coalesce(ag.total_ai_cost_usd, 0)::numeric,
        coalesce(ag.total_unpriced_events, 0)::bigint,
        coalesce(ag.failed_agent_events, 0)::bigint
    from public.companies c
    left join public.platform_company_accounts p on p.company_id = c.company_id
    left join member_counts m on m.company_id = c.company_id
    left join activity ac on ac.company_id = c.company_id
    left join file_counts f on f.company_id = c.company_id
    left join agent_counts ag on ag.company_id = c.company_id
    order by lower(c.company_name), c.company_id;
end;
$$;

revoke all on function public.platform_admin_company_dashboard(uuid, integer)
    from public, anon, authenticated;
grant execute on function public.platform_admin_company_dashboard(uuid, integer)
    to service_role;

comment on table public.platform_staff is
    'Explicit cross-company platform access. This is independent of company membership roles.';
comment on table public.product_usage_events is
    'Content-free product activity events for company-level adoption metrics.';
comment on function public.platform_admin_company_dashboard(uuid, integer) is
    'Read-only cross-company summary guarded by active platform_staff membership.';
