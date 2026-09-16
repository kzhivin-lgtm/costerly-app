-- Stage 2: add only the two invitation RPCs. No existing RFQ policy changes.
-- Preflight rejects unexpected existing functions before any DDL.
begin;

do $$
begin
    if to_regclass('public.company_members') is null
       or to_regclass('public.company_creation_invites') is null
       or to_regclass('public.company_join_links') is null then
        raise exception 'Run stage 1 before invitation RPCs';
    end if;
    if to_regprocedure('public.create_company_from_invite(text,uuid,text,text)') is not null
       or to_regprocedure('public.join_company_by_link(text,uuid)') is not null then
        raise exception 'An invitation RPC already exists; stop and recheck';
    end if;
end $$;

create function public.create_company_from_invite(
    p_token_hash text, p_user_id uuid, p_company_id text, p_display_name text
) returns text
language plpgsql security invoker set search_path = pg_catalog, public
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

create function public.join_company_by_link(
    p_join_token text, p_user_id uuid
) returns text
language plpgsql security invoker set search_path = pg_catalog, public
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

commit;
