# Detection research round 1, 2026-11-10

[verified] The frozen V8.4.9 experiments did not establish a reason to
replace the OCR recognizer or the grouping compiler. The labelled Adda
misses are localized to finding a readable crop. The five-file reference
pack separates location, role, and group membership for subsequent tests.

Base is the local V8.4.9 tag
`detection-v8.4.9-post-cleanup-checkpoint-2026-11-10`, runtime `3f3f157`.
This round uses saved inputs and local engines with zero provider calls.
Q, routing and automatic singleton attachment are deferred in the TODO.

Private reproducibility bundle:
`/Users/qb/Documents/ChatGPT/Costerly/output/detection-research-2026-11-10`.
It contains the scripts, raw comparisons, reference annotations, two saved
Adda failure inputs, and per-file SHA-256 checksums. The original drawing
and replay inputs remain in the existing private checkpoint archive.
All 20 bundled file hashes passed. A second run reproduced the numeric
labels and their boxes, partitions and reference pack exactly, excluding
CPU timing. The HSL P04 tile arm took 10.23 and 10.70 seconds.

## eDOCr2 and location-first OCR

Sources: [eDOCr2 paper](https://www.mdpi.com/2075-1702/13/3/254) and
[upstream code and model](https://github.com/javvi51/edocr2/releases/tag/v1.0.0).
The paper's dimension workflow uses overlapping text-detection patches,
orientation correction and a dedicated recognizer. The experiment
isolates the two stages. The tiled arm keeps the current pinned PP-OCRv6
tiny detector and recognizer, and reads padded, overlapping tiles of the
frozen Views. The fixed-crop arm compares both recognizers on the same
prelocated 600-DPI source crops. It supplies orientation from the known
native span when available and corrects it for PDF page rotation.

| Control | Current full-page reading | Tiled with current reader | Full page / tiles, local seconds |
| --- | ---: | ---: | ---: |
| Adda P02–P04 | 25/27 | 25/27 | 2.29 / 1.17 total |
| HSL 07 P04 | 12/157 | 82/157 | 0.80 / 10.23 |
| HSL 07 P08 | 13/100 | 18/100 | 1.34 / 4.58 |

A match requires exact text and at least 60% intersection over the smaller
label box. Adda's controls come from the prior per-page 27-label benchmark.
For the 25 available controls the reference positions use the frozen
reading rectangles. The two P03 misses have manually located source
rectangles. HSL references are standalone numeric spans from the native PDF
layer already present in the frozen View dimension inventory. Those HSL
hits measure redundant OCR coverage of a known source, not net new
dimensions or document-wide precision. HSL P08's saved short-deadline run
had no local readings, so the full-page comparator is a fresh offline
read, with no provider deadline. Times are warm, serial CPU measurements
including tile extraction and encoding, not user-facing latency.

| Same prelocated crop set | PP-OCRv6 tiny | Official eDOCr2 recognizer |
| --- | ---: | ---: |
| Adda, 27 controls | 27/27 | 0/27 |
| HSL 07 P04 | 153/157 | 151/157 |
| HSL 07 P08 | 57/100 | 56/100 |

For Adda P03 the existing recognizer read both `458` and `2000` once
their source crops were supplied. The official v1.0.0 eDOCr2 recognizer
missed both. The thin-stroke enhancement arm also returned 0/27. A
follow-up diagnostic rescanned the whole lower strip of the right-hand
View at 200 and 600 DPI, with an additional 600-DPI arm that removed long
rules. None recovered either missing label. These tests isolate a
location/crop problem in the two measured cases. They do not validate an
automatic localizer. The comparison uses the upstream recognizer only.
An earlier recorded full eDOCr2 detector/recognizer run on two Adda P03
regions took 244.735 seconds and returned one of eleven controls. The
previous and current trials have different input windows.

Disposition: reject an eDOCr2 recognizer replacement and a general
second tiled pass on this evidence. A later localization experiment should
start with the two verified misses, require automatically selected
positions and include false readings and added latency in acceptance.

## DocLayNet and PubTables-1M reference pack

Use [DocLayNet](https://arxiv.org/abs/2206.01062) as a reference for
separate labelled region boxes and [PubTables-1M](https://arxiv.org/abs/2110.00061)
for evaluating detection, functional role and structure independently.
`region-role-membership-references.json` contains 54 frozen regions
across Adda, Lev 1, Lev 2, Page 23 and HSL 07. It stores normalized core
and evidence rectangles, expected role where checked, expected commercial
group where accepted, and evidence owner where separately established.

All four protected membership controls reproduce the reference
partitions. Coarse role classification matches 22/23 reviewed examples.
The exception is HSL 07 N57, PDF P04. `P04.V5` is the dimension chain
directly below `P04.V4`, but the saved output classified it as a
technical detail and made it its own singleton package. The visual
evidence owner is the view directly above it. That is a role and ownership
witness, not acceptance of the other N57 groups.

[verified] The exact HSL source is shared by the accepted V6.25 run
`run_2dceafe62d3440668ca56b6b74101cc8` and the V8.4.9 replay.
V6.25 retained the same strip as a View, but linked it to P04.V4 within
one N57 object. The separate-object outcome already occurs in the saved
Haiku 5.5 run `run_e508dea053ae472d9038a0b8047c8ed9`, before the new
coordinate OCR audit. In that run and the final V8.4.9 run, all seven
P04 Views are singleton components. This establishes the output regression
between these witnesses. It does not isolate the first affected version
or the cause of the broader page split.

These rectangles are frozen regression references, not an independently
redrawn, exhaustive region inventory. HSL's full grouping remains
unlabelled. A separate unseen drawing is required before using this
fixture to claim general quality.

## Higher-Order Multicut diagnostic

The [Higher-Order Multicuts paper](https://www.keuper-labs.org/research/2022-higher-order-multicuts-for-geometric-model-fitting-and-motion-segmentation/)
motivates scoring groups as well as pairs. The prototype enumerates all
partitions for up to eight Views. The two arms share the same pair
evidence and explicit conflicting pairs. The higher-order arm also uses
a group cost for each saved hypothesis that covers every member with
typed pair evidence and contains no explicit conflict. It is a small
experimental objective, not a port of the paper's optimizer.

| Witness | Pair-only partition | Pair and group costs |
| --- | --- | --- |
| Accepted Adda evidence | Four split pairs | Both exact four-View groups |
| Lev 1, Lev 2, Page 23 | All exact | All exact |
| Two saved failed Adda hypotheses | False merge blocked, four groups | Same four groups, seven required same-object pairs still split |
| Synthetic weak bridge AB–BC–CD with AD conflict | AB and CD | AB and CD |
| Synthetic conflict known only for the full triple | One group | Triple separated |

The accepted Adda result depends on the already-correct saved Membership
hypotheses, which the current runtime already uses. In the two historical
failures, the same-page pair verdict blocks the false pair in both arms.
Removing the bad grouping still leaves the correct cross-page joins
unsupported. The synthetic triple supplies an explicit group conflict
solely to show what the higher-order objective can express.

Disposition: keep the prototype offline. Revisit it when there is a
labelled real case with group-level evidence that is absent from the pair
ledger. This comparison provides no measured improvement over the
current production grouping.
