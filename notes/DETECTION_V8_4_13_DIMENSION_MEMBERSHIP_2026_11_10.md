# Detection V8.4.13 dimension membership

Release title: Haiku 5.5 · Detection V8.4.13 · Strengthen same-sheet dimension membership.

Baseline: V8.4.12 production commit `e9770bd`, tagged
`detection-v8.4.12-short-fingerprint-production-2026-11-10`.

The ordinary route widens the minimum top and bottom bands for uniquely
owned dimension text from 80 to 96 OCR pixels. Core geometry and the side
bands retain their existing bounds. Widening the side band in an early
replay also admitted a sheet number, so the release change is vertical.

A same-sheet 100-point pair can use an exact common large extent if
distinct source labels prove an independent matching measurement sequence.
Rare-extent proofs retain priority. A common-extent candidate cannot
invalidate them or connect their existing components.

A short technical View can join a unique established object on the same
sheet when at least two of its Views corroborate at least two independent
exact sizes covering at least three quarters of its two to four positions.
Repeated values count once and ambiguous readings do not count. The
compiler records the chosen edge and its corroborating pairs. Ada and
Page 23 keep their existing Membership paths.

The frozen Floor 06 production witness yielded 18 to 13 groups. P06
joined V1/V2/V3, P10 joined V1/V2/V3, and P13 joined V1 through V6. The
outer 60 label entered P10.V3 and the sheet number on P03 stayed out.
The frozen 10-group Floor 07 control kept the same partition.

Private replay evidence is under `output/detection-v8413-2026-11-10/`
in the Costerly workspace. The replay reconstructs source ownership and
matches the baseline dimension inventory before varying the vertical band.
It seeds previously accepted connections to isolate new compiler joins.

The first fresh Floor 06 test (`run_24080f08c22a40bcb46ee3335dcc1d2a`)
completed OCR, Detection, and Naming. P06, P10, and P13 each yielded one
object. P03 split because a new common-extent bridge invalidated both
previously admissible rare-extent pairs. The final priority rule prevents
this regression. The first fresh test used the initial wider band on all
sides, before the final directional restriction.

With the final rule, replaying the fresh Floor 06 OCR and exact captured
provider replies produced 17 objects. Only one changed optional local
review called the provider again. P06, P10, and P13 still produced one
object each. P03 improved from nine groups to three. P04 and P07 each still
produce two. The first run took 251 seconds through Detection and save.

Fresh Floor 07 run `run_9f40aa2d6bc848bd9a773787ffc09e8b` completed with
nine objects in 109 seconds through Detection and save, and Naming
completed. The final rule replay matched its exact partition with zero
new provider calls. Discovery classified the small P11 location plan as
document context, leaving two technical Views in one object.

The final Detection/OCR file suite passed 275 tests. The broader
name-based selection had two Estimation Handoff failures that also
reproduce on the production baseline.

Release tag: `detection-v8.4.13-dimension-membership-production-2026-11-10`.
Rollback reference: `detection-v8.4.12-short-fingerprint-production-2026-11-10`.

## Production checkpoint, November 11, 2026

The owner reported 13 objects from Floor 06. Production run
`run_dce43f565ef64a47b1965bd71f97a101` verifies 13 persisted objects and
13 completed names, with one object on each physical sheet P03–P15.
OCR, Detection, Document Identity, File Review, Naming, and preview
generation completed. The cycle took 105.173 seconds through save,
including 34.7 seconds of OCR and 59.217 seconds of Detection.

Discovery retained 34 Views. Thirty technical Views entered the
published objects. The three standalone renders on P09 and the photo on
P13 each received `no_match` and were excluded from package membership.
A presentation image can enter a package through a proven relationship
to a technical View. A component made entirely of presentation images
is excluded from publication. This run verifies the exclusion path.

Floor 06 P03–P08 each arrived at Membership as one technical View.
They account for the entire 59-to-34 View inventory difference from
the earlier production witness. P09–P15 retained the same per-page View
counts. The archived 18-object replay separately verifies the P06
short-View join. The fresh 13-object run verifies the published count.
Per-island Discovery completeness and positive render attachment remain
separate checks.

The private full checkpoint is stored in
`backups/detection-v8.4.13-floor06-13-production-checkpoint-2026-11-11/`.
It contains the source PDFs, persisted production evidence, frozen
regressions, replay scripts, test output, deployment receipt, and a Git
bundle with the exact release, rollback, and checkpoint documentation.
