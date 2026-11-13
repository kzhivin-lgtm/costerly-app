# Estimation 9 Parts Check from Upload

## Estimation 9.15 Drawer runs and sheet thickness

Work 3.17.4.6. Parts gives visually similar drawers one size when they
form a horizontal row with a printed overall width and have no individual
printed dimensions. It retains each Front instance. Clear visible wood
grain supports a provisional veneered MDF stock choice in Material Demand.
Explicit stock notes retain priority. Nearby vector thickness projections
can share a nominal thickness only where the part construction and finish
agree. The original projection and the printed anchor remain traceable.

With Lev1's saved Detection partition and fresh Estimation responses,
three drawer fronts are 498 × 227 mm and three drawer bottoms are
600 × 478 mm. V04's external caption `4` binds 40 mm to the right
upright. The 39 mm seat and 36–37 mm ribs use 40 mm as a construction
assumption. The left upright remains a separate 30 mm projection.
The saved catalogs produce one 40 mm veneered MDF demand with two
allowance sheets and no exact catalog price. Lev1's materials subtotal
is 3,493.42 ILS excluding VAT, with four allowances. The estimate
continues to report open coverage findings.

A Lev2 repeat kept nine Blocks, two lift-up fronts and five drawer fronts.
The different heights in its vertical stack remain distinct. The fresh
repeat yielded 110 Parts rows and is not an exact match to the historical
107-row witness.

An Adda repeat kept all 133 rows for the corner object and reported 25
rows for the straight object. Front tagged two mirror contours on V02
for the straight object, which produced three Blocks instead of the two
in the accepted witness. This happened before Parts and remains open.
The three archived 9.12–9.14 Lev1 estimates still replay with their
original ten purchasing lines and 2,923.99 ILS self cost excluding VAT.
Estimation 9.15 remains a local candidate pending the Adda review.

## Estimation 9.14 production checkpoint

The owner accepted the Materials interface and the Lev1 material-cost
repeatability checkpoint on 2026-11-13, work 3.17.4.6. Tag
`estimation-v9.14-checkpoint` pins the runtime and rollback point
`14605a4bdb999952ea7fc10a3ca9de6a4bba43ff`. Railway deployment
`c04a13d9-ab7e-4314-b4f2-8b18f7c82291` reported success for this commit.

The three fresh production uploads use the same `Lev_1.pdf` with SHA-256
`56bfa63e0236c85a161a2fa95a8996b03003df8f2f01d54ac4236acb5a7287b8`.
Each Detection run assigns `P01.V1` through `P01.V6` to one object with
identical view bounding boxes. Each estimate has three Blocks, the same
28 part rows by role, dimensions and quantity (54 total units), ten
identical purchase lines and zero unpriced requirements.

| Local time (Israel) | Version | Run | Detection cycle | Detection tokens in / out | Detection API | Parts Check | Estimation tokens in / out | Estimation API | Parts Check to saved Material Plan |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 17:28 | 9.12 | `run_5a5362fcee2d445888bfab457f0ce5a2` | 42.546 s | 23,993 / 4,392 | $0.086973 | 49.277 s | 50,768 / 4,086 | $0.213594 | 30.717 s |
| 17:45 | 9.13 | `run_22aed17fe86e4cae8ea006fb4c266a98` | 43.872 s | 23,993 / 4,546 | $0.088079 | 61.536 s | 51,044 / 4,931 | $0.227097 | 30.877 s |
| 18:09 | 9.14 | `run_339be39b989242669a24ce9d2b631d20` | 51.091 s | 23,993 / 4,706 | $0.090442 | 52.187 s | 50,761 / 3,384 | $0.203043 | 34.131 s |

Detection tokens and API cost include deferred Naming. Cost includes
Mistral OCR at $0.004 per sheet. The Detection cycle timer ends before
Naming, which finished 54.459 seconds after the start of the 9.14 cycle.
Each Parts Check recorded five Sonnet 4.6 requests with zero cache reads.
Detection plus Parts Check API cost was $0.293485 on 9.14.

