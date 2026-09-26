# Price Source Agent Accuracy

Task: 3.12.1
Status: active
Priority: P1
Protected checkpoint: `d99a594` (accepted 3.12.1 Price Lists interaction checkpoint)

## Objective

Make the agent reliably turn real supplier websites, files, and photos into
auditable catalog prices. Improve extraction, material-type classification,
unit normalization, confidence, and ready-versus-unresolved decisions while
preserving the accepted catalog structure. Source Details may add the approved
document metadata, per-row Material Type and VAT, timing, and TC fields.

## Product hypothesis and source value

[Hypothesis] In the Israeli supplier market, public website prices and reusable
downloadable price lists may be less common than customer-specific prices shown
after an order in invoices, tax invoices, delivery documents, order
confirmations, and quotes. Historical post-fact purchasing documents may
therefore become the primary and highest-value source stream.

Do not encode this market hypothesis as an extraction fact. Test it against the
company's real source mix. The agent must remain evidence-driven for every
document. The product should, however, preserve the distinction between a
public/list price and a customer-specific observed transaction price because
the latter is private company purchasing evidence, not a universal market
price.

## Identified contract gap

The previous schema assigned one top-level category to the entire source. This
was insufficient for mixed supplier documents, where separate rows may be Wood
Sheets, Wood Supplies, Metal Supplies, and Paints & Coatings. Prompt-only edits
could not solve this. The approved v2 contract moves Material Type to every
extracted row while retaining source-level document metadata.

Recommended target separation:

- source level: supplier, document type, document number, document date,
  currency defaults, VAT defaults, and price context;
- row level: material type, raw identity and SKU, quantity, package, unit price,
  line total, discount basis, VAT basis, normalized identity and unit,
  conversion evidence, status, confidence, and evidence reference;
- deterministic application layer: arithmetic, activation gates, duplicate
  handling, offer versioning, and selection of the applicable company price.

`price_context` should distinguish at least `public_list`, `supplier_quote`,
`customer_transaction`, and `unknown`. It must describe the evidence, not make
the price available to other companies.

## Run cost observability

Use `TC` as the compact internal product label for Token Cost. `TC` is the run's
calculated cost from provider-reported input and output token usage and the
configured per-model pricing table. Display only the compact value, such as
`TC 0.042`, without a currency sign, the word cents, or a raw token count.

For Price Source Agent, show the completed run's timing and TC in the source
result/details. Preserve the stored input tokens, output tokens, model, prompt
version, and total USD cost for audit. If pricing for the model is unavailable,
show TC as unavailable rather than zero.

Cross-agent follow-up is tracked as 3.12.2: add the same per-run TC convention
to Detection, OCR where billable usage is available, Naming, and Estimation,
and show both stage TC and total-cycle TC without double counting.

## Current evidence

- The source pipeline and private persistence exist and pass deterministic
  tests.
- Prior production URL imports completed but sometimes produced zero ready
  prices and many unresolved rows.
- Script-only or protected pages may expose no readable HTML and currently
  require a PDF, screenshot, or photo.
- Arithmetic normalization and package-to-unit activation guards are already
  deterministic and must remain protected.

These observations prove that the weak result is not one single UI problem.
They do not yet identify whether the earliest failing boundary is source
acquisition, evidence extraction, prompt classification, unit interpretation,
schema validation, or activation policy.

## Required workflow

Before changing the prompt or thresholds, agree a scenario matrix and select
representative sources for each applicable scenario. For every run retain the
effective prompt version, source format, extracted evidence, raw structured
response, validation changes, activation result, duration, tokens, and cost.

Classify every experiment as confirmed, rejected, inconclusive, or invalid.
Change one meaningful variable at a time and compare against checkpoint output.
Do not improve ready-row count by weakening evidence or unit requirements.

## Scenario matrix to agree

| Group | Scenarios |
| --- | --- |
| Source format | Static website, protected/dynamic website, PDF, spreadsheet, single photo, multi-photo document |
| Document type | Price list, catalog, quote, invoice, tax invoice, delivery note, order confirmation, credit note, other |
| Department | Automatic detection, selected Wood, selected Metal, selected Coating, source contradicts selected department |
| Material type | Each supported material type, mixed-type source, legacy broad type, unsupported material |
| Price evidence | Unit price, package price, quantity plus line total, discount, VAT included/excluded, multiple currencies |
| Unit evidence | Direct unit, sheet dimensions, package conversion, missing conversion factor, conflicting units |
| Row quality | Ready, unresolved, excluded, duplicate row, revised supplier price, ambiguous material identity |
| Failure | Empty extraction, truncated output, provider timeout, invalid schema, persistence failure |

## Acceptance boundary

