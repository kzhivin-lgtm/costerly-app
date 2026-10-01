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
rates, overhead, margin, VAT, sale price and totals. It decomposes each actual
detected object directly from its evidence. Material families come from the
versioned material catalog. Manufacturing features, purchased components and
fabrication operations have bounded field sets and cannot carry money or time
estimates.

Blocking reason codes are finite and grouped around evidence, quantity,
dimensions, material identity and price, machinery route and cost,
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

- 36 focused Estimation v2 evidence, extraction, persistence, composition and
  revision tests pass;
- full suite passes with 778 tests and 27 warnings;
- `py_compile` and `git diff --check` pass.

## Object Facts extractor, verified 2026-10-01

`agents/estimation_v2_facts_agent.py` is a separate bounded extractor. It
receives only one frozen `estimation_input_v2` package. The original source
document is not attached and OCR is not called again.

Each supplied OCR block now has a deterministic evidence reference in the form
`ocr:{ocr_event_id}:p{page}:b{source_index}`. The extractor rejects citations
outside the supplied OCR blocks and private evidence artifacts.

The provider boundary uses a compact structured-output schema for the actual
transport object. The returned object is still checked for exact fields,
normalized, validated against the full internal contract, checked against the
versioned material-family set and checked for invented evidence references
before it can leave the agent boundary.

Server-owned versions, identifiers, object name, approved quantity and preview
reference are never copied from model output. They are bound deterministically
after extraction. This prevents the model from changing object identity and
reduces unnecessary output tokens.

Live synthetic checks passed:

- E01 extracted one birch-plywood requirement from the supplied object evidence
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
Estimation completes. After production acceptance,
`ESTIMATION_V2_FACTS_SHADOW_ENABLED` defaults to true. An explicit `false`
remains the Railway rollback switch.

The additive migration was applied to production on 2026-10-01. The new table
is readable and contains no fact rows before acceptance. The active Israel
catalog contains 2,832 pricing identities across three PostgREST pages and 51
material families. The runtime loader paginates all rows instead of silently
stopping at the 1,000-row API default.

Production backend acceptance passed on 2026-10-01 with benchmark object
`CB-01 Storage cabinet`. Revision 2 reused the persisted OCR event, original
reference and private preview while adding deterministic OCR block refs. One
bounded call persisted the earlier facts contract as `review_required` with
four material requirements and explicit missing-
quantity review items. Usage proves `source_document_attached=false` and
`ocr_rerun=false`. An immediate repeat reused the stored result without a
second model call.

## Labor Engine compatibility inspection, 2026-10-01

This historical inspection is superseded by the universal operation contract
approved on 2026-10-01. Labor now consumes an agent-created operation plan,
validates exact Company Profile capability codes and calculates hours without
classifying the object. Delivery and site work remain excluded from self cost.

One separate Object Facts issue found by the inspection was fixed: exact
versioned material-family values may contain spaces. Validation now accepts a
non-empty exact catalog value rather than requiring identifier syntax.

## Labor Engine compatibility repair, 2026-10-01

The user confirmed that delivery 3% and installation 10% are additions to the
already calculated selling price. They are not self cost. Labor Engine now
emits workshop labor only: fabrication, quality inspection and protective
packaging. Vehicle loading, delivery trips and site installation operations
were removed from its active baselines and cannot change the labor trace.

The bounded Object Facts to Labor adapter now maps actual part, connection and
material facts without asking extraction to duplicate fields. Labor uses
the production Company Profile codes `wood_edge_bander` and
`finish_powder_booth`, reads nested thickness, and understands production
`stainless_steel` with an explicit 304 or 316 alloy specification.

Compatibility is verified against the real E01 Object Facts shape and real
Company Profile machinery-row shape. Installation scope included versus
excluded produces identical self-cost labor output. Cross-object batch
aggregation remains separate work.

Verification: 11 direct Labor Engine tests, 83 Labor, Machinery and
manufacturing tests, and the full 778-test suite pass.

## Production transition repair, 2026-10-01

The first live transition from File Review reached `Objects`, but the access
guard ran before the background worker had created the `rfq_estimates` shell.
Runtime events recorded `company_access_error` at 21:38:35 UTC, followed by the
same estimate shell being created at 21:38:36 UTC. Detection and the background
Estimation job had not failed. The UI had rejected a valid estimate during this
one-second creation race.

The shell and any File Review edits are now persisted synchronously before the
expensive background job is submitted. The company access guard remains strict.
If shell preparation fails, the transition stays in File Review and records a
visible Estimation error instead of entering Objects with an invalid route.

Verification: the regression test requires the order `edits_applied`,
`shell_created`, `background_submitted`; 203 targeted access and persistence
tests pass; the full 778-test suite passes.

## Image-only evidence repair, 2026-10-01

The first accepted production drawing exposed a second independent issue. OCR
returned the page body as one image while Detection extracted object facts from
the visual document. Exact text anchors therefore could not resolve to OCR
bounding boxes, all four v2 inputs were skipped, and no Object Facts call ran.
The visible `failed` status came from the legacy Estimation placeholder before
it emitted a usage event. It was not an Object Facts failure.

When an exact OCR anchor is unavailable, the handoff now uses the object's
declared physical evidence page as a source-derived full-page preview. It does
not attach the original document or invent crop coordinates. Exact OCR crops
remain preferred when available. Object Facts is also queued before the legacy
path so a legacy failure cannot prevent v2 evidence processing.

Verification: the image-only fixture creates one immutable input with a private
preview and zero OCR text blocks; ordering requires `facts_queued` before
`legacy_started`; the full 774-test suite passes.

The first bounded image-only production call then exposed an invalid citation:
Object Facts correctly read dimensions and materials from the approved
Detection object, but cited an unrelated OCR footer because it was present in
the allowed page blocks. Image-only fallback inputs now remove all unrelated
OCR blocks and leave the private source preview as the only evidence ref for
Detection-derived facts. The prompt explicitly forbids citing OCR text that
does not support the fact. The extractor version advanced to
`estimation_object_facts_agent_v2`, so the invalid v1 result cannot be reused.

The first v2 retry correctly rejected unrelated OCR citations, then exposed a
transport mismatch for square profile text such as `20x20`. The bounded
normalizer now converts equal square dimensions to the numeric weld face used
by Labor Engine. A rectangular value such as `20x40` remains blocked until the
joint orientation identifies the actual weld face. The full 778-test suite
passes.

The next retry exposed an asymmetric sentinel conversion. Unknown material
quantity `0` already normalized to null, while an unknown purchased component
quantity did not. Purchased component quantity now follows the same rule.
Validation allows null only for `review_required` facts and still rejects it for
`ready` facts. The full 778-test suite passes.

## Next implementation slice

Deploy the transition repair and repeat the same production File Review to
Objects acceptance. After the route is stable, verify the new input, facts and
usage rows. Material resolution, machinery, overhead and self-cost publication
remain deterministic downstream stages.
