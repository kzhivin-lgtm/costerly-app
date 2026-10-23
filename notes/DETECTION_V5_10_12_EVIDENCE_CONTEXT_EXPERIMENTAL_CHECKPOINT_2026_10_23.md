# Detection V5.10.12 evidence and context experimental checkpoint

Date: 2026-10-23  
Status: protected experimental evaluation baseline, not accepted and not deployed  
Base: V5.10.3 two-call checkpoint `67d2a84`

## Scope

V5.10.12 preserves the two-call temperature-zero Registry: Discovery creates
the Island inventory and classification, Review receives immutable Island
overlays and crops, then returns only multi-View membership hypotheses.
Deterministic runtime retains Fusion, Dimension Fingerprints, Weighted
Similarity, semantic validation, graph construction, package ownership and
Detection Validation.

## Protected repairs

1. Final same-page Object Islands are always compared by the deterministic
   Dimension Engine. Candidate Q remains a bounded cross-page recall queue and
   cannot suppress a final same-page comparison.
2. Generic architectural floor plans are demoted to `document_context` from
   their concrete visual description when the Registry mislabels the
   representation kind.
3. Discovery returns compact exact-once page coverage. A page cannot disappear
   because it lacks a Candidate Region.
4. Every Island carries a tight `core_bbox` and an evidence `bbox`. An
   otherwise-unowned numeric source fact of at least 20 may enter one bounded
   evidence halo only when exactly one Island can own it. Revision-row numbers
   and overlapping claims remain excluded.
5. If Mistral exposes no graphic region, Fusion produces broad source-text
   clusters only as Candidate Region recall hints. They cannot create Islands,
   decide identity or override the full-page Registry inspection.
6. OCR uses Mistral native coordinate blocks. The rejected custom per-item
   annotation schema remains disabled because it caused provider timeouts.

## Verified local evidence

- Focused changed-path suite: `125 passed in 2.40s`.
- `py_compile` for the altered Detection modules and `git diff --check` pass.
- HSL run `v51012-hsl-01`: P02 is Document Context, P03.V1-V3 and P09.V1-V3
  each form one package, and P09 has five accounted Candidate Regions including
  a non-Island revision table. It produced 32 Visual Islands and 10 packages
  in 124.481 seconds at `$0.208045`.
- The HSL result is the evaluation-wheel baseline requested by the owner. It
  does not claim final cross-page commercial-boundary acceptance.

## Explicit limitations

- Page23 is not accepted. Its PDF text layer has no authored drawing dimensions
  and the current Mistral page response provides an image block without interior
  text, literals or local OCR coordinates. Its Dimension graph therefore has
  no evidence by design.
- Page23 `v51012-page23-01` creates five Object Islands, splitting a continuous
  shelving depiction and its diagonal extension, then Review re-merges them.
  That is an Island-boundary defect, not a Dimension or Fusion ownership loss.
- V5.10.13 tested a 200-dpi shelf crop and a stronger prompt-only water rule.
  Mistral still supplied zero facts and Discovery still emitted five Islands.
  The variation is rejected and not part of this checkpoint.

## Next experiment

V5.11 is an isolated, per-page visual-only router experiment for Page23. It
must not alter the V5.10.12 route for evidence-bearing pages. The first gate is
three visually grounded object candidates, with no invented numeric evidence.
Only then continue the evaluation wheel with Metal and Adda.
