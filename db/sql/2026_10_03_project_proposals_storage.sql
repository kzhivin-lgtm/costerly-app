-- 3.16.4 Client Proposal PDF storage.
-- Proposals are private and are exposed only through short-lived signed URLs.

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'project-proposals',
    'project-proposals',
    false,
    10485760,
    array['application/pdf']
)
on conflict (id) do update set
    public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;
