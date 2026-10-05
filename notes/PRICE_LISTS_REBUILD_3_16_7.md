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

### Increment, 2026-10-05, invoice issuer boundary

- Supplier HP is optional, exactly nine digits, and accepted only from the
  seller's issuer block. Hebrew `לכבוד` is a buyer block, so its company
  number must never create or merge a supplier.
- A brand-only sheet row remains Review by default. It can inherit a known
  family only from one existing offer in the same supplier lane whose SKU,
  price, unit, VAT, and structural attributes all agree.
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

### Checkpoint, 2026-10-05, repeated invoice identity and Material Jobs removal

- A printed numeric invoice item code is supplier provenance, never the
  internal extracted row position. The schema repairs the known `27`, `41`,
  `4` misplacement into `raw_sku` before persistence, while retaining the
  sequential internal row position.
- Repeated material from the same canonical supplier can reuse the first
  catalog material when original source wording, price, unit, VAT and proven
  dimensions agree, even when the model changes the English family label. SKU
  strengthens the match but is not required. Perforation remains distinct.
- The archive RPC now archives supplier-operation offers too. The resolver
  also ignores legacy active job offers whose source is already archived. This
  prevents a removed source from making a later Material Job appear "already
  in catalog" while the Material Jobs department shows zero jobs.
- Verification: focused Price Sources and archive migration tests, 118 passed;
  Python compilation and diff check passed. Production migration
  `2026_10_05_archive_supplier_operation_offers.sql` applied successfully.

### Checkpoint, 2026-10-05, supplier canonicalisation accepted in production

- User acceptance: two real invoices from the same supplier now resolve to the
  same canonical supplier. This is the strongest accepted Price Lists result
  so far and is the rollback baseline for the following service-offer repair.
- Production diagnosis of duplicate `Supplier cut and edge banding` entries:
  both offers have one canonical operation, one canonical supplier, ₪17.50,
  ILS, excluded VAT and `supplier_defined` pricing. The only differing field
  is source unit: one invoice stored `piece`, the other stored no unit. The
  current operation-offer comparator treats missing source unit as a distinct
  service. This is an incorrect constraint for a supplier-defined job, where
  a visible `piece` is not a reusable rate basis.

### Increment, 2026-10-05, Material Jobs current-offer identity

- For `supplier_defined` Material Jobs, an omitted source unit and `piece`
  match the same offer. The current catalog identity is canonical operation,
  canonical supplier, effective price, currency, VAT and pricing basis. A
  unit remains identity-bearing only for measured bases such as linear metre
  and square metre. Legacy duplicate evidence is retained by source, but the
  Material Jobs catalog displays only the newest equivalent offer.
- Verification: focused Price Sources and archive migration tests, 121 passed;
  Python compilation and diff check passed.

### P1 pending, 2026-10-05, photo extraction session recovery

- A submitted JPEG photo showed client-side progress for roughly 200 seconds
  and then a blank screen. Production has neither a new source record nor a
  `server.price_source_job_submitted` runtime mark for that attempt. Therefore
  the extractor/OCR did not stall: browser/session state was lost before a
  server worker was acknowledged. The current Future exists only in Streamlit
  session state, so it cannot recover an interrupted browser session. Repair
  requires a durable submitted-job record before the worker starts, plus a
  client recovery path. Do not claim photo OCR quality until a real submitted
  photo has a terminal trace.

### Increment, 2026-10-05, explicit OCR text layer for Price Sources

- JPEG, PNG, TIFF, HEIC and HEIF Price Sources now run through the existing
  Mistral OCR adapter before commercial extraction. The commercial agent gets
  only the resulting bounded text layer, never an untracked image attachment.
- A PDF with at least 120 characters of embedded text uses that native text.
  A scanned or textless PDF falls back to one direct Mistral OCR request.
  XLSX and CSV remain direct structured-table imports. Supplier URLs retain
  their fetched visible HTML text.
- OCR preserves a provider response, usage data, timing, page count and the
  selected text-layer strategy in the company-scoped usage ledger. The source
  summary contains only the strategy and compact metrics.
