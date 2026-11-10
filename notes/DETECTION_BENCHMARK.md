# Detection Agent benchmark

The V8.4.9 production-path release replay and private full checkpoint are
indexed by `notes/DETECTION_V8_4_9_PRODUCTION_CHECKPOINT_2026_11_10.md`.

### Production HSL Floor 06 witness

Run `run_24f9ed47537c41758129081ddda9e60a` completed with 62 Views and
52 objects, including 50 singleton objects. Haiku supplied two hypotheses
and both passed validation. The current production graph reproduced exactly
with frozen inputs. Recalculating only the unit as centimeters increased the
technical pairs scoring at least 85 from 3 to 49 and left all 52 groups
unchanged. The unit heuristic reacted to OCR noise and a sheet number.
The missing typed Membership evidence is a separate demonstrated limit.

### Haiku 5.5 Discovery batch admission

Floor 06 production run `run_e8b4f48d106942d3bde4e66e7387ccff` retained
12 Views in 7 groups after a single Discovery request used 182,933 input
tokens against a 101,703 estimate. Discovery marked P04 through P15 empty.
With the same PDF and saved production OCR, fresh Detection run
`run_b9053221388d49f0abb667aca901bc71` measured 182,933 tokens before sending
Discovery and planned batches for P01–P07, P08–P14, and P15. It retained 56
Views across all 13 technical sheets (P03–P15) in 25 groups. The first check
encountered a response without text. The repeat completed the three batches.
Floor 07 measured 129,536 tokens in its archived request and stayed
single-pass. Its fixed-input replay retained 33 Views in the accepted 10
groups. Fresh production Floor 06 Upload run
`run_6f5b804b71a945b0936ef731a11bb959` used two Discovery batches and retained
62 Views across all 13 technical sheets. It returned 32 groups, including
19 singletons. The fixed-input merge replay reproduced those exact groups.
Using centimeters with the same Views, Q, and model evidence produced 22
groups, a diagnostic result whose object boundaries require verification.

### V8.4.11 Discovery coverage and complete JSON

The Floor 06 production incident retained only a presentation render on P05
and returned empty coverage for P06 and P07 after a truncated Discovery
batch was retried. Ordinary Haiku independently reinspects pages with
missing technical coverage and conflicting source candidates before
Membership. Context already covering the source candidates stays excluded.
Recovery uses bounded groups of full pages and replaces a page only when
the validated response adds technical views. The saved incident selects
P03 through P07.

The Floor 07 incident filled the 12,288-token response and stopped inside
`classification_reason`. Its input was smaller than earlier complete runs.
In a controlled live comparison at the same 12,288-token ceiling, adaptive
thinking used the entire output budget and left invalid JSON after 61.160 s.
With thinking disabled, the same request returned valid JSON for all 11 pages
with 8,304 output tokens after 41.206 s. Single-pass ordinary Haiku
Discovery and targeted recovery explicitly disable adaptive thinking.
The first pass of multi-batch Discovery keeps its existing settings. The
original initial and retry budgets remain in place. Other stages and
routes retain their configuration.

With fresh OCR and a full upload cycle in an isolated persistence harness,
Floor 07 `run_5b7e5316ad9d403a8e09f545571b90d2` completed Discovery on the
first call with 8,124 output tokens. It retained 34 Views in 13 objects,
compared with 33 Views and 10 objects in the accepted lab benchmark.
P05 and P11 each split one additional component; Conflict Resolver admitted
an extra P07 title-block fragment. The cycle took 141.840 s before deferred
Naming, compared with 149.512 s in the lab. All 13 names persisted in the
isolated harness. The accepted 10-object partition still reproduces on
archived inputs and replies; fresh grouping remains a separate open issue.

Floor 06 `run_2c6161f20d9141dbb014af8000dce746` used fresh OCR and retained
all 13 technical sheets. P05, P06, and P07 retained 6, 3, and 7 Views and
published 1, 1, and 7 objects, respectively. The full upload cycle returned
62 Views and 23 objects, compared with 36 Views and 13 objects in the
production benchmark. It took 160.415 s before deferred Naming, compared
with 120.312 s. OCR was 23.582 s versus 12.953 s, and Detection was 136.552 s
versus 102.733 s. All 23 names persisted in the isolated harness. An
independent run on saved OCR retained all 13 technical sheets in 20 objects,
including a single P07 group. Neither fresh run of the release candidate
needed the new coverage recovery call. Regression tests exercise it on
render-only and empty technical sheets. Coverage is verified; grouping
quality on P07 and other split sheets remains open.

### V8.4.10 same-sheet view evidence

