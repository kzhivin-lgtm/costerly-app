-- Platform Admin session metrics revision.
-- Apply after 2026_09_27_platform_admin_dashboard.sql.

alter table public.product_usage_events
    drop constraint if exists product_usage_events_event_name_check;

alter table public.product_usage_events
    add constraint product_usage_events_event_name_check
    check (event_name in (
        'authenticated_daily_activity',
        'authenticated_session_started',
        'rfq_uploaded',
        'detection_completed',
        'estimation_started',
        'estimation_completed',
        'price_source_processed',
        'proposal_pdf_generated'
    ));

create unique index if not exists product_usage_events_session_idx
    on public.product_usage_events (
        company_id,
        user_id,
        event_name,
        entity_fingerprint
    )
    where event_name = 'authenticated_session_started'
      and user_id is not null
      and entity_fingerprint is not null;

create or replace function public.platform_admin_company_dashboard_v2(
    p_requesting_user_id uuid,
    p_days integer default 0
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
language sql
security definer
set search_path = public
as $$
    with dashboard as (
        select *
        from public.platform_admin_company_dashboard(
            p_requesting_user_id,
            p_days
        )
    ),
    sessions as (
        select
            e.company_id,
            count(*) filter (
                where e.occurred_at >= now() - interval '7 days'
            )::bigint as sessions_7,
            count(*) filter (
                where e.occurred_at >= now() - interval '30 days'
            )::bigint as sessions_30
        from public.product_usage_events e
        where e.event_name = 'authenticated_session_started'
        group by e.company_id
    )
    select
        d.company_id,
        d.company_name,
        d.account_stage,
        d.users_count,
        coalesce(s.sessions_7, 0)::bigint,
        coalesce(s.sessions_30, 0)::bigint,
        d.files_uploaded,
        d.files_reuploaded,
        d.detection_runs,
        d.detection_cost_usd,
        d.detection_unpriced_events,
        d.estimation_calls,
        d.estimation_cost_usd,
        d.estimation_unpriced_events,
        d.price_source_runs,
        d.price_source_cost_usd,
        d.price_source_unpriced_events,
        d.pdfs_generated,
        d.total_ai_cost_usd,
        d.total_unpriced_events,
        d.failed_agent_events
    from dashboard d
    left join sessions s on s.company_id = d.company_id;
$$;

revoke all
on function public.platform_admin_company_dashboard_v2(uuid, integer)
from public, anon, authenticated;

grant execute
on function public.platform_admin_company_dashboard_v2(uuid, integer)
to service_role;

comment on function public.platform_admin_company_dashboard_v2(uuid, integer) is
    'Platform Admin company matrix with rolling authenticated session counts.';
