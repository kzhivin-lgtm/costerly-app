-- Additive and repeat-safe. Creates one private bucket for normalized company
-- logo cards. The application reads and writes through its server-only service
-- role; no browser SELECT, INSERT, UPDATE, or DELETE policy is introduced.

insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
values (
    'company-logos',
    'company-logos',
    false,
    2097152,
    array['image/png']::text[]
)
on conflict (id) do nothing;
