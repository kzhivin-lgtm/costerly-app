# Labor operation formulas v0

Status: deterministic formula specification. It consumes object facts and a
route selected by `LABOR_ROUTE_CATALOG_V0.md`. It does not call an LLM and does
not set labor prices.

## Common notation

For every line, productive labor hours are:

`hours(role) = crew * max(min_batch, setup_once + rate * quantity) / 60`

`setup_once` is charged once for the stated batch key. `rate` and `min_batch`
come from `LABOR_TIME_BASELINE_V0.md`, with the route and material-specific
row taking precedence. A formula that lacks a required fact returns `review`,
not an invented quantity.

`explicit` means stated in the source drawing or bill. `derived` means
transparently calculated from cited geometry or part facts. The Estimation
Agent selects catalog operations and physical driver quantities, but cannot
provide labor minutes or hours.

## Preproduction

| Operation | Required facts | Quantity formula | Setup / minimum rule |
| --- | --- | --- | --- |
| `site_measurement` | site zones, access condition | `q = count(site_zones)` | one visit setup; add restricted-access zone only if explicit |
| `estimate_review` | objects, drawing pages, exclusions | `q = object_count + 0.25 * drawing_page_count` | one estimate batch |
| `shop_drawing` | unique modules, drawing pages, revisions | `q = unique_module_count + 0.5 * revision_count` | one drawing-package setup |
| `cnc_programming` | CNC batch, unique toolpaths, verified reusable-program status | `q = unique_toolpath_count` | zero when subcontractor includes programming or an existing verified program is reusable |
| `sheet_nesting` | sheets, panels, grain constraints | `q = sheet_count` | one material-thickness-route batch |
| `supplier_quotation` | suppliers, external components | `q = supplier_quote_count` | zero for active deterministic supplier price |
| `quality_inspection` | completed modules and purchased critical parts | `q = completed_module_count + critical_component_count` | one delivery-batch setup |

## Panel and solid wood

| Operation | Required facts | Quantity formula | Setup / minimum rule |
| --- | --- | --- | --- |
| `panel_material_handling` | internal panels, sheets | `q = internal_part_count + sheet_count` | one material-route batch |
| `panel_saw_cutting` | cutting plan, straight cuts | `q = cut_sequence_count` | sequences derive from cutting-map class, never raw panel count |
| `cnc_router_profile_cutting` | CNC contours | `q = sum(contour_length_lm)` | shared `cnc_router_session` setup per material, thickness and tool set |
| `cnc_vertical_drilling` | explicit or derived joint and hardware pattern | `q = derived_vertical_hole_count` | shared `cnc_router_session`; hole classes come from cited part and connection facts |
| `cnc_horizontal_drilling` | explicit or derived end-hole pattern | `q = derived_horizontal_hole_count` | shared drilling-pattern session |
| `cnc_grooving` | groove geometry | `q = sum(groove_length_lm)` | shared router session by cutter and depth class |
| `cnc_pocketing` | pocket geometry and depth class | `q = sum(pocket_area_cm2) / 100` | shared router session by cutter and depth class |
| `manual_panel_cutting` | supported simple straight cuts | `q = cut_sequence_count` | one material-thickness batch, prohibited for shaped parts |
| `manual_drilling` | explicit or derived hole pattern | `q = derived_manual_hole_count` | shared manual-drilling session by hole class |
| `manual_routing` | simple manual profile/groove | `q = sum(manual_routed_length_lm)` | shared manual-routing session by cutter |
| `edge_banding` | exposed banded edges | `q = sum(banded_edge_length_lm)` | one edge-material and thickness batch |
| `veneer_lamination` | substrate faces, veneer faces | `q = sum(pressed_surface_area_sqm)` | one substrate, veneer and adhesive batch |
| `solid_wood_ripping` | raw solid stock, required sections | `q = sum(raw_stock_length_lm)` | one species and section batch |
| `solid_wood_crosscutting` | stock pieces and final lengths | `q = crosscut_count` | one species and section batch |
| `solid_wood_jointing_planing` | raw and finished section | `q = sum(planed_length_lm)` | one species and finished-section batch |
| `solid_wood_profiling` | profile path and tool profile | `q = sum(profiled_length_lm)` | one species, profile and cutter batch |
| `solid_wood_glueup` | glue joints, glued panels | `q = sum(glue_joint_length_lm)` | each separate clamping assembly gets its own setup; cure wait excluded |
| `wood_sanding` | finish area, edge/profile area, grit class | `q = flat_area_sqm + edge_profile_equivalent_area_sqm` | one finish-system and grit batch |