| Purchase | Source | Unit | Quantity | ILS per unit | ILS excluding VAT |
| --- | --- | --- | ---: | ---: | ---: |
| MDF 50 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| LDSP 36 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| LDSP 37 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| LDSP 39 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| LDSP 40 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| Furniture leg | Assumption Fallback | piece | 1 | 200 | 200.00 |
| 600 mm roller runner | Israel Reference | piece | 3 | 96 | 288.00 |
| HDF 6 mm | Israel Reference | sheet | 1 | 104.91024 | 104.91 |
| LDSP 17 mm | Israel Reference | sheet | 2 | 295.84512 | 591.69 |
| LDSP 20 mm | Israel Reference | sheet | 2 | 286.944 | 573.89 |

Materials cost 2,758.49 ILS excluding VAT. Assumption Fallback accounts
for 1,200.00 ILS. Consumables add 137.92 ILS and packaging adds 27.58 ILS.
Paint consumables are zero. Self cost is 2,923.99 ILS excluding VAT and
3,450.31 ILS including 526.32 ILS VAT. None of the three plans has a
manual purchase override. The three plans stay in Review with 31, 28
and 29 open findings, respectively. The earlier 9.11 Lev1 run
`run_f837297d641e489880b162626eaf5916` had 55 part rows and a saved manual
purchase quantity of 60 runners. The acceptance covers repeatable Lev1
pricing across the three recorded runs. The outstanding material choices,
part counts and older divergence remain tracked in TODO.

Private archive `backups/estimation-v9.14-lev1-production-checkpoint-2026-11-13/`
contains the source PDF, exact Detection and usage events, immutable
File Review inputs, Parts Check reports, original plans and object totals,
catalog and policy replay inputs, a Git bundle, a receipt and SHA-256
checksums. The replay recalculates each saved report with the archived
catalog and settings. It matches every purchase line, the part signature,
the per-requirement costs and the published totals. It verifies Detection
against the saved partitions and bounding boxes.

## Estimation 9.14 Materials quantity edits and display

Purchase Unit and Unit Price wrap to two lines. The quantity fields are
wider and display whole values (positive quantities below half a unit show
`<1`). The preview and saved plan keep the exact quantities.

Editing Purchase Quantity changes only the purchase and its cost.
Editing Required Material returns that row to calculated purchasing,
including when a manual purchase was already saved. A manual purchase
entered after a required edit still wins for that draft. The browser
updates immediately; Save sends one batch. The material engine accepts
the canonical piece unit for Assumption requirements as well as catalog
requirements.

The saved Lev1 Assumption sheet rate is 200 ILS per sheet, an allowance.
The separate LDSP 17 mm and 20 mm Israel Reference lines cost 295.85 and
286.94 ILS per sheet, respectively. Material selection is unchanged.
Local Chrome verified both edit orders and persistence on saved Lev1
at 1280 px and Adda at 390 px. The focused suite passed 83 tests.
Authenticated production interaction remains open.

## Estimation 9.13 Materials unit price and quantity editing

Materials shows the price per purchase unit as a read-only column
between Purchase Unit and Purchase Quantity. Formula rows show no unit
price. Quantity inputs are narrower and keep the centered alignment.

The 9.12 preview rewrote untouched purchase fields using a baseline that
existed only after JavaScript initialization. With those attributes
absent, the saved Lev1 control reproduced the blank fields in Chrome.
The server now renders each editable field with its baseline. The local
preview only restores a purchase input when the preview previously
changed that field. Preview and batch save behavior remain the same.
Chrome verified the repair against the missing-baseline reproduction on
saved Lev1 at 1280 px and Adda at 390 px, including two edits in one save.
The focused suite passed 82 tests. Authenticated production interaction
remains open.

## Estimation 9.12 Object Detail draft and save

The owner’s Lev1 purchase edit saved successfully in 9.11 but held all
material inputs for 42 seconds while the plan rebuilt. In 9.12, entering
a quantity updates a local cost preview and leaves the page in place.
Save changes sends the whole draft once, and the server reconciles the
preview without replacing the input nodes. A failed save keeps the draft.
Required Material previews use the current stock format; the saved plan
still owns catalog selection and exact packing.

Purchase-only saves update prices and allocations from the existing plan.
Changes to Required Material rebuild the material plan from the saved
Parts Check, with no recognition calls. Neither path changes the Parts
rows. The Lev1 material selection and part-count audit is separate.

