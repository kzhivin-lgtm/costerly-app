-- 3.5.1 Labor Costs: employer-cost factor and retained worker records.
-- Non-destructive migration. Existing compensation records remain active.

alter table public.company_employees
    add column if not exists employment_factor numeric(5, 2) not null default 1.25;

alter table public.company_employees
    add column if not exists deleted_at timestamptz;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'company_employees_employment_factor_check'
          and conrelid = 'public.company_employees'::regclass
    ) then
        alter table public.company_employees
            add constraint company_employees_employment_factor_check
            check (employment_factor > 0);
    end if;
end $$;

create index if not exists company_employees_active_company_name_idx
    on public.company_employees(company_id, worker_name)
    where deleted_at is null;
