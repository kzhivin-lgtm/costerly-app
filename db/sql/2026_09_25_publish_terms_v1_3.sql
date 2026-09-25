-- Publish the final pre-launch Terms 1.3 revision for task 3.11.1.
-- Terms 1.3 advances acceptance_version from 3 to 4.
-- Privacy remains independently published at version 1.2.

begin;

do $$
begin
    if exists (
        select 1
        from public.legal_documents
        where document_type = 'terms' and version = '1.3'
    ) then
        raise exception 'Terms version 1.3 already exists; inspect before publishing';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'terms' and version = '1.2'
    ) then
        raise exception 'Expected current Terms release 1.2 is missing; inspect before publishing';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'privacy' and version = '1.2'
    ) then
        raise exception 'Expected current Privacy release 1.2 is missing; inspect before publishing';
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
    '1.3',
    '4',
    'Terms of Service',
    '2026-09-25T00:00:00Z',
    '346cb5ee4be1cac1b0fa4a80deb8c1a89a330e426dae8d931485b79233cc2b0d',
    '/terms',
    true,
    now()
);

update public.legal_document_releases
set version = '1.3', updated_at = now()
where document_type = 'terms' and version = '1.2';

do $$
begin
    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'terms' and version = '1.3'
    ) then
        raise exception 'Terms release pointer did not advance to version 1.3';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'privacy' and version = '1.2'
    ) then
        raise exception 'Privacy release pointer changed unexpectedly';
    end if;
end $$;

commit;
