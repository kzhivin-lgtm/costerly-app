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

## Verification and publication

Exact runtime 0a99c988d7c4e6da2863d855e3e267c286634779, build
labor-v3.10-b20261128172554-reload-approve-back-detection-v8.4.29.

[verified] Full exact clean local gate passed all1247 Python tests/all10 browser
suites in623.977s. Exact clean GitHub gate passed the same set in550.484s,
run46170656590/job141058101839. First full candidate passed both. Official
artifact15273797699,1778015bytes, SHA256
8fd7e059658e280678fcc41cdb76f65ed0c10cf4080e213ed9dde16baf1d298f:
size/digest/CRC, clean SHA, unit count and every suite exit verified. Four saved
material controls passed with network blocked; no paid calls or schema change.

[verified] Identical fixed-latency full reload on unchanged V3.9 exceeded15s;
V3.10 completed in9.022s focused,8.973s exact local and8.427s CI. Every required
source/publication/Project read completed, Continue was ready and no Parts Check
launched. Local covered Back259ms/Approve267ms are synthetic observations, not
production latency claims. Existing approval/reopen/Save/quantity/auth/update/
blank-Project and stage timing assertions remain, plus actual purple700 style.

Focused precommit164 checks passed. One earlier Python run became invalid for
version parity when stamping files while its process held imported V3.9; fresh
unchanged parity and both complete final gates pass. The invalid original log is
retained. Initial expected stub/signature/owner-approved Back expectation updates
were completed before the first full exact candidate; no gate was weakened.

Bounded reads: restore uses existing2/3/4 joins, approved Labor and Overhead
use at most3 each and commercial refresh at most5 (plan/lines only when inputs
are invalidated). Groups run in existing dependency order, join on success/error,
retain client/retry timeouts, and terminate with the accepted action. No detached
worker, read loop, extra write or request frequency is introduced. Reused plan is
only the acknowledged approval result; other callers retain defaults.

Actual active strict/trusted/no-bypass main ruleset27499066 verified. Normal
publisher accepted the exact gate and advanced main to the runtime. Railway/
Pages rollout succeeded (Railway d680888d-3769-4119-ade8-182503c49860,
GitHub deployment8133140228, Pages check141061305513). Fresh anonymous browser
at17:42:20 UTC verified visible initial Loading then Login, matching Core DOM,
wrapper metadata, executed telemetry, version.json and health200/ok. An earlier
probe during Railway rollout correctly saw old Core and is retained separately;
only the final matching probe establishes delivery.
Authenticated owner speed acceptance is pending. Timeout-specific Last Estimate
hunt remains owner-deferred. The unexplained browser ready-delivery gap remains
unknown; no speculative browser guard repair is claimed.

Rollback: stamped forward revert through the full gate/publisher to V3.9,
preserving business data and the immutable owner-accepted V3.8 checkpoint.
Permanent evidence:
/Users/qb/Documents/ChatGPT/Costerly/outputs/labor-v3.10-transitions-20261128/.
