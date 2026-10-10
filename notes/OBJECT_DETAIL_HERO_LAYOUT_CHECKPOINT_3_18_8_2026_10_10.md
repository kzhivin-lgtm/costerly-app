# Object Detail Hero Layout Checkpoint 3.18.8

Status: completed and owner-accepted on 2026-10-10

Production implementation: `8c0eb53` (`fix: balance object detail preview spacing`)

## Accepted outcome

The Object Detail hero card now has equal vertical whitespace around the right
preview:

- The native Streamlit row gap supplies the sole 16px clearance below the
  accepted `Object:` title and navigation-controls row.
- The preview wrapper supplies a matching 16px bottom clearance before the
  Cost, VAT and Total row.

The left object name and quantity content use the same second-row origin, so
the complete detail row rises together without disturbing the accepted header
axis.

## Cause and correction

The shared header already creates a 16px gap before its second row. Object
Detail added a second `margin-top: 16px` both to the preview and the left
details block. The stacked margins made the preview look too low while its
bottom clearance remained only 16px.

The correction removes those redundant top margins and retains the preview's
bottom `16px` margin. It is a layout-card adjustment only, not a navigation
control change.

## Protected behavior

- The 3.18.7 shared `Object:` title/action-controls axis remains unchanged.
- No action callback, preview source, total, table calculation, DOM mutation,
  polling, observer or timer behavior changed.
- Responsive Object Detail rules remain unchanged.

## Verification

- `py_compile` passed for `styles/object_detail.py`.
- `git diff --check` passed.
- Focused automated coverage: `262 passed` across company access, workflow
  header and navigation-route suites.
- Live authenticated owner acceptance: “Сойдет. делай чекпойнт, задача закрыта.”
