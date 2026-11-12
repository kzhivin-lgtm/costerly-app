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
