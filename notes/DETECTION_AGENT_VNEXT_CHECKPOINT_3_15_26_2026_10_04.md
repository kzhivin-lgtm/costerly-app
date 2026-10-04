# 3.15.26 Detection Agent vNext checkpoint, 2026-10-04

Status: COMPLETED AND OWNER-ACCEPTED for deferred File Review publication,
isolated previews, and shared-track door-system quantity. External envelope
dimensions are deliberately deferred and are not a Detection critical-path
requirement. Estimation evidence quality remains open work.

## Checkpoints

- Code commit: `43933e5 fix: stabilize deferred review artifacts`
- Git tag: `checkpoint-2026-10-04-deferred-review-artifacts`
- Previous independent File Review handoff checkpoint: `5c322bf`

## Accepted production outcome

The owner accepted the production Page 23 result after confirming that:

- all three detected commercial objects received isolated previews;
- deferred Naming published the saved object names into File Review;
- the two leaves on one continuous track appeared as one Sliding door system
  with quantity `1`.

The accepted production evidence run is
`run_a341ead8c4724e9d8b0b95e238b39b2f`. Its Preview worker persisted three
artifacts with no skips.

## Repairs in this checkpoint

- Detection may return a valid preview bbox as page fractions despite the OCR
  pixel-coordinate contract. Fractional `0..1` boxes are now expanded to the
  OCR page dimensions before cropping and before saving `preview_bbox` back to
  the detected-object evidence.
- File Review publishes deferred Naming and Preview from their durable terminal
  usage events, rather than relying only on in-memory futures. A terminal
  partial or failed Preview stops the spinner after reloading any saved refs.
- A door registry that describes leaves on one continuous/shared track cannot
  retain a quantity greater than one. This applies to the commercial door
  system, not to its leaf count.

## Detection to Estimation evidence state

For the accepted Page 23 run, every object has:

- one isolated preview ref;
- physical page `1` as `identity`, `overall_dimensions`, and `construction`;
- no OCR text anchor, because the OCR result exposes only page headers and
  footer rather than the drawing dimensions.

Estimation will receive the isolated preview and a private full-page artifact.
The full page is still required as construction evidence, but it contains all
three products. Therefore the preview is the current object-isolation boundary;
there is not yet an object-local construction crop or region artifact.

No `rfq_estimation_object_inputs` row exists for the accepted run yet. This
checkpoint verifies the prepared handoff, not a completed Estimation result.

## Explicit non-acceptance boundaries

- External dimensions are not accepted. The Page 23 door record still carries
  leaf width `950` while the evidence shows track span `4130`; the console
  record carries `1760` rather than its full `3610` span.
- Detection external dimensions are optional File Review context only. They
  must never be treated as authoritative Estimation facts or block Estimation.
- When an envelope is not directly and unambiguously evidenced, Detection must
  leave it unknown rather than infer it from components, pages, projections or
  visual proportions.
- This checkpoint does not alter evidence-page selection, Estimation material
  calculation, labor, pricing, routing, object-card layout, or the 120 ms
  Processing to File Review transition handshake.

## Verification

- Focused regression suite: 70 passed.
- Full suite: 916 passed, 25 pre-existing deprecation warnings.
- `git diff --check` passed.
- Local real Page 23 run through OCR and Haiku: three objects, one shared-track
  door system with quantity `1`, and three non-empty preview crops.
- Production owner acceptance: three previews, deferred names, and door-system
  quantity confirmed.

## Protected repository state

The pre-existing untracked `.streamlit/`,
`db/sql/3_15_4_israel_global_catalog_v1_parts/`, and `tmp/` paths remain outside
the checkpoint.

## 2026-10-04 owner decision: defer external envelopes

The owner and implementation review concluded that external envelopes do not
provide enough information to calculate cabinet parts, material area, hardware
or fabrication work. Incorrect envelopes are more harmful than absent values.

Experiments with isolated visual crops, expanded context, annotated page
regions, dimension-chain maps and object-scoped OCR were not retained. They
could not reliably associate all projections of one object with its external
chains on Page 23. Object-scoped OCR did recover some local dimension text, but
the accepted object preview bounds did not always cover every relevant view.
No experiment modified the accepted production code or this checkpoint's
preview, Naming, or shared-track quantity behavior.

Estimation v2 may proceed without overall dimensions when object-scoped parts,
materials and operation drivers are evidenced. Detection dimensions remain
locator hints only and are not trusted fabrication facts. If evidence is
insufficient, Estimation must return `review_required`, not derive a bill of
materials from an uncertain envelope.

## Next authorized direction

Prioritize an object-scoped evidence pack for Estimation and test the kitchen
with external dimensions omitted. Evidence must link the kitchen's overview,
assembly views and component drawings to one locked commercial object without
creating new objects from its details.
