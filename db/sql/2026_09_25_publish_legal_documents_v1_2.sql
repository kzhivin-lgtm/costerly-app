-- Publish the material Terms 1.2 revision for task 3.11.1.
-- Terms 1.2 advances acceptance_version from 2 to 3.
-- Privacy remains independently published at version 1.1.

begin;

do $$
begin
    if exists (
        select 1
        from public.legal_documents
        where document_type = 'terms' and version = '1.2'
    ) then
        raise exception 'Terms version 1.2 already exists; inspect before publishing';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'terms' and version = '1.1'
    ) then
        raise exception 'Expected current Terms release 1.1 is missing; inspect before publishing';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'privacy' and version = '1.1'
    ) then
        raise exception 'Expected current Privacy release 1.1 is missing; inspect before publishing';
    end if;
end $$;

insert into public.legal_documents (
    document_type,
    version,
    acceptance_version,
    title,
    effective_at,
    content_sha256,
    public_path,
    requires_reacceptance,
    published_at
) values (
    'terms',
    '1.2',
    '3',
    'Terms of Service',
    '2026-09-25T00:00:00Z',
    'aadc32bc8cf8c2b30d8d8d7b4e721ee5864fd39d6c61ca54ddee30e6b00a5ec3',
    '/terms',
    true,
    now()
);

update public.legal_document_releases
set version = '1.2', updated_at = now()
where document_type = 'terms' and version = '1.1';

do $$
begin
    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'terms' and version = '1.2'
    ) then
        raise exception 'Terms release pointer did not advance to version 1.2';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'privacy' and version = '1.1'
    ) then
        raise exception 'Privacy release pointer changed unexpectedly';
    end if;
end $$;

commit;
