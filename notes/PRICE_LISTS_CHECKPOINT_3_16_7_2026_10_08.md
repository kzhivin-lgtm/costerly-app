# Price Lists checkpoint, 3.16.7, 2026-10-08

## Authority and state

This is the full checkpoint for the active Price Lists rebuild. The detailed
contract and active Price Lists backlog remain
`notes/PRICE_LISTS_REBUILD_3_16_7.md`; this document is its verified handoff
index. The old 3.12.1 record in `notes/TODO.md` is historical only.

- Work number: `3.16.7`
- Branch: `main`
- Latest Price Source commits: `37342bb`, `c50765e`, `2fda016`, `834ee68`
- Recovery archives exist under `backups/` for each recent price change. They
  are rollback inputs, not production acceptance.

## Protected contract

1. **Supplier**: resolve seller or issuer, never recipient. H.P., `ח.פ.`,
   `ע.מ.` and `ע.פ.` with a nine-digit value identify the supplier. Existing
   canonical supplier identity wins on identifier match. Material changes must
   not reopen this path.
2. **Evidence**: source spelling, document number, raw rows, original text,
   SKU and printed price stay auditable. Canonical records never overwrite them.
3. **Matching**: within a supplier, SKU is strong confirmation, never a
   cross-supplier key. Price, entity, thickness or dimensions, and decisive
   construction or finish drive merge. Quantity is never an identity criterion.
4. **Units and consumables**: absent purchase unit defaults to one item unless
   category identifies a package or pair. Drawer slides default to left-right
   set. Consumables never enter the active catalog.
5. **Prices**: quantity, unit price and total are separate. Never derive a
   printed price from total divided by quantity. Every JPEG, PNG, HEIC and TIFF
   priced row receives enlarged source-table visual verification before active
   persistence. PDF text layers and XLSX/CSV cells keep their native paths.
   Visual ambiguity means Review, not activation. Currency rounding noise does
   not rewrite printed price.
6. **VAT**: retain evidenced basis. A missing totals page is not price failure.
   Legal entity labels do not currently infer VAT.
7. **Delete/UI**: deletion removes visible source-owned records immediately;
   storage/database cleanup follows independently. Background completion cannot
   reset active upload, discard selection, duplicate sections, or collapse
   Source Library.
8. **Cycle notice**: only successful extraction has green result. It clears at
   selection/drop, remains across navigation in the same session, and reports
   `merged`, `already in catalog`, and `Already processed` distinctly.
9. **Order**: upload controls first, then Catalog, Material Jobs, Review, Source
   Library. The controls must remain usable while data loads.
10. **Future material naming**: names are deterministic display formatting over
    structured identity: entity, primary attribute, up to four discriminating
    attributes, optional brand. AISI and steel grades are technical attributes;
    SKU stays supplier-scoped.

## Verified current evidence

Production photo source `IMAGE 2026-10-05 19:04:55.jpg`, invoice `63385`,
completed with five ready rows and no unresolved/excluded rows. The previously
systematic hinge failure for SKU `956A1004WL` is now stored as quantity 5,
ILS 27.50, total ILS 137.50.

Recorded timings: OCR 0.444 s, primary Price Source agent 16.361 s, visual
table verifier 2.924 s, full cycle 45.508 s. The verifier added roughly 2.6 s
of model time versus the immediately preceding photo path, not the suspected
large latency regression.

The final checkpoint suite reports `400 passed, 25 warnings` across Price
Source, OCR and company-access tests. This is representative production
evidence, not the completed authenticated acceptance matrix.

## Authoritative continuation backlog

### P0: close source ingestion with authenticated production evidence

1. **3.16.7.1 Material Job classification and persistence**
   - Status: implementation exists, production acceptance pending
   - Ensure `פס חיתוך + קנט` and equivalent supplier operation text produces a
     supplier operation offer, never a Wood Supplies material. Repeat evidence
     must reuse one operation and preserve source wording and price.

2. **3.16.7.2 VAT fallback for incomplete invoices**
   - Status: pending policy decision
   - Define line-only invoice VAT handling without treating absent totals as a
     price mismatch. Do not infer from legal entity labels.

3. **3.16.7.3 Source-ingestion acceptance matrix**
   - Status: pending, after items 1 and 2
   - Run text PDF, scanned PDF, photo, spreadsheet, repeat supplier, supplier
     price change, cross-supplier offer, consecutive delete, and Profile
     navigation persistence in authenticated production.

4. **3.16.7.4 Lifecycle boundary acceptance**
   - Status: implementation exists, production acceptance pending
   - Delete two sources and immediately select/extract one new file. Verify one
     server trace/source, no stale visible row, no uploader reset. Delete final
     source and verify natural zero state without reload.

5. **3.16.7.5 Cycle terminology acceptance**
   - Status: implementation exists, production acceptance pending
   - Verify real completion copy distinguishes `merged`, `already in catalog`,
     and `Already processed`.

6. **3.16.7.6 Image-table price verification acceptance**
   - Status: representative production evidence verified, broader acceptance
     pending
   - Keep conservative image-only verification until measured acceptance data
     shows narrowing is safe.

### P1: improvements after P0 closure

1. **3.16.7.7 Source Library invoice label**: document number under supplier,
   filename only when number is absent.
2. **3.16.7.8 Bilingual brand catalog**: department-scoped aliases, initially
   Blum, Hettich, Egger, Sayerlack and Homag. Preserve brand, never let it alone
   classify an item.
3. **3.16.7.9 Price Lists first paint**: controls interactive before projections,
   then independently load Catalog, Material Jobs, Review, Source Library with
   no duplication/reordering. Current serial read baseline: 0.273 s source,
   0.660 s catalog, 0.323 s Review, 0.536 s Material Jobs, plus render time.
4. **3.16.7.10 Unified material-normalisation design**: requires explicit design
   approval before implementation. Define shared entity, primary spec,
   dimensions, technical grade, substrate, finish, construction, color, brand,
   and supplier-only SKU, then one canonical formatter for Price Source,
   company catalog, Israel Price List and Detection.

### Deferred

1. **3.16.7.11 Estimation resolver**: choose eligible offers only after source
   ingestion acceptance. It must not mutate source evidence, supplier identity,
   catalog identity or offer history.
2. **3.12.3 Batch Price Source ingestion**: post-MVP bounded multi-source queue.
3. Brand expansion and market-reference enrichment: after the normalization
   schema is approved.

### Global backlog retained, outside 3.16.7

`notes/TODO.md` remains the global queue for 3.15.24 canonical object quantity,
3.15.25 File Review handoff, 3.15.26 sleeping-session recovery, 3.16.3
Processing/File Review polish, 3.16.5 Project Summary XLS, 3.16.6 Unknown
Partner, Detection dimensions, cross-agent token-cost reporting, and deferred
legal-template research. None is silently pulled into this Price Lists task.

## Non-goals and next instruction

Do not reopen supplier matching while fixing material jobs, unit behavior,
price arithmetic or UI. Do not modify upload/auth while improving first paint.
Do not merge via quantity or use SKU as cross-supplier display identity. Do not
retroactively reclassify history without an approved repair plan.

Resume at **3.16.7.1, Material Job production acceptance**, unless the owner
explicitly selects another P0 item. Inspect the authoritative Price Lists
backlog first, preserve the protected contract above, and perform the smallest
representative acceptance scenario.
