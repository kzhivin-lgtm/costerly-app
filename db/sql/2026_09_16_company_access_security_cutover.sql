-- Audited production cutover based on the live 2026-09-16 policy snapshot.
-- Changes permissions and RLS policies only. It never mutates application rows.
begin;

alter table public.companies enable row level security;
alter table public.company_members enable row level security;

drop policy if exists company_members_self_read on public.company_members;
create policy company_members_self_read on public.company_members
    for select to authenticated
    using (user_id = (select auth.uid()));

drop policy if exists companies_member_read on public.companies;
create policy companies_member_read on public.companies
    for select to authenticated
    using (exists (
        select 1 from public.company_members m
        where m.company_id = companies.company_id
          and m.user_id = (select auth.uid())
    ));

do $$
declare
    v_table_name text;
begin
    foreach v_table_name in array array[
        'rfq_runs', 'rfq_detected_objects', 'rfq_estimates',
        'rfq_object_estimates', 'rfq_estimate_lines', 'agent_usage_events'
    ] loop
        execute format('alter table public.%I enable row level security', v_table_name);
        execute format('drop policy if exists company_member_read on public.%I', v_table_name);
        execute format($policy$
            create policy company_member_read on public.%I
            for select to authenticated
            using (exists (
                select 1 from public.company_members m
                where m.company_id = %I.company_id
                  and m.user_id = (select auth.uid())
            ))
        $policy$, v_table_name, v_table_name);
    end loop;
end $$;

drop policy if exists rfq_estimate_pricing_overrides_anon_select
    on public.rfq_estimate_pricing_overrides;
drop policy if exists rfq_estimate_pricing_overrides_anon_insert
    on public.rfq_estimate_pricing_overrides;
drop policy if exists rfq_estimate_pricing_overrides_anon_update
    on public.rfq_estimate_pricing_overrides;

drop policy if exists pricing_overrides_company_member
    on public.rfq_estimate_pricing_overrides;
create policy pricing_overrides_company_member
    on public.rfq_estimate_pricing_overrides
    for all to authenticated
    using (exists (
        select 1 from public.rfq_estimates e
        join public.company_members m on m.company_id = e.company_id
        where e.estimate_id = rfq_estimate_pricing_overrides.estimate_id
          and m.user_id = (select auth.uid())
    ))
    with check (exists (
        select 1 from public.rfq_estimates e
        join public.company_members m on m.company_id = e.company_id
        where e.estimate_id = rfq_estimate_pricing_overrides.estimate_id
          and m.user_id = (select auth.uid())
    ));

create or replace view public.rfq_object_estimate_progress_public
with (security_invoker = true) as
select estimate_id, object_id, status, progress_percent, progress_label,
       progress_updated_at, quantity, self_cost_ex_vat
from public.rfq_object_estimates;

revoke all privileges on table
    public.companies, public.company_members, public.rfq_runs,
    public.rfq_detected_objects, public.rfq_estimates,
    public.rfq_object_estimates, public.rfq_estimate_lines,
    public.agent_usage_events, public.rfq_estimate_pricing_overrides,
    public.rfq_object_estimate_progress_public
from anon, authenticated;

grant select on table
    public.companies, public.company_members, public.rfq_estimates,
    public.rfq_object_estimates, public.rfq_object_estimate_progress_public
to authenticated;

grant select, insert, update
    on table public.rfq_estimate_pricing_overrides
    to authenticated;

commit;
