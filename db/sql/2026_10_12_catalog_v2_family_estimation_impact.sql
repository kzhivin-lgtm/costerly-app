-- 3.17.2.8 construction-pattern foundation, increment 1.
--
-- Estimation impact is a Global Material Family property. It is deliberately
-- separate from price, supplier offers, market availability and company-item
-- identity. A low-impact family is not automatically interchangeable: a
-- separate explicit compatibility rule is still required before resolution can
-- relax a variant match.

begin;

alter table public.reference_material_families
    add column if not exists estimation_impact text not null default 'high'
    check (estimation_impact in ('low', 'medium', 'high'));

-- Safe default: a family remains strictly resolved unless the curated registry
-- explicitly says otherwise. This backfills every existing family and makes
-- the migration safe for future seeds that do not yet name an impact.
update public.reference_material_families
set estimation_impact = 'high'
where estimation_impact is null
   or estimation_impact not in ('low', 'medium', 'high');

-- Medium-impact fittings still require compatible functional facts, but do
-- not have the price-bearing variant sensitivity of slides, lift systems and
-- other hardware systems.
update public.reference_material_families
set estimation_impact = 'medium'
where family_code in (
    'hardware_hinge',
    'hardware_connector',
    'hardware_fastener',
    'hardware_mounting_part',
    'hardware_handle',
    'hardware_lock_latch'
);

-- This is the initial, narrowly scoped low-impact family. It does not permit
-- drawer slides, table bases, frames, or arbitrary hardware to match generic
-- cabinet legs. Compatibility remains a later explicit resolver rule.
update public.reference_material_families
set estimation_impact = 'low'
where family_code = 'hardware_leg_caster';

commit;
