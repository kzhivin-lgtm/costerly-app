# Operation Dictionary v1, 3.17.1.3

Status: owner-accepted operation contract, time priors pending. It defines
operation meanings and calculation boundaries. It does not activate new labor
norms, routes, machines, prices, or database rows.

## Accepted decision, 2026-10-10

The owner accepted this operation model as the common contract for Material
Family Matrix, Estimation Agent, route resolver, Machinery and Labor Engine:

1. the four recipe stages: `prepare`, `execute`, `finish`, `closeout`;
2. shared setup and cleanup only inside a compatible machine session;
3. specialist Glass, Stone and Acrylic work as `external_component` routes in
   V1;
4. the plywood-sheet decomposition as the canonical sheet-material pattern.

The Material Family Matrix is also accepted. The next approval gate is
source-backed time priors and formula parameters by recipe, not a new operation
taxonomy.

The owner accepts this as a deliberately incomplete V1 catalogue. A missing
operation is a recorded future gap, not permission to map it to a similar code
or invent a time value. New identities enter only through a versioned catalogue
change with their scope, drivers, route posture, recipe and evidence boundary.

## Non-negotiable boundaries

1. A material family makes an operation *eligible*, never mandatory.
2. The Estimation Agent selects zero or more eligible operations from object
   evidence. It returns physical facts and evidence, never minutes, prices,
   routes, machinery availability, rates or totals.
3. `reference_operation` is the stable work identity. A `recipe` is a
   versioned, route-specific way of carrying it out. One operation can have
   manual, in-house machine and external-component recipes.
4. Machinery is a capability gate and, where relevant, a machine-cost input.
   It selects an approved recipe. It is never a free multiplier on an
   operation, and a missing machine produces `review_required` or an approved
   external route.
5. An external recipe creates a purchased fabricated component or supplier
   service. It must not also generate the supplier's labor or machine cost as
   internal company labor.
6. Preparation, execution, finishing and cleanup are visible calculation
   stages. A physical action is counted either as a shared session component or
   as its own reference operation, never both.
7. Delivery and Installation remain project-level commercial work outside the
   Estimation Agent's fabrication-operation plan. Packaging remains governed
   by the approved allowance policy, not this dictionary.

## Recipe shape

Each approved recipe has these fields:

```text
operation_code
route                       # in_house_manual | in_house_machine | external_component
machine_requirement         # optional Machinery capability, never inferred
eligible_material_families
batch_key_fields
primary_drivers
secondary_drivers
required_evidence
stage_components
role_allocations
complexity_signals
output_facts
review_required_conditions
formula_version + source / approval metadata
```

### Four calculation stages

| Stage | What it contains | Typical measurement | Rule |
| --- | --- | --- | --- |
| `prepare` | programme/nesting when applicable, material staging, machine or tool setup, jig and tool selection | fixed batch minutes, sheets, tooling changes | amortised by a compatible batch key |
| `execute` | the physical transformation | cuts, holes, edge metres, area, bends, weld metres, parts | primary direct driver |
| `finish` | unload, trim/deburr where inseparable, label, operation-level inspection | parts, exposed edge, inspection count | separate only when it is not a distinct next operation |
| `closeout` | cleanup, tool return, waste handling, session close | fixed session minutes or documented waste quantity | a session component, never an undocumented percent uplift |

`minimum_batch` remains a guard around the whole recipe, not a fifth physical
stage. Every stage component needs its own source-backed low/typical/high
minutes or rate before it becomes active. Existing numeric v0 Labor baselines
are implementation placeholders, not approved norms for this dictionary.

The calculation form is:

```text
elapsed_minutes = max(
  minimum_batch_minutes,
  prepare_minutes
  + execute_minutes(primary and declared secondary drivers)
  + finish_minutes
  + closeout_minutes
)

labor_hours_by_role = elapsed_minutes × approved_attendance × approved_crew / 60
machine_runtime_minutes = approved machine-stage components only
```

Machine runtime and operator labor are deliberately separate. For example, a
CNC router may run while the CNC operator has an approved fractional attendance;
both values are retained, but neither is guessed from the other.

## Machine sessions, especially CNC

A machine session is a calculation grouping, not a new material family and not
a new `reference_operation`. It carries the shared `prepare` and `closeout`
components once, then contains the selected child operations. A session is
limited to compatible work on one route and one machine capability. It never
shares setup or cleanup across different machines.

