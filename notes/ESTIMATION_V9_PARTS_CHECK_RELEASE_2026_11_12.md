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

### Fresh Lev2 production Upload

Run `run_6096a134aae24951ac6f36a54500c21d`, Detection event
`15536d54-5d96-4c43-bc60-c72fcd4cf43c`, Parts Check event
`7a79d15e-df4a-43cd-87c3-3beda4e6d402`. Detection took 53.384 seconds and
published one object. Parts Check `estimation-v9.4-parts-check` succeeded
in 57.094 seconds. The Objects report reader returned `ready` for that
estimate. The downloaded report hash matched the event. All 107 rows
matched the saved control by identity, quantity, unit and millimeter
dimensions. It retained nine blocks, the B02 and B04 panels, and the
2480 × 3005 × 30 mm worktop envelope. Four lower carcass depths use the
explicit 600 mm estimate. Inventory Check remains open for the worktop
and unresolved element identities or ownership.

The separate legacy costing pipeline reached `estimation_analyze` and
failed at `calculation_agent` in event
`c60a2348-f5ff-4857-ac4b-8b50a82f7d91`. The stored reason is generic and
does not retain the provider exception. The 9.4 Parts Check report was
already saved when costing failed.

### Lev2 Parts Check checkpoint

Tag `estimation-v9.4-lev2-parts-check-2026-11-12` points to the deployed
runtime commit `52f2f8356edcae860be442cc49ef121e5d61c3b9`.
Two independent repeats ran the production Parts Check pipeline with
fresh Sonnet responses and the exact saved PDF, Detection result, OCR and
File Review inputs from `run_6096a134aae24951ac6f36a54500c21d`. The source
PDF SHA-256 is `b69e132814531862c1abbf2ea3910e0221ab013dd2d0fb184400149d6ec02b1d`.

| Test | Time | Matching Parts rows | Block envelopes | Open Inventory Check items |
| --- | --- | --- | --- | --- |
| Fresh production Upload | 57.094 s | 107/107 | 9/9 | 9 |
| Repeat 1 on the saved Detection input | 45.08 s | 107/107 | 9/9 | 8 |
| Repeat 2 on the saved Detection input | 41.98 s | 107/107 | 9/9 | 11 |

Both repeats retained all expected part identities, quantities, units and
millimeter dimensions. Apart from the owner source references on two rows,
the Parts data also matched the production report. Front observation counts
and Inventory Check findings varied. The final counts stayed at 17 doors,
5 drawer fronts and 2 lift-up fronts. Four 600 mm lower carcass depths are
still assumptions. Replaying each captured model response set without new
requests reproduced its full Parts Check JSON byte for byte. Report SHA-256
values for the two repeats are
`784e555e47a93f2272c7cf618c5eff84b3e0ba48c7c5049aa1cbac9925950ed4` and
`e420a6b99e1338a4a8863c44a5dc76fff5e801481fb1aba96756c5396fd09c24`.

This checkpoint covers the Lev2 Parts Check results. The two repeats reused
Detection and File Review, so the test isolates model variability within
Parts Check. Inventory Check gaps, exact countertop geometry and the legacy
costing failure remain open.

### Legacy Calculation diagnosis and Material Demand handoff

The three Lev2 production inputs have a saved Dimension Graph and no
saved structural BOM, successful `assembly_first_bom` usage event, or
detailed failure trace. The checked-in trace constraint accepts
`assembly_agent`, while runtime sends `calculation_agent` and catches
trace insert errors. This can hide the error type from the detailed trace.

One isolated replay used the saved 9.4 Lev2 object input, Dimension Graph
and source page. A fresh Haiku Analyze response supplied nine scope zones.
The Haiku Calculation request returned `stop_reason=max_tokens` at 8,000
output tokens after 32.991 seconds. The runtime passed the incomplete
response to `JSONDecoder.raw_decode`, which raised `JSONDecodeError` at
the end of the returned text. This reproduces a cause of the production
symptom. The historical responses were unavailable for comparison.

Legacy Calculation extracts assemblies, sizes, counts and material family
hints or assumptions. The structural composer calculates parts and
requirements before catalog selection and project-wide purchasing. The
production Material Plan still reads that legacy BOM. A dry run of the
existing CB Parts adapter against the checked Lev2 repeat produced seven
material requirements and 55 cut part rows. It reported 28 unsupported
carcass rows because it maps sides, tops, bottoms and the divider to
`carcass_sheet`, which has no family preference in that adapter's lookup.
The dry run stopped at Material Demand and made no production writes.

### Parts Check to Material Demand adapter

The adapter consumes saved Parts Check reports and retains each row in a
material requirement or a review item. It uses the existing internal-sheet
family preferences for carcass sheets when a material note is absent.
Recognized stock notes carry their original text and source references.
Unresolved notes, ownership conflicts and quantities stay with the source
row. The shared worktop envelope remains a review item for cut geometry.
Quantity multipliers are carried from the original scope when present.

| Saved report | Source rows | Rows in demand | Rows held for review |
| --- | --- | --- | --- |
| Lev1 | 28 | 28 | 0 |
| Lev2 | 107 | 106 | 1 |
| Adda | 149 | 62 | 87 |

The Lev2 replay uses the archived provider responses and reaches the
existing Material Engine through the experimental material-context entry
point. All 107 Parts Check rows and all nine Block envelopes match the
checkpoint. The 28 carcass rows are included. Lev2 needs review because
the 2480 × 3005 mm worktop dimensions describe an envelope. The Adda review
rows preserve the unresolved stock notes, missing dimensions, glass
treatment, lighting specifications and the unsupported interior skin.
The verification used a saved catalog snapshot and did not publish pricing.
Seventy-one focused tests passed.

