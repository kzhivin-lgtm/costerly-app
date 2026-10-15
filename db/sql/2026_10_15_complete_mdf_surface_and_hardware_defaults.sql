-- Complete the approved MDF surface fallback rules and package-price hardware
-- defaults. Run WITHOUT RLS: this migration changes one existing server-side
-- table and creates only temporary tables. It creates no client-readable table.

begin;

alter table public.reference_material_family_default_variants
    add column if not exists applicability_specifications jsonb not null default '{}'::jsonb;

-- Existing defaults remain applicable unless they declare a narrower input
-- shape below. The input shape is never written back to Object Facts.
update public.reference_material_family_default_variants
set applicability_specifications = '{}'::jsonb
where applicability_specifications is null;

-- Existing generic defaults are the target purchasing positions. The explicit
-- surface variants below retain their input evidence but use these positions
-- only when the thickness is missing.
update public.reference_material_family_default_variants variant
set default_specifications = '{"thickness":17}'::jsonb,
    applicability_specifications = '{"board_type":"mdf","surface":"laminated"}'::jsonb,
    updated_at = now()
from public.reference_material_families family
where variant.family_id = family.family_id
  and family.family_code = 'mdf_hdf'
  and variant.priority = 30;

update public.reference_material_family_default_variants variant
set default_specifications = '{"thickness":18}'::jsonb,
    applicability_specifications = '{"board_type":"mdf","surface":"veneer_two_sided"}'::jsonb,
    updated_at = now()
from public.reference_material_families family
where variant.family_id = family.family_id
  and family.family_code = 'mdf_hdf'
  and variant.priority = 40;

insert into public.reference_material_family_default_variants (
    family_id,
    reference_position_id,
    default_specifications,
    applicability_specifications,
    priority,
    active
)
select variant.family_id,
       variant.reference_position_id,
       '{"thickness":17}'::jsonb,
       surface.applicability_specifications,
       surface.priority,
       true
from public.reference_material_family_default_variants variant
join public.reference_material_families family on family.family_id = variant.family_id
cross join (
    values
        (31, '{"board_type":"mdf","surface":"melamine_one_sided"}'::jsonb),
        (32, '{"board_type":"mdf","surface":"melamine_two_sided"}'::jsonb)
) as surface(priority, applicability_specifications)
where family.family_code = 'mdf_hdf'
  and variant.priority = 30
on conflict (family_id, priority) do update set
    reference_position_id = excluded.reference_position_id,
    default_specifications = excluded.default_specifications,
    applicability_specifications = excluded.applicability_specifications,
    active = true,
    updated_at = now();

insert into public.reference_material_family_default_variants (
    family_id,
    reference_position_id,
    default_specifications,
    applicability_specifications,
    priority,
    active
)
select variant.family_id,
       variant.reference_position_id,
       '{"thickness":18}'::jsonb,
       '{"board_type":"mdf","surface":"veneer_one_sided"}'::jsonb,
       41,
       true
from public.reference_material_family_default_variants variant
join public.reference_material_families family on family.family_id = variant.family_id
where family.family_code = 'mdf_hdf'
  and variant.priority = 40
on conflict (family_id, priority) do update set
    reference_position_id = excluded.reference_position_id,
    default_specifications = excluded.default_specifications,
    applicability_specifications = excluded.applicability_specifications,
    active = true,
    updated_at = now();

-- Hardware with no more specific evidence uses the lowest active package in
-- its Family. Drawer slides deliberately remain absent: their length comes
-- from drawer depth minus 100 mm in Material Engine.
create temporary table _hardware_default_candidates on commit drop as
with ranked as (
    select family.family_id,
           family.family_code,
           model.material_model_id as reference_position_id,
           row_number() over (
               partition by family.family_id
               order by price.price_typical asc, model.material_model_code asc
           ) as candidate_rank
    from public.reference_material_families family
    join public.reference_material_models model
      on model.family_id = family.family_id and model.active
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    join public.reference_market_material_legacy_mappings mapping
      on mapping.material_model_id = model.material_model_id
     and mapping.market_code = 'IL' and mapping.classification_status = 'mapped'
    join public.market_material_model_prices price
      on price.material_id = mapping.legacy_material_id
     and price.market_code = 'IL'
     and price.status = 'active'
     and price.price_scope = 'retail_package'
     and price.price_typical > 0
    where family.active
      and family.family_code in (
          'hardware_connector',
          'hardware_door_system',
          'hardware_drawer_system',
          'hardware_electrical_component',
          'hardware_fastener',
          'hardware_furniture_system',
          'hardware_handle',
          'hardware_hinge',
          'hardware_leg_caster',
          'hardware_lift_system',
          'hardware_lock_latch',
          'hardware_mounting_part',
          'hardware_storage_system'
      )
)
select family_id, family_code, reference_position_id
from ranked
where candidate_rank = 1;

do $$
declare
    expected_count integer := 13;
    selected_count integer;
begin
    select count(*) into selected_count from _hardware_default_candidates;
    if selected_count <> expected_count then
        raise exception 'Expected % hardware default positions, found %', expected_count, selected_count;
    end if;
end $$;

insert into public.reference_material_family_default_variants (
    family_id,
    reference_position_id,
    default_specifications,
    applicability_specifications,
    priority,
    active
)
select candidate.family_id,
       candidate.reference_position_id,
       '{}'::jsonb,
       '{}'::jsonb,
       100,
       true
from _hardware_default_candidates candidate
on conflict (family_id, priority) do update set
    reference_position_id = excluded.reference_position_id,
    default_specifications = excluded.default_specifications,
    applicability_specifications = excluded.applicability_specifications,
    active = true,
    updated_at = now();

commit;
