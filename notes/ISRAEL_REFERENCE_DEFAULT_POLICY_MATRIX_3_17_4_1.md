# Israel Reference Default Policy Matrix, 3.17.4.1

Status: proposed catalog-rebuild baseline. This document is generated from the live Israel Reference catalog plus owner-confirmed default decisions.

## Contract

- A catalog identity ends at the Family Pricing Key. Secondary attributes are descriptive and do not multiply identities.
- A Family Default is allowed only after the family is proven. It fills absent Pricing Key facts, then the normal Company-first, Israel-second resolver runs.
- A generic hardware default means the lowest compatible active package candidate, not an invented component specification.
- Missing family stays review-visible. A fully specified uncommon item absent from both catalogs is an Assumption Fallback and a Catalog Gap, never a Family Default.

Live audit summary: 54 active families, 2 fully covered under the current default-anchor model

## Family matrix

| Family | Pricing Key | Default mode | Owner-confirmed baseline | Purchase format | Live status |
| --- | --- | --- | --- | --- | --- |
| acrylic_pmma | thickness | Israel-backed Pricing Key default | pending | required | no active default anchor |
| aluminium_composite_panel | thickness | Israel-backed Pricing Key default | pending | required | no active Israel identity |
| compact_laminate | thickness | Israel-backed Pricing Key default | thickness_mm=12 | required | no active default anchor |
| composite_sandwich_panel | thickness | Israel-backed Pricing Key default | pending | required | no active Israel identity |
| decorative_film_foil | width | Israel-backed Pricing Key default | pending | not_required | no active Israel identity |
| edge_banding | width_thickness | Israel-backed Pricing Key default | width_mm=22, thickness_mm=0.8 | not_required | no active default anchor |
| engineered_quartz_mineral_hybrid | thickness | Israel-backed Pricing Key default | thickness_mm=20 | required | no active default anchor |
| faced_mdf | thickness | Israel-backed Pricing Key default | thickness_mm=17 | standard_sheet_2400x1220 | no active Israel identity |
| fibreboard_hardboard | thickness | Israel-backed Pricing Key default | thickness_mm=3 | standard_sheet_2400x1220 | no active default anchor |
| filler_hardener_thinner | chemistry_product_type | Israel-backed Pricing Key default | pending | not_required | no active Israel identity |
| glass | thickness | Israel-backed Pricing Key default | pending | required | no active default anchor |
| hardware_connector | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_door_system | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_drawer_slide | nominal_length | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_drawer_system | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_electrical_component | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_fastener | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_furniture_system | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_handle | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_hinge | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_leg_caster | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_lift_system | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_lock_latch | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_mounting_part | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hardware_storage_system | none | lowest compatible package candidate, Company first, then Israel | pending | not_required | no active Israel identity |
| hpl_cpl | thickness | Israel-backed Pricing Key default | pending | required | no active Israel identity |
| lightweight_sandwich_panel | thickness | Israel-backed Pricing Key default | pending | standard_sheet_2400x1220 | no active Israel identity |
| mdf_hdf | thickness | Israel-backed Pricing Key default | thickness_mm=17 | standard_sheet_2400x1220 | covered |
| melamine_faced_particleboard | thickness | Israel-backed Pricing Key default | thickness_mm=17 | standard_sheet_2400x1220 | no active Israel identity |
| metal_flat_bar | width_thickness, metal_type | Israel-backed Pricing Key default | metal_type=carbon steel, width_mm=30, thickness_mm=1.5 | required | no active Israel identity |
| metal_profile_angle_channel | section_profile, metal_type, wall_thickness | Israel-backed Pricing Key default | metal_type=carbon steel, section_profile=angle 30×30 mm, secondary_wall_thickness_mm=1.5 | required | no active Israel identity |
| metal_round_bar_rod_wire | diameter, metal_type | Israel-backed Pricing Key default | pending | required | no active Israel identity |
| metal_tube | section_profile, metal_type, wall_thickness | Israel-backed Pricing Key default | metal_type=carbon steel, section_profile=round tube Ø20 mm, secondary_wall_thickness_mm=1.5 | required | no active Israel identity |
| mirror | thickness | Israel-backed Pricing Key default | pending | required | no active Israel identity |
| natural_stone_slab | thickness, stone_type | Israel-backed Pricing Key default | stone_type=marble, thickness_mm=20 | required | identity has incomplete Pricing Key |
| osb | thickness | Israel-backed Pricing Key default | thickness_mm=18 | standard_sheet_2400x1220 | no active default anchor |
| packaging_material | packaging_type | standard Israel candidate after package type is known | pending | not_required | no active Israel identity |
| paint_lacquer_stain | coating_system | Israel-backed Pricing Key default | coating_system=standard paint | not_required | no active Israel identity |
| particleboard | thickness | Israel-backed Pricing Key default | thickness_mm=17 | standard_sheet_2400x1220 | no active default anchor |
| plywood | thickness | Israel-backed Pricing Key default | thickness_mm=17 | standard_sheet_2400x1220 | covered |
| plywood_special | thickness | Israel-backed Pricing Key default | pending | standard_sheet_2400x1220 | no active Israel identity |
| polycarbonate_petg_pvc_abs | thickness | Israel-backed Pricing Key default | pending | required | no active default anchor |
| porcelain_ceramic_slab | thickness | Israel-backed Pricing Key default | thickness_mm=12 | required | no active default anchor |
| powder_coating | coating_system | Israel-backed Pricing Key default | coating_system=standard semi-matte powder coating | not_required | no active Israel identity |
| primer | coating_system | Israel-backed Pricing Key default | pending | not_required | no active Israel identity |
| purchased_fabricated_component | component_type | no generic default, component type remains required | pending | not_required | no active Israel identity |
| sheet_metal | thickness, metal_type | Israel-backed Pricing Key default | pending | required | no active Israel identity |
| sheet_plastic | thickness | Israel-backed Pricing Key default | pending | required | no active default anchor |
| sintered_ultra_compact_surface | thickness | Israel-backed Pricing Key default | thickness_mm=12 | required | no active default anchor |
| solid_surface | thickness | Israel-backed Pricing Key default | thickness_mm=12 | required | no active default anchor |
| terrazzo_engineered_agglomerate | thickness | Israel-backed Pricing Key default | thickness_mm=20 | required | no active Israel identity |
| timber_solid_wood_panel | species, dimensions | Israel-backed Pricing Key default | pending | required | no active Israel identity |
| vinyl_film | width | Israel-backed Pricing Key default | pending | not_required | no active Israel identity |
| wood_veneer | species | Israel-backed Pricing Key default | species=oak, secondary_thickness_mm=0.6 | required | identity has incomplete Pricing Key |
