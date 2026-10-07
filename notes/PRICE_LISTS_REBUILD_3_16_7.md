# Price Lists rebuild, 3.16.7

Status: active. Stage 1 is the additive data contract. It does not change the
current Price Lists UI or automatically modify any existing source.

## Working contract, 2026-10-06

- A completed and accepted work item is frozen. A later task must not alter
  its code path, UI, timing, or data behaviour unless the user reports a
  regression in that item or the active task has a demonstrated dependency on
  it.
- Before touching a frozen area, record the dependency, the protected
  behaviour, and an end-to-end verification that proves it still works. A
  speculative resilience or cleanup change is not sufficient reason.
- Every implementation update names its scoped work item and the files it may
  affect. Findings outside that scope become backlog entries, not opportunistic
  patches.

## Closure contract, 2026-10-07

This is the completion boundary for the source-ingestion tool. The tool is
complete only after every P0 item below is accepted in the authenticated
production UI. A passing unit suite or one screenshot is not acceptance.

### 1. Supplier lane

- Each document identifies the seller from issuer evidence, not the buyer.
  Header and footer evidence, including OCR evidence, remain eligible for every
  supported document format.
- The active company's legal names and registration identifier are a blacklist:
  they can never create a supplier from a seller invoice.
- `ח.פ.`, `ע.פ.`, and `ע.מ.` with exactly nine digits are one supplier-identity
  field. An exact seller identifier reuses the existing supplier lane. The
  earliest accepted supplier name remains the canonical display name; source
  spelling and aliases remain evidence rather than competing suppliers.
- Material normalisation, offer matching, VAT work and UI changes may not alter
  issuer OCR, buyer exclusion, supplier matching, aliases or canonical supplier
  persistence. Those paths are frozen by the accepted 2026-10-07 supplier
  checkpoint.

### 2. Materials and supplier offers

- A material is normalised from literal source evidence into its department,
  family and structural attributes. Important distinguishing attributes include
  thickness, dimensions and construction. Perforation is retained as evidence,
  but may be collapsed under the same-price rule. Colour, décor, OCR word
  order and a generic word such as `sheet` do not create a separate material.
- Within one canonical supplier lane, identity is decided from material-bearing
  evidence, not invoice prose. The strong evidence hierarchy is: matching SKU
  when present, otherwise matching price; then category/family, a proven primary
  discriminator such as model, thickness or literal primary size, and explicit
  construction. A matching SKU may represent the same item
  at a changed price, in which case the supplier offer is updated or versioned.
  Quantity, décor, colour, word order and unproven extracted geometry never
  create a second material. A literal contradiction in a primary discriminator
  remains a boundary.
- A supplier SKU is valid only inside its canonical supplier lane. It never
  resolves an item across suppliers. It is paired with the material-bearing
  evidence above. It cannot by itself collapse a different construction. A
  plain and perforated sheet may collapse only when supplier, family, format,
  thickness and price are identical.
- The bilingual taxonomy may prove a category, but unfamiliar wording is kept
  as source evidence. It must not itself create an `Unknown material` when the
  literal evidence already proves a recognised family.

### 3. Same material from different suppliers, an explicit open decision

The recommended policy is adopted for source ingestion: one canonical company
material may retain several supplier-specific offers. Different suppliers and
different prices are therefore not duplicates. Each offer retains supplier,
source, unit, currency, VAT basis, observed date and provenance. The source
tool never selects a best offer. The later Estimation resolver will select from
those eligible offers under an explicit project policy.

### 4. VAT and prices, current next P0 scope

- Keep raw price, quantity, unit price, line total and VAT evidence separately.
  Arithmetic may repair only a proven transposition, otherwise the row is
  reviewed after its independent re-read.
- The catalog presents ex-VAT and VAT-inclusive prices only when each value is
  proven by source evidence or an accepted supplier/document VAT rule. A missing
  totals page is not a line-price error.
