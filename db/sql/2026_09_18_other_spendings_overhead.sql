-- Add the company-level catch-all monthly overhead used by Company Metrics and
-- deterministic Object Detail overhead allocation.

alter table public.overhead_monthly
    add column if not exists other_spendings_cost bigint not null default 0;

alter table public.overhead_monthly
    drop constraint if exists overhead_monthly_other_spendings_cost_nonnegative;

alter table public.overhead_monthly
    add constraint overhead_monthly_other_spendings_cost_nonnegative
    check (other_spendings_cost >= 0);
