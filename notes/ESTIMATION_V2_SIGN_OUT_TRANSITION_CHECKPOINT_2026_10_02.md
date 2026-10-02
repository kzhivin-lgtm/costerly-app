# Sign Out transition production checkpoint, 2026-10-02

## Acceptance boundary

This checkpoint protects the authenticated production path:

`Upload or Profile -> Sign Out -> Login`

The owner confirmed that Sign Out again returns to Login quickly and cleanly.
This is a transition-readiness contract, not a change to authentication,
session persistence, Fast Resume, estimation, pricing, or workflow behavior.

## Non-negotiable readiness contract

For `upload_to_sign_out` and `profile_to_sign_out`, the gray wrapper may reveal
Login only when Login sends target `app-ready` with
`metadata.auth_css_ready === true`.

At that point the wrapper must:

1. Remove exactly that pending transition and clear its timeout.
2. Record `browser.transition_styled` with `source: "target_app_ready"`.
3. Call `revealInternalTransition("target_app_ready")` immediately.

The wrapper must not require a `transition-styled` message from the originating
Streamlit iframe. A Sign Out rerun can destroy that iframe before it sends the
message, making the wrapper stay gray until its 10-second timeout despite an
already styled Login form.

Changing this rule requires an explicit replacement readiness contract,
automated regression coverage, and repeated authenticated production acceptance
for Upload Sign Out and Profile Sign Out. Reverting `d3e83bd` without such a
replacement reintroduces a known production regression.

## Root cause and correction

`4d06044` generalized the workflow rule that waits for a source-side
`transition-styled` signal to all masked transitions. That inadvertently
included Sign Out and replaced Login's already sufficient target-side
`app-ready + auth_css_ready` signal with a dependency on a source iframe that
can no longer exist.

`d3e83bd fix sign out transition readiness` restores the narrow Sign Out
exception. It does not weaken the protected workflow transitions.

## Verification

- Production trace before correction:
  `2d902e88-ca7e-41b9-9d72-ca2e0ea372ce` showed Login ready in 1.381s and
  0.815s, followed by transition timeouts of approximately 15 seconds.
- Production trace after correction:
  `03368f6c-b4b0-48aa-9a08-f61a2ac6403a` recorded repeated Sign Out at
  1.217s and 1.318s. Both emitted `browser.transition_styled` from
  `target_app_ready` and had `auth_css_ready=true`.
- Automated suite: 854 passed, 26 dependency warnings.
- Regression test asserts both protected Sign Out transition names, target
  auth-CSS readiness, timeout clearing, telemetry source, and immediate reveal.
- Owner accepted the live production result.

## Protected behavior

- Login is never revealed merely because its DOM exists. Its auth computed-style
  readiness contract remains mandatory.
- Generic workflow transitions keep their destination-control readiness rules.
- Browser session clearing on Sign Out remains unchanged.
- Fast Resume remains separate and unchanged.
- Estimation Engine, Resolver, Labor Engine, pricing, persistence, statuses,
  routes, and calculation formulas remain unchanged.

## Dirty worktree preservation

The pre-existing dirty `notes/TODO.md`, `.streamlit/`,
`db/sql/3_15_4_israel_global_catalog_v1_parts/`, and `tmp/` are deliberately
outside this checkpoint commit.