The Floor 06 production witness `run_b00f70fe709d4ed884bf5a15ff3abbbc`
contained two exact-score pairs that failed merge admission. P04.V3/V4
had a validated hypothesis citing both elevations and the common plan.
The compiler had projected its evidence only onto pairs involving the
hypothesis root. The repaired projection resolves both explicit View
citations and the owner of each cited OCR fact. In
`run_209af599b54444a39f7fef71658df622`, the same elevations were cited via
owned OCR facts, and the saved input now admits their link. P06.V1/V2
had an exact 4,970 mm total and three aligned
1,660 mm readings in both Views. The old ordered-span check discarded
consecutive equal values. The saved inputs admit both links under the
new rules. Negative controls cover uncited Views, renders, cross-sheet
pairs, mismatched geometry and repeated labels with reused source facts.

During full upload checks, a native PDF sheet identifier reached P03
through a dimension halo and changed the effective unit to millimeters.
The new inference policy reads units from the established evidence inside
the View envelope before halo expansion. Halo readings remain available
for Fingerprint. The accepted Floor 07 fixed-input partition stayed at
10 groups throughout.

The ordinary route now records an omitted render decision as an
unresolved abstention. Confirmed attachments still require a valid
positive model decision. A render-only component is excluded from the
published object list. The failure payload from the full Floor 06 check
omitted one known render; the replay produced one abstention and no edge.

Final V8.4.10 verification used the OCR captured during earlier fresh
uploads after Mistral timed out on the final fresh attempts. Live
Detection and Naming finished on both PDFs. Floor 06
`run_6bf38c6017d046ffa0c2906bbe1ddf97` retained 63 Views across all 13
technical sheets in 20 groups, joined the P04 elevations and all three
P06 Views, and saved all 20 names in the isolated verification store.
Floor 07 `run_adef5436b50646a38682dd0f75c40a1d` retained 33 Views in
11 groups and saved all 11 names. One P05 View remained separate.
On Floor 06 P04, Discovery mislabeled a render as technical and a plan
as a render. The render appeared as a singleton because the exclusion
policy sees the assigned role. Track the role defect independently.

### Haiku 5.5 dimension units and deferred Naming

The object-scale unit policy excludes renders from bare unit inference and
ignores implausible object spans. On fixed Floor 06 production evidence it
inferred centimeters, raised strong technical pairs from 3 to 45, and
produced 22 groups. Source inspection confirmed the seven joined P07 Views
describe the same assembly. With fresh model replies and the saved production
OCR, run `run_7e10798785754017bc8e00e829ddd554` retained 58 Views in 22 groups
on all 13 technical sheets and kept all seven P07 Views together. A separate
attempt retained 35 Views, missed two technical sheets, and reported a
recompile error. The accepted Floor 07 fixed-input partition stayed at 10.

Deferred Naming completed both prior locked production sets in a read-only
check. Floor 06 used 3,324 output tokens for 32 names. Floor 07 used its
bounded retry after reaching 3,072 tokens, then returned all 12 names.
The verified inputs were reconstructed from saved production records and
source imagery. No names were written during this check. Production run
`run_b00f70fe709d4ed884bf5a15ff3abbbc` used centimeters and two Discovery
batches, retained 62 Views on all 13 technical sheets, and produced 23 groups
with 11 singletons. Naming validated and wrote all 23 names in one call.

### Haiku 5.5 ordinary Membership recovery

The ordinary Upload path now uses the grouping logic from the accepted
`3a003a4` experiment. The product entry point reproduced all 10 accepted
groups and 33 Views from the fixed Floor 07 inputs. Membership and both
follow-up requests matched the archived requests byte for byte. The
Discovery comparison differed only in the company ID supplied by the
test. Adda, Lev 1, Lev 2, and both Page 23 branches matched the checkpoint.

Fresh regular runs completed with 11 groups on Floor 07
(`run_2ec20e59f8f74243b434d2ddff8a9d3c`) and 39 groups on Floor 06
(`run_d68bf1d980e046ddaab935e31d3df017`). Floor 07 had one additional
singleton on P04 compared with the accepted partition. Floor 06 technical
grouping remains open. Replay state and token counts are local to each
request. Supplementary reviews use fixed Views and same-sheet pairs.

## V8.4.9 local post-cleanup checkpoint, 2026-11-10

Fixed-input restored replay verified identical provider requests, View
geometry, membership and quantities before and after cleanup. Adda kept
two exact four-View groups. Lev 1 kept six Views in one object. Lev 2
kept four Views including its render in one kitchen. Page 23 used native
PDF anchors and returned three packages. HSL 07 ordinary Registry
reproduced the saved 30-object output. That count is a replay witness.
Visual fallback without native anchors also matched. Manifest:
`notes/evidence/detection-v8.4.9-post-cleanup-checkpoint.json`.