Automated tests are necessary but insufficient. Acceptance requires an agreed
representative production set with row-level review of source evidence,
classification, normalized price and unit, status, and confidence. The accepted
3.10.1 layout remains the protected checkpoint, except for the
explicitly approved Source Details metadata and table additions in this task.

## v2 implementation candidate

- source metadata now includes document number, ISO document date, price
  context, subtotal, VAT amount, and total;
- every extracted row now owns its Material Type, discount evidence, and VAT
  basis;
- explicit subtotal, VAT, and total mismatches are downgraded
  deterministically;
- a selected-department mismatch becomes unresolved instead of aborting the
  complete document;
- byte-level duplicate protection is supplemented by a semantic fingerprint
  for the same numbered document uploaded as another file or photo;
- Source Details displays the document date as MM/DD/YY, document totals,
  per-row Material Type and VAT, agent time, and TC without a currency sign;
- the uploader accepts several ordered photos of one logical document and lets
  backend validation report unsupported formats instead of silently rejecting
  them in the browser;
- the named customer or delivery recipient may belong to another company and
  never affects source acceptance or row confidence.
- the upload form has no source-level Department or Category selector because
  classification belongs to each extracted row.

This candidate is not a product checkpoint until the representative production
scenario set is reviewed and accepted.

## 3.12.1 revision 2 candidate

The workbook `furniture_hardware_consumables.xlsx` established that extraction
and activation must be reported separately. The agent extracted all 10 product
rows, while the deterministic 85 percent threshold activated 8 and retained 2
as unresolved. The main catalog showed only the 8 active prices, which made the
result look incomplete even though both unresolved rows were persisted.

Revision 2 keeps the activation threshold and unresolved policy unchanged. It:

- reports extracted, active, unresolved, and excluded row counts immediately
  after the completed run;
- displays agent duration and compact `TC X.XXX` in the same completion notice;
- moves Price Lists interactions into an established Streamlit fragment;
- queues processing in the button callback, shows immediate client-side button
  progress, and removes both explicit Price Source reruns;
- restores pointer hit testing for the native per-file delete buttons.

The rejected first implementation used `st.rerun(scope="fragment")` after
processing. A deterministic AppTest proved that a recovery/full run can reach
that call outside a fragment rerun and raise a Streamlit API exception. The
final candidate performs processing and renders the fresh result in the same
native fragment cycle, with no manual rerun.

All 354 automated tests pass. Production acceptance must still confirm that
adding and deleting files does not dim the complete page, Extract shows one
stable progress state, and the completion notice matches the persisted source
summary.

## 3.12.1 revision 3 candidate

Production evidence from `lumber_pricelist_israel.xlsx` rejected the fixed
85 percent activation threshold. The workbook contained eight usable rows and
the agent extracted all eight, but confidence values of 75 and 78 alone moved
every row to unresolved. Confidence is now diagnostic, not a pass/fail gate.

The agreed row-level policy is:

- unknown VAT basis blocks activation because it changes the effective price;
- an unsupported package-to-unit conversion blocks activation because it can
  multiply or divide the effective price incorrectly;
- low confidence, currency uncertainty, and an Other material type remain
  visible diagnostic signals but do not independently block an otherwise usable
  row;
- every normalized name must be concise, standalone, and systematic, using the
  same attribute order and terminology across rows;
- unresolved rows enter an individual Review flow rather than a document-level
  editor;
- active prices remain editable and every edit archives the previous offer;
- removing one price archives its active offer while retaining the original source
  and row evidence for audit;
- row removal requires confirmation and cancellation changes nothing;
- a complete source cannot be removed through the product interface because
  deletion belongs to individual catalog positions.

The implementation adds row-level Review, Edit, and Remove actions to Source
Details, deterministic
recalculation after owner review. The original source, extracted row, confidence,
reason codes, prompt version, time, and TC remain retained. All 359 automated
tests pass. This remains a candidate until the owner accepts the real production
matrix: complete active row, VAT review, package conversion review, edit, row
removal, cancellation, failure recovery, and duplicate-submit
protection.

## 3.12.1 revision 4 candidate

Production rejected whole-source removal and exposed a client-only processing
indicator defect. The second `furniture_hardware_consumables.xlsx` run completed
successfully in 18.799 seconds with 10 of 10 rows active and TC 0.015, while the
browser continued to show Extracting prices. The agent and persistence did not
hang. The JavaScript guard had manually changed and disabled the button, but its
cleanup removed only the event listener and did not restore the mutated DOM.

Revision 4:

- removes whole-source deletion from Source Library and the application service;
- places compact Remove and Edit actions on every active main-catalog row;
- lets Edit change the normalized name, price, VAT, source unit, purchase unit,
  estimation unit, and conversion factor for one position;
