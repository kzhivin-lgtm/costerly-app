# Unified Header Geometry Checkpoint 3.18.7

Status: partially owner-accepted on 2026-10-10

Production implementation: `b8bd3b0` (`fix: anchor shared controls to header axis`)

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
- Live authenticated owner acceptance confirmed the five listed screens.

## Remaining boundary

Object Detail is not accepted. Its title, action rail and right-side preview
still require a screen-specific diagnosis against the shared component's
contract. This is the sole remaining scope of 3.18.7. Do not solve it with a
new independent rail, a fixed viewport control, or an offset-only CSS tweak.
