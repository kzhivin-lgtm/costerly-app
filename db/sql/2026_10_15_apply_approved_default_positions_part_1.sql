-- Approved default positions, part 1.
--
-- This file contains only values explicitly settled in the 15 Oct review.
-- It does not guess defaults for the separately tracked unresolved Families.
-- Every inserted default is anchored to an active IL listing with an active
-- material-only price. The selected position is the lowest-priced compatible
-- Israel Reference position, unless the approved default explicitly names its
-- required secondary construction.

begin;

create temporary table _approved_default_seed (
    family_code text not null,
    lookup_specifications jsonb not null,
    default_specifications jsonb not null,
    canonical_name text,
    priority integer not null,
    primary key (family_code, priority)
) on commit drop;

insert into _approved_default_seed (
    family_code, lookup_specifications, default_specifications, canonical_name, priority
) values
    ('acrylic_pmma', '{"thickness":5}', '{"thickness":5}', null, 10),
    ('aluminium_composite_panel', '{"thickness":4}', '{"thickness":4}', null, 10),
    ('compact_laminate', '{"thickness":12}', '{"thickness":12}', null, 10),
    ('composite_sandwich_panel', '{"thickness":10}', '{"thickness":10}', null, 10),
    ('decorative_film_foil', '{"width":1220}', '{"width":1220}', null, 10),
    ('edge_banding',
        '{"width_thickness":{"width_mm":24,"thickness_mm":0.8}}',
        '{"width_thickness":{"width_mm":24,"thickness_mm":0.8}}',
        'Edge banding, 24 × 0.8 mm, PVC edge band, 0.8 mm, up to 24 mm wide', 10),
    ('engineered_quartz_mineral_hybrid', '{"thickness":20}', '{"thickness":20}', null, 10),
    ('mdf_hdf',
        '{"board_type":"mdf","surface":"laminated","thickness":17}',
        '{"board_type":"mdf","surface":"laminated","thickness":17}', null, 30),
    ('mdf_hdf',
        '{"board_type":"mdf","surface":"veneer_two_sided","thickness":18}',
        '{"board_type":"mdf","surface":"veneer_two_sided","thickness":18}', null, 40),
    ('filler_hardener_thinner',
        '{"chemistry_product_type":"solventborne polyurethane clear lacquer system, matt"}',
        '{"chemistry_product_type":"solventborne polyurethane clear lacquer system, matt"}', null, 10),
    ('glass', '{"thickness":4}', '{"thickness":4}', null, 10),
    ('hpl_cpl', '{"thickness":1}', '{"thickness":1}', null, 10),
    ('lightweight_sandwich_panel', '{"thickness":10}', '{"thickness":10}', null, 10),
    ('mdf_hdf',
        '{"board_type":"mdf","surface":"raw","thickness":17}',
        '{"board_type":"mdf","surface":"raw","thickness":17}', null, 10),
    ('mdf_hdf',
        '{"board_type":"hdf","surface":"raw","thickness":8}',
        '{"board_type":"hdf","surface":"raw","thickness":8}', null, 20),
    ('melamine_faced_particleboard', '{"thickness":16}', '{"thickness":16}', null, 10),
    ('metal_flat_bar',
        '{"metal_type":"carbon steel","width_thickness":{"width_mm":30,"thickness_mm":1.5}}',
        '{"metal_type":"carbon steel","width_thickness":{"width_mm":30,"thickness_mm":1.5}}', null, 10),
    ('metal_profile_angle_channel',
        '{"metal_type":"carbon steel","section_profile":"angle_30x30"}',
        '{"metal_type":"carbon steel","section_profile":"angle_30x30"}', null, 10),
    ('metal_round_bar_rod_wire',
        '{"metal_type":"carbon steel","diameter":10}',
        '{"metal_type":"carbon steel","diameter":10}', null, 10),
    ('metal_tube',
        '{"metal_type":"carbon steel","section_profile":"round_tube_d20"}',
        '{"metal_type":"carbon steel","section_profile":"round_tube_d20"}', null, 10),
    ('mirror', '{"thickness":4}', '{"thickness":4}', null, 10),
    ('natural_stone_slab',
        '{"stone_type":"marble","thickness":20}',
        '{"stone_type":"marble","thickness":20}', null, 10),
    ('osb', '{"thickness":12}', '{"thickness":12}', null, 10),
    ('paint_lacquer_stain',
        '{"coating_system":"waterborne clear lacquer system, matt"}',
        '{"coating_system":"waterborne clear lacquer system, matt"}', null, 10),
    ('plywood', '{"thickness":17}', '{"thickness":17}', null, 10),
    ('plywood_special', '{"thickness":15}', '{"thickness":15}', null, 10),
    ('polycarbonate_petg_pvc_abs', '{"thickness":4}', '{"thickness":4}', null, 10),
    ('porcelain_ceramic_slab', '{"thickness":12}', '{"thickness":12}', null, 10),
    ('primer',
        '{"coating_system":"metal etch primer"}',
        '{"coating_system":"metal etch primer"}', null, 10),
    ('powder_coating',
        '{"coating_system":"powder coating standard colour"}',
        '{"coating_system":"powder coating standard colour"}', null, 10),
    ('sheet_metal',
        '{"metal_type":"carbon steel","thickness":1.5}',
        '{"metal_type":"carbon steel","thickness":1.5}', null, 10),
    ('sheet_metal',
        '{"metal_type":"stainless steel","thickness":1.5}',
        '{"metal_type":"stainless steel","thickness":1.5}', null, 20),
    ('sheet_metal',
        '{"metal_type":"aluminium","thickness":1.5}',
        '{"metal_type":"aluminium","thickness":1.5}', null, 30),
    ('sheet_metal',
        '{"metal_type":"copper","thickness":1.5}',
        '{"metal_type":"copper","thickness":1.5}', null, 40),
    ('sheet_metal',
        '{"metal_type":"brass","thickness":1.5}',
        '{"metal_type":"brass","thickness":1.5}', null, 50),
    ('sheet_plastic', '{"thickness":12}', '{"thickness":12}', null, 10),
    ('sintered_ultra_compact_surface', '{"thickness":6}', '{"thickness":6}', null, 10),
    ('solid_surface', '{"thickness":6}', '{"thickness":6}', null, 10),
    ('terrazzo_engineered_agglomerate', '{"thickness":20}', '{"thickness":20}', null, 10),
    ('timber_solid_wood_panel',
        '{"species":"oak"}',
        '{"species":"oak","secondary_thickness_mm":20}', null, 10),
    ('vinyl_film', '{"width":1220}', '{"width":1220}', null, 10),
    ('wood_veneer',
        '{"species":"european oak"}',
        '{"species":"european oak","secondary_thickness_mm":0.5}', null, 10);

