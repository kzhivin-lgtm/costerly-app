-- 3.2.1 Labor Costs: private employee compensation records.
-- This table is intentionally separate from public.labor, which is the
-- estimation catalog of labor roles and rates.

create table if not exists public.company_employees (
    employee_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    worker_name text not null check (length(trim(worker_name)) between 1 and 160),
    department text not null check (department in ('management', 'office', 'production')),
    position_code text not null check (length(trim(position_code)) between 1 and 100),
    pay_type text not null check (pay_type in ('monthly_salary', 'hourly_rate')),
    gross_monthly_salary numeric(12, 2),
    gross_hourly_rate numeric(12, 2),
    monthly_hours numeric(7, 2),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint company_employees_pay_details_check check (
        (
            pay_type = 'monthly_salary'
            and gross_monthly_salary > 0
            and gross_hourly_rate is null
            and monthly_hours is null
        )
        or
        (
            pay_type = 'hourly_rate'
            and gross_monthly_salary is null
            and gross_hourly_rate > 0
            and monthly_hours > 0
        )
    )
);

create index if not exists company_employees_company_name_idx
    on public.company_employees(company_id, worker_name);

alter table public.company_employees enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'company_employees'
          and policyname = 'company_employees_owner_select'
    ) then
        create policy company_employees_owner_select on public.company_employees
            for select to authenticated
            using (exists (
                select 1 from public.company_members m
                where m.company_id = company_employees.company_id
                  and m.user_id = (select auth.uid())
                  and m.role = 'owner'
            ));
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'company_employees'
          and policyname = 'company_employees_owner_insert'
    ) then
        create policy company_employees_owner_insert on public.company_employees
            for insert to authenticated
            with check (exists (
                select 1 from public.company_members m
                where m.company_id = company_employees.company_id
                  and m.user_id = (select auth.uid())
                  and m.role = 'owner'
            ));
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'company_employees'
          and policyname = 'company_employees_owner_update'
    ) then
        create policy company_employees_owner_update on public.company_employees
            for update to authenticated
            using (exists (
                select 1 from public.company_members m
                where m.company_id = company_employees.company_id
                  and m.user_id = (select auth.uid())
                  and m.role = 'owner'
            ))
            with check (exists (
                select 1 from public.company_members m
                where m.company_id = company_employees.company_id
                  and m.user_id = (select auth.uid())
                  and m.role = 'owner'
            ));
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'company_employees'
          and policyname = 'company_employees_owner_delete'
    ) then
        create policy company_employees_owner_delete on public.company_employees
            for delete to authenticated
            using (exists (
                select 1 from public.company_members m
                where m.company_id = company_employees.company_id
                  and m.user_id = (select auth.uid())
                  and m.role = 'owner'
            ));
    end if;
end $$;

revoke all on public.company_employees from anon;
grant select, insert, update, delete on public.company_employees to authenticated;
