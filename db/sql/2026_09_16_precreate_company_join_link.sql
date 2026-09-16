-- Align the already-installed pilot tables with the two-link creation contract.
-- Future operator commands create both secrets at once. Existing invitations
-- receive a cryptographically random staff secret during this migration.
begin;

alter table public.company_creation_invites
    add column if not exists join_token text;

update public.company_creation_invites
set join_token = rtrim(
    replace(replace(encode(gen_random_bytes(32), 'base64'), '+', '-'), '/', '_'),
    '='
)
where join_token is null;

alter table public.company_creation_invites
    alter column join_token set not null;

create unique index if not exists company_creation_invites_join_token_idx
    on public.company_creation_invites(join_token);

drop function if exists public.create_company_from_invite(text, uuid, text, text, text);

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
    where i.token_hash = p_token_hash and i.used_at is null
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

commit;