For the separate attachment work, the owner identified the sparse detail
at the lower left of HSL 07 P03. This is a whole-sheet context witness.
Its precise identity and assignment still require inspection. Pair this
with negative controls for an already-owned cross-sheet View and a real
independent small item on a dense sheet.

## V8.4.5 large batched assembly-set checkpoint, 2026-11-01

Status: owner-verified positive boundary witness for the narrow
`assembly_set + V6.41 batching` combination. `24-215. Кухня. СБ.pdf` had
previously completed after V8.4.4 but published 25 ordinary Membership
components because the V6.41 batch merge intentionally emitted an ordinary
scope. V8.4.5 (`4c9ff38`) runs one optional, fail-closed V6.11 scope
observation after all batches have produced a fixed Object Evidence inventory;
the established V6.26 compiler then has valid document-wide evidence without
changing Membership or Islands. The owner reran the document and confirmed one
published commercial object. No exact run ID, timing or cost was supplied for
that witness, so none is inferred. This does not accept Floor 06, Floor 07,
Page 23, Ada, or Cabineter by substitution. Full record:
`notes/DETECTION_V8_4_5_GLOBAL_BATCHED_ASSEMBLY_SCOPE_CHECKPOINT_2026_11_01.md`.

## V6.37 Ada covered-membership checkpoint, 2026-10-27

Status: protected live checkpoint for the existing Ada route only. Two Adda
runs retained eight Mistral Views and published the accepted two four-View
components, Counter `{V2,V3,V5,V7}` and L-shaped `{V1,V4,V6,V8}`. Two Lev
runs retained six Views and published one object. Adda Detection took
42.793-43.863 seconds at `$0.071588-$0.072353`; Lev took 34.833-35.796 seconds
at `$0.043409-$0.044534`. The route retains Mistral anchors, Haiku Discovery,
and one Sonnet Membership Review. Group membership requires pair-local visual
fact coverage of every View, but does not falsely require a pairwise tree among
complementary projections. Full record:
`notes/DETECTION_V6_37_ADA_COVERED_MEMBERSHIP_CHECKPOINT_2026_10_27.md`.

## V6.14 ordinary HSL cost and membership checkpoint, 2026-10-25

Status: protected live checkpoint for the ordinary HSL route, not universal
Detection acceptance. `run_e8006a40e1fe4c68846b59b44dacaf4c` selected
`ordinary_object_set` and Haiku, retained 32 object-evidence Islands in ten
proof-graph components, and completed without a V6.13 proposal retry. Its
Detection cost was `$0.151403` for 66.514 seconds, while the known Detection
plus Naming total was `$0.175261`. The page-2 floor plan was classified as
`document_context` and discarded before membership, not saved as a commercial
object. File Review names remain an independent deferred-Naming defect. Full
record: `notes/DETECTION_V6_14_ORDINARY_HSL_CHECKPOINT_2026_10_25.md`.

## V6.10 Adda combined Evidence Review checkpoint, 2026-10-25

Status: protected experimental result, not a universal acceptance. Source is
the private Adda drawing. V6.10 applies only to the bounded V6.7 Sonnet
Mistral-anchor route with two to ten object-evidence Islands. It leaves the
ordinary Haiku, Page23 and source-degraded paths unchanged.

Adda `run_c2ddd6be0c5b4add910d317382691d54` retained eight Mistral groups and
returned the expected two four-View commercial components: the L-shaped cabinet
owns P1-right, P2-right, P3-right and P4-right, while the counter owns P1-left,
P2-left, P3-left and P4-left. Combined Evidence Review used 98.857 Detection
seconds, 23,557 input tokens, 6,436 output tokens and `$0.167211`, compared
with V6.9's 143.445 seconds and `$0.237150` for the equivalent correct result.
Conditional reconciliation was not exercised because all eight selected links
were already strong. Page-1 positional View labels remain locally reversed
relative to pages 2 through 4, but membership is correct. Full audit:
`notes/DETECTION_V6_10_COMBINED_EVIDENCE_REVIEW_EXPERIMENTAL_CHECKPOINT_2026_10_25.md`.

## HSL Visual-Island recall gate, owner-defined 2026-10-21

Status: active. Source: private `Hasolelim_Carpentry_Plan_Floor_07.pdf`.
This gate measures only Visual-Island inventory and classification. It does
not approve graph links, packages, merges, quantities, or File Review objects.

Expected `object_evidence` Island counts:

