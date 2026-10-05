# Price Lists rebuild, 3.16.7

Status: active. Stage 1 is the additive data contract. It does not change the
current Price Lists UI or automatically modify any existing source.

## Decision

`reference_operations` is the single global catalog of normalised work. It is
already used by the manufacturing and labor foundations. Price Lists must not
create a parallel work catalog.

A supplier service is distinct from a material:

```text
source row -> reference operation -> company supplier operation offer
source row -> company material item -> company material offer
```

The first path is for subcontract work. The second is for purchasable material.
No source row may follow both paths unless a future approved split creates
separate source rows with separate evidence.

## Stage-1 storage contract

- `company_price_sources.source_supplier_name` retains the exact spelling found
  in the evidence. `supplier_id` is the selected canonical supplier.
- `company_supplier_aliases` records source-observed and manually confirmed
  company-private supplier aliases. It enables a later reversible supplier
  merge without overwriting source evidence.
- `company_price_source_rows.row_kind` separates `material`,
  `operation_service`, and `non_catalog` rows. Existing rows retain the
  additive default `material`; no historical row is reclassified in this stage.
- `reference_operation_id` connects an operation-service row to the existing
  global catalog.
- `company_supplier_operation_offers` is a versioned, company-private price
  observation for that operation and supplier. It points to the exact source
  and source row, preserves VAT and currency, and cannot be a material offer.

## Bundles and units

`supplier_cut_and_edge_banding` is a normalised supplier bundle. It is not a
claim that a supplier price can be decomposed into independent cutting and edge
banding prices.

`pricing_basis = supplier_defined` is required when an invoice gives a price
and quantity but does not prove a physical billing unit. It must never be
displayed or calculated as `piece`, `m`, `m2`, `sheet`, or `hour`. The
`supplier_service_unit_count` driver records the observed count only.

## Protected behaviour

- Existing material source rows and offers remain untouched.
- Current Estimation object-facts and Labor Engine contracts do not receive the
  new supplier bundle in this stage.
- No operation price is automatically attached to a material price.
- No historic service row is promoted into the new table without a reviewed
  classifier in a later stage.

## Stage-1 acceptance criteria

1. Migration is additive and transaction-wrapped.
2. Service offers reference a shared `reference_operation`, supplier, source,
   and source row, and cannot be stored in material-offer tables.
3. Exact supplier spelling can be retained separately from canonical supplier
   identity.
4. The bundled `supplier_cut_and_edge_banding` operation can preserve a
   supplier-defined billing unit without false conversion.
5. RLS protects the two new company-private tables.

## Next stage

Stage 2 changes the Price Source application layer: classify rows, persist
service offers, exclude consumables completely, resolve VAT and currency under
the accepted policies, and keep ambiguous calculation units in review.

## Stage 3, interactive Price Lists workspace

Stage 3 replaces the legacy interaction around the established data contract.
The released extraction remains synchronous and stable: one extraction runs at
a time and no new source can enter a hidden queue. Existing catalog and Review
rows remain available between cycles. The upload control shows an immediate
indeterminate activity bar and elapsed time, but it must not invent a completed
agent stage or percentage.

True concurrent editing during extraction and confirmed server-side phases
require a durable job model. They are not implied by this synchronous release.

### Checkpoint, 2026-10-05

The source-first data contract, Review downgrade for unresolved canonical
units, Material Jobs separation, and compact Price Lists structure are working
in production. This is an implementation checkpoint, not task completion.

The next 3.16.7 increment runs the one active extraction in a background
worker. It is intentionally company-locked and remains active while the user
switches between Profile tabs. It is not a durable server job: an app-process
restart still cancels it. The UI reports only the truthful active state
(`Extracting prices` plus elapsed time), rather than invented processing
phases. Production acceptance with a real uploaded PDF remains required.

For invoice rows, a line quantity is not a package-conversion blocker. A
proven `sheet -> sheet` factor of one is active even when the invoice lists
two or more sheets. Repeated material rows reuse an existing catalog offer
only when supplier lane, price, unit, VAT, material family, and available
structural dimensions agree. Supplier jobs reuse the existing offer by
canonical operation, supplier lane and price basis, never by raw OCR wording.

