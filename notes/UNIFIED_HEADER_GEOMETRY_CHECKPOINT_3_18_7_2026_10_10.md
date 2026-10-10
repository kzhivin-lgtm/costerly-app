# Unified Header Geometry Checkpoint 3.18.7

Status: completed and owner-accepted on 2026-10-10

Production implementation: `b8bd3b0` (`fix: anchor shared controls to header axis`)

Object Detail completion: `9bd7339` (`fix: tighten object detail header layout`)

## Accepted outcome

The authenticated action controls now use one shared document-flow header
component. The component places a title and the existing action rail inside one
local primary header container. The rail is positioned relative to that
container's title axis and right edge, rather than to Streamlit-generated
columns or the viewport.

The owner accepted the live authenticated result on:

- Company Profile
- File Review
- Objects Estimation
- Partners
- Admin
- Object Detail

The controls remain one existing Streamlit action component. Their callbacks,
authorization-dependent visibility and button keys were not changed.

## Cause and correction

The previous `3:2` Streamlit-column layout did not give CSS a reliable parent
row to align. A selector-based grid adjustment therefore had no visible effect
in production.

The correction removes that grid dependency. `render_screen_header` now emits
a keyed primary container holding both title and controls. The contextual
control CSS is locally absolute within that container: `top: 50%` aligns its
centre with the title container and `right: 0` aligns its outer edge with the
screen surface. Because the primary container is still in normal document flow,
the title and controls leave the viewport together on scroll.

## Protected behavior

- The accepted 3.18.6 document-flow scrolling behavior remains intact.
- Upload retains its established control placement.
- File Review, Objects and Object Detail retain their transition-ready markers.
- Company Profile and its accepted Price Lists callbacks, fragments, upload,
  Source, Review and catalog-loading contract are untouched.
- No DOM move, polling, observer, timer, uploader callback or client-side
  navigation path was added.

## Verification

- Syntax compilation passed for `ui/layout.py` and `styles/base.py`.
- `git diff --check`: passed.
- Focused automated coverage: `262 passed` across company access, workflow
  header and navigation-route suites.
- Live authenticated owner acceptance confirmed all six listed screens.

## Object Detail completion

Object Detail initially retained a legacy `44px` bottom margin inside the new
primary `Object:` title row. That margin enlarged the row and lowered the
action rail. `9bd7339` removes that margin only inside the shared primary
header, which places the controls on the `Object:` title axis. The live owner
check accepted the resulting navigation-control alignment.

The preview's surrounding content-card spacing is intentionally excluded from
this checkpoint. It is tracked separately as 3.18.8 so it cannot regress the
accepted shared navigation geometry.