| Page | Expected |
|---|---:|
| 2 | 0 |
| 3 | 3 |
| 4 | 6 or 7 |
| 5 | 3 |
| 6 | 3 |
| 7 | 4 |
| 8 | 4 |
| 9 | 3 |
| 10 | 3 |
| 11 | 2 or 3 |

Page 11 must retain two `object_evidence` Islands and one or two
`document_context` Islands. The plan may reasonably be classified either way;
the title block is context. Pages 9 and 10 must not be inflated to four object
Islands.

Page 2 is a generic floor plan and must be `document_context`, never an
object View or Dimension-graph endpoint. Page 1 remains outside this gate.

## V5.7.1 experimental checkpoint, 2026-10-23

Status: **not accepted and not deployed**. Protected base is V5.6.1
`5de4cf4`; full record is
`notes/DETECTION_V5_7_1_EXPERIMENTAL_CHECKPOINT_2026_10_23.md`.

The single-call membership-edge experiment passed one local Page 23 run at 4
Object Islands and 3 packages, and one Adda run at 9 and 2. Metal returned 42
and 14, which requires visual membership review even though the package count
is within its historical interpretation range. HSL returned 29 and 10, failing
this HSL recall gate before graph construction. Its raw Island loss is page 3,
two rather than three, and its classification loss is page 11, four raw
Islands but one Object Island. The next experiment must restore the V5.6.1
Island/classification contract before judging the membership-edge strategy.

## V4 Page 23 release gate, 2026-10-16

Status: accepted for the Page 23 temperature-zero gate on 2026-10-18. The
source is the private `page-23.pdf` drawing provided by the owner. Its V4 run
`run_cc459dc46e91445cb045614b69ca559e` incorrectly merged all products into
one object, so it cannot be used as an acceptance result.

A fresh V4 production run passes this gate only when it returns these three
commercial objects, each with quantity `1` and page `1` evidence:

- Shelving unit, the separate tall shelving assembly at left.
- Sliding door system, both leaves on their single shared track.
- TV console, the separate L-shaped console at bottom.

Every UI-only presentation preview must isolate its respective object. The
complete page may be shared as evidence and must never turn the three products
into one object. For this source, the expected metadata is `project_name`
`Beregovoy Proezd 5`, `design_partner` `ZE | WORKROOM studio`, and client
`unknown`. The generic filename `page-23.pdf` is not project evidence.

### Temperature-zero checkpoint, 2026-10-18

Commit `2593c23` explicitly sends `temperature=0.0` to the one integrated
Haiku Visual Registry request and records that setting in every usage event.
Ten fresh Page 23 runs all returned the expected three objects, quantities
`1, 1, 1`, and one TV-console object containing both complete console views.
All ten subsequent locked Detection records also contained exactly three
objects. There were no Registry validation failures. Registry duration averaged
12.639 seconds and RFQ processing-cycle duration averaged 23.705 seconds.

This accepts Page 23 only. It does not replace the Adda, Kitchen or Metal
boundary gates. Full run evidence and protected contract:
`notes/DETECTION_V4_PAGE23_TEMPERATURE_ZERO_CHECKPOINT_2026_10_18.md`.

### V4.2 diagnostic checkpoint, 2026-10-17

Code checkpoint: `1049e85`. The accepted V4 Registry path is retained, with a
narrow Haiku-to-Sonnet boundary router and persisted structured Registry audit.
This is not a release-gate pass for boundary stability.

Fresh runs after the checkpoint returned Page 23 counts `3`, `4`, `3`.
The router selected Haiku in both routed runs because OCR saw one large drawing
region on the single page. The four-object failure split the two views of the
TV console without positive evidence that they were different products. The
next boundary repair must use this persisted decision audit to address that
cause, not add a Page-23 count override.

### H1 Haiku correspondence checkpoint, 2026-10-17

Checkpoint `1a62549` adds a Haiku-only correspondence audit before Registry
locking. Four fresh persisted Page 23 runs returned three objects. The next
run failed validation because Haiku omitted a Registry object from the only
page's coverage, leaving it with no derived evidence page. This is recorded as
a transport failure, not a fifth boundary result. The H1 five-run stability
gate remains open until single-page coverage normalization and failed-response
audit persistence are added and tested.

The H1 reliability repair is now implemented and focused checks cover both
paths. It normalizes only a missing object ID on a document's sole physical
page, and saves a failed Registry audit without creating a synthetic RFQ run.
The Page 23 five-run boundary gate remains open and needs fresh production
runs after deployment.

## Current no-cache baseline

- Date: 2026-07-22
- Environment: local Streamlit, port 8501
- Detection prompt: `detection_v3_2_6_ocr_identity_reconciliation`
- OCR contract: `ocr_v2`
- Architecture: PDF visual analysis plus OCR evidence
- Anthropic prompt/document cache: disabled
- Backup: `v3.0.27_detection_v3_2_6_object_boundaries`

