# Price Source Agent Accuracy

Task: 3.10.2
Status: active
Priority: P1
Protected checkpoint: `d18b533` (accepted 3.10.1 Price Catalog UI)

## Objective

Make the agent reliably turn real supplier websites, files, and photos into
auditable catalog prices. Improve extraction, material-type classification,
unit normalization, confidence, and ready-versus-unresolved decisions without
changing the accepted catalog presentation.

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
3.10.1 UI must remain visually unchanged throughout this task.
