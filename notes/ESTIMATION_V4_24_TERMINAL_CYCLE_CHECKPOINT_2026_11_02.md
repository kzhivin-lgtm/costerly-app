# Estimation V4.24 terminal-cycle checkpoint

Date: 2026-11-02

Work: `3.17.4.3`, Estimation V4 material-only path.

Code baseline: `797dc33` (`fix(estimation-v4.24): separate purchase format
metadata`), documented at `6fb26ed`. At checkpoint time `origin/main` was
verified at `6fb26ed9e5ee8e0d9838aa0ef77b0b98b26ab46c`.

## What this checkpoint establishes

This is a **technical terminal-cycle checkpoint**, not material-quote
acceptance. It establishes that a fresh production run completed all persisted
V4 stages after the V4.24 purchase-format serialization repair. It does not
establish that the inferred BOM or the selected material sources are correct.

The V4 contract remains material-only: Detection owns object identity, the
immutable `estimation_input_v4` owns supplied evidence, the Assembly/BOM path
emits demand, and Material Engine owns Company Catalog -> Israel Reference ->
Assumption Fallback selection and estimate-wide sheet rounding. Labor,
manufacturing, overhead and final selling price remain outside this checkpoint.

## Production witness

| Field | Verified value |
| --- | --- |
| run | `run_d82f58af38f84a4eb6fc3a2dbb8faeab` |
| estimate | `run_d82f58af38f84a4eb6fc3a2dbb8faeab_estimate_20261102202039` |
| object | `object-001`, `Cabinet`, quantity `1` |
| immutable input | `aa28c944-5395-40c0-be5d-028b7973f687`, contract `estimation_input_v4` |
| terminal state | `completed`, `materials_costed`, 100% |
| material cost | ILS 800.00 excl. VAT, ILS 144.00 VAT, ILS 944.00 total |
| active Assembly prompt | `estimation_assembly_bom_v4_24` |
| visual model | `claude-haiku-4-5-20251001` |

Persisted stage order was complete: Dimension Graph, evidence artifact load,
Assembly Agent, structural composition and BOM persistence, Material Plan,
publisher, then allocation. The successful Material Plan record was written at
`2026-11-02T20:21:23Z`; publication and allocation markers followed at
`20:21:25Z` and `20:21:28Z`.

## Persisted material result

| Material | Source marker | Net required material | Purchase unit | Purchase quantity | Total excl. VAT |
| --- | --- | ---: | --- | ---: | ---: |
| Veneered MDF, 18 mm | A | 4.2 m2 | sheet 2440 x 2653 mm | 1 sheet | ILS 200 |
| LDSP, 18 mm | A | 3.6 m2 | sheet 2653 x 1220 mm | 2 sheets | ILS 400 |
| Hardboard, 3 mm | A | 4.2 m2 | sheet 2440 x 2653 mm | 1 sheet | ILS 200 |

The source result is preserved exactly as generated. The V4.24 formatter now
stores only physical purchase dimensions in the visible snapshot, so the
catalog metadata field `format_source` cannot again be coerced to a number.

## Explicit non-acceptance and next diagnosis

All three lines are `A`. This is not accepted material-resolution behavior for
a company that already has the corresponding catalog positions. The persisted
reasons are specific:

* Veneered MDF: `material_pricing_key_incomplete`.
* LDSP and Hardboard: `no_physically_compatible_company_or_israel_candidate`.

Therefore the next action is a read-only Resolver audit for company `610`:
compare the three emitted Family/Pricing-Key/specification demands against the
active Company Catalog candidates and identify the first missing or incompatible
field. Do not change the resolver or create catalog guesses from this
checkpoint alone.

## Protected behavior

* V4.24 keeps technical failure separate from a missing catalog match. A
  missing compatible candidate is immediately priced through Assumption
  Fallback, while a persistence or serialization fault is terminally failed
  with a bounded trace.
* The successful cycle remains inspectable by immutable input ID, persisted BOM
  facts, Material Plan snapshot and stage markers. No provider prompt, raw
  response, chain-of-thought or secret is stored in those diagnostics.
* This checkpoint makes no Detection-code, OCR, object-boundary, labor,
  manufacturing or overhead claim.
