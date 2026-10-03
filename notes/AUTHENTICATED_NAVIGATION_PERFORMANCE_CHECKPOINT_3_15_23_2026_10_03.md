# 3.15.23 authenticated navigation performance checkpoint, 2026-10-03

## Checkpoint status

This is an owner-accepted intermediate performance checkpoint, not completion
of 3.15.23.

Accepted production code: `7c81a5a`.

The owner confirmed that the current transitions are sufficiently fast to
preserve as the new baseline, destinations open at the top, and the
authenticated navigation rail survives transitions among File Review, Objects,
and Object Detail.

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
- The workflow header alignment guard ignores stale Streamlit DOM, clears the
  preceding screen's inline transform, and aligns against the destination
  screen's explicit title selector.

## Production evidence and acceptance

Before the final repair, telemetry showed that ordinary File Review and Objects
transitions could complete in roughly 1.1 to 2.9 seconds, while visiting Object
Detail fractured transition correlation and produced 15-second wrapper
timeouts. The target Object Detail screens themselves rendered in roughly 1.8
to 3.5 seconds under a new trace, proving that the long visible wait was a
transition-lifecycle defect rather than only slow screen computation.

After deployment of `7c81a5a`, the owner confirmed that transitions are now
sufficiently fast, scroll-to-top works, and the navigation rail no longer
disappears, including after Object Detail to Objects. Exact post-fix p50 and
p95 figures have not yet been collected, so no stronger timing claim is made.

## Verification

- complete automated suite: 885 passed, 26 dependency warnings;
- Python compilation: passed;
- `git diff --check`: passed;
- `app.costerly.ai`: HTTP 200 after deployment;
- owner production acceptance: transition speed, scroll-to-top, and workflow
  navigation rail accepted as the next baseline.

## Remaining performance work

The workflow navigation regression is closed at this checkpoint. Work 3.15.23
remains active only for measured initial-load and transition outliers. The next
performance change must start from fresh production telemetry, preserve
`7c81a5a`, and vary one confirmed cause at a time.

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
