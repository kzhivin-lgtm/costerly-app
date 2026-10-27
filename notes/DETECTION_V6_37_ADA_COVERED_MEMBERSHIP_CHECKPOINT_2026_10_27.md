# Detection V6.37 Ada covered-membership checkpoint

Date: 2026-10-27

Status: protected live checkpoint for the existing Ada route. It accepts the Ada and Lev membership results below. It is not a universal Detection acceptance, a recalibration of the V6.29 router threshold, or a replacement for the protected ordinary HSL, Page23, or assembly-set checkpoints.

Implementation commit: `d5a306c`, `fix(detection-v6.37): preserve covered Ada hypotheses`.

## Contract

V6.37 retains exactly the established V6.34 mixed-model Ada shape:

1. Mistral remains the graphic-anchor and bbox authority.
2. Haiku performs Discovery.
3. One Sonnet Membership Review emits non-overlapping multi-View hypotheses.
4. No V6.10 pairwise/reconciliation call runs on this route.

The V6.37 runtime keeps a multi-View hypothesis only when its accepted, pair-local visual facts cover every declared View and every cited View belongs to that exact hypothesis. A group of more than two Views needs at least two distinct local pairs. Title blocks, shared project/order identifiers, authors, sheet sequence, and a common fabrication package remain context only and can never become merge evidence.

This deliberately does not demand a connected pairwise tree. Complementary plan, elevation, section, and isometric Views can establish one commercial object without any truthful pairwise bridge between every pair of sub-views. The runtime stores those local facts as supporting evidence and publishes the validated group component without inventing root-to-member edges.

## Production verification

### Adda.pdf

Both V6.37 runs selected `ada_boundary_risk_sparse_native_graphics`, retained eight Mistral graphic Views and published the expected two commercial components:

- Counter: `view-002`, `view-003`, `view-005`, `view-007`.
- L-shaped display: `view-001`, `view-004`, `view-006`, `view-008`.

| Run | Detection time | Detection cost | Initial cycle | Known OCR + Detection + Naming cost |
| --- | ---: | ---: | ---: | ---: |
| `run_3cbb2411236443448605580061e12554` | 43.863 s | $0.072353 | 49.202 s | $0.099715 |
| `run_4e47c1226af946698779203ca31ff705` | 42.793 s | $0.071588 | 47.027 s | $0.098950 |

Each run accepted two non-overlapping hypotheses. Every View was covered by accepted local evidence, with no rejected semantic fact or coverage failure.

### Lev_1.pdf

Both V6.37 runs selected `ada_boundary_risk_single_page_mistral_graphics`, retained six Mistral Views, and published one six-View commercial component: `view-001` through `view-006`.

| Run | Detection time | Detection cost | Initial cycle | Known OCR + Detection + Naming cost |
| --- | ---: | ---: | ---: | ---: |
| `run_f8cd8bed9c6f4bd189552d38767cc5fb` | 35.796 s | $0.044534 | 41.720 s | $0.053240 |
| `run_4f4493875f584866baad1d7087d0cb9a` | 34.833 s | $0.043409 | 39.366 s | $0.052115 |

The four accepted local facts cover all six Views. The V6.36 validator failure caused by the provider using `strength: direct` for a visual fact did not recur under the V6.37 contract, which requires `standard` for non-document visual evidence and defensively canonicalizes the old provider wording.

## Verification

- `git diff --check` passed.
- `py_compile agents/anthropic_adapter.py agents/schemas/detection_registry_schema.py` passed.
- Targeted graph and timing suite passed: `109 passed`.
- Four independent live runs passed the specified Ada and Lev gates above.

## Protected boundaries and limitations

- The only changed runtime path is the already-selected Ada route. Ordinary, Page23, source-degraded and assembly-set paths retain their existing model and membership contracts.
- This checkpoint does not establish the V6.29 sparse-native-graphics threshold as a calibrated universal classifier. It confirms only that its current Adda signature remains on Ada.
- Visual grouping is now a bounded Sonnet semantic decision with deterministic local-evidence coverage validation. It is not a claim that all future documents may merge non-connected Views.
- No change to object quantity, physical-page Evidence, View bbox ownership, Document Identity, Naming, Preview selection, or Estimation handoff is accepted by this checkpoint.

## Next safe work

Keep V6.37 fixed while validating a document outside these two Ada benchmarks. Do not reopen the Ada evidence contract merely to optimize cost or reduce the number of facts. Any route expansion requires a new benchmark and separate approval.
