-- Estimation v2 validated Object Facts. Additive only. Existing estimate,
-- Object Detail and legacy Estimation tables remain unchanged.

begin;

create table if not exists public.rfq_estimation_object_fact_results (
    fact_result_id uuid primary key default gen_random_uuid(),
    input_id uuid not null
        references public.rfq_estimation_object_inputs(input_id) on delete cascade,
    agent_usage_event_id uuid not null
        references public.agent_usage_events(id),
    agent_version text not null check (length(trim(agent_version)) between 1 and 200),
    contract_version text not null check (
        contract_version = 'estimation_object_facts_v1'
    ),
    status text not null check (
        status in ('ready', 'review_required', 'failed')
    ),
    facts_payload jsonb not null check (jsonb_typeof(facts_payload) = 'object'),
    created_at timestamptz not null default now(),
    unique (input_id, agent_version)
);

create index if not exists rfq_estimation_object_fact_results_input_idx
    on public.rfq_estimation_object_fact_results (input_id, created_at desc);

alter table public.rfq_estimation_object_fact_results enable row level security;

do $policy$
begin
    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'rfq_estimation_object_fact_results'
          and policyname = 'rfq_estimation_object_fact_results_company_member_read'
    ) then
        execute $sql$
            create policy rfq_estimation_object_fact_results_company_member_read
                on public.rfq_estimation_object_fact_results
                for select to authenticated
                using (exists (
                    select 1
                    from public.rfq_estimation_object_inputs input
                    join public.company_members member
                      on member.company_id = input.company_id
                    where input.input_id = rfq_estimation_object_fact_results.input_id
                      and member.user_id = (select auth.uid())
                ))
        $sql$;
    end if;
end
$policy$;

revoke all on public.rfq_estimation_object_fact_results from anon;
grant select on public.rfq_estimation_object_fact_results to authenticated;
grant all on public.rfq_estimation_object_fact_results to service_role;

commit;
