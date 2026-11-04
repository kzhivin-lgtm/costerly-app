# Estimation V5.8.2 production checkpoint, 2026-11-04

## Scope and protected boundary

This checkpoint records the Estimation navigation and handoff recovery line
inside approved task `3.17.4.4`. It does not accept the Cabinet Block,
2VN, Analyze, Calculation, material pricing or Detection quality contracts.
Those require their own object-level production witnesses.

The protected workflow is one accepted estimate per unchanged File Review:

1. File Review accepts the reviewed objects.
2. Objects Estimation starts or resumes that same estimate.
3. Back to File Review and Continue to Objects Estimation must not create a
   second estimate or abandon an active worker.
4. A terminal worker failure must present a terminal object state, never an
   indefinitely active progress row.

## Releases

| Release | Commit | Published runtime responsibility |
| --- | --- | --- |
| Estimation V5.8 | `512bf6e` | Prepare source data and navigation target readiness before controls become actionable |
| Estimation V5.8.1 | `7405e67` | Resume an active or pending estimate instead of allocating a second estimate during File Review and Objects navigation |
| Estimation V5.8.2 | `710165d` | Retry a transient blank Storage JSON response during immutable evidence-page upload and make unrecoverable handoff failures terminal |

Production returned the V5.8.2 wrapper marker
`estimation-v5.8.2-handoff-recovery`. The public core endpoint returned
HTTP 200 after deployment.

## Incident and diagnosis

[verified] The owner observed the exact error:

```
Estimation V4 handoff failed: Expecting value: line 1 column 1 (char 0)
```

[verified] The same Objects screen retained `Estimating` at a visual 45% after
the worker had already failed. The error occurred after V5.8.1 had stopped the
previous Back/Continue estimate reset.

[verified] In the prior path, a handoff exception left the worker exception on
the browser path without converting the known object rows to `failed`. The
visual 45% is the Objects screen's bounded smooth-progress cap for an early
base progress range. It is not evidence that the Estimation worker reached a
real 45% stage.

[likely] The empty JSON response came from the Storage client's response parse
while persisting the immutable full evidence page. The handoff code itself
does not parse provider JSON, and the Storage upload is content-addressed with
upsert semantics. The diagnosis is intentionally recorded as likely until a
provider-side response trace confirms the upstream blank body.

## Repair

- `use_cases/estimation_artifacts.py` retries only the bounded blank-response
  `JSONDecodeError` case, at most three Storage upload attempts with short
  backoff. The same immutable artifact path and bytes make repetition safe.
- `use_cases/estimation_runtime.py` turns a final handoff failure into
  `failed / 100%` for every known non-ignored object in the estimate.
- `screens/objects.py` preserves the terminal failure in the active browser
  session even if the same infrastructure failure prevented an immediate
  durable state refresh.
- V5.8.1 retains the current estimate identity, its active Future, pending
  launch request and prepared source access when navigating back and forth.

No retry is applied to arbitrary handoff or model failures. No Detection,
immutable input, material resolver, BOM or pricing contract was changed.

## Verification

[verified] V5.8.1 targeted navigation coverage passed: 393 tests. Its full
suite passed 1,636 tests with the same 10 unrelated pre-existing failures.

[verified] V5.8.2 focused handoff, runtime and navigation coverage passed:
403 tests. The complete suite produced `1639 passed, 10 failed, 29 warnings
in 15.90s`. The ten failures are the established unrelated baseline: one
Detection browser-handshake assertion, one Estimate material-resolution
assertion, three historical Estimation handoff preview/OCR fixtures, four
material identity/normalization/profile fixture failures, and one
sheet-material family policy fixture failure. `py_compile` and
`git diff --check` passed before the release.

[verified] The owner live-tested V5.8.1 before V5.8.2. Back to File Review and
Continue no longer reset the worker. That test exposed the distinct handoff
failure which V5.8.2 repairs.

## Acceptance still required

This is a deployed recovery checkpoint, not full interaction acceptance. Run
one fresh authenticated LF1 estimate and verify all of the following:

1. Start Objects Estimation, use Back to File Review, then Continue.
2. The original estimate ID and worker continue. No second calculation starts.
3. If Storage returns one transient blank response, evidence upload retries and
   the calculation reaches its normal terminal result.
4. If all three attempts fail, each affected row reaches `Failed`, not
   `Estimating 45%`, with the actionable bounded error visible.
5. Review and Back remain visually coherent throughout the navigation.

The last criterion deliberately remains open: prior reports of faded or broken
intermediate frames require a fresh authenticated end-to-end observation. A
passing unit suite or wrapper marker alone does not prove that UI acceptance.

## Rollback boundary

`7405e67` is the prior V5.8.1 checkpoint. Reverting V5.8.2 removes only the
bounded Storage retry and terminal handoff-failure presentation. It must not
reintroduce the active-estimate reset fixed by V5.8.1.
