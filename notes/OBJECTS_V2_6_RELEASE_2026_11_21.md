# Objects V2.6 release

Status: owner-requested follow-up, candidate under full verification.
Rollback/runtime base: Object Details V2.5,3493a84a. Its accepted Objects V2.4
checkpoint remains intact. No new work block or hierarchical number assigned.
Build: `objects-v2.6-b20261121162542-metrics-estimation-v3.2-detection-v8.4.29`.

Scope: compact R1/R2/... technical metrics, fixed right disclosure arrow, bounded
one-line overflow; correct premature timing receipt retention; confirmed Set
Prices green, clear two-stroke checkmarks; aligned Excel/PDF frames with grey
unavailable and green/red available format colors. Export availability is not
implemented or changed. No additional user notices or controls.

[verified] Pre-change deterministic replay: ready10s, active20s, ready35s
incorrectly remained10s. EstimationCycle.observe returned its first frozen
total before reconsidering the current rows, and the renderer showed remembered
R readiness even for a currently running row. The correction revokes stale
timing/readiness, preserves failure completion and observes the new terminal
frame. Empty rows no longer prove completion. This is UI telemetry only.
The historical trigger in owner run535bdac5fa14cc6bbbf7c6885c32109 is unknown;
no production project data or new paid calculation was used to infer it.

Original numeric input/price writes, confirmation callback/basis, proposal,
Object Details, transition controller/auth and calculation/status publishers
remain protected. Set button color derives from the existing stage2 completion
state, including its existing input-event invalidation. Markers use scoped CSS
strokes rather than font glyph rendering. Existing metrics disclosure runtime
is unchanged. No new observer, timer, callback, request or persistent write.

Focused verification:79 timing/workflow/navigation checks and a browser Objects
flow pass. The focused browser retained1440/2536 geometry,48 boundary probes,
original saved prices/generation failure/retry/PDF URL. Ten metrics fit inside
950.64px;40 entries stay within960px with local overflow. Arrow right edge stays
1200px in both cases. Excel/PDF frames both start253px; unavailable icons share
rgb129/122/128, available PDF uses180/59/70. Full exact-commit gates and actual
served version/protection checks follow. Synthetic data is not production
owner acceptance. Private evidence: `.ui-artifacts/objects-v26-release/` and
the retained focused probes.