## Assembly

| Operation | Required facts | Quantity formula | Setup / minimum rule |
| --- | --- | --- | --- |
| `carcass_assembly` | actual structural panels and connection facts | `q = carcass_module_count` | cited part and connection facts define the work, not agent-supplied minutes |
| `drawer_assembly` | drawer type, count | `q = drawer_box_count` | one drawer-system batch |
| `door_front_fitting` | doors/fronts, hardware family | `q = door_front_count` | one front-hardware batch |
| `hardware_installation` | itemized hardware | `q = installed_hardware_count` | one hardware-family setup |
| `workshop_dry_fit` | high-risk/complex module flag | `q = dry_fit_module_count` | zero for standard low-risk modules |

## Metal fabrication

| Operation | Required facts | Quantity formula | Setup / minimum rule |
| --- | --- | --- | --- |
| `sheet_laser_cutting` | alloy, thickness, cut path, pierces | `q = cut_length_lm`, plus `pierce_count * pierce_rate` | one sheet, alloy, thickness and gas batch |
| `sheet_shearing` | alloy, thickness, straight-cut plan | `q = shear_cut_count` | one alloy, thickness and backgauge batch |
| `metal_profile_cutting` | alloy, profile section, cut list | `q = profile_cut_count` | one alloy, section and stop-length batch |
| `metal_drilling` | alloy, thickness, hole diameter/depth | `q = drilled_hole_count` | one alloy and hole-class batch; deep stainless hole requires review modifier |
| `metal_milling` | alloy, milling paths, pockets, tolerance | `q = milling_path_lm + pocket_equivalent_lm` | one alloy, tool and tolerance batch |
| `metal_punching` | alloy, thickness, punch tool, features | `q = punched_feature_count` | one punch-tool and sheet batch |
| `sheet_metal_bending` | alloy, thickness, bends, flips, tooling | `q = bend_count + flip_count * flip_equivalent` | one alloy, thickness and tool set batch |
| `metal_profile_bending` | alloy, section, bend radius and count | `q = profile_bend_count` | one alloy, section, die and radius batch |
| `metal_rolling` | alloy, section, radius, part count | `q = rolled_part_count` | one alloy, section and radius batch |
| `mig_mag_welding` | alloy, joint type, weld paths | `q = sum(mig_weld_length_lm)` | one alloy, filler and joint-position batch |
| `tig_welding` | alloy, visible/precision class, weld paths | `q = sum(tig_weld_length_lm)` | one alloy, filler and finish class batch |
| `metal_grinding` | alloy, weld/edge finish class | `q = sum(grind_length_lm)` | one abrasive and finish-class batch |
| `metal_polishing` | alloy, exposed finish area, finish grade | `q = exposed_polish_area_sqm` | one alloy and finish-grade batch |
| `metal_assembly` | actual frame members, joints and mechanical fasteners | `q = metal_subassembly_count` | one compatible frame-geometry batch |

## Glass, stone and acrylic

| Operation | Required facts | Quantity formula | Setup / minimum rule |
| --- | --- | --- | --- |
| `glass_cutting` | glass type, thickness, straight cut path | `q = glass_cut_count` | external-component route in V0 |
| `glass_edge_processing` | edge finish and length | `q = glass_edge_length_lm` | external-component route in V0 |
| `glass_drilling` | hole class and count before tempering | `q = glass_hole_count` | external-component route in V0 |
| `glass_tempering` | glass area and specification | `q = tempered_glass_area_sqm` | external-component route in V0 |
| `stone_cutting` | stone, thickness, cut plan | `q = stone_cut_length_lm` | external-component route in V0 |
| `stone_edge_processing` | edge profile and length | `q = stone_edge_length_lm` | external-component route in V0 |
| `stone_cutout` | sink/cooktop/technical cutout class | `q = stone_cutout_count` | external-component route in V0 |
| `stone_seaming` | seam type and length | `q = stone_seam_length_lm` | external-component route in V0 |
| `acrylic_cnc_machining` | thickness, contours, holes, pockets | `q = acrylic_contour_lm + hole_equivalent + pocket_equivalent` | external-component route in V0 |
| `acrylic_laser_cutting` | thickness, cut path | `q = acrylic_laser_cut_length_lm` | external-component route in V0 |
| `acrylic_thermoforming` | part, thickness, mould class | `q = thermoformed_part_count` | external-component route in V0 |

