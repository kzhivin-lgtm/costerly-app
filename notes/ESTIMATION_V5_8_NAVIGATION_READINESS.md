# Estimation V5.8: Navigation Readiness

## Scope

V5.8 replaces the File Review to Objects Estimation handoff and the unchanged
Objects Estimation to File Review return. It does not change Detection,
Estimation calculation, material selection, or Object Detail calculation.

## Decision

`CONTINUE TO OBJECTS ESTIMATION` is enabled only after File Review owns one
complete readiness bundle for the exact company and RFQ run. The bundle holds:

- the immutable reviewed edits and ignored object IDs;
- source bytes only when a new Estimation worker is required;
- the target estimate ID selected before the click;
- a complete initial Objects screen payload, either reviewed seed rows for a
  new estimate or the cached/durable completed result with Object Detail route
  tokens for an unchanged estimate.

The click callback consumes that bundle. It must not reconstruct a plan, read
the RFQ source, load Object rows, or write to Supabase before selecting the
Objects screen.

The return callback retains the exact File Review snapshot that is already in
session. The next File Review render consumes it once and skips its optional
Naming, Document Identity, and Preview refreshes for that initial paint. The
existing deferred fragment remains responsible for later real updates.

## Protected behavior

- Direct URLs and refreshes still run the established ownership path.
- A changed quantity invalidates the readiness plan before it can be used.
- A running worker is never treated as a reusable completed estimate.
- New Estimate clears both V5.8 handoff receipts.
- Completed Object Detail route tokens are prepared by the existing Objects
  fragment after the worker becomes terminal, not during a Back click.

## Verification boundary

Automated checks confirm that the Continue callback only consumes prepared
state, a completed estimate can prepare without source bytes, and Back returns
the cached File Review snapshot. They do not prove browser paint atomicity.

Manual production acceptance for V5.8 is:

1. Complete an LF1 estimate and wait until its Objects state is terminal.
2. Go File Review to Objects and verify that the first visible Objects screen
   has the full prepared table, without a source-screen mashup.
3. Go Back to File Review, then Continue again. Both routes should use the
   warm session data without a five-second blank or grey stale screen.
4. Change quantity or Ignore, wait for the normal File Review rerun, then
   Continue and verify the changed reviewed data appears in Objects.
5. Refresh or open a direct workflow URL and verify normal authorization and
   durable loading still apply.

## Local verification

- `py_compile app.py screens/file_review.py screens/objects.py state/session.py
  ui/screen_transition.py` passed.
- Navigation, marker, observability, timing, and company-access suites passed:
  391 tests.
- Full suite: 1,634 passed, 10 failed. The failures are in pre-existing
  Processing, material identity, price-resolution, and Estimation evidence
  expectations. None imports or exercises a V5.8-modified navigation file;
  they are not treated as V5.8 acceptance evidence.

## Deployment marker

Core and wrapper build marker: `estimation-v5.8-navigation-readiness`.
The core screen marker exposes this value as `data-costerly-core-build`; the
wrapper exposes it through the `costerly-wrapper-version` meta tag.