The focused suite passed 82 tests. Local Chrome used the saved Lev1
estimate at 1280 px and the saved Adda estimate at 390 px. Both verified
no request during input, draft persistence after a failed save, continued
editing during a save, and preserved input nodes. Adda also verified the
updated shared purchase in the second object. Authenticated production
interaction remains open.

## Estimation 9.11 Object Detail material edits

Required Material and Purchase Quantity have centered headings and values.
Leaving either field saves the changed value and refreshes the affected
purchase rows, formula costs, VAT and object totals. Required Material is
the net demand for this object; Purchase Quantity is the shared purchase
amount for the estimate. The Material Engine uses the published Parts Check
and existing purchase rules. It makes no model calls and does not rerun
Parts Check. An unchanged edit triggers no rebuild.

The saved Adda control exercised both fields in Chrome, using the real
Material Engine and local persistence fixtures. Checks covered 1280 px and
390 px alignment, keyboard and pointer blur, a failed rebuild and retry,
and the shared purchase after navigating to the second object. The focused
suite passed 81 tests. The rollback
tag is `estimation-v9.10-checkpoint` (`b86906d`). Authenticated production
interaction remains for the owner to verify on an editable estimate.

## Estimation 9.10 Object Detail Materials and Elements

Materials displays panel stock before glass and mirrors, followed by
other materials, hardware, LED, and the locked formula rows. Required
Material uses a common numeric alignment and shows the piece unit only in
Purchase Unit when both units are pieces.

Elements opens a table with the same styling as Materials. Its rows group
the same part role and dimensions, including thickness, across all Blocks
of the object. Estimated dimensions retain their indicator, and incomplete
panel sizes remain separate. The saved Adda estimate rendered 14 and 56
rows from 24 and 133 Parts rows with the same total quantities. Local
Chrome checked both objects at 1280 px and 390 px, keyboard and pointer
interaction, purchase quantity editing, and return with unsaved edits.
The rollback checkpoint is `estimation-v9.9-checkpoint`.
The focused suite passed 33 tests. Railway confirmed production commit
`b86906d`, deployment `820051af-38bd-4498-ad3d-32e19a33c9a5`. The
owner's production screenshot confirms the reordered Materials and the
collapsed Elements section. Tag `estimation-v9.10-checkpoint` pins this
runtime before changing the material editors.

## Estimation 9.9 Objects Estimation review and subtitles

Advance the Estimation release number in the runtime and this record for
every production Estimation release, including small interface fixes.

The owner reported that Review stayed disabled for a ready object after
returning from Object Detail. The completed table used prefetch readiness
to disable the link and had no refresh to observe the pending read finish.
Review now follows the object estimate status. Object Detail reuses a
finished prefetch or makes its normal authorized read with a loading
indicator. The subtitle uses the main facade stock by allocated area and
includes LED, mirror and glass boxes only when present. The self-cost cell
shows the same amount without the approximation sign.

Local Chrome with the saved Adda Material Plan verified both navigation
orders with cold, warm and failed prefetch, mouse and keyboard use, narrow
layout, the running object state, and return after a failed detail read.
The focused suite passed 32 tests. Railway confirmed Estimation 9.9 at
`d291888`, deployment `b82b99c5-8b53-42d5-a952-43f047b970c1`. On 2026-11-13
the owner confirmed Review works on production Adda and accepted the
Objects Estimation changes. The screenshots also capture the existing
Materials and Elements presentation. Tag `estimation-v9.9-checkpoint`
pins the accepted runtime for rollback.

## Estimation 9.8 stock inheritance

Work 3.17.4.6. Parts uses the printed material and finish for an individual
panel when an indexed leader binds it to that panel. A hidden mirror backing
inherits the object's carcass stock when there is no local specification.
Plinth pieces inherit the object's facade stock unless an explicit part
callout specifies another material. An explicit local thickness wins. A
local note with matching facade material and finish can inherit its stock
thickness, with both sources retained. Front reads material callouts in the
existing component request. The rollback reference is `c705688` (9.7).

