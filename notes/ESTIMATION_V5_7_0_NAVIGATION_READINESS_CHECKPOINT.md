# Estimation V5.7.0 Navigation Readiness

Status: active, task `5.7.0.1` implemented locally, pending production acceptance.

## Objective

Make internal navigation have one owner and one observable completion boundary.
An enabled destination action must eventually be backed by prepared target data,
but no browser-side recovery may destroy an existing `core.costerly.ai` Streamlit
session while that preparation or rerun is still in progress.

## V5.7.0.1 decision

`app.costerly.ai` owns browser history, initial cold-load masking and runtime
observability. `core.costerly.ai` owns Streamlit route state, authorization,
calculation and the final `app-ready` signal. The public wrapper has exactly
one live iframe and does not change its `src` for an internal transition.

The previous 900 ms `New Estimate` fallback and build-mismatch page reload both
created a competing navigation owner. They are removed. A lost callback now
records a timeout or target mismatch without replacing the active iframe.

## Route lifecycle

1. `transition-click`: browser intent, never a readiness result.
2. `transition-visible` / `transition-styled` / `transition-stage`: browser
   presentation milestones, retained for diagnosis only.
3. `new_estimate_callback_received`: confirms the native callback reached the
   core Streamlit session.
4. `transition_ready`: emitted only from the correlated `core` `app-ready`.

No milestone before step 4 may be used to start an iframe recovery or claim a
completed route.

## Protected behaviour

- Initial cold startup retains the existing neutral loading mask.
- Browser routes and durable route tokens remain unchanged.
- Authentication and all core data authorization remain core-owned.
- A target rendering exception remains visible and closes its pending browser
  transition instead of leaving a hidden iframe.
- No user or file data is placed into wrapper telemetry or browser history.

## Acceptance for 5.7.0.1

On authenticated production, repeat New Estimate from File Review, Objects,
Object Detail and Profile. Each normal case must keep one iframe, show no
second gray/reload cycle, emit one correlated `app-ready` and no
`browser.new_estimate_iframe_recovery` event. A deliberately unavailable core
callback must leave the visible session intact and produce a timeout, not a
fresh iframe.

## Local verification

- Inline wrapper JavaScript parsed with the bundled Node.js runtime.
- `py_compile app.py state/company_auth.py` passed.
- `tests/test_runtime_observability.py tests/test_navigation_routes.py`: 65
  passed.
- Full suite: 1,616 passed, 10 pre-existing failures outside this task in
  Processing handshake, Estimation handoff and material-policy expectations.
  None of their source files are changed by V5.7.0.1.

## Deployment note

Deploy wrapper and core together under build `estimation-v5.7.0`. The wrapper
intentionally tolerates a temporary build mismatch without reloading the page,
so deploy convergence must be verified by the recorded wrapper/core versions
and an authenticated interaction, not by an automatic browser refresh.

## Next task

`5.7.0.2` prepares actual route data before enabling File Review → Objects and
Objects → Review. It must not begin until the single-iframe transport witness
passes, because preparation cannot compensate for a click that never reaches
core.
