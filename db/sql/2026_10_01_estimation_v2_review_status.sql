-- 3.15.8: a valid estimate can require user review without being a failure.

begin;

alter table public.rfq_object_estimates
    drop constraint if exists rfq_object_estimates_status_check,
    add constraint rfq_object_estimates_status_check check (
        status in ('pending', 'running', 'review_required', 'completed', 'failed')
    );

commit;
