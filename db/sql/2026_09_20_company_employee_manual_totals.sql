-- 3.5.2 Labor Costs revision: persist editable calculated totals.
-- Non-destructive migration. Existing employee rows are retained and backfilled.

alter table public.company_employees
    add column if not exists total_hourly_cost numeric(12, 2);

alter table public.company_employees
    add column if not exists total_monthly_cost numeric(12, 2);

update public.company_employees
set
    total_hourly_cost = case
        when pay_type = 'hourly_rate'
            then round(gross_hourly_rate * employment_factor, 2)
        else null
    end,
    total_monthly_cost = case
        when pay_type = 'hourly_rate'
            then round(gross_hourly_rate * monthly_hours * employment_factor, 2)
        else round(gross_monthly_salary * employment_factor, 2)
    end
where total_monthly_cost is null;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'company_employees_total_costs_check'
          and conrelid = 'public.company_employees'::regclass
    ) then
        alter table public.company_employees
            add constraint company_employees_total_costs_check
            check (
                total_monthly_cost is null
                or (
                    total_monthly_cost > 0
                    and (
                        (pay_type = 'monthly_salary' and total_hourly_cost is null)
                        or
                        (pay_type = 'hourly_rate' and total_hourly_cost > 0)
                    )
                )
            );
    end if;
end $$;
