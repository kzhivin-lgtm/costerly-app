# Estimation 9 Parts Check from Upload

Work 3.17.4.6. The owner confirmed the production release on 2026-11-12.
The release starts from Detection V8.4.27 at
`379f91f5760dbacb1652da2a6d0b379d17745586` and ports the Parts Check
checkpoint `391ac35`. Detection code and locked dependencies are identical
to the release base.

Upload the PDF, review the accepted objects in File Review and select
Continue. The existing worker persists the immutable Estimation inputs.
The Parts Check worker uses the same accepted partition and published
Detection evidence. Pricing uses its established route. In Objects,
select Parts Check and download the report when ready. The button refreshes
the result on demand. Report storage is private and bound to the company,
upload and estimate. The document includes sheet coverage, the part rows
and the open dimensions, quantities and ownership issues.

Local acceptance uses the saved Adda inputs and archived provider readings.
It exercises new native crops, Analyze, Block Geometry, Parts, Parts Check,
and a simulated private publication and readback. It covers both objects,
all four sheets and 149 rows. A repeated immutable handoff reuses the
report. A foreign company cannot load it. The archived V8.4.27 Floor 07
audit checks the published Detection contract, including normalized
dimensions and zero-level datum annotations. Forty-one focused tests pass.
The pre-existing dependency-list assertion is stale at the Detection
base. The runtime dependency list, lock and Dockerfile remain identical.

Build marker `estimation-v9-detection-v8.4.27`. The owner will upload a
fresh Adda after the marker appears in production. Check the actual
report and source coverage before claiming fresh Adda acceptance.
`ESTIMATION_V9_PARTS_CHECK=false` disables the report route and button.
The Detection rollback reference is
`detection-v8.4.27-same-sheet-render-matching-production-2026-11-12`.

## Fresh production Adda witness

Acceptance remains open for work 3.17.4.6. Upload
`run_c226c39adb364b30a5c3d8d26c91dd2b` used Detection event
`9abd27ad-b865-48e9-9cee-9b91e4d44665`. Detection retained all eight View
boxes and grouped the corner cabinet as before. It split the straight
cabinet into `Vanity unit` (P1/P3) and `Console cabinet` (P2/P4). The three
immutable Estimation inputs retain that partition. The live Detection event
confirms ADA routing with Haiku 5.5 Discovery and Sonnet 4.6 Membership Review.

The pricing route took 182 seconds from estimate creation to the last
object update: 48 seconds before Analyze, 25 seconds in shared Analyze,
95 seconds in sequential Calculation through final BOM persistence, and
14 seconds for publication and pricing. Detection took 65 seconds in a
separate upload phase. The two straight-cabinet entries reached
`materials_costed`. The corner cabinet failed at `calculation_agent`
before `2vn_geometry`. No detailed failure trace was recorded. The checked
SQL stage constraint omits `calculation_agent`, a possible reason for the
missing trace. The underlying Calculation exception is unknown.

At 13:09 local time, roughly 15 minutes after estimate creation, the
estimate had no Parts Check report in its private storage prefix and no
Parts Check status or request events in the database. The production
handoff data could be read, but the last stage reached by the background
job and its underlying exception remain unknown. Railway runtime logs
require an authenticated session. No new model request or upload was made.

Estimation 9 wrote the final status and model metrics in a single PostgREST
insert. The live schema requires `input_tokens` and `output_tokens`. The
request rows provide both counts, and the terminal row omits them. The
installed client sends the union of columns without `missing=default`.
A mixed insert therefore violates the token column constraints and can
discard a failure record along with every request record. This explains
how the journal can be empty. The missing storage artifact has a separate
cause because upload precedes the insert.

Parts Check has one background worker and no job-wide deadline. Each model
request has a 120-second limit. The four original sheets are reviewed in
sequence, allowing up to eight minutes for Inventory Check alone after the
earlier calls. The prior two-object Adda archive contains nine request
records totalling 116.761 provider seconds. This is a reference, not a
measurement of this production job. Pending, P0: use runtime logs to
identify the stop if available.

## Estimation 9.1

