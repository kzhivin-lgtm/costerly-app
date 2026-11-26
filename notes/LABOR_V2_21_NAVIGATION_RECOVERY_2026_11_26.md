# Labor2.21: calculation navigation recovery and Profile spacing

Owner selected release number2.21 on26November2026. Existing work3.17.4.6.
Base runtime deb8b8fe8a572d6e84807fdc0d117e68b29e8632, records9f9417e1.
Accepted2.20 previews, Project name, Advance payment, buttons and zoom behavior
remain protected, as do prior checkpoints and the mandatory publication gate.
No paid calls, estimate restart, production writes or Detection changes.

## Incident and supported cause

[verified] Exact Ada RFQ run_b10730a250624e53a5b46a6fe0528510, estimate
run_b10730a250624e53a5b46a6fe0528510_estimate_20261126115535, company610.
File Review routeSrKJ4vnwhE-R, Project routeEiTYFdrAYzxL.
Private read-only evidence: output/labor-v2.20-incident-20261126/saved-run.json.

-11:55:37UTC: accepted Continue and worker started
-11:57:40UTC: Parts Check saved its report and provider receipts
-11:57:56UTC: Corner display cabinet terminal100%, savedSC22423.24exVAT
-11:57:57UTC: owner navigated Project to File Review
-11:58:00UTC: Vanity unit terminal100%, savedSC7064.71exVAT
-11:58:21UTC: Continue returned to Project, same browser/server session
-11:58:26UTC: Profile opened
-11:59:14UTC: Last Estimate returned to File Review
-11:59:18UTC: Continue returned to Project; screenshot retains45%/pending

Thus the worker completed and persisted both results before the stale screen.
Profile did not cancel it. No failure event was recorded for the worker.
The top-level rfq_estimates status remains pending, while terminal object rows
are the existing UI's authority. It is not evidence that Parts is still running.
No schema/status redesign is introduced for this incident.

[verified] File Review treats an unconsumed Future as active, even after it is
done, and prepares seed rows. Project consumes the done Future first, marks
its cache dirty and clears the Future. It then consumes the earlier prepared
rows, caches them while clearing dirty, and creates a non-live fragment.
Consequently the finished result is replaced by a seed snapshot and is never
read again. The same sequence is present in V5.8.1/7405e67 (4November), before
2.20; the current source diff did not introduce a worker/Parts change.
This establishes an older latent navigation race, not a new failed calculation.

## Minimal repair and verification boundary

When accepting a terminal Future, discard only a prepared navigation envelope
for that Future's estimate. Existing dirty-cache loading then obtains the saved
terminal rows before the ready screen is revealed. Keep the worker, immutable
handoff, estimate identity, scoped navigation, existing1.5s live fragment and
all pricing/calculation paths. No new timer, observer, poll or retry job.

Red/green Python reproduction: terminal success and failure, completion before
and after File Review preparation. The old source returned running45% seeds;
the repair rejects them and preserves dirty/result or terminal failure state.
A real browser fixture holds the existing worker, navigates Profile then File
Review, completes the worker there, and requires saved cost/Review on return
with exactly one worker submission. It makes no model/provider call.

File Review input counter is hidden with the established InputInstructions
CSS pattern; max_chars240 and backend validation stay intact. Profile Metrics
and Pricing had two invisible zero-height bridge slots, each contributing16px
flex gap:61px below Save versus29px normal Contacts/Bank/Labor card edge.
Remove only those layout slots, retain normal28px padding/border and real
save errors. Existing callbacks, bridge DOM, acknowledgement feedback and
fixed Privacy are preserved. Browser checks compare button-to-card bottom
against actual padding/border and retain the existing failure/retry scenarios.

## Publication state

Candidate implementation. Full local and exact-SHA remote gates, actual remote
strict/no-bypass enforcement and Core/executed wrapper/meta/version parity are
required before publication. Owner production acceptance remains pending.
Build labor-v2.21-b20261126121656-navigation-recovery-detection-v8.4.29.

A preliminary2.20-labelled local gate passed Python then was cancelled during
navigation when the owner selected2.21. No source runtime changed during that
run; it was not a failed check or publication receipt. Final local2.21 run is
independent. Previous checkpoints remain immutable. Rollback is deb8b8fe through
the same gated publisher, never a forced/unchecked main push.

The first2.21 local candidate passed1098 Python and navigation, then its new
limit test failed because it assumed Streamlit emits a DOM maxlength attribute.
Installed Streamlit1.64 TextInput/useUpdateUiValue instead enforces maxChars in
the React change handler. The test now accepts240 characters, rejects241 and
restores the original value before blur. Runtime validation was never changed.
Failed candidate6ddebe32 is not approved for publication.

The next new browser case exposed an invalid direct-submission fixture: it
called submit_prepared_estimation_job but omitted objects_estimation_future_id,
which production _start_prepared_estimation_launch always sets. A source search
confirmed these are the only submission sites. The fixture now records the same
owned estimate receipt; no assertion or production behavior was weakened.
The isolated exact completion-away scenario then passed11.072s with one worker,
saved result on the first ready return, hidden counter and240/241 boundary.
Profile measurement passed8.223s: Metrics/Pricing closing gaps reduced61to29px,
matching unchanged Contacts/Bank/Labor. Existing full gates remain required.
