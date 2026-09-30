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

- 22 focused Estimation v2 evidence, composition and revision tests pass;
- full suite passes with 753 tests and 27 existing warnings;
- `py_compile` and `git diff --check` pass.

## Next implementation slice

Define the bounded Object Facts extraction request and response schema for the
model, then run it against frozen E01, E05 and E06 evidence packages. The model
must emit facts only. Material resolution, Labor Engine, machinery, overhead,
self cost and UI persistence remain outside that call.
