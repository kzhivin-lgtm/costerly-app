# 3.15.25 Processing to File Review Handoff Checkpoint

Status: COMPLETED AND OWNER-ACCEPTED

Date: 2026-10-03

## Checkpoints

- Final code checkpoint: `5c322bf`
- First-render cache implementation: `267d6eb`
- Previous independently accepted documentation checkpoint: `2718a6e`

## Accepted outcome

After Processing completes, File Review opens quickly without exposing broken or
intermediate Streamlit fragments. The owner accepted the remaining gray interval
of approximately 1-2 seconds in production.

## Architecture

Processing validates and persists the Detection result, then builds the same
normalized File Review view model and stores it in the current Streamlit session.
The first File Review render consumes this cache instead of repeating ownership,
RFQ run, detected-object, and usage reads. Refresh, direct navigation, and restored
sessions continue to load the durable state from Supabase.

The completion marker waits for a bounded 120 ms handshake. The existing browser
watcher polls every 80 ms, so it can begin transition masking before Streamlit
destroys the Processing DOM and reruns File Review.

## Rejected experiment

The zero-delay handoff was rejected. It made navigation fast but could remove the
completion marker before the browser observer saw it, which exposed intermediate
Streamlit fragments. Do not restore zero delay or stack another transition guard
without new evidence.

## Protected behavior

- Detection persistence remains authoritative.
- File Review refresh and restored-session recovery remain Supabase-backed.
- File Review content and workflow routing are unchanged.
- Cloudflare target readiness, Sign Out readiness, Fast Resume, session clearing,
  and authentication contracts were not changed.
- Protected untracked `.streamlit/`, `db/sql/3_15_4_israel_global_catalog_v1_parts/`,
  and `tmp/` content remains untouched.

## Verification

- Production owner acceptance: fast transition, no visible fragments, accepted
  gray interval approximately 1-2 seconds.
- Automated suite: 899 tests passed.
- `git diff --check`: passed before the final documentation checkpoint.

## Rollback

- Revert `5c322bf` only to remove the bounded observer handshake.
- Revert `267d6eb` only to remove first-render Detection-result reuse.
- Do not roll back to the rejected zero-delay intermediate behavior.

## Successor checkpoint, 2026-10-04

`43933e5` and tag `checkpoint-2026-10-04-deferred-review-artifacts` extend
this handoff without changing the accepted 120 ms completion-marker contract.
The successor records durable publication of deferred Naming and Preview,
including a terminal Preview failure state that stops a permanent spinner. The
owner accepted the production result for three Page 23 previews, three names,
and one shared-track door system. External dimensions and Estimation output are
not part of that acceptance.
