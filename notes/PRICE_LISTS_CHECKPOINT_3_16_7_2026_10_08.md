# Price Lists checkpoint, 3.16.7, 2026-10-08

## Authority and state

This is the full checkpoint for the active Price Lists rebuild. The detailed
contract and active Price Lists backlog remain
`notes/PRICE_LISTS_REBUILD_3_16_7.md`; this document is its verified handoff
index. The old 3.12.1 record in `notes/TODO.md` is historical only.

- Work number: `3.16.7`
- Branch: `main`
- Latest Price Source commits: `c6d289b`, `97c3c73`, `69da191`, `2528ad6`,
  `6d77806`, `41bedd1`, `62920ad`, `5905a4e`
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
6. **VAT**: source totals win. Otherwise use seller legal identifier, canonical
   supplier history, then the Israeli supplier-price default. Persist both VAT
   basis and rate, so a partial page displays its VAT-inclusive price. The
   statutory fallback is 17% before 2025-01-01 and 18% from that date.
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

### Implementation checkpoint, 2026-10-08, supplier and invoice identity

This is a code-and-data-contract checkpoint, pending the next authenticated
four-photo acceptance run. It is not a claim that the entire Price Lists work
is accepted.

- A valid nine-digit seller legal identifier is decisive. Phone-like values
  beginning with zero are rejected. The recognised forms are `ח.פ.`, `ע.מ.`,
  `ע.פ.` and H.P.; `בע"מ` remains seller-header and company-form evidence.
- An issuer header without a readable identifier may join exactly one existing
  legal supplier when its same-script normalised name differs by at most one
  OCR edit for a short name or two for a longer name. Cross-script fuzzy merge
  and shared-word merge are forbidden. This prevents both duplicate suppliers
  from a one-letter OCR error and a false merge between ASh Pirzul and YAAD
  PIRZUL 1984.
- Explicit invoice labels determine the document number, including
  `חשבונית מס - קבלה`; invoice identifiers can contain letters, digits and
  punctuation. An internal customer number is never substituted merely because
  it looks numeric.
- A supplier-source row with no VAT evidence defaults to VAT-excluded even if
  OCR called its origin `unknown`. A later explicit document for that canonical
  supplier confirms the inferred basis. Explicit `company_internal` sources
  remain outside this default.
- The extraction result remembers the selection that started its worker. A
  later fragment rerender cannot make the successful second-cycle result look
  stale and remove the green result panel.
- Verification at this checkpoint: `tests/test_price_sources.py` and
  `tests/test_company_access.py`, 460 passed, 25 warnings; `git diff --check`
  passed. The production four-source rerun is still required.

## Verified current evidence

Production photo source `IMAGE 2026-10-05 19:04:55.jpg`, invoice `63385`,
completed with five ready rows and no unresolved/excluded rows. The previously
systematic hinge failure for SKU `956A1004WL` is now stored as quantity 5,
ILS 27.50, total ILS 137.50.

Recorded timings: OCR 0.444 s, primary Price Source agent 16.361 s, visual
table verifier 2.924 s, full cycle 45.508 s. The verifier added roughly 2.6 s
of model time versus the immediately preceding photo path, not the suspected
large latency regression.

The final checkpoint suite reports `405 passed, 25 warnings` across Price
Source, OCR and company-access tests. This is representative production
evidence, not the completed authenticated acceptance matrix.

### Supplementary production checkpoint, 2026-10-08

Production source `10d81812-92e0-433b-bf87-325e653c85da`, invoice `66536`,
dated 2024-12-31, is the verified VAT and Review-state acceptance sample:

- canonical supplier history supplied VAT-excluded basis and the persisted
  rate is 17%; no document-total page was required;
- all 14 material rows are active, with zero Review rows;
- 9 offers are new and 5 existing offers are updated, which is the expected
  same-supplier merge result rather than loss of source lines;
- the displayed-price case ILS 2.63 x 30 = ILS 78.75 is accepted as normal
  hidden-third-decimal rounding. The printed price remains ILS 2.63;
- `סכין חותך זכוכית` is a glass-cutting tool/consumable and is excluded before
  material or offer creation. It must never classify as Glass.

The state transition is now deterministic: after the persistence layer has a
canonical supplier and VAT fact, every unresolved row is re-evaluated against
real price, unit and material blockers. Agent wording for missing supplier or
VAT evidence cannot by itself leave a valid row in Review.

## Authoritative continuation backlog

### P0: close source ingestion with authenticated production evidence

1. **3.16.7.1 Material Job classification and persistence**
   - Status: moved to active 3.17.1
   - Ensure `פס חיתוך + קנט` and equivalent supplier operation text produces a
     supplier operation offer, never a Wood Supplies material. Repeat evidence
     must reuse one operation and preserve source wording and price.

2. **3.16.7.2 VAT fallback for incomplete invoices**
   - Status: implementation checkpoint complete, production recheck pending
   - Supplier invoices resolve VAT by current-document evidence, seller legal
     identity, supplier history, then the Israeli default. Partial pages retain
     a date-appropriate rate and do not enter Review only because totals are
     absent. Broader matrix evidence remains under 3.16.7.3.

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
   shows narrowing is safe. Printed two-decimal price versus line total may
     differ by ordinary currency rounding, capped at ILS 1 per line, without
   deriving or replacing the printed price.

