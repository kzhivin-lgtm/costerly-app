# Labor V3.3 timing audit and V3.4/V3.5 Project progress

Scope: owner request after the full accepted V3.3 checkpoint. Historical timing
evidence and optimization proposals. Project-progress implementation was approved
28November2026 and is tracked below; navigation/caching/costing remain unchanged.
Exact accepted runtimea077dd84 and records25dd8bcf have independent immutable tags.
The three-line PDF refinement3136a583 is separately published and verified.

## Labor V3.6 published,28November2026

Owner approved the complete selected customer-loop package. Published runtime9ce04226 builds on
the V3.5 checkpoint; detailed scope, before/after, tests and rollback are in
[V3.6 release record](LABOR_V3_6_TRANSITIONS_2026_11_28.md). Later triage/proposal
sections below retain the analysis history, not current publication status.
Object preparation now includes Labor/Overhead and gates Review per Object;
pending work is reused, quantity/access/invalidation remain enforced. Existing
Project/File Review prepared paths remain; cold File Review reads overlap only
after ownership. Local pending Naming/Preview/Identity skip futile durable reads;
canonical terminal publication is preserved. Startup shows Loading until actual
ready; simple approval retains valid caches. No new AI run/schema/costing policy.
Exact clean1212/6subtests/all10 GitHub gate502.571s, local full648.274s and four
network-blocked frozen controls passed. Normal publisher, actual main enforcement,
Railway/Pages and served Core/executed-wrapper parity verified. Owner real
production speed acceptance remains pending.

## Current transition triage, owner clarification28November2026

The V3.5 full accepted checkpoint is complete. Owner asks for the actionable
list now, not further exhaustive measurement. No runtime optimization is applied
by this report. Owner explicitly requests a visible loading screen in place of
the blank grey startup mask. Show truthful immediate feedback using the existing
shell through actual readiness, without invented percentages, premature reveal
or extra polling. Include first entry, normal/hard reload, deploy refresh and
session restoration. This expands historical recovery-only request3.15.26.

[verified] Latest explicitly matching Core/wrapper observations: File Review to
Project0.543s(V3.5,n1), Processing completion to File Review4.241s(V3.4,n1),
Sign in to working screen4.581s(V3.3,n1). Most remaining ordinary-route values
below are older observations, not fresh V3.5 guarantees. Historical raw526-event
set contains383 explicit matches,88 mismatches and55 absent Core markers;
missing Core must not be inferred from wrapper version. Profile aggregate
timings cannot be attributed to each individual tab pair.

| Decision | Route/family | Evidence | Bounded next action |
|---|---|---|---|
|Work first, P1|Initial entry, normal/hard reload, post-deploy refresh, session restore|V3.5 normal reload Login4.088s and Upload3.391s; older Project reload19.631s(V3.2)/27.741s(V3.3), each n1. True hard reload and linked deploy-refresh duration unknown.|Immediate visible loading feedback first. Separately split bootstrap/auth/context/render to reduce real delay.|
|Work, P1|Last Estimate from Upload/Profile/All Projects; Project Back to File Review; Processing completion to File Review|Older Last Estimate14.450/11.688/4.602s; Project Back4.729s; latest Processing completion4.241s.|Shared File Review loader: ownership first, avoid duplicate reads, fetch only required fields and reuse valid scoped data; independent reads may overlap after ownership.|
|Work, P2|Project Review to Object Detail|V3.2 3.969s,n1; server0.782s, much of remaining time after server.|Trace client delivery/component/ready chain. Existing parallel detail reads already exist. Preserve quantity freshness and complete-screen cover.|
|Work, P2|Object Detail APPROVE to Project|V3.2 3.346s,n1; approximate2.313s before main rerun.|Split draft/save/cleanup/return; remove proven duplicate work while preserving atomic approval and existing committed receipt.|
|Validate before repair, P2|Sign in; New Estimate from Object Detail/Profile; current All Projects page entry|Sign in4.581s,n1; slower New Estimate samples are older or missing build attribution; All Projects predates V3.3 redesign.|Obtain current route-specific breakdown before acceleration. No blanket navigation rewrite.|
|Leave alone now|File Review Continue to Project; Project New Estimate; Object Detail Back|0.543s(V3.5),0.877s(V3.2),1.319s(V2.19), respectively, each n1.|Preserve accepted behavior.|
|Leave alone now|Warm Profile tabs; usual Profile entry|Tab group20 observations0.548-1.505s,median0.715s(V2.21). Entry examples0.719-1.617s on older builds.|No new tab caching/lazy-loading system; these already exist.|
|Leave alone now|All Projects native hierarchy expansion and existing PDF download|Hierarchy expansion is local, without server rerun. Persistent download slowdown not reproduced.|Preserve Partner/Project/File/Calculation/Version hierarchy and current download.|
|Leave alone now|Project calculation progress|Owner accepted V3.5 real cycle, minor70/71 pauses and93-to-ready jump nonblocking.|Do not reopen accepted counter refinement.|
|Lowest, P3 deferred|All Admin entries/tabs/returns|Historical entry6.395-8.345s; separate dashboard SQL probe5.228s.|Only after customer paths. Target expensive aggregates when resumed.|

