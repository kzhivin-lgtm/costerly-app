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
- `notes/PRICE_LISTS_REBUILD_3_16_7.md` is the authoritative active Price Lists
  rebuild contract and backlog. `notes/PRICE_LISTS_CHECKPOINT_3_16_7_2026_10_08.md`
  records the latest verified ingestion checkpoint, protected behavior, and
  prioritized continuation queue.
- `notes/OBJECT_QUANTITY_AND_DETAIL_DRAFT_CHECKPOINT_3_15_24_2026_10_03.md`
  stores the canonical quantity, Object Detail draft/Approve architecture,
  rejected component-rerun path, Materials-zeroing root cause, migration, and
  production acceptance matrix for 3.15.24.
- `notes/PROCESSING_FILE_REVIEW_HANDOFF_CHECKPOINT_3_15_25_2026_10_03.md`
  stores the accepted Processing to File Review cache handoff, bounded browser
  observer handshake, rejected zero-delay experiment, verification evidence,
  and rollback points for 3.15.25.
- Keep notes short and update them when structure changes.