Application-level file and OCR result caching is disabled for benchmark runs.
Anthropic input prompt/document caching is also disabled by default. Enable it
later for production with `DETECTION_INPUT_CACHE_ENABLED=true`.

## page-23.pdf

Expected commercial objects: 3.

| Run | OCR | Detection | Total | Objects |
|---|---:|---:|---:|---:|
| 1 | 6.236 s | 12.476 s | 20.273 s | 3 |
| 2 | 5.658 s | 14.890 s | 23.799 s | 3 |
| 3 | 5.851 s | 12.465 s | 19.652 s | 3 |
| Median | 5.851 s | 12.476 s | 20.273 s | 3 |

Object boundaries and metadata are stable. All three runs return one shelving
unit, one sliding-door system, and one console; component leaves are not split.
External dimensions remain a separate known issue.

### Accepted vNext artifact checkpoint, 2026-10-04

Checkpoint: `43933e5`, tag
`checkpoint-2026-10-04-deferred-review-artifacts`. Production owner acceptance
on `run_a341ead8c4724e9d8b0b95e238b39b2f` confirmed three isolated previews,
three deferred names, and one shared-track Sliding door system with quantity
`1`. Preview production must accept normalized `0..1` model coordinates and
persist their OCR-pixel equivalent before crop creation.

This is an artifact-publication and door-quantity checkpoint, not an external
dimension acceptance. The same run still stored door leaf width `950` instead
of the `4130` track span and console width `1760` instead of the `3610` full
span. The next benchmark must score every W/H/D axis separately after an
isolated dimension pass.

## Металл (1).pdf

Expected commercial objects: 15, including distinct ЛП-1, ЛС-1, ЛС-2, and МП-1 positions.

| Run | OCR | Detection | Total |
|---|---:|---:|---:|
| 1 | 19.040 s | 30.094 s | 51.800 s |
| 2 | 9.512 s | 30.285 s | 41.998 s |
| 3 | 22.486 s | 31.878 s | 57.715 s |
| Median | 19.040 s | 30.285 s | 51.800 s |

All three runs returned the expected 15 objects and stable quantities. OCR
returned byte-identical evidence in 9.512–22.486 seconds; the wide total range
comes from provider OCR latency, while Detection remained at 30.094–31.878
seconds. External dimension axes remain a separate known issue.

## 20.10.2023_Furniture.pdf

Expected commercial objects: **27**, corrected after the product owner inspected
the object sheets on 2026-09-14. The earlier 23-object target was wrong. The
table of contents is useful package evidence, not the final authority: the
object sheets contain reused and conflicting codes.

Reference physical membership:

- `CM-1.1`, `CM-1.2`, not the parent heading `CM-1`;
- `CM-2`, `CM-3`, `CM-4`, `CM-4.1`, `CM-5`;
- two independent `CM-6` products: bathroom vanity and door/panel assembly;
- separate `CM-7.1` and `CM-7.2`, not an extra parent `CM-7`;
- `CM-8`, `CM-8.1`, `CM-9`, `CM-10`, `CM-11`, `CM-12`, `CM-13`,
  `CM-14`, `CM-15`, `CM-16`, `CM-16.1`, `CM-17`, `CM-18`, `CM-19`;
- two independent `CM-20` products: bench pillows and wooden shelf/ledge.

The `CM-11/CM-12` sheet internally mislabels its two chair bodies as `CM-10`.
The `CM-17/CM-18` sheet labels the second, quantity-four product as `CM-17`.
Resolve these against sheet titles, product bodies, dimensions, and quantities;
do not create `CM-17.1` or a dimensionless extra `CM-18`. A benchmark match
requires the correct physical products, not merely the total count or a flat
set of code strings.

The source is a 27,904,163-byte, 39-page A3 production drawing package. The
original monolithic PDF fails Anthropic document processing even through the
Files API. A 96-DPI page-image experiment produced:

| Variant | Render | OCR | Detection | Effective total | Objects |
|---|---:|---:|---:|---:|---:|
| JPEG pages + OCR | 3.872 s | 36.397 s | 42.151 s | 78.548 s | 17 |
| JPEG pages, no OCR | 3.872 s | 0 s | 75.038 s | 78.910 s | 23 |
| Integrated JPEG, no OCR, run 1 | 3.892 s | 0 s | 68.683 s | 74.170 s | 26 |
| Integrated JPEG, no OCR, run 2 | 3.722 s | 0 s | 80.991 s | 85.513 s | 26 |