Complete supported route families, grouped rather than duplicating every pair:

- Header: sources Upload, Processing, File Review, Project, Object Detail,
  All Projects, Profile, Admin. Conditional actions Admin, Profile, All Projects,
  New Estimate, Last Estimate, Sign out comprise41 source/action edges. The older
 106-row inventory below omitted five Processing header edges. Processing has
  Admin/Profile/All Projects/Last Estimate/Sign out, with active-work protection.
- Workflow: Upload to Processing; Processing to File Review; File Review Back to
  Upload and Continue to Project; Project Back to File Review and Review to Object
  Detail; Object Detail Back and APPROVE to Project. Processing/calculation job
  duration is separate from the final page transition.
- Profile: every ordered pair between Overhead Expenses, Labor Costs, Pricing
  Cost, Machinery, Price Lists, Contacts, Bank Details and Users (56 pairs,
  role-dependent). Save is a separate action wait, not page navigation.
- All Projects: page entry, local Partner/Project/File/Calculation/Version
  expansion, available saved-route opening and historical/latest PDF download.
  Treat a saved-route opening as its actual File Review/Project/Object Detail
  destination, not a new parallel navigation system.
- Auth and links: Sign in/out, registration/invitation, confirmation, password
  recovery, terms/company setup where required, saved File Review/Project/Object
  Detail deep links, browser back/forward where supported, Privacy Policy.
  No fresh attributable speed evidence for all exceptional auth routes; leave
  them alone absent a defect, do not describe them as measured fast.
- Startup/recovery: fresh entry, ordinary reload, Command-Shift-R cache-bypass,
  safe post-deploy refresh, deferred refresh during active work/unsaved edits,
  long-idle restoration, reconnect, expired/revoked session and retry after error.
- Action waits retained separately: File Review metadata save, Profile Save,
  Object Detail Preview/Save, Set Prices, Generate with first download, repeat
  Download Proposal/red PDF action. No current evidence warrants changing their
  accepted persistence/versioning behavior merely to shorten a cover.

[verified] Blank startup is an empty outer app-loading-mask with hidden iframe.
The8s fallback reveal is not actual readiness. Existing outerHTML revalidation,
immutable cached/gzip Core assets, preconnect, lazy Profile and parallel Object
Detail reads are already implemented. Adding them again is not an optimization.
One Core-build event triggers safe/deferred deploy refresh; preserve this policy,
authentication and pending-work guards. Do not introduce version polling.

[hypothesis] Cold Project work is partly amplified by the full UI build being
included in labor-basis identity. Exact contribution versus context I/O is unknown.
Changing this cache/costing contract requires a separate owner-approved before/
after proposal and full dependency/replay checks, not a quick startup-feedback fix.

Fresh evidence is in /private/tmp/labor35-transition-analysis (aggregate technical
timings and two own anonymous startup traces only). Anonymous reload is not an
authenticated Project measurement or true Command-Shift-R. No paid calculation,
new PDF, production input edit or database mutation was required.

## Owner-selected customer loop,28November2026

Latest owner refinement supersedes the broader triage order above. Active plan:
Project -> Object Detail first; Project -> File Review; Last Estimate -> File
Review; terminal Processing -> File Review; APPROVE -> Project. Ordinary Back
to Project1.319s and File Review -> Project0.543s are excluded from current
repairs and remain regression controls. Admin remains last. These are proposals;
no runtime/cache/navigation patch is applied here.

Owner-approved design requirement for the plan: complete and validate the
object's presentation snapshot before Review becomes available, accepting a
short additional preparation phase at the end of the long calculation instead
of making every subsequent click wait. Target approximately0.5s from click to
interactive Object Detail, not an already-proven guarantee. Prepare each object
independently using existing bounded prefetch and refresh paths, consume
in-flight work rather than duplicating it, and preserve current access, quantity,
write-order/failure/retry and freshness checks. Data preparation alone does not
prove that Streamlit DOM/ready delivery meets this target; measure both.

Use immutable source/company/run identity for reusable File Review content;
quantity and mutable calculation state remain dependent data with scoped
invalidation. A quantity change must not redownload an unchanged source file.
Optional progressive presentation loading is allowed only for noncritical
elements, never incomplete price/quantity state or prematurely enabled actions.
The plan does not introduce another cache, router, worker or polling system.

