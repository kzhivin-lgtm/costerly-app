# Labor V3.3: cycle progress, downloads and navigation timing audit

Scope: owner request after the full accepted V3.3 checkpoint. Diagnostic/proposal,
not an implemented change to progress, navigation, caching, security or costing.
Exact accepted runtimea077dd84 and records25dd8bcf have independent immutable tags.
The three-line PDF refinement is a separate verified candidate.

## Evidence and limits

[verified] Existing production app_runtime_events were read directly. The first
seven-day extraction contained287 completed transitions; November history was then
included,526 completed transitions in total. Event builds/dates stay separate. Statistics use the most recent build
per route, not a mixture of old releases. One observation is not a p95 or SLA.
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

Proposal: move the current70 boundary to approximately90, not95. Add real stage
receipts around geometry/evidence preparation, parallel understanding, front/
locator resolution, original-sheet inventory checks, deterministic Parts,
material/nesting readiness, result persistence and final UI-ready. Suggested
bands:0-10,10-40,40-60,60-80,80-90,90-97,97-99,100.
Percent is an estimate of progress, not a guaranteed remaining duration.
Use existing progress transport/refresh, not new timers/polls/extra model calls.
Bound display interpolation by the next phase; reject stale/out-of-order updates,
never regress, never show100 before a usable terminal result. Preserve failures,
cache reuse, parallel requests, multi-object runs and navigation-away recovery.
Weights and milestones are proposals pending a concrete implementation iteration.

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
