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

Focused automated checks: 64 passed. They cover V4 evidence assembly,
V4.1 bounded batching, incomplete-page rejection, no source-page duplication,
runtime handoff, publisher, contract, Material Engine and cost accounting.
`git diff --check` passed.

The saved production kitchen object input
`2be20d54-1962-4747-b2e3-9207ad9dff42` was read without change and passed
through the V4.1 local planner: all 39 physical pages were represented once,
with no batch over six pages. Its current deterministic index creates seven
batches, not one 472,178-token request. This is a planner verification only,
not a Cloud material result or a price acceptance.

## Explicit limitations before production acceptance

1. No paid V4.1 Cloud replay has been made yet. The model response quality,
   real token use, latency and material completeness are still unknown.
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

Commit and deploy this bounded extraction checkpoint, then run one controlled
V4.1 replay of the saved kitchen input. Acceptance is not merely completing:
every Cloud call must stay under the provider limit, all 39 pages must have a
coverage declaration, every published claim must have exact local evidence,
and unresolved material scopes must remain review-visible rather than guessed.
