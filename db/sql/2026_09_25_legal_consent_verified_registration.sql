-- 3.11.1 Legal consent and verified registration.
-- Additive only. Applying this migration does not enable the application
-- feature and does not publish a legal document.

begin;

do $$
begin
    if to_regclass('public.companies') is null
       or to_regclass('public.company_members') is null
       or to_regclass('public.company_creation_invites') is null
       or to_regclass('public.company_join_links') is null
       or to_regclass('public.company_member_invites') is null then
        raise exception 'Required company access tables are missing; stop and recheck migration order';
    end if;

    if to_regclass('public.legal_documents') is not null
       or to_regclass('public.legal_document_releases') is not null
       or to_regclass('public.legal_acceptance_events') is not null
       or to_regclass('public.pending_legal_registrations') is not null
       or to_regclass('public.legal_acceptance_company_bindings') is not null
       or to_regprocedure('public.prevent_legal_evidence_mutation()') is not null
       or to_regprocedure('public.prevent_published_legal_document_mutation()') is not null
       or to_regprocedure('public.begin_verified_legal_registration(uuid,uuid,text,text,text,text,text,text,text,text,text,text,uuid,text,text)') is not null
       or to_regprocedure('public.complete_verified_legal_registration(uuid,text)') is not null
       or to_regprocedure('public.record_current_terms_acceptance(uuid,text,text,text,uuid,text,text)') is not null then
        raise exception 'A 3.11.1 legal-consent object already exists; stop and inspect instead of rerunning';
    end if;
end $$;

create table public.legal_documents (
    document_type text not null check (document_type in ('terms', 'privacy')),
    version text not null,
    acceptance_version text not null,
    title text not null,
    effective_at timestamptz not null,
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    public_path text not null check (public_path like '/%'),
    requires_reacceptance boolean not null default false,
    published_at timestamptz,
    created_at timestamptz not null default now(),
    primary key (document_type, version),
    check (document_type = 'terms' or requires_reacceptance = false)
);

create table public.legal_document_releases (
    document_type text primary key check (document_type in ('terms', 'privacy')),
    version text not null,
    updated_at timestamptz not null default now(),
    foreign key (document_type, version)
        references public.legal_documents(document_type, version)
);

create table public.legal_acceptance_events (
    event_id uuid primary key default gen_random_uuid(),
    event_type text not null check (event_type in ('signup', 'terms_reacceptance')),
    user_id uuid not null,
    email text not null,
    organization_id text,
    represented_organization_name text,
    registration_id uuid,
    terms_version text not null,
    terms_acceptance_version text not null,
    terms_sha256 text not null check (terms_sha256 ~ '^[0-9a-f]{64}$'),
    privacy_version text not null,
    privacy_sha256 text not null check (privacy_sha256 ~ '^[0-9a-f]{64}$'),
    checkbox_text text not null,
    accepted_at timestamptz not null default now(),
    ip_address inet,
    user_agent text,
    request_id uuid not null unique,
    created_at timestamptz not null default now(),
    unique (user_id, event_type, terms_acceptance_version)
);

create index legal_acceptance_events_user_idx
    on public.legal_acceptance_events(user_id, accepted_at desc);

create table public.pending_legal_registrations (
    registration_id uuid primary key,
    user_id uuid not null unique,
    email text not null,
    invitation_kind text not null check (invitation_kind in ('create', 'join')),
    invitation_token_hash text not null check (invitation_token_hash ~ '^[0-9a-f]{64}$'),
    represented_organization_name text,
    target_company_id text,
    acceptance_event_id uuid not null unique
        references public.legal_acceptance_events(event_id),
    created_at timestamptz not null default now(),
    completed_at timestamptz,
    completed_company_id text,
    check (
        (invitation_kind = 'create' and represented_organization_name is not null)
        or invitation_kind = 'join'
    ),
    check ((completed_at is null) = (completed_company_id is null))
);