[verified] Current Project -> Object Detail path already prefetches snapshots
and loads independent projections concurrently. However,
screens/object_detail.py:_load_object_detail_or_render_error pops an unfinished
prefetch, calls cancel(), then starts load_object_detail_data again. Cancellation
cannot stop an already-running Future. Thus a Review can overlap an existing
read with a duplicate read. Proposal: consume the exact target's in-flight work
instead of duplicating it, with existing ownership, quantity-write ordering,
freshness validation, error recovery and invalidation. Never wait for other
cards. Current evidence proves the code path, not its frequency or the seconds
saved. The V3.2 ready total3.969s contains only0.782s server work; investigate
client delivery/DOM completion too. Do not remove complete-screen ready guards.

[verified] Processing seeds File Review from its just-persisted result already.
Project Back already supplies a company/run-scoped File Review snapshot.
File Review Continue already uses a prepared Project launch plan. Recommending
these mechanisms as new fixes would duplicate accepted work. Latest final
Processing -> File Review4.241s is a handoff after the job, not the job duration.
Proposal: split remaining durable Naming/identity restoration, saved-estimate
route/launch preparation, previews, complete rendering and ready delivery;
reuse only still-valid accepted results in the existing paths. No earlier100,
partial screen exposure or another polling system. Keep the fast Continue
path0.543s and extend its current prepared-state behavior only where measured
slow cases bypass it.

Last Estimate cold entry still uses ownership followed by three serial run,
object and usage reads. Proposal: preserve ownership first, overlap independent
reads, narrow usage/preview projections and avoid repeated original-file download
when immutable source identity is unchanged. Reuse existing ready snapshots for
warm entry. Project Back's older4.729s cannot be assumed to represent today's
already-cached return; current-code verification is required before changing it.

Object Detail -> Project separates Back1.319s from APPROVE3.346s (older builds).
Back should consume valid existing Project state. APPROVE must persist first;
reuse the existing committed-result/cache merge approach for Project row and
dependent totals, avoiding proven duplicate reloads. Shared material allocations
must remain coherent. Existing atomic save/approve is not replaced by a new RPC.

Rare top-left loading surface: owner rejected Please wait and defers further
identification until screenshot/URL. Current Updating app surfaces are normally
centered. releaseDeployCover clears flex styles before the160ms opacity fade;
this may allow a brief top-left label during cover release, but no reproduction
was completed before the owner stopped this investigation. Exact identity and
font mismatch remain unknown. Owner permits a confirmed correction in the next
deployment; do not claim this hypothesis is already fixed or ship it alone.

## Evidence and limits (historical audit)

[verified] Existing production app_runtime_events were read directly. The first
seven-day extraction contained287 completed transitions; November history was then
included,526 completed events in total. Event builds/dates stay separate. Statistics use the most recent Core/wrapper build pair
per route, not a mixture of old releases.88 historical completed events have
different Core/wrapper builds, so grouping by wrapper alone would be misleading. One observation is not a p95 or SLA.
There were no duplicate trace/transition keys in the seven-day287-row sample.
V3.3 contained no completed ordinary navigation transitions at initial extraction,
but did retain startup/Project render and successful Generate metrics. Most last
ordinary customer observations are V3.2 on27November. UI fixture timings are
synthetic and are not substituted for production numbers.

The user opened an authenticated in-app browser. Authenticated Upload was visibly
verified. The control tool could read the page, but click/keyboard/coordinate
input failed before dispatch. This is a blocker to the fresh automated click
matrix, not evidence that the app's Profile button failed. The user is not asked
to perform the matrix manually; previous database records remain the audit basis.
No credentials, new paid estimate, approval, input edit or new PDF version was
needed for these read-only probes.

## Last recorded normal transitions

| Transition | n | Median s | Range s | Build | Last observed (Israel) |
|---|---:|---:|---:|---|---|
|Project -> File Review|1|4.729|4.729 - 4.729|labor-v3.2|27 Nov 17:14|
|File Review -> Project|2|0.627|0.579 - 0.676|labor-v3.2|27 Nov 17:22|
|Project -> Review|1|3.969|3.969 - 3.969|labor-v3.2|27 Nov 17:24|
|APPROVE -> Project|1|3.346|3.346 - 3.346|labor-v3.2|27 Nov 17:24|
|Back -> Project|1|1.319|1.319 - 1.319|labor-v2.19|26 Nov 12:43|
|Project -> New Estimate|1|0.877|0.877 - 0.877|labor-v3.2|27 Nov 17:19|
|Upload -> Last Estimate|1|14.45|14.45 - 14.45|labor-v3.1|27 Nov 14:57|
|Profile -> Last Estimate|1|11.688|11.688 - 11.688|labor-v2.21|26 Nov 23:21|
|Processing -> File Review|1|8.706|8.706 - 8.706|labor-v2.21|26 Nov 17:28|
|Profile tabs (aggregate)|20|0.715|0.548 - 1.505|labor-v2.21|26 Nov 17:36|