7. **3.17.1.1 Shelf-support taxonomy boundary**
   - Status: active, before next four-source rerun
   - Outcome: `מתלה מדף` and abbreviated/OCR variants are Hardware shelf
     supports, never MDF or Wood Sheets. Under the approved consumables
     boundary, a generic shelf support is excluded from the purchasable catalog
     while its source evidence remains available for audit.
   - Protected dependency: this is taxonomy-only. It must not alter supplier,
     invoice-number, VAT, source-deletion or cycle-result paths.

8. **3.16.7.12 Stable Price Lists loading and deletion feedback**
   - Status: active. Extraction-accounting portion is implemented under
     3.17.1.2; stable loading and deletion interaction remain pending.
   - Outcome: source deletion must neither collapse Source Library nor move the
     viewport. Consecutive confirmed deletes must remain actionable while the
     database worker finishes. Use one minimal in-place `Updating…` state when
     interactions must be temporarily unavailable, rather than rerender jumps
     or per-section status copy.
   - Initial loading must show one `Loading catalog…` state with a spinner.
     It must not sequentially display `Loading Material Jobs`, `Loading
     Review`, or `Loading Source Library`. Preserve independent background
     reads and fast upload controls, but keep the visual transition singular
     and stable.
   - Acceptance: delete two adjacent sources rapidly without losing the second
     click, collapsing the library or changing scroll position. On cold entry,
     see one loading state only, then the final ordered view.
   - Implementation update, 2026-10-09: a completed background purge mutates
     the already visible projection snapshot in place instead of forcing a full
     app rerun. A confirmed delete preserves the open Source Library and the
     current scroll location. The initial page shows only `Loading catalog…`
     with a spinner until all independent projections are ready.
   - Extraction accounting: the terminal result must account for every
     price-table line read from every source. Rows excluded in an early
     consumables/non-candidate pass count as `excluded`; they must not vanish
     from the total merely because no source-row record or offer is persisted.

9. **3.17.1.2 Hardware taxonomy and complete extraction accounting**
   - Status: implementation verified locally, authenticated production
     acceptance pending.
   - Outcome: preserve every extracted table row in cycle accounting, including
     rows excluded before persistence. Classify `push-to-open` and butterfly
     catches as Hardware door closures, not hinges. Classify plinth clips as
     Hardware pieces, not drawer-slide sets.
   - Protected dependency: supplier resolution, invoice matching, VAT and
     merge logic are out of scope.
   - Temporary catalog boundary, 2026-10-09: a material with a printed source
     price below ₪2.00 per purchase unit excluding VAT is excluded from the
     active catalog but remains included in the source's excluded count.
     Operation-service rows are unaffected. This is a temporary price floor,
     not a replacement for the durable consumables taxonomy.
   - Normalisation requirement: drawer-runner length, such as 500, 550, 600
     or 750 mm, is a required primary identity attribute, equivalent to sheet
     thickness. It must be parsed as millimetres and used for comparison and
     merge, never reduced to an arbitrary `width` value or optional prose.
   - Supplier settings, 2026-10-09: every Source exposes the same canonical
     supplier card. Saving canonical supplier name, HeadPay or VAT from any
     one source updates the entire supplier lane, including its sources,
     material offers and Material Jobs. No source is privileged as a parent.
     The former canonical name becomes a private manual alias, and ingestion
     matches incoming OCR against all retained aliases as well as HeadPay.
   - Compact price card, 2026-10-09: the row editor contains only Material
     name, Material type, Source price and Estimation unit. VAT, currency,
     source/purchase units and conversion are source-level or persisted
   defaults, not routine row-level controls.

10. **3.16.7.13 Multi-invoice PDF router and compact Review reason**
   - Status: implemented locally, owner acceptance pending.
   - Outcome: a PDF stays on the current single-document path unless its
     already-prepared native text or direct-PDF OCR proves at least two
     distinct `(issuer identity, invoice number)` pairs. Only then it is split
     in memory into one-page PDF inputs. The existing supplier plus invoice
     merge contract groups pages of the same invoice, while distinct proven
     invoices become distinct Source Library records.
   - Cost boundary: the router never invokes OCR only to classify a PDF. It
     reuses the text/OCR pass required for extraction. A normal generated PDF
     and a multi-page single invoice keep the fast path unchanged.
   - Safety boundary: page count, scan-like metadata and filename are hints at
     most, never a routing decision. A page without a proven separate identity
     cannot cause a batch-adjacency merge.
   - Review contract: Source Review exposes only `Price` and `Unit`. The
     reason is exactly one of those words and the corresponding editable label
     is red. Name, category and supplier identity remain immutable in Review,
     so correcting evidence cannot split a catalog merge.

### P1: improvements after P0 closure

1. **3.16.7.7 Source Library invoice label**: document number under supplier,
   filename only when number is absent.
2. **3.16.7.8 Bilingual brand catalog**: moved to active 3.17.1.
3. **3.16.7.9 Price Lists first paint**: implementation complete, production
   behavior check pending. Controls render before projections, then Catalog,
   Material Jobs, Review and Source Library load through independent read-only
   background tasks. A completed task does not refresh an active selection.
   Current pre-change serial read baseline: 0.273 s source, 0.660 s catalog,
   0.323 s Review, 0.536 s Material Jobs, plus render time.
4. **3.16.7.10 Unified material-normalisation design**: moved to active 3.17.1.

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
