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

Published runtime, owner acceptance pending. Full local and exact-SHA remote gates, actual remote
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

Local full1098/ten passed489.997s. Remote run45820352449 on a8e3ca3a
passed1098 and nine browser suites including the repaired worker-return and
Profile cases, then failed the unchanged Prices test: it waited for row0 and
immediately counted1 rather than10 while Streamlit was still streaming the
row widgets. The artifact shows one partially rendered row at390px, not a
completed catalog. Source loops/row data are unchanged by this release. Artifact
15118501843 retained privately, SHA256
07d6e287363f7e1ace3bebfa6668ae11b1a99ede17a8e5f394bffefd81eeece0.
Test-only readiness correction waits for expected final row9 with the existing
ten-second timeout before the unchanged exact10-row assertion. Closed groups,
independent reads, reopening and all original assertions remain. No Prices
runtime edit or gate bypass. New exact-SHA full remote gate remains mandatory.
Additional scoped local Profile failure/retry witness passed11.355s for both
Pricing and Overhead: real save errors stay visible after spacing correction.

Remote run45822429477/cde91890 passed1098/navigation, then one original
File Review Privacy check sampled14.125px versus the unchanged26±2px contract
and blocked publication. The same exact application source had passed this
check in the complete local gate and the preceding remote calculation suite.
An isolated four-transition/160-frame witness at1758/390px measured stable
26.40625/26.125px, fonts loaded. Historical failure cause is not established;
no Privacy runtime or tolerance change is made. Retain failed artifact
15118433306, digestfc11ad52b020b2ab902c533f8970ff8184041692c2bc8e464198851f79f7b350.
A full fresh check is required, not a fabricated successful status. GitHub
integration and existing Git credential both reject the rerun endpoint403, so
a records commit starts the normal cumulative full gate without changing code.

## Published verification,26November2026

[verified] Runtime b7902b424c0797e4fc6ef009b5921f68ec3b4106 published via
normal tools/promote_ui_release.py after exact-SHA full UI gate. GitHub run
45823691299/job139922220098 passed1098 Python and all ten browser suites in
446.307s, clean working tree. Artifact15120056347 downloaded and SHA256 checked:
fdee7b8d41b7b02186dd7f35994b9256678f03f5a294a9f38e994c540dcaf2bd.
Local full1098/ten489.997s plus Prices ready17.568s and scoped error/retry
11.355s passed. No threshold/assertion removed; only Prices completion wait
added. The later full exact-source pass includes unchanged26±2px Privacy checks.
The isolated prior CI Privacy sample remains an unexplained observation, not
a claimed application repair or reason to weaken that contract.

Actual ruleset27499066 active/strict/trusted UI gate, no bypass actors, verified
independently after publication; remote main points to the exact runtime SHA.
Core service reports success. Browser15:16:02.733UTC verified Core, executed
wrapper, meta and uncached version.json all equal
labor-v2.21-b20261126121656-navigation-recovery-detection-v8.4.29, zero exceptions.
This was an anonymous build-parity witness, not owner-authenticated acceptance.

Owner checklist: fresh calculation, Profile then File Review while work runs,
wait away from Project, Continue shows completed results without another
calculation; File Review counters absent; Profile Save-card bottoms consistent,
Saving/Saved and errors still usable. Previous2.20 features remain protected.
Owner production acceptance pending. All private receipts are in
output/labor-v2.21-20261126; exact affected RFQ evidence remains in the incident
folder. Records-only follow-up stays on the candidate branch, no second runtime
deployment. Full2.18 and other accepted checkpoints remain immutable.

## Owner preservation request,26November2026

Owner reports generally correct behavior but says not everything checked, then
requests a full checkpoint. Acceptance is partial. Exact runtime is preserved
with independent source restoration and existing release evidence; no new paid
cycle or runtime deployment. Machinery Save Machinery and Price Lists Extract
Prices visual consistency are deferred in TODO. See the
[full preservation guide](LABOR_V2_21_PRODUCTION_CHECKPOINT_2026_11_26.md).