The full CSV inventory enumerates every ordinary header source/action pair,
workflow transitions,56 ordered pairs between eight Profile tabs and separate
startup/recovery classes. Missing samples are explicit, not fabricated. Header
controls are conditional on role, saved-route availability and active screen;
Stay/Leave, revoked access, errors and active processing are separate conditions.
Profile target names are redacted by the browser metadata sanitizer: /file/
also matches the word profile. Therefore an aggregate Profile distribution cannot
be honestly relabelled as a per-tab or per-pair measurement.

## Where the visible time goes

[verified] Latest V3.2 ordinary client measurements27November:
- Back to File Review4.729s: server3.550s, including screen render3.540s.
- Review3.969s: server0.782s, screen render0.516s. Approximately3.011s remains
  after server completion, including delivery/DOM/ready stabilization.
- APPROVE return3.346s: approximately2.313s before main rerun, server0.256s,
  and0.777s after it. Before-rerun time can include persistence/callback/transport.
- Continue saved estimate0.579-0.676s, server0.017-0.047s; this is already fast.
- New Estimate0.877s has incomplete server breakdown, do not invent zero server time.
Pre/post splits compare client/server epoch clocks and are approximate, not pure
CPU measurements. Browser transition totals and server spans are measured on
one clock each. No exact subcause is assigned to an unsplit gap.

[verified] V3.3 cold/restored Project had server15.753s, including screen render
12.388s, auth access1.387s and session refresh1.077s. Later same-session renders
were0.016-0.017s server time. These are render/startup samples, not ordinary
click-to-ready transitions. Ready-message delivery had one6.141s sample;
other delivery samples were18-25ms. Do not blame the overlay without accounting
for those different paths and asynchronous browser scheduling.

[verified] Read-only current Admin dashboard SQL RPC took5.228s for five company
rows. This is a DB probe, not a full browser transition. Its repeated aggregations
are a concrete server-side target. File Review's saved run has15 usage events,
about139606 raw JSON bytes; excluding provider_response leaves117625bytes.
Removing only provider_response saves around16%, not an explanation of all delay.

## Project progress

[verified] Runtime persists15% before Parts Check and70% after Parts Check/report
publication. prepare_sheet_layout already calculates materials/nesting inside
Parts Check, before the70% mark. The existing timer moves15 toward45 in1.2s
steps, then caps. It cannot display intermediate actual progress that the worker
does not report. The70 branch advances toward95 at3s per point.

[verified]13 saved successful cycles, based on request aggregate start/finish,
object seed creation and first plan creation, place Parts Check completion at
84.87-88.45% of seed-to-first-plan time (median86.27%). Long phase64-120s,
then11.1-21.8s remain. First plan created_at is immutable on ordinary upsert;
updated_at was not used because later edits can move it. These are proxy phase
boundaries, not a captured exact70%-paint timestamp or complete UI-ready time.

Owner approved28November2026: move the current70 boundary to90, not95,
and add completed internal-stage receipts. Continuing work3.17.4.6 within Labor
V3.4 (owner requested version increment), no new hierarchical work block. Published build:
labor-v3.4-b20261128072035-project-progress-detection-v8.4.29.

Implementation: existing Parts Check/pipeline/material publisher receive an
optional synchronous callback. It only updates the existing process-local progress
store. Initial15 and post-report90 retain the same durable-write count and path.
Existing1.5s fragment and percentage interpolation are unchanged, no requests/timers/
workers/model calls added. Provider concurrency, requests/prompts/schema, model
cost, cost math, cache identity, layouts and proposal bytes are unchanged.

Completed milestones: inputs15, source geometry20, parallel understanding45,
front/locators60, checked original-sheet inventory75, deterministic block
geometry80, checked Parts85, material selection/layout88, published Parts Check90,
demand lines94, assumption follow-up96 (including its existing isolated failure),
allocated object costs98, final persisted project plan99. Percent remains an
estimate of work, not a guaranteed remaining duration. Existing interpolation is
bounded below the next milestone. Running values are clamped to99 even with
malformed/missing timestamps; final usable costs/Review replace the indicator.

A generation token rejects late old-worker receipts. Monotonic per-object state
rejects duplicate/backwards updates without resetting the interpolation timestamp.
All objects in the active batch share stage receipts, not only the last object.
The active overlay holds prematurely terminal allocation rows until final plan
persistence, including another tab in the same process. Finishing closes stage
receipts; consuming the Future retains existing cache invalidation/overlay cleanup.
Old in-process snapshots cannot replace a completed saved result after finish.
Errors retain Failed and technical-failure behavior, never a false success.
Cache-hit reports skip completed extraction phases rather than replaying them.

