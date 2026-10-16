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

`db/sql/2026_10_16_detection_v4_object_evidence.sql` adds `review_required` and permits `estimation_input_v4`. Focused V4 checks pass: 49 tests covering schema validation, handoff assembly, UI normalization, deferred Naming and timing paths. A direct live model smoke call did not return within its 30-second local observation window, so it is inconclusive, not acceptance.

Production acceptance requires one real upload with review of every object ID, quantity, pages, UI preview, OCR, naming result and persisted V4 input payload.

## Production benchmark record

- `page-23.pdf`: three independent commercial objects remain the accepted
  labelled-sheet benchmark.
- `24-215. Кухня. СБ.pdf`: one Kitchen with all 39 relevant physical pages is
  the accepted Evidence-completeness benchmark.
- `Металл (1).pdf`, run `run_fc5f26951bdf47b5baf8e7633c78aee9`: returned 15
  objects under the current V4 registry. The earlier 13-object result and the
  current 15-object result differ only on the genuinely ambiguous `ЛС-1` and
  `ЛС-2` drawings. Neither number is a global canonical rule.
- The same Metal run verified source-identifier transport as
  `ОМ 15-1 — Stair railing`.

## Open boundary defect

`Adda.pdf`, run `run_590733e409c44ed990b5636f685cd69f`, used the integrated
Visual Registry V4 but incorrectly merged two visually separate, unlabelled
complete assemblies into one commercial object. This is neither a Naming nor
an Evidence defect.

## Active boundary experiment, not a checkpoint

The owner approved a replacement for the rejected in-registry island and
post-hoc reviewer experiments. Before Registry, a conditional correspondence
stage receives only isolated large drawing crops and physical page numbers. It
does not receive the file name, OCR, project metadata, room titles or title
block. It partitions the cropped representations into candidate physical
assemblies using positive cross-view visual correspondence.

When two or more crops exist and all of them fit in one request, the Registry
must map each resulting assembly candidate to exactly one commercial object.
It cannot merge two candidates. When the crop set would exceed the request
image ceiling, Detection keeps the accepted V4 path rather than silently
truncating a physical partition. This experiment adds one conditional Sonnet
call and does not alter the V4 Estimation handoff.

The correspondence usage event persists an `assembly_partition_audit` with
candidate membership, visual identity and correspondence basis. It is
observability only and cannot alter a Detection result.

The result remains unverified until live benchmarks show all of the following:

- Adda produces the two separate assemblies, each with all four relevant
  pages.
- `page-23.pdf` retains three objects, including one TV console across its
  repeated views.
- Kitchen remains one object with all 39 related pages.
- Metal retains accepted object-boundary and source-code behavior.

If the isolated correspondence stage produces a false partition or regresses a
protected benchmark, revert only this experiment to `e8480a1` behavior.
