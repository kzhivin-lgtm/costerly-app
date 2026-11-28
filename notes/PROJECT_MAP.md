# Costerly AI Project Map

This file explains where code belongs so the project stays understandable.

Estimation 9.4 Parts Check uses the accepted File Review PDF handoff and
publishes a private report from Objects. Work 3.17.4.6 and verification
are recorded in [Estimation 9 Parts Check from Upload](ESTIMATION_V9_PARTS_CHECK_RELEASE_2026_11_12.md).

## Entry Point

- `app.py` sets Streamlit page config, applies global CSS, initializes state, and routes to screens.
- It should stay small. Business logic does not belong here.

## UI Layer

- Published Labor V3.7 runtime d9177eb2: [approval and Last Estimate](LABOR_V3_7_APPROVAL_2026_11_28.md).
  APPROVING/green APPROVED, canonical committed-cost/PDF identity handoff and
  missing post-Save Labor readiness. Harvest precedes readiness paint and scoped
  timer cancellation, fixing the deterministic stranded-Estimating race.
  Existing last Project read cache survives New Estimate, active identities clear.
  Zero focus preserves untouched blur versus explicit Delete; inapplicable LDSP
  coating is hidden without changing costs. Exact clean1224/6subtests/all10 gate,
  full local1224/all10, four frozen controls and actual Railway/Pages/Core/wrapper
  parity passed. Owner real-cycle acceptance pending; V3.5 checkpoint preserved.

- Published Labor V3.6 runtime9ce04226: [prepared Project/Object navigation](LABOR_V3_6_TRANSITIONS_2026_11_28.md).
  Object/Labor/Overhead preloads gate Review per Object; selected Future reused,
  owned File Review reads overlap, local pending publication reads are skipped,
  simple approval preserves valid caches, startup has shared visible feedback.
  Existing interval stops via a scoped native message, without app rerun.
  Exact clean1212/6subtests/all10 gate502.571s and local full648.274s passed;
  four frozen controls unchanged, Railway/Pages and actual served version verified.
  Owner real-cycle speed acceptance pending; V3.5 checkpoint preserved.

- Latest accepted full preservation: [Labor V3.5 checkpoint](LABOR_V3_5_PRODUCTION_CHECKPOINT_2026_11_28.md),
  runtime4f11834c,882 exact files, restored1198 checks/four controls. Owner accepts
  the real counter cycle; startup/navigation latency remains the next analysis.

- Preserved Labor V3.5 runtime4f11834c refines the Project counter: owned pending
  refresh uses accepted seeds, then normal scoped terminal reload. Shared
  interpolation catches up gradually and real catalog/material-plan receipts
  widen late bands. Quantity receipts require server-rendered agreement before
  clearing. No new polling/writes/models; [timing, gates and acceptance limits](LABOR_V3_3_PERFORMANCE_AUDIT.md).

- Preserved Labor V3.4 runtime997a4a33 replaces the Project counter's70 boundary
  with90 and adds completed stage receipts. `use_cases/estimation_progress.py`
  owns bounded batch/generation state; optional pipeline/material callbacks do
  no extra durable I/O. Existing fragment/elapsed interpolation hold all active
  rows below100 until final persisted readiness. [Evidence and limits](LABOR_V3_3_PERFORMANCE_AUDIT.md).

- Current PDF refinement3136a583 keeps three physical production-term rows per
  language,18pt pitch and the accepted proposal/version workflow. [Release](LABOR_V3_PDF_2026_11_27.md).
  [Performance audit](LABOR_V3_3_PERFORMANCE_AUDIT.md) preserves historical timings,
  published V3.4 progress and separate unimplemented navigation proposals.

- Previous full preservation: [Labor V3.3 checkpoint](LABOR_V3_3_PRODUCTION_CHECKPOINT_2026_11_27.md), exact
  runtimea077dd84. Owner accepts the working proposal/version mechanism; the
  requested three-line terms and performance audit are subsequent work. Restore
  source880files,1159 checks and four frozen controls passed. Earlier checkpoints
  remain immutable; source/records/evidence are separate.

