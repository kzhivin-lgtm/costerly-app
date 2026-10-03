# 3.15.23 authenticated navigation performance checkpoint, 2026-10-03

## Checkpoint status

This is an owner-accepted intermediate performance checkpoint, not completion
of 3.15.23.

Accepted production code: `a789638`.

The owner confirmed that the current transitions are sufficiently fast to
preserve as the new baseline. The remaining visible regression is that the
authenticated navigation rail is missing on File Review.

## What changed

- Internal masked transitions can close from the destination `app-ready`
  signal instead of waiting for a destroyed source iframe.
- Objects to Object Detail and Object Detail to Objects use a native Streamlit
  navigation bridge when the matching control is available.
- Destination-side scroll reset runs after the destination DOM is ready, with
  short follow-up passes to avoid Streamlit restoring the previous scroll
  position afterward.
- The latest-estimate lookup is reused instead of being repeated during the
  same render path.

## Production evidence and acceptance

Before the final repair, telemetry showed that ordinary File Review and Objects
transitions could complete in roughly 1.1 to 2.9 seconds, while visiting Object
Detail fractured transition correlation and produced 15-second wrapper
timeouts. The target Object Detail screens themselves rendered in roughly 1.8
to 3.5 seconds under a new trace, proving that the long visible wait was a
transition-lifecycle defect rather than only slow screen computation.

After deployment of `a789638`, the owner confirmed that transitions are now
sufficiently fast. Exact post-fix p50 and p95 figures have not yet been
collected, so no stronger timing claim is made.

## Verification

- complete automated suite: 884 passed, 26 dependency warnings;
- Python compilation: passed;
- `git diff --check`: passed;
- `app.costerly.ai`: HTTP 200 after deployment;
- owner production acceptance: current transition speed accepted as the next
  baseline.

## Known regression and next repair

File Review loses the authenticated navigation rail. Server telemetry had
previously confirmed that `account_controls_render` executed, so the next fix
must inspect the real rendered DOM and visibility state. It must not change the
accepted transition lifecycle, routing, authentication, or scroll reset unless
new evidence proves that one of them causes the missing rail.

Acceptance for the next repair:

1. File Review shows the correct authenticated navigation controls.
2. File Review to Objects and Objects to File Review retain the accepted speed.
3. Objects to Object Detail to Objects does not reintroduce a 15-second timeout.
4. Each destination opens at the top.

## Protected behavior

- the `d3e83bd` Sign Out target-side readiness contract;
- Fast Resume, membership verification, and browser-session clearing;
- File Review, Objects, and Object Detail business behavior;
- accepted Partners, Final Approval, Client Proposal, Pricing Cost, and
  Machinery behavior;
- current target-side scroll reset and transition timing baseline.

## Preserved dirty state

The following pre-existing untracked paths remain outside the checkpoint:

- `.streamlit/`
- `db/sql/3_15_4_israel_global_catalog_v1_parts/`
- `tmp/`
