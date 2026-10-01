# Furniture Core Work Recipes v0

Status: design draft, no production time priors or Estimation Agent changes

## Purpose

Define the first deterministic furniture work recipes. They are the bridge
between a future structured fabrication specification and later source-backed
time formulas. A recipe creates labor only after its explicit triggering facts
and route are present.

## Shared rules

- A batch is a compatible group of work, not an object or entire project.
- Agent-derived facts must retain `explicit` or `inferred` provenance.
- The formula engine owns quantities derived from a selected recipe. The agent
  must not send labor hours or a free-form hole count.
- One physical task must resolve to one route. Manual and CNC variants of the
  same task are mutually exclusive.
- Handling is included in the first relevant recipe unless a dedicated handling
  requirement is explicitly present.

| # | Recipe | Triggering facts | Batch key | Time components to parameterize | Role | Complexity signals | Exclusions / route rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `sheet_nesting` | sheet material, derived panel dimensions, panel count | material family, thickness, sheet format, grain requirement | setup, panels placed, sheets reviewed, yield exceptions | CNC operator / draftsperson | grain direction, mirrored parts, nested small parts, multiple materials | Creates planning work only. It never creates saw or CNC labor by itself. |
| 2 | `panel_saw_cutting` | rectangular panels, derived sheets, straight cuts | material family, thickness, sheet format, blade/setup class | setup, sheet staging, cut sequences, panel sorting, labeling | wood machine operator, optional assistant | cuts per sheet band, small-part band, rotation band, fragile surface | Only if panel saw is in-house and the manual route is selected. Excludes CNC profile cutting for the same panel. |
| 3 | `cnc_router_session` | any compatible CNC panel work | material family, thickness, tooling/program family | programming, shared setup, sheet load, sheet unload, part sort | CNC operator | tool family, program family, sheet format, batch size | Calculation grouping only. Shared time is counted once, then distributed across child operations. |
| 4 | `cnc_router_profile_cutting` | panel parts requiring CNC profile or repeatability | parent CNC session | contour length, internal cutouts, incremental tool changes | CNC operator | straight vs shaped profile, internal cutouts, repeatability, small parts | In-house CNC only. If unavailable or ineligible, route whole compatible CNC work to subcontractor component. |
| 5 | `cnc_vertical_drilling` | face holes supported by the explicit drawing or derived part and connection facts | parent CNC session | hole patterns, hole classes, incremental drill changes | CNC operator | System 32 row, repeated pattern, hinge cup, mixed diameters | Coexists with CNC cutting under one session. Excludes manual drilling for the same hole set. |
| 6 | `cnc_grooving` | groove or dado supported by the explicit drawing or derived part and connection facts | parent CNC session | groove length, incremental tool changes | CNC operator | through groove, stopped groove, repeated grooves, depth band | In-house CNC only. Excludes manual routing and subcontractor component for the same groove set. |
| 7 | `manual_drilling` and `manual_routing` | simple low-volume holes or grooves supported by manual route | material family, thickness, tool family | shared work setup, marking, panel positioning, each operation's holes or profile length, tool changes, inspection | carpenter | hole count band, end drilling, mixed diameters, visible-face risk | Separate existing operation identities under one optional manual-panel session. They replace matching CNC work, never supplement it. |
| 8 | `edge_banding` | exposed panel edges and selected edge material | edge material, thickness, colour/system, panel thickness | setup, edge length, part feed/handling, ends, trimming/cleanup, inspection | edge-bander operator or carpenter | straight vs curved, edge thickness, narrow parts, visible quality | In-house edge-bander recipe only if available. A manual recipe must be explicitly selected, not assumed. |
| 9 | `carcass_assembly` | derived carcass modules, panels, back-panel type and connection facts | construction method, material family, module geometry | kit preparation, panel positioning, structural connections, back panel, squaring, inspection | carpenter | module size, fixed/adjustable shelves, partitions, construction system | Does not include drilling, hardware, fronts, finishing, or installation. Those are separate recipes. |
| 10 | `hardware_and_front_fitting` | derived or explicit doors, drawer fronts, drawers and fitting families | hardware family, front/drawer system and connection facts | setup, hinge cups/plates, runners, handles, special fittings, alignment and adjustment | carpenter | door count, drawer system, soft-close/lift mechanism, alignment sensitivity | Does not include carcass assembly. Hole production stays in CNC/manual drilling recipe. |
| 11 | `protective_packaging` | completed object, packing requirement, transport risk | packaging system, finish sensitivity, package dimensions | protection setup, wrap/protection area, corner protection, labeling, packing unit | packer | fragile finish, glass/stone insert, knock-down vs assembled, transport class | Object-level only. Loading, delivery, and site work remain project/site recipes. |

## Resulting deterministic facts

The recipes require a future specification to hold, at minimum:

- component family and material family;
- dimensions, thickness, count, and sheet format where applicable;
- derived panel, exposed-edge, groove, hole-set, carcass, front, drawer, and
  hardware-fact collections;
- explicit joinery and connection facts plus bounded complexity signals;
- evidence/provenance for each source fact.

The next document will define formulas for these recipes. It must set
which components receive numeric priors, their measurement units, and which
signals select a different formula variant rather than an arbitrary multiplier.
