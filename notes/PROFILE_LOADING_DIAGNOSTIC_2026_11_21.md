# Profile Loading: diagnosis and proposed correction, 21 November 2026

Original owner scope: diagnose Loading after adding a worker and propose a fix.
That diagnostic iteration changed no application source, canonical tests or
deployment. The evidence below retains that boundary.

Subsequent owner instruction21November2026 explicitly approves only this
mechanism repair, preservation of protection, all mandatory local/GitHub checks
and publication with a new deploy number. Implementation is now active as
[Objects V2.7](OBJECTS_V2_7_RELEASE_2026_11_21.md). The V2.6 checkpoint stays intact.

## Checkpoint and original evidence

- Runtime remains `82d5502689d83dfc8b75f3d41f50e350334c2815`, Objects V2.6.
- Records checkpoint `1a1b8f7f12872f5ca60a251a433e615594998642` and both published
  checkpoint tags/archive remain intact.
- CI `44950510955`, job `136987180726`, stopped in `profile_save.mjs:135`,
  Add Worker -> Pricing Cost, waiting 10 seconds for correlated account-ready.
  Its saved fixture DB contains the added worker. Pricing Cost was rendered
  behind Loading, with no reported application exception.
- The V2.4 first local timeout stopped at the same test line and symptom.
  Those historical reports contain no controller candidate/frame timeline.

## Confirmed mechanism

[verified] `screens/company_profile.py:5600-5615` accepts the employee write,
sets the success/reset state and reruns the Profile fragment. The new Labor
render shows Worker added at line5237 before finishing its body and enqueueing
ready. An immediate tab switch can overlap this completion with Pricing Cost.
The existing ready component also repeats its ready call after120ms
(`ui/js_guards.py:1512-1515`).

[verified] `ui/workflow_transition.js:441-478` replaces its current ready
candidate on each distinct run ID. It disconnects the observer and cancels
`transition.frame`, but does not clear that handle. `schedule()` only requests
a frame if that handle is empty. Two distinct receipts before the old frame
executes can therefore leave no scheduled check and a permanently truthy
handle. Duplicate retries for the same candidate return immediately. Loading
remains despite a single correct, nonstale target render and completed server work.
The test times out at10s; the unchanged UI has its own15s recovery deadline.

[verified] Resetting the cancelled handle alone fixes only one order: a late
older receipt can still replace the current candidate, leaving an observer
waiting for a render ID that is no longer in the DOM. Also, account-ready alone
does not distinguish the intermediate Labor render from selected Pricing Cost.
The existing `metrics.profile_tab` can disambiguate them without a new message field.

[verified] The same cancellation block exists in the accepted V1.3.3 tag,
`estimation-labor-v1.3.3-2026-11-17`. It was not introduced by V2.6 layout.
[unknown] What precise timing first triggered each historical failure.
[likely] This reproduced race explains the historical Profile symptom; their
exact receipt order cannot be proven retroactively from the retained logs.

## Bounded verification

All experiments use the existing local synthetic fixture and original Profile
UI/handlers. No paid model call or production project/DB access.

1. Unmodified ordinary Profile Save replay passed. A fresh replay with CPU6
   throttling only around Add Worker also passed. Neither pass disproves a race.
2. Controlled execution of the unchanged controller reproduces the overlap
   failure. A reset-only proposal is insufficient for reversed receipt order.
3. In a real browser, hold the genuine worker-ready receipt, then deliver it
   immediately before genuine Pricing-ready. Unchanged production controller
   reproduces the same10s failure/screenshot. The added worker is persisted,
   Pricing's sole marker is current/nonstale, no stale nodes remain. Observed
   frame327 is scheduled then cancelled, with no replacement check.
4. A proposed controller exists only as a diagnostic source string, substituted
   into local fixture module memory. With the same injection, the full original
   Profile Save scenario passes, including writes/reopen for Overhead, Pricing,
   Contacts, Bank Details, Machinery, employee addition and member removal.
5. The final proposal also checks existing `metrics.profile_tab` against the
   selected native tab. It passes the same real-browser scenario and all7
   applicable controller cases: delivery orders, ready-before-DOM, stale-DOM,
   wrong run and an intermediate worker render for another selected tab.
   The full17-case comparison also includes unchanged/reset-only controls.

Evidence under `.ui-artifacts/`:

- `profile-timeout-diagnostic/`, `profile-timeout-diagnostic-cpu6/`: ordinary
  replays, ready/DOM/server observations, saved local fixture state.
- `profile-timeout-diagnostic-overlap/`: unchanged-controller controlled failure,
  screenshot, receipt/frame timeline and DB receipt.
- `profile-timeout-diagnostic-overlap-proposal/`: initial receipt-pool browser pass.
- `profile-timeout-diagnostic-overlap-proposal-v2/`: final proposed tab-aware
  variant, full Profile Save pass, same fault injection.
- `profile-ready-order.json`, `profile-ready-order.mjs`:17 comparative cases,
  including7 checks of the final proposal and unchanged/reset-only controls.
- `profile-ready-pool-proposal.js`: diagnostic proposal, not application source.
- `profile-timeout-diagnostic.py`, `profile-timeout-observer.js`: reproducible
  local fixture runner/observations and explicitly marked fault injection.

## Proposed repair at the diagnostic boundary

Keep one DOM observer and one pending frame check per active transition. Store
the ready receipts by run ID instead of replacing/cancelling a candidate on
every arrival. Pick the receipt matching the actual current render marker and,
for Profile, the selected tab using the already supplied profile_tab metric.
Require the same nonstale target and two stable frames before revealing.
Clear this transition's resources on completion/failure as before.

The proposed change is confined to existing ready coordination and its regression
tests. Preserve the current regional/full-screen cover, callbacks/input handlers,
worker writes/cache invalidation, auth/tenant/protocol/origin checks and deadlines.
Do not add polling, waits for the user, background requests or fail-open behavior.
The mandatory regression must force both receipt orders, not retry until green.

The owner subsequently approved implementation/publication. The 17-case
comparison and diagnostic Profile Save pass are not a full nine-suite gate or
production acceptance. The approved release must still pass the complete
local/exact-SHA GitHub gate, protected publisher and actual Core/wrapper checks.
Publication status is recorded in the linked V2.7 release, not inferred here.
