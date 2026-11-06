# Costerly AI Project Map

This file explains where code belongs so the project stays understandable.

## Entry Point

- `app.py` sets Streamlit page config, applies global CSS, initializes state, and routes to screens.
- It should stay small. Business logic does not belong here.

## UI Layer

- `screens/` contains one Streamlit screen per file.
- `ui/` contains shared rendering helpers used by multiple screens.
- `ui/browser_session.py` owns the tab-scoped Auth storage bridge. Its component
  must remain inside the hidden Sidebar and outside the main screen layout. It
  reads only during session bootstrap; browser store/clear commands must remain
  callback-free so they cannot consume the next user interaction.
- `styles/` contains CSS grouped by responsibility.
- `styles/base.py` owns global design tokens and base Streamlit overrides.

## Application Layer

- `use_cases/` contains product flows such as processing an uploaded RFQ.
- `use_cases/rfq_processing.py` runs detection, writes the result to Supabase, and loads File Review data.
- `use_cases/estimation.py` starts object estimation by creating pending estimate records from detected objects.
- Estimation V6.2 research checkpoint/restart: `notes/ESTIMATION_V6_2_HSL_N68_CHECKPOINT_2026_11_05.md`
  (3.17.4.5). Selected Front V2 + Planner V4, retained V5/V6 experiments, exact
  HSL evidence and pending defects. Authoritative task states remain in TODO.
- Additional owner-requested PARTIALLY COMPROMISED Front V3 + Planner V7 checkpoint:
  `notes/ESTIMATION_V6_2_FRONT_V3_PLANNER_V7_PARTIALLY_COMPROMISED_CHECKPOINT_2026_11_06.md`
  (same 3.17.4.5). Exact Lev2 paired-run evidence, known failures and private
  recovery archive. Explicit research pair, not a change to V2/V4 defaults or
  a production release. Earlier checkpoint remains protected.
- CB Parts V1, 3.17.4.6: `agents/prompts/cb_parts_v1.md`, opt-in inside
  `run_estimation_assembly_bom_agent(cb_parts_scope=...)`; deterministic expansion
  in `use_cases/estimation_cb_parts.py`, local replay `tools/probe_cb_parts.py`.
  One Calculate request per object, no additional Parts stage. Reuses 2VN,
  slide-depth policy and existing assembly BOM shape. Not a production route;
  recent saved Front/Planner probes are not integrated document-wide Analyze.
  V1 live acceptance FAILED (0/3): timeout/thinking exhaustion, then malformed
  and semantically wrong output with thinking disabled. See TODO and
  `notes/evidence/cb-parts-v1-2026-11-06/lev2-calculation.json` before reuse.
- Historical Parts diagnostic **CB Parts V2**, same 3.17.4.6, owner-requested
  count-only list. `agents/prompts/cb_parts_v2.md`, `validate_cb_part_counts`.
  `--parts-version V2` replays it; V1 also remains available.
  Lev2 shape passes in 5.676 s, semantic defects retained, not a production BOM.
  Evidence: `notes/evidence/cb-parts-v2-2026-11-06/lev2-counts.json`.
- Current opt-in Parts diagnostic: **CB Parts V3**, same 3.17.4.6,
  `agents/prompts/cb_parts_v3.md`, `compose_cb_sized_parts`, probe default V3.
  Quantities and sizes, declared unit conversion, 17/30 mm defaults, drawer
  depth arithmetic. One call, no legacy BOM/material resolution or extra stage.
  Lev2 16.529 s: format passes, B08 geometry fails visual review; not accepted.
  `notes/evidence/cb-parts-v3-2026-11-06/lev2-sized-parts.json` preserves raw
  response plus separate normalized rows. Front/Planner/production unchanged.
- CB Parts V3.1 explicit experiment: `agents/prompts/cb_parts_v3_1.md`,
  `--parts-version V3.1`. V3 plus one universal width-span instruction, unchanged
  schema/geometry code. Lev2 13.439 s, failed block-versus-bay width consistency,
  missing divider. Not promoted over V3. Raw evidence:
  `notes/evidence/cb-parts-v3-1-2026-11-06/lev2-sized-parts.json`.