- Current Objects V2.7 repair: `ui/workflow_transition.js` coordinates one
  per-transition DOM watcher with run-indexed ready receipts and Profile tab
  matching. Original covers/recovery/host-auth/protocol checks remain protected.
  `tests/ui/profile_ready_regression.mjs` supplies7 deterministic local browser
  cases inside the existing Profile Save suite. Layout, inputs, writes, costing
  and all other mechanics are unchanged. [Publication/evidence](OBJECTS_V2_7_RELEASE_2026_11_21.md).

- Previous full runtime/records restoration reference: [Labor2.21 checkpoint](LABOR_V2_21_PRODUCTION_CHECKPOINT_2026_11_26.md),
  runtimeb7902b42. Preserve exact code/records, complete release/incident evidence
  and partial owner acceptance separately. Source restore1098 checks and four
  offline controls passed. Previous [Objects V2.6 checkpoint](OBJECTS_V2_6_PRODUCTION_CHECKPOINT_2026_11_21.md)
  and [Labor2.18 checkpoint](LABOR_V2_18_PRODUCTION_CHECKPOINT_2026_11_26.md) remain immutable.
  No runtime is published by preservation.

- Preserved Objects V2.6 presentation: `ui/objects_pricing.py` owns compact R labels,
  `ui/objects_workflow.py` the right-arrow markup, `styles/objects.py` confirmation/
  check/icon presentation, and `EstimationCycle.observe` UI timing receipts in
  `use_cases/estimation_progress.py`. Worker/status publication and original
  input/actions runtime remain unchanged. [Release/evidence](OBJECTS_V2_6_RELEASE_2026_11_21.md).

- Accepted Objects Estimation UI reference: [Objects V2.4 full checkpoint](OBJECTS_V2_4_PRODUCTION_CHECKPOINT_2026_11_21.md),
  runtimea8b08ba5. `styles/objects.py` owns layout, `ui/objects_workflow.py` the
  stage/header view and `ui/objects_pricing.py` the pricing/document rendering.
  Original handlers, V2.2 protection and V3.2 costing remain protected. Next
  Object Details V2.5 implements the approved compact presentation in
  `styles/object_detail.py`, `ui/object_detail_view.py` and the existing Labor/
  Assembly view renderers. [Release/evidence](OBJECT_DETAIL_V2_5_RELEASE_2026_11_21.md).
  Screen/input/auth/controller/persistence/costing implementations are unchanged.
- `screens/` contains one Streamlit screen per file.
- `ui/` contains shared rendering helpers used by multiple screens.
- `ui/browser_session.py` owns the tab-scoped Auth storage bridge. Its component
  must remain inside the hidden Sidebar and outside the main screen layout. It
  reads only during session bootstrap; browser store/clear commands must remain
  callback-free so they cannot consume the next user interaction.
- `styles/` contains CSS grouped by responsibility.
- `styles/base.py` owns global design tokens and base Streamlit overrides.

## Application Layer

The current Labor continuation point is documented in
[`ESTIMATION_LABOR_NEXT_CHAT_HANDOFF_2026_11_14.md`](ESTIMATION_LABOR_NEXT_CHAT_HANDOFF_2026_11_14.md),
updated through deployed V1.3.4 on 18 November 2026. Sheet Processing lives in
`use_cases/sheet_processing.py` with the CNC and panel-saw calculators; Block
Assembly lives in `use_cases/block_assembly.py`. Both consume the saved Parts
Check used by Materials. The legacy `labor_engine.py` is not the new runtime
entry point. Remaining extra assembly/finishing and final cost aggregation
must not be mistaken for an instruction to rebuild these existing blocks.

- `use_cases/` contains product flows such as processing an uploaded RFQ.
- `use_cases/rfq_processing.py` runs detection, writes the result to Supabase, and loads File Review data.
- `use_cases/estimation.py` starts object estimation by creating pending estimate records from detected objects.
- `use_cases/machinery.py` owns the 27-code storage catalog, the 16-capability
  Company Profile subset, outsourceable-operation boundary, company/supplier
  validation, Supabase persistence, and the bounded production-context snapshot
  used by future routing.
- A screen calls a use case. It should not call Claude, Supabase, or file parsing directly.

## Domain / Data Layer

