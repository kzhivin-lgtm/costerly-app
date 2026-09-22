-- One-use, 24-hour company member invitations and owner-controlled access removal.
-- Apply before deploying the matching app revision. The legacy
-- company_join_links table remains untouched as a rollback surface, but the
-- app no longer reads or creates links from it.

create table if not exists public.company_member_invites (
    token_hash text primary key check (length(token_hash) = 64),
    company_id text not null references public.companies(company_id),
    created_by uuid not null references auth.users(id),
    created_at timestamptz not null default now(),
    expires_at timestamptz not null,
    used_at timestamptz,
    used_by uuid references auth.users(id),
    check (expires_at > created_at),
    check (expires_at <= created_at + interval '24 hours'),
    check ((used_at is null) = (used_by is null))
);

create index if not exists company_member_invites_company_id_idx
    on public.company_member_invites(company_id, created_at desc);

alter table public.company_member_invites enable row level security;
revoke all on public.company_member_invites from public, anon, authenticated;

create or replace function public.join_company_by_one_time_invite(
    p_token_hash text, p_user_id uuid
) returns text
language plpgsql security definer set search_path = public
as $$
declare
    v_company_id text;
begin
    select i.company_id into v_company_id
    from public.company_member_invites i
    where i.token_hash = p_token_hash
      and i.used_at is null
      and i.expires_at > now()
    for update;

    if v_company_id is null then
        raise exception 'Company invitation is invalid, expired, or already used';
    end if;

    if exists (select 1 from public.company_members where user_id = p_user_id) then
        raise exception 'User already belongs to a company';
    end if;

    insert into public.company_members(user_id, company_id, role)
    values (p_user_id, v_company_id, 'member');

    update public.company_member_invites
    set used_at = now(), used_by = p_user_id
    where token_hash = p_token_hash;

    return v_company_id;
end $$;

revoke all on function public.join_company_by_one_time_invite(text, uuid)
    from public, anon, authenticated;
grant execute on function public.join_company_by_one_time_invite(text, uuid)
    to service_role;

create or replace function public.remove_company_member_access(
    p_company_id text, p_owner_id uuid, p_member_id uuid
) returns uuid
language plpgsql security definer set search_path = public
as $$
begin
    if not exists (
        select 1 from public.company_members
        where user_id = p_owner_id
          and company_id = p_company_id
          and role = 'owner'
    ) then
        raise exception 'Only the company owner can remove access';
    end if;

    if p_member_id = p_owner_id or exists (
        select 1 from public.company_members
        where user_id = p_member_id
          and company_id = p_company_id
          and role = 'owner'
    ) then
        raise exception 'The company owner cannot be removed';
    end if;

    delete from public.company_members
    where user_id = p_member_id
      and company_id = p_company_id
      and role = 'member';

    if not found then
        raise exception 'Company member was not found';
    end if;

    return p_member_id;
end $$;

revoke all on function public.remove_company_member_access(text, uuid, uuid)
    from public, anon, authenticated;
grant execute on function public.remove_company_member_access(text, uuid, uuid)
    to service_role;