- CB Parts V3.2 explicit experiment: `agents/prompts/cb_parts_v3_2.md`,
  `--parts-version V3.2`. Adds bay sum and shared mounting wall reminder.
  Lev2 15.041 s: partition PASS, block/bay sum FAIL. No default promotion.
  `notes/evidence/cb-parts-v3-2-2026-11-06/lev2-sized-parts.json`.
  Owner-requested repeatability series (two additional identical requests):
  `notes/evidence/cb-parts-v3-2-2026-11-06/three-run-repeatability.json`.
  B08 widths 500/600/760 mm and partition 1/0/1, stability not established.
  Requested checkpoint paused before creation, pending owner review.
- CB Parts V3.3 opt-in bay contract, same 3.17.4.6:
  `agents/prompts/cb_parts_v3_3.md`, `use_cases/estimation_cb_bays.py`,
  `tests/test_cb_parts_v3_3.py`, `--parts-version V3.3`. Straight-carcass width
  and common construction derive from bays; nonrectangular geometry is explicit.
  V3.2 diagnostic `--omit-block-locator B08` removes only that outgoing region,
  after validating the original scope; never edits saved upstream artifacts.
  `notes/evidence/cb-parts-v3-3-2026-11-06/locator-and-bay-trials.json` preserves
  ablation failure and two V3.3 whole-object height failures. B08 isolated
  width/partition checks pass, model-estimated dimensions remain unverified.
  No default promotion or checkpoint; document-wide Analyze integration pending.
- Latest owner-requested Parts research checkpoint/restart, same 3.17.4.6:
  `notes/ESTIMATION_V6_2_CB_PARTS_V3_3_CHECKPOINT_2026_11_06.md`, immutable tag
  `estimation-v6.2-cb-parts-v3.3-research-checkpoint-2026-11-06`.
  Supersedes the earlier pending-preservation status, not its raw findings.
  Four identical requests: B08 derived widths 900/800/620/1000 mm, one divider
  each; complete objects 0/4 pass. Exact replies, per-block audits, 22-file
  private archive/manifest and safe restart are documented. No default promotion
  or deploy. Preserve as research with known limits, stop further experiments.
- Post-checkpoint explicitly approved experiment: CB Parts V3.4,
  `agents/prompts/cb_parts_v3_4.md`, `use_cases/estimation_cb_spans.py`,
  `--parts-version V3.4`. Conserves cross-block dimension-span totals from
  model-associated endpoints/weights before the V3.3 compiler. One Lev2 trial
  failed topology/height despite conserved totals; no default/checkpoint change.
  `notes/evidence/cb-parts-v3-4-2026-11-06/lev2-span-trial.json`.
- Subsequently approved fixed-topology diagnostic: CB Parts V3.5,
  `agents/prompts/cb_parts_v3_5.md`, `use_cases/estimation_cb_width_probe.py`,
  `tests/test_cb_parts_v3_5.py`. Probe uses `--parts-version V3.5` plus
  `--topology-witness` pointing to the original V3.3 replay. Checks source
  identity, freezes only bay/front IDs, reuses span allocator, emits widths
  for review, never a Parts BOM. One Lev2 trial still misassigned 151 cm and
  failed on null fallback widths. Fixed topology alone is insufficient here.
  `notes/evidence/cb-parts-v3-5-2026-11-06/lev2-fixed-topology-trial.json`.
  Research checkpoint/defaults untouched; no new production stage or deploy.
- Owner-selected next architecture, CB Parts V4, same 3.17.4.6:
  `agents/prompts/cb_parts_v4.md`, `use_cases/estimation_cb_v4.py`,
  `tests/test_cb_parts_v4.py`. `tools/probe_cb_parts.py --parts-version V4`
  takes only `--front-witness`, no prior Planner. Physical dimensional runs
  precede workshop groups, reuse `compose_cb_bay_parts` and `build_assembly_bom`.
  Returns material-bearing parts/BOM, not only a width audit. One request.
  Three whole-object trials failed (Lev2/Lev1/N68), not promoted:
  `notes/evidence/cb-parts-v4-2026-11-06/three-object-trials.json`.
  Next owner-selected direction is measured input preparation, not worked
  examples; no implementation of that direction yet. Full contract/limits in
  the Cabinet Block contract and authoritative TODO, no competing backlog.
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
