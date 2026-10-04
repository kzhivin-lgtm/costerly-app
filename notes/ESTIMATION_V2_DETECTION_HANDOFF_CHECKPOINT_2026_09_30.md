# Estimation v2 Detection handoff checkpoint, 2026-09-30

Task: 3.15.8. Backend foundation and production shadow acceptance. File Review,
Objects, Object Detail and CSS remain unchanged.

## Completed and verified

- private original-file contract, SHA-256 audit identity and Storage ref;
- private evidence artifact and immutable object-input schema migrations;
- `estimation_input_v2` pure builder, strict OCR anchor-to-bbox validation and
  source-derived WebP cropper;
- Detection optional `evidence_page_refs` and `evidence_anchors` contract;
- synchronous repository primitive that returns `ocr_event_id`.

The original file is retained privately. Hash reuse across different runs is
not implemented yet and must not be claimed as current behavior.

## Verification

13 targeted tests passed, `py_compile db/repositories.py` passed, and
`git diff --check` passed.

## Shadow handoff completed after this checkpoint

The backend shadow vertical slice is now wired: Detection persists the original
in parallel and one synchronous OCR event; after File Review edits, the
background estimation job resolves an exact OCR anchor, renders the source
page, uploads a WebP preview, and persists the immutable input revision plus
artifact metadata. Invalid or missing evidence skips only the v2 shadow input
and does not break the legacy UI flow.

## Production shadow acceptance

- additive migrations are applied in production, including physical page refs,
  exact anchors, immutable v2 inputs, artifact metadata and both private buckets;
- Detection evidence contract is versioned as
  `detection_v3_2_6_3_estimation_evidence` and requires physical OCR page numbers
  plus verbatim unique bbox-bearing anchors;
- an unsafe real image result and a partial-block anchor result both skipped the
  v2 input without breaking Detection;
- a one-page furniture PDF produced four objects, four exact OCR anchor matches,
  four immutable `estimation_input_v2` rows and four private WebP artifacts;
- all four rows link to the persisted OCR event and one SHA-256-addressed private
  original; every referenced private Storage object was read back successfully;
- 737 tests passed and `git diff --check` passed.

## Remaining acceptance boundary

Authenticated browser verification of File Review to Objects routing, refresh,
company isolation and unchanged rendered UI is still required. It is separate
from the completed production backend acceptance and must not be inferred from
source inspection or automated tests.

## Current Detection vNext evidence checkpoint, 2026-10-04

The later owner-accepted checkpoint is `43933e5`, tagged
`checkpoint-2026-10-04-deferred-review-artifacts`. Detection now persists an
isolated source-derived preview for each accepted object before Estimation input
creation. File Review publishes the durable deferred Naming and Preview results
without requiring the in-memory worker future to survive a rerun.

For accepted one-page Page 23 evidence, Estimation will receive both the
object-local preview and the relevant private full-page artifact. This is enough
to preserve construction context, but the full page contains multiple products;
it must not be mistaken for object-local construction evidence. The accepted
run has no Estimation input row or Estimation output yet. In addition, external
dimensions are explicitly non-authoritative until the planned isolated
dimension pass is implemented.