- Discounts are private source accounting evidence. When an explicit meaningful
  discount proves the effective line price, persist the effective price. Do not
  expose discounts in the catalog. Tiny rounding adjustments do not create a
  discount or an error.
- The precise fallback for a line-only invoice is an active P0 decision and
  implementation task. Until it is accepted, an unproved VAT basis remains a
  Review reason instead of being silently invented.

### 5. Source lifecycle and final-cycle UI

- PDF, XLSX, CSV, JPEG and PNG are supported. One PDF/spreadsheet is one source;
  several selected photos may be one logical document. OCR and progress must
  reach an observable terminal state, not an unbounded browser spinner.
- The final extraction dashboard represents exactly the latest completed cycle.
  It persists across Profile-tab navigation and ordinary rerenders, then clears
  immediately when the user selects or drops a replacement file or enters a
  replacement URL, before preview generation.
- `Delete source` is permanent: it deletes source-owned rows, offers, aliases,
  resolver artifacts and orphan materials, while preserving materials still
  referenced by another source. The selected source row disappears immediately;
  the irreversible storage/database work follows in the background. Failure
  restores that one row with an actionable error.
- Optimistic deletion hides every UI projection owned by the confirmed source:
  its Source Library row, catalog offers, Material Jobs and Review rows. It may
  never hide a generic Streamlit container, duplicate the page, or alter other
  sources. Its immediate disappearance is the only success acknowledgement. A
  visible error is shown only if the irreversible deletion fails.
- A background purge must never force a full app rerun. It may clear its read
  cache after completion, but an Extract callback owns its selected file and
  cannot be interrupted or re-keyed by unrelated deletion work.

### 6. Minimal Needs Review

- Review contains only a real activation blocker: unproved price arithmetic,
  VAT basis, unit/conversion, required material distinction or a true category
  ambiguity. Known taxonomy and supplier defaults must resolve before Review.
- Each row exposes one concise reason and one bounded correction action. Review
  is not a second catalog, and non-blocking confidence language is not shown.

### 7. Production acceptance matrix

P0 acceptance requires representative authenticated production runs for: a
text-layer PDF, a graphical/scanned PDF, a photographed JPEG/PNG invoice, a
spreadsheet, repeat documents from one supplier, matching material with a
changed supplier price, two suppliers offering the same material, source
deletion of two sources in succession, and a final-cycle dashboard surviving a
Profile-tab visit. Every run records source, OCR, agent, persistence and
terminal timing so a failed run can be diagnosed at the earliest missing stage.

### After closure: Estimation resolver, separate task

The next task consumes active supplier offers for one estimation cycle. It may
choose eligible offers using an approved project policy, but must not change
source evidence, supplier identity, catalog material identity or historical
offer records. It is deliberately not a gate for completing source ingestion.

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

### Checkpoint, 2026-10-06, photographed hardware invoice

The first successful image-OCR production pass for Pirzul invoice 63385
identified the seller from its issuer block and HP `337791438`, not the Hebrew
`לכבוד` buyer block. OCR recovered all five priced lines. The initial
consumables filter then incorrectly discarded an adjustable plinth leg with
included screws because it matched the word for screws. Hardware is now a
separate company catalog category under the Wood department. A fitting with
integral screws remains Hardware, rather than being discarded as a consumable.

For Hardware rows only, omitted units default deterministically to `piece`.
Positively identified drawer runners/slides default to one left/right `set`.
This is a user-approved commercial default, not an inferred package conversion.

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

### Diagnostic guard, 2026-10-06, zero-row source extraction

- A source that reaches OCR and the commercial agent but returns no rows is no
  longer stored as a successful empty Price Source. Its usage record retains
  the OCR strategy, evidence length, page count, row-status counts, document
  type, and origin; the user receives a terminal extraction error instead.
- This separates a true extraction failure from a valid invoice with excluded
  rows and gives the next diagnosis evidence before any catalog state changes.

### Increment, 2026-10-06, self-identity boundary and low-threshold private merge