- renders non-archived unresolved rows in a separate visible Needs review block;
- gives each unresolved row independent Review and Remove actions;
- resets the client-mutated Extract button after every completed or failed server
  cycle while preserving the real in-progress state;
- retains Source Details for audit and original-source access rather than making
  it the only place where rows can be managed.

The archived `lumber_pricelist_israel.xlsx` source was identified as the missing
eight-row unresolved set. Its source and all eight unresolved rows remain intact,
with zero offers, so it can be safely restored to partial after deployment. All
363 automated tests pass. Production acceptance remains required.

## 3.12.1 revision 5 candidate

Repeated uploads are normal update checks rather than duplicate errors. The
accepted comparison contract is row-level:

- an exact file digest returns the previously processed result without calling
  the agent, spending TC, writing another source, or replacing prices;
- a changed file or alternate scan is extracted and compared with the current
  active offer for the same company material and supplier;
- supplier SKU is the preferred stable row identity when present, with the
  normalized material identity as the fallback;
- price, currency, VAT basis, source unit, purchase unit, estimation unit,
  conversion factor, and normalized price determine whether a row changed;
- unchanged rows retain the current active offer and are counted as
  `unchanged` without a catalog write;
- changed rows are counted as `updated`, archive the preceding active offer,
  and create the new active offer;
- new identities are counted as `new`;
- unresolved rows never overwrite an active price;
- rows missing from a later upload are not removed automatically because an
  upload or extraction can be incomplete;
- a failed apply restores any active offers superseded before the failure.

The completion notice reports `new`, `updated`, `unchanged`, `unresolved`,
time, and TC. Exact duplicates report `Already processed`, the unchanged count,
zero agent time, and zero TC.

Revision 5 also repairs the visual regression introduced when row actions moved
from the accepted static catalog table into Streamlit controls. It retains
row-level Edit, Review, Source, and Remove while restoring the soft purple
surfaces, normal text weight, compact action buttons, and a square destructive
cross without a tooltip. All 366 automated tests pass. Production acceptance
must cover the exact duplicate, one changed row, one new row, one unresolved
row, missing-row preservation, rollback on failure, desktop geometry, hover
state, and narrow-screen wrapping.

## 3.12.1 revision 6 candidate

The catalog interaction pass removes duplicated source inspection and reduces
the amount of Streamlit UI rebuilt by each row action:

- Source and Source Library View are direct links: uploaded files download
  immediately through a short-lived owned URL, and supplier URLs open directly;
- active-row Edit reuses the source row already loaded with the catalog and
  avoids a second source-row query in the normal path;
- Needs review renders 5 rows per page instead of rebuilding every unresolved
  row and its controls after every click;
- only the field blocking activation receives a red asterisk, with no duplicate
  row title or review explanation above the form;
- catalog and review rows remove the extra divider and vertical gap, keep the
  accepted active-row tint, and use a neutral review-row surface;
- destructive crosses move left and all non-informational hover tooltips are
  suppressed on the Company Profile interface.

The follow-up geometry pass removes the remaining Streamlit block gap between
rows, restores the rounded Wood, Metal, and Coating containers, places removal
confirmation and its compact actions on one line, keeps Cancel secondary and
transparent, and aligns Previous, Next, and the page count on one row.

All 369 automated tests pass. Production acceptance remains required for row
geometry, Source/View behavior for URL, image, PDF, and spreadsheet sources,
review pagination, blocking-field markers, and Edit/Review/Save/Cancel latency.

## 3.12.1 revision 7 candidate

The accepted revision 6 geometry is preserved. The Needs review column labels
move down by 3 pixels without changing the header or row dimensions.

The interaction trace identified two avoidable latency sources. Every Price
Lists fragment action reloaded the same source, catalog, and review data through
11 sequential Supabase requests, and Previous/Next then forced a second fragment
rerun after the rerun already caused by the button. Revision 7:

- reuses a 60-second read snapshot keyed by company and user for UI-only
  interactions;
- invalidates that snapshot after source processing, row save, and row removal;
- moves pagination, Cancel, Save, and Remove state changes into callbacks so each
  action needs one fragment cycle rather than a follow-up manual rerun;
- keeps fresh database reads after every successful mutation;
- adds deterministic coverage proving pagination does not repeat the three
  loaders and Save receives the current form values.

All 373 automated tests pass. Production acceptance must measure Previous,
Next, Edit, Review, Cancel, Save, and Remove in the real authenticated session.

The owner completed that production interaction pass and accepted `d99a594` as
the rollback checkpoint on 26.09.2026. Previous, Next, Edit, Review, Cancel,
Save, and Remove are now responsive in the real authenticated interface. The
current layout is explicitly accepted as a good working version, not as final
visual polish. Further extraction-agent accuracy work remains inside task
3.12.1 and must preserve this checkpoint.
