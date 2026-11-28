# Labor V3.7: approval state and last-view reuse

Owner approved28November2026, continuing reference3.17.4.6. Published baseline
V3.6 runtime9ce04226; last fully accepted checkpoint remains V3.5/4f11834c.
Keep all accepted fast paths and protection. Only the following package changes.

|Scenario|Required result|
|---|---|
|Unapproved Object, unchanged|APPROVE remains actionable.|
|Approval pending|Immediate APPROVING feedback, duplicate submission blocked.|
|Approval acknowledged|Project Done, no false Estimating while preparing the same Object again.|
|Reopen approved Object, no edits|Green APPROVED, no repeated approval write.|
|Edit / successful Save|Existing Save/Back/discard rules; changed saved data requires Review/APPROVE.|
|Approval/save failure|No false success, keep actionable data/retry. Accepted approval and return-load failure remain distinct.|
|Shared allocation changes|Keep canonical allocation and dependent costs; merge committed receipts, preserve source/schema/preview.|
|New Estimate -> Last Estimate|Retain one valid last Project read snapshot; clear active worker/upload/confirmation identities. Canonical names and tenant checks stay.|
|Actual new upload, even same bytes|Fresh run/widget identity, no old worker or source reuse.|
|Numeric zero focused|Visually blank; untouched blur restores zero with no write or proposal invalidation. Nonzero/text/NULL semantics stay.|
|LDSP with no coating demand|Hide Part Coating; preserve calculations and genuinely eligible mixed/wood finishes.|

Extend existing caches, callbacks, input guards and transition shield. No new
worker, timer, polling, data schema, model call, material formula or navigation
system. Approval and return-preparation phases use the existing completed-action
telemetry. Baseline UI release gate, all earlier scenarios and four frozen
material controls remain required. Publish only the exact successful SHA through
the normal publisher, then verify actual Core/wrapper versions and main ruleset.
Rollback is a newly stamped, gated forward revert, never rewriting old checkpoints.

Implementation prepared. Build: labor-v3.7-b20261128111248-approval-last-estimate-detection-v8.4.29.
Verification/publishing are pending. Earlier focused cases confirmed approval
pending/reopen/changed Save, committed receipt preservation and cache/access
boundaries. The retained LDSP all-work edit scenario now omits coating, with
its expected totals reduced by the same existing150ILS labor/12ILS overhead;
separate eligible-finish coating override/payroll/reopen checks stay mandatory.
No existing gate/check was removed or weakened. Production speed/owner acceptance
remain unverified until the owner repeats the real cycle.


Final inspection found that a dirty Project must refresh durable cost basis,
material labels/partial flags and the plan revision as well as amounts, otherwise
Set Prices/Generate would compare an obsolete proposal identity. The existing
commercial refresher now has an approval-only durable-input projection, without
rerunning costs. Same-price changed-input regression coverage is mandatory.
Candidate35d62744 was not published; its local full run was intentionally stopped
for this correction. It is not recorded as passing or as a checkpoint.


Candidate154d8e22 was rejected by the mandatory GitHub gate46137564580/
140956239340. All1222 Python checks and navigation passed; Calculation's
geometry assertion still required14 visible work rows after owner-approved LDSP
coating removal left13. The correction asserts the complete exact13-key list,
retaining every geometry tolerance and eligible-finish coating test. Local full
run also observed one Review-wait timeout after completion-away; cause is not
established from its old logs. Calculation now captures DOM/route/readiness on
failure, without changing application behavior, waits, retries or thresholds.
The failed candidate is not published or recorded as passing.


The separate Calculation run reached both desktop/mobile geometry with no
repeated Review timeout, then caught a real zero-focus edge: Delete on the
already visually empty field did not emit input, so focus-only restoration
incorrectly retained a pending0 instead of returning unknown/NULL. Existing
keydown handlers now clear the focus-only marker on explicit Delete/Backspace.
No new callback or editor was added. The original unknown ->0 ->clear invariant
and Profile optional0 ->NULL scenario stay unchanged. A focused production-screen
replay passed12.901s, and complete Profile Save suite passed91.708s, total107.167s.
The isolated earlier Review timeout remains unexplained, not claimed repaired;
final complete gates and failure captures remain required.


Candidate3a4f4cc1 passed1222 Python checks, navigation123.928s and complete
Calculation155.967s locally, but its new Project-zero fixture incorrectly
changed only displayed delivery0 while its canonical local price remained39.
GitHub46138814685/140959981479 rejected the same invalid fixture. The correction
sets both the existing manual-price cache and DOM to0, verifies focus/untouched
blur without a write, then restores both and the derived summary. Runtime code
and waits are unchanged. Complete Project/Proposal suite then passed77.078s,
gate78.272s. The final exact-commit full gate is still required before publication.
