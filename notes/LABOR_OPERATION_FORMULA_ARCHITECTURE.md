# Labor Operation Formula Architecture

Status: draft, not an Estimation Agent contract and not production data

## Purpose

Define how a fixed catalog of production operations becomes deterministic labor
hours from structured object facts. The model deliberately estimates bounded
production blocks, not every screw, dowel, or CAM toolpath.

## Boundary

The future Estimation Agent supplies only structured object facts and records
whether each fact is explicit or inferred. It does not return labor hours,
machine minutes, rates, or costs.

The deterministic work engine:

1. derives required work recipes from components and fabrication features;
2. selects one eligible route using the Company Machinery profile;
3. groups compatible work into batches;
4. calculates labor time by operation formula;
5. allocates resulting labor hours to company roles.

## Formula contract

For one operation batch:

```text
elapsed_minutes = max(
  minimum_batch_minutes,
  setup_minutes
  + handling_minutes
  + sum(driver_quantity_i * direct_minutes_per_unit_i)
  + inspection_minutes
)

labor_hours_by_role = elapsed_minutes * crew_share / 60
```

`setup`, `handling`, direct drivers, and `inspection` are separate formula
components. A complexity modifier may only target named components, never
multiply the whole object price without explanation.

The batch key is operation-specific. It normally includes material family,
thickness or section where material-sensitive, operation route, tooling or
finish system, and other setup-changing attributes. Thus preparation is
amortized across compatible sheets or parts, not added once per object.

## Work sessions and child operations

Some catalog operations are distinct fabrication features but share one physical
machine session. Their identities stay separate, while their common work is
calculated once at session level. This prevents duplicated programming, setup,
sheet loading, and unloading.

Example: one compatible panel batch may require CNC contour cutting, vertical
drilling, grooves, and pockets. It creates one `cnc_router_session` with shared
setup and handling, followed by the applicable child operations. A child owns
only its incremental contour, hole, groove, or pocket work.

The same pattern applies where supported by the work route, for example a
manual-panel session may share marking and panel positioning across manual
drilling and manual routing. The parent session is a calculation grouping, not
a new global operation identity and not a new Machinery capability.

## Work recipe contract

Every route-specific recipe has:

- operation identity;
- route: manual, in-house machine, or subcontractor;
- required object facts and eligible material families;
- batch-key fields;
- primary and secondary drivers;
- formula components and minimum batch;
- labor roles and crew shares;
- bounded complexity signals and their affected formula components;
- exclusions, prerequisites, and resulting output facts.

`subcontractor` recipes create a purchased fabricated component. They do not
create matching internal labor or machine-cost lines.

## Operational families

The existing 77 operations are retained and organised into these formula
families:

1. preproduction;
2. panel and wood processing;
3. assembly and hardware;
4. metal processing;
5. glass, stone, and acrylic;
6. finishing;
7. packaging, logistics, and installation.

The family does not set a time. It limits the allowed recipes, roles, drivers,
and complexity signals.

## Route-readiness matrix

The existing catalog contains 77 operations. A work route needs one of four
states before a time formula can be activated:

- `in_house_recipe`: a labor recipe can exist when the stated work and
  required company capability are present;
- `external_component`: an outside fabricator supplies a completed component
  or service, so the estimate contains a purchased fabricated component and
  no matching internal labor;
- `project_site_recipe`: valid work, but allocated at project or site level,
  not silently distributed across fabricated objects;
- `needs_review`: the catalog identity exists but neither a supported company
  route nor an approved external-component rule exists yet.

