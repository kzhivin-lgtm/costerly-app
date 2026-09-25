-- Publish the exact 3.11.1 playground legal artifacts as version 1.0.
-- A later material Terms revision must use a new document version and a new
-- acceptance_version. Never update a published legal_documents row.

begin;

do $$
begin
    if exists (
        select 1
        from public.legal_documents
        where (document_type, version) in (('terms', '1.0'), ('privacy', '1.0'))
    ) or exists (
        select 1
        from public.legal_document_releases
        where document_type in ('terms', 'privacy')
    ) then
        raise exception 'Legal version 1.0 or a current release already exists; inspect before publishing';
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
        '1.0',
        '1',
        'Terms and Conditions',
        '2026-09-25T00:00:00Z',
        'a4f970a69d10f0988b275b704f36bee297ad2a23c53b59853c85895d7bfc6fa4',
        '/terms',
        true,
        now()
    ),
    (
        'privacy',
        '1.0',
        '1',
        'Privacy Policy',
        '2026-09-25T00:00:00Z',
        '437bd95ede5edef786762d9a5ec185935bf518808d517ddcf7d6a46188f7b17d',
        '/privacy',
        false,
        now()
    );

insert into public.legal_document_releases (document_type, version)
values ('terms', '1.0'), ('privacy', '1.0');

commit;