create temporary table _approved_default_positions on commit drop as
with model_specifications as (
    select value.material_model_id, jsonb_object_agg(value.attribute_code, value.attribute_value) as specifications
    from public.reference_material_model_attribute_values value
    group by value.material_model_id
), ranked as (
    select seed.family_code,
           seed.default_specifications,
           seed.priority,
           model.material_model_id as reference_position_id,
           row_number() over (
               partition by seed.family_code, seed.priority
               order by price.price_typical asc, model.material_model_code asc
           ) as candidate_rank
    from _approved_default_seed seed
    join public.reference_material_families family
      on family.family_code = seed.family_code and family.active
    join public.reference_material_models model
      on model.family_id = family.family_id and model.active
    join model_specifications specs
      on specs.material_model_id = model.material_model_id
     and specs.specifications @> seed.lookup_specifications
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
     and price.price_scope = 'material_only'
     and price.price_typical > 0
    where seed.canonical_name is null
       or model.canonical_name = seed.canonical_name
)
select family_code, default_specifications, priority, reference_position_id
from ranked
where candidate_rank = 1;

do $$
declare
    expected_count integer;
    selected_count integer;
begin
    select count(*) into expected_count from _approved_default_seed;
    select count(*) into selected_count from _approved_default_positions;
    if selected_count <> expected_count then
        raise exception 'Expected % approved default positions, found %', expected_count, selected_count;
    end if;
end $$;

insert into public.reference_material_family_default_variants (
    family_id, reference_position_id, default_specifications, priority, active
)
select family.family_id,
       chosen.reference_position_id,
       chosen.default_specifications,
       chosen.priority,
       true
from _approved_default_positions chosen
join public.reference_material_families family on family.family_code = chosen.family_code
on conflict (family_id, priority) do update set
    reference_position_id = excluded.reference_position_id,
    default_specifications = excluded.default_specifications,
    active = true,
    updated_at = now();

commit;
