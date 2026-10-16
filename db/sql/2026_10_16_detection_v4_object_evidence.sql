-- Detection V4 stores the only non-legacy object-state decision: whether an
-- evidence-backed physical quantity needs human review. Evidence regions and
-- the UI preview live in evidence_page_refs, so they cannot be confused with
-- Estimation facts.

alter table public.rfq_detected_objects
    add column if not exists review_required boolean not null default false;

alter table public.rfq_estimation_object_inputs
    drop constraint if exists rfq_estimation_object_inputs_contract_version_check;

alter table public.rfq_estimation_object_inputs
    add constraint rfq_estimation_object_inputs_contract_version_check
    check (contract_version in ('estimation_input_v2', 'estimation_input_v3', 'estimation_input_v4'));
