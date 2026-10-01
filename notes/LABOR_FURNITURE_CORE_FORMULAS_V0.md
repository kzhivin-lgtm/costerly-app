# Furniture Core Time Formulas v0

Status: formula contract only. Coefficients are deliberately blank until a
source-backed Israel-prior pass and representative-object validation.

## Notation

- `max(min_batch, ...)` prevents unrealistic short-job results.
- `S(x)` means a setup or handling minute coefficient for the named event.
- `R(x)` means a direct minutes-per-unit coefficient.
- A subscript selects a declared recipe variant, rather than applying a hidden
  object-wide multiplier.
- All driver quantities come from the structured fabrication specification or
  deterministic derivation rules. The agent supplies no time values.

## 1. Sheet nesting

```text
T = max(min_batch,
        S(nesting_setup)
        + sheets_reviewed * R(sheet_review)
        + panels_placed * R(panel_placement)
        + grain_constrained_sheets * R(grain_constraint)
        + yield_exceptions * R(yield_exception))
```

`sheets_reviewed` and `panels_placed` are derived from panel dimensions and
selected sheet format. Grain constraints and yield exceptions are explicit or
inferred documented signals.

## 2. Panel-saw cutting

```text
T = max(min_batch,
        S(saw_setup_variant)
        + sheets_staged * R(sheet_stage)
        + estimated_cut_sequences * R(cut_sequence_variant)
        + panel_rotations * R(panel_rotation)
        + finished_panels * R(sort_and_label)
        + waste_sheets * R(waste_clearance))
```

`estimated_cut_sequences` is a deterministic proxy derived from the panel list
and cutting-map complexity class. It is not claimed to be a CAM-confirmed cut
count. The recipe records this as inferred and reduces confidence accordingly.

## 3. CNC router profile cutting

```text
T_session = max(min_batch,
        S(program_and_tool_setup_variant)
        + sheets_loaded * R(sheet_load_unload)
        + parts_sorted * R(part_sort))

T_profile = contour_length_m * R(contour_metre_variant)
        + internal_cutouts * R(internal_cutout)
        + profile_tool_changes * R(tool_change)
```

`T_session` is created once for all compatible CNC child operations. Each child
adds only its incremental time. The corresponding CNC machine calculator
separately prices machine use and must not be duplicated by these labor lines.

## 4. CNC vertical drilling

```text
T_vertical_drilling =
        system32_holes * R(system32_hole)
        + hinge_cups * R(hinge_cup)
        + other_face_holes * R(other_face_hole_variant)
        + drill_changes * R(drill_change)
```

Hole classes are explicit drawing facts or transparent derivations from cited connections.
They are not a single unqualified `hole_count`.

## 5. CNC grooving

```text
T_grooving =
        through_groove_m * R(through_groove_metre)
        + stopped_groove_m * R(stopped_groove_metre)
        + groove_tool_changes * R(tool_change)
```

Through and stopped grooves are separate formula variants because their setup
and execution are different.

## 6. Manual drilling and routing

```text
T_session = max(min_batch,
        S(manual_tool_setup_variant)
        + panels_positioned * R(panel_position)
        + marked_features * R(mark_feature)
        + inspected_panels * R(inspect_panel))

T_manual_drilling = face_holes * R(face_hole_variant)
        + end_holes * R(end_hole_variant)
        + drill_changes * R(drill_change)

T_manual_routing =
        routed_profile_m * R(manual_route_metre_variant)
        + routing_tool_changes * R(tool_change)
```

This is enabled only for a manually eligible work package. Manual drilling and
routing retain distinct catalog identities but may share `T_session`. Matching
CNC work is not created at the same time.

## 7. Edge banding

```text
T = max(min_batch,
        S(edge_system_setup_variant)
        + straight_edge_m * R(straight_edge_metre_variant)
        + curved_edge_m * R(curved_edge_metre_variant)
        + narrow_parts * R(narrow_part_handling)
        + exposed_ends * R(end_trim)
        + inspected_parts * R(edge_inspection))
```

The edge-system variant is material and thickness specific. It selects explicit
rates for melamine, ABS, veneer, or other supported edge systems, not an
arbitrary price multiplier.

## 8. Carcass assembly

```text
T = max(min_batch,
        modules * S(module_kit_prepare_variant)
        + panels_positioned * R(panel_position)
        + structural_connections * R(connection_variant)
        + fixed_shelves * R(fixed_shelf)
        + adjustable_shelves * R(adjustable_shelf)
        + back_panels * R(back_panel_variant)
        + modules * R(square_and_inspect))
```

`structural_connections` are explicit or derived from cited part and connection facts.
This formula excludes holes, hardware, fronts, finishing, and installation.

## 9. Hardware and front fitting

```text
T = max(min_batch,
        S(hardware_setup_variant)
        + hinge_pairs * R(hinge_pair_variant)
        + runner_pairs * R(runner_pair_variant)
        + handles * R(handle_variant)
        + lift_mechanisms * R(lift_mechanism_variant)
        + special_fittings * R(special_fitting_variant)
        + fronts_adjusted * R(front_adjustment_variant))
```

The hardware family determines the allowed rates and ensures that a simple
handle, a drawer runner, and a lift mechanism cannot be treated as equivalent.

## 10. Protective packaging

```text
T = max(min_batch,
        S(packing_setup_variant)
        + protected_surface_sqm * R(protect_surface_variant)
        + corners_protected * R(corner_protection)
        + packing_units * R(pack_unit_variant)
        + labels * R(label)
        + fragile_inserts * R(fragile_insert))
```

Packaging variant is selected from finish sensitivity, fragility, and
knock-down versus assembled delivery. Vehicle loading and delivery remain
project/site work.

## Required future derivation rules

Before numeric priors are entered, the deterministic layer must define rules
for:

1. panel and sheet derivation from object dimensions and material;
2. compatible batch grouping;
3. estimated cutting-map complexity from a panel list;
4. connection and hole-set generation from explicit drawing and part facts;
5. exposed-edge and finish-surface generation;
6. hardware quantities and variants;
7. confidence reduction when a driver is inferred rather than explicit.