- The Bank Details label is `Company registration number (H.P.)`.  The company
  name, Hebrew and English legal names, and its nine-digit H.P. form an exact
  local blacklist for supplier identification.  A buyer identity found in an
  invoice cannot create or update a company supplier.  This check is local and
  does not disclose Bank Details to the commercial extraction provider.
- Exact supplier H.P. continues to select the already stored supplier before
  text matching.  Without H.P., supplier-name OCR matching now tolerates a
  larger, length-scaled edit distance, while names of five characters or fewer
  remain limited to one changed character.  The oldest accepted supplier stays
  canonical.
- Material merging remains strictly inside the same supplier lane.  An existing
  material can now be reused when category, effective price, proven thickness,
  compatible material family and all non-conflicting proven dimensions agree.
  SKU, colour and decor corroborate provenance but do not split the catalog.
  An explicit construction mismatch, including `perforated` versus ordinary,
  a price mismatch, or a thickness mismatch prevents a merge.  Cross-supplier
  material merging remains deliberately out of scope.
- Focused Price Sources and Company Profile checks: 330 passed.  Production
  acceptance remains required with two real invoices from the same supplier.

### Increment, 2026-10-06, issuer evidence and clean Price Lists baseline

- The terminal green extraction dashboard is session-scoped. It remains visible
  while the owner moves between Profile tabs and through later reruns. It is
  cleared only when a different file selection or supplier URL is chosen, and
  is then replaced by the next terminal result.
- OCR evidence before the Hebrew buyer boundary `לכבוד` is used as a local
  issuer correction. `ח.פ.`, `ע.מ.`, `ע.פ.` and `H.P.` are equivalent labels
  for one nine-digit supplier identity. When an agent selected the company as
  buyer, a printed issuer header corrects it before the self-identity blacklist
  can create an `Unknown supplier` source.
- Consumable filtering no longer lets a screw/dowel pack through merely because
  the model called it Hardware. A durable fitting marker still protects legs,
  hinges, runners and brackets with integral screws. Bulk packs of at least 50
  units priced at at most ILS 2 per packed unit are supporting consumables
  evidence, never a reason to hide a recognisable durable fitting.
- Company 610 Price Lists test data was permanently deleted with user
  authorisation: source objects, source rows, material items/offers, suppliers,
  aliases, Material Job offers, material-identity evidence, and Price Source
  OCR/extraction usage events. Final verification returned zero rows and zero
  source objects for every one of those scopes. The company profile and other
  product domains were not touched.
- Verification: focused Price Sources and Company Profile checks, 334 passed.

### Hotfix, 2026-10-06, native Extract button event delivery

- Runtime traces proved a reported 165-second `Starting extraction` state had
  no `server.price_source_job_submitted` event, worker event, or lock. It was
  therefore neither OCR nor an agent/provider timeout: the click had not
  reached the Streamlit callback.
- The capture-phase UI guard no longer changes the Extract button's native
  `disabled` property at any time. It keeps the first click untouched for
  Streamlit's delegated handler and suppresses only later clicks through the
  guard's own pending/processing state. This replaces the earlier one-tick
  workaround, which was still unsafe in some render states.
- Verification: focused Price Sources and Company Profile checks, 334 passed.

### Increment, 2026-10-06, structured OCR issuer evidence

- Price Source OCR now preserves typed `header` and `footer` blocks as a
  separate local supplier-evidence layer. Header blocks are seller-priority
  evidence because an invoice body often contains the buyer after `לכבוד`.
  Footer blocks corroborate the issuer but never override a conflicting header
  identifier.
- The commercial extraction agent keeps its established body-text input. The
  structured issuer layer is used locally for deterministic supplier repair,
  so this change neither expands external disclosure nor alters material-row
  extraction semantics.

### Checkpoint, 2026-10-06, Pirzul invoice supplier and consumables

- Real image invoice `62336` completed with canonical supplier `א.ש. פירוזל`
  and seller identifier `513453233`, repaired from the OCR header rather than
  the buyer beneath `לכבוד`.
