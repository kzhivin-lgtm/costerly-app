# Labor route catalog v0

Status: deterministic route specification. No production code or production
seed is created by this document.

## Route contract

For every triggered operation, the engine selects exactly one route:

- `in_house_machine`: an approved Company Profile capability exists.
- `in_house_manual`: qualified internal role, no conflicting machine route.
- `external_component`: the company buys the completed fabrication or service.
- `site`: work occurs at installation and consumes installer labor.
- `review`: required facts or an approved route are missing.

`external_component` suppresses every matching internal fabrication operation.
It never silently creates a company labor or machine line. `review` is not an
error, it is an explicit stop against false precision.

## Preproduction

| Operation | Trigger | Preferred route | Fallback or exclusion | Batch key |
| --- | --- | --- | --- | --- |
| `site_measurement` | site-specific object or installation | `site` | exclude for repeat measured site | project + site |
| `estimate_review` | every estimate | `in_house_manual` | never external | estimate |
| `shop_drawing` | fabrication detail beyond source drawing | `in_house_manual` | `review` if design scope unknown | object family |
| `cnc_programming` | internal CNC route with non-template work | `in_house_manual` | exclude for subcontractor price that includes programming | CNC batch |
| `sheet_nesting` | sheet cutting on internal CNC or panel saw | `in_house_manual` | exclude when supplier delivers cut-to-size parts | material + thickness + route |
| `supplier_quotation` | external component needs quote | `in_house_manual` | exclude where active supplier price is deterministic | supplier + service |
| `quality_inspection` | fabricated or purchased critical component | `in_house_manual` | exclude only for non-delivered preliminary estimate | delivery batch |

## Wood and panel processing

| Operation | Trigger | Preferred route | Fallback or exclusion | Batch key |
| --- | --- | --- | --- | --- |
| `panel_material_handling` | internal panel processing | `in_house_manual` | exclude for bought cut-to-size components | material + route |
| `panel_saw_cutting` | rectangular panel cuts | `in_house_machine:wood_panel_saw` | `manual_panel_cutting` only for low-volume simple rectangles, otherwise CNC or external | material + thickness + cutting plan |
| `cnc_router_profile_cutting` | shaped panel contour or internal CNC profile | `in_house_machine:wood_cnc_router` | `external_component` via CNC contractor | material + thickness + tooling |
| `cnc_vertical_drilling` | CNC-compatible face-hole pattern | `in_house_machine:wood_cnc_router` | manual drilling only for low quantity standard holes, otherwise external CNC | material + thickness + drilling pattern |
| `cnc_horizontal_drilling` | end or horizontal-hole pattern | `in_house_machine:wood_cnc_router` | manual drilling only for low quantity standard holes, otherwise `review` | material + thickness + drilling pattern |
| `cnc_grooving` | groove, dado or channel | `in_house_machine:wood_cnc_router` | manual routing for short simple groove, otherwise external CNC | material + thickness + cutter |
| `cnc_pocketing` | recess or pocket | `in_house_machine:wood_cnc_router` | external CNC. No manual default | material + thickness + cutter |
| `manual_panel_cutting` | low-volume supported straight cut | `in_house_manual` | forbidden for shaped geometry or high-volume nested sheet work | material + thickness |
| `manual_drilling` | low-volume standard holes | `in_house_manual` | exclude when matching CNC drilling route selected | material + hole class |
| `manual_routing` | short simple profile or groove | `in_house_manual` | exclude when matching CNC route selected | material + cutter |
| `edge_banding` | exposed panel edge needs band | `in_house_machine:wood_edge_bander` | `external_component` or `review`, never silently hand-band production work | edge material + thickness |
| `veneer_lamination` | veneer/laminate must be pressed | `in_house_machine:wood_veneer_press` | external pressed panel, otherwise `review` | substrate + veneer + adhesive |
| `solid_wood_ripping` | solid stock must be sized to width | `in_house_machine:wood_solid_preparation` | manual saw only for minor trim, otherwise external prepared stock | species + section |
| `solid_wood_crosscutting` | solid stock must be sized to length | `in_house_machine:wood_solid_preparation` | manual saw only for minor trim | species + section |
| `solid_wood_jointing_planing` | stock requires true faces/edges or final section | `in_house_machine:wood_solid_preparation` | external prepared timber, otherwise `review` | species + section |
| `solid_wood_profiling` | moulded or curved profile | `in_house_machine:wood_solid_preparation` | external profile service, otherwise `review` | species + profile + cutter |
| `solid_wood_glueup` | laminated solid panel or assembly | `in_house_manual` | external laminated panel if purchased | species + section + adhesive |
| `wood_sanding` | exposed wood or paint-prep surface | `in_house_machine:wood_wide_belt_sander` for flat stock | `in_house_manual` for edges, profiles and touch-up | finish system + grit class |

