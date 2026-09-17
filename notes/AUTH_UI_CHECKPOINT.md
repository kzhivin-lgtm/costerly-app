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

Keep browser-session persistence isolated from Sign out feedback. The accepted
transport must remain in the hidden Sidebar and must not intercept native
Streamlit clicks. Any future Auth revision must pass two consecutive
`Sign out -> Sign in -> Upload` cycles without duplicate credential entry,
stale screens, a stuck loading state, or changed Upload geometry.

## v3.0.49 boundary

The accepted Company Profile revision does not change Auth or Upload CSS. It
only suppresses the global authenticated controls while `screen == "account"`
and renders the same Sign out action inside the Profile header. Full-refresh
login persistence remains a separate unresolved architecture decision. Do not
couple it to further Profile layout work.

## v3.0.50 accepted session boundary

The isolated follow-up is accepted. Supabase access and refresh tokens are now
stored in tab-scoped `sessionStorage`, so a refresh no longer requires another
Sign in. The Streamlit component runs only inside the hidden Sidebar and never
enters the main `.block-container`; Upload and Profile CSS are unchanged. The
user manually confirmed both session restoration and preserved layout. See
`notes/AUTH_SESSION_CHECKPOINT.md` for the protected contract.

## v3.0.51 interaction boundary

The session component now reads browser storage only during bootstrap. Store
and clear commands do not return component values, so they cannot schedule a
rerun that consumes the next Profile or Auth interaction. The user confirmed
that Profile opens on the first click. Auth, Upload, and Profile CSS are
unchanged.