`Effective total` assumes JPEG rendering runs concurrently with OCR. The
sequential sum for the OCR variant is 82.420 seconds. These are historical
experiments measured against the superseded 23-object target. Under the
corrected 27-object target, count alone cannot establish their quality.

## Historical cached-input reference

Backup `v3.0.24_detection_v3_2_2_speed_quality_baseline` used Anthropic
prompt/document caching. Its medians were 20.963 s for `page-23.pdf` and
43.976 s for `Металл (1).pdf`; these values are retained only for historical
comparison and are not the active benchmark.

The previous no-cache metadata checkpoint
`v3.0.26_detection_metadata_no_cache_baseline` had medians of 23.035 seconds
for `page-23.pdf` and 51.831 seconds for `Металл (1).pdf`, with Detection
medians of 13.891 and 36.813 seconds respectively.

## Acceptance rules

Quality has priority over speed. Compare candidates on the same files with at least three fresh runs and use the median, not one run.

- `page-23.pdf`: retain 3 correct commercial objects; investigate a median total above 25 seconds.
- `Металл (1).pdf`: retain 15 correct commercial objects; investigate a median total above 53 seconds.
- `20.10.2023_Furniture.pdf`: compare all 27 physical products and their boundaries, including the two `CM-6` and two `CM-20` products; the monolithic PDF route is not acceptable because it fails before returning JSON.
- Accept a material slowdown only when it produces a clear, reviewed quality improvement.
- Treat fallback retries and validation failures as separate diagnostics rather than normal benchmark samples.
- Never enable application-level result caching during development benchmarks.
- Keep Anthropic input caching disabled while measuring fresh-file behavior.

For quality review, compare object boundaries, short names, quantities, and every external W/H/D axis. Matching object count alone is not sufficient.

## Rejected naming experiments

V3.2.7 and V3.2.8 attempted to enforce compact bilingual names inside one
free-form `object_name`. V3.2.9 separated index, English name, and original name
in the Detection response and assembled the UI label in Python. These versions
were rejected: naming compliance remained inconsistent, page-23.pdf regressed
to four objects and quantity 2 in one run, and V3.2.9 medians increased to
28.160 s for page-23.pdf and 50.297 s for Металл (1).pdf.

The additive Supabase columns `object_index`, `object_name_en`, and
`object_name_original` may remain in the database. V3.2.6 does not read or write
them, so no destructive rollback SQL is required.

## Direct PDF + Naming Split v3.0.30 baseline

Backup: `v3.0.30_experimental_direct_pdf_naming_split_checkpoint`.
Despite the historical archive slug, this checkpoint is the accepted stable
baseline and its flow is active by default in production.

The active flow sends the original document to Mistral once, removes
user-facing naming from Detection, and applies a separate Naming Agent after
the object list is locked. The former rendered-page OCR route remains only as
an explicit rollback path.

Three accepted repeated runs of `Металл (1).pdf` produced:

| Run | OCR | Detection | Naming | Total | Objects |
|---|---:|---:|---:|---:|---:|
| 1 | 1.061 s | 30.124 s | 4.298 s | 38.216 s | 15 |
| 2 | 0.798 s | 30.913 s | 4.390 s | 38.586 s | 15 |
| 3 | 0.960 s | 29.508 s | 4.461 s | 38.308 s | 15 |
| Median | 0.960 s | 30.124 s | 4.390 s | 38.308 s | 15 |

All three OCR results contained 11 pages and 633 literal evidence items.
Commercial object boundaries stayed correct, including distinct LS-1, LS-2,
and LP-1 positions. External dimensions varied materially between identical
OCR handoffs, so dimension binding remains the next quality task.

The sub-second OCR repeats may include provider-side deduplication of the same
PDF. They must not replace the cold-user benchmark until Direct PDF is tested
on previously unseen or byte-unique documents. `page-23.pdf` also returned two
objects in one of four Direct PDF runs, so that quality variance remains an
open issue even though v3.0.30 is the active baseline.

## Restored API-compatible checkpoint — 2026-09-12

Checkpoint commit: `bb7c712`.

After restoring one-request Direct PDF OCR and the Detection + text-only Naming
split, the user-visible runs returned to approximately 23 seconds for
`page-23.pdf` and 43 seconds for `Металл (1).pdf`. The corresponding persisted
cycle timings were 19.925 seconds (OCR 0.864, Detection 12.801, Naming 4.380)
and 41.551 seconds (OCR 1.271, Detection 26.928, Naming 11.138).

This is a recovered speed checkpoint, not a new quality acceptance baseline;
object-boundary quality remains subject to the existing 3-object and 15-object
acceptance rules.

## Compact Naming input — 2026-09-12