Work 3.17.4.6. Build marker `estimation-v9.1-detection-v8.4.27`. Parts
Check writes its terminal status separately, with
explicit zero token counts. Rejected model metrics are logged without
invalidating the status. Regression tests cover both a saved report and
a recorded pipeline failure when metrics persistence fails. Existing
production jobs have no recoverable status from this change.

Pending, P0: establish a bounded Inventory Check before relying on the
production report flow. Preserve the all-sheet check and record the job
start, current stage, and outcome. Proposed approach: reconcile existing
Detection, OCR and Offline Vector evidence on every sheet against Object
Inventory. Send unresolved material candidates or uncovered drawing regions
as one bounded request and report unresolved evidence explicitly. Parts
Check itself stays a deterministic reconciliation of Parts with the checked
inventory. Verify recall on archived findings and measure the whole path
before setting a production latency target. The proposal has no runtime
changes in this repair.

## Estimation 9.2

Work 3.17.4.6. Build marker `estimation-v9.2-detection-v8.4.27`.
Offline Vector feeds Island Map and Understanding, then Front, Block
Planner and Block Locator. Object Inventory and Inventory Check precede
Block Geometry. Parts uses its measured block envelopes. Parts Check
now includes those envelopes and their source references.

The Adda production witness `run_60b71cf1428b4f8cb93ecc51098a186b`
had 33 RapidOCR numeric readings and an empty canonical dimension
inventory. Estimation 9.2 validates the saved coordinate readings against
each frozen View and uses them when the primary measurements yield no
printed spans. The casework resolver can corroborate owned orthographic
views by their drawer bank or by matching both elevations to one plan.
Glass box base estimates reuse the corresponding shelf size, and the
standard backing recipe uses 6 mm when no thickness is available.

An offline replay used the exact production Detection and OCR payloads,
the matching original PDF and archived Analyze and Inventory Check model
responses. All nine block envelopes had at least one axis, 22 of 27 axes
were resolved, and five blocks had all three axes. The report contained
149 rows and 75 rows with an unresolved dimension. Eight glass bases
had estimated footprints and 40 panes were represented. The earlier
production report contained 147 rows and 139 dimension gaps. New upload
acceptance and full detail sizing remain open. Remaining work includes
front face boundaries, glass wall heights, LED routes, partial block
depths and standalone dimensions. Model responses in the replay were
archived, so its output is a control for the handoff and local compilation.
Two saved Lev1 and three saved Lev2 Block Geometry runs reproduced
exactly. The Lev2 Parts result also matched the Estimation 9.1 control.
Thirty-three focused tests passed.

## Estimation 9.3

Work 3.17.4.6. Combined build `estimation-v9.3-detection-v8.4.28`.
The saved successful Block Geometry results remain the comparison baseline.
The Parts compiler measures individual fronts, display glass, mirrors,
visible plinth runs, and closures on corroborated source boundaries.
The shared kitchen worktop carries its plan envelope and still requires
seam, edge and cutout confirmation.

The former three-object Adda input `run_b6da521544bb40fba48fb40c73cd0d54`
reproduced the 9.2 failure. The Front Role Review used all 4,000 output
tokens and returned truncated JSON. A second failure was an out-of-frame
contour ID in Block Locator. The role review now binds a compact schema
to eligible contour IDs and exposes missing or rejected decisions in Parts
Check. Block Locator retains valid additions to the locked Planner output
and flags scopes with rejected references. The request ledger records the
stop reason and validation failure type.

Front component review runs alongside Island Map and initial Front.
Inventory Check still reviews every original sheet independently, with
up to three requests in parallel. Indexed callout crops bind LED labels
to the original vector leaders. Plan strokes provide route extents for
the two 4000 K lights on the two-object Adda control.

| File | Detection witness | Fresh provider time, end to end | Final compiled control |
| --- | --- | --- | --- |
| Lev1 | `run_1cba0b2491dc413c9a3be2fdd526226b` | 53.51 s | 3 Blocks, 28 Parts rows, zero dimension gaps. Block Geometry matches the saved control |
| Lev2 | `run_189150ebf62447fc958f7c23cc34e3bb` | 45.42 s | 9 Blocks, 107 Parts rows, zero empty part-dimension fields after the plan-envelope compilation. Four lower carcass depths still use the worktop proxy |
| Adda | `run_090b2315dc6a4036a0932bfbaf9ec319` | 79.46 s | 9 Blocks, 149 Parts rows, 18 rows with missing dimensions. 9 drawer fronts, 8 door fronts, 8 pull-out shelves, 40 panes and 5 LED runs |

