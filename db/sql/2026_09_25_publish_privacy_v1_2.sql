-- Publish the reviewed Privacy Policy 1.2 revision for task 3.11.1.
-- Privacy acceptance_version remains 1 and does not create a blocking gate.

begin;

do $$
begin
    if exists (
        select 1
        from public.legal_documents
        where document_type = 'privacy' and version = '1.2'
    ) then
        raise exception 'Privacy version 1.2 already exists; inspect before publishing';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'privacy' and version = '1.1'
    ) then
        raise exception 'Expected current Privacy release 1.1 is missing; inspect before publishing';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'terms' and version = '1.2'
    ) then
        raise exception 'Expected current Terms release 1.2 is missing; inspect before publishing';
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
    'privacy',
    '1.2',
    '1',
    'Privacy Policy',
    '2026-09-25T00:00:00Z',
    'baee97a79a3be012dec6b0e5610aa380abd01e753dd64930ea97ec25bf13d674',
    '/privacy',
    false,
    now()
);

update public.legal_document_releases
set version = '1.2', updated_at = now()
where document_type = 'privacy' and version = '1.1';

do $$
begin
    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'privacy' and version = '1.2'
    ) then
        raise exception 'Privacy release pointer did not advance to version 1.2';
    end if;

    if not exists (
        select 1
        from public.legal_document_releases
        where document_type = 'terms' and version = '1.2'
    ) then
        raise exception 'Terms release pointer changed unexpectedly';
    end if;
end $$;

commit;
