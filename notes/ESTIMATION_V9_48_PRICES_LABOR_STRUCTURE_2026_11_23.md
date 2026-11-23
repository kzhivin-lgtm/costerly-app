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

## Published release receipt

Status: published, owner production acceptance pending. Runtime
862e28f0a848d387f2cf540c34f5769c6a16a3fe. The original approved9.47 checkpoint
and rollback refs remain accepted; this release is not a new accepted checkpoint.

- Full local gate:964 Python checks and ten browser suites,420.358s,
  outputs/estimation-v9.48/full-local-04/gate-report.json. After the test-only
  closure correction, focused Prices passed both1280/390 in19.540s.
- Exact clean-SHA remote gate:964 checks/ten suites,400.189s,
  [run45220109273](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/45220109273),
  job137851749969, artifact14840671173. All nine retained suites passed.
- Existing protected publisher promoted that exact SHA to main. Actual remote
  ruleset27499066 was active, trusted Actions gate required, bypass_actors=[].
  Local checks and remote enforcement were verified independently.
- Railway deployment8005194941 succeeded. Cloudflare Pages production deployment
  48d7b621-bd3b-4684-a9aa-8d6045530f23 succeeded. The unrelated existing Workers
  Builds service is a separate check and was not modified.
- Read-only production DOM at app.costerly.ai verified executable wrapper, wrapper
  meta and rendered Core equal
  estimation-v9.48-b20261123160825-prices-labor-structure-detection-v8.4.29.
  Static version.json also returned HTTP200 with that build at16:55:50UTC.
  No owner-account Calculation/Prices interaction was performed by this probe.
- Complete source backup829files/4,742,110B, helper validation and byte comparison
  passed: backups/v9.48_prices_labor_ci_verified/. The initial archive attempt
  exceeded the unchanged5MiB cap due to a temporary compression-wrapper mistake;
  helper rejected it. Correcting that wrapper reproduced the established LZMA
  workflow; helper code, exclusions and cap were not changed.
- Retained evidence: candidate.json, backup.json, ci-job.json, ci-artifact.zip,
  ci-gate-report.json, promotion.json, deployments.json, served-builds.json,
  remote-checks-after-publish.json, local and failed/diagnostic reports under
  outputs/estimation-v9.48/. No credentials are included in these receipts.

Next acceptance: owner opens Prices and a saved Calculation through app.costerly.ai,
checks collapsed/selected groups and all four Labor stages with unchanged totals.
No paid OCR/model run is needed to verify this structural change. New numerical
coating, additional-assembly and preparation/packing work remains deferred.

## Owner acceptance and full checkpoint

On 23 November 2026 the owner reported normal production operation and requested
a full checkpoint with all project records. This supersedes every earlier
acceptance-pending statement in this chronological release record. Runtime and
build remain unchanged. The source archive, complete checks, failed candidate,
independent restore, frozen controls and final refs are preserved in the
[accepted checkpoint](ESTIMATION_V9_48_PRODUCTION_CHECKPOINT_2026_11_23.md).
Future Labor 2.x naming is recorded for the next release; historical 2.8/2.9 tags
are not reused and deployed 9.48 is not retroactively renamed.
