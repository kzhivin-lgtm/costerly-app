-- Estimation V4.18: bounded diagnostics for rare technical failures.
-- The trace deliberately excludes raw model output and chain-of-thought.

begin;

create table if not exists public.rfq_estimation_failure_traces (
    failure_trace_id uuid primary key default gen_random_uuid(),
    input_id uuid not null
        references public.rfq_estimation_object_inputs(input_id) on delete cascade,
    agent_version text not null check (length(trim(agent_version)) between 1 and 200),
    stage text not null check (stage in (
        'dimension_graph', 'evidence_artifact', 'assembly_agent',
        'structural_composition', 'usage_persistence', 'bom_persistence',
        'material_plan', 'publisher', 'allocation'
    )),
    error_type text not null check (length(trim(error_type)) between 1 and 120),
    error_message text not null check (length(trim(error_message)) between 1 and 400),
    created_at timestamptz not null default now()
);

create index if not exists rfq_estimation_failure_traces_input_idx
    on public.rfq_estimation_failure_traces (input_id, created_at desc);

alter table public.rfq_estimation_failure_traces enable row level security;

do $policy$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public'
          and tablename = 'rfq_estimation_failure_traces'
          and policyname = 'rfq_estimation_failure_traces_company_member_read'
    ) then
        execute $sql$
            create policy rfq_estimation_failure_traces_company_member_read
                on public.rfq_estimation_failure_traces
                for select to authenticated
                using (exists (
                    select 1
                    from public.rfq_estimation_object_inputs input
                    join public.company_members member on member.company_id = input.company_id
                    where input.input_id = rfq_estimation_failure_traces.input_id
                      and member.user_id = (select auth.uid())
                ))
        $sql$;
    end if;
end
$policy$;

revoke all on public.rfq_estimation_failure_traces from anon;
grant select on public.rfq_estimation_failure_traces to authenticated;
grant all on public.rfq_estimation_failure_traces to service_role;

commit;
