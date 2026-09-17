# Auth session checkpoint

Version: v3.0.51
Date: 2026-09-17

## Accepted behavior

- A signed-in user remains authenticated after refreshing the same browser tab.
- Authentication is scoped to `window.sessionStorage`. Closing the tab clears
  the browser-held session; it is not a persistent `localStorage` login.
- Sign out revokes the Supabase session when possible, always clears Streamlit
  state, and removes the browser-held session before returning to Sign in.
- Invalid or expired restored tokens are cleared from both state layers instead
  of being restored again on the next refresh.
- Sign in and the first Profile navigation click are processed once, without a
  browser-storage callback rerun consuming the interaction.

## v3.0.51 interaction fix

- `sessionStorage` is read only while bootstrapping a new Streamlit session.
- Once bootstrap completes, the hidden component is not rendered during normal
  button or form interactions.
- Store and clear commands are fire-and-forget. They update browser storage but
  do not send a component value callback that schedules another Streamlit run.
- This supersedes the v3.0.50 transport lifecycle, which preserved refresh
  authentication and layout but could consume the first Profile click.

## Layout isolation decision

- `ui/browser_session.py` is the only bridge between Streamlit and browser
  session storage.
- The component must render inside `st.sidebar`, which is hidden by the existing
  base design. It must never render in the main `.block-container`.
- This boundary prevents the component iframe from becoming a flex child of the
  Upload layout. The rejected experiment rendered the transport in the main
  tree, changed flex geometry, and shifted the header, actions, hero, and
  uploader without changing their CSS.
- Auth persistence must not modify Upload, Profile, or Auth CSS.

## Verification

- User manually confirmed one-submit Sign in on a fresh process and first-click
  Profile navigation after the lifecycle fix. The accepted v3.0.50 refresh and
  layout behavior remains unchanged.
- Automated suite: 133 tests passed.
- Tests verify token restore/store behavior, `sessionStorage` rather than
  `localStorage`, execution inside the hidden Sidebar context, one-time
  bootstrap, and callback-free store/clear commands.
- `git diff --check`: clean before checkpoint commit.

## Protected checkpoint rule

Future Auth work may change feedback or token policy only if it preserves this
Sidebar isolation and the accepted v3.0.49 UI geometry. Any change affecting the
component location requires a fresh before/after browser geometry check.