Initial local checks:1188 Python checks passed22.660s; four frozen material controls
Lev1/Lev2/Adda/Fresh Lev2 V3.3 passed with network blocked and identical purchase
signatures, unresolved requirements and immutable input reports. Existing browser
Calculation now drives20/45/60/75/85/90/98/99 through a real local worker, checks
monotonic painted frames, no premature100/Review and final saved readiness. The
fixture intentionally makes allocations durable while holding the final result.
[verified] Publication completed28November2026. Runtime997a4a33, exact clean
GitHub run46120888622/job140904985107:1188checks/6subtests/all10 suites485.604s.
Artifact15253569006 digest8a43d2e3c70ff0513bc904f32397ffbd4efdd5acabcb9fac2c1884f8b9a076be
matched downloaded ZIP/CRC/clean SHA and every suite. Local full551.732s preceded
the owner-requested public increment; version-only60 checks and browser refresh
22.683s then passed. Actual strict/trusted/no-bypass ruleset27499066 and publisher
verified, main997a4a33. Railway89aa6b9a/deployment8126262000 and target Pages
140907471437 succeeded. Real Chrome07:34:57UTC Core/executed wrapper/meta/version
all match V3.4, health200/ok, zero exceptions. Existing legacy Workers Builds
integration was still in_progress07:34:30UTC, outside this repair. All evidence:
/Users/qb/Documents/ChatGPT/Costerly/outputs/labor-v3.4-project-progress-20261128/.
Working-source882files/5164658bytes backup CRC/every-byte/5MiB-cap verified.
Its71 unrelated TODO lines remain excluded from runtime/records commits. No paid model
run, production calculation, new quote or schema mutation. Owner acceptance on
an actual next calculation remains pending, distinct from fixture and deployment
evidence. Earlier unissued3.3 candidate was superseded/cancelled for the explicit
public V3.4 increment. Counter rollback must be a forward gated revert preserving
the3136a583 PDF refinement and issued history. No force-push or test weakening.

## Download observation

[verified] One existing issued PDF was signed/read, never regenerated. Link
resolution485ms. Real isolated Chrome clicks completed at1362/438/73ms, first
popup at1297ms; all186582 bytes and SHA256 match on every download. This isolates
storage/browser transport, not a complete authenticated app click measurement.
The first generated download helper uses a temporary anchor without _blank;
repeat footer/secondary links use _blank. A separate tab is therefore expected
on repeat and was observed. No persistent long delay was reproduced.
Proposal: reuse the existing no-popup download path for explicit repeat clicks,
preserving modifier-key behavior, signed-link expiry/retry, browser download,
unchanged bytes/version and no server rerun. This requires a bounded interaction
matrix; do not change the whole navigation system to address it.

## Prioritized optimization proposals

1. Cold Project: load_objects_estimation_data reads objects/overrides/plan/
   settings serially, then _ensure_full_object_costs loads additional context.
   The labor basis includes the global LABOR_BUILD_VERSION, so a visual-only
   deployment invalidates it. Separate semantic costing version from UI build
   only through an approved cache-identity change, with explicit input/settings/
   machinery/quantity invalidation and old checkpoint replays. First measure
   context reads, unchanged writes and actual recomputation independently.
2. Last Estimate / Back to File Review: profile the cache hit/miss, three serial
   run/objects/usage reads and preview downloads. Preserve the already-rendered
   run snapshot; parallelize only independent reads after ownership check, and
   project the metadata actually needed. Payload trimming alone is insufficient.
3. Review: investigate DOM/component delivery and target-ready delay, not just
   SQL. Object Detail already loads three independent projections in parallel;
   proposing that same parallelization again would add no improvement. Retain
   continuous shielding until the matching ready marker, no cosmetic timeout cut.
4. APPROVE: split draft read, save/approval, draft cleanup and cache merge before
   changing persistence. Preserve acknowledgement, stale-write rejection and
   quantity/input correctness. The pre-rerun gap is not screen-render time.
5. Admin: inspect the5.228s aggregate RPC plan/indexes/windows and repeated reads.
   Agree freshness explicitly before any cache; preserve live role revocation.
6. Profile: separate cold tab data from normal warm tabs. Preserve fragment/header
   behavior and tenant-scoped caches. A narrow technical-metadata whitelist can
   retain enum tab/timing fields without allowing filenames or private content;
   keep existing metadata limits and negative privacy tests.
7. Keep already-fast Continue/New Estimate and native All Projects history
   expansion unchanged until current evidence identifies a regression.

