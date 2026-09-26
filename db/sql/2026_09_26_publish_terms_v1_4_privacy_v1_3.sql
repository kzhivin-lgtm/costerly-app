-- Publish the final three-layer Customer Content model for task 3.11.1.
-- Terms 1.4 is material and advances acceptance_version from 4 to 5.
-- Privacy 1.3 is independently versioned; Privacy acceptance_version remains 1.

begin;

do $$
begin
    if exists (
        select 1
        from public.legal_documents
        where (document_type, version) in (('terms', '1.4'), ('privacy', '1.3'))
    ) then
        raise exception 'Terms 1.4 or Privacy 1.3 already exists; inspect before publishing';
    end if;

    if not exists (
        select 1 from public.legal_document_releases
        where document_type = 'terms' and version = '1.3'
    ) or not exists (
        select 1 from public.legal_document_releases
        where document_type = 'privacy' and version = '1.2'
    ) then
        raise exception 'Expected current Terms 1.3 and Privacy 1.2 releases are missing';
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
        '1.4',
        '5',
        'Terms of Service',
        '2026-09-26T00:00:00Z',
        '16092ef0d0373774dfb4023d2ed15bc866170bf56224a5d16cdf7cea10f494f5',
        '/terms',
        true,
        now()
    ),
    (
        'privacy',
        '1.3',
        '1',
        'Privacy Policy',
        '2026-09-26T00:00:00Z',
        '21f380232a37c56c8e0b6f5b735d2be556cb3e0ddf551360fb90c67bfb87b978',
        '/privacy',
        false,
        now()
    );

update public.legal_document_releases
set version = '1.4', updated_at = now()
where document_type = 'terms' and version = '1.3';

update public.legal_document_releases
set version = '1.3', updated_at = now()
where document_type = 'privacy' and version = '1.2';

do $$
begin
    if not exists (
        select 1 from public.legal_document_releases
        where document_type = 'terms' and version = '1.4'
    ) or not exists (
        select 1 from public.legal_document_releases
        where document_type = 'privacy' and version = '1.3'
    ) then
        raise exception 'Legal release pointers did not advance';
    end if;
end $$;

commit;