Remaining work includes durable server jobs with confirmed processing phases,
the Material Jobs resolver, and production acceptance of asynchronous editing.

The workspace requirements are:

- Catalog and Review use the same compact information hierarchy: English name
  above source/original name, Category, shortened Supplier with full hover
  text, Price, and Updated where applicable.
- `Other` category is visibly `?` in Review, not a fake resolved category.
- Review fields that caused the blocker start unselected. They are visibly
  required rather than defaulted to `piece` or another unsupported value.
- Saved is a viewport confirmation for five seconds. Extraction result is a
  green confirmation directly below the upload card, sticky while scrolling,
  for ten seconds and can be closed earlier.
- Supplier-provided material processing is shown as `Material Jobs`, separate
  from material prices and separate from in-house labour.
- Material prices, Review rows, and Material Jobs show a proved ex-VAT and
  VAT-inclusive value. If the source cannot prove the tax rate, the unavailable
  side stays blank rather than being guessed.
- A source row with an unknown canonical unit is downgraded to Review with
  `Estimation unit required`; it never aborts the complete document. A known
  canonical Material Job is the exception: its reference operation determines
  department and a `supplier_defined` billing basis, so a missing reusable
  unit does not send it to Review.
- Source Library columns are Supplier/source name, document type, department,
  row count, compact View, and compact Remove. It does not expose the removed
  source-wide VAT settings.
- A new source cannot start while an extraction is active. There is no hidden
  queue, and a concurrent request is rejected rather than delayed.

### Increment, 2026-10-05, canonical supplier and delayed tab handoff

- The first saved supplier remains the canonical company spelling. When OCR
  variants have equal safe edit distance, a production lookup with timestamps
  selects the oldest supplier rather than creating a second lane. Untimestamped
  import/test ties stay unresolved.
- A Profile-tab click made immediately after Extract is delayed only until the
  background worker is observed, or for a three-second maximum. The same click
  is then replayed automatically. It is not discarded and does not cancel the
  extraction.
- `Material Jobs` is always the fourth top-level catalog department, including
  when empty, and uses the same expander/card component geometry as materials.
- `Glass` requires an explicit glass marker in the original source text. The
  agent's own normalised label is not proof. An unproved category becomes
  `Other` and stays editable, rather than creating a false Glass material.
- The price-source stream has a 60-second wall-clock cap in addition to its
  network timeout. A slow or stalled stream produces an actionable failure
  instead of leaving an indefinite Extracting state.

### Increment, 2026-10-05, canonical supplier evidence and material identity

- `company_suppliers.supplier_hp` is additive evidence from an invoice's HP or
  HeadPay number. Exact company-private HP wins supplier matching before OCR
  text, while the first accepted supplier remains the canonical display name.
- New sheet-material rows persist a deterministic structural identity: material
  family, proven thickness and dimensions, and proven construction. It ignores
  `sheet`, colour, décor, OCR word order and SKU. `perforated` remains a real
  distinction. This preserves one first canonical material while preventing a
  normal sheet and a perforated sheet from collapsing together.
- Supplier SKU is source provenance only. It may corroborate an already equal
  structural material offer but cannot select a material by itself.
- Starting a new extraction removes the prior green result immediately in the
  browser, before the server callback rerenders the upload controls.
- Tab navigation acknowledges the server processing marker, not an arbitrary
  timer. A click immediately after Extract is replayed only after the worker
  has accepted the job, so navigation cannot silently discard a source.
- The existing durable `app_runtime_events` sink records the extraction job
  submission, worker and lock state, source input, duplicate check, agent
  start and first stream event/token, storage, database, and terminal worker
  outcome. These marks are keyed by the runtime trace and job id.

### Increment, 2026-10-05, supplier canonicalisation and descriptors

- Among all safely matching timestamped supplier spellings, the earliest stored
  company supplier is canonical, even if a later OCR spelling is a closer edit
  match for a particular invoice.
- Explicit source descriptors are canonicalised before catalog resolution:
  perforated construction, and glossy, matte, rough/textured, sanded,
  polished, and mirror finishes. The resolver never infers material category
  from an unexplained proper name or possible brand.
- Test-company 610 Price Lists data and uploaded source objects were cleared
  on 2026-10-05 with user authorisation. The next real invoice run is a clean
  acceptance baseline.
