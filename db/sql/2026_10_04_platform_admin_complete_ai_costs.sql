-- Complete AI-cost accounting for the Platform Admin matrix.
--
-- Category is durable telemetry for new Anthropic events. The fallback by
-- agent-name prefix keeps historical Anthropic request versions visible even
-- when an older worker did not write raw_usage.cost_category. Mistral is
-- deliberately excluded until its billing contract is separately approved.

create or replace function public.agent_usage_cost_category(
    p_agent_name text,
    p_raw_usage jsonb
) returns text
language sql
immutable
as $$
    select case
        when lower(coalesce(p_raw_usage ->> 'cost_category', '')) in ('detection', 'estimation', 'price_source')
            then lower(p_raw_usage ->> 'cost_category')
        when lower(coalesce(p_agent_name, '')) = 'price_source'
          or lower(coalesce(p_agent_name, '')) like 'price_source\_%' escape '\'
            then 'price_source'
        when lower(coalesce(p_agent_name, '')) = 'estimation'
          or lower(coalesce(p_agent_name, '')) like 'estimation\_%' escape '\'
            then 'estimation'
        else 'detection'
    end;
$$;

create or replace function public.platform_admin_company_dashboard_v3(
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
        select * from public.platform_admin_company_dashboard_v2(
            p_requesting_user_id,
            p_days
        )
    ),
    metric_window as (
        select case when coalesce(p_days, 0) <= 0 then '-infinity'::timestamptz
                    else now() - make_interval(days => p_days) end as starts_at
    ),
    billable_events as (
        select
            a.company_id,
            a.status,
            a.total_cost_usd,
            public.agent_usage_cost_category(a.agent_name, a.raw_usage) as category
        from public.agent_usage_events a
        where a.created_at >= (select starts_at from metric_window)
          -- Current scope is only Anthropic token-cost accounting. Do not
          -- represent Mistral OCR or internal workers as a priced or unpriced
          -- Anthropic event.
          and lower(coalesce(a.model, '')) like 'claude-%'
    ),
    costs as (
        select
            company_id,
            count(*) filter (where category = 'detection')::bigint as detection_runs,
            coalesce(sum(total_cost_usd) filter (where category = 'detection'), 0)::numeric as detection_cost_usd,
            count(*) filter (where category = 'detection' and total_cost_usd is null)::bigint as detection_unpriced_events,
            count(*) filter (where category = 'estimation')::bigint as estimation_calls,
            coalesce(sum(total_cost_usd) filter (where category = 'estimation'), 0)::numeric as estimation_cost_usd,
            count(*) filter (where category = 'estimation' and total_cost_usd is null)::bigint as estimation_unpriced_events,
            count(*) filter (where category = 'price_source')::bigint as price_source_runs,
            coalesce(sum(total_cost_usd) filter (where category = 'price_source'), 0)::numeric as price_source_cost_usd,
            count(*) filter (where category = 'price_source' and total_cost_usd is null)::bigint as price_source_unpriced_events,
            coalesce(sum(total_cost_usd), 0)::numeric as total_ai_cost_usd,
            count(*) filter (where total_cost_usd is null)::bigint as total_unpriced_events,
            count(*) filter (where status = 'failed')::bigint as failed_agent_events
        from billable_events
        group by company_id
    )
    select
        d.company_id, d.company_name, d.account_stage, d.users_count,
        d.active_days_7, d.active_days_30, d.files_uploaded, d.files_reuploaded,
        coalesce(c.detection_runs, 0)::bigint,
        coalesce(c.detection_cost_usd, 0)::numeric,
        coalesce(c.detection_unpriced_events, 0)::bigint,
        coalesce(c.estimation_calls, 0)::bigint,
        coalesce(c.estimation_cost_usd, 0)::numeric,
        coalesce(c.estimation_unpriced_events, 0)::bigint,
        coalesce(c.price_source_runs, 0)::bigint,
        coalesce(c.price_source_cost_usd, 0)::numeric,
        coalesce(c.price_source_unpriced_events, 0)::bigint,
        d.pdfs_generated,
        coalesce(c.total_ai_cost_usd, 0)::numeric,
        coalesce(c.total_unpriced_events, 0)::bigint,
        coalesce(c.failed_agent_events, 0)::bigint
    from dashboard d
    left join costs c on c.company_id = d.company_id;
$$;

revoke all on function public.platform_admin_company_dashboard_v3(uuid, integer)
    from public, anon, authenticated;
grant execute on function public.platform_admin_company_dashboard_v3(uuid, integer)
    to service_role;

comment on function public.platform_admin_company_dashboard_v3(uuid, integer) is
    'Complete paid AI cost matrix, grouped by durable category with historical prefix fallback.';