- `models/` will define data contracts used by UI, services, validation, and database code.
- `validation/` will validate and normalize external responses before UI uses them.

## External Integrations

- `agents/` contains LLM detection orchestration, prompt loading, and detection schema validation.
- `agents/detection_agent.py` selects the Page 23, Ada, and ordinary
  Detection paths and owns the Registry handoff. The visual fallback shares
  structural admission with the native-graphic Page 23 path.
  `agents/ocr_rendering.py` runs Mistral and local coordinate OCR.
  Coordinate readings are bound after Membership in an audit.
- The
  [V8.4.26 production checkpoint](DETECTION_V8_4_26_PRODUCTION_CHECKPOINT_2026_11_12.md)
  indexes the current rollback tag, owner Uploads, and saved render review.
- The baseline for the ordinary supporting-View experiment is
  `detection-v8.4.22-before-supporting-views-checkpoint-2026-11-11`.
  Its production and replay evidence is indexed in
  `notes/evidence/detection-v8.4.22-before-supporting-views-checkpoint.json`.
- The V8.4.9 local post-cleanup checkpoint is
  `detection-v8.4.9-post-cleanup-checkpoint-2026-11-10`. Its exact replay
  inputs and restore instructions are indexed by
  `notes/evidence/detection-v8.4.9-post-cleanup-checkpoint.json`.
- The regular V8.4.9 production release and full experimental archive are
  indexed by `notes/DETECTION_V8_4_9_PRODUCTION_CHECKPOINT_2026_11_10.md`.
- V8.4.12 adds exact short same-sheet coverage to final Fingerprint
  scoring in `agents/schemas/detection_registry_schema.py`. The release
  and rollback are indexed by
  `notes/DETECTION_V8_4_12_PRODUCTION_CHECKPOINT_2026_11_10.md`.
- V8.4.13 expands ordinary Detection's vertical dimension evidence band
  and lets same-sheet measurement sequences and complementary short
  Fingerprints prove membership. See
  `notes/DETECTION_V8_4_13_DIMENSION_MEMBERSHIP_2026_11_10.md`.
  The same record indexes the November 11 full production checkpoint
  with the 13-object Floor 06 Upload and the render exclusion audit.
- `db/` contains Supabase client and repositories.
- `db/sql/2026_09_24_machinery_foundation.sql` is the additive Machinery schema
  and catalog seed. It does not modify the prototype `company_machines` table.
- `db/sql/2026_09_28_manufacturing_cost_parameters.sql` is the additive,
  Platform Staff-only versioned parameter registry for the demand-driven CNC
  and sheet-laser calculation strategies. It does not affect current Estimation.
- `db/sql/2026_09_28_cnc_estimate_levels.sql` stores append-only explicit CNC
  estimate-level changes for behavioral calibration without estimate cost or
  customer content.
- `db/sql/2026_09_28_reference_catalog_foundation.sql` separates global
  material, operation, and labor-role identities from market-specific evidence,
  prices, and time standards. Israel is the first market; it seeds no estimates.
- `db/sql/2026_09_28_reference_catalog_taxonomy_v1.sql` seeds only controlled
  category, labor-role, and physical-driver identities, with no prices or time
  assumptions.
- `db/sql/2026_09_28_israel_reference_prices_panels_v1.sql` stores the first
  sourced Israeli panel-material identities and candidate offers without
  manufacturing an unsupported market average.
- `db/sql/2026_09_28_israel_reference_prices_hardware_v1.sql` stores exact
  fixed-price Blum hardware observations from an Israeli retailer, preserves
  the VAT evidence, and normalizes candidate prices excluding VAT.
- `db/sql/2026_09_28_israel_reference_prices_metal_v1.sql` stores the first exact
  Israeli galvanized-steel stock-length observation with VAT, cutting, delivery,
  and purchasable-length boundaries preserved.
- `db/sql/2026_09_28_israel_reference_prices_coatings_consumables_v1.sql` stores
  exact varnish, adhesive, solvent, and abrasive package observations while
  blocking normalization where VAT is unresolved.
- `db/sql/2026_09_28_israel_reference_prices_solid_wood_v1.sql` stores exact
  planed-pine sections, OSB sheets, and a glued-pine panel with nominal versus
  actual geometry and VAT-normalized market units.