Naming v4 keeps locked identifiers, existing labels, evidence pages, up to 300
characters of Detection context, and capped OCR snippets. It no longer repeats
dimensions, materials, or complete notes. The serialized Naming payload was
reduced by approximately 30% for `page-23.pdf` and 41% for `Металл (1).pdf`
relative to the full text-only input.

Observed Naming time fell from 4.380 to 2.934 seconds for `page-23.pdf` and
from 11.138 to 2.650 seconds for `Металл (1).pdf`. Product categories recovered
after the context hint was added, while original-language labels remain less
consistent. Detection object-count variance is evaluated separately because
Naming runs only after the object list is locked.

## Asynchronous Supabase diagnostics — 2026-09-12

The authoritative RFQ run and detected objects remain a synchronous File Review
dependency. Full OCR JSON and OCR, Detection, Naming, and cycle usage events now
leave the critical path and are inserted afterward as one background batch.

The verified `page-23.pdf` cycle completed in 18.512 seconds (OCR 0.700,
Detection 13.431, Naming 3.420); its unclassified persistence/orchestration tail
was 0.961 seconds versus 1.940 seconds in the preceding run. The verified
`Металл (1).pdf` cycle completed in 28.664 seconds (OCR 1.192, Detection 24.393,
Naming 2.536); its tail was 0.543 seconds versus 2.850 seconds. All four events
and complete OCR payloads were subsequently present in Supabase; the stored OCR
payloads were approximately 7 KB and 229 KB.

This persistence change cannot alter Detection semantics. The large-file run
returned 13 rather than the 15 acceptance objects, which remains an independent
upstream Detection variance tracked by the existing acceptance benchmark.

## Deferred Naming checkpoint — 2026-09-12

Naming v4 now starts only after the provisional Detection result is stored, so
File Review no longer waits for Naming. The screen opens with locked provisional
labels and replaces only unchanged names when the background result arrives.

The first local user-visible laps were approximately 16 seconds for
`page-23.pdf` and 29 seconds for `Металл (1).pdf`. Persisted critical-path cycles
were 13.177 seconds (OCR 0.967, Detection 11.805) and 26.649 seconds (OCR 1.160,
Detection 24.427). Background Naming took 2.526 and 9.335 seconds respectively
and is excluded from Total lap. The remaining 2–3 user-visible seconds occur in
the final Streamlit transition and File Review load.

This checkpoint improves perceived latency but does not change Detection. The
same runs returned 4 and 13 objects rather than the 3 and 15 acceptance targets,
so object-boundary stabilization remains the next prompt task.

## Semantic-category Naming V5 — 2026-09-12

Naming V5 keeps the compact text-only background route but no longer accepts an
object index or proper/model name as a complete product name. Every English
label must identify the physical product category; an explicit model name may
be retained only alongside that category. The application now joins the index
and semantic label with a space instead of a dash.

The local qualitative check produced useful category-bearing names and about
2.9 seconds of background Naming. The tested large-file Detection result held
13 objects, which is below the 15-object acceptance target and remains an
upstream Detection issue. Some source-language labels present in local OCR,
including an OM15-1 railing label, were not returned consistently; that is the
reason V5.1 adopts a single English-only MVP label instead.

V5.1 returns one 2–3 word English semantic label; explicit proper/model names
may be transliterated when useful. The application renders `index + name` with
a space, without a dash, parentheses, or source-language duplicate. The compact
text-only background route is unchanged.

## Key rollback checkpoint — Detection 3.2.6.1 — 2026-09-13

Detection 3.2.6.1 deliberately keeps the effective Claude prompt byte-identical
to the accepted 3.2.6 no-naming prompt. Its only user-facing change is the File
Review heading `Detected Objects: N`, where Python computes `N` from the object
list already loaded for rendering. This code runs after the measured processing
cycle and makes no OCR, Claude, or Supabase request.

The user-designated verification set produced:

| File | OCR | Detection | Total | Objects |
|---|---:|---:|---:|---:|
| `page-23.pdf` | 0.934 s | 13.698 s | 15.293 s | 4 |
| `Металл (1).pdf` run 1 | 1.386 s | 28.263 s | 30.293 s | 13 |
| `Металл (1).pdf` run 2 | 1.281 s | 27.526 s | 29.381 s | 13 |
| `Металл (1).pdf` run 3 | 1.917 s | 28.156 s | 31.168 s | 15 |

This is the key code and UX rollback point requested by the user. It does not
replace the earlier 3-object and 15-object quality targets: Detection output
still varies on both benchmark documents and remains the next investigation.

### Detection/UI 3.2.6.2 — persisted File Review names

