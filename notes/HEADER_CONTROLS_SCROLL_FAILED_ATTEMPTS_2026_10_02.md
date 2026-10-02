# Header controls scroll, unresolved follow-up

Status: unresolved. Return point requested by owner: `8b76d0a`.

Scope is limited to File Review, Objects, Object Detail, Company Profile and
Platform Admin. Upload and the authentication flow are excluded. Preserve the
accepted Sign Out transition checkpoint `d3e83bd`.

Do not repeat these rejected approaches:

- `8b76d0a`: generic service scroll guard plus Sign In transition changes. It
  did not produce the required fixed behavior and mixed unrelated auth work.
- `f25b91f`: workflow-specific pin-to-top behavior. It partially affected File
  Review and Objects, but changed the requested resting position and did not
  solve the complete screen matrix. Reverted by `8ae1595`.
- `76de29c`: globally forced authenticated controls to the viewport top. This
  moved controls away from their accepted position. Reverted by `1cc852c`.
- `15d1d2c`: measured and rewrote Upload DOM geometry. Upload was outside
  scope and the change was invasive. Reverted by `d7d2ea1`.
- `89f4370`: changed Upload controls from static to fixed. Upload was outside
  scope. Reverted by `81ecd5c`.
- `356888e`: stopped repeated workflow mutation alignment and added fixed CSS
  for Profile and Admin. Production observation showed no improvement.
- `38e8ad3`: added a guard for Streamlit `section[data-testid="stMain"]`.
  Production observation showed no improvement.

Before another patch, inspect the authenticated production DOM while actively
scrolling each scoped screen. Record the actual scrolling element, every
containing block between the controls and viewport, computed `position`, `top`,
`transform`, and the controls' `getBoundingClientRect()` before and after
scrolling. A new branch is valid only after this identifies the element that
changes the controls' viewport coordinate. Do not infer the cause from source
CSS alone.

