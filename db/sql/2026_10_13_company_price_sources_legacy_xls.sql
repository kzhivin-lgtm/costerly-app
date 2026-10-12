-- 3.17.2.12: permit legacy Excel workbooks in the private Price Source bucket.
-- Preserve every existing accepted MIME type. The application already parses
-- .xls with xlrd and records this MIME type in immutable source evidence.

begin;

update storage.buckets
set allowed_mime_types = array(
    select distinct mime_type
    from unnest(
        coalesce(storage.buckets.allowed_mime_types, array[]::text[])
        || array['application/vnd.ms-excel']::text[]
    ) as accepted(mime_type)
    order by mime_type
)
where id = 'company-price-sources';

do $$
begin
    if not exists (
        select 1
        from storage.buckets
        where id = 'company-price-sources'
    ) then
        raise exception 'Price Source storage bucket is missing';
    end if;

    if not exists (
        select 1
        from storage.buckets
        where id = 'company-price-sources'
          and 'application/vnd.ms-excel' = any(allowed_mime_types)
    ) then
        raise exception 'Legacy XLS MIME type was not enabled for Price Source';
    end if;
end $$;

commit;