Adda verification combined one fresh Front component request with frozen
remaining provider responses. Front read the plywood and finish note at
`view-002:A04`; the native leader terminates on panel contour `C04`. The
straight panel and both plinths priced as 18 mm plywood, and the hidden
corner panel as 16 mm plywood. The replay retained 157 Parts rows (24 and
133). Pricing against the active catalogs yielded 11 sheets of 16 mm
plywood, 3 of 18 mm, no LDSP, and no Assumption Fallback. Purchase cost:
9,810.51 ILS excluding VAT, down from 10,363.92 ILS in the owner 9.7 run.
An autonomous repeat from the same saved Detection evidence used nine new
model responses and reproduced the same material selections, Parts counts
and purchase total. The seven relevant test modules passed (69 tests).
Railway reported a successful production deployment for commit `7cf9207`,
deployment `5db90e3c-01fe-4fd3-80c5-920090a87375`.

Fresh production Upload `run_9dddd6c9088945c08c234e2597f2f7e2` produced
estimate `run_9dddd6c9088945c08c234e2597f2f7e2_estimate_20261113120235`
with a new Detection event. Both groups exactly matched the accepted
partition: V02/V03/V05/V07 for the straight object and V01/V04/V06/V08
for the corner cabinet. The straight object's displayed name was
`Vanity unit`. Parts Check 9.8 completed in 96.5 seconds and published
157 rows (24 and 133), matching the 9.7 role and quantity counts. Both
plinths and the straight backing used 18 mm plywood, with the latter bound
to `view-002:A04` and `C04`. The corner backing used 16 mm plywood.
Twenty demands received catalog prices, with zero unresolved requirements
and zero Assumption Fallback. Purchase cost reproduced 9,810.51 ILS
excluding VAT. Both objects remain in Review for open Parts findings.
The straight shelf, additional corner plinth spans and LED power supplies
remain outstanding.

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

The owner authorized a production Israel Reference position for two-sided
P2 LDSP, 20 mm. Its typical rate is 98 ILS/m², interpolated one third of
the way from 96.20 ILS/m² at 19 mm to 101.60 ILS/m² at 22 mm. Both anchors
share the 2400 × 1220 mm catalog format. The live loader returned the new
position. A saved Adda replay matched it, but the current sheet calculator
accepted the 2850 × 1000 mm panel on that 2400 mm stock by area alone.
Treat this allocation as invalid until the engine checks the physical fit.

The Parts-to-Demand audit accounts for all 149 source rows. 62 entered
the ten requirements. The remaining 87 were recorded only as review items
and skipped: 43 unresolved stock notes, 24 glass-box holds, 14 dimension
gaps, five LED holds and one unsupported role. Missing mirror thicknesses
never reached the live 4 mm mirror default. The runtime also disables the
priced estimator allowance for requirements which reach Material Engine.
Replace this handoff systematically. Preserve each identified part and its
source, separate missing attributes from identity, and expose assumptions
and true duplicates for review. Do not bypass review using per-role
exceptions. Israel Reference already contains 5 m LED strips, drivers,
2 m recessed and surface-mounted profiles and a diffuser. An experiment
showed that the electrical family's empty pricing key and default can
select cable for a strip unless the catalog identity is preserved.

### Estimation 9.6

Every identified part becomes a material requirement. Missing information
is kept with its source and can be filled from a matching dimension, an
owning block span, or an approved catalog default. Unresolved material or
stock goes to priced Assumption Fallback. Duplicate evidence remains under
review so it is not costed twice. Exact material name evidence constrains
catalog matching before pricing. Sheet candidates must fit the part in a
permitted orientation. A total computed with open findings is marked
provisional on Objects and the estimate retains Review status.

Verified with the saved Adda, Lev1 and Lev2 inputs and live catalog data:
all 149, 28 and 110 Parts Check rows, respectively, reached priced
requirements. Adda's three mirrors used the 4 mm catalog default,
tempered glass resolved to Israel Reference, and ambiguous LED strip
requirements received allowances instead of cable prices. The 2850 mm
LDSP part used a format allowance. Lev2 retained three shelves and the
400 ILS cutout service. The replay verifies costing and the published
status contract. A fresh authenticated Upload is pending.
