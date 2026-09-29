# Price Source Pricing Identity Checkpoint

Task: 3.15.4
Date: 2026-09-29
Code checkpoint: `27afd06 feat: add missing canonical price classes`
Database checkpoint: production, additive Israel pricing expansion applied

## Outcome

Price Source can now resolve supplier material rows to an estimation price
class, rather than pretending that supplier SKU, decor, colour, or a full
physical product name must exactly equal one canonical material.

The global Israel catalog remains the fallback. A company's own item and
price stay private and remain first priority when Estimation is later enabled.

## Verified production data

- 2,832 active pricing identities;
- 2,832 active identity price models;
- zero active identities without an active price model;
- 12 new physical catalog positions added;
- 25 pricing identities added by the additive expansion;
- no existing catalog record, identity, source row, or company price was
  deleted or rewritten.

The expansion restores 13 MDF price classes missed by a generator defect and
adds the acceptance classes needed by the first representative supplier source:

- raw plywood: 16 mm and 17 mm;
- plastic-laminate-faced plywood: 17 mm;
- melamine-faced board: 17 mm and 27 mm;
- raw MDF and plastic-laminate-faced MDF: 17 mm;
- raw hardboard: 3.2 mm;
- laminated solid wood panels: pine 18/28 mm and oak 20/40 mm.

The existing canonical `Standard MDF, raw, 4 mm` and its active model were
also promoted into the restored MDF price class. It was not duplicated.

## Rules now protected

1. Supplier SKU is never a cross-supplier decision criterion. It can only be
   supporting evidence for the same supplier.
2. Colour, decor, pattern, marketing wording, and supplier naming do not
   create separate price classes.
3. Thickness is strict. A 17 mm input can never silently use 16 mm or 18 mm.
4. Generic plywood with no declared facing means raw plywood. Birch wording
   is species evidence, not a separate mandatory price class.
5. `white lacquer` on MDF maps to plastic-laminate-faced MDF for price
   routing.
6. `butcher block` is a recognition alias for `laminated solid wood panel`.
   It is not an independent material family.
7. Any unresolved or ambiguous class remains reviewable. It must not become a
   false automatic link.

## Root cause repaired

The first V3 seed classified normal MDF as HDF when a material belonged to the
shared catalog subcategory `MDF and HDF`. The generator now reads the concrete
material name before the shared subcategory. A regression test covers both MDF
and HDF.

## Acceptance evidence

Read-only replay, without rerunning URL extraction or modifying company data,
used archived Tsidky source `46e5cc7e-0f13-4287-a8f4-2edd66fa9e6b`.

- 26 of 26 material rows resolved to exactly one pricing identity;
- 9 operation-service rows remain excluded from material handling;
- 17 mm raw plywood, faced plywood, MDF, and melamine resolved only after
  explicit 17 mm price classes were created;
- pine and oak laminated-panel rows resolved; oak `butcher block` resolved to
  the same laminated solid-panel class;
- 17 targeted resolver and seed tests passed;
- `git diff --check` passed before commit.

This is code and database acceptance. It is not yet a real production browser
acceptance of a new source uploaded after `27afd06` deploys.

## What is intentionally not done

- Estimation does not yet consume pricing identities. It must be rebuilt only
  after Price Source identity acceptance and the remaining operations, labor,
  machinery, and subcontractor inputs are verified.
- Internal review UI is not built. Its future input is the bounded internal
  shortlist and its user-facing result is `review`, never the internal word
  `shortlist`.
- Price comparison disambiguation is not yet implemented. It may run only
  when source and canonical prices have compatible unit, currency, VAT, and
  scope, otherwise it must not fabricate a comparison.
- Performance has not been accepted. The prior URL run was slow and needs
  separate measurement after correctness acceptance.

## Next acceptance sequence

1. Confirm Railway has deployed `27afd06`.
2. Upload a new, distinct public supplier URL through production. Do not reuse
   an already archived source as a write test.
3. Inspect four outcomes separately: resolved materials, correctly excluded
   services, user-visible review rows, and failed-fetch diagnostics.
4. Repeat with a second source that differs in language, terminology, units,
   or material family.
5. Record every miss as one of: extraction defect, classification defect,
   canonical coverage gap, resolver-rule defect, or review-queue candidate.
   Do not add a rule until that classification is evidenced.

## Protected files and state

Only these files belong to this checkpoint commit:

- `tools/seed_material_pricing_identities.py`
- `tools/seed_material_pricing_expansion_v1.py`
- `use_cases/material_pricing_identity_resolution.py`
- `use_cases/price_source_material_resolution.py`
- `tests/test_seed_material_pricing_identities.py`
- `tests/test_material_pricing_identity_resolution.py`

Known unrelated dirty work remains outside this checkpoint, including CNC,
Estimation, auth, `.streamlit/`, `tmp/`, and staged catalog SQL artifacts.
