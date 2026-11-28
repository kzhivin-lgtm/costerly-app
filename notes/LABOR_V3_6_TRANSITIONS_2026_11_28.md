# Labor V3.6: prepared Project and Object navigation

Owner approved the whole proposed transition package28November2026. Internal
names are Project and Object; existing route/storage identifiers remain intact.
Continuation reference3.17.4.6, no new hierarchical block allocated. Baseline is
the accepted V3.5 runtime4f11834c and immutable full checkpoint. Implementation
and production speed are pending verification, not established by this plan.

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
presentation work after a saved Project first paints. It ends with one full
rerun once preparations are terminal, then has no interval. No separate worker,
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
