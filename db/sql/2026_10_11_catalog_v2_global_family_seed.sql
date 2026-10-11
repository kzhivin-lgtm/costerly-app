-- 3.17.2.2 Global family registry seed.
--
-- Depends on 2026_10_11_catalog_v2_contract_foundation.sql. This is an
-- unapplied seed: it establishes Global vocabulary only. It does not import
-- legacy materials, create Israel listings, alter Company Price Catalog data,
-- or switch any reader.

begin;

with category_seed (
    category_code, category_name, production_department_code, entity_role_code, sort_order
) as (
    values
        ('wood_panels', 'Wood panels', 'wood', 'material', 10),
        ('wood_surfaces', 'Wood surfaces and edges', 'wood', 'material', 20),
        ('wood_solid', 'Timber and solid wood', 'wood', 'material', 30),
        ('metal_stock', 'Metal stock', 'metal', 'material', 40),
        ('glass', 'Glass and mirrors', 'glass_plastics', 'material', 50),
        ('plastics', 'Plastics and composites', 'glass_plastics', 'material', 60),
        ('stone', 'Stone fabricated surfaces', 'stone', 'material', 70),
        ('coating', 'Coating systems', 'coating', 'material', 80),
        ('hardware_fittings', 'Furniture fittings', null, 'hardware', 90),
        ('hardware_fasteners', 'Fasteners and connectors', null, 'hardware', 100),
        ('hardware_systems', 'Hardware systems and components', null, 'hardware', 110),
        ('purchased_components', 'Purchased fabricated components', null, 'purchased_fabricated_component', 120),
        ('consumables', 'Consumables', null, 'consumable', 130),
        ('packaging', 'Packaging', null, 'packaging', 140)
)
insert into public.reference_material_categories_v2 (
    category_code, category_name, production_department_code, entity_role_code, sort_order, active
)
select category_code, category_name, production_department_code, entity_role_code, sort_order, true
from category_seed
on conflict (category_code) do update set
    category_name = excluded.category_name,
    production_department_code = excluded.production_department_code,
    entity_role_code = excluded.entity_role_code,
    sort_order = excluded.sort_order,
    active = true;