### Worktop area from plan contours

The experimental branch compiles the outline from Offline Vector after
Block Geometry. It joins linked plan faces and calibrates both axes from
printed dimensions. Separate surface requirements need a seam in the plan
and finish evidence in Understanding. Parts Check keeps the original part
and its envelope; Material Demand receives the area of each surface.

A fresh Lev2 Estimation run reused the original Detection output. Five
Sonnet calls took 41.3 seconds end to end, with no extra call for the worktop.
All nine Block envelopes and 107 Parts Check rows matched the checkpoint.
The gross area is 3.0 m²: 2.8 m² of main surface (artificial stone by
assumption) and 0.2 m² of the contrasting beveled end (material unresolved).
Parts Check displays one decimal place. Machine-readable output retains
calculation precision. The end material remains open.

Worktop material purchasing uses the complete outline without deducting
appliance openings. Understanding locates openings on one source Island;
Parts Check keeps the crop location on the worktop part. Material Demand
records each opening as a separate supplier service, in pieces. Stone
worktops use the existing `stone_cutout` operation code. Appliance type
from visual recognition is a hint only. The supplier offer is still
pending; the stock planner does not treat the service as a material.
Fresh Lev2 recognition found one opening on V02 in 50.4 seconds with five
existing Sonnet calls. Replaying those responses through the final adapter
emitted one `stone_cutout` and the same gross areas, with all nine Block
envelopes and 107 Parts Check rows still matching the checkpoint.

### Lev2 worktop Material Demand checkpoint

Owner accepted the experimental checkpoint on 2026-11-12, work 3.17.4.6.
Tag `estimation-v9.4-lev2-worktop-demand-2026-11-12` preserves
`5479af3bf759bddcb6e219692437fb835be993f7`. The run reused the saved
Detection and File Review inputs from `run_6096a134aae24951ac6f36a54500c21d`.
Acceptance covers 3.0 m² of gross worktop area split across the two surface
requirements, one `stone_cutout` service sourced to V02, and parity with the
previous Lev2 Parts Check. The fixture subtype and contrasting end material
remain unconfirmed. Supplier service pricing and production acceptance
remain open.

Final replay SHA-256 values for `parts-check.json` and `cb-materials.json`
are `8d9e3edccebbfeb4b5d5570cbe1a360bc24b6fb6fde2bc4ac9367060e64cb3bb`
and `7d3acee381384e9cbf0c61735593d5b96d59c3b3f3607cdc196deb19dff7d203`.

### Estimation 9.5

The estimate worker saves Parts Check before building Material Demand and
calling Material Engine. The second geometry and BOM pipeline is removed
from the launch. Repricing reads the saved, hash-checked report and its
exact File Review input revisions. Objects and Object Detail read the same
material plan. Unpriced requirements remain visible and an incomplete plan
cannot publish a final self cost.

Supplier services can enter the engine as per-piece Company Catalog offers.
The saved Lev2 replay against current Supabase catalogs retains 107 parts
across nine Blocks. Seven of ten purchasing requirements receive prices,
including the drawer slides. Three requirements still need evidence or
a source price: MDF finish, the contrasting worktop end and the cutout
service. Missing prices enter Assumption Fallback as gaps. Automated price
research remains open.

Parts Check now makes one bounded repair pass for unowned fixed-shelf
findings with distinct near-isometric planes and a unique matching native
elevation. It adds one part per visible plane to its Block, rechecks the
reconciled inventory and passes the result to Material Demand. It adds no
model calls and preserves findings without a defensible match.

On the saved Lev2 production input `run_6096a134…`, Front observed an open
shelf stack in V02; the inventory had no owner for it and Parts Check only
reported the gap. The repair matched V02 to the B02 lateral bay in V03
and emitted three separate shelf rows, each provisionally 206 × 206 × 17 mm.
The adjacent facade supplies the scale; the carcass supplies the assumed
thickness. The original 107 rows and nine Block envelopes are unchanged.
All three rows are allocated to sheet stock (127,308 mm² of cut parts).
The result has 110 rows, with the other Inventory Check issues still open.

Railway deployed production commit `820b5669677871c842f8cdeb5e410674d6510453`
on 2026-11-12 (deployment `47743a48-2824-43b7-88b1-c6ae5a5377ab`).
Core health returned HTTP 200. The owner applied the SQL migration. A
replay of the 110-row Lev2 report against the live catalog priced all ten
purchasing requirements, including one Israel Reference cutout at 400 ILS
excluding VAT. The material plan stays in review while the inventory has
open findings. A fresh authenticated production Upload is pending.
Release checks passed 48 tests; the dependency-list assertion also fails
against the unchanged 9.4 inputs because it predates the Detection
dependencies. This release did not change the runtime dependencies.

Fresh production Adda run `run_d5519c70ba9342f1873b0719749c6ed3`
published Parts Check 9.5 in 91.89 seconds: two objects, nine Blocks and
149 part rows (24 and 125). Material Engine allocated 2,955.31 ILS ex VAT
to nine of the ten admitted requirements. Object 001 has an open LDSP
20 mm assumption; Object 002 priced all five admitted requirements.
The demand adapter still holds all 24 glass-box part rows (including
4 mm tempered parts) and the LED strip rows. Inventory and dimension gaps
also remain. The server wrote `review_required` and null self-cost totals
for both objects, so Objects displays Review without a final price.
This confirms the production handoff and exposes incomplete costing.
Fresh Lev2 Upload verification remains pending.