- TIFF and HEIC/HEIF previews and multi-photo documents are normalized through
  Pillow before being rendered or sent to Mistral. The optional `pillow-heif`
  dependency enables HEIC/HEIF decoding.
- The earlier P1 durable-job recovery remains open. This increment improves a
  submitted image's extraction route, it does not make an unacknowledged
  Streamlit session recoverable.

### Hotfix, 2026-10-05, OCR table evidence and invoice returns

- Mistral stores invoice-table HTML in `pages[].tables[].content` while page
  Markdown has only a `tbl-N.html` reference. The Price Source text flattener
  now includes the table content, so a photographed invoice reaches the
  commercial agent with its line rows rather than an empty reference.
- A negative quantity or negative line total denotes a return or credit row.
  It is retained as source evidence, normalized to a positive observed
  quantity, marked `return_or_credit_line`, and excluded from cataloging. It
  cannot invalidate the remaining invoice rows.
- Diagnostic replay of the user-provided photographed invoice: 11 extracted
  rows, 7 ready, 1 Review, 3 excluded, including one return row. This is a
  non-persistent verification run and did not alter the company catalog.

### Hotfix, 2026-10-05, unacknowledged extraction start

- A five-minute `Extracting` display with no matching runtime event proved the
  browser could optimistically paint progress before the Streamlit callback
  created a worker. The UI now says `Starting extraction` until it observes
  the server processing marker. If no marker arrives in 20 seconds, it stops,
  re-enables Extract and shows an actionable server-acknowledgement failure.
- This removes the false infinite progress state. The durable-job recovery
  work remains P1 because a browser refresh after an acknowledged worker start
  still requires persistent job state to recover the result.

### Hotfix, 2026-10-05, worker authorization boundary and bounded OCR

- Production trace for a submitted job stopped immediately after
  `server.price_source_process_started`. The next operation was a duplicate
  owner lookup from the background worker. Authorization is now revalidated on
  the authenticated request thread before submission, then carried as an
  explicit verified flag into the worker. Direct processing paths retain their
  own owner validation.
- Mistral OCR now has a 45-second transport timeout. A provider stall fails
  the job and releases the company lock instead of occupying it for up to
  three minutes.
- The browser no longer paints a zero-second elapsed bar while submission is
  unconfirmed. It displays `Starting extraction`; the real elapsed progress
  begins only after the server processing marker arrives.

### Hotfix, 2026-10-05, progress observer recursion

- The first server-confirmed progress update recreated its own progress DOM on
  every `MutationObserver` callback. Those mutations recursively triggered the
  observer and froze Chrome. The progress bar is now created once per stable
  server processing marker; later observer callbacks do not modify its DOM.

### Hotfix, 2026-10-05, immediate extraction acknowledgement

- Production tracing showed that the request had reached the server, but the
  synchronous owner lookup in the Streamlit click callback took about 18
  seconds before a job could be submitted. That raced the browser's 20-second
  acknowledgement watchdog and produced a false `did not reach the server`
  message.
- Submission now only creates the background job and returns the processing
  marker. The worker still performs the owner check before it reads, writes,
  or calls an extraction provider. This restores a fast acknowledgement
  without weakening the server-side authorization boundary.

### Hotfix, 2026-10-06, preserve the Streamlit Extract click

- The browser guard listened in capture phase and disabled the native Extract
  button during that same event. In some browser/Streamlit render states this
  prevented Streamlit's own delegated handler from receiving the click, so no
  server event was emitted and the watchdog was correct only accidentally.
- The guard now waits one browser tick before changing button UI state. The
  original click reaches Streamlit first, while duplicate-click protection and
  the acknowledgement marker remain intact.

### Hotfix, 2026-10-06, remove false client-side extraction failure

- A DOM marker is not a reliable transport acknowledgement. Slow Streamlit
  rerenders let the browser's 20-second watchdog announce a server failure
  while the worker could already be running. The client must not make that
  claim.
- The client now starts an elapsed `Starting extraction` display immediately,
  upgrades it when the server marker arrives, and allows deferred Profile-tab
  navigation after three seconds. Only a server-rendered error can state that
  extraction failed.