with family_seed (
    family_code, family_name, category_code, production_department_code,
    entity_role_code, primary_attribute_code, primary_attribute_name,
    primary_value_type
) as (
    values
        ('mdf_hdf', 'MDF / HDF', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('faced_mdf', 'Faced MDF', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('particleboard', 'Particleboard', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('melamine_faced_particleboard', 'Melamine-faced particleboard', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('plywood', 'Plywood', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('plywood_special', 'Special plywood', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('osb', 'OSB', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('fibreboard_hardboard', 'Fibreboard / hardboard', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('lightweight_sandwich_panel', 'Lightweight / sandwich panel', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('hpl_cpl', 'HPL / CPL', 'wood_surfaces', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('compact_laminate', 'Compact laminate', 'wood_panels', 'wood', 'material', 'thickness', 'Thickness', 'dimension'),
        ('wood_veneer', 'Wood veneer', 'wood_surfaces', 'wood', 'material', 'species', 'Species', 'text'),
        ('edge_banding', 'Edge banding', 'wood_surfaces', 'wood', 'material', 'width_thickness', 'Width × thickness', 'dimension'),
        ('decorative_film_foil', 'Decorative film / foil', 'wood_surfaces', 'wood', 'material', 'width', 'Width', 'dimension'),
        ('timber_solid_wood_panel', 'Timber / solid wood panel', 'wood_solid', 'wood', 'material', 'species', 'Species', 'text'),
        ('sheet_metal', 'Sheet metal', 'metal_stock', 'metal', 'material', 'thickness', 'Thickness', 'dimension'),
        ('metal_tube', 'Metal tube', 'metal_stock', 'metal', 'material', 'section_profile', 'Section profile', 'dimension'),
        ('metal_profile_angle_channel', 'Metal profile / angle / channel', 'metal_stock', 'metal', 'material', 'section_profile', 'Section profile', 'dimension'),
        ('metal_flat_bar', 'Metal flat bar', 'metal_stock', 'metal', 'material', 'width_thickness', 'Width × thickness', 'dimension'),
        ('metal_round_bar_rod_wire', 'Metal round bar / rod / wire', 'metal_stock', 'metal', 'material', 'diameter', 'Diameter', 'dimension'),
        ('glass', 'Glass', 'glass', 'glass_plastics', 'material', 'thickness', 'Thickness', 'dimension'),
        ('mirror', 'Mirror', 'glass', 'glass_plastics', 'material', 'thickness', 'Thickness', 'dimension'),
        ('acrylic_pmma', 'Acrylic / PMMA', 'plastics', 'glass_plastics', 'material', 'thickness', 'Thickness', 'dimension'),
        ('polycarbonate_petg_pvc_abs', 'Polycarbonate / PETG / PVC / ABS', 'plastics', 'glass_plastics', 'material', 'thickness', 'Thickness', 'dimension'),
        ('sheet_plastic', 'Sheet plastic', 'plastics', 'glass_plastics', 'material', 'thickness', 'Thickness', 'dimension'),
        ('vinyl_film', 'Vinyl film', 'plastics', 'glass_plastics', 'material', 'width', 'Width', 'dimension'),
        ('aluminium_composite_panel', 'Aluminium composite panel', 'plastics', 'glass_plastics', 'material', 'thickness', 'Thickness', 'dimension'),
        ('composite_sandwich_panel', 'Composite sandwich panel', 'plastics', 'glass_plastics', 'material', 'thickness', 'Thickness', 'dimension'),
        ('natural_stone_slab', 'Natural stone slab', 'stone', 'stone', 'material', 'thickness', 'Thickness', 'dimension'),
        ('engineered_quartz_mineral_hybrid', 'Engineered quartz / mineral hybrid', 'stone', 'stone', 'material', 'thickness', 'Thickness', 'dimension'),
        ('sintered_ultra_compact_surface', 'Sintered / ultra-compact surface', 'stone', 'stone', 'material', 'thickness', 'Thickness', 'dimension'),
        ('porcelain_ceramic_slab', 'Porcelain / ceramic slab', 'stone', 'stone', 'material', 'thickness', 'Thickness', 'dimension'),
        ('solid_surface', 'Solid surface', 'stone', 'stone', 'material', 'thickness', 'Thickness', 'dimension'),
        ('terrazzo_engineered_agglomerate', 'Terrazzo / engineered agglomerate', 'stone', 'stone', 'material', 'thickness', 'Thickness', 'dimension'),
        ('paint_lacquer_stain', 'Paint / lacquer / stain', 'coating', 'coating', 'material', 'coating_system', 'Coating system', 'text'),
        ('primer', 'Primer', 'coating', 'coating', 'material', 'coating_system', 'Coating system', 'text'),
        ('powder_coating', 'Powder coating', 'coating', 'coating', 'material', 'coating_system', 'Coating system', 'text'),
        ('filler_hardener_thinner', 'Filler / hardener / thinner', 'coating', 'coating', 'material', 'chemistry_product_type', 'Chemistry / product type', 'text'),
        ('hardware_hinge', 'Hardware: hinge', 'hardware_fittings', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_drawer_slide', 'Hardware: drawer slide', 'hardware_fittings', null, 'hardware', 'nominal_length', 'Nominal length', 'dimension'),
        ('hardware_connector', 'Hardware: connector', 'hardware_fasteners', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_fastener', 'Hardware: fastener', 'hardware_fasteners', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_mounting_part', 'Hardware: mounting part', 'hardware_fasteners', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_handle', 'Hardware: handle', 'hardware_fittings', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_leg_caster', 'Hardware: leg / caster', 'hardware_fittings', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_lift_system', 'Hardware: lift system', 'hardware_systems', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_lock_latch', 'Hardware: lock / latch', 'hardware_fittings', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_drawer_system', 'Hardware: drawer system', 'hardware_systems', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_storage_system', 'Hardware: storage system', 'hardware_systems', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_door_system', 'Hardware: door system', 'hardware_systems', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_furniture_system', 'Hardware: furniture system', 'hardware_systems', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('hardware_electrical_component', 'Hardware: electrical component', 'hardware_systems', null, 'hardware', 'model_series', 'Model / series', 'text'),
        ('purchased_fabricated_component', 'Purchased fabricated component', 'purchased_components', null, 'purchased_fabricated_component', 'component_type', 'Component type', 'text'),
        ('packaging_material', 'Packaging material', 'packaging', null, 'packaging', 'packaging_type', 'Packaging type', 'text')
)
insert into public.reference_material_families (
    family_code, family_name, category_id, production_department_code, entity_role_code, active
)
select
    seed.family_code,
    seed.family_name,
    category.category_id,
    seed.production_department_code,
    seed.entity_role_code,
    true
from family_seed seed
join public.reference_material_categories_v2 category using (category_code)
on conflict (family_code) do update set
    family_name = excluded.family_name,
    category_id = excluded.category_id,
    production_department_code = excluded.production_department_code,
    entity_role_code = excluded.entity_role_code,
    active = true,
    updated_at = now();

with primary_attributes (
    family_code, attribute_code, attribute_name, value_type
) as (
    values
        ('mdf_hdf', 'thickness', 'Thickness', 'dimension'), ('faced_mdf', 'thickness', 'Thickness', 'dimension'),
        ('particleboard', 'thickness', 'Thickness', 'dimension'), ('melamine_faced_particleboard', 'thickness', 'Thickness', 'dimension'),
        ('plywood', 'thickness', 'Thickness', 'dimension'), ('plywood_special', 'thickness', 'Thickness', 'dimension'),
        ('osb', 'thickness', 'Thickness', 'dimension'), ('fibreboard_hardboard', 'thickness', 'Thickness', 'dimension'),
        ('lightweight_sandwich_panel', 'thickness', 'Thickness', 'dimension'), ('hpl_cpl', 'thickness', 'Thickness', 'dimension'),
        ('compact_laminate', 'thickness', 'Thickness', 'dimension'), ('wood_veneer', 'species', 'Species', 'text'),
        ('edge_banding', 'width_thickness', 'Width × thickness', 'dimension'), ('decorative_film_foil', 'width', 'Width', 'dimension'), ('timber_solid_wood_panel', 'species', 'Species', 'text'),
        ('sheet_metal', 'thickness', 'Thickness', 'dimension'), ('metal_tube', 'section_profile', 'Section profile', 'dimension'),
        ('metal_profile_angle_channel', 'section_profile', 'Section profile', 'dimension'), ('metal_flat_bar', 'width_thickness', 'Width × thickness', 'dimension'),
        ('metal_round_bar_rod_wire', 'diameter', 'Diameter', 'dimension'), ('glass', 'thickness', 'Thickness', 'dimension'),
        ('mirror', 'thickness', 'Thickness', 'dimension'), ('acrylic_pmma', 'thickness', 'Thickness', 'dimension'),
        ('polycarbonate_petg_pvc_abs', 'thickness', 'Thickness', 'dimension'), ('sheet_plastic', 'thickness', 'Thickness', 'dimension'),
        ('vinyl_film', 'width', 'Width', 'dimension'), ('aluminium_composite_panel', 'thickness', 'Thickness', 'dimension'), ('composite_sandwich_panel', 'thickness', 'Thickness', 'dimension'), ('natural_stone_slab', 'thickness', 'Thickness', 'dimension'),
        ('engineered_quartz_mineral_hybrid', 'thickness', 'Thickness', 'dimension'), ('sintered_ultra_compact_surface', 'thickness', 'Thickness', 'dimension'),
        ('porcelain_ceramic_slab', 'thickness', 'Thickness', 'dimension'), ('solid_surface', 'thickness', 'Thickness', 'dimension'), ('terrazzo_engineered_agglomerate', 'thickness', 'Thickness', 'dimension'),
        ('paint_lacquer_stain', 'coating_system', 'Coating system', 'text'), ('primer', 'coating_system', 'Coating system', 'text'),
        ('powder_coating', 'coating_system', 'Coating system', 'text'), ('filler_hardener_thinner', 'chemistry_product_type', 'Chemistry / product type', 'text'),
        ('hardware_hinge', 'model_series', 'Model / series', 'text'), ('hardware_drawer_slide', 'nominal_length', 'Nominal length', 'dimension'),
        ('hardware_connector', 'model_series', 'Model / series', 'text'), ('hardware_fastener', 'model_series', 'Model / series', 'text'),
        ('hardware_mounting_part', 'model_series', 'Model / series', 'text'), ('hardware_handle', 'model_series', 'Model / series', 'text'),
        ('hardware_leg_caster', 'model_series', 'Model / series', 'text'), ('hardware_lift_system', 'model_series', 'Model / series', 'text'),
        ('hardware_lock_latch', 'model_series', 'Model / series', 'text'), ('hardware_drawer_system', 'model_series', 'Model / series', 'text'),
        ('hardware_storage_system', 'model_series', 'Model / series', 'text'), ('hardware_door_system', 'model_series', 'Model / series', 'text'), ('hardware_furniture_system', 'model_series', 'Model / series', 'text'),
        ('hardware_electrical_component', 'model_series', 'Model / series', 'text'),
        ('purchased_fabricated_component', 'component_type', 'Component type', 'text'), ('packaging_material', 'packaging_type', 'Packaging type', 'text')
)
insert into public.reference_material_family_attributes (
    family_id, attribute_code, attribute_name, attribute_role, value_type, required, sort_order
)
select family.family_id, attribute_code, attribute_name, 'primary', value_type, true, 10
from primary_attributes
join public.reference_material_families family using (family_code)
on conflict (family_id, attribute_code) do update set
    attribute_name = excluded.attribute_name,
    attribute_role = excluded.attribute_role,
    value_type = excluded.value_type,
    required = excluded.required,
    sort_order = excluded.sort_order;

with secondary_template (
    entity_role_code, production_department_code, attribute_code, attribute_name, value_type, sort_order
) as (
    values
        ('material', 'wood', 'brand', 'Brand', 'text', 20),
        ('material', 'wood', 'construction', 'Construction', 'text', 30),
        ('material', 'wood', 'finish', 'Finish', 'text', 40),
        ('material', 'wood', 'surface', 'Surface', 'text', 50),
        ('material', 'wood', 'colour', 'Colour', 'text', 60),
        ('material', 'wood', 'dimensions', 'Dimensions', 'dimension', 70),
        ('material', 'metal', 'metal_type', 'Metal type', 'text', 20),
        ('material', 'metal', 'alloy', 'Alloy', 'text', 30),
        ('material', 'metal', 'technical_grade', 'Technical grade', 'text', 40),
        ('material', 'metal', 'finish', 'Finish', 'text', 50),
        ('material', 'metal', 'surface', 'Surface', 'text', 60),
        ('material', 'metal', 'coating', 'Coating', 'text', 70),
        ('material', 'metal', 'length', 'Length', 'dimension', 80),
        ('material', 'glass_plastics', 'brand', 'Brand', 'text', 20),
        ('material', 'glass_plastics', 'construction', 'Construction', 'text', 30),
        ('material', 'glass_plastics', 'finish', 'Finish', 'text', 40),
        ('material', 'glass_plastics', 'surface', 'Surface', 'text', 50),
        ('material', 'glass_plastics', 'colour', 'Colour', 'text', 60),
        ('material', 'glass_plastics', 'dimensions', 'Dimensions', 'dimension', 70),
        ('material', 'stone', 'brand', 'Brand', 'text', 20),
        ('material', 'stone', 'stone_type', 'Stone type', 'text', 30),
        ('material', 'stone', 'finish', 'Finish', 'text', 40),
        ('material', 'stone', 'surface_treatment', 'Surface treatment', 'text', 50),
        ('material', 'stone', 'colour', 'Colour', 'text', 60),
        ('material', 'stone', 'veining', 'Veining', 'text', 70),
        ('material', 'stone', 'dimensions', 'Dimensions', 'dimension', 80),
        ('material', 'coating', 'brand', 'Brand', 'text', 20),
        ('material', 'coating', 'chemistry', 'Chemistry', 'text', 30),
        ('material', 'coating', 'substrate', 'Substrate', 'text', 40),
        ('material', 'coating', 'sheen', 'Sheen', 'text', 50),
        ('material', 'coating', 'colour', 'Colour', 'text', 60),
        ('hardware', null, 'brand', 'Brand', 'text', 20),
        ('hardware', null, 'construction', 'Construction', 'text', 30),
        ('hardware', null, 'finish', 'Finish', 'text', 40),
        ('hardware', null, 'colour', 'Colour', 'text', 50)
)
insert into public.reference_material_family_attributes (
    family_id, attribute_code, attribute_name, attribute_role, value_type, required, sort_order
)
select family.family_id, template.attribute_code, template.attribute_name,
    'secondary', template.value_type, false, template.sort_order
from public.reference_material_families family
join secondary_template template on template.entity_role_code = family.entity_role_code
    and template.production_department_code is not distinct from family.production_department_code
where not exists (
    select 1 from public.reference_material_family_attributes existing
    where existing.family_id = family.family_id
      and existing.attribute_code = template.attribute_code
)
on conflict (family_id, attribute_code) do nothing;

with operation_seed (family_code, operation_code) as (
    values
        ('mdf_hdf', 'panel_material_handling'), ('mdf_hdf', 'panel_saw_cutting'), ('mdf_hdf', 'cnc_router_profile_cutting'), ('mdf_hdf', 'cnc_vertical_drilling'), ('mdf_hdf', 'cnc_horizontal_drilling'), ('mdf_hdf', 'cnc_grooving'), ('mdf_hdf', 'cnc_pocketing'), ('mdf_hdf', 'manual_panel_cutting'), ('mdf_hdf', 'manual_drilling'), ('mdf_hdf', 'manual_routing'), ('mdf_hdf', 'edge_banding'), ('mdf_hdf', 'veneer_lamination'), ('mdf_hdf', 'wood_sanding'), ('mdf_hdf', 'finish_surface_preparation'), ('mdf_hdf', 'wood_priming'), ('mdf_hdf', 'wood_lacquering'), ('mdf_hdf', 'wet_spray_painting'),
        ('faced_mdf', 'panel_material_handling'), ('faced_mdf', 'panel_saw_cutting'), ('faced_mdf', 'cnc_router_profile_cutting'), ('faced_mdf', 'cnc_vertical_drilling'), ('faced_mdf', 'cnc_horizontal_drilling'), ('faced_mdf', 'cnc_grooving'), ('faced_mdf', 'cnc_pocketing'), ('faced_mdf', 'manual_panel_cutting'), ('faced_mdf', 'manual_drilling'), ('faced_mdf', 'manual_routing'), ('faced_mdf', 'edge_banding'), ('faced_mdf', 'veneer_lamination'), ('faced_mdf', 'wood_sanding'), ('faced_mdf', 'finish_surface_preparation'), ('faced_mdf', 'wood_priming'), ('faced_mdf', 'wood_lacquering'), ('faced_mdf', 'wet_spray_painting'),
        ('particleboard', 'panel_material_handling'), ('particleboard', 'panel_saw_cutting'), ('particleboard', 'cnc_router_profile_cutting'), ('particleboard', 'cnc_vertical_drilling'), ('particleboard', 'cnc_horizontal_drilling'), ('particleboard', 'cnc_grooving'), ('particleboard', 'cnc_pocketing'), ('particleboard', 'manual_panel_cutting'), ('particleboard', 'manual_drilling'), ('particleboard', 'manual_routing'), ('particleboard', 'edge_banding'), ('particleboard', 'veneer_lamination'), ('particleboard', 'wood_sanding'), ('particleboard', 'finish_surface_preparation'), ('particleboard', 'wood_priming'), ('particleboard', 'wood_lacquering'), ('particleboard', 'wet_spray_painting'),
        ('melamine_faced_particleboard', 'panel_material_handling'), ('melamine_faced_particleboard', 'panel_saw_cutting'), ('melamine_faced_particleboard', 'cnc_router_profile_cutting'), ('melamine_faced_particleboard', 'cnc_vertical_drilling'), ('melamine_faced_particleboard', 'cnc_horizontal_drilling'), ('melamine_faced_particleboard', 'cnc_grooving'), ('melamine_faced_particleboard', 'cnc_pocketing'), ('melamine_faced_particleboard', 'manual_panel_cutting'), ('melamine_faced_particleboard', 'manual_drilling'), ('melamine_faced_particleboard', 'manual_routing'), ('melamine_faced_particleboard', 'edge_banding'), ('melamine_faced_particleboard', 'veneer_lamination'), ('melamine_faced_particleboard', 'wood_sanding'), ('melamine_faced_particleboard', 'finish_surface_preparation'), ('melamine_faced_particleboard', 'wood_priming'), ('melamine_faced_particleboard', 'wood_lacquering'), ('melamine_faced_particleboard', 'wet_spray_painting'),
        ('plywood', 'panel_saw_cutting'), ('plywood', 'cnc_router_profile_cutting'), ('plywood', 'cnc_vertical_drilling'), ('plywood', 'cnc_horizontal_drilling'), ('plywood', 'cnc_grooving'), ('plywood', 'cnc_pocketing'), ('plywood', 'manual_panel_cutting'), ('plywood', 'manual_drilling'), ('plywood', 'manual_routing'), ('plywood', 'edge_banding'), ('plywood', 'wood_sanding'), ('plywood', 'finish_surface_preparation'), ('plywood', 'wood_priming'), ('plywood', 'wood_lacquering'), ('plywood', 'wet_spray_painting'),
        ('plywood_special', 'panel_material_handling'), ('plywood_special', 'panel_saw_cutting'), ('plywood_special', 'cnc_router_profile_cutting'), ('plywood_special', 'cnc_vertical_drilling'), ('plywood_special', 'cnc_horizontal_drilling'), ('plywood_special', 'cnc_grooving'), ('plywood_special', 'cnc_pocketing'), ('plywood_special', 'manual_panel_cutting'), ('plywood_special', 'manual_drilling'), ('plywood_special', 'manual_routing'), ('plywood_special', 'edge_banding'), ('plywood_special', 'veneer_lamination'), ('plywood_special', 'wood_sanding'), ('plywood_special', 'finish_surface_preparation'), ('plywood_special', 'wood_priming'), ('plywood_special', 'wood_lacquering'), ('plywood_special', 'wet_spray_painting'),
        ('osb', 'panel_saw_cutting'), ('osb', 'cnc_router_profile_cutting'), ('osb', 'manual_panel_cutting'), ('osb', 'manual_drilling'), ('osb', 'manual_routing'), ('osb', 'wood_sanding'),
        ('fibreboard_hardboard', 'panel_material_handling'), ('fibreboard_hardboard', 'panel_saw_cutting'), ('fibreboard_hardboard', 'cnc_router_profile_cutting'), ('fibreboard_hardboard', 'cnc_vertical_drilling'), ('fibreboard_hardboard', 'cnc_horizontal_drilling'), ('fibreboard_hardboard', 'cnc_grooving'), ('fibreboard_hardboard', 'cnc_pocketing'), ('fibreboard_hardboard', 'manual_panel_cutting'), ('fibreboard_hardboard', 'manual_drilling'), ('fibreboard_hardboard', 'manual_routing'), ('fibreboard_hardboard', 'edge_banding'), ('fibreboard_hardboard', 'veneer_lamination'), ('fibreboard_hardboard', 'wood_sanding'), ('fibreboard_hardboard', 'finish_surface_preparation'), ('fibreboard_hardboard', 'wood_priming'), ('fibreboard_hardboard', 'wood_lacquering'), ('fibreboard_hardboard', 'wet_spray_painting'),
        ('lightweight_sandwich_panel', 'panel_saw_cutting'), ('lightweight_sandwich_panel', 'cnc_router_profile_cutting'), ('lightweight_sandwich_panel', 'manual_panel_cutting'), ('lightweight_sandwich_panel', 'manual_routing'), ('lightweight_sandwich_panel', 'edge_banding'),
        ('hpl_cpl', 'panel_material_handling'), ('hpl_cpl', 'panel_saw_cutting'), ('hpl_cpl', 'cnc_router_profile_cutting'), ('hpl_cpl', 'manual_panel_cutting'), ('hpl_cpl', 'manual_routing'), ('hpl_cpl', 'edge_banding'),
        ('compact_laminate', 'panel_material_handling'), ('compact_laminate', 'panel_saw_cutting'), ('compact_laminate', 'cnc_router_profile_cutting'), ('compact_laminate', 'manual_panel_cutting'), ('compact_laminate', 'manual_drilling'), ('compact_laminate', 'manual_routing'), ('compact_laminate', 'edge_banding'),
        ('wood_veneer', 'veneer_lamination'), ('wood_veneer', 'wood_sanding'), ('wood_veneer', 'finish_surface_preparation'), ('wood_veneer', 'wood_staining'), ('wood_veneer', 'wood_priming'), ('wood_veneer', 'wood_lacquering'), ('wood_veneer', 'wet_spray_painting'),
        ('edge_banding', 'edge_banding'),
        ('timber_solid_wood_panel', 'solid_wood_ripping'), ('timber_solid_wood_panel', 'solid_wood_crosscutting'), ('timber_solid_wood_panel', 'solid_wood_jointing_planing'), ('timber_solid_wood_panel', 'solid_wood_profiling'), ('timber_solid_wood_panel', 'solid_wood_glueup'), ('timber_solid_wood_panel', 'cnc_router_profile_cutting'), ('timber_solid_wood_panel', 'cnc_vertical_drilling'), ('timber_solid_wood_panel', 'cnc_horizontal_drilling'), ('timber_solid_wood_panel', 'cnc_grooving'), ('timber_solid_wood_panel', 'cnc_pocketing'), ('timber_solid_wood_panel', 'manual_drilling'), ('timber_solid_wood_panel', 'manual_routing'), ('timber_solid_wood_panel', 'wood_sanding'), ('timber_solid_wood_panel', 'finish_surface_preparation'), ('timber_solid_wood_panel', 'wood_staining'), ('timber_solid_wood_panel', 'wood_priming'), ('timber_solid_wood_panel', 'wood_lacquering'), ('timber_solid_wood_panel', 'wet_spray_painting'),
        ('sheet_metal', 'sheet_laser_cutting'), ('sheet_metal', 'sheet_shearing'), ('sheet_metal', 'metal_punching'), ('sheet_metal', 'sheet_metal_bending'), ('sheet_metal', 'metal_drilling'), ('sheet_metal', 'metal_milling'), ('sheet_metal', 'mig_mag_welding'), ('sheet_metal', 'tig_welding'), ('sheet_metal', 'metal_grinding'), ('sheet_metal', 'metal_polishing'), ('sheet_metal', 'finish_surface_preparation'), ('sheet_metal', 'wet_spray_painting'), ('sheet_metal', 'powder_coating_preparation'), ('sheet_metal', 'powder_coating_application'), ('sheet_metal', 'sandblasting'), ('sheet_metal', 'galvanizing'),
        ('metal_tube', 'metal_profile_cutting'), ('metal_tube', 'metal_drilling'), ('metal_tube', 'metal_milling'), ('metal_tube', 'metal_profile_bending'), ('metal_tube', 'metal_rolling'), ('metal_tube', 'mig_mag_welding'), ('metal_tube', 'tig_welding'), ('metal_tube', 'metal_grinding'), ('metal_tube', 'metal_polishing'), ('metal_tube', 'finish_surface_preparation'), ('metal_tube', 'wet_spray_painting'), ('metal_tube', 'powder_coating_preparation'), ('metal_tube', 'powder_coating_application'), ('metal_tube', 'sandblasting'), ('metal_tube', 'galvanizing'),
        ('metal_profile_angle_channel', 'metal_profile_cutting'), ('metal_profile_angle_channel', 'metal_drilling'), ('metal_profile_angle_channel', 'metal_milling'), ('metal_profile_angle_channel', 'metal_profile_bending'), ('metal_profile_angle_channel', 'metal_rolling'), ('metal_profile_angle_channel', 'mig_mag_welding'), ('metal_profile_angle_channel', 'tig_welding'), ('metal_profile_angle_channel', 'metal_grinding'), ('metal_profile_angle_channel', 'metal_polishing'), ('metal_profile_angle_channel', 'finish_surface_preparation'), ('metal_profile_angle_channel', 'wet_spray_painting'), ('metal_profile_angle_channel', 'powder_coating_preparation'), ('metal_profile_angle_channel', 'powder_coating_application'), ('metal_profile_angle_channel', 'sandblasting'), ('metal_profile_angle_channel', 'galvanizing'),
        ('metal_flat_bar', 'metal_profile_cutting'), ('metal_flat_bar', 'metal_drilling'), ('metal_flat_bar', 'metal_milling'), ('metal_flat_bar', 'metal_profile_bending'), ('metal_flat_bar', 'metal_rolling'), ('metal_flat_bar', 'mig_mag_welding'), ('metal_flat_bar', 'tig_welding'), ('metal_flat_bar', 'metal_grinding'), ('metal_flat_bar', 'metal_polishing'), ('metal_flat_bar', 'finish_surface_preparation'), ('metal_flat_bar', 'wet_spray_painting'), ('metal_flat_bar', 'powder_coating_preparation'), ('metal_flat_bar', 'powder_coating_application'), ('metal_flat_bar', 'sandblasting'), ('metal_flat_bar', 'galvanizing'),
        ('metal_round_bar_rod_wire', 'metal_profile_cutting'), ('metal_round_bar_rod_wire', 'metal_drilling'), ('metal_round_bar_rod_wire', 'metal_milling'), ('metal_round_bar_rod_wire', 'metal_profile_bending'), ('metal_round_bar_rod_wire', 'metal_rolling'), ('metal_round_bar_rod_wire', 'mig_mag_welding'), ('metal_round_bar_rod_wire', 'tig_welding'), ('metal_round_bar_rod_wire', 'metal_grinding'), ('metal_round_bar_rod_wire', 'metal_polishing'), ('metal_round_bar_rod_wire', 'finish_surface_preparation'), ('metal_round_bar_rod_wire', 'wet_spray_painting'), ('metal_round_bar_rod_wire', 'powder_coating_preparation'), ('metal_round_bar_rod_wire', 'powder_coating_application'), ('metal_round_bar_rod_wire', 'sandblasting'), ('metal_round_bar_rod_wire', 'galvanizing'),
        ('glass', 'glass_cutting'), ('glass', 'glass_drilling'), ('glass', 'glass_edge_processing'), ('glass', 'glass_tempering'),
        ('mirror', 'glass_cutting'), ('mirror', 'glass_drilling'), ('mirror', 'glass_edge_processing'),
        ('acrylic_pmma', 'acrylic_cnc_machining'), ('acrylic_pmma', 'acrylic_laser_cutting'), ('acrylic_pmma', 'acrylic_thermoforming'),
        ('aluminium_composite_panel', 'panel_saw_cutting'), ('aluminium_composite_panel', 'cnc_router_profile_cutting'), ('aluminium_composite_panel', 'manual_panel_cutting'), ('aluminium_composite_panel', 'manual_routing'),
        ('composite_sandwich_panel', 'panel_saw_cutting'), ('composite_sandwich_panel', 'cnc_router_profile_cutting'), ('composite_sandwich_panel', 'manual_panel_cutting'), ('composite_sandwich_panel', 'manual_routing'),
        ('natural_stone_slab', 'stone_cutting'), ('natural_stone_slab', 'stone_cutout'), ('natural_stone_slab', 'stone_edge_processing'), ('natural_stone_slab', 'stone_seaming'),
        ('engineered_quartz_mineral_hybrid', 'stone_cutting'), ('engineered_quartz_mineral_hybrid', 'stone_cutout'), ('engineered_quartz_mineral_hybrid', 'stone_edge_processing'), ('engineered_quartz_mineral_hybrid', 'stone_seaming'),
        ('sintered_ultra_compact_surface', 'stone_cutting'), ('sintered_ultra_compact_surface', 'stone_cutout'), ('sintered_ultra_compact_surface', 'stone_edge_processing'), ('sintered_ultra_compact_surface', 'stone_seaming'),
        ('porcelain_ceramic_slab', 'stone_cutting'), ('porcelain_ceramic_slab', 'stone_cutout'), ('porcelain_ceramic_slab', 'stone_edge_processing'), ('porcelain_ceramic_slab', 'stone_seaming'),
        ('solid_surface', 'stone_cutting'), ('solid_surface', 'stone_cutout'), ('solid_surface', 'stone_edge_processing'), ('solid_surface', 'stone_seaming'),
        ('terrazzo_engineered_agglomerate', 'stone_cutting'), ('terrazzo_engineered_agglomerate', 'stone_cutout'), ('terrazzo_engineered_agglomerate', 'stone_edge_processing'), ('terrazzo_engineered_agglomerate', 'stone_seaming'),
        ('primer', 'finish_surface_preparation'), ('primer', 'wood_priming'), ('primer', 'wet_spray_painting'),
        ('paint_lacquer_stain', 'finish_surface_preparation'), ('paint_lacquer_stain', 'wood_staining'), ('paint_lacquer_stain', 'wood_lacquering'), ('paint_lacquer_stain', 'wet_spray_painting'),
        ('powder_coating', 'finish_surface_preparation'), ('powder_coating', 'powder_coating_preparation'), ('powder_coating', 'powder_coating_application'),
        ('hardware_hinge', 'door_front_fitting'), ('hardware_hinge', 'hardware_installation'),
        ('hardware_drawer_slide', 'drawer_assembly'), ('hardware_drawer_slide', 'hardware_installation'),
        ('hardware_connector', 'hardware_installation'), ('hardware_fastener', 'hardware_installation'), ('hardware_mounting_part', 'hardware_installation'), ('hardware_handle', 'hardware_installation'), ('hardware_leg_caster', 'hardware_installation'), ('hardware_lift_system', 'hardware_installation'), ('hardware_lock_latch', 'hardware_installation'), ('hardware_drawer_system', 'drawer_assembly'), ('hardware_drawer_system', 'hardware_installation'), ('hardware_storage_system', 'hardware_installation'), ('hardware_door_system', 'door_front_fitting'), ('hardware_door_system', 'hardware_installation'), ('hardware_furniture_system', 'hardware_installation')
)
insert into public.reference_material_family_operation_eligibilities (family_id, operation_id, active)
select family.family_id, operation.operation_id, true
from operation_seed
join public.reference_material_families family using (family_code)
join public.reference_operations operation using (operation_code)
where operation.active
on conflict (family_id, operation_id) do update set active = true;

commit;
