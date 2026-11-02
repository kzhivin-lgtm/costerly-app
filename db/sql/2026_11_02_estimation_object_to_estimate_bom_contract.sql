-- Add Object-to-Estimate V1 and its deterministic approximate BOM result.
-- Existing immutable fact results remain unchanged.

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
        'estimation_material_facts_v4_2',
        'estimation_object_to_estimate_v1',
        'estimation_approximate_bom_v1'
    ));

commit;