The 3.2.6.2 checkpoint keeps the same effective Detection prompt and adds one
post-Detection behavior: committing an object-name input with Enter or blur
immediately updates `rfq_detected_objects.object_name`, synchronizes the local
File Review cache, and leaves the active screen unchanged. The persistence path
was verified directly in Supabase on `unknown_project_run_001`, `object-002`,
whose edited value was stored as `Sliding door panelbjhbj`.

### Detection/UI 3.2.6.3 — Page-aware processing progress

The final Detection checkpoint keeps the exact Golden runtime prompt and
provider schema:

- effective prompt SHA-256: `682b91359ae4ac72b6329e1968360a63f37e714fa115725fa151d13a0ef676c5`;
- provider schema SHA-256: `ec673df2276cf316fa059bda8f14b064e463a96a3c6f99fa077a73d68c1ba52c`.

The rejected schema and quantity-prompt experiments are not included. The UI
change is based on 35 Golden orchestration runs, whose median backend stages
were 1.386 seconds for OCR, 25.065 seconds for Detection, and 1.011 seconds for
saving. The visible range is now 8–13% for OCR, 13–96% for Detection, and
96–99% for saving. Detection uses an ease-in curve so progress starts
conservatively and accelerates when the backend phase completes.

After OCR, the authoritative OCR page count selects only the expected Detection
pacing, without changing backend work or completion:

| OCR pages | Expected Detection pacing |
|---:|---:|
| 1–2 | 14 s |
| 3–6 | 18 s |
| 7–12 | 28 s |
| 13–20 | 45 s |
| 21+ | 60 s |
| Unknown | 28 s |

Across 36 matched Golden runs, page count and Detection time had Pearson
correlation `0.853`. Production upload time remains outside orchestration
timing because the browser progress shell starts before Streamlit receives the
file. No unverified production multiplier is applied.

### v3.0.41 - Large PDF Sonnet transport and resilient Naming checkpoint

The accepted experimental route keeps the Golden effective Detection prompt
and provider schema unchanged:

- prompt SHA-256 `682b91359ae4ac72b6329e1968360a63f37e714fa115725fa151d13a0ef676c5`;
- schema SHA-256 `ec673df2276cf316fa059bda8f14b064e463a96a3c6f99fa077a73d68c1ba52c`.

PDFs whose estimated inline Base64 payload reaches 30,000,000 bytes are
rendered into ordered JPEG pages at 96 DPI and sent as one complete package to
Sonnet 4.6. The large route skips Mistral OCR, Identity Lock, and the rejected
flat index anchor. Smaller files retain the Golden Mistral OCR plus inline PDF
route and Haiku Detection. The original PDF still remains available to the
downstream workflow; Detection receives all page images together, not separate
page-wise object decisions. Each benchmark run can append a timestamp to its
run_id so stored outputs do not overwrite earlier trials.

Naming V5.2 accepts a precise one-word physical category. A single invalid
name no longer discards valid names for the entire locked object set: only the
invalid row retains its original placeholder. Naming failures are logged and
persisted as failed usage events. This fixes the observed Naming failure caused
by one one-word category being rejected under the former 2-3-word-only rule.

Three `jpeg_sonnet_clean` runs on the 27,904,163-byte, 39-page furniture PDF
were stored under unique run_ids:

| Run | Render | Detection | Total to File Review | Objects | Naming background |
|---|---:|---:|---:|---:|---:|
| 1 | 6.836 s | 141.315 s | 149.371 s | 25 | 17.011 s, succeeded |
| 2 | 6.743 s | 139.057 s | 146.470 s | 26 | 18.011 s, succeeded |
| 3 | 6.656 s | 114.593 s | 121.846 s | 27 | 5.320 s, succeeded |

All three runs used 67,278 input tokens and generated 5,735-5,991 output
tokens. Detection cost was $0.288-$0.292 per run. The median total to File
Review was 146.470 seconds. JSON generation after the first token was stable
at approximately 80-82 seconds; first-token time ranged 32-61 seconds.

This is a working transport and Naming checkpoint, **not a 27/27 quality
acceptance**. Run 1 missed the second `CM-6` and the pillow `CM-20`. Run 2
found both `CM-6` bodies but joined pillows with the wooden `CM-20`. Run 3
again missed the pillows, created a weak/dimensionless `CM-18`, and labelled
the quantity-four `CM-18` body as a second `CM-17`. The count 27 was therefore
accidental. File Review remains required before estimating this package.

Known limitation: the one-call image route rejects PDFs over 100 pages because
the provider request cannot contain more than 100 images. A universal route for
such packages is still pending. The rejected duplicate-identifier addendum,
OCR-plus-Identity-Lock path, and local index anchor are not part of this
checkpoint.
