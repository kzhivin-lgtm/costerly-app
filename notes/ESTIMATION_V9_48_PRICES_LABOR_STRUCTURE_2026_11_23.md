# Estimation9.48: Prices responsiveness and four Labor stages

Owner approved implementation23November2026 on accepted9.47 runtime6764b9a7,
records90478cee, existing work reference3.17.4.6. No new hierarchical work number.
Both approved steps ship as one candidate; Detection/material/Parts/provider
behavior remains unchanged. Accepted9.47 rollback refs stay intact.

## Before and after

Prices previously awaited all four independent reads and created widgets for
every open department. It now renders closed group headers before the unrelated
reads finish, prepares open contents on demand, and fills the last requested
group before other open groups. Data still warms through the existing four-worker
projection reader. No new reader pool, HTTP polling or timer. Native disclosure
callbacks record explicit intent/priority only and rerun the existing fragment.
Count-label changes alter Streamlit widget identity, so independent intent is
restored before registering a renamed widget. Active editors stay mounted when
their group is closed. Source library is also lazy and preserves open-once actions.

Labor previously contained Sheet Processing and Assembly. It now always contains
four stages: Part Production, Part Coating, Assembly, Preparation and Packing.
Existing Sheet Processing is nested in Production. Existing Block Assembly and
a read-only Additional Assembly0 are nested in Assembly. Coating and final
preparation/packing remain read-only0 as explicitly requested. No production
norms are invented or activated. Existing unknown work is not converted to0.
The saved hour keys sheet-processing/assembly and their arithmetic stay unchanged.
Only the leaves are editable; draft previews update parent rows and root Labor
without counting nested hours twice. Supplier/stock, full SC, Overhead and VAT
continue through the existing pipeline.

An explicitly in-house CNC now returns before building the alternate manual
panel-saw calculation. It was already the selected numeric route; the inactive
alternative is removed from calculation/presentation. Existing manual/no-CNC
routes remain, and source lineage/Material Plan are preserved.

## Protection and scope

Named before/after contract: notes/UI_GUIDELINES.md9.48 amendment. Earlier
UI tests remain required. The full gate adds the Prices browser suite and
focused/legacy Price Sources, sheet route and structural checks. Controlled
Prices evidence shows selected10 rows usable while290 closed rows are not
constructed and other projections are still pending. Existing Calculation
scenarios retain failure/retry/save/reopen and commercial-quantity invariance.

Preliminary failures retained: the new Prices locator initially anchored to a
summary containing an icon; the next run exposed native count-label identity
resetting open state, fixed in the actual callback/state lifecycle. Calculation
reopen needed to open the newly approved parent stages before inspecting the
retained leaf editors. Navigation geometry compares the same independent mobile
table scroll position after opening the new parents; original1px column-axis
assertions and dimensions remain unchanged. Closed-group AppTest cases now
explicitly open the group before their unchanged edit/review/pagination/source
assertions, with a real browser covering native disclosure. Local temporary npm CLI was incomplete; installed
Playwright/fsevents versions were verified against the unchanged lock instead.
No production code or lockfile was changed for that environment issue.

Full local and exact-SHA remote gate evidence, source backup and actual served
build identities are retained under outputs/estimation-v9.48/. Owner production
acceptance is required after publication; this candidate is not a new accepted
checkpoint. No paid OCR/model calls or production database writes for testing.

## First remote gate result

Exact-SHA a82c7764 remote gate passed964 unit checks and all nine retained browser
suites. The additional Prices suite reached closed cached content, but its new
assertion incorrectly required DOM detachment. CI evidence shows the rows were
already hidden. The corrected test checks native closed state plus hidden content
and retained reopen/snapshot reuse. Initial closed-group zero-row assertions,
selected-group priority and all original tests/timeouts remain unchanged.
Application code is unchanged by this test correction. Failed artifact retained
under outputs/estimation-v9.48/ci-failed-artifact.zip.
An instrumented closure timeline also confirmed that native details.open settles
after rows disappear during the rerender (about600ms locally). The test awaits
both observable conditions within its existing timeout, then verifies reopening.
No additional sleep, increased timeout or application change was introduced.
