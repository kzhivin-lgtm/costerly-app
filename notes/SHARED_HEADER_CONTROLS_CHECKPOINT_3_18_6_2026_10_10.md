# Shared Header Controls Checkpoint 3.18.6

Status: completed and owner-accepted on 2026-10-10

Production implementation: `b5bce72` (`fix: place shared controls in screen headers`)

## Accepted outcome

The authenticated navigation controls are one existing Streamlit component,
rendered in the document-flow header row of these screens:

- Company Profile
- File Review
- Objects Estimation
- Object Detail

When the document scrolls beyond a screen title, the controls leave the
viewport with that title. They are no longer an independent root-level rail
whose viewport position is managed by CSS or JavaScript.

## Cause and correction

The controls previously rendered before the active screen, as a root-level
Streamlit container. `position: fixed` held that independent container in the
viewport. `absolute` and top-offset variants could only position that same
unrelated container. They could not make it belong to a screen header.

The correction passes the existing control renderer to the active screen and
renders it in native Streamlit columns beside the title. The account callbacks,
role-dependent visibility and button keys remain unchanged. The workflow
alignment guard now makes no transform when controls are in normal document
flow.

## Protected behavior

- Upload retains its established control placement.
- No DOM moving, observer, timer or polling path was added.
- File Review, Objects and Object Detail retain their existing transition-ready
  markers and server-rendered control readiness.
- Company Profile retains its existing tabs and does not alter the accepted
  Price Lists callbacks, fragments, upload, Source, Review or catalog loading.
- The rejected fixed, top-offset and absolute rail experiments are reverted.

## Verification

- Focused automated coverage: `262 passed` across company access, workflow
  header and navigation-route suites.
- `git diff --check`: passed before the production commit.
- Production owner acceptance: the controls no longer move independently while
  scrolling. The owner described the resulting geometry as functional but not
  visually final.

## Boundary

This checkpoint closes the scrolling defect only. Any visual redesign of the
header geometry, spacing or button treatment is a separate UI task and must
start from `b5bce72`, without reintroducing root-level fixed controls.
