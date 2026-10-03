# 3.15.23 Object Detail edit and Approve checkpoint, 2026-10-03

## Checkpoint status

Checkpoint code: `89dda51`.

This checkpoint extends the accepted authenticated-navigation baseline at
`7c81a5a`. The owner confirmed in production that Object Detail material edits
no longer collapse the Materials section to zero and that changing Unit Cost or
Quantity updates the current row Cost.

The fast Approve bridge is deployed and regression-tested. Its post-deployment
production timing has not yet been measured, so this checkpoint does not claim
a verified Approve latency.

## Accepted Object Detail edit contract

- The browser calculates only the active row's immediate Cost feedback.
- Material Cost is `unit_cost * quantity`.
- Labor Cost is `hours * rate`.
- Browser code does not recalculate whole sections, policy rows, VAT, or final
  object totals.
- Enter or blur is the persistence boundary.
- The server remains authoritative for pricing-policy rows, Materials, Labor,
  employer load, Overhead, VAT, self cost, and persisted object totals.
- Pricing-policy material rows remain locked and derived.

## Rejected approaches

Two browser-wide calculation candidates were rejected after production
acceptance failed:

1. selecting a presumed current Object Detail DOM subtree;
2. rebuilding all material totals from editable fields in the browser.

Both still caused the visible Materials calculation to collapse to zero. They
must not be restored or extended. Future calculation changes must preserve one
authoritative server calculator and use narrowly scoped browser feedback only.

## Approve transition diagnosis and repair

Production trace `28dac1ea-5c35-40aa-9109-8246a22c2078` showed the direct-link
Approve path creating a new iframe/server session. The original wrapper
transition received zero Python runs and reached its 15-second timeout even
though the destination Objects server run completed in about 1.8 seconds.

The repair reuses the accepted native Streamlit navigation bridge when the
Object Detail snapshot is clean. If edits remain unsaved, the direct snapshot
route remains as the correctness-first fallback so the edits and approval are
persisted atomically.

## Implementation commits

- `422d473`: header guard observes stale-state changes; the attempted DOM-wide
  calculator isolation was later rejected.
- `e26f0f9`: attempted browser material rebuild, rejected in production.
- `5b17f63`: removed the duplicate browser-wide calculator and restored the
  server-authoritative save and recalculation path.
- `5fb491a`: added current-row live Cost feedback and Enter-to-save behavior.
- `89dda51`: added the clean-snapshot Approve Streamlit bridge and retained the
  unsaved-snapshot fallback.

## Verification

- owner production acceptance of material edit behavior after `5fb491a`;
- direct server test verifies Unit Cost editing, material line Cost,
  Consumables, self cost, VAT, and total recalculation;
- focused navigation, runtime, and pricing-policy suite: 47 passed;
- complete suite at `89dda51`: 887 passed, 26 dependency warnings;
- Python compilation: passed;
- `git diff --check`: passed;
- production Approve timing after `89dda51`: pending one measured pass.

## Protected behavior

- accepted File Review, Objects, and Object Detail layout and navigation rail;
- destination scroll-to-top and transition masking;
- `d3e83bd` Sign Out target-side readiness contract;
- Fast Resume, membership checks, browser-session clearing, hidden-sidebar
  session component, and Cloudflare topology;
- Estimation, Labor, material resolver, pricing-policy arithmetic, Final
  Approval, Projects, and Client Proposal behavior.

## Preserved dirty state

These pre-existing untracked paths remain outside the checkpoint:

- `.streamlit/`
- `db/sql/3_15_4_israel_global_catalog_v1_parts/`
- `tmp/`

## Next verification

Run one clean production Approve Estimate transition after deployment. Pass
requires one internal Python run, destination Objects readiness without a
15-second timeout, correct approved state, and preserved navigation controls.