```text
cnc_router_session
  shared: programme, nesting, load, zero/tool setup, unload, cleanup
  children: profile cutting, vertical drilling, horizontal drilling,
            grooving, pocketing
```

The child operations own only their incremental geometry. This prevents five
selected CNC features on one sheet from charging five programme, setup and
cleanup blocks. A panel-saw session follows the same principle for sheets cut
in one compatible run. Work moving from panel saw to CNC is two sessions and
therefore has two machine-specific setup/closeout traces.
`panel_material_handling` is only selected as a separate operation when it is
documented work outside the bounded machine session. An upstream
material-staging batch may be shared across later sessions only when it has its
own explicit batch key and is allocated exactly once.

## Operation catalogue and route posture

The existing reference catalogue has 78 active operation identities. The
proposed `stone_edge_profiling` is a candidate 79th identity and does not yet
exist in the runtime catalogue. The groups below are the approval dictionary;
each code inherits the four-stage recipe contract above.

| Group | Operation codes | Route and Machinery boundary | Primary driver(s) |
| --- | --- | --- | --- |
| Planning and batch preparation | `site_measurement`, `estimate_review`, `shop_drawing`, `cnc_programming`, `sheet_nesting`, `supplier_quotation`, `quality_inspection` | Project/batch scope. `cnc_programming` and `sheet_nesting` belong to a CNC session only when needed | visit, drawing pages, parts, sheets, supplier quotes, inspection scope |
| Panel and wood machining | `panel_material_handling`, `panel_saw_cutting`, `manual_panel_cutting`, `manual_drilling`, `manual_routing`, `edge_banding`, `veneer_lamination`, `solid_wood_ripping`, `solid_wood_crosscutting`, `solid_wood_jointing_planing`, `solid_wood_profiling`, `solid_wood_glueup`, `wood_sanding` | Machine requirement is respectively declared and checked: panel saw, edge bander, veneer press, solid-wood preparation or wide-belt sander. Otherwise only an approved manual or external recipe may apply | sheets, cuts, holes, edge metres, area, stock metres, glue-up count |
| CNC wood | `cnc_router_profile_cutting`, `cnc_vertical_drilling`, `cnc_horizontal_drilling`, `cnc_grooving`, `cnc_pocketing` | `wood_cnc_router` only, grouped as one CNC session. If unavailable, use the deterministic CNC subcontractor route when eligible, not a pretend manual substitute | contour metres, holes, groove metres, pockets, parts, tool changes |
| Assembly | `carcass_assembly`, `drawer_assembly`, `door_front_fitting`, `hardware_installation`, `workshop_dry_fit` | In-house manual recipes. A machine is not implied by the assembly name | cabinets, drawers, fronts, fittings, object count |
| Sheet and structural metal | `sheet_laser_cutting`, `sheet_shearing`, `metal_profile_cutting`, `metal_drilling`, `metal_milling`, `metal_punching`, `sheet_metal_bending`, `metal_profile_bending`, `metal_rolling` | Respectively Sheet Laser, shear, profile saw, drill/tap, milling capability, punch press, press brake, profile bender, rolling machine. Absence is review or approved subcontract, never an inferred fallback | cut metres/cuts, holes, pockets, bends, parts |
| Metal join and finish | `mig_mag_welding`, `tig_welding`, `metal_grinding`, `metal_polishing`, `metal_assembly` | Welding, deburring/grinding or polishing capability only when an approved in-house recipe exists | weld metres, joints, grind metres, surface area |
| Glass and specialist plastics | `glass_cutting`, `glass_edge_processing`, `glass_drilling`, `glass_tempering`, `acrylic_cnc_machining`, `acrylic_laser_cutting`, `acrylic_thermoforming` | Current V1 posture is `external_component`. In-house machinery is not implied by a wood CNC or metal laser | cut or edge metres, holes, material area, parts |
| Stone fabricated surfaces | `stone_cutting`, `stone_edge_processing`, `stone_edge_profiling` (candidate), `stone_cutout`, `stone_seaming` | Current V1 posture is `external_component`. `stone_edge_profiling` needs an approved specialist recipe before activation | cut metres, straight-edge metres, profiled-edge metres, cutout count, seam metres |
| Coating | `finish_surface_preparation`, `wood_staining`, `wood_priming`, `wood_lacquering`, `wet_spray_painting`, `powder_coating_preparation`, `powder_coating_application`, `sandblasting`, `galvanizing` | Relevant Machinery capability selects only a compatible approved in-house recipe. Coating system and substrate are evidence, not a free rate multiplier | finish area, coat count, masking area, rack load, material weight |
| Excluded from Agent production plan | `protective_packaging`, `vehicle_loading`, `delivery_trip`, `manual_site_carry`, `site_protection`, `cabinet_installation`, `countertop_installation`, `metalwork_installation`, `glass_mirror_installation`, `site_anchoring`, `site_sealing`, `led_low_voltage_installation`, `final_adjustment`, `site_cleanup` | Packaging policy or project/site scope only. They are retained in the reference catalogue but excluded from material-operation eligibility | project/site drivers only |

