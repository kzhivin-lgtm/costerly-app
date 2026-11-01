# Detection V8.4.5 global batched assembly-scope checkpoint, 2026-11-01

## Status

Owner-verified production checkpoint for the rare combination of an
`assembly_set` document and V6.41 budgeted Discovery batches. The positive
witness is `24-215. Кухня. СБ.pdf`: after V8.4.5, the owner observed one final
commercial object, as intended.

- Production commit: `4c9ff38`,
  `fix(detection-v8.4.5): restore global batched assembly scope`.
- Protected production tag:
  `detection-v8.4.5-global-batched-assembly-scope-production-2026-11-01`.
- Protected pre-change tag:
  `detection-v8.4.4-before-v8.4.5-global-assembly-scope` at `940389b`.
- The production observation confirms final object count only. No run ID,
  timing, token or cost record was supplied for this successful rerun, so none
  is inferred here.

## Problem and supported cause

[verified] V8.4.4 allowed `24-215. Кухня. СБ.pdf` to complete V6.44 geometry
validation, but it published 25 Membership components. The document was
correctly pre-categorised as `assembly_set`; V6.41 split Discovery into four
transport batches and retained 38 Object Evidence Islands.

[verified] The V6.41 merge path then wrote a synthetic
`ordinary_object_set` `document_scope` because a single page-local Discovery
batch cannot truthfully assert a document-wide hierarchy. The existing V6.26
assembly compiler correctly saw that ordinary scope and did not compile the
25 intermediate Membership components into one dossier.

[verified] This was not a Membership or Island-recall repair. V6.41 had
discarded the only scope signal that could authorise the already-existing
V6.26 compiler after all batches were merged.

## V8.4.5 behaviour

V8.4.5 adds exactly one optional scope observation after all V6.41 Discovery
batches have been deterministically merged and classifications have produced a
fixed Object Evidence inventory.

It activates only when all conditions hold:

1. the pre-router category is `assembly_set`;
2. V6.41 budgeted Discovery is active;
3. the Mistral-anchor route is inactive.

The additional call receives only the fixed Object Evidence crops and bounded
per-View OCR facts. It receives no full-page context. It returns only the
pre-existing V6.11 `document_scope` schema. The existing V6.11 validator still
requires Registry-owned roots and relationship witnesses. A positive result
allows the existing V6.26 compiler to publish one document assembly only after
ordinary Membership has completed.

It cannot create, remove, split, reclassify or move Islands. It cannot change
Candidate Regions, Fusion, Conflict Resolver, router, render attachment rules,
Membership evidence, Membership components, dimensions, Naming, preview or UI.

## Failure and cost boundary

The V8.4.5 call is fail-closed and has no retry. Provider, JSON, schema,
unknown-Island, incomplete-crop or provider-image-limit failure preserves
V6.41's ordinary-scope fallback and continues the usual Membership path.

The new call occurs only on the rare large batched assembly route. It sends no
additional full-page images and is separately audited with its own provider
usage. Its tokens and cost are included in total Detection usage. It is not
called for:

- ordinary object sets, including Floors 06 and 07;
- single-pass assembly sets, including the accepted six-page `V_Cabineter.pdf`;
- Mistral-anchor routes, Page 23, Ada, or source-degraded routes.

## Verification

[verified] `python -m py_compile` completed for the changed module and tests.

[verified] Focused V8.4.5 checks passed, `20 passed`. They prove that the
scope call is gated to a batched non-anchor assembly set, gets the complete
fixed inventory without full-page context, and treats unknown IDs as a
non-fatal invalid observation.

[verified] Detection regression subset passed, `153 passed`. It includes
Discovery, scope validation, V6.41 batching, Membership, Registry Evidence and
prompt-contract tests.

[verified] Full repository suite on the current checkout returned `1526
passed, 22 failed`. Every failed test concerns UI, Estimation or materials
files outside V8.4.5's changed Detection path. [unknown] Their exact historical
status was not re-established from the pre-change commit in this session.
They were not repaired opportunistically in this checkpoint.

[verified] Owner production check on `24-215. Кухня. СБ.pdf` produced one
commercial object.

## Chat history and experiment ledger

### V7 discovery and floor-plan sequence

