-- Publish the exact 3.11.1 playground legal artifacts as version 1.1.
-- Terms 1.1 is material and advances acceptance_version from 1 to 2.
-- Privacy 1.1 is independently versioned and does not create a blocking gate.

begin;

do $$
begin
    if exists (
        select 1
        from public.legal_documents
        where (document_type, version) in (('terms', '1.1'), ('privacy', '1.1'))
    ) then
        raise exception 'Legal version 1.1 already exists; inspect before publishing';
    end if;

    if not exists (
        select 1 from public.legal_document_releases
        where document_type = 'terms' and version = '1.0'
    ) or not exists (
        select 1 from public.legal_document_releases
        where document_type = 'privacy' and version = '1.0'
    ) then
        raise exception 'Expected current legal release 1.0 is missing; inspect before publishing';
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
) values
    (
        'terms',
        '1.1',
        '2',
        'Terms of Service',
        '2026-09-25T00:00:00Z',
        'c57cb8acd7fc91a59d05a6c49bf0fc52b9efbf1e614500a092d59039952630c1',
        '/terms',
        true,
        now()
    ),
    (
        'privacy',
        '1.1',
        '1',
        'Privacy Policy',
        '2026-09-25T00:00:00Z',
        '96fbec67a23be6b518a60ae42d988a8e86f745de1e2b718f8a32b03131b44801',
        '/privacy',
        false,
        now()
    );

update public.legal_document_releases
set version = '1.1', updated_at = now()
where document_type = 'terms' and version = '1.0';

update public.legal_document_releases
set version = '1.1', updated_at = now()
where document_type = 'privacy' and version = '1.0';

do $$
begin
    if not exists (
        select 1 from public.legal_document_releases
        where document_type = 'terms' and version = '1.1'
    ) or not exists (
        select 1 from public.legal_document_releases
        where document_type = 'privacy' and version = '1.1'
    ) then
        raise exception 'Legal release pointers did not advance to version 1.1';
    end if;
end $$;

commit;
