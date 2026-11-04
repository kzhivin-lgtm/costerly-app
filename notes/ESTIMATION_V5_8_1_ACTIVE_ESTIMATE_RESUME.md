# Estimation V5.8.1: Active-estimate resume

## Decision

File Review and Objects Estimation are two views of the same accepted estimate.
Returning while its worker is active, or in the callback-to-first-render launch
gap, must resume that estimate. It must not allocate a new estimate ID or
discard the session-only ownership receipt before a durable shell exists.

## Protected behaviour

- Unchanged File Review edits resume the current estimate, including a live worker.
- Changed edits still create a new estimate and launch request.
- A live or pending estimate first paints from already reviewed seed rows, with no
  source restore or synchronous persistence read.
- The ownership receipt is cleared only after the worker completes or when no
  worker/request exists for the current estimate.

## Verification

`tests/test_navigation_routes.py` covers completed reuse, active-worker reuse,
and the undispatched launch handoff.  The deployment marker is
`estimation-v5.8.1-resume-active-estimate`.
