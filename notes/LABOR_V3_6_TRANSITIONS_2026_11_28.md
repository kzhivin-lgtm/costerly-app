# Labor V3.6: prepared Project and Object navigation

Owner approved the whole proposed transition package28November2026. Internal
names are Project and Object; existing route/storage identifiers remain intact.
Continuation reference3.17.4.6, no new hierarchical block allocated. Baseline is
the accepted V3.5 runtime4f11834c and immutable full checkpoint. Implementation,
full release checks and deployment are verified below. Production speed and owner
real-cycle acceptance remain pending.

| Scenario | Accepted change and protected behavior |
|---|---|
|Calculation terminal, Object not prepared|Keep Review unavailable until its own snapshot exists; other Objects do not wait for this Object.|
|Prepared Object, Review click|Reuse the snapshot; retain canonical quantity/access and pending-write validation. Target about0.5s, measured click to interactive screen.|
|In-flight preparation/direct route|Reuse the selected Future; no duplicate read or wait for unrelated Objects.|
|Preparation failure|Use the same action slot for retry; never enable editing with stale data or leave an unbounded disabled action.|
|Quantity/edit/Profile change|Retain existing invalidation and write ordering; stale or failed reads cannot expose an old card.|
|Project Back to File Review|Reuse the exact scoped snapshot and prepared Project state; retain deferred Naming/manual-name protection.|
|Last Estimate cold entry|Check ownership before overlapping independent reads; retain complete timing/cost/source metadata.|
|Processing terminal|Reuse saved result and avoid durable reads for still-running local deferred jobs; existing fragment publishes canonical terminal results.|
|Object Back and File Review Continue|Retain current fast paths and existing pricing freshness checks.|
|APPROVE|Persist first; simple approval keeps valid Object caches, changes involving shared allocations still invalidate/reload affected costs.|
|Startup/reload/deploy|Immediate shared-font Loading status; reveal only actual ready. Preserve safe-deploy/auth/active-work guards.|
|Old wrappers/auth/access/errors/PDF|All existing contract scenarios retained; no pricing/AI/schema/history changes.|

Use existing bounded detail executor and existing Project fragment. Preparation
starts only for terminal Objects; the existing1.5s refresh also observes pending
presentation work after a saved Project first paints. Its native interval is cancelled once preparations are terminal, without an
app rerun or changing the current screen. No separate worker,
observer, polling mechanism or write is introduced. Pending-only presentation refresh
uses the existing Project snapshot and must not reread the whole estimate.

Alternative rejected by owner: enable Review on calculation completion and make
the click load the card. A wholesale client router/cache replacement is outside
scope. Optional noncritical presentation may finish later; usable values/actions
and current-screen ready protection remain obligatory.

Verification: focused cache/concurrency/tenant/quantity/retry tests; production
screens in the retained ten-suite browser contract; exact-commit GitHub UI gate;
normal publisher; actual main enforcement and deployed Core/wrapper parity.
Synthetic performance and owner real-cycle acceptance are reported separately.
Rollback is a newly stamped, fully gated forward revert to V3.5, preserving all
issued PDFs and database history. The original checkpoint is never rewritten.

## Verified publication

Runtime9ce042267df03a99e4f916e48c1a78c4e4fd0dcf. Build
labor-v3.6-b20261128095454-prepared-navigation-detection-v8.4.29.
Exact clean GitHub run46132681718/job140941105589 passed1212 Python checks,
6 subtests and all10 browser suites in502.571s. Artifact15257703924 ZIP
1638858bytes, SHA2569c2f912f529b85d54362deb950d3e4738707209bd11038604da2ce0896c6e626,
its official digest, CRC, exact commit and each suite exit were verified.
Final local full gate passed1212/all10 in648.274s. Its dirty marker is the
protected unrelated71-line TODO addition and node_modules link, not runtime edits.
Four frozen material controls passed with network blocked and no paid calls.

Normal publisher fast-forwarded exact SHA to main only after the trusted check;
active ruleset27499066 remains strict, Actions15368-only and without bypass.
Railway c3a0fb19-2f72-4e11-bd52-abf9ae3e2d75 / deployment8127816926 and target
Cloudflare Pages succeeded. Fresh actual anonymous browser showed Loading then
Sign in; Core DOM, wrapper DOM, executed wrapper telemetry and version.json all
match. Health200/ok. Own trace f4b6f054-f6d9-488c-b8f6-24ad3b7a0b82; no credentials
or business inputs entered. Additional Cloudflare Workers Builds check is still
in_progress, as is the corresponding earlier V3.5 check. It is separate from
successful target Pages/Core and from the mandatory UI gate; do not report it
as successful. No infrastructure repair is included here.

Local synthetic Object clicks after preparation:1047ms for the changed-input
case, then205/211/198/227/213/211/213ms. File Review -> Project and ordinary Back
remain regression controls. No authenticated production0.5s acceptance or fresh
real paid estimate is claimed. Next: assess the next owner cycle using existing
technical timing logs, retaining actual query and ready boundaries.

Evidence, including failed candidates:
/Users/qb/Documents/ChatGPT/Costerly/outputs/labor-v3.6-transitions-20261128/.
All earlier checkpoints and issued PDFs remain untouched.

## Intermediate verification and discarded experiment

The first full local unit runs exposed a metrics fixture that had not modelled
presentation readiness. It now explicitly holds preparation, asserts no Review,
and retains all original first-ready/cost/later-running assertions with injected
ready snapshots. Cache invalidation remains covered independently.

The new fade test initially compared the label alone to the viewport center,
ignoring its existing Retry sibling. Its corrected invariant compares label
position before/after cover release and preserves shared-font/noninteractive
checks. It passes locally.

The original experimental completion app rerun caused a real old-wrapper
recovery regression (changed render ID during blocked navigation). It was
discarded, the original no-app-rerun assertion restored, and the pinned
Streamlit1.64 stop_auto_rerun message now cancels only the owned fragment's
interval. This is the same protocol used by the installed framework for timed
child eviction. Scoped/absent-context Python checks and unchanged old-wrapper
recovery passed. Full final local/remote integration gates remain mandatory.

Candidate843f4d75 was blocked by exact GitHub run46132019215/job140939117240.
Its Objects closing-gap failure325px was secondary to a Streamlit exception:
the fragment ID belongs to ThreadState, not ScriptRunContext. Official artifact
15258148413 digest d7eef5dd207f52dab46f7e18856a03291eaf9dc6711363d5ccfceea96e1f5196
and local server logs confirm the same cause. The helper now reads the installed
framework's ThreadState API; a real AppTest fragment additionally covers this
boundary instead of relying on a mock context shape. No geometry assertion or
timeout was weakened. This candidate was never published.