- The 1,000-piece screw pack was excluded as a consumable. Zero-price lines
  were discarded as non-candidates and the negative return line was retained
  only as excluded provenance, with no catalog offer.
- The seven remaining purchasable Hardware rows are a verified acceptance
  checkpoint for issuer identification and consumable removal.
- Pending, not implemented: Hardware matching must never use invoice quantity
  as identity evidence. Exact SKU is a strong positive merge signal; matching
  price is corroboration, not sufficient by itself. The normalised names must
  have meaningful overlap under the other evidence. With no overlapping
  meaning-bearing token, merge is forbidden even if the price agrees. Distinct
  hardware SKU/function/series/capacity remain separate. This is a new
  Hardware-normalisation task, not a change to accepted sheet-material merge
  rules.

### Increment, 2026-10-06, Hardware merge evidence

- Invoice quantity is excluded from all Hardware identity paths. It cannot
  cause, prevent, or strengthen a merge.
- A Hardware SKU is stored as supplier provenance and acts as a strong match
  signal only when both values agree and product names still have meaningful
  overlap. Conflicting SKU values are a hard boundary.
- Without SKU, Hardware rows need both equal price and meaningful product-name
  overlap. A changed supplier price for the same SKU updates that item's offer
  rather than creates a new item.
- Hardware catalog keys include supplier SKU when present. Thus rows such as
  `T766H750` and `B766H750` cannot collapse merely because their generic
  family and invoice quantity look similar.

### Hotfix, 2026-10-06, Hardware database identity

- The company-material database unique constraint is keyed by company,
  category and persisted normalized name. Hardware persistence now encodes the
  complete Hardware identity, including the SKU or proven name discriminator,
  rather than only its generic structural tuple. Distinct SKUs therefore no
  longer fail with a duplicate-key error or collapse into one material.

### Increment, 2026-10-06, line-price arithmetic

- Price extraction now treats quantity, unit price and line total as a required
  three-value relationship, independent of source language or table direction.
  The prompt requires header-led column interpretation and arithmetic proof for
  every priced row.
- The deterministic fallback applies only to the proven transposition signature:
  the extracted unit price equals the extracted quantity while `line total /
  quantity` gives a different positive value. In that case the derived value is
  preserved as the effective unit price with `unit_price_derived_from_line_total`.
  Every other line-total conflict stays in Review. This prevents an unproven OCR
  number from becoming a catalog price.
- The arithmetic repair runs before active-row eligibility checks, so a repaired
  row is still subject to the existing VAT and canonical-unit safeguards.
- Verification: focused Price Sources checks, 139 passed.

### Increment, 2026-10-06, arithmetic recheck before Review

- An invoice row whose initial `quantity × unit price` does not reconcile with
  its line total now receives one independent arithmetic re-read against the
  structured OCR source before it can remain in Review.
- The re-read may alter only quantity, unit price and line total. Its result is
  accepted only when those three values independently reconcile. It cannot
  change supplier, material identity, unit, VAT or any other established
  extraction decision.
- If the re-read fails, times out, or still cannot prove the arithmetic, the
  existing conservative path applies: a proven `price == quantity` transposition
  can use `line total / quantity`; every other conflict remains in Review.
- Recheck latency and provider usage are recorded as a separate
  `price_source_arithmetic_recheck` event so it can be diagnosed separately
  from OCR and the primary extraction call.

### Pending Price Sources follow-ups, recorded 2026-10-06

- VAT for incomplete supplier-invoice captures: a line-only photo must be
  catalogued with a clearly defined invoice VAT fallback even when its matching
  totals page was not uploaded. This must not use a missing document total as a
  line-price error.
- Source Library label: show the extracted invoice number beneath the canonical
  supplier name when it is present, otherwise retain the uploaded file name.

### Increment, 2026-10-06, terminal extraction dashboard lifecycle

- Selecting a replacement file now clears the green terminal dashboard at the
  selection event, not at the later Extract click. The same selection clears
  any stale cycle error.
