# Auth and Upload UI checkpoint

## v3.7.1 accepted production transition checkpoint

- Product checkpoint: `a626462`.
- The existing transition observer now releases Upload to Profile and Profile
  to Upload only after the target marker and its screen-specific computed-style
  contract pass. It does not wait for the later general `app-ready` component.
- The general `app-ready` event remains the authoritative end-of-run telemetry
  boundary. Authentication, routing, native controls, and Python-run count are
  unchanged.
- Production trace `3ae650ed-7e9e-4b15-b333-3e4691e4c227` measured two Upload
  to Profile styled reveals at 704ms and two Profile to Upload styled reveals at
  663ms and 895ms. All four transitions used one Python run.
- The previous Upload to Profile measurement was 3.650s because the wrapper
  waited about 2.97s after the target screen was already visible. The accepted
  path removes that wait without exposing an unstyled target.
- The user explicitly accepted the production speed. Company Price Sources is
  still active and is not completed by this checkpoint.

Date: 2026-09-21

## v3.6.2 accepted hard-refresh Sign in checkpoint

- Product checkpoint: `fb1ad97`.
- The user verified on production that Sign in remains fast, the spinner stays
  inside the existing Sign in button, and no partial screen appears after the
  tested hard-refresh cycle.
- The preserved Auth shell now waits for 120ms without target-app DOM changes
  before release, with a 450ms fail-open. Authentication, routing, and the
  one-Python-run Sign in path are unchanged.
- Production trace `eaf99421-c863-4886-ac74-e34f8d56298b` measured the preceding
  Sign in at 1.106 seconds with one Python run. Target visibility preceded
  app-ready by only 29ms, which showed that the former two-frame release rule
  did not establish visual stability. The trace does not identify the exact
  pixels shown by the reported fragment, so no stronger root-cause claim is
  recorded.
- Automated suite: 217 tests passed.

Date: 2026-09-20

## v3.5.11 accepted production checkpoint

- Product checkpoint: `aa05a5d`.
- The user confirmed production Sign in, Sign out, Upload, and Profile behavior
  is satisfactory. The accepted Sign in interaction keeps the existing Auth
  screen visible with the spinner inside the Sign in button.
- The preserved Auth shell is released after two browser animation frames,
  rather than on the first app-ready callback. This prevents partial target
  DOM from appearing without changing authentication or navigation.
- The first cold Upload to Profile transition remains slightly slower than
  repeated transitions. The user accepted that behavior for this stage, so it
  is not an active defect. The safe phase metrics added in this version remain
  available if cold Profile latency becomes a priority again.
- Automated suite: 216 tests passed.

Date: 2026-09-20

## v3.5.10 production working reference

- Commit `95b3bdc` preserves the one-run Sign in path and keeps the accepted
  Auth screen visible with the spinner inside the Sign in button.
- The user confirmed on production that the spinner presentation is restored
  and that the Sign in action itself is fast.
- This is a working reference, not a stable checkpoint. Two defects remain:
  fragments of the next screen can appear at the end of Sign in, and the first
  Upload to Profile transition is materially slower than later transitions.
- Production trace `2a93527c-f100-4d5f-9507-b1d4fa58b8ba` measured Sign in at
  1.041 and 1.131 seconds, each with one Python run. The first Upload to Profile
  took 2.799 seconds, while Profile to Upload took 0.691 seconds.
- Preserve the v3.5.10 Sign in behavior while diagnosing those defects. Do not
  replace the accepted button spinner or restore the rejected gray mask.

Date: 2026-09-20

## v3.3.1 accepted authenticated home

- Product checkpoint: `cf35d9b`.

- The accepted large Upload logo keeps its existing CSS, size, and position.
- The product credo remains on the authenticated home page at a compact 24px.
- Upload-only navigation is centered below the credo with compact Projects,
  Profile, and Sign out controls. Projects remains disabled until its route and
  persistence contract are implemented.
- The full below-logo composition is 32px lower than the initial v3.3.1
  candidate. The code compensates for Streamlit's 16px wrapper overlap so the
  credo-to-controls and controls-to-uploader gaps are both 32px.
- The 340px controls group keeps the complete `Sign out` label visible.
- The native uploader, drag interaction, transition markers, authentication,
  and post-upload state reset are unchanged.
- The user accepted the production presentation. Automated suite: 188 tests
  passed.

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
