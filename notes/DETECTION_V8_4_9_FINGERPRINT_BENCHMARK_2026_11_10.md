# Detection V8.4.9. Replay of numeric evidence and View links

[verified] Coordinate OCR restored a missing source of comparison evidence on
Adda. On the frozen 28 pairs it exposed three cross-sheet pairs above the
current support threshold, all within the correct assemblies. One of the
three numerical matches compares two different physical dimensions. The
active grouping path still reads the previous evidence. This experiment
does not establish a quality or latency gain in live grouping.

## Controls

- Runtime `a1f1562`. Fixed PDFs, Mistral/MyPDF facts, Discovery results, View
  rectangles, View IDs, and existing semantic facts. Each baseline inventory
  and every final score reproduced the saved runtime exactly.
- Locked View witnesses were Adda `run_b9a002a9ef2341208efeb6e1a7837edf`,
  Lev 1 `run_87a093dde8184a3ab4c054f77911c60b`,
  Lev 2 `run_fbc2e7606823415abfac8be7a2e217dd`, and HSL 07
  `run_49a6d5bd14fa4e0e971a763af919470c`. HSL used the new coordinate
  readings from all eleven pages. PDF hashes and page frames matched the
  baseline. Only the numeric readings were replaced on HSL.
- Ground truth for Adda was the two owner-accepted sets `01/04/06/08` and
  `02/03/05/07`. Both Lev controls were one assembly. HSL ownership has no
  accepted reference for this run, so its pair counts are score counts.
  Page 23 was outside this numeric grouping comparison.
- Compared the production Fingerprint against standard facts plus the new
  View-owned readings. Used the same final Candidate Q for the primary
  comparison. Ran a separate replay of Q on frozen Fusion candidate boxes
  and another run with all possible cross-sheet pairs to check opportunity.
  Same-sheet scoring stayed exhaustive for every document.

## Production scorer on fixed Views

`25` is the dimension-support threshold. A support edge carries evidence
into the later graph policy. For the Ada route the owner remains Sonnet
Membership. Timing is the local median of nine runs of final scoring,
excluding OCR, PDF rendering, provider calls and object packaging.

| File | Normalized occurrences before → after | Views with sizes | Same-sheet pairs | Pairs with support before → after | Final scorer before → after |
| --- | ---: | ---: | ---: | ---: | ---: |
| Adda | 0 → 33 | 0 → 6 of 8 | 4 | 0 → 3, all cross-sheet | 0.08 → 0.59 ms |
| Lev 1 | 14 → 14 | 4 of 6 | 15 | 1 → 1 | 0.14 → 0.14 ms |
| Lev 2 | 15 → 15 | 3 of 4 | 6 | 1 → 1 | 0.11 → 0.11 ms |
| HSL 07 | 700 → 731 | 32 of 32 | 49 | 74 → 76, one same-sheet and one cross-sheet added | 53.1 → 57.4 ms |

All seven Lev 1 and nine Lev 2 local readings coalesced with existing
occurrences. They add source confirmation. HSL retained 192 of 237 OCR
readings on the fixed Views. 159 normalized occurrences combine new OCR and
existing source facts. The HSL additions at 25 had no independent accepted
semantic facts. Replaying the initial merge compiler with the same semantic
facts gave the same two HSL merges. The quality of HSL package boundaries
remains open.

Adda had 12 true and 12 false inter-sheet pairs. The old scorer found zero
dimension-support edges. The new one covered 3/12 true pairs at 25 and
0/12 false pairs at 25. Two of the three already had accepted semantic
facts. The one additional pair without a semantic fact was `06–08`, with
a size coincidence described below. Adda still evaluated all 28 pairs.

Removing raw x/y boxes after View ownership and occurrence compilation left
every pair score identical in all four files. The scorer reads value,
frequency, magnitude and multiplicity. It uses coordinate-derived
ambiguity slots to avoid double counting. Removing those slots changed 16
HSL scores, raising one extra pair above 25 and two extra pairs above 85.
This separates the actual benefit of location from the effect of simply
recovering more numbers.

## Geometry witnesses

Reused the protected Estimation PDF vector binder in a separate offline
experiment. This binds numeric labels to printed dimension lines and
their endpoints. It records x/y in the page projection. Shared physical
width, height, or depth still requires interpreting the projections.
The experimental binder proposed 33 bindings on Adda, seven on Lev 1 and
seven of nine local readings on Lev 2. On HSL P04/P08 it proposed zero
bindings with this arrow-tip contract. HSL uses different dimension marks,
visible on the P08 crop. The unoptimized HSL probe also took 43 seconds
for the local-reading arm, so it gives no usable runtime gain.

