# Price Source XLS resilience and resolver checkpoint, 2026-10-12

Work: 3.17.2.12, Price Source upload resilience

Status: production XLSX path verified. Legacy XLS and user-facing cancellation
remain explicit production acceptance checks.

## Code checkpoint

- `40f4739` adds bounded spreadsheet imports, selection validation, and real
  cancellation plumbing.
- `e0b6176` synchronizes the legacy XLS reader in the locked Railway build.
- `7d93348` reconciles supplier-operation taxonomy with the canonical operation
  registry and degrades any future registry mismatch to Review evidence instead
  of failing the whole source.

The checkpoint branch is `main` at `7d93348`.

## Production evidence

The controlled 44-row XLSX source was successfully imported for company 610:

- 40 active source rows, 37 active material offers, and 3 active supplier
  operation offers;
- 4 excluded consumable rows;
- 0 Review rows;
- the material catalog contains 43 active prices after the import, including
  pre-existing offers.

The first apparent result claiming `40 already in catalog` with agent duration
of `0.0 s` was not an extraction. It was the exact-content duplicate fast path,
which returns the existing source summary without calling the agent or changing
catalog data. Re-importing after deleting the source produced the real 40-row
write above.

## Resolver-status snapshot

The 43 active material prices resolve as follows:

- green, 17: canonical Israel Reference link is complete;
- yellow, 16: material family is known, but a pricing-key fact remains absent;
- blue, 10: pricing key is sufficient, but no Israel Reference candidate link
  exists yet.

Representative yellow gaps are purchasable sheet format, drawer-slide nominal
length, metal base material, profile, and wall thickness. Blue is catalog
coverage work, not a reason to discard the company price.

## Protected behaviour

- A supplier source never creates a canonical operation at import time.
- `.xls`, `.xlsx`, CSV, PDF, and supported image formats remain valid Price
  Source inputs.
- A registry mismatch preserves the row as Review evidence with
  `reference_operation_missing`; it does not create a partial silent catalog or
  abort unrelated rows.
- Existing user work in `.streamlit/`, `tmp/`, Israel-catalog SQL parts, and
  the two unrelated Price List notes is excluded from this checkpoint.

## Verification

- `tests/test_price_sources.py`: 320 passed after the supplier-operation fix.
- read-only production inspection confirms the controlled XLSX source,
  active offers, active material rows, supplier-operation offers, and live
  resolver status distribution above.

## Remaining acceptance

1. Upload a legacy `.xls` file in production.
2. Start an extraction and use Cancel before persistence, verifying terminal
   Cancelled state and no created source or offers.
3. Resolve the yellow pricing-key gaps and blue Israel Reference coverage as
   catalog work, not as an ingestion regression.