Acceptance for any optimization: compare the same cold/warm route and data,
click/callback/read/write/render/ready/visible times, multiple runs and failures,
continuous cover, one ready-correlated rerun, owner/role/company isolation,
pending inputs and current saved-estimate reuse. Preserve full release gate,
exact Core/wrapper builds, existing checkpoints and an isolated rollback.

Authoritative request state remains in notes/TODO.md, not a second backlog here.

## Full route inventory

Blank timing means no attributable sample. Every numeric observation retains its
Core/wrapper build pair in all-route-inventory.csv. Historical values do not
claim a fresh measurement of V3.3. Profile pair timings cannot be reconstructed
from redacted target-tab metadata.

| From | Action | To | Last median seconds | n |
|---|---|---|---:|---:|
|Upload|Profile|Profile|0.964|2|
|Upload|Admin|Admin|8.345|1|
|Upload|All Projects|All Projects|n/a|0|
|Upload|Last Estimate|File Review|14.45|1|
|Upload|Sign out|Login|n/a|0|
|File Review|Profile|Profile|n/a|0|
|File Review|Admin|Admin|n/a|0|
|File Review|All Projects|All Projects|n/a|0|
|File Review|New Estimate|Upload|0.613|1|
|File Review|Sign out|Login|n/a|0|
|Project|Profile|Profile|1.617|1|
|Project|Admin|Admin|n/a|0|
|Project|All Projects|All Projects|1.363|1|
|Project|New Estimate|Upload|0.877|1|
|Project|Sign out|Login|n/a|0|
|Object Detail|Profile|Profile|1.507|1|
|Object Detail|Admin|Admin|n/a|0|
|Object Detail|All Projects|All Projects|1.07|1|
|Object Detail|New Estimate|Upload|5.181|1|
|Object Detail|Sign out|Login|n/a|0|
|All Projects|Profile|Profile|0.719|1|
|All Projects|Admin|Admin|n/a|0|
|All Projects|New Estimate|Upload|n/a|0|
|All Projects|Last Estimate|File Review|4.602|1|
|All Projects|Sign out|Login|n/a|0|
|Profile|Admin|Admin|6.395|1|
|Profile|All Projects|All Projects|2.411|1|
|Profile|New Estimate|Upload|3.062|1|
|Profile|Last Estimate|File Review|11.688|1|
|Profile|Sign out|Login|n/a|0|
|Admin|Profile|Profile|0.864|1|
|Admin|Admin|Admin|n/a|0|
|Admin|All Projects|All Projects|1.048|1|
|Admin|New Estimate|Upload|n/a|0|
|Admin|Last Estimate|File Review|n/a|0|
|Admin|Sign out|Login|n/a|0|
|Upload|Upload file|Processing|0.001|2|
|Processing|Detection finished, open File Review|File Review|8.706|1|
|File Review|Continue to Project|Project|0.627|2|
|Project|Review|Object Detail|3.969|1|
|Object Detail|Back to Project|Project|1.319|1|
|Object Detail|APPROVE|Project|3.346|1|
|Project|Back to File Review|File Review|4.729|1|
|File Review|Back to Upload|Upload|0.618|3|
|Profile / Overhead Expenses|Select Labor Costs|Profile / Labor Costs|n/a|0|
|Profile / Overhead Expenses|Select Pricing Cost|Profile / Pricing Cost|n/a|0|
|Profile / Overhead Expenses|Select Machinery|Profile / Machinery|n/a|0|
|Profile / Overhead Expenses|Select Price Lists|Profile / Price Lists|n/a|0|
|Profile / Overhead Expenses|Select Contacts|Profile / Contacts|n/a|0|
|Profile / Overhead Expenses|Select Bank Details|Profile / Bank Details|n/a|0|
|Profile / Overhead Expenses|Select Users|Profile / Users|n/a|0|
|Profile / Labor Costs|Select Overhead Expenses|Profile / Overhead Expenses|n/a|0|
|Profile / Labor Costs|Select Pricing Cost|Profile / Pricing Cost|n/a|0|
|Profile / Labor Costs|Select Machinery|Profile / Machinery|n/a|0|
|Profile / Labor Costs|Select Price Lists|Profile / Price Lists|n/a|0|
|Profile / Labor Costs|Select Contacts|Profile / Contacts|n/a|0|
|Profile / Labor Costs|Select Bank Details|Profile / Bank Details|n/a|0|
|Profile / Labor Costs|Select Users|Profile / Users|n/a|0|
|Profile / Pricing Cost|Select Overhead Expenses|Profile / Overhead Expenses|n/a|0|
|Profile / Pricing Cost|Select Labor Costs|Profile / Labor Costs|n/a|0|
|Profile / Pricing Cost|Select Machinery|Profile / Machinery|n/a|0|
|Profile / Pricing Cost|Select Price Lists|Profile / Price Lists|n/a|0|
|Profile / Pricing Cost|Select Contacts|Profile / Contacts|n/a|0|
|Profile / Pricing Cost|Select Bank Details|Profile / Bank Details|n/a|0|
|Profile / Pricing Cost|Select Users|Profile / Users|n/a|0|
|Profile / Machinery|Select Overhead Expenses|Profile / Overhead Expenses|n/a|0|
|Profile / Machinery|Select Labor Costs|Profile / Labor Costs|n/a|0|
|Profile / Machinery|Select Pricing Cost|Profile / Pricing Cost|n/a|0|
|Profile / Machinery|Select Price Lists|Profile / Price Lists|n/a|0|
|Profile / Machinery|Select Contacts|Profile / Contacts|n/a|0|
|Profile / Machinery|Select Bank Details|Profile / Bank Details|n/a|0|
|Profile / Machinery|Select Users|Profile / Users|n/a|0|
|Profile / Price Lists|Select Overhead Expenses|Profile / Overhead Expenses|n/a|0|
|Profile / Price Lists|Select Labor Costs|Profile / Labor Costs|n/a|0|
|Profile / Price Lists|Select Pricing Cost|Profile / Pricing Cost|n/a|0|
|Profile / Price Lists|Select Machinery|Profile / Machinery|n/a|0|
|Profile / Price Lists|Select Contacts|Profile / Contacts|n/a|0|
|Profile / Price Lists|Select Bank Details|Profile / Bank Details|n/a|0|
|Profile / Price Lists|Select Users|Profile / Users|n/a|0|
|Profile / Contacts|Select Overhead Expenses|Profile / Overhead Expenses|n/a|0|
|Profile / Contacts|Select Labor Costs|Profile / Labor Costs|n/a|0|
|Profile / Contacts|Select Pricing Cost|Profile / Pricing Cost|n/a|0|
|Profile / Contacts|Select Machinery|Profile / Machinery|n/a|0|
|Profile / Contacts|Select Price Lists|Profile / Price Lists|n/a|0|
|Profile / Contacts|Select Bank Details|Profile / Bank Details|n/a|0|
|Profile / Contacts|Select Users|Profile / Users|n/a|0|
|Profile / Bank Details|Select Overhead Expenses|Profile / Overhead Expenses|n/a|0|
|Profile / Bank Details|Select Labor Costs|Profile / Labor Costs|n/a|0|
|Profile / Bank Details|Select Pricing Cost|Profile / Pricing Cost|n/a|0|
|Profile / Bank Details|Select Machinery|Profile / Machinery|n/a|0|
|Profile / Bank Details|Select Price Lists|Profile / Price Lists|n/a|0|
|Profile / Bank Details|Select Contacts|Profile / Contacts|n/a|0|
|Profile / Bank Details|Select Users|Profile / Users|n/a|0|
|Profile / Users|Select Overhead Expenses|Profile / Overhead Expenses|n/a|0|
|Profile / Users|Select Labor Costs|Profile / Labor Costs|n/a|0|
|Profile / Users|Select Pricing Cost|Profile / Pricing Cost|n/a|0|
|Profile / Users|Select Machinery|Profile / Machinery|n/a|0|
|Profile / Users|Select Price Lists|Profile / Price Lists|n/a|0|
|Profile / Users|Select Contacts|Profile / Contacts|n/a|0|
|Profile / Users|Select Bank Details|Profile / Bank Details|n/a|0|
|Login|Sign in|Upload|4.58|1|
|outside app|Initial load / deep link|resolved page|n/a|0|
|current page|Version refresh|restored page|n/a|0|
|offline page|Network recovery|restored page|n/a|0|
|current page|Session expired / revoked|Login|n/a|0|
|current page|Read failure / retry|same target or recovery|n/a|0|