## Coating

| Operation | Required facts | Quantity formula | Setup / minimum rule |
| --- | --- | --- | --- |
| `finish_surface_preparation` | material, finish area, defect class | `q = prep_area_sqm + repair_equivalent_area_sqm` | one material and finish-system batch |
| `wood_staining` | exposed wood area and stain system | `q = stained_area_sqm` | one species and stain-system batch |
| `wood_priming` | finish area and coat count | `q = primed_area_sqm * primer_coat_count` | one material and primer-system batch |
| `wood_lacquering` | finish area and coat count | `q = lacquered_area_sqm * lacquer_coat_count` | one material and lacquer-system batch |
| `wet_spray_painting` | finish area, color, coat count | `q = painted_area_sqm * spray_coat_count` | one color and coating-system batch |
| `powder_coating_preparation` | parts, masking/fixture need | `q = powder_coated_part_count` | one color and hanging-rack batch |
| `powder_coating_application` | parts, color, coat system | `q = powder_coated_part_count` | one color and powder-system batch; cure wait excluded |
| `sandblasting` | blast area and blast class | `q = blasted_area_sqm` | one material and media batch |
| `galvanizing` | dispatch weight and batch | `q = galvanized_weight_kg` | one external or internal galvanizing batch; bath time excluded |

## Packaging, logistics and site work

| Operation | Required facts | Quantity formula | Setup / minimum rule |
| --- | --- | --- | --- |
| `protective_packaging` | delivery modules and fragility class | `q = package_count` | one delivery batch |
| `vehicle_loading` | packages, weight, vehicle access | `q = package_count + heavy_package_equivalent` | one vehicle load |
| `delivery_trip` | route distance, visit count, traffic class | `q = route_distance_km` | one trip setup; traffic modifier must be explicit |
| `manual_site_carry` | packages, floors, carry distance class | `q = package_count * floor_equivalent` | one unloading-site batch |
| `site_protection` | protected site area | `q = protected_area_sqm` | one site visit |
| `cabinet_installation` | cabinet modules, wall/floor conditions | `q = installed_cabinet_count` | one site and room batch |
| `countertop_installation` | countertop pieces, seams, weight class | `q = countertop_piece_count + seam_equivalent` | one site and countertop batch; supplier install suppresses it |
| `metalwork_installation` | assemblies, anchors, access class | `q = installed_metalwork_count` | one site and installation batch |
| `glass_mirror_installation` | panels, area, access class | `q = installed_glass_area_sqm` | one site and glass batch |
| `site_anchoring` | anchors, substrate class | `q = anchor_count` | one substrate and anchor-class batch |
| `site_sealing` | sealed interface length | `q = seal_length_lm` | one sealant-system batch |
| `led_low_voltage_installation` | LED length, drivers, connection points | `q = led_length_lm + connection_equivalent` | one LED-system batch; mains work is review |
| `final_adjustment` | moving hardware and installed modules | `q = adjusted_hardware_count + module_equivalent` | one site visit |
| `site_cleanup` | work zones and visits | `q = cleanup_zone_count` | one site visit |

## Deterministic quantity derivation rules

1. The agent decomposes visible geometry into parts, fronts, shelves, drawers,
   connection facts, hardware and exposed edges.
2. Hole and fastener quantities must be explicit or transparently derived from
   cited part and connection facts.
3. Geometry supplies length and area drivers only where the drawing contains
   dimensions. Missing dimensions produce `review`, never a hidden assumed
   measurement.
4. A formula emits source facts, derived facts, selected route, operation code,
   baseline version, confidence, and a human-readable explanation with every
   labor line.
