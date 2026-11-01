-- 3.17.4.2: permit immutable Estimation V4.2 material facts.
-- Additive contract extension only. Existing V1 through V4.1 results remain valid.

begin;

alter table public.rfq_estimation_object_fact_results
    drop constraint if exists rfq_estimation_object_fact_results_contract_version_check;

alter table public.rfq_estimation_object_fact_results
    add constraint rfq_estimation_object_fact_results_contract_version_check
    check (contract_version in (
        'estimation_object_facts_v1',
        'estimation_object_facts_v2',
        'estimation_material_facts_v3',
        'estimation_material_facts_v4_1',
        'estimation_material_facts_v4_2'
    ));

commit;
