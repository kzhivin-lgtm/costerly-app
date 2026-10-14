# Israel Reference Default Policy Matrix, 3.17.4.1

Status: policy baseline generated from the Family registry and owner-confirmed defaults.

## Contract

- Every Israel Reference row is an authoritative canonical market position.
- A Company row links many-to-one to one Israel position when Family and Pricing Key match.
- Family plus Pricing Key is the complete matching depth. Secondary attributes describe the position but do not create another price class.
- A default completes missing Pricing Key facts only after Family is proven. It never infers Family.
- Hardware uses a deterministic package-selection branch, Company first and Israel second.

Live snapshot: 54 active families, 4 covered by canonical Israel positions

| Family | Pricing Key | Default policy | Confirmed baseline | Purchase format | Catalog state |
| --- | --- | --- | --- | --- | --- |
| acrylic_pmma | thickness | Pricing-Key default after family is proven | pending | required | no canonical model |
| aluminium_composite_panel | thickness | Pricing-Key default after family is proven | pending | required | no canonical model |
| compact_laminate | thickness | Pricing-Key default after family is proven | thickness=12 | required | no approved purchase format |
| composite_sandwich_panel | thickness | Pricing-Key default after family is proven | pending | required | no canonical model |
| decorative_film_foil | width | Pricing-Key default after family is proven | pending | not_required | no canonical model |
| edge_banding | width_thickness | Pricing-Key default after family is proven | width=22, thickness=0.8 | not_required | models lack complete Pricing Key |
| engineered_quartz_mineral_hybrid | thickness | Pricing-Key default after family is proven | thickness=20 | required | no approved purchase format |
| faced_mdf | thickness | Pricing-Key default after family is proven | thickness=17 | standard_sheet_2400x1220 | no approved purchase format |
| fibreboard_hardboard | thickness | Pricing-Key default after family is proven | thickness=3 | standard_sheet_2400x1220 | no approved purchase format |
| filler_hardener_thinner | chemistry_product_type | Pricing-Key default after family is proven | pending | not_required | covered |
| glass | thickness | Pricing-Key default after family is proven | pending | required | no approved purchase format |
| hardware_connector | none | lowest compatible package, Company first, then Israel | pending | not_required | no active package price |
| hardware_door_system | none | lowest compatible package, Company first, then Israel | pending | not_required | no canonical model |
| hardware_drawer_slide | nominal_length | lowest compatible package, Company first, then Israel | pending | not_required | no active package price |
| hardware_drawer_system | none | lowest compatible package, Company first, then Israel | pending | not_required | no canonical model |
| hardware_electrical_component | none | lowest compatible package, Company first, then Israel | pending | not_required | no active package price |
| hardware_fastener | none | lowest compatible package, Company first, then Israel | pending | not_required | no active package price |
| hardware_furniture_system | none | lowest compatible package, Company first, then Israel | pending | not_required | no active package price |
| hardware_handle | none | lowest compatible package, Company first, then Israel | pending | not_required | no canonical model |
| hardware_hinge | none | lowest compatible package, Company first, then Israel | pending | not_required | no active package price |
| hardware_leg_caster | none | lowest compatible package, Company first, then Israel | pending | not_required | no canonical model |
| hardware_lift_system | none | lowest compatible package, Company first, then Israel | pending | not_required | no canonical model |
| hardware_lock_latch | none | lowest compatible package, Company first, then Israel | pending | not_required | no canonical model |
| hardware_mounting_part | none | lowest compatible package, Company first, then Israel | pending | not_required | no canonical model |
| hardware_storage_system | none | lowest compatible package, Company first, then Israel | pending | not_required | no canonical model |
| hpl_cpl | thickness | Pricing-Key default after family is proven | pending | required | no approved purchase format |
| lightweight_sandwich_panel | thickness | Pricing-Key default after family is proven | pending | standard_sheet_2400x1220 | no approved purchase format |
| mdf_hdf | thickness | Pricing-Key default after family is proven | thickness=17 | standard_sheet_2400x1220 | no approved purchase format |
| melamine_faced_particleboard | thickness | Pricing-Key default after family is proven | thickness=17 | standard_sheet_2400x1220 | no approved purchase format |
| metal_flat_bar | width_thickness, metal_type | Pricing-Key default after family is proven | metal_type=carbon steel, width=30, thickness=1.5 | required | no canonical model |
| metal_profile_angle_channel | section_profile, metal_type, wall_thickness | Pricing-Key default after family is proven | metal_type=carbon steel, section_profile=angle | required | models lack complete Pricing Key |
| metal_round_bar_rod_wire | diameter, metal_type | Pricing-Key default after family is proven | pending | required | no canonical model |
| metal_tube | section_profile, metal_type, wall_thickness | Pricing-Key default after family is proven | metal_type=carbon steel, section_profile=round_tube | required | models lack complete Pricing Key |
| mirror | thickness | Pricing-Key default after family is proven | pending | required | no approved purchase format |
| natural_stone_slab | thickness, stone_type | Pricing-Key default after family is proven | stone_type=marble, thickness=20 | required | models lack complete Pricing Key |
| osb | thickness | Pricing-Key default after family is proven | thickness=18 | standard_sheet_2400x1220 | no approved purchase format |
| packaging_material | packaging_type | standard Israel position after package type is known | pending | not_required | covered |
| paint_lacquer_stain | coating_system | Pricing-Key default after family is proven | coating_system=standard paint | not_required | default baseline pending |
| particleboard | thickness | Pricing-Key default after family is proven | thickness=17 | standard_sheet_2400x1220 | no approved purchase format |
| plywood | thickness | Pricing-Key default after family is proven | thickness=17 | standard_sheet_2400x1220 | no approved purchase format |
| plywood_special | thickness | Pricing-Key default after family is proven | pending | standard_sheet_2400x1220 | no approved purchase format |
| polycarbonate_petg_pvc_abs | thickness | Pricing-Key default after family is proven | pending | required | no canonical model |
| porcelain_ceramic_slab | thickness | Pricing-Key default after family is proven | thickness=12 | required | no approved purchase format |
| powder_coating | coating_system | Pricing-Key default after family is proven | coating_system=standard semi-matte powder coating | not_required | default baseline pending |
| primer | coating_system | Pricing-Key default after family is proven | pending | not_required | covered |
| purchased_fabricated_component | component_type | no generic default, component type remains required | pending | not_required | covered |
| sheet_metal | thickness, metal_type | Pricing-Key default after family is proven | pending | required | no canonical model |
| sheet_plastic | thickness | Pricing-Key default after family is proven | pending | required | no approved purchase format |
| sintered_ultra_compact_surface | thickness | Pricing-Key default after family is proven | thickness=12 | required | no approved purchase format |
| solid_surface | thickness | Pricing-Key default after family is proven | thickness=12 | required | no approved purchase format |
| terrazzo_engineered_agglomerate | thickness | Pricing-Key default after family is proven | thickness=20 | required | no canonical model |
| timber_solid_wood_panel | species, dimensions | Pricing-Key default after family is proven | pending | required | models lack complete Pricing Key |
| vinyl_film | width | Pricing-Key default after family is proven | pending | not_required | no canonical model |
| wood_veneer | species | Pricing-Key default after family is proven | species=oak, secondary_thickness_mm=0.6 | required | no approved purchase format |
