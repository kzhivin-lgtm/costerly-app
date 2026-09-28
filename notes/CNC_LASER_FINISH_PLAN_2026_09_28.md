# CNC / Laser Finish Plan

Task: 3.14.1
Status: active, highest priority; C1 verified in production, C2 implementation candidate complete

## Finish boundary

The CNC / Laser subsystem is complete when production has the approved schema,
Staff Admin parameter library, reviewed parameters, deterministic routing,
exclusive calculator dispatch, four verified calculators, immutable parameter
snapshots, and production acceptance. It must be ready to accept bounded
material and manufacturing features from Estimation v2.

The final connection to customer estimates follows the shared material catalog
and Price Source resolver work. CNC must not introduce a parallel material
identity or price system merely to connect earlier.

## C1: Production schema

Production status: complete on 2026-09-28. Both tables and the guarded Staff RPC
were verified live with zero unintended seed records.

1. Apply `2026_09_28_cnc_estimate_levels.sql`.
2. Apply `2026_09_28_manufacturing_cost_parameters.sql`.
3. Verify tables, indexes, RLS, grants, Staff RPC authorization, empty state,
   and repeat-safe application.
4. Change the CNC estimate reserve and verify one bounded event while confirming
   that the Machinery setting still saves normally.

Checkpoint: both tables and the guarded read RPC exist in production. No
parameter is activated merely by applying the schema.

## C2: Read-only Staff Admin library

Implementation status: candidate complete. Automated acceptance passed; deploy
and authenticated production scenario acceptance remain.

1. Add the `CNC / Laser` action to Admin.
2. Render CNC Router and Sheet Laser with separate In-house and Subcontractor
   tables.
3. Display scope, low, typical, high, unit, source, source date, confidence,
   status, version, and history.
4. Support bounded empty, permission, query-failure, refresh, and narrow-screen
   states.

Checkpoint: Platform Viewer and Platform Admin can inspect the library.
Company users cannot see the action or call the RPC.

## C3: Controlled parameter editing

1. Allow Platform Admin, but not Platform Viewer, to create Candidate records.
2. Review and activate through explicit actions.
3. Editing an Active record creates a new version and archives the previous
   version without mutating historical references.
4. Validate range order, units, currencies, scopes, source evidence, effective
   dates, approval, and provider isolation.
5. Preserve entered values when a save fails.

Checkpoint: version creation, failed save, history, permissions, and rollback
are verified in production.

## C4: Reviewed Israel parameter sets

1. Define the exact required parameter keys for each calculator.
2. Load official, manufacturer, named-provider, research, and explicitly marked
   platform-prior evidence as Candidate records.
3. Keep provider models separate. Never average incompatible charge structures.
4. Review and activate only complete compatible parameter sets.
5. Leave unsupported material, thickness, machine, provider, region, or object
   scope as `needs_review`.

Checkpoint: every calculator has at least one reviewed representative scenario
and every unsupported scenario fails explicitly.

## C5: Runtime composition

1. Load Active parameters for the selected calculator and exact market.
2. Resolve scope deterministically and reject missing or ambiguous parameters.
3. Convert the resolved set into the selected calculator's typed inputs.
4. Run only the calculator selected by the route decision.
5. Persist or expose the route reasons, cost components, reserve level,
   parameter IDs, parameter versions, confidence, and inclusion boundaries.

Checkpoint: four representative end-to-end fixture calculations use production-
shaped rows and reproduce their totals from immutable inputs.

## C6: Production acceptance and checkpoint

1. Verify CNC in-house, simple panel-saw manual, CNC subcontractor, unknown
   evidence, laser in-house, laser subcontractor, rare rough manual metal, and
   not-required routes.
2. Verify estimate reserve levels 1 through 5 and untouched level 3.
3. Verify supplier minimum, material included, cutting included, delivery, rush,
   and unsupported-scope behavior.
4. Verify permissions, refresh, failure, and narrow-screen Admin states.
5. Run targeted and full automated suites, `git diff --check`, deployment health,
   and authenticated production acceptance.

Checkpoint: establish one committed and deployed rollback point. Record any
remaining Estimation connection work explicitly rather than calling it part of
the finished CNC subsystem.

## Ordered program after CNC

1. Finish CNC / Laser through C6.
2. Finish the shared material and Israel reference catalog program.
3. Integrate Price Source with Material Resolution Core and the candidate buffer.
4. Build Estimation v2 and connect bounded manufacturing features to the
   finished CNC / Laser subsystem.