- `db/sql/2026_09_28_israel_reference_prices_wood_surfaces_v1.sql` stores exact
  Israeli PVC edge-band rolls with decor identity, roll geometry, VAT evidence,
  and normalized linear-metre prices.
- `db/sql/2026_09_28_israel_reference_prices_plastics_v1.sql` stores eight
  clear cast-acrylic thicknesses and keeps raw full-sheet pricing separate from
  cut-to-size laser pricing.
- `notes/ISRAEL_REFERENCE_MASTER_CHECKLIST.md` is the 395-cell material and
  purchased-component coverage denominator used to plan and measure Israel
  source collection.
- `db/sql/2026_09_28_remove_legacy_machining_point_rules.sql` removes the unused
  machining-points table after the runtime read dependency is removed.
- `engine/` will contain estimating/routing logic when we bring that part back.

## Project Notes

- `notes/` stores architecture notes, migration decisions, and project memory.
- `notes/WORK_RULES.md` stores working rules for debugging and project changes.
- `notes/AUTH_PASSWORD_RECOVERY_HANDOFF.md` stores the current 3.8.2 Auth and
- `notes/AUTH_PASSWORD_RECOVERY_HANDOFF.md` stores the closed 3.8.2 historical
  Auth and password-recovery contract.
- `notes/MACHINERY_FOUNDATION.md` stores the 3.9.1 scenario matrix, catalog
  boundary, routing priority, and verification state.
- `notes/CNC_LASER_COSTING.md` stores the 3.14.1 protected Machinery boundary,
  Admin information architecture, scenario matrix, parameter precedence, and
  staged delivery plan.
- `notes/ISRAEL_REFERENCE_CATALOG.md` stores the 3.15.1 multi-market boundary,
  Israel fallback contract, evidence rules, and staged catalog plan.
- `notes/ISRAEL_REFERENCE_BASELINES_3_15_2.md` stores the active 3.15.2
  checkpoint, protected data, baseline rules, delivery sequence, verification,
  and decision gates.
- `notes/ISRAEL_REFERENCE_READINESS_2026_09_28.md` records the reproducible
  normalized-price and source-depth starting metrics for 3.15.2.
- `notes/ISRAEL_REFERENCE_SOURCE_REGISTER.md` records candidate Israeli market
  sources, their valid use, and evidence gaps before catalog activation.
- `notes/ISRAEL_REFERENCE_COVERAGE.md` tracks every furniture-material domain as
  observed, partial, or missing so common retail items cannot masquerade as a
  complete fallback catalog.
- `notes/LEGAL_CONSENT_VERIFIED_REGISTRATION.md` stores the 3.11.1 Terms,
  Privacy Policy, verified-signup, repeat-acceptance, and production acceptance
  contract.
- `notes/PRICE_CATALOG_UI.md` stores the 3.10.1 material-first Price Lists UI,
  source-library boundary, and scenario matrix.
- `notes/PRICE_SOURCE_AGENT.md` stores the active 3.12.1 extraction contract and
  the accepted `d99a594` Price Lists interaction rollback checkpoint.
- `notes/PRICE_LISTS_REBUILD_3_16_7.md` is the authoritative closed Price Lists
  rebuild contract and retained backlog. `notes/PRICE_LISTS_CHECKPOINT_3_16_7_2026_10_08.md`
  records the owner-accepted Price Sources UI checkpoint, protected behavior,
  and the narrowly deferred performance measurement.
- `notes/OBJECT_QUANTITY_AND_DETAIL_DRAFT_CHECKPOINT_3_15_24_2026_10_03.md`
  stores the canonical quantity, Object Detail draft/Approve architecture,
  rejected component-rerun path, Materials-zeroing root cause, migration, and
  production acceptance matrix for 3.15.24.
- `notes/PROCESSING_FILE_REVIEW_HANDOFF_CHECKPOINT_3_15_25_2026_10_03.md`
  stores the accepted Processing to File Review cache handoff, bounded browser
  observer handshake, rejected zero-delay experiment, verification evidence,
  and rollback points for 3.15.25.
- Keep notes short and update them when structure changes.