## Labor V3.5 continuity refinement, owner requested28November2026

Owner accepts that V3.4 feels materially smoother, reports early1/2/3-to20+
and later50-to60 jumps, but a long visible83 plateau. Pauses are the priority;
forward jumps are less harmful. Existing work3.17.4.6 continues, public V3.5.

[verified] Read-only latest persisted cycle at07:46UTC:
run_de1804c81e2a4a39bc1def6e222a4f56_estimate_20261128073548,
object seed07:40:07.695468UTC, first plan07:41:28.041999UTC,80.346531s.
Parts aggregate starts07:40:10.777644UTC, lasts66.252252s; provider island-map
25.551s, front21.087s and front-components16.336s run in parallel, then front-role
review7.810s and original-page review11.673s. Last provider finishes07:40:57.266UTC,
about19.764s before aggregate completion, then11.012s to first plan creation.
Source: private latest-cycle.json, no new paid model or production calculation.
[likely] This is the owner's reported cycle based on timing; source/paint were
not independently correlated. [unknown] Exact duration/phase of83: V3.4 keeps
only the latest in-process receipt, not a durable phase or paint history.
The prior80-to85 band could spend its four pending integers in4.8s; that is a
verified cap mechanism, not proof that the literal83 pause was its final cap.

[verified] Each running Project fragment waited for a fresh scoped object read,
pricing overrides, material plan and company settings before rendering progress
already present in memory. Full-load cost restoration can add dependent work.
These reads are unrelated to pending percentage display. V3.5 uses the same
worker-owned accepted seed projection for pending refreshes, then the original
scoped terminal reload/error/cache invalidation. Foreign/no-owned worker and no
usable projection retain the durable path. No timer/poll/background reader is
added; the existing1.5s fragment remains. This removes a supported blocking
dependency; old telemetry does not prove its exact contribution to the83 pause.