| Adda pair | Score | Source-grounded assessment |
| --- | ---: | --- |
| 03–07 | 61.25 | `3096 ≈ 3094` refers to the main horizontal run in front and plan Views. |
| 04–06 | 91.875 | Three vertical datums `515/665/1112` match on the two Views. The repeated exact pattern is the strongest new support. |
| 06–08 | 42.875 | The Views belong together, but `1995` is elevation height and `2000` is the length of a return in plan. Both lines point along page y. Their numerical proximity does not establish the same physical dimension. |
| 03–06 | 24.5 | Different assemblies. `1026` is one bay's horizontal width and `1025` is a vertical datum on the other drawing. It falls just below the current support threshold. |

The highlighted source crops show the `1995/2000` mismatch and the HSL unit
triggers. Raw label positions support this verification. They do not by
themselves supply a world axis or a projection transform.

## Candidate Q and units

Adda retained 28 pairs and gained one strong cross-sheet candidate at 85.
Its Q formatting changed from 2,095 to 2,099 characters. The number of
scheduled comparisons did not decrease. Both Lev queues and their
formatted lengths were unchanged.

On HSL, unrestricted unit inference changed cm to mm. Source crops verify
that `77131` and `01777` came from Hebrew text and `681` came from a
rotated `189`. The new values crossed the heuristic's 600 threshold.
Unrestricted Q increased from 304 to 472 pairs, reduced strong cross-sheet
candidates from 8 to 1, and increased Q text from 20,682 to 31,595
characters. Holding the baseline cm unit gave 304 pairs, 8 strong
cross-sheet candidates and 20,684 characters. Median candidate-stage
CPU was 82 ms baseline, 194 ms with the unit flip and 90 ms with the
unit preserved.

The current application adds no model calls or model tokens for these
readings. They enter only the post-Membership audit. The visible cost
remains local OCR. The controlled fast-provider HSL replay spent 6.24 s
waiting after standard OCR for all eleven sheets. The live slow-provider
HSL control had essentially no tail wait.

## Sonnet reasoning probe

Same six Adda cross-sheet pairs, same six locked crops, same Sonnet 4.6
prompt and schema, and two calls per arm. The inputs provided no expected
group labels. The visual arm could still read numbers visible in the
images. The three other arms varied only the structured numerical hints.
The pair set was chosen after the deterministic replay to expose specific
positive, negative and ambiguous cases. This is a diagnostic sample.

| Structured hints | Correct decisions out of 12 across repeats | Input tokens per call | Wall time, observed |
| --- | ---: | ---: | ---: |
| None, identical crops | 6 | 4,065 | 25.7–30.6 s |
| Values only | 4 | 4,179 | 25.4–27.2 s |
| Same values plus OCR centres | 9 | 4,441 | 24.1–27.6 s |
| Same values plus centres and printed line geometry | 7 | 5,102 | 24.7–29.1 s |

Centres improved object-pair decisions in this small probe. Both
centre-only runs still gave the wrong physical explanation for
`1995/2000`, calling both heights. One of two line-geometry runs
wrongly accepted the `1026/1025` pair even with different printed
axes provided. These outputs show why a correct same-object decision
cannot stand in for a validated dimension witness. The sample does not
establish a latency advantage or general reasoning improvement. Calls
were interleaved and concurrent. Earlier full-context Adda Membership
with numerical injection returned six groups instead of two.

Eight standalone benchmark calls cost $0.214707 at configured rates. The
diagnostic left the product prompt, Q, merge policy and locked Views intact. The production path still incurs zero extra LLM calls and
tokens for the coordinate audit.

## Replay artifacts and open decision

Private local folder `/private/tmp/detection-fingerprint-ab.IHBkJi` contains
the replay scripts, pair-level ledgers, raw model response IDs, and checked
source crops. Source PDF and OCR/result hashes are recorded in `result.json`.

| Artifact | SHA-256 |
| --- | --- |
| `result.json` | `36cb9e1a4487e98c038e89c9da5fe8fb7e97e31c2964f96702cace648ffe01d3` |
| `units_merge.json` | `876b1c58a9ee3e4c821badd87860d41c467f2c900c6022328ea5855f7e254e2b` |
| `vector.json` | `832073f51c7c76c394b9aedbd685165dc2fbb9cc35238dfe5b47cd1a75149f15` |
| `adda-different-dimension-roles.png` | `3e9d0654d594450819b72b6bde8c6779c673b1dc40184a0b622cc3c93e51f46f` |
| `hsl-unit-trigger-crops.png` | `069be2147e693863124f7d868b8fc405935ec57f957eec7bfcc47e1a125220b7` |

Keep the current audit placement. The next isolated test can preserve the
known unit and admit a cross-sheet numeric witness only when its printed
line and dimension role agree across the two projections. Same-sheet
comparisons stay exhaustive. Benchmark that rule on additional labelled
cross-sheet pairs before considering any production effect.
