# Labor V3.9: bounded Last Estimate restore reads

Continuation work 3.17.4.6. Owner approved only Last Estimate delay/timeout repair,
version update and publication after checks. Accepted V3.8 runtime cb70b113 and
runtime/records checkpoint tags remain immutable. APPROVE, Back, Processing,
ordinary File Review, Project/Object readiness, pricing math and PDF flow stay.

## Evidence and cause

[verified] Fresh V3.8 Last Estimate had four successes 2.672-7.486s and a 14.999s
failed transition. That failed request reached Python, which completed 14.214s
after start, including 13.176s File Review preparation. Ready was enqueued near
the unchanged 15s browser deadline. Exact production per-query attribution is
not available; no single slow SQL request is claimed identified.

Code traces the avoidable serial path: canonical Naming/Document Identity
publication reads, saved Project rows/price overrides/material plan, then cost
dependency context. A retained Project still refreshes canonical commercial
inputs. These required checks are independent within their read groups, but
the old path awaited each before starting the next. Ownership and any dependent
canonical-name-after-terminal reads remain ordered.

Controlled production-screen replay on unchanged V3.8 cb70b113 with fixed read
delays emitted the real native Last Estimate failure at about 15s and never
returned a correlated File Review ready. Same fixture/read work under the
candidate completed in 8.578s with all canonical read groups completed and no
Parts Check. The browser deadline, assertions and data readiness were unchanged.
This establishes the serial critical-path mechanism; it is not a claim that
production now takes 8.578s or that every possible transport timeout is repaired.

## Bounded change and protected paths

Last Estimate puts an operation marker in the existing one-shot company/run
navigation receipt. The company is captured from the existing header access;
the callback does no auth or network lookup before the normal app auth gate.
File Review consumes the marker once for the exact current company/run. A Back
receipt, direct route, Processing handoff or ordinary rerender has no opt-in.

Only that Last Estimate render joins independent Naming/Identity reads (max 2),
Project initial reads (max 3), canonical cost-context reads (max 4) and cached
commercial reads (max 3). Groups execute in the existing dependency order. Each
local executor is created per accepted click and joined before the caller
continues, including errors; running I/O retains existing client/retry limits.
No detached task, poll, timer, callback, observer or request frequency is added.
No state/widget access or cost persistence runs in the added read workers.
Ownership is accepted before each scoped data-read group. Publication/cache
reconciliation and existing cost calculations/writes remain on the main caller.

Default loader behavior stays sequential for every other caller. Existing
canonical quantities, current manual names/metadata, source/plan signatures,
Profile inputs, price/PDF invalidation and material/approval semantics stay.
In particular this does not skip cost validation or remove the existing UI-build
component from the Labor basis hash, change formulas, enable Continue/Review
early, increase the 15s timeout, or repair APPROVE/Back/startup incidentally.

## Verification state

Focused pre-existing navigation/preparation/name checks passed 97 before adding
new cases. New checks verify captured tenant/client context without worker auth
state access, ownership-before-parallel reads, exact sequential/parallel DTO
equality for cold and warm data, same cost context, read failure before writes,
pending local publication read avoidance and single-use route scope.
All 107 focused Python checks passed; the complete required Python set passed
1241 tests in 24.91s. The final version-stamped focused browser replay completed
Last Estimate in 8.481s. Navigation keeps all existing scenarios and adds the real 15s restore regression.
Synthetic fixture connections remain local-only, no paid calls or production
business-data writes are used for testing. Fixture reload/ready fixes accepted
in V3.8 remain; no further Profile changes are included.

Build: labor-v3.9-b20261128164457-last-estimate-reads-detection-v8.4.29.
Full local gate, exact clean GitHub gate, official artifact verification, actual
strict main enforcement, normal publisher and served/executed Core/wrapper parity
are required before claiming delivery. Current production speed acceptance is
pending. Rollback is a newly stamped forward revert to V3.8 through the same
full gate/publisher, preserving saved estimates and issued proposals.

Private focused evidence: /private/tmp/labor39-before/,
/private/tmp/labor39-after-bound-company/ and /private/tmp/labor39-versioned-focused/.