- A successfully rendered terminal dashboard is retained in this browser tab's
  session display cache. If a Streamlit rerender loses the in-memory notice
  after the worker has completed, the same completed dashboard is restored.
  The cache is display-only and is cleared with the next file selection.
- The server records `server.price_source_ui_terminal_result` after it stores a
  successful worker outcome in session state. This distinguishes a completed
  backend cycle from a client-side display loss in later diagnostics.
- Verified with focused Price Sources and Company Profile tests, 347 passed.

### Checkpoint, 2026-10-06, terminal dashboard cardinality

- Production evidence shows two green terminal extraction dashboards visible
  after two consecutive completed cycles. The accepted contract is exactly one
  dashboard: it describes only the latest terminal cycle, survives Profile-tab
  navigation and ordinary rerenders, and is removed immediately when a new
  file or URL selection begins.
- [verified] The session-storage restoration guard could append a stale cached
  dashboard during a rerender, then preserve it beside the server-rendered
  current result.
- Every server-rendered terminal result now carries its processing-cycle id.
  The browser keeps only the highest cycle result, replacing stale restored
  markup rather than appending it. File and supplier-URL selection both clear
  the browser cache before the next Extract click.
- A server-owned selection-cycle marker is now advanced before the next file
  or URL source is processed. A cached dashboard from an earlier selection is
  rejected even if the browser did not observe the file-input event.
- Verification: focused Company Access and Price Sources checks, 349 passed.
  Production acceptance remains one manual check with two consecutive cycles.
- This is a display-only repair. It does not change source processing,
  supplier resolution, or catalog persistence.

### Increment, 2026-10-06, PDF issuer-header OCR

- Every PDF now follows a hybrid evidence path, including PDFs that contain a
  usable native text layer. Native text remains the authoritative evidence for
  price rows; the first PDF page is always OCRed so its graphical header and
  footer can supply the seller's legal name and nine-digit identifier.
- This removes the old 120-character native-text bypass, which could read an
  invoice table but omit a graphical seller masthead. OCR issuer evidence is
  resolved before the existing buyer-boundary guard, so data after `לכבוד`
  remains ineligible to become a supplier.

### Hotfix, 2026-10-07, rendered PDF issuer band

- Direct PDF OCR may represent a graphical masthead as an untranscribed image,
  even when `extract_header` is requested. The seller then remains unknown
  despite a successful OCR call.
- PDFs with native row text now always render the generic upper-centre issuer
  band of their first page at high resolution and OCR that PNG with the
  evidence profile. This is one document-wide rule for every PDF, not a
  supplier exception. The native PDF text remains the source for price rows.
- OCR may reverse Hebrew two-letter business labels in visual order, for
  example `ח.פ` as `פ.ח`. Issuer parsing accepts both visual orders for all
  three Israeli seller identifiers (`ח.פ`, `ע.פ`, `ע.מ`) before validating the
  required nine digits.

### Checkpoint, 2026-10-07, supplier resolution is frozen

- Production acceptance: the two consecutive PDF sources `HashDoc_2_159930`
  and `HashDoc_2_160146` both resolved to the same canonical company supplier
  `לבידי בוקטוס`, H.P. `514539998`, and the same `supplier_id`. This proves
  first recognition and subsequent canonical merge for the current four-invoice
  supplier set.
- Frozen supplier surface: PDF issuer-header OCR, issuer identity parsing,
  buyer/company blacklist, canonical supplier matching, aliases and supplier
  persistence. Material classification and material-offer matching must not
  alter these paths. Any demonstrated cross-dependency requires a new explicit
  decision before touching this checkpoint.
- Next scope only: explain and correct `Unclassified sheet material` and
  repeated sheet-material merging using the protected canonical supplier lane.

### In progress, 2026-10-07, wood-sheet classification and repeat merge

- Diagnostic evidence: the current extractor returned `Other / other` for
  Twin and Okume rows, even while retaining thickness, price, SKU and the
  source trade wording. Existing matching therefore reuses rows in its
  `Other` lane but exposes `Unclassified sheet material` in the catalog.
