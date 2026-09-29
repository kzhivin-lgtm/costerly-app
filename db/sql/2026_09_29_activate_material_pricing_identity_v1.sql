-- 3.15.5 activation checkpoint.
-- Run only after Railway has deployed commit 38d6846 successfully.
-- This is intentionally a separate, short transaction: it turns the already
-- validated candidate layer on, then switches the resolver version.

begin;

do $$
declare
    identity_count integer;
    member_count integer;
    price_count integer;
begin
    select count(*) into identity_count
    from public.reference_material_pricing_identities
    where market_code = 'IL' and status = 'candidate';
    select count(*) into member_count
    from public.reference_material_pricing_identity_members;
    select count(*) into price_count
    from public.market_material_pricing_identity_prices
    where status = 'candidate';
    if identity_count <> 2807 or member_count <> 4436 or price_count <> 2807 then
        raise exception 'Pricing identity activation precondition failed: identities %, members %, prices %',
            identity_count, member_count, price_count;
    end if;
end $$;

update public.reference_material_pricing_identities
set status = 'active', updated_at = now()
where market_code = 'IL' and status = 'candidate';

update public.market_material_pricing_identity_prices
set status = 'active', updated_at = now()
where status = 'candidate';

update public.material_resolver_versions
set status = 'retired'
where market_code = 'IL' and status = 'active';

insert into public.material_resolver_versions (
    resolver_version, market_code, algorithm_version, catalog_fingerprint,
    status, activated_at
) values (
    'material_identity_v3', 'IL', 'pricing_identity_v1',
    'IL:global_catalog_v1:4436:pricing_identities:2807:2026-09-29',
    'active', now()
)
on conflict (resolver_version) do update set
    algorithm_version = excluded.algorithm_version,
    catalog_fingerprint = excluded.catalog_fingerprint,
    status = 'active',
    activated_at = coalesce(
        public.material_resolver_versions.activated_at,
        excluded.activated_at
    );

commit;

select
    (select count(*) from public.reference_material_pricing_identities where market_code = 'IL' and status = 'active') as active_pricing_identities,
    (select count(*) from public.market_material_pricing_identity_prices where status = 'active') as active_pricing_prices,
    (select resolver_version from public.material_resolver_versions where market_code = 'IL' and status = 'active') as active_resolver_version;
