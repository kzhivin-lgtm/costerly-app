-- 3.17.4.1 Family Default matrix.
--
-- A default fills missing Pricing Key facts only after OCR has already proved
-- a material family. It is not a source fact and it never infers a family.
-- Each active variant is anchored to an active Israel pricing identity, so a
-- policy default cannot select a material absent from the reference catalog.

begin;

create table if not exists public.reference_material_family_default_variants (
    default_variant_id uuid primary key default gen_random_uuid(),
    family_id uuid not null references public.reference_material_families(family_id)
        on delete cascade,
    reference_pricing_identity_id uuid not null
        references public.reference_material_pricing_identities(pricing_identity_id),
    default_specifications jsonb not null check (
        jsonb_typeof(default_specifications) = 'object'
    ),
    priority integer not null check (priority > 0),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (family_id, priority)
);

-- These rows are seeded only because their linked active Israel prices already
-- exist. The values are policy baselines, not claims about source evidence.
-- LDSP 15/17 has no active Israel price identity yet, so it is intentionally
-- not inserted until its catalog entries are authoritative.
with seed(family_code, pricing_identity_id, default_specifications, priority) as (
    values
        ('mdf_hdf', '371347ea-2c31-551e-bb2b-85bc71913a87'::uuid, '{"thickness_mm":17}'::jsonb, 10),
        ('plywood', 'ab232753-7ff8-58f5-a095-921e83e3cd0a'::uuid, '{"thickness_mm":17}'::jsonb, 10)
)
insert into public.reference_material_family_default_variants (
    family_id, reference_pricing_identity_id, default_specifications, priority, active
)
select family.family_id, seed.pricing_identity_id, seed.default_specifications, seed.priority, true
from seed
join public.reference_material_families family using (family_code)
join public.reference_material_pricing_identities identity
    on identity.pricing_identity_id = seed.pricing_identity_id
   and identity.market_code = 'IL'
   and identity.status = 'active'
on conflict (family_id, priority) do update set
    reference_pricing_identity_id = excluded.reference_pricing_identity_id,
    default_specifications = excluded.default_specifications,
    active = true,
    updated_at = now();

alter table public.reference_material_family_default_variants enable row level security;
revoke all on public.reference_material_family_default_variants from public, anon, authenticated;
grant all on public.reference_material_family_default_variants to service_role;

commit;