- Scope is restricted to material normalisation and matching. The frozen
  supplier checkpoint above is not a dependency of this work and must remain
  untouched.

### Increment, 2026-10-07, bilingual material taxonomy

- Added a deterministic bilingual taxonomy layer after commercial extraction
  and before catalog matching. It has no supplier inputs and cannot call or
  alter issuer OCR, supplier identity parsing, buyer blacklist, aliasing or
  canonical supplier persistence.
- The first vocabulary covers all existing catalog areas rather than a Wood
  exception: Wood Sheets, Solid Wood, Wood Supplies, Hardware, Glass, Metal
  Sheets, Metal Profiles, Metal Supplies, Paints & Coatings, Coating Supplies,
  plus the existing Material Jobs reference-operation vocabulary.
- English and Hebrew aliases map to one canonical category/family. Unknown
  wording is retained as source evidence, but cannot undo a category proven by
  a different literal marker. Twin/Combi is a plywood construction attribute;
  Okoume is a plywood species attribute, not a supplier brand or standalone
  material family. Perforated remains a distinct construction boundary.
- VAT legal-status inference is explicitly deferred. `ע.מ.` is a VAT-registered
  dealer, `ע.פ.` is VAT-exempt, and `ח.פ.` identifies a company but does not by
  itself prove a row's VAT treatment. No VAT rule changed in this increment.
- Verification: `tests/test_price_sources.py` reports 161 passed. Added
  bilingual regression cases across all catalog areas and existing Material
  Jobs operation codes.

### Checkpoint, 2026-10-06, permanent Price Source deletion

- Production is on commits `a8e6280`, `e1f0086`, and `740bd62`. The SQL function
  `public.purge_company_price_source(text, uuid)` is applied to production.
- Source Library now uses one compact `View` and `Delete` action size. `Delete`
  opens a modal, rather than expanding a second inline table row. `Cancel` is
  client-side only. Confirming `Delete source` hides the source immediately;
  database and Storage cleanup proceed in a background worker. A failed purge
  restores the source and reports the failure.
- Purge removes source-owned material offers, supplier-operation offers,
  service offers, source rows, source-observed supplier aliases, material
  aliases, resolver events and orphan source-created materials. A material
  still used by another offer survives and is detached from the deleted source.
- The source-row and identity-candidate tables have reciprocal foreign keys.
  The production function now first clears `identity_candidate_id` on those
  rows, then removes candidates, then rows. This is required for real deletion,
  not merely UI hiding.
- Production rollback verification against source
  `6b7fa94f-69ed-4f9f-bd6b-51198ea44b28` completed successfully and reported
  five source rows, four material offers and four orphan materials eligible for
  deletion. The transaction was rolled back, so that verification changed no
  user data.
- Post-check: literal `company_id = 1` contains zero Price Source records,
  offers, materials, aliases, candidates and resolver events. The current
  test company `610` deliberately retains three sources, 18 source rows, nine
  material offers and seven materials.
- Verification: 148 focused Price Source and purge-migration tests passed after
  the dependency-order fix. This is a functional checkpoint, not completion of
  the full Price Lists rebuild.

### Checkpoint, 2026-10-07, canonical supplier-sheet merge

- Production sources `HashDoc_2_159930.pdf` (`30829`, source
  `d288b292-558b-4ee1-a81c-1b06cb90aab1`) and `HashDoc_2_160146.pdf`
  (`30912`, source `f96368da-2d18-4a40-859a-98e6b6ff2491`) resolved to the
  frozen canonical supplier `לבידי בוקטוס`, H.P. `514539998`.
- Ordinary Twin plywood, 17 mm, SKU `27`, ILS 110, is one canonical material
  (`e2d45e1e-9d25-4d90-a9bd-b2f72e90c28b`) across three invoice rows. This
  remains true although the extractor produced inconsistent secondary geometry
  (`3100×3100` and `3100×2000`) for source wording that literally contains the
  same primary `3100` span.
