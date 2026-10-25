# Detection V6.10 combined Evidence Review experimental checkpoint

Date: 2026-10-25
Status: protected experimental checkpoint. It is not a universal Detection
acceptance or a release gate for other routes.

Implementation commits: `1bd3c6e`, `c447b5c`, `27e7e22`.
Production deployment title: `fix(detection-v6.10): bound combined review output`.

## Scope

V6.10 changes only the V6.7 Sonnet Mistral-anchor route when the immutable
Mistral inventory contains two to ten object-evidence Islands. It preserves
Mistral page-local boxes as boundary authority, sparse universal candidate
selection, the five public evidence criteria, the deterministic strong-link
rule, and conditional reconciliation.

It replaces V6.9's two sequential provider calls, preliminary link discovery
and criteria review, with one Combined Evidence Review response. Every selected
candidate still receives all five criterion statuses: identifier, topology,
geometry, dimensions, and construction. The provider returns compact enum
statuses, a short pair reason, and at most two typed facts. Runtime creates the
auditable criterion rows and accepts a link only when deterministic evidence
validation passes. Reconciliation remains conditional and was not needed in the
successful Adda run.

V6.10 does not change the ordinary Haiku path, Page23 route, source-degraded
route, OCR, Fusion, Mistral anchor geometry, or deterministic package
reconciliation.

## Verified live Adda result

Run: `run_c2ddd6be0c5b4add910d317382691d54`.
Created: `2026-10-25T18:21:17.311691+00:00`.
Prompt: `detection_v6_10_combined_evidence_review`.
Model: `claude-sonnet-4-6`.

- Mistral supplied eight stable page-local groups. The run returned two
  commercial components, each with four Views.
- L-shaped cabinet membership was
  `G-P001-001`, `G-P002-002`, `G-P003-002`, `G-P004-002`.
- Counter membership was
  `G-P001-002`, `G-P002-001`, `G-P003-001`, `G-P004-001`.
- Combined review selected eight same-product candidate pairs: four within the
  L-shaped component and four within the counter component. All eight passed
  the deterministic strong-link rule. The accepted merge graph retained six
  necessary edges and no cross-product edge.
- Each candidate card recorded `identifier: not_visible`; topology, geometry,
  dimensions, and construction supplied the supported evidence. The run
  persisted sixteen typed evidence facts.
- No Island remained outside a strong reference component, so conditional
  reconciliation did not execute. This is correct for this run, but it is not
  proof that reconciliation is correct in production.

The resulting object memberships are correct for the owner-defined Adda
benchmark. Local View labels on page 1 remain positional rather than semantic:
`P01.V1` is the right/upper L-shaped view and `P01.V2` is the left/lower
counter, whereas pages 2 through 4 use the opposite local ordering. This is an
audit-label defect, not an object-membership defect.

## Measured cost and latency

| Stage | Duration | Input tokens | Output tokens | Cost |
|---|---:|---:|---:|---:|
| Proposal | 45.628 s | 12,805 | 3,151 | $0.085680 |
| Combined Evidence Review | 52.662 s | 10,752 | 3,285 | $0.081531 |
| Detection aggregate | 98.857 s | 23,557 | 6,436 | $0.167211 |
| OCR | 2.581 s | - | - | provider cost unavailable |
| Full RFQ orchestration | 105.582 s | - | - | - |
| Naming | 3.516 s | - | - | $0.009716 |

Known Detection plus Naming cost is `$0.176927` (17.6927 cents). It excludes
Mistral OCR cost because the persisted usage event has no provider cost.

| Comparator | Detection duration | Detection cost | Result |
|---|---:|---:|---|
| V6.7 | 80.101 s | $0.140559 | incorrect three-component Adda result |
| V6.8 | 133.222 s | $0.203607 | correct two four-View components |
| V6.9, true three-call sum | 143.445 s | $0.237150 | correct two four-View components |
| V6.10 | 98.857 s | $0.167211 | correct two four-View components |
| V5.10 historical baseline | 75.948 s | $0.160950 | different contract, not a direct acceptance comparator |

Relative to V6.9, V6.10 removes 44.588 Detection seconds (31.1 percent) and
$0.069939 (29.5 percent). Relative to V6.8, it removes 34.365 seconds (25.8
percent) and $0.036396 (17.9 percent). V6.7 is cheaper but failed the required
Adda object boundary, so it is not a viable replacement.

## Failure repaired by this checkpoint

The first V6.10 attempt at `2026-10-25T18:14:30.064873+00:00` failed provider
response parsing with `Unterminated string starting at: line 1 column 22676
(char 22675)`. Its failed Review used 10,723 input tokens, 6,144 output tokens,
$0.124329, and 96.048 seconds. Whole-attempt cost is not known because the
failed aggregate lacks complete Proposal usage. Commit `27e7e22` bounded the
provider schema to compact statuses and the next Adda run succeeded.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 /Users/qb/costerly-app/.venv/bin/python -m
  py_compile agents/anthropic_adapter.py` passed.
- Focused regression suite passed: `104 passed` across spatial inventory,
  registry evidence, model router, page-image and timing tests.
- `git diff --check` passed before documentation changes.

No full suite was run after V6.10. A prior V6.9 full-suite result of `1401
passed, 19 failed` contained pre-existing failures outside Detection. It is not
V6.10 verification.

## Explicit limitations and protected continuation

1. One successful Adda run verifies this bounded route once. It does not prove
   HSL, Page23, ordinary Haiku, source-degraded, or universal Detection safety.
2. Reconciliation has unit coverage but no V6.10 live run where a partial
   component requires it.
3. Pair reasons can still use a third View as corroboration. Endpoint IDs and
   typed facts remain pair-specific, but the prose should not be treated as an
   independent proof channel.
4. Provider `maxLength` is not a hard output cap. The compact contract lowered
   risk and passed once, but must be watched on larger inventories.
5. Page-1 local View ordering needs a separate audit-label diagnosis. Do not
   change object boundaries to cosmetically align the labels.

The next safe experiment is a document whose sparse strong graph leaves an
Island or component for conditional reconciliation. It must inspect exact
membership, candidate rows, all criterion cards, call count, latency, tokens,
and cost before any prompt tuning, candidate pruning, route expansion, or
generalization.
