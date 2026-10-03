# Machinery Save and initial-load checkpoint, 2026-10-03

Work: 3.15.18 and 3.15.23

## Accepted Machinery outcome, 3.15.18

The owner accepted the production Machinery workflow after changing capability
answers and using the single bottom Save action. The database was confirmed to
update and the screen did not perform a full-page reload during selection.

The accepted contract is:

- selectors and detail controls update a session-scoped draft;
- the draft survives navigation among Profile tabs in the same session;
- Supabase is not changed until the owner presses Save;
- the single Save action is sufficient confirmation for changing an existing
  in-house capability to No;
- selected Yes and No states use the softer green and red treatments;
- a successful fragment rerun retains a visible `Machinery saved` notice;
- the approved Machinery capability subset and persistence model are unchanged.

The first production attempt exposed a rejected validation sequence. One row
was written before `Confirm that the capability is no longer available
in-house` stopped the remaining loop. Commit `1e1edaa` removes that redundant
barrier. The explicit bottom Save is now the confirmation.

The owner observed one screen flash after Save. It is recorded as a visual
follow-up, but did not block functional acceptance because the selected values
and database update were confirmed.

## Initial authenticated load candidate, 3.15.23

Commit `1536746` remains deployed as an active performance candidate:

- Sign In retains the required Terms acceptance gate;
- authenticated Fast Resume and later reruns do not repeat the legal release
  lookup;
- product-session activity is submitted outside the render path;
- the first Platform Admin and Last Estimate lookups run concurrently;
- no polling fragment, additional full-page rerun, or Cloudflare readiness
  change was introduced.

Five post-deployment authenticated Upload samples measured 2.911, 3.006,
2.932, 3.154, and 4.300 seconds in the browser. Four of five Python runs were
0.422-1.270 seconds; the fifth was 2.717 seconds. The owner did not perceive a
material improvement over the best earlier state, so 3.15.23 is not accepted as
complete. The remaining delay is primarily outside the now-short Python render
in the four normal samples and requires a separate transport/startup diagnosis.

The failed instrumentation experiment `b12e903` was fully reverted by
`3e2f665`. The tree after that revert matched `389cce1`; none of its added spans
or wrapper metrics remain.

## Legal follow-up

Repeated Terms lookup is intentionally removed from Fast Resume. A separate
backlog item must add a background release-version check and a blocking
in-product modal when reacceptance is required. Immutable acceptance evidence
and the mandatory Sign In gate remain protected.

## Verification

- Owner production acceptance of Machinery Save and persistence.
- Read-only production evidence showed the first rejected Save had written only
  `finish_galvanizing`; this confirmed the partial-loop cause before repair.
- Focused Machinery suite: 197 passed.
- Complete suite after the repair: 863 passed, 25 dependency warnings.
- `git diff --check`: passed.
- `app.costerly.ai` and `core.costerly.ai`: HTTP 200 after deployment.
- Accepted Machinery implementation HEAD: `1e1edaa`.

## Protected behavior

- `d3e83bd` Sign Out readiness and target-side reveal are unchanged.
- Fast Resume cookie/sessionStorage topology and hidden-sidebar component are
  unchanged.
- Pricing Cost, File Review, Objects, Object Detail, Estimation, and resolver
  behavior are unchanged by the Machinery repair.
- The untracked `.streamlit/`, Israel catalog SQL parts, and `tmp/` remain
  preserved and outside commits.

## Known follow-ups

- Remove the accepted-but-visible single fragment flash after Machinery Save
  without changing persistence behavior.
- Consider an atomic batch RPC so a future transport or database failure cannot
  leave a multi-row Save partially applied.
- Continue 3.15.23 only from measured browser/transport evidence, not by adding
  another wrapper or rerun guard.
