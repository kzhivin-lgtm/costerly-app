-- Company access foundation for the MVP.
-- Apply together with the company-auth app release, not to the current legacy UI.
-- The live project already has public.companies(company_id, company_name),
-- plus many billing/contact columns. Reuse that table without rewriting it.
do $$
begin
    if to_regclass('public.companies') is null or not exists (
        select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'companies'
          and column_name = 'company_name'
    ) then
        raise exception 'Existing companies table with company_name is required';
    end if;
end $$;

create table if not exists public.company_members (
    user_id uuid primary key references auth.users(id),
    company_id text not null references public.companies(company_id),
    role text not null check (role in ('owner', 'member')),
    joined_at timestamptz not null default now()
);

create index if not exists company_members_company_id_idx
    on public.company_members(company_id);

-- At most one owner can exist for a company. The creation transaction assigns
-- that role; the reusable join link can only add ordinary members.
create unique index if not exists company_members_one_owner_idx
    on public.company_members(company_id) where role = 'owner';

create table if not exists public.company_creation_invites (
    token_hash text primary key,
    join_token text not null unique,
    label text,
    used_at timestamptz,
    created_company_id text references public.companies(company_id),
    created_at timestamptz not null default now()
);

create table if not exists public.company_join_links (
    company_id text primary key references public.companies(company_id),
    join_token text not null unique,
    created_at timestamptz not null default now()
);

alter table public.company_creation_invites enable row level security;
alter table public.company_join_links enable row level security;
revoke all on public.company_creation_invites, public.company_join_links
    from anon, authenticated;

-- One manually generated platform link creates one company. Creation,
-- membership, join link, and invite consumption happen in one transaction.
create or replace function public.create_company_from_invite(
    p_token_hash text, p_user_id uuid, p_company_id text, p_display_name text
) returns text
language plpgsql security definer set search_path = public
as $$
declare
    v_join_token text;
begin
    if length(trim(p_display_name)) = 0 then
        raise exception 'Company name is required';
    end if;
    select i.join_token into v_join_token
    from public.company_creation_invites i
    where token_hash = p_token_hash and used_at is null
    for update;
    if not found then
        raise exception 'Company creation link is invalid or already used';
    end if;
    if exists (select 1 from public.company_members where user_id = p_user_id) then
        raise exception 'User already belongs to a company';
    end if;
    insert into public.companies(company_id, company_name)
    values (p_company_id, trim(p_display_name));
    insert into public.company_members(user_id, company_id, role)
    values (p_user_id, p_company_id, 'owner');
    insert into public.company_join_links(company_id, join_token)
    values (p_company_id, v_join_token);
    update public.company_creation_invites
    set used_at = now(), created_company_id = p_company_id
    where token_hash = p_token_hash;
    return p_company_id;
end $$;

revoke all on function public.create_company_from_invite(text, uuid, text, text)
    from public, anon, authenticated;
grant execute on function public.create_company_from_invite(text, uuid, text, text)
    to service_role;

-- The company's own link is unlimited and reusable. The server checks the
-- authenticated user before calling this service-role-only function.
create or replace function public.join_company_by_link(
    p_join_token text, p_user_id uuid
) returns text
language plpgsql security definer set search_path = public
as $$
declare
    v_company_id text;
begin
    select l.company_id into v_company_id
    from public.company_join_links l
    where l.join_token = p_join_token;
    if v_company_id is null then
        raise exception 'Company join link is invalid';
    end if;
    if exists (select 1 from public.company_members where user_id = p_user_id) then
        raise exception 'User already belongs to a company';
    end if;

    insert into public.company_members(user_id, company_id, role)
    values (p_user_id, v_company_id, 'member');
    return v_company_id;
end $$;

revoke all on function public.join_company_by_link(text, uuid)
    from public, anon, authenticated;
grant execute on function public.join_company_by_link(text, uuid)
    to service_role;

-- Existing benchmark rows already belong to company 001. Do not reassign
-- them automatically to a company created through a new invitation.

