# Price Source Material Resolution

Task: 3.15.4
Status: implementation candidate
Started: 2026-09-28
Market: Israel (`IL`)

## Objective

Route Price Source rows through the shared material identity core after price
extraction. Reuse the extracted row for historical processing and never repeat
OCR merely to resolve material identity.

## Verified starting checkpoint

Production has the four 3.15.3 tables and one active resolver version,
`material_identity_v1`. The private alias table, candidate buffer, and event
log started empty. Production currently has no Price Source rows, company
material items, or company material offers.

## Candidate behavior

1. Price Source creates or reuses the private company material and price offer.
2. The shared resolver checks supplier SKU, confirmed company alias, exact
   Israel alias, hard attributes, then a department-bounded shortlist.
3. Exact resolution links both the Price Source row and the company material to
   `reference_material_id`.
4. A shortlist or new identity remains usable in the company catalog and enters
   `material_identity_candidates`. It never creates a global material.
5. Every attempted resolution appends an immutable event.
6. Repeating the same resolver version skips already processed rows. A manual
   row edit can force a new event and refresh the current pending candidate.
7. Identity-stage failure preserves the completed price import and records
   `retry_required` in the source summary for a later no-OCR retry.

Broad Price Source categories narrow only shortlist candidates. They do not
block stronger exact SKU, company alias, or market alias evidence.

## Verification

- exact alias links the company item and source row;
- non-exact match stays private and creates one review candidate;
- repeated same-version batch creates no duplicate event;
- isolated resolution and Price Source suite: 89 passed;
- complete repository suite: 657 passed;
- production no-OCR smoke pass: zero rows examined, as expected from the empty
  company Price Source tables.

## First production source

The first real supplier URL completed successfully with 47 extracted rows: 41
price-ready, one unresolved, and five excluded. The identity stage linked two
exact materials and created 39 bounded shortlists. No global identity was
created automatically.

The run also exposed a real latency regression. The agent took 60.6 seconds,
legacy row and offer persistence took about 31 seconds, and sequential identity
writes added about 36 seconds. The identity stage now batches new candidates,
source-row updates, and immutable events. A 40-row test verifies one write per
destination table. The complete suite now passes 657 tests. A new production
source is required to measure the deployed batch path.

## Next acceptance

Deploy the batching revision and measure a new representative production
source. Verify completion-state reset, unmatched behavior, refresh, and tenant
isolation. This stage does not activate Estimation fallback and does not publish
private company data to the Israel catalog.