create table public.legal_acceptance_company_bindings (
    acceptance_event_id uuid primary key
        references public.legal_acceptance_events(event_id),
    company_id text not null,
    bound_at timestamptz not null default now()
);

alter table public.legal_documents enable row level security;
alter table public.legal_document_releases enable row level security;
alter table public.legal_acceptance_events enable row level security;
alter table public.pending_legal_registrations enable row level security;
alter table public.legal_acceptance_company_bindings enable row level security;

revoke all on public.legal_documents from public, anon, authenticated;
revoke all on public.legal_document_releases from public, anon, authenticated;
revoke all on public.legal_acceptance_events from public, anon, authenticated;
revoke all on public.pending_legal_registrations from public, anon, authenticated;
revoke all on public.legal_acceptance_company_bindings from public, anon, authenticated;

grant all on public.legal_documents to service_role;
grant all on public.legal_document_releases to service_role;
grant all on public.legal_acceptance_events to service_role;
grant all on public.pending_legal_registrations to service_role;
grant all on public.legal_acceptance_company_bindings to service_role;

create function public.prevent_legal_evidence_mutation()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    raise exception 'Legal evidence is append-only';
end $$;

create function public.prevent_published_legal_document_mutation()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if old.published_at is not null then
        raise exception 'Published legal documents are immutable';
    end if;
    if tg_op = 'DELETE' then
        return old;
    end if;
    return new;
end $$;

create trigger published_legal_documents_immutable
before update or delete on public.legal_documents
for each row execute function public.prevent_published_legal_document_mutation();

create trigger legal_acceptance_events_append_only
before update or delete on public.legal_acceptance_events
for each row execute function public.prevent_legal_evidence_mutation();

create trigger legal_acceptance_bindings_append_only
before update or delete on public.legal_acceptance_company_bindings
for each row execute function public.prevent_legal_evidence_mutation();

create function public.begin_verified_legal_registration(
    p_registration_id uuid,
    p_user_id uuid,
    p_email text,
    p_invitation_kind text,
    p_invitation_token_hash text,
    p_organization_name text,
    p_terms_version text,
    p_terms_acceptance_version text,
    p_terms_sha256 text,
    p_privacy_version text,
    p_privacy_sha256 text,
    p_checkbox_text text,
    p_request_id uuid,
    p_ip_address text,
    p_user_agent text
) returns uuid
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    v_event_id uuid;
    v_target_company_id text;
