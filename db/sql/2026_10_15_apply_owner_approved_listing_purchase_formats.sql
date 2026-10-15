-- Owner-approved default purchase formats for active Israel Reference listings.
--
-- These are catalog defaults until supplier-specific listing formats are
-- curated. They make a physical purchase unit explicit for Material Engine;
-- they never rewrite source evidence. Run WITHOUT RLS.

begin;

create temporary table _owner_format_seed (
    family_code text primary key,
    supply_format_code text not null,
    purchase_unit text not null,
    purchasable_dimensions jsonb not null
) on commit drop;

insert into _owner_format_seed (
    family_code, supply_format_code, purchase_unit, purchasable_dimensions
) values
    ('acrylic_pmma', 'default_2440x1220', 'sheet',
        '{"length_mm":2440,"width_mm":1220,"format_source":"owner_approved_catalog_default"}'),
    ('aluminium_composite_panel', 'default_2440x1220', 'sheet',
        '{"length_mm":2440,"width_mm":1220,"format_source":"owner_approved_catalog_default"}'),
    ('compact_laminate', 'default_2790x2060', 'sheet',
        '{"length_mm":2790,"width_mm":2060,"format_source":"owner_approved_catalog_default"}'),
    ('engineered_quartz_mineral_hybrid', 'default_3050x1440', 'slab',
        '{"length_mm":3050,"width_mm":1440,"format_source":"owner_approved_catalog_default"}'),
    ('glass', 'default_3210x2250', 'sheet',
        '{"length_mm":3210,"width_mm":2250,"format_source":"owner_approved_catalog_default"}'),
    ('hpl_cpl', 'default_3050x1310', 'sheet',
        '{"length_mm":3050,"width_mm":1310,"format_source":"owner_approved_catalog_default"}'),
    ('mirror', 'default_2440x1830', 'sheet',
        '{"length_mm":2440,"width_mm":1830,"format_source":"owner_approved_catalog_default"}'),
    ('polycarbonate_petg_pvc_abs', 'default_2440x1220', 'sheet',
        '{"length_mm":2440,"width_mm":1220,"format_source":"owner_approved_catalog_default"}'),
    ('sheet_plastic', 'default_2440x1220', 'sheet',
        '{"length_mm":2440,"width_mm":1220,"format_source":"owner_approved_catalog_default"}'),
    ('porcelain_ceramic_slab', 'default_3200x1600', 'slab',
        '{"length_mm":3200,"width_mm":1600,"format_source":"owner_approved_catalog_default"}'),
    ('sintered_ultra_compact_surface', 'default_3200x1600', 'slab',
        '{"length_mm":3200,"width_mm":1600,"format_source":"owner_approved_catalog_default"}'),
    ('terrazzo_engineered_agglomerate', 'cut_1000x1000', 'slab',
        '{"length_mm":1000,"width_mm":1000,"format_source":"owner_approved_cut_segment"}'),
    -- Sold as a one-metre cut across a 1220 mm width, not an unbounded roll.
    ('wood_veneer', 'cut_1000x1220', 'sheet',
        '{"length_mm":1000,"width_mm":1220,"format_source":"owner_approved_cut_segment"}'),
    ('decorative_film_foil', 'cut_1000x1220', 'sheet',
        '{"length_mm":1000,"width_mm":1220,"format_source":"owner_approved_cut_segment"}'),
    ('vinyl_film', 'cut_1000x1220', 'sheet',
        '{"length_mm":1000,"width_mm":1220,"format_source":"owner_approved_cut_segment"}'),
    -- The stock is a 50 m roll, but cost is deliberately calculated by metre.
    ('edge_banding', 'standard_roll_50000x24', 'roll',
        '{"length_mm":50000,"width_mm":24,"thickness_mm":0.8,"format_source":"owner_approved_roll_meter_pricing"}'),
    ('metal_flat_bar', 'standard_bar_6000', 'bar',
        '{"length_mm":6000,"format_source":"owner_approved_catalog_default"}'),
    ('metal_profile_angle_channel', 'standard_bar_6000', 'bar',
        '{"length_mm":6000,"format_source":"owner_approved_catalog_default"}'),
    ('metal_round_bar_rod_wire', 'standard_bar_6000', 'bar',
        '{"length_mm":6000,"format_source":"owner_approved_catalog_default"}'),
    ('metal_tube', 'standard_bar_6000', 'bar',
        '{"length_mm":6000,"format_source":"owner_approved_catalog_default"}');

-- Retire an earlier owner default only when it is one of our defaults. A
-- supplier-proven listing format stays active and can coexist with this one.
update public.reference_market_material_supply_formats format
set active = false,
    updated_at = now()
from public.reference_market_material_listings listing
join public.reference_material_models model on model.material_model_id = listing.material_model_id
join public.reference_material_families family on family.family_id = model.family_id
join _owner_format_seed seed on seed.family_code = family.family_code
where format.market_material_listing_id = listing.market_material_listing_id
  and listing.market_code = 'IL'
  and listing.active
  and format.active
  and format.purchasable_dimensions ->> 'format_source' like 'owner_approved_%'
  and format.supply_format_code <> seed.supply_format_code;

insert into public.reference_market_material_supply_formats (
    market_material_listing_id, supply_format_code, purchase_unit,
    purchasable_dimensions, minimum_purchase_quantity, active
)
select listing.market_material_listing_id,
       seed.supply_format_code,
       seed.purchase_unit,
       seed.purchasable_dimensions,
       1,
       true
from _owner_format_seed seed
join public.reference_material_families family
  on family.family_code = seed.family_code and family.active
join public.reference_material_models model
  on model.family_id = family.family_id and model.active
join public.reference_market_material_listings listing
  on listing.material_model_id = model.material_model_id
 and listing.market_code = 'IL' and listing.active
on conflict (market_material_listing_id, supply_format_code) do update
set purchase_unit = excluded.purchase_unit,
    purchasable_dimensions = excluded.purchasable_dimensions,
    minimum_purchase_quantity = excluded.minimum_purchase_quantity,
    active = true,
    updated_at = now();

do $$
declare
    missing_formats integer;
begin
    select count(*) into missing_formats
    from _owner_format_seed seed
    join public.reference_material_families family
      on family.family_code = seed.family_code and family.active
    join public.reference_material_models model
      on model.family_id = family.family_id and model.active
    join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL' and listing.active
    left join public.reference_market_material_supply_formats format
      on format.market_material_listing_id = listing.market_material_listing_id
     and format.supply_format_code = seed.supply_format_code
     and format.active
    where format.supply_format_id is null;
    if missing_formats <> 0 then
        raise exception 'Owner-approved listing purchase formats missing: %', missing_formats;
    end if;
end $$;

commit;