## Worked example: one plywood sheet becomes parts

This is the expected decomposition, with no invented numbers:

```text
Input facts
  material family: plywood
  one 2440 × 1220 sheet
  declared parts: dimensions and quantities
  evidence: drawing or stated cut list
  selected operation: panel_saw_cutting

Route validation
  wood_panel_saw is available in-house
  geometry is straight, rectangular and within the approved manual/panel-saw route
  otherwise choose the CNC or external route, or return review_required

Batch: panel_saw_session
  key: material family + stock thickness/format + route + machine + cut-list revision
  prepare: retrieve/identify sheet, optimise or validate cut order, load and set fence/blade
  execute: direct time from declared cut_count, with part_count as a secondary complexity fact
  finish: unload, mark and stack parts, operation-level dimensional check
  closeout: remove offcuts/waste, clean machine/work area, return or record tooling

Result
  one elapsed-time trace with its stage components, one operator labor trace,
  separate machine-runtime trace where the approved saw recipe has one,
  and produced part facts for following edge-banding, CNC, assembly or coating.
```

One plywood sheet does not automatically create edge banding, drilling, CNC,
sanding, assembly or cleanup as separate catalog lines. Those arise only from
facts and selected operations. Conversely, the required setup and closeout of
the chosen cutting session must not disappear merely because they are not a
separate material attribute.

## Required deterministic inputs and review gates

| Concern | Deterministic input | `review_required` when |
| --- | --- | --- |
| Material applicability | material family and selected operation | operation is not eligible for the family |
| Route | company Machinery availability, route policy, supplier offer where relevant | no eligible in-house or approved external route |
| Batch | operation-specific key and compatible work facts | shared setup cannot be safely allocated |
| Direct work | primary driver plus declared complexity signals | primary driver, units or geometry are missing/conflicting |
| Machinery | exact capability, capacity and approved recipe | machine is missing, incompatible or capacity is unknown |
| Labor | approved role, crew and attendance profile | source-backed recipe component is absent |
| External work | supplier scope and pricing basis | supplier component or its price basis is unresolved |

## Implementation order after approval

1. Add the recipe and stage-component contract to the target schema. Extend the
   existing `market_operation_time_components` types rather than creating a
   parallel calculator.
2. Add `stone_edge_profiling` only with drivers, a specialist external route,
   source-backed time/price model and tests.
3. Convert one representative panel-saw and one CNC-router session from the
   current flat baseline into staged traces. Confirm no duplicate handling,
   programming, setup or cleanup.
4. Add the remaining recipe families progressively, with source-backed priors
   and golden object tests before Agent integration.

## Next evidence phase

The next work is to populate source-backed time priors, in this order:

1. recover and audit the existing Labor library before new research:
   `LABOR_TIME_SOURCE_AUDIT_V0`, `LABOR_TIME_BASELINE_V0`, Furniture Core
   recipes/formulas and Route Catalog. The active Labor Engine currently uses
   53 flat v0 baselines; the library contains source-backed (`R`),
   equipment-bound (`E`) and derived (`D`) rows. A legacy `D` or `E` row must
   never be promoted to an approved norm without new evidence;
2. define a confidence class for each source, separating vendor throughput,
   manufacturer capability, internal observed time and unsupported anecdote;
3. set low/typical/high parameters separately for each stage component and
   route, beginning with the panel-saw and CNC-router canonical sessions;
4. test calculated traces against representative objects before a parameter is
   activated. Missing evidence stays `review_required`, never a guessed weight.
