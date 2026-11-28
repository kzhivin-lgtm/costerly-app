# Labor V3.10: owner-approved navigation package

Continuation work 3.17.4.6. Owner approves one package: full reload restoration,
APPROVE -> Project, unchanged versus saved Object Back -> Project, and purple
bold Project calculation percentages. Baseline runtime a38d7278 (V3.9), last
owner-accepted full checkpoint cb70b113 (V3.8). Existing unrelated TODO edits
and node_modules stay untouched.

Before/after: ordinary Back always marks prices dirty even if nothing changed;
after, existing valid cache opens directly, while actual Save/input invalidation
still refreshes canonical data. APPROVE retains acknowledged writes, immediate
APPROVING/green APPROVED and Done readiness, reuses returned plan and overlaps
independent context/commercial reads. Full document File Review restoration
opts into the existing bounded restore joins after route ownership. Fresh
Project restoration also uses bounded independent input reads. No earlier
ready, stale-data success, auth bypass, new poll/timer/observer or model call.

Verification matrix before implementation:
- Unchanged Back: no price/cost read, same quantities/prices/approval/PDF state.
- Saved Back: accepted edits survive, canonical totals and Review replace Done;
  failed/pending Save and unsaved Stay/Leave keep their original protection.
- APPROVE: immediate pending feedback, no success before acknowledgement,
  unchanged approved no duplicate write; plan reuse and read overlap yield the
  same cost/Labor/Overhead/pricing/PDF inputs, failures retain retry semantics.
- Full reload: owned existing routes and all data/Continue gates remain;
  foreign/expired auth/old wrapper and active-work protections stay.
- Percent styling: shared accent purple and bold, no progress timing change.
- Retain every existing Python/browser gate; compare the fixed-latency restore
  against unchanged V3.9, then exact clean CI/publisher and actual Core/wrapper.

Status: implementation active, no new publication claimed. Timeout-specific
Last Estimate hunt remains owner-deferred. Browser ready-delivery gap remains
unconfirmed and is not repaired speculatively. Rollback is a stamped forward
revert through the full gate/publisher to V3.9, preserving business data.

Initial verification: 164 focused Python checks passed. Required Python set
1246 passed plus one invalid concurrent version-stamp failure (process imported
V3.9 while files were being stamped V3.10); unchanged version-parity check passes
in a fresh process. Exact final clean gates remain required. Current focused
browser on V3.10 completes Last Estimate and full outer reload with every
canonical read, Continue ready and no Parts Check. Controlled V3.9 replay and
unchanged V3.9 replay exceeded the same15s restore bound, while V3.10
completed full reload in9.022s (Last Estimate8.546s). All required reads were
completed, no estimation launched. Full exact gates are pending. Build:
labor-v3.10-b20261128172554-reload-approve-back-detection-v8.4.29.

Bounded reads: restore uses existing2/3/4 joins, approved Labor and Overhead
use at most3 each and commercial refresh at most5 (plan/lines only when inputs
are invalidated). Groups run in existing dependency order, join on success/error,
retain client/retry timeouts, and terminate with the accepted action. No detached
worker, read loop, extra write or request frequency is introduced. Reused plan is
only the acknowledged approval result; other callers retain defaults.
