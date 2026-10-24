# Detection V5.37 native-XObject embedding witness checkpoint

Date: 2026-10-24
Status: protected production checkpoint for the narrow native-XObject route. It
is not an accepted universal Detection solution.
Production commit: `8dbf34e`.

## Scope

V5.37 retains V5.35's source-authored PDF image-XObject envelopes as immutable
Visual Islands. It changes only how the second Haiku pairwise audit must account
for a DINOv2 visual similarity result on this route.

1. A pair is strong only when both views are on one page, are mutual top-1,
   cosine is at least `0.80`, and its lowest margin to the next candidate is at
   least `0.10`. A two-XObject page has no comparison margin and remains
   ranking-only.
2. The provider must return `embedding_reference` and `embedding_assessment`
   for every technical pair. A strong pair must cite its exact reference.
3. A strong `same_object` decision counts the embedding as one evidence item,
   but still needs a concrete pair-specific visual witness and two original
   `assembly_view` roles. Embedding never creates a graph edge alone.
4. A strong `different_object` decision is allowed only with explicit author
   distinction, incompatible visible dimensions, or physical separation of two
   finished products.
5. Ordinary V5, Fusion, Dimension Fingerprint, Weighted Similarity, semantic
   validation, graph construction and Detection Validation are unchanged.

## Verified production evidence

Six independent production Page23 runs completed with the V5.37 prompt
`detection_v5_37_native_graphic_embedding_witness_pairwise_audit_v1`:

`run_2d366104271c4b939efc598d942d4ebd`,
`run_5345cb45dfee48748a1066fd823fccae`,
`run_f762152691654dc6ad5741f62a2dbf73`,
`run_f12acd287eca4d8c8c06301ad6be11c1`,
`run_ec97b66622a54502b971d74ac7020941`, and
`run_8e6da784db0d43d08ab2c7b14b021d23`.

- Every run found the same four source-authored XObject Islands: shelving,
  doors, and two TV-console representations.
- Every run emitted the same strong V3/V4 pair:
  `native_mutual_top1:0.8278`, margin `0.144397`, assessment
  `supports_same_object`.
- Every run admitted only the V3/V4 `alternate_projection` edge, with visible
  finished-envelope and internal-layout witnesses. No V1 edge was admitted.
- Every run published three packages: shelving, the joined TV console and the
  standalone door system. This is the expected Page23 boundary result.
- Each run used 5,586 input and 1,218 output tokens at `$0.011676`. End-to-end
  audit time ranged from `27.679` to `36.975` seconds, mean `31.444` seconds.

## Known limitations

1. The provider repeatedly calls the door system `component_detail` of V4 and
   labels the final standalone object `Wall panel system`. Runtime correctly
   rejects the unproven V2/V4 edge and promotes V2 back to an assembly, so the
   object boundary is correct but that reasoning and naming are not.
2. Persisted File Review evidence anchors remain empty on this visual-only
   route, despite the complete raw pairwise audit. This is a traceability issue,
   not an identity failure.
3. Six repetitions establish Page23 repeatability only. A second eligible
   native-XObject drawing must pass before this evidence rule can be considered
   broadly reliable.

## Protected continuation

Do not weaken the mutual-rank, margin, exact-reference or visible-witness
requirements to improve a single document. Do not extend V5.37 to ordinary V5
or source-degraded files without native XObject envelopes. The next approved
task is deployment efficiency only: build the pinned DINO artifact in a layer
whose cache key depends on the model revision, not on every application source
change.
