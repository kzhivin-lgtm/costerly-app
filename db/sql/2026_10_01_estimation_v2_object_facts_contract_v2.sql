-- Allow the universal Estimation Object Facts contract while retaining
-- immutable v1 results. No rows or payloads are changed.

begin;

alter table public.rfq_estimation_object_fact_results
    drop constraint if exists rfq_estimation_object_fact_results_contract_version_check;

alter table public.rfq_estimation_object_fact_results
    add constraint rfq_estimation_object_fact_results_contract_version_check
    check (contract_version in (
        'estimation_object_facts_v1',
        'estimation_object_facts_v2'
    ));

commit;