## Assembly

| Operation | Trigger | Preferred route | Fallback or exclusion | Batch key |
| --- | --- | --- | --- | --- |
| `carcass_assembly` | cabinet carcass/module | `in_house_manual` | exclude if bought assembled module | module archetype |
| `drawer_assembly` | drawer box/system | `in_house_manual` | exclude if supplier supplies assembled drawer | drawer system |
| `door_front_fitting` | door or front present | `in_house_manual` | site adjustment belongs to `final_adjustment` | front + hardware family |
| `hardware_installation` | hardware item has internal installation scope | `in_house_manual` | exclude hardware supplied pre-fitted | hardware family |
| `workshop_dry_fit` | complex fit, nonstandard joinery, or high-risk assembly | `in_house_manual` | exclude simple standard modules | object |

## Metal processing

| Operation | Trigger | Preferred route | Fallback or exclusion | Batch key |
| --- | --- | --- | --- | --- |
| `sheet_laser_cutting` | sheet part needs contour/cutouts | `in_house_machine:metal_sheet_laser` | `external_component` via accepted laser calculator | material + thickness + sheet |
| `sheet_shearing` | thin sheet, straight cuts only | `in_house_manual` | external laser for complex or precision work; `review` for unsupported thickness | material + thickness + cut plan |
| `metal_profile_cutting` | tube, bar, or profile cut to length | `in_house_machine:metal_profile_saw` | `in_house_manual` for minor trim, external cut-to-length profile otherwise | alloy + profile section |
| `metal_drilling` | standard drilled metal hole | `in_house_manual` | exclude when punching, laser, or milling already creates feature | alloy + thickness + hole class |
| `metal_milling` | slot, pocket, face or precision feature | `in_house_manual` | external machining if capability or tolerances are unknown | alloy + feature + tool |
| `metal_punching` | repeat sheet holes/features | `in_house_machine:metal_punch_press` | laser for low-volume/complex work, otherwise `review` | material + thickness + tool |
| `sheet_metal_bending` | sheet bend | `in_house_machine:metal_press_brake` | `external_component` for press-brake work | alloy + thickness + tooling |
| `metal_profile_bending` | tube/bar/profile bend | `in_house_machine:metal_profile_bender` | external formed profile, otherwise `review` | alloy + section + radius |
| `metal_rolling` | rolled sheet/profile radius | `in_house_machine:metal_rolling_machine` | external rolled part, otherwise `review` | alloy + section + radius |
| `mig_mag_welding` | structural/non-cosmetic welded joint | `in_house_manual` | external fabricated frame when no qualified welder | alloy + joint type |
| `tig_welding` | thin, stainless, visible, sanitary or precision joint | `in_house_manual` | external fabricated frame when no qualified TIG welder | alloy + joint type + finish |
| `metal_grinding` | structural weld or cut edge needs dressing | `in_house_manual` | exclude if supplier returns finished component | alloy + finish class |
| `metal_polishing` | visible metal finish specified | `in_house_manual` | external pre-finished/fabricated component if finish class unsupported | alloy + finish class |
| `metal_assembly` | frame needs alignment, tacking or mechanical joining | `in_house_manual` | exclude if supplied fabricated | frame archetype + alloy |

## Glass, stone and acrylic