alter table public.companies enable row level security;
alter table public.company_members enable row level security;

drop policy if exists company_members_self_read on public.company_members;
create policy company_members_self_read on public.company_members
    for select to authenticated using (user_id = (select auth.uid()));

drop policy if exists companies_member_read on public.companies;
create policy companies_member_read on public.companies
    for select to authenticated using (
        exists (
            select 1 from public.company_members m
            where m.company_id = companies.company_id
              and m.user_id = (select auth.uid())
        )
    );

grant select on public.companies, public.company_members to authenticated;
revoke all on public.companies, public.company_members from anon;

-- Membership writes are server-only. The service-role client creates a company
-- after a verified sign-in, or later redeems an invite. No client INSERT policy.

-- Existing company-scoped tables may have been created in different SQL
-- iterations. Add one owner policy only when the table and column exist.
do $$
declare
    v_table_name text;
begin
    foreach v_table_name in array array[
        'rfq_runs', 'rfq_detected_objects', 'rfq_estimates',
        'rfq_object_estimates', 'rfq_estimate_lines', 'agent_usage_events',
        'materials', 'labor', 'works', 'company_machines',
        'overhead_settings', 'overhead_monthly', 'estimate_driver_quantities'
    ] loop
        if to_regclass(format('public.%I', v_table_name)) is not null and exists (
            select 1 from information_schema.columns c
            where table_schema = 'public'
              and c.table_name = v_table_name
              and column_name = 'company_id'
        ) then
            execute format('alter table public.%I enable row level security', v_table_name);
            execute format('drop policy if exists company_member_access on public.%I', v_table_name);
            execute format($policy$
                create policy company_member_access on public.%I
                for select to authenticated
                using (exists (
                    select 1 from public.company_members m
                    where m.company_id = %I.company_id
                      and m.user_id = (select auth.uid())
                ))
            $policy$, v_table_name, v_table_name);
        end if;
    end loop;
end $$;

-- The current anonymous price override policy allows anyone to update any
-- estimate. Replace it with ownership through the parent estimate.
drop policy if exists rfq_estimate_pricing_overrides_anon_select
    on public.rfq_estimate_pricing_overrides;
drop policy if exists rfq_estimate_pricing_overrides_anon_insert
    on public.rfq_estimate_pricing_overrides;
drop policy if exists rfq_estimate_pricing_overrides_anon_update
    on public.rfq_estimate_pricing_overrides;

drop policy if exists pricing_overrides_company_member
    on public.rfq_estimate_pricing_overrides;
create policy pricing_overrides_company_member
    on public.rfq_estimate_pricing_overrides
    for all to authenticated
    using (exists (
        select 1 from public.rfq_estimates e
        join public.company_members m on m.company_id = e.company_id
        where e.estimate_id = rfq_estimate_pricing_overrides.estimate_id
          and m.user_id = (select auth.uid())
    ))
    with check (exists (
        select 1 from public.rfq_estimates e
        join public.company_members m on m.company_id = e.company_id
        where e.estimate_id = rfq_estimate_pricing_overrides.estimate_id
          and m.user_id = (select auth.uid())
    ));

revoke all on public.rfq_estimate_pricing_overrides from anon;
grant select, insert, update on public.rfq_estimate_pricing_overrides to authenticated;
grant select on public.rfq_estimates to authenticated;

-- A SECURITY DEFINER view bypassed RLS and disclosed costs via estimate_id.
-- SECURITY INVOKER makes the underlying authenticated table policy effective.
create or replace view public.rfq_object_estimate_progress_public
with (security_invoker = true) as
select estimate_id, object_id, status, progress_percent, progress_label,
       progress_updated_at, quantity, self_cost_ex_vat
from public.rfq_object_estimates;

revoke all on public.rfq_object_estimate_progress_public from anon;
grant select on public.rfq_object_estimate_progress_public to authenticated;
grant select on public.rfq_object_estimates to authenticated;
