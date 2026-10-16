# Detection V4 evidence handoff candidate, 2026-10-16

Status: accepted benchmark checkpoint for the V4 Evidence handoff and
source-identifier transport. It is not a completed boundary-quality checkpoint
for unlabelled multi-object drawings. Adda remains the active boundary defect.

## Decision

Detection V4's outcome is a correct, sufficient, auditable immutable `rfq_estimation_object_inputs.input_payload`, not an asserted external object envelope. Detection owns commercial object identity, source-label transport, physical quantity, full relevant physical pages and non-semantic visual regions.

Quantity is always present. It defaults to one unless source evidence proves another count. `review_required` records material count ambiguity.

Detection does not emit external dimensions, dimension candidates, nodes, detected materials, notes, missing information, or model confidence values.

## Evidence boundary

`presentation_preview_bbox` and its persisted crop are UI-only for File Review and Object Detail. Neither the crop nor its reference reaches Naming or Estimation.

The V4 input contains only object ID/name/quantity, cited physical pages, immutable full-page private artifacts and raw spatial OCR blocks from those pages. It carries no Detection roles, boundary claim, dimensions, materials, notes or preview ref.

Naming receives the locked object list, relevant full pages once per batch and object-specific OCR. It combines vision and OCR while preserving author code/label order. Estimation receives the same full pages and OCR after File Review, deduplicated by immutable storage reference in one batch.

## Metadata

`project_name`, `design_partner` and `client` remain separate. Design partner created the design or technical brief. Client is the end owner or operator. They may match only for source-supported self-designed direct commissioning. `author` remains hidden technical metadata.

## Protected behavior

The registry still locks commercial objects before Naming. Repeated views and kitchen/detail packages remain one commercial object. A shared physical page may belong to several object packages. Presentation Preview remains asynchronous and non-blocking for File Review.

## Migration and verification

`db/sql/2026_10_16_detection_v4_object_evidence.sql` adds `review_required` and permits `estimation_input_v4`. Focused V4 checks pass: 48 tests covering schema validation, handoff assembly, UI normalization, deferred Naming and timing paths. A direct live model smoke call did not return within its 30-second local observation window, so it is inconclusive, not acceptance.

## Production benchmark record

- `page-23.pdf`: three independent commercial objects remain the accepted
  labelled-sheet benchmark.
- `24-215. Кухня. СБ.pdf`: one Kitchen with all 39 relevant physical pages is
  the accepted Evidence-completeness benchmark.
- `Металл (1).pdf`, run `run_fc5f26951bdf47b5baf8e7633c78aee9`: returned 15
  objects with the current V4 registry. The prior 13-object interpretation
  remains valid, but `ЛС-1` and `ЛС-2` are an unresolved source-document
  ambiguity, not a product defect: the sheet provides their labels but no
  decisive commercial-scope or quantity evidence. Do not hard-code either 13
  or 15 as a global rule from this file.
- The same Metal run verified the source identifier fix: the spaced label
  `ОМ 15-1` persisted as `ОМ 15-1 — Stair railing`. The parser now treats a
  literal identifier with an internal space as an identifier, rather than a
  name without an index.

## Open boundary defect

`Adda.pdf`, run `run_590733e409c44ed990b5636f685cd69f`, used Visual Registry
V4 but incorrectly merged two visually separate, unlabelled complete
assemblies into one commercial object. This is not a Naming or Evidence-page
failure. The next change must make visual physical-assembly candidates and
their positive merge evidence auditable within the existing registry call;
it must not rely on OCR labels or add a second model call.
