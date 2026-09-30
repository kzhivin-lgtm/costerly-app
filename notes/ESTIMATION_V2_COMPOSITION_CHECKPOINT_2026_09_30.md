# Estimation v2 pure composition checkpoint, 2026-09-30

Task: 3.15.8 Estimation v2 replacement

## Protected boundaries

- no legacy Estimation Agent code is reused as architecture;
- Labor Engine is not modified or called by this slice;
- File Review, Objects, Object Detail and CSS are unchanged;
- no new database schema or production write path is added;
- delivery and installation remain project-level pricing policy, not object
  self-cost lines.

## Implemented contract

`use_cases/estimation_v2_composition.py` defines two pure contracts:

1. `estimation_object_facts_v1` accepts only evidence-backed object facts;
2. `estimation_object_composition_v1` combines already-produced deterministic
   cost lines and publishes self cost only when every required line is resolved.

Object-fact status is exactly `ready`, `review_required`, or `failed`.
Composed-estimate status is exactly `complete`, `review_required`, or `failed`.
Cost-line status is exactly `resolved`, `review_required`, or `failed`.

The extraction boundary rejects prices, costs, labor hours, machine minutes,
rates, overhead, margin, VAT, sale price and totals. It accepts only the 21
approved construction-template identifiers and material families supplied by a
versioned catalog. Manufacturing features and purchased components have bounded
field sets and cannot carry money or time estimates.

Blocking reason codes are finite and grouped around evidence, quantity,
dimensions, template, material identity and price, machinery route and cost,
purchased components, labor, overhead, currency, extraction and deterministic
engine failures. Unsupported free-form reason codes are rejected.

## Frozen scenarios covered

- E01: one complete cabinet fixture produces deterministic section totals,
  self cost and the temporary `self cost + 30%` unit selling-price suggestion;
- E02: two objects share one persisted OCR event and receive independently
  bounded evidence packages without another OCR call;
- E03: only cited physical pages and their OCR blocks enter the object input;
- E04: name, quantity and Ignore changes receive distinct bounded actions;
- E05: missing required facts remain explicit, block self cost and require a
  blocking review reason;
- E06: an unresolved material price remains visible while self cost and selling
  price remain unpublished;
- E07: external fabrication is a purchased component and has no corresponding
  internal machinery line;
- E08: manufacturing facts require a resolved machinery-cost result;
- E09: a failed object does not invalidate a completed object;
- E10: the same frozen input and version set has one stable idempotency key;
- E11: a name-only change does not create a revision or recalculate cost;
- E12: quantity and Ignore changes affect only aggregation or active membership.

Missing labor output and mixed currencies also block self cost explicitly.

The E01 fixture is stored at
`tests/fixtures/estimation_v2/e01_complete_object.json`. Repeated composition of
identical inputs produces identical output and requires no LLM, database or
engine call.

## Verification

- 34 focused Estimation v2 evidence, extraction, persistence, composition and
  revision tests pass;
- full suite passes with 764 tests and 28 warnings;
- `py_compile` and `git diff --check` pass.

## Object Facts extractor, verified 2026-10-01

`agents/estimation_v2_facts_agent.py` is a separate bounded extractor. It
receives only one frozen `estimation_input_v2` package. The original source
document is not attached and OCR is not called again.

Each supplied OCR block now has a deterministic evidence reference in the form
`ocr:{ocr_event_id}:p{page}:b{source_index}`. The extractor rejects citations
outside the supplied OCR blocks and private evidence artifacts.

Anthropic rejected the complete nested JSON grammar because of unsupported
keywords and grammar-size limits. The provider boundary therefore uses one
strict `facts_json` string field. The decoded compact transport is still
checked for exact fields, normalized, validated against the full internal
contract, checked against the versioned material-family set and checked for
invented evidence references before it can leave the agent boundary.

Server-owned versions, identifiers, object name, approved quantity and preview
reference are never copied from model output. They are bound deterministically
after extraction. This prevents the model from changing object identity and
reduces unnecessary output tokens.

Live synthetic checks passed:

- E01 selected `base_cabinet_open`, extracted one birch-plywood requirement
  and correctly returned `material_quantity_missing` rather than guessing;
- E05 kept width, depth and height null and returned
  `dimensions_missing` plus `material_quantity_missing`;
- both usage records report `source_document_attached=false` and
  `ocr_rerun=false`.

No File Review, Objects, Object Detail, CSS or Labor Engine code changed.

## Object Facts persistence candidate, verified locally 2026-10-01

The additive `rfq_estimation_object_fact_results` migration stores one immutable
validated result per `input_id + agent_version` and links it to the standard
agent usage ledger. Company-member reads are protected through the owning
immutable input row.

The shadow coordinator:

- loads the allowed family vocabulary only from active Israel pricing
  identities;
- reuses an existing result for the exact input and agent version without a
  second model call;
- persists usage and validated facts;
- isolates one object's failure from every other object and from legacy
  Estimation.

The runtime hook uses a separate executor and starts only after legacy
Estimation completes. `ESTIMATION_V2_FACTS_SHADOW_ENABLED` defaults to false,
so the prepared code cannot alter production behavior before the migration and
an explicit enablement decision.

Local verification now passes with 764 tests. The migration is not yet applied
to production, the feature flag is not enabled, and no production fact row has
been written.

## Next implementation slice

After explicit approval, apply the additive migration, deploy the code, enable
the shadow flag and run one bounded production acceptance file. Keep the current
UI and Labor Engine unchanged. Material resolution, machinery, overhead and
self-cost publication remain deterministic downstream stages.