| Operation | Trigger | Preferred route | Fallback or exclusion | Batch key |
| --- | --- | --- | --- | --- |
| `glass_cutting` | non-tempered flat glass/mirror part | `external_component` | no in-house default in V0 | material + thickness + shape |
| `glass_edge_processing` | exposed glass edge | `external_component` | no in-house default in V0 | material + thickness + edge finish |
| `glass_drilling` | hole before tempering | `external_component` | no in-house default in V0 | material + thickness + hole class |
| `glass_tempering` | tempered glass required | `external_component` | mandatory external unless future capability approved | material + thickness + standard |
| `stone_cutting` | stone/quartz/porcelain piece | `external_component` | raw slab route is out of V0 scope | material + thickness + cut plan |
| `stone_edge_processing` | specified finished stone edge | `external_component` | bundled with supplier service when possible | material + edge profile |
| `stone_cutout` | sink, cooktop or technical cutout | `external_component` | treated as purchased fabrication line | material + cutout class |
| `stone_seaming` | on-site or shop stone seam | `external_component` | no internal V0 route | material + seam type |
| `acrylic_cnc_machining` | acrylic contour, hole, groove or pocket | `external_component` | internal routing requires future approved capability mapping | material + thickness + tooling |
| `acrylic_laser_cutting` | acrylic laser contour | `external_component` | laser contractor, not sheet-metal internal laser by default | material + thickness + cut plan |
| `acrylic_thermoforming` | formed acrylic part | `external_component` | no internal V0 route | material + thickness + mould |

## Coating

| Operation | Trigger | Preferred route | Fallback or exclusion | Batch key |
| --- | --- | --- | --- | --- |
| `finish_surface_preparation` | finish system requires prep | `in_house_manual` | external only when bundled with coating service | material + finish system |
| `wood_staining` | stain finish specified | `in_house_manual` | exclude if purchased prefinished panel/part | species + stain system |
| `wood_priming` | primer/sealer coat specified | `in_house_manual` | exclude if prefinished | material + coating system |
| `wood_lacquering` | lacquer coat specified | `in_house_manual` | external finish service if no qualified finisher | material + coating system |
| `wet_spray_painting` | liquid spray finish | `in_house_machine:finish_wet_spray_booth` | external coating service | material + color + coating system |
| `powder_coating_preparation` | powder coating specified | `in_house_machine:finish_powder_booth` | external powder-coat service | material + color + coating system |
| `powder_coating_application` | powder coating specified | `in_house_machine:finish_powder_booth` | external powder-coat service | material + color + coating system |
| `sandblasting` | blast clean/texture specified | `in_house_machine:finish_sandblast_booth` | external blasting service | material + blast class |
| `galvanizing` | galvanized protective finish specified | `in_house_machine:finish_galvanizing` | external galvanizing service | material + coating class |

## Packaging, logistics and installation

| Operation | Trigger | Preferred route | Fallback or exclusion | Batch key |
| --- | --- | --- | --- | --- |
| `protective_packaging` | internal delivery of finished object | `in_house_manual` | exclude if supplier delivers directly and company scope ends there | delivery batch |
| `vehicle_loading` | company delivery scope | `in_house_manual` | exclude for supplier-direct delivery | delivery batch |
| `delivery_trip` | company delivery scope | `in_house_manual` | external carrier as purchased logistics line | delivery route |
| `manual_site_carry` | carry needed after unloading | `site` | external carrier service if delivery scope outsourced | site + floor |
| `site_protection` | installation scope | `site` | exclude for delivery-only scope | site visit |
| `cabinet_installation` | cabinet install scope | `site` | exclude for supply-only scope | site + room |
| `countertop_installation` | countertop install scope | `site` or `external_component` | external stone supplier install takes precedence | site + countertop |
| `metalwork_installation` | metalwork install scope | `site` | external installer only if explicitly bought | site + metal assembly |
| `glass_mirror_installation` | glass/mirror install scope | `site` or `external_component` | glass supplier install takes precedence | site + glass batch |
| `site_anchoring` | documented anchors required | `site` | exclude if furniture is freestanding | substrate + anchor class |
| `site_sealing` | sealed interface required | `site` | exclude if no wet-area or visible seal scope | material interface |
| `led_low_voltage_installation` | LED system within supported low-voltage scope | `site` | `review` for mains work or missing electrical scope | LED system |
| `final_adjustment` | installed moving/visible component | `site` | exclude for supply-only scope | site visit |
| `site_cleanup` | company installation scope | `site` | exclude for delivery-only scope | site visit |

## Non-negotiable route checks

1. A shaped panel cannot fall through to `manual_panel_cutting`.
2. Any CNC or laser subcontractor route must use the accepted calculator and
   create a purchased component, not an internal operation line.
3. Stainless visible work selects TIG and visible-finish branches only when the
   source specifies alloy and finish. Otherwise it enters `review`.
4. A stone, glass, or acrylic operation never becomes internal merely because a
   matching general machine exists in a different material family.
5. Installation operations require an explicit installation scope. A product
   image alone does not justify them.
