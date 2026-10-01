# Estimation v2 functional checkpoint, 2026-10-01

## Status and acceptance boundary

This checkpoint establishes a working production File Review to Objects to
Object Detail cycle for Estimation v2. Every non-ignored object in the accepted
production run received editable material, labor and overhead rows, a persisted
self cost and a source preview. Objects displays provisional self cost and sale
price even when downstream diagnostics retain `review_required`.

This checkpoint does not accept estimation quality. Material classification,
quantities, catalog identity selection, prices, labor duration, machinery
routing and overhead accuracy remain subject to audit. `review_required` is an
audit signal and no longer suppresses an available provisional estimate.

## Production evidence

- Run: `run_150a23e06697467397501e1d27427b62`
- Estimate: `run_150a23e06697467397501e1d27427b62_estimate_20261001175237`
- Source: `page-23.pdf`, one Russian-language page, 365,918 bytes
- Company: `610`
- Object count: 3
- Terminal failures: 0
- Object Facts: 3 ready results
- Published object statuses: 1 completed, 2 review_required
- Objects with persisted self cost: 3 of 3
- Object Detail rows: 81 total, 20 material, 22 labor, 39 overhead
- Diagnostic rows: 14 marked for review, including 2 missing exact prices
- Extracted facts: 12 materials, 22 labor operations, 3 manufacturing features,
  2 purchased components
- Total modeled labor: 8.5739 hours

Persisted self costs, excluding VAT:

- object-001, Wall shelving unit: ILS 2,743.14
- object-002, Wall cabinet: ILS 2,574.05
- object-003, Display shelf: ILS 598.21
- project objects subtotal: ILS 5,915.40

These values prove persistence and UI publication only. They are not accepted
as accurate estimates.

## Timing

- OCR provider wall time: 0.649 seconds
- Detection orchestration including OCR: 13.646 seconds
- Deferred Naming wall interval: 2.483 seconds, provider timing 1.392 seconds
- Upload processing start through Naming completion: 16.129 seconds
- Estimate shell creation through final object publication: 50.468 seconds
- Haiku page fact extraction for all 3 objects: 14.152 seconds
- Deterministic publication after Haiku response through final object: 5.787 seconds
- Unattributed interval from final input persistence to Haiku request: 24.735 seconds

The 24.735-second interval is not yet instrumented precisely. It may include
catalog/context loading, evidence retrieval and worker scheduling, but no causal
allocation is accepted without phase telemetry.

## Token and cost telemetry

Estimation v2 used `claude-haiku-4-5-20251001` with prompt version
`estimation_page_facts_agent_v15_nonblocking_approximations`:

- input tokens: 7,005
- output tokens: 2,580
- input cost: USD 0.007005
- output cost: USD 0.012900
- Estimation total: USD 0.019905
- average Estimation model cost per object: USD 0.006635

Naming recorded 1,313 input tokens and 73 output tokens inside raw telemetry,
but its top-level cost fields are null. Detection has no separate usage event
for this run, and OCR cost is also null. Therefore USD 0.019905 is the verified
Estimation cost, not the complete upload-to-estimate cost. Full-cycle cost is
unknown until Detection, Naming and OCR cost telemetry is completed.

## Verified implementation state

- `305f508 fix: keep estimation domain uncertainty nonblocking`
- `25cf3ee fix: show provisional totals on objects`
- full automated suite: 827 passed, 27 warnings
- `git diff --check`: passed
- `HEAD...origin/main`: 0 0 before this checkpoint note
- production behavior observed by the owner: all objects calculated, persisted
  and displayed on Objects

## Protected behavior

- File Review controls which objects enter Estimation.
- Estimation uses one page-level Haiku extraction with one preview per object.
- Domain uncertainty produces logged approximations or review diagnostics, not
  terminal object failure.
- Technical failures remain distinguishable from domain uncertainty.
- Object Detail remains editable and retains source previews.
- Self cost excludes Delivery and Installation.
- Suggested sale price is self cost plus 30 percent.
- Delivery is 3 percent and Installation is 10 percent of the objects sale
  subtotal.
- Consumables and Packaging remain formula rows in Materials.

## Next ordered work

1. Instrument and reduce the 24.735-second pre-Haiku interval.
2. Complete cost telemetry for Detection, Naming and OCR.
3. Execute the P0 Israel Price List taxonomy and pricing-identity normalization,
   beginning with MDF/HDF, without mixing incompatible subcategories.
4. Audit estimate quality through representative golden production documents.

## Dirty worktree preservation

The existing uncommitted Material Resolution and Price Source changes,
`.streamlit/`, `db/sql/3_15_4_israel_global_catalog_v1_parts/` and `tmp/` were
not staged or modified by this checkpoint commit.