- The material distinctions from the two documents are correct: ordinary Twin
  17 mm, perforated Twin 17 mm, ordinary Okoume 5 mm, perforated Okoume 5 mm,
  and MDF 19 mm. The perforated variants remain distinct despite equal prices.
- The same-supplier merge contract is covered by deterministic tests for equal
  SKU with changed price, conflicting secondary extracted dimensions, and the
  `perforated` boundary. Focused verification: 177 Price Source tests passed.
- The owner intentionally restarted from clean sources rather than running a
  special repair for historical duplicate material cards. This checkpoint is
  therefore evidence for the forward ingestion path, not a retroactive-data
  migration.

## Authoritative Price Source backlog, 2026-10-07

### Actionable P0

1. **Material Job classification and canonical persistence**
   - Status: in progress, implementation `2c387a3`, production acceptance pending
   - Outcome: a known supplier operation, including `פס חיתוך + קנט` / cut and
     edge banding, always follows the Material Job path
     (`reference_operation -> company supplier operation offer`) and never
     creates a `Wood Supplies` material or material offer.
   - Evidence: source `30829` persisted SKU `41`, ILS 17.5 as the material
     `Edge Banding Cutting Strip`; source `30912` correctly classified the same
     evidence as an operation service. This is a classifier/persistence
     inconsistency, not a supplier or sheet-material merge defect.
   - Acceptance: repeat documents reuse one canonical operation and supplier
     operation offer, source rows retain the original wording and price, no
     material card is created, and supplier-resolution and sheet-merge paths
     remain unchanged.
   - Implemented scope: exact Hebrew singular/plural and punctuation variants
     for the combined cutting-and-edge-banding phrase now override an incorrect
     material classification before material taxonomy runs. Hebrew final forms,
     the joined conjunction `ו־`, and a one-character OCR error are normalised
     only for multi-signal phrases. A bare edge-band product remains material.

2. **VAT fallback for incomplete invoice captures**
   - Status: pending, requires the already-recorded P0 policy decision before
     implementation
   - Outcome: determine the active VAT basis for a line-only invoice without
     mistaking a missing totals page for a line-price error.

3. **Production acceptance matrix for source ingestion closure**
   - Status: pending, depends on the two items above
   - Outcome: execute and record the authenticated production matrix in the
     closure contract: text PDF, graphical/scanned PDF, photo, spreadsheet,
     repeat supplier, supplier-price change, cross-supplier offer, consecutive
     deletion, and dashboard persistence across Profile navigation.

4. **Optimistic lifecycle interaction boundary**
   - Status: in progress, local implementation pending production acceptance
   - Outcome: Delete immediately removes all records belonging to that source
     from every Price Lists projection, while database/storage cleanup remains
     asynchronous. A completed background delete cannot reset an in-progress
     file selection or prevent the next Extract cycle from reaching the server.
   - Evidence: the prior background-purge fragment used `st.rerun(scope="app")`.
     The 2026-10-07 failed second cycle created no source and no agent/OCR event,
     consistent with its uploader state being re-keyed before callback capture.
   - Acceptance: delete two sources in succession, immediately select a new
     file while a purge is still running, start extraction, and verify exactly
     one new server trace/source plus no visible records from either deleted
     source.

5. **Cycle outcome terminology**
   - Status: in progress, local implementation pending production acceptance
   - Outcome: a row collapsed into an offer staged earlier in the same source is
     reported as `merged`; `already in catalog` is reserved for an equivalent
     offer that pre-dated the current source. Exact repeat-source detection
     remains `Already processed`.

### Pending P1

1. **Source Library invoice label**
   - Status: pending
   - Outcome: show the extracted invoice number below the canonical supplier
     name when present, otherwise show the uploaded file name.

### Deferred until Source ingestion is accepted

1. **Estimation resolver**
   - Status: deferred
   - Outcome: select eligible supplier offers for one estimation under an
     approved project policy. It must not modify source evidence, supplier
     identity, catalog material identity or offer history.
