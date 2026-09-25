# Price Source Agent Accuracy

Task: 3.12.1
Status: active
Priority: P1
Protected checkpoint: `d18b533` (accepted 3.10.1 Price Catalog UI)

## Objective

Make the agent reliably turn real supplier websites, files, and photos into
auditable catalog prices. Improve extraction, material-type classification,
unit normalization, confidence, and ready-versus-unresolved decisions without
changing the accepted catalog presentation.

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

The current schema assigns one top-level category to the entire source. This is
insufficient for mixed supplier documents, where separate rows may be Wood
Sheets, Wood Supplies, Metal Supplies, and Paints & Coatings. Prompt-only edits
cannot solve this. Before accuracy tuning, decide whether to move Material Type
to every extracted row while retaining source-level document metadata.

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

Use `TC` as the compact product label for Token Cost. `TC` is the run's
calculated USD cost from provider-reported input and output token usage and the
configured per-model pricing table. Display a currency value such as
`TC $0.042`, not the word cents and not a raw token count.

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
| Document type | Price list, catalog, quote, estimate, invoice, order, mixed or irrelevant document |
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
The accepted 3.10.1 UI must remain visually unchanged throughout this task.
