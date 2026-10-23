# Detection V5.21 source-degraded boundary ledger checkpoint

Date: 2026-10-24  
Status: protected continuation checkpoint. It is not accepted as a universal
Island-segmentation solution.  
Production commit: `d9b1fa6`.

## Scope

V5.21 changes only the source-degraded visual-only route. Ordinary V5 retains
Fusion, deterministic Dimension Fingerprints, Weighted Similarity, semantic
validation, graph construction and Detection Validation.

1. The route keeps two Haiku calls over full rendered pages. Static Discovery
   crops remain disabled.
2. Discovery creates provisional visual groups. Same-page pairs whose
   `core_bbox` values overlap become boundary-review candidates, never
   automatic merges.
3. The full-page Registry must return one decision for every candidate:
   `physically_continuous` with named joined geometry, or
   `physically_separate` with `visible_background_gap`,
   `separate_closed_contour`, or `independent_projection`.
4. Only attested continuous pairs are unioned before role assignment and object
   partitioning. Roles and commercial partitions then operate on the effective
   representation, not a discarded continuous fragment.
5. The persisted Detection ledger contains source capability, raw Discovery
   groups, boundary candidates, boundary decisions, continuity consolidation,
   roles, partitions, positive edges, provider timings and cost.

## Verified production evidence

Page 23 run `run_caed454c5f6b49479d300f0b532c85c4` executed the V5.21 prompt
`detection_v5_21_source_degraded_required_boundary_ledger_v1`.

- Source capability was degraded: 14 coordinate facts, zero dimension-like
  facts and one localized position, so the visual-only route was appropriate.
- Discovery produced five groups: `V1` shelving depiction, `V2` door depiction,
  `V3` angled panel, and `V4/V5` console projections.
- V5.21 generated the required `V1/V3` candidate and Registry returned an
  explicit `physically_separate / independent_projection` decision.
- Final packages were `V1`, `V2`, and `V4+V5`. The resulting product categories
  were shelving, sliding doors and TV console. Naming is not evidence for the
  package boundaries.
- `V3` remained `component_detail` and was excluded from the first package.
- Provider time was 24.485 seconds, Detection cost was `$0.016145`, with 6,980
  input and 1,833 output tokens.
- Local verification before deploy: `128 passed`, `py_compile` and
  `git diff --check`.

## Known limitation

The V5.21 ledger made the split auditable but did not prove it true. Registry's
`V1/V3` observation cites different dimensions and an asserted absence of shared
geometry, rather than a visible blank gap, separate closed contour or identifiable
independent projection. The current validator confirms exhaustive, well-formed
claims, not pixel-level truth. Therefore V5.21 is a checkpoint for observation
and controlled continuation, not a resolved continuous-contour defect.

## Protected decision and next work

Do not add further prompt wording or enum variants merely to make the model
state a more plausible separation rationale. Do not restore static crops or
treat bbox overlap as a merge. The next approved diagnostic must introduce
independent visual evidence of physical continuity, or reject that approach
after a bounded discriminator test. No further work starts from this checkpoint
until the owner resumes the evaluation.
