# Estimation V4.1 batched evidence experiment, 2026-11-01

Work number: `3.17.4.1`, continuing the existing material-only boundary.

## Decision

V4.1 replaces the active V3 material-facts extraction call with a new,
versioned `estimation_material_facts_v4_1` path. The immutable
`estimation_input_v4` dossier is unchanged. It is retrieved once, indexed
locally, then passed to bounded Cloud calls. Labor, manufacturing, overhead,
pricing, supplier selection and purchase rounding remain outside the agent.

## V4.1 guarantees

- Each source page belongs to exactly one bounded Cloud batch, currently at
  most six page images. Its OCR blocks and literals travel only with that
  batch. The source page and OCR are not re-created or sent to every call.
- The model must account for every requested page. A missing, repeated or
  malformed page declaration rejects the whole object result.
- Every material claim must cite an exact private page artifact or OCR block
  from the batch which produced it. Claims cannot cite a page outside their
  batch.
- V4.1 emits no cut rectangles, envelope proxies, inferred areas, inferred
  perimeters or construction-derived material quantities. A proven material
  with no direct norm is retained with empty quantity and a review item.
- Repeated claims with the same physical family/specification/unit are not
  silently summed. Their quantities are cleared and `material_scope_overlap`
  is blocking review, until a later evidence-backed aggregation policy exists.
- Resolver and Material Engine keep their existing Company Catalog -> Israel
  Reference -> `assumption_required` authority and estimate-wide purchasing
  role. V4.1 only changes extraction and evidence retrieval.

## Verified local evidence

Focused automated checks: 18 passed after the live-replay repair set. The
broader pre-replay material boundary suite passed 70 checks. They cover V4 evidence assembly,
V4.1 bounded batching, incomplete-page rejection, no source-page duplication,
runtime handoff, publisher, contract, Material Engine and cost accounting.
`git diff --check` passed.

The saved production kitchen object input
`2be20d54-1962-4747-b2e3-9207ad9dff42` was read without change and passed
through the V4.1 local planner: all 39 physical pages were represented once,
with no batch over six page images. The first planner made seven batches,
instead of one 472,178-token request.

## Controlled Cloud replay result

The owner explicitly approved the saved kitchen package for V4.1 testing.
No V4.1 fact result was persisted. The first local wrapper was interrupted
before aggregate persistence. Two later attempts reached the provider but
exposed output-boundary defects: the provider may wrap JSON in markdown, and
a dense specification batch can exceed the prior 4,000 output-token cap,
producing an unterminated JSON string. The earlier aggregate telemetry also
recorded zero tokens when a response failed parsing, because it retained a
response only after parsing.

V4.1 now recovers the first complete JSON object before applying its strict
schema, records a received response before parsing so its usage survives a
failure, raises the output cap to 8,000, and limits a multi-page batch to 240
OCR blocks as well as six images. The real kitchen dossier now plans as 20
calls, with each page still present exactly once. A one-page source with more
than 240 OCR blocks remains one page rather than being silently truncated.
This is deliberately not yet another paid replay: the 20-call cost/latency
trade-off needs owner confirmation.

## Explicit limitations before production acceptance

1. No complete paid V4.1 Cloud replay has produced persisted facts. The model
   response quality, full-token receipt, latency and material completeness
   remain unknown.
2. The topic index is intentionally conservative and OCR-keyword based. It
   helps batching and auditability but does not yet decide a construction or a
   BOM hierarchy.
3. V4.1 safely refuses to aggregate repeated material scopes. A later,
   separately approved aggregation rule is needed to turn non-overlapping
   detailed production pages into one approximate consumption norm.
4. The existing UI submission path can use V4.1 for a new estimate. The
   controlled replay tool `tools/replay_estimation_v4_1_input.py` reads an
   already persisted input without OCR or upload. Its default is read-only;
   `--execute` is intentionally explicit because it calls Cloud and persists
   a V4.1 fact result. It does not yet republish the whole estimate or replace
   an existing V3 result.

## Next verification

Choose the output budget for the next controlled replay. The current safe
plan has 20 calls, each with no more than six images and 240 OCR blocks when
the source page itself permits it. Acceptance is not merely completing: every
Cloud call must stay under the provider limit, all 39 pages must have a
coverage declaration, every published claim must have exact local evidence,
and unresolved material scopes must remain review-visible rather than guessed.
