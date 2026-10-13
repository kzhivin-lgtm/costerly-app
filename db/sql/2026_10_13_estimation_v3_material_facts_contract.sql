-- 3.17.4.1: immutable V3 material-only facts.
-- Existing V1/V2 facts remain valid and untouched.

begin;

alter table public.rfq_estimation_object_inputs
    drop constraint if exists rfq_estimation_object_inputs_contract_version_check;

alter table public.rfq_estimation_object_inputs
    add constraint rfq_estimation_object_inputs_contract_version_check
    check (contract_version in ('estimation_input_v2', 'estimation_input_v3'));

alter table public.rfq_estimation_object_fact_results
    drop constraint if exists rfq_estimation_object_fact_results_contract_version_check;

alter table public.rfq_estimation_object_fact_results
    add constraint rfq_estimation_object_fact_results_contract_version_check
    check (contract_version in (
        'estimation_object_facts_v1',
        'estimation_object_facts_v2',
        'estimation_material_facts_v3'
    ));

commit;