| Existing operations | Initial route state | Rule boundary |
| --- | --- | --- |
| `site_measurement`, `estimate_review`, `shop_drawing`, `supplier_quotation` | `project_site_recipe` | Scope once per estimate or revision, never once per object by default. |
| `cnc_programming`, `sheet_nesting`, `quality_inspection` | `in_house_recipe` | Batch by production file, material/operation setup, and inspection scope. |
| `panel_material_handling` | `in_house_recipe` | Only instantiate when separately documented. Otherwise handling belongs in the relevant machine or assembly recipe to prevent double counting. |
| `panel_saw_cutting`, `manual_panel_cutting` | `in_house_recipe` | Use only for supported straight panel work and a confirmed panel-saw or manual route. |
| `cnc_router_profile_cutting`, `cnc_vertical_drilling`, `cnc_horizontal_drilling`, `cnc_grooving`, `cnc_pocketing` | `in_house_recipe` or `external_component` | In-house only through the accepted CNC Router route. Complex or unavailable work becomes the CNC subcontractor component. |
| `manual_drilling`, `manual_routing` | `in_house_recipe` | Only for the accepted low-volume, simple manual route. It is mutually exclusive with the matching CNC operation. |
| `edge_banding` | `in_house_recipe` | Edge-bander recipe if available, otherwise an explicitly supported manual recipe. No silent external fallback. |
| `veneer_lamination`, `solid_wood_ripping`, `solid_wood_crosscutting`, `solid_wood_jointing_planing`, `solid_wood_profiling`, `solid_wood_glueup`, `wood_sanding` | `in_house_recipe` or `needs_review` | Activate only when the required in-house woodworking capability and formula are defined. |
| `carcass_assembly`, `drawer_assembly`, `door_front_fitting`, `hardware_installation`, `workshop_dry_fit` | `in_house_recipe` | Direct labor recipes. Drivers are modules, panels, fronts, drawers, fittings, and explicitly inferred construction features. |
| `sheet_laser_cutting` | `in_house_recipe` or `external_component` | Use the accepted Sheet Laser calculator and contractor route. |
| `sheet_shearing`, `metal_profile_cutting`, `metal_drilling`, `metal_punching`, `sheet_metal_bending`, `metal_profile_bending`, `metal_rolling`, `mig_mag_welding`, `tig_welding`, `metal_grinding`, `metal_polishing`, `metal_assembly` | `in_house_recipe` or `needs_review` | The identities remain active, but only Sheet Laser presently has an accepted external calculator. Do not invent an external price route for the others. |
| `glass_cutting`, `glass_edge_processing`, `glass_drilling`, `glass_tempering`, `stone_cutting`, `stone_edge_processing`, `stone_cutout`, `stone_seaming`, `acrylic_cnc_machining`, `acrylic_laser_cutting`, `acrylic_thermoforming` | `external_component` | V1 treats specialist fabrication as an externally purchased fabricated component unless a later explicit in-house capability is approved. |
| `finish_surface_preparation`, `wood_staining`, `wood_priming`, `wood_lacquering`, `wet_spray_painting`, `powder_coating_preparation`, `powder_coating_application`, `sandblasting`, `galvanizing` | `in_house_recipe`, `external_component`, or `needs_review` | Machinery may select in-house wet spray, powder, sandblasting, or galvanizing. Only wet spray and powder currently have a defined contractor capability. |
| `protective_packaging` | `in_house_recipe` | Object-level work, after fabrication scope is established. |
| `vehicle_loading`, `delivery_trip`, `manual_site_carry`, `site_protection`, `cabinet_installation`, `countertop_installation`, `metalwork_installation`, `glass_mirror_installation`, `site_anchoring`, `site_sealing`, `led_low_voltage_installation`, `final_adjustment`, `site_cleanup` | `project_site_recipe` | Allocate from documented delivery and site scope. Never fabricate an object-level installation share without a rule. |

The matrix deliberately does not add machinery. It makes absent capability or
unapproved external pricing visible as `needs_review` instead of inventing a
route.

## Complexity signals

Complexity is per work recipe, not per object. A recipe may use only its
declared signals, for example:

- panel cutting: straight rectangular, repeated parts, shaped contours,
  nested small parts;
- drilling: face-only versus end drilling, repeated rows, hardware type;
- edge banding: exposed edge type, part count, curves;
- assembly: module type, number of fronts, drawers, adjustable shelves,
  special fittings;
- finishing: substrate, visible faces, finish system, coat count, masking.

Each signal resolves to an explicit formula variant or named adjustment.
Unknown signals reduce confidence and may force review. They never cause a
free-form time estimate.

## Machinery interaction

Machinery selects a recipe, not an arbitrary multiplier. Example for a panel:

- CNC Router in-house: CNC cutting and drilling recipes plus CNC operator
  labor and a separate CNC machine-cost calculator;
- CNC unavailable, simple supported panel work with in-house panel saw:
  manual cutting and drilling recipes;
- CNC unavailable and work exceeds the manual route: CNC subcontractor
  purchased fabricated component, excluding matching internal labor.

## Adjacent systems

- Materials supply material family, dimensions, quantity, thickness, and
  processing eligibility. Material price is not part of a labor formula.
- Company Labor Costs resolve the compatible employee role after operation
  hours are calculated.
- Machinery supplies availability and machine cost only after a route is
  selected.
- Overhead reads final direct productive labor hours. It does not select or
  change operations.

## Next work sequence

1. Partition all existing operations into route-specific recipes.
2. Define each recipe's object facts, batch key, drivers, role allocation,
   exclusions, and complexity signals.
3. Establish formula definitions by operation family, without numeric priors yet.
4. Research and enter source-backed Israel time priors.
5. Validate recipes against structured representative objects before any agent
   integration.