begin
    if p_invitation_kind not in ('create', 'join') then
        raise exception 'Registration invitation is invalid';
    end if;

    if not exists (
        select 1 from auth.users u
        where u.id = p_user_id
          and lower(u.email) = lower(trim(p_email))
          and u.email_confirmed_at is null
    ) then
        raise exception 'Registration user does not match Auth';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases r
        join public.legal_documents d
          on d.document_type = r.document_type and d.version = r.version
        where r.document_type = 'terms'
          and d.published_at is not null
          and d.version = p_terms_version
          and d.acceptance_version = p_terms_acceptance_version
          and d.content_sha256 = p_terms_sha256
    ) or not exists (
        select 1
        from public.legal_document_releases r
        join public.legal_documents d
          on d.document_type = r.document_type and d.version = r.version
        where r.document_type = 'privacy'
          and d.published_at is not null
          and d.version = p_privacy_version
          and d.content_sha256 = p_privacy_sha256
    ) then
        raise exception 'Published legal documents changed. Reload and try again';
    end if;

    if p_invitation_kind = 'create' then
        if length(trim(coalesce(p_organization_name, ''))) = 0 then
            raise exception 'Company name is required';
        end if;
        if not exists (
            select 1 from public.company_creation_invites i
            where i.token_hash = p_invitation_token_hash and i.used_at is null
        ) then
            raise exception 'Company creation link is invalid or already used';
        end if;
    else
        select i.company_id into v_target_company_id
        from public.company_member_invites i
        where i.token_hash = p_invitation_token_hash
          and i.used_at is null
          and i.expires_at > now();
        if v_target_company_id is null then
            raise exception 'Company invitation is invalid, expired, or already used';
        end if;
    end if;

    select p.acceptance_event_id into v_event_id
    from public.pending_legal_registrations p
    where p.user_id = p_user_id;
    if v_event_id is not null then
        return v_event_id;
    end if;

    insert into public.legal_acceptance_events (
        event_type, user_id, email, organization_id,
        represented_organization_name, registration_id,
        terms_version, terms_acceptance_version, terms_sha256,
        privacy_version, privacy_sha256, checkbox_text,
        ip_address, user_agent, request_id
    ) values (
        'signup', p_user_id, lower(trim(p_email)), v_target_company_id,
        nullif(trim(coalesce(p_organization_name, '')), ''), p_registration_id,
        p_terms_version, p_terms_acceptance_version, p_terms_sha256,
        p_privacy_version, p_privacy_sha256, p_checkbox_text,
        nullif(trim(coalesce(p_ip_address, '')), '')::inet,
        nullif(left(p_user_agent, 1024), ''), p_request_id
    )
    on conflict (user_id, event_type, terms_acceptance_version)
    do nothing
    returning event_id into v_event_id;

    if v_event_id is null then
        select e.event_id into v_event_id
        from public.legal_acceptance_events e
        where e.user_id = p_user_id
          and e.event_type = 'signup'
          and e.terms_acceptance_version = p_terms_acceptance_version;
    end if;

    insert into public.pending_legal_registrations (
        registration_id, user_id, email, invitation_kind,
        invitation_token_hash, represented_organization_name,
        target_company_id, acceptance_event_id
    ) values (
        p_registration_id, p_user_id, lower(trim(p_email)), p_invitation_kind,
        p_invitation_token_hash,
        nullif(trim(coalesce(p_organization_name, '')), ''),
        v_target_company_id, v_event_id
    )
    on conflict (user_id) do nothing;

    return v_event_id;
end $$;

revoke all on function public.begin_verified_legal_registration(
    uuid, uuid, text, text, text, text, text, text, text, text, text, text,
    uuid, text, text
) from public, anon, authenticated;
grant execute on function public.begin_verified_legal_registration(
    uuid, uuid, text, text, text, text, text, text, text, text, text, text,
    uuid, text, text
) to service_role;

create function public.complete_verified_legal_registration(
    p_user_id uuid,
    p_new_company_id text
) returns text
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    v_pending public.pending_legal_registrations%rowtype;
    v_company_id text;
    v_join_token text;
begin
    select * into v_pending
    from public.pending_legal_registrations p
    where p.user_id = p_user_id
    for update;

    if not found then
        raise exception 'Pending registration was not found';
    end if;
    if v_pending.completed_at is not null then
        return v_pending.completed_company_id;
    end if;
    if not exists (
        select 1 from auth.users u
        where u.id = p_user_id and u.email_confirmed_at is not null
    ) then
        raise exception 'Email verification is required';
    end if;
    if exists (select 1 from public.company_members m where m.user_id = p_user_id) then
        raise exception 'User already belongs to a company';
    end if;

    if v_pending.invitation_kind = 'create' then
        if p_new_company_id !~ '^[0-9]{3}$' then
            raise exception 'Company ID is invalid';
        end if;
        select i.join_token into v_join_token
        from public.company_creation_invites i
        where i.token_hash = v_pending.invitation_token_hash
          and i.used_at is null
        for update;
        if v_join_token is null then
            raise exception 'Company creation link is invalid or already used';
        end if;
        v_company_id := p_new_company_id;
        insert into public.companies(company_id, company_name)
        values (v_company_id, v_pending.represented_organization_name);
        insert into public.company_members(user_id, company_id, role)
        values (p_user_id, v_company_id, 'owner');
        insert into public.company_join_links(company_id, join_token)
        values (v_company_id, v_join_token);
        update public.company_creation_invites
        set used_at = now(), created_company_id = v_company_id
        where token_hash = v_pending.invitation_token_hash;
    else
        select i.company_id into v_company_id
        from public.company_member_invites i
        where i.token_hash = v_pending.invitation_token_hash
          and i.used_at is null
          and i.expires_at > now()
        for update;
        if v_company_id is null then
            raise exception 'Company invitation is invalid, expired, or already used';
        end if;
        insert into public.company_members(user_id, company_id, role)
        values (p_user_id, v_company_id, 'member');
        update public.company_member_invites
        set used_at = now(), used_by = p_user_id
        where token_hash = v_pending.invitation_token_hash;
    end if;

    insert into public.legal_acceptance_company_bindings(
        acceptance_event_id, company_id
    ) values (v_pending.acceptance_event_id, v_company_id)
    on conflict (acceptance_event_id) do nothing;

    update public.pending_legal_registrations
    set completed_at = now(), completed_company_id = v_company_id
    where registration_id = v_pending.registration_id;

    return v_company_id;
