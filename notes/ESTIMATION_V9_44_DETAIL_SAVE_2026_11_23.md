# Estimation9.44 Detail delta Save, totals and footer

Status: published23November2026, owner authenticated acceptance pending. Existing work3.17.4.6, same Objects workflow.
Protected baseline: runtime d41eb1275c400788e374b20fc26a9e9571d2ca17,
records4f0b7912206d167db95bcaeac06f2c917f9c936d and
estimation-v9.43-2026-11-23. Full9.41 checkpoint and earlier rollbacks remain.
Owner accepts9.43 quantity persistence but reports slow transitions, mismatched
batch/unit totals and failed Save after changing front panel material.

## Evidence and causal limits

[verified] Route3_6d38ijvhQP identifies run_186f97810a4b4506a8fe356c0d5abf9b,
estimate run_186f97810a4b4506a8fe356c0d5abf9b_estimate_20261123100439,
object-001, company610, quantity3. Stored unit net4979.21, VAT896.26, gross5875.47.
Its full-cost audit sums to14937.63 batch net. Sections already display batch;
the footer displayed the stored unit amounts. The screenshot mismatch is exactly
this quantity factor. Unit persistence is an accepted V3.1 contract, not corrupt
stored arithmetic. Card presentation now uses the exact saved batch audit and
configured VAT once; Objects keeps unit prices.

[verified] The older material editor waits for persistence, invalidates the card,
then reads a separate receipt. A controlled negative check makes persistence
succeed and that read fail: the old editor reports Save failed after the write.
The new material worker returns the already calculated receipt only after plan
persistence. The UI merges it into the existing scoped cache and acknowledges
success without that extra read. Numeric changes preserve saved Labor except when
object quantity changes. The affected material rows and dependent policy totals
are reused consistently in both cost audit and response. Norm/purchase edits are
published even when rounded purchase cost stays unchanged.

[unknown] The exact historical exception is absent from the available runtime
events. Missing quantity_basis schema and invalid front-save JSON were checked
and rejected as causes. Read-only replay plus captured writes can validate the
repair but cannot prove which transport operation failed in the owner's session.
New stage-correlated operational events distinguish validation/pricing/receipt
failures without logging exception text or credentials.

[verified] Actual event timings: cold Review8.382s (server render4.716549s,
server elapsed5.252944s), warm Review3.4868s (render0.660728s), APPROVE return
7.2518s (render3.776365s). Guarded read profiling discovers three pricing-policy
write attempts on detail load. The HTTP guard rejects every non-GET/HEAD before
transmission. No production project mutation or model call was made in diagnostics.
The proposed no-op write/read parallelisation and immutable Parts/preview cache
remain separate backlog proposals. Do not claim faster authenticated transitions
from synthetic timings or this receipt repair alone.

## Interaction and preserved behavior

Save stays on the card, becomes green Saved only after acknowledgement, and
resets on a new edit. Back confirms unsaved changes. APPROVE saves/approves and
returns. Failure retains the draft, offers Retry save on the same button and
keeps an accessible status without a visible paragraph under the actions.
No schema change, model call, timer, observer, polling or navigation system added.

Privacy stays fixed. Shared reserve72px means46px footer plus26px action gap.
Short detail cards place Self Cost and actions together at the bottom; long ones
retain the same scroll-end gap. The previously in-flow invisible material bridge
is positioned without consuming space; it remains mounted and operational.
Other screen geometry and all accepted9.43 behavior remain protected.

## Verification and release

Full local/exact-SHA GitHub gates and protected publication pass. Private
evidence is underoutputs/estimation-v9.44 in the handoff workspace. Retain real
route/events/schema/read-profile, strict in-memory write replays, baseline and
corrected detail probes. Synthetic fixture checks are not owner production
acceptance. Replay adapter/setup failures are not product failures: initial
uncaptured writes were blocked, invalid6decimal input was rejected, and Pandas
capture initially aligned dict values incorrectly. Final independent scenarios
must use scalar object assignment and a restored source snapshot per case.

Rollback only this candidate's attributable runtime changes to9.43. Stored unit
cost conventions, Detection8.4.29, source evidence and9.41 checkpoint stay intact.

Focused verification:73 related Python checks pass across five suites. The
Calculation browser suite passes50.722s, retaining its original scenarios and
adding front Save failure/retry/Back/APPROVE at quantity3. Synthetic click to green
Saved is0.435s desktop/0.430s narrow; these are controlled persistence timings,
not authenticated production measurements. Footer gap26/25.844px. Strict actual
saved-data replay independently passes load/purchase/required/front/labor, with
all mutations captured in memory. Purchase/required/front return committed
receipts identical to an independent projection, including exact row values and
batch net; JSON rejects nonfinite values. Front scenario2.301s, purchase0.809s,
required1.050s include real guarded reads, captured writes and comparison reads.
No inference/model or production mutation was run.

Final clean local605 checks/nine suites278.354s; exact-SHA GitHub605/nine354.227s,
run45163779296/job137655438915/artifact14814676984. GitHub job407s includes setup.
Published runtimefa67572a2d74db121c303667e9a68bac4b35b33f through the required
publisher and active no-bypass ruleset27499066. Core deployment7997364902 reports
success11:25:05UTC. Actual live Core/wrapper/meta/version all match9.44 at
11:26:46UTC, health/wrapperHTTP200. Release tagestimation-v9.44-2026-11-23;
records tagestimation-v9.44-records-2026-11-23. No runtime change after that gate.

Owner real-project acceptance remains pending. Do not claim live Save speed from
the0.43s synthetic writer. Existing actual cold/warm Review8.382/3.487s separates
server and browser wait; further no-op-write/read/cache options are a proposal.
A narrow390px screenshot also shows the pre-existing Object header/menu overlap;
shared header source is unchanged. Compare against9.43 before any separate repair,
not part of this Save objective or an accepted regression claim.