The table measures Parts Check from the frozen Detection input through
local compilation. The final deterministic measurements were also run
against archived responses from those same source PDFs. The failed
three-object Adda witness completed with a fresh compact review after
reusing the exact initial responses; the extra object still lacks a
source-grounded Block. The second fresh two-object run proposed an overlapping
second mirror on the mounting-panel contour. The exact-response replay now
retains this proposal as an unresolved identity finding and publishes one
mirror on that assembly. Thirty-one focused tests passed. The private
report publication and download contract were replayed for all three files.

Active, P0: confirm the final report on a fresh production Upload and
reconcile open Inventory Check findings. On Adda, three lower carcass
depths, mirror stock thicknesses, three 3000 K route lengths, and hidden
construction remain open. Verify quantities, profiles and seams before
using the estimates for fabrication. Material selection and pricing are
outside the Parts Check scope.

## Estimation 9.4

Work 3.17.4.6. Build `estimation-v9.4-detection-v8.4.28`.
Previous release and rollback reference `78ad867038eca4b498786758dc76cdd1b9e65194`.

The first Lev2 production run contained 106 Parts rows. It matched 53 of
107 control rows and left 53 rows with missing dimensions. Substituting only
its accepted Detection observations into the frozen control reproduced the
missing block envelopes. Both plan-to-elevation links used `unique_geometry`,
which Estimation had excluded from the plan alignment. The second production
run contained 105 rows and matched 100 of 107 control rows. Its relation type
passed the gate, but two omitted fixed panels reduced the measured spans.

Planner and Block Geometry now accept both geometry-backed link types.
The native span match still gates selection of the plan and elevation.
Cross-view depth still requires calibrated drawing scales and matching
boundaries. On the aligned elevation, an unclaimed full-height rectangular
panel can extend the uniquely adjacent block at an outer edge or a closed
seam. Contours already claimed by Front keep their ownership. The recovered
contour is recorded in Object Inventory and used by Block Geometry and Parts.
The rule uses drawing geometry and no file names, contour IDs or target counts.
The Detection implementation and legacy BOM costing are unchanged.

| Saved production input | Fresh Parts Check | Elapsed | Comparison |
| --- | --- | --- | --- |
| Lev2 `run_da0b26c5a03742118490aa193e7d15db` | 9 Blocks, 107 rows | 49.70 s | 107/107 matching control rows |
| Lev2 `run_b5c3bfdf65f44e64bc949b6bcb79c632` | 9 Blocks, 107 rows | 50.85 s | 107/107 matching control rows |
| Lev1 run prefix `run_16d850` | 3 Blocks, 28 rows | 44.58 s | 28/28 matching control rows |

The fresh provider tests used the original PDF, saved Detection partition
and OCR from those Uploads. Comparison uses object, block, role, source
instance, quantity, unit and dimensions. Controlled replays deliberately
omitting the lost panel reads also reproduced all 107 Lev2 rows. B02 returned
to 690 × 650 × 1150 mm and B04 to a width of 990 mm. The shared worktop
returned to a plan envelope of 2480 × 3005 × 30 mm. Parts Check contains zero
empty dimension fields on both Lev controls. Four Lev2 lower carcass depths
still use the explicitly assumed 600 mm derived from the worktop proxy.
The exact worktop cut outline remains open. Front on fresh Lev1 reported
four drawer observations. Parts retains the three distinct V04 drawer fronts.

On the same archived model responses and inputs, the two-object Adda replay
matches 9.3 for all nine Block envelopes, Front counts, and 149 Parts rows.
Eighteen Adda rows still have missing dimensions. Forty-four focused tests
and two subtests passed. Production acceptance requires a new Upload and
confirmation in Objects. The legacy costing agent failure is tracked separately.
