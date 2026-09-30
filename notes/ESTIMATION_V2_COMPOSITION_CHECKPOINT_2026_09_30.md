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

- 36 focused Estimation v2 evidence, extraction, persistence, composition and
  revision tests pass;
- full suite passes with 769 tests and 28 warnings;
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

The additive migration was applied to production on 2026-10-01. The new table
is readable and contains no fact rows before acceptance. The active Israel
catalog contains 2,832 pricing identities across three PostgREST pages and 51
material families. The runtime loader paginates all rows instead of silently
stopping at the 1,000-row API default.

Local verification now passes with 769 tests. The feature flag is not enabled,
and no production fact row has been written.

## Labor Engine compatibility inspection, 2026-10-01

The existing Labor Engine remains isolated and has no runtime caller outside
its eight direct tests. Its deterministic core is useful, but it is not yet
compatible with `estimation_object_facts_v1` or the production Company Profile
context:

- Object Facts stores the template under `template.code`; Labor expects
  `template_code`;
- material specifications are nested; Labor reads `thickness_mm` as a direct
  material field;
- Labor checks `edge_bander` and `powder_coating_booth`, while production uses
  `wood_edge_bander` and `finish_powder_booth`;
- production uses family `stainless_steel` plus an alloy specification, while
  Labor expects `stainless_304` or `stainless_316` as family values;
- only five of the 21 approved construction templates are implemented;
- delivery and site setup were emitted per object before the compatibility
  repair, contradicting the approved sales-only policy.

Direct compatibility probes before the repair returned `unsupported_template`,
`edge_bander_availability_unknown` and
`external_powder_component_not_yet_enabled` for otherwise valid v2 and
production-shaped inputs. Labor must therefore receive facts only through the
bounded adapter and production machine codes.

One separate Object Facts issue found by the inspection was fixed: exact
versioned material-family values may contain spaces. Validation now accepts a
non-empty exact catalog value rather than requiring identifier syntax.

## Labor Engine compatibility repair, 2026-10-01

The user confirmed that delivery 3% and installation 10% are additions to the
already calculated selling price. They are not self cost. Labor Engine now
emits workshop labor only: fabrication, quality inspection and protective
packaging. Vehicle loading, delivery trips and site installation operations
were removed from its active baselines and cannot change the labor trace.

The bounded `object_facts_v1 -> labor_input_v1` adapter now maps nested template
and material facts without asking extraction to duplicate fields. Labor uses
the production Company Profile codes `wood_edge_bander` and
`finish_powder_booth`, reads nested thickness, and understands production
`stainless_steel` with an explicit 304 or 316 alloy specification.

Compatibility is verified against the real E01 Object Facts shape and real
Company Profile machinery-row shape. Installation scope included versus
excluded produces identical self-cost labor output. The five existing template
routes are compatible; expanding the remaining templates and cross-object
batch aggregation remains separate work.

Verification: 11 direct Labor Engine tests, 83 Labor, Machinery and
manufacturing tests, and the full 769-test suite pass.

## Next implementation slice

After explicit approval, apply the additive migration, deploy the code, enable
the shadow flag and run one bounded production acceptance file. Keep the current
UI and Labor Engine unchanged. Material resolution, machinery, overhead and
self-cost publication remain deterministic downstream stages.
