# Auth and Upload UI checkpoint

Date: 2026-09-16

## Accepted state

- Sign in completes from one credential submission.
- Sign out is functionally working, but its interaction feedback still needs polish.
- The shared Costerly header and accepted Upload/Auth layout are retained.
- Upload dimensions, spacing, hover, hero typography, background, and logo position remain protected.

## Root cause of the rejected branch

Commit `58eb6eb` introduced a custom browser-session Streamlit component and a
top-level synchronization gate. Its component callbacks added reruns around
authentication transitions. In the browser this appeared as a cleared Sign in
form after a successful first request and a stale Upload screen after Sign out.

Auth was restored to the runtime behavior from `23b216d`, the commit immediately
before browser-session persistence. The custom component was removed. A full
browser refresh may therefore require Sign in again.

## Verification

- User manually confirmed that authorization and Sign out function locally.
- Automated suite: 125 tests passed.
- `git diff --check`: clean.

## Protected checkpoint rule

Do not reintroduce browser session persistence while fixing Sign out feedback.
Treat persistence and transition feedback as separate experiments. Any future
Auth revision must pass two consecutive `Sign out -> Sign in -> Upload` cycles
without duplicate credential entry, stale screens, or a stuck loading state.

## v3.0.49 boundary

The accepted Company Profile revision does not change Auth or Upload CSS. It
only suppresses the global authenticated controls while `screen == "account"`
and renders the same Sign out action inside the Profile header. Full-refresh
login persistence remains a separate unresolved architecture decision. Do not
couple it to further Profile layout work.
