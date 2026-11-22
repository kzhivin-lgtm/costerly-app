# Front panels: MVP material class and switching plan

Current implementation: Estimation9.40, published22November2026. Owner authenticated acceptance pending.
The originally approved V3.3 implementation remains a historical release.
[Current incremental implementation and verification](ESTIMATION_V9_40_FRONT_PANELS_2026_11_22.md).
[Runtime, verification and limits](ESTIMATION_V3_3_FRONT_PANELS_2026_11_22.md).
The owner first requested a plan for changing facade/visible sheet stock, then
explicitly narrowed MVP to fronts only. Exposed sides, wall/cabinet adjacency,
floor-plan interpretation and automatic visibility inference are excluded.
The owner approved implementation and deployment after selecting the name and
four material types. The current Objects V2.7 Loading repair is part of the base.
No new hierarchical work number or block is assigned at this planning boundary.

User-facing label approved on22November2026: `Front panels`. This covers
door fronts, drawer fronts and lift-up fronts. Preserve the existing internal
part role codes.

The MVP selector has exactly four user-facing options, approved on22November2026:
`LDSP`, `Veneered MDF`, `MDF`, and `Plywood`. For MVP, the veneer option means MDF with a
veneer finish. Each option resolves through the existing catalog to the
compatible family and finish variant, retaining the group's thickness.

## User outcome

Materials distinguishes Front panels from the remaining material demands even when
both currently resolve to the same LDSP stock. The user can choose another
compatible material for the fronts of the selected object. Existing carcass,
drawer boxes, sides, backs, shelves, worktops and other components keep their
material assignments. Recalculate using saved Parts and the existing shared
Resolver/Material Engine, without rerunning Detection/OCR/Parts recognition.

## Verified pre-implementation foundation

- `use_cases/estimation_cb_geometry_parts.py` already maps casework front
  types to `door_front`, `drawer_front`, `lift_up_front`.
- `use_cases/estimation.py::_FRONT_PART_ROLES` already recognises those and
  legacy explicit facade roles for the object summary. Reuse one consistent
  definition rather than building a competing classification from names.
- `use_cases/estimation_cb_material_demand.py::_ROLES` currently maps fronts
  to `visible_sheet`, together with fixed panels, frame/seat parts, plinths
  and other components. The entire visible_sheet category is not Front panels.
  Its existing role also participates in defaults and finish policies, so a
  blind rename would change costing beyond the approved scope.
- The CB adapter preserves part_sources/roles, quantities and evidence.
- `use_cases/material_engine.py` groups purchase demands by selection_key
  across the estimate. `use_cases/estimation.py::_material_rows_from_plan`
  displays each selected stock line using that object's allocations. Front panels
  and other parts using one stock can therefore appear in the same UI row.
- `save_object_detail_material_edits` currently edits quantities, purchase
  counts and related existing fields. A group material selector is an addition,
  not already shipped functionality.
- `_recalculate_from_parts_check` reuses the saved immutable report/inputs.
  That is the existing recomputation path to extend, not a new model cycle.

The code inspection does not establish the exact front grouping of any current
production project. First verify one saved casework witness before implementation.

## Proposed implementation sequence

1. Trace one saved casework object's front roles through Parts, material
   requirements, allocations and rendered rows. Produce a small before/after
   classification table. Do not create or recount fronts from geometry.
2. Preserve a fronts-purpose distinction downstream, bound to the existing
   physical parts and saved source revision. Use existing explicit role aliases
   for old saved data. Do not classify all MDF/LDSP or all visible_sheet rows
   as fronts. Preserve old manual overrides and unrelated requirement IDs.
3. Project a separate Front panels position in Materials. Keep its material identity
   separate from its purpose. One LDSP stock shared with the carcass remains
   one actual purchase plan, not one independently rounded sheet basket per
   class. Do not duplicate purchased quantities or add the same cost twice.
4. Add material selection only for the front group, within the selected object.
   Offer exactly `LDSP`, `Veneered MDF`, `MDF`, and `Plywood`. Resolve the chosen type to
   compatible catalog stock for that group's thickness and finish.
   Store the user's choice as an estimate-local setting, preserving immutable
   source facts and company/catalog defaults. Use compatible catalog variants
   through the existing Company Catalog / Israel Reference / Assumption Fallback
   path. Material choices retain the part geometry/quantity and must respect
   the existing thickness/specification constraints.
