# Detection V5.10.3 two-call experimental checkpoint

Date: 2026-10-23
Status: protected experimental checkpoint, not accepted and not deployed
Base: V5.6.1 `5de4cf4`

## Decision

The Registry remains a two-call Haiku pipeline at temperature zero. Returning
to one call is out of scope: discovery and membership were too coupled to make
their failure modes observable or repairable.

## Contract

1. MyPDF extraction and Mistral OCR run independently, then Evidence Fusion
   emits source-traceable page evidence in one coordinate system.
2. Candidate Regions and the preliminary Dimension queue are deterministic
   recall aids. They do not create Islands, packages or identity decisions.
3. Discovery receives full pages, Fusion and Candidate Regions. It returns the
   complete Visual-Island inventory, classifications and exceptions only.
4. Review receives that immutable inventory, full-page Island overlays, crops
   and View-local evidence. It returns non-singleton multi-View hypotheses.
5. Runtime canonicalises only an exact known display wrapper, for example
   `[SF00202]` to `SF00202`, before source validation and records each change.
   Unknown IDs are still rejected.
6. Runtime validates positive typed semantic facts, recalculates Dimension
   Fingerprints and Weighted Similarity, compiles the graph and creates object
   packages. It does not run a new all-to-all merge pass.
7. Detection Validation guards ownership, source bboxes, graph/package links
   and persistence before File Review.

## Verification

- Focused suite: `135 passed`, plus `py_compile` and `git diff --check`.
- Page23 `v590-coordinate-page23-02`: 4 Object Islands and 3 packages,
  including the two-view TV console. Coordinate transformation is verified.
- HSL `v5103-hsl-01`: P03=3, P04=6, P05=3, P06=3, P07=4, P08=4, P09=3,
  P10=3 Object Islands; P11 has 2 Object and 2 Context Islands. Review has
  63 accepted semantic facts, no accepted bracketed IDs and no
  `unknown_source_fact` rejection. Wall time 165.346 seconds; Anthropic cost
  $0.206013.

## Protected interpretation

- P04 may legitimately contain one to three objects. Its current one-package
  result is neither a pass nor a failure by itself.
- Package counts do not establish object-boundary correctness. Inspect View
  membership and grounded evidence.
- This checkpoint does not claim stable Adda or Metal behavior and is not a
  production candidate.

## Known defect and next task

HSL P02's generic floor plan is wrongly published as `object_evidence` and a
singleton package. Registry declared its `representation_kind` as
`object_evidence`, so the existing generic-plan safeguard could not fire. The
next change must repair this classification-contract breach in isolation, then
run HSL followed by Page23. Do not change P04 policy, semantic scoring,
Dimension Similarity or merge rules as part of that repair.