Implementation: real weights5/8/40/50/65/66/67 then material-context74 and priced
material-plan82 before CNC layout88, saved Parts90, demand94, follow-up96,
allocations98 and final plan99. New optional material callbacks occur after
actual catalog/override reads and actual deterministic calculation. Progress
interpolation is shared and pure: real receipts catch up at2 points/second,
then variable material bands approach their next unconfirmed bound gradually.
Completion never waits for this catch-up and running percent never reaches100.
Duplicate, backwards and old/closed worker receipts retain V3.4 protections.

Pending quantities remain editable. Source inspection found that the client
could discard an accepted quantity receipt when locally restored text matched,
without a server-rendered acknowledgement. Existing polling often masked this.
The quantity renderer now carries its rendered value and the unchanged write
handler clears a receipt only when that projection matches. No new input event,
observer, writer, RPC, price math or business persistence is added. Tests retain
all earlier quantity/failure/latest-write/reopen scenarios and add an actual
accepted quantity during held progress, multiple seed renders and final reload.

[verified] Local1198/all10 passed563.632s (unit22.81s). The browser fixture rejects
any result read while its owned worker is active, holds a real material stage,
requires its visible count to advance and retains quantity2 to terminal reload.
Four frozen material controls passed with network blocked, unchanged purchase
signatures, unresolved requirements and immutable report inputs. An illustrative
80s profile using observed provider times and assumed internal splits displayed
1,2,4,5,8,...99 with largest3-point change per1.5s sample. This simulation is not
a fresh production measurement. Exact clean remote run46124285714/job140915298618
passed1198/6subtests/all10 in437.451s. Artifact15254968877 digest
dca327771ffcb9176cf1d6abcf048938c3192ec71768ead86315b75977285877 verified by ZIP
bytes/CRC/exact SHA/clean report/all suite exits. Remote Chrome1353 frames,
no backwards or premature100, largest3-point painted step; held material moves
22-to25, accepted quantity2 remains through progress and terminal reload.
Runtime4f11834c10280cded4c164e60ba06cfca397df1b published normally; actual active
strict/trusted/no-bypass main rule27499066 independently checked. Railway874568b2/
deployment8126700154 and target Pages140917696180 success. Real Chrome
08:18:57UTC Core/executed wrapper/meta/version.json parity, health200/ok and zero
exceptions. Separate legacy Workers Builds was still in_progress08:18:22UTC,
not a repair claim. Working-source882files/5172711bytes backup CRC/every byte/
unchanged5MiB cap verified (71 unrelated TODO lines excluded from commits).
All evidence: /Users/qb/Documents/ChatGPT/Costerly/outputs/labor-v3.5-progress-continuity-20261128/.
Published build labor-v3.5-b20261128075537-progress-continuity-detection-v8.4.29.
Owner acceptance on the next real cycle remains required. V3.4 runtime997a4a33
and the earlier PDF/checkpoint remain valid preserved baselines. Rollback is a
forward gated revert of only this refinement with a fresh build, preserving
issued versions, costing and all accepted behavior. No schema mutation.

## Owner acceptance and preservation,28November2026

Owner reports V3.5 real progress very smooth overall, accepts short70/71 pauses
and93-to-ready jump as nonblocking, requests the full checkpoint first.
[Accepted V3.5 preservation](LABOR_V3_5_PRODUCTION_CHECKPOINT_2026_11_28.md) freezes runtime4f11834c with882 exact
files, independently restored1198 checks/four frozen controls and the complete
release evidence. New authorized analysis must classify all transitions, include
hard reload and post-deploy refresh/grey startup explicitly, and put Admin last.
No new counter or navigation runtime change is made by these records.
