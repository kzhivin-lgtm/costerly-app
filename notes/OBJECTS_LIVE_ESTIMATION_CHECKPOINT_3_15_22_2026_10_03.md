# 3.15.22 Objects live Estimation checkpoint, 2026-10-03

## Accepted outcome

The owner accepted the production Objects Estimation behavior after a complete
live cycle. Objects update progressively without requiring a manual refresh or
navigation through File Review. Timed refreshes no longer dim or flash the
pricing screen.

While any object is still being estimated:

- each object shows its live progress;
- Delivery and Installation remain visible with blank values;
- Project Summary, Project Price, VAT, and Project Total remain visible with
  blank values;
- no partial project total is presented as final.

After the Estimation future finishes and every object has a terminal priced
result, stale process-local progress is cleared and all project-level values
are populated.

## Confirmed causes and corrections

The previous client-side progress runtime mutated Streamlit React-owned DOM and
could leave Objects stale. The replacement uses a scoped server-side fragment
to read persisted per-object results while the background future is active.

The first fragment implementation exposed two additional issues:

1. Streamlit marked fragment contents stale during every timed rerun, producing
   a gray flash. A CSS override now disables stale opacity only inside the
   keyed Objects live-pricing container.
2. Process-local progress could remain at an intermediate percentage after the
   persisted row reached a terminal status. Completion now clears that overlay.

Project-level values are gated independently from their layout. Their rows and
summary remain visible, but values stay blank until the future is inactive and
all object rows are terminal and priced.

## Implementation commits

- `93c2ae8` adds persisted live Objects refresh in a Streamlit fragment.
- `e3a492f` removes fragment dimming, clears stale progress, and gates project
  values on full completion.
- `8b18fc3` preserves the project-level rows and summary with blank values until
  full completion.

Accepted production implementation HEAD: `8b18fc3`.

## Verification

- Owner production acceptance: progressive updates work and the resulting
  behavior is considered normal.
- Focused Objects and Estimation checks: 32 passed.
- Complete automated suite: 861 passed, 25 dependency warnings.
- `git diff --check`: passed.
- `app.costerly.ai` and `core.costerly.ai`: HTTP 200 after deployment.
- GitHub `main` received `8b18fc3` through the established Railway autodeploy
  path.

## Protected behavior

- The accepted `d3e83bd` Sign Out readiness contract is unchanged.
- Cloudflare transition logic, authentication, Fast Resume, browser-session
  clearing, routing, and scroll behavior are unchanged.
- File Review and Object Detail interfaces are unchanged.
- Delivery and Installation remain project-level additions to sale price, not
  object self cost.
- The current Pricing Cost calculation contract remains unchanged.

## Related restored work

The current branch also contains the restored 3.15.17 Pricing Cost work:

- `878a6ce` company pricing policy;
- `669ff6b` compact Profile navigation;
- `92964cd` Bank Details-style Pricing Cost form.

Pricing Cost is visually accepted. Its remaining owner/member persistence and
calculation acceptance stays tracked separately under 3.15.17.

## Preserved dirty state

The following pre-existing untracked paths were not added, deleted, or changed
by this checkpoint:

- `.streamlit/`
- `db/sql/3_15_4_israel_global_catalog_v1_parts/`
- `tmp/`

## Next recommended task

The next P0 candidate is authenticated full-reload optimization already
recorded in `notes/TODO.md`. It must begin with instrumentation and preserve the
accepted `d3e83bd` transition contracts. It is a separate task and is not part
of this checkpoint.