- V7.14 became the accepted operational baseline because it retained expected
  Islands, including Conflict Resolver recovery for the difficult P10 islands,
  preserved dimension ownership, and ordinarily assembled the expected
  commercial objects. Its known defect was one extra whole-level floor-plan
  object.
- Several later floor-plan experiments were rejected. They changed Discovery
  classification, candidate order or downstream handling together, which made
  Membership output fragile and inflated the final count. No such experiment
  is a base for V8.4.5.
- The key design conclusion is retained: a whole-level plan is
  `document_context` only when Discovery can support that classification. It
  is not a reason to mutate IDs, reorder retained evidence, rebuild
  Membership, or discard technical plans that are Object Evidence.

### Render/photo work

- Presentation renders and photos remain `representation_kind` of ordinary
  Object Evidence. They are not a Discovery route, a separate object creator
  or a global adapter.
- Their attachment is governed by the existing narrow visual criteria and
  strict V7.11 decision validation. V8.4.5 does not alter it.
- Earlier failures such as `V7.11 presentation render attachment/decision is
  invalid` were schema-contract failures. V8.4.5 neither weakens that
  validation nor hides it.

### V8 reconstruction and rollback lessons

- The first V8 rewrite was rejected because it recreated contracts without
  preserving all Registry and Membership invariants. It produced schema errors
  and Island-loss regressions, so it is not the source of the accepted path.
- V8.2 attempts to strengthen Membership pairing exposed invalid-link failures
  and lower Island counts. They were rejected rather than patched around.
- V8.3 returned to the V7.14 behaviour with isolated experiments. V8.4 became
  the exact protected V7.14 runtime baseline, so every later adjustment can be
  compared against a known implementation rather than a cumulative rewrite.

### V8.4.x narrow repairs

- V8.4.1 fixed Page 23 preview materialisation and terminal Processing-error
  feedback without changing Discovery or Membership.
- V8.4.2 normalised only one semantically inert non-render `no_match` row;
  genuine presentation-render decisions remain strict.
- V8.4.3 compacted the existing V6.11 scope observation so valid scope
  evidence fits its declared schema limit.
- V8.4.4 repaired a valid `core_bbox` that escapes an otherwise valid outer
  `bbox` by retaining the outer evidence envelope and using it as `core_bbox`.
  It fixed the V6.44 P35 validation stop without changing geometry ownership
  outside that condition.
- V8.4.5 restores the missing document-scale scope observation only after
  batched Discovery has a complete inventory. This is the first change in this
  chain that addresses the 25-component kitchen outcome directly.

## Estimation evidence state

[verified] Detection already persists bounded evidence suitable for beginning
the next Estimation-agent work:

- locked object identity, quantity and review state;
- every relevant physical `evidence_page_ref`, with page number, source label
  and bounded retrieval regions;
- cited OCR text blocks and literal items on those pages;
- private full-source-page artifacts, generated from the original file;
- a private original-file reference, OCR event identity and immutable object
  input revision.

The active `estimation_input_v4` contract deliberately gives Estimation source
pages and OCR, not a Detection narrative presented as evidence. The current
V3 Estimation agent can extract material facts, bounded dimensions and parts,
then feed the deterministic Company Catalog -> Israel Reference ->
`assumption_required` Material Engine path.

[verified] This does not yet make a full commercial estimate correct. Known
V3 material-facts defects remain: unsupported cut geometry must not be
invented, explicit source measurements must outrank envelope proxies, and
physical subtype compatibility must prevent unrelated catalog selection. Labor,
manufacturing, overhead, installation and sales pricing are separate engines
and are not delegated to the agent.

## Next safe verification

Before expanding Estimation behaviour, perform one read-only audit of the
successful V8.4.5 kitchen run: confirm the compiled single object's persisted
`evidence_page_refs`, immutable `estimation_input_v4`, OCR event, private page
artifacts and artifact count. This confirms that the newly repaired assembly
scope preserved the full dossier into Estimation, rather than only fixing the
visible object count.

After that audit, continue existing task `3.17.4.1` with a written contract
for the next Estimation-agent capability. Keep source extraction, deterministic
material resolution, labor routes and pricing authority separate.