5. Apply the effective front choice before material-demand and dependent edge/
   finish generation, then reuse Resolver/Engine and existing dependent-cost
   recalculation. A selected variant must describe base and finish coherently
   (for example raw MDF and veneered MDF are different specifications), without
   inventing an additional finish model or doubling supplier-included work.
6. Review the small UI scenario matrix/mockup before a UI patch. Keep the
   accepted collapsed Materials behavior, flat material rows, existing fields,
   header/preview/other cost sections and transition protection. No new
   incomplete-calculation warnings or unrequested notifications.

No separate side/visibility class, exposed-panel inheritance, floor-plan job,
new material catalog, general material replacement for every row, or project
revision/export workflow belongs to this MVP.

## Acceptance before a future publication

- The front class contains only the existing explicit front parts. Fixed
  decorative panels and other visible_sheet parts do not enter by accident.
- Each of the four selector options resolves to its compatible material and
  finish specification. LDSP fronts can change to a compatible MDF/veneered variant while carcass,
  side, backing and drawer-box material assignments/geometry/counts remain.
- Identical stock across classes remains one shared purchase; mixed stock
  replans correctly and allocated costs sum to the project material total.
  Other allocations may change when the shared purchase changes; their parts
  and material choices must not be silently changed.
- Unrelated manual quantity/purchase edits survive. An override tied to an old
  stock cannot silently become a purchase count for a different stock.
- Switching back, saving/reopening, older saved plans and multiple objects keep
  correct identities, quantities and totals. Class/choice participate in the
  existing input fingerprint so a previous plan cannot be reused incorrectly.
- No recognition/model call is made for a material choice. Existing costing
  and labor dependencies are checked before promising complete repricing.
- The exact implementation candidate must pass relevant regression cases,
  the complete local/exact-SHA GitHub UI gate and protected publication path,
  with a distinct release number and actual Core/wrapper verification.

## Approved interaction and verification matrix

The selector sits inside the existing collapsed Materials band, above the flat
purchase rows. Front purpose stays separate from shared stock purchasing. Each
source material/thickness group has its own Front panels selector. The current
cycle choice is selected. Plywood is selected for existing plywood fronts.
The owner approved retaining any explicitly specified other material, including
metal, and offering the four standard alternatives. For an older source outside the four MVP stock types,
retain its actual original stock as the restore option alongside the four new
choices. Preserve the source specification and its price until explicitly changed.

Changing a selector triggers one read-only preview through the existing material
editor component/executor. No model call, permanent write or page navigation.
Show the existing footer action as Calculating while it is pending. Save changes
or APPROVE commits the choice and its recalculated plan. Coating is the next
workstream. This release changes material, cut/edge requirements and their current
dependent costs; it does not invent coating time or price.

| Scenario | Required result |
| --- | --- |
| Initial or reopened object | Materials starts collapsed, current choices selected, stock totals preserved |
| Each of four compatible material choices | Automatic preview updates purchasing and Self Cost, source Parts remains immutable |
| Fronts and body initially share stock | One common purchase basket, front-only material substitution |
| Several source groups or objects | Change is scoped to that object's selected front group |
| Restore original choice | Original assignments and control purchase signature return |
| No eligible sheet fronts | No selector is added |
| Legacy saved plan | Recover front groups from saved source line facts, retain other edits |
| Rapid selection changes or late response | Latest choice wins, stale preview cannot overwrite the current choice |
| Catalog gap or failed preview | Keep actionable draft and last confirmed saved prices, existing error handling |
| Save, failed Save, retry and reopen | Explicit persistence, saved result agrees with Objects |
| APPROVE during preview | Wait for latest preview, commit draft, then existing protected navigation |
| Other edits during preview/save | Keep unrelated numeric/labor drafts and original input behavior |
| Desktop, narrow screen and keyboard | Same accessible selector and existing cost/editor/navigation contracts |

Run the full accepted UI gate including the Objects V2.7 Profile cases and exact
SHA publication check. Production interaction acceptance remains owner-verified.