end $$;

revoke all on function public.complete_verified_legal_registration(uuid, text)
    from public, anon, authenticated;
grant execute on function public.complete_verified_legal_registration(uuid, text)
    to service_role;

create function public.record_current_terms_acceptance(
    p_user_id uuid,
    p_company_id text,
    p_email text,
    p_checkbox_text text,
    p_request_id uuid,
    p_ip_address text,
    p_user_agent text
) returns uuid
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    v_terms public.legal_documents%rowtype;
    v_privacy public.legal_documents%rowtype;
    v_event_id uuid;
begin
    if not exists (
        select 1 from auth.users u
        where u.id = p_user_id
          and u.email_confirmed_at is not null
          and lower(u.email) = lower(trim(p_email))
    ) then
        raise exception 'Verified Auth user does not match';
    end if;
    if not exists (
        select 1 from public.company_members m
        where m.user_id = p_user_id and m.company_id = p_company_id
    ) then
        raise exception 'Company access changed';
    end if;

    select d.* into v_terms
    from public.legal_document_releases r
    join public.legal_documents d
      on d.document_type = r.document_type and d.version = r.version
    where r.document_type = 'terms' and d.published_at is not null;
    select d.* into v_privacy
    from public.legal_document_releases r
    join public.legal_documents d
      on d.document_type = r.document_type and d.version = r.version
    where r.document_type = 'privacy' and d.published_at is not null;
    if v_terms.version is null or v_privacy.version is null then
        raise exception 'Published legal documents are unavailable';
    end if;

    insert into public.legal_acceptance_events (
        event_type, user_id, email, organization_id,
        terms_version, terms_acceptance_version, terms_sha256,
        privacy_version, privacy_sha256, checkbox_text,
        ip_address, user_agent, request_id
    ) values (
        'terms_reacceptance', p_user_id, lower(trim(p_email)), p_company_id,
        v_terms.version, v_terms.acceptance_version, v_terms.content_sha256,
        v_privacy.version, v_privacy.content_sha256, p_checkbox_text,
        nullif(trim(coalesce(p_ip_address, '')), '')::inet,
        nullif(left(p_user_agent, 1024), ''), p_request_id
    )
    on conflict (user_id, event_type, terms_acceptance_version)
    do nothing
    returning event_id into v_event_id;

    if v_event_id is null then
        select e.event_id into v_event_id
        from public.legal_acceptance_events e
        where e.user_id = p_user_id
          and e.terms_acceptance_version = v_terms.acceptance_version
        order by e.accepted_at desc
        limit 1;
    end if;
    return v_event_id;
end $$;

revoke all on function public.record_current_terms_acceptance(
    uuid, text, text, text, uuid, text, text
) from public, anon, authenticated;
grant execute on function public.record_current_terms_acceptance(
    uuid, text, text, text, uuid, text, text
) to service_role;

commit;
