# Labor crew allocation v0

Status: deterministic labor allocation specification. It converts operation
elapsed time into hours by role. It does not set the monetary hourly rate.

## Rule

`role_hours = elapsed_hours * attendance_fraction * crew_size`

`crew_size` is never guessed from a photo. The base crew below applies unless a
listed safety, weight, size, or access condition changes it. Machine runtime is
not automatically equal to operator labor time. For CNC and laser, use the
selected company-machine attendance fraction when it exists; otherwise use the
v0 default shown below.

## Preproduction and wood

| Operations | Primary role | Base crew | Attendance | Escalation rule |
| --- | --- | ---: | ---: | --- |
| `site_measurement` | project manager | 1 | 1.00 | add installer only for explicit technical survey |
| `estimate_review`, `supplier_quotation` | estimator | 1 | 1.00 | none |
| `shop_drawing` | designer draftsperson | 1 | 1.00 | none |
| `cnc_programming`, `sheet_nesting` | CNC operator | 1 | 1.00 | none |
| `quality_inspection` | production manager | 1 | 1.00 | add qualified fabricator only for corrective inspection |
| `panel_material_handling` | general worker | 1 | 1.00 | crew 2 for panel over 35 kg or unsafe solo handling |
| `panel_saw_cutting`, `edge_banding` | wood machine operator | 1 | 1.00 | assistant only for declared oversized/heavy sheet |
| `cnc_router_profile_cutting`, `cnc_vertical_drilling`, `cnc_horizontal_drilling`, `cnc_grooving`, `cnc_pocketing` | CNC operator | 1 | 0.25 | use company attendance fraction when available |
| `manual_panel_cutting`, `manual_drilling`, `manual_routing` | carpenter | 1 | 1.00 | none |
| `veneer_lamination` | carpenter | 1 | 1.00 | crew 2 for declared large veneer layup |
| `solid_wood_ripping`, `solid_wood_crosscutting`, `solid_wood_jointing_planing`, `solid_wood_profiling` | wood machine operator | 1 | 1.00 | assistant only for oversized stock |
| `solid_wood_glueup`, `wood_sanding` | carpenter | 1 | 1.00 | crew 2 for declared large glue-up |

## Assembly and metal

| Operations | Primary role | Base crew | Attendance | Escalation rule |
| --- | --- | ---: | ---: | --- |
| `carcass_assembly`, `drawer_assembly`, `door_front_fitting`, `hardware_installation`, `workshop_dry_fit` | carpenter | 1 | 1.00 | crew 2 only for an explicit heavy or oversized assembly |
| `sheet_laser_cutting` | sheet laser operator | 1 | 0.25 | use company laser attendance fraction when available |
| `sheet_shearing`, `metal_profile_cutting`, `metal_drilling`, `metal_milling`, `metal_punching`, `sheet_metal_bending`, `metal_profile_bending`, `metal_rolling` | metal machine operator or press-brake operator | 1 | 1.00 | assistant only for declared oversized/heavy workpiece |
| `mig_mag_welding`, `tig_welding` | welder | 1 | 1.00 | fitter is separately counted through `metal_assembly`, never silently added |
| `metal_grinding`, `metal_polishing` | grinder polisher | 1 | 1.00 | none |
| `metal_assembly` | welder | 1 | 1.00 | crew 2 for frame over 35 kg or explicit two-person alignment |

## External components

`glass_*`, `stone_*`, and `acrylic_*` are external components in V0. Their
internal labor crew is zero. Any company coordination is represented by
`supplier_quotation` or `quality_inspection`, not by copying the supplier's
fabricator labor into company labor.

## Coating, delivery and installation

| Operations | Primary role | Base crew | Attendance | Escalation rule |
| --- | --- | ---: | ---: | --- |
| `finish_surface_preparation`, `wood_staining`, `wood_priming`, `wood_lacquering`, `wet_spray_painting` | painter finisher | 1 | 1.00 | no silent second painter |
| `powder_coating_preparation`, `powder_coating_application` | powder-coating operator | 1 | 1.00 | crew 2 only for declared oversized rack load |
| `sandblasting`, `galvanizing` | assigned finishing operator | 1 | 1.00 | external route produces zero internal hours |
| `protective_packaging` | packer | 1 | 1.00 | crew 2 for package over 35 kg or fragile oversized item |
| `vehicle_loading` | general worker | 1 | 1.00 | crew 2 for package over 35 kg |
| `delivery_trip` | delivery driver | 1 | 1.00 | helper only if manual carry is included separately |
| `manual_site_carry` | general worker | 1 | 1.00 | crew 2 for package over 35 kg or no safe solo route |
| `site_protection`, `cabinet_installation`, `metalwork_installation`, `site_anchoring`, `site_sealing`, `final_adjustment` | installer | 1 | 1.00 | crew 2 for declared heavy/oversized installation only |
| `countertop_installation` | installer | 2 | 1.00 | supplier installation suppresses this line |
| `glass_mirror_installation` | installer | 1 | 1.00 | crew 2 for panel over 1 sqm, 25 kg, or elevated placement |
| `led_low_voltage_installation` | low-voltage installer | 1 | 1.00 | mains electrical work is review |
| `site_cleanup` | general worker | 1 | 1.00 | none |

## Safety and accounting constraints

1. A safety escalation changes both labor hours and the explanation attached to
   the estimate line.
2. Helper labor must be represented as an explicit `general_worker` or
   `installer` allocation, never hidden inside the primary role rate.
3. External supplier headcount is not company labor. Its cost belongs to the
   purchased component.
4. Machine runtime with low attendance still contributes to machine cost, while
   only attendance-adjusted time contributes to operator labor.
