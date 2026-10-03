# 3.15.24 Object quantity and Object Detail draft checkpoint, 2026-10-03

## Checkpoint status

Checkpoint code: `5f6360f`.

Database migration:
`db/sql/2026_10_03_object_detail_draft_rpc.sql`, applied and structurally
verified in production on 03.10.2026.

This is a complete implementation checkpoint and rollback point. The full test
suite passes and the production schema is active. Final owner acceptance of the
latest Materials edit and changed-draft Approve behavior remains pending one
production pass, so 3.15.24 is not marked completed.

## Product contract

- Object quantity is editable on File Review, Objects, and Object Detail.
- `rfq_detected_objects.quantity` is canonical; the current
  `rfq_object_estimates.quantity` is its synchronized workflow read model.
- Objects quantity saves immediately and resets that object's approval without
  rerunning Estimation.
- Object Detail quantity and line edits remain a local draft until Approve.
- Back to Objects with a changed draft uses the accepted Costerly confirmation
  dialog. Leaving discards the draft; staying preserves it.
- Approve persists one draft snapshot, recalculates through the deterministic
  server engine, marks the object approved, and returns to Objects.
- Pricing-policy material rows remain locked and formula-derived.

## Final architecture

### Objects quantity

The browser calls authenticated RPC `save_rfq_object_quantity`. The RPC checks
the signed-in user's company membership and estimate ownership, then updates the
canonical detected-object quantity and estimate mirror together. The current DOM
updates without a Streamlit rerun. A saving overlay appears immediately.

### Object Detail draft and Approve

The browser calls authenticated RPC `save_rfq_object_detail_draft`. The RPC
stores one user-, company-, estimate-, and object-scoped JSON draft. After the
write succeeds, the existing native Streamlit Approve bridge runs exactly once.
The server reads the draft, applies line and quantity edits, recalculates the
object, writes totals and approval together, deletes the draft only after a
successful calculation, and returns to Objects.

The prior `streamlit:setComponentValue` quantity and draft components were
deleted. They caused extra reruns, exposed intermediate Object Detail renders,
and failed production acceptance twice. They must not be restored.

## Materials zeroing root cause

The visible zeroing was not a price-data failure. The Object Detail renderer
used the display escape helper for the `data-policy-percent` HTML attribute.
For an ordinary material row, the intended empty value became an em dash.
JavaScript treated every truthy attribute as a pricing-policy row, calculated a
zero primary-material base, and visually replaced all material costs with zero.

Ordinary rows now render `data-policy-percent=""`. Only locked policy rows carry
a numeric percentage. A deterministic regression test protects this boundary.

## Approve latency reduction

For a changed draft, recalculated totals and `approved=true` are now written in
one object-estimate update. This removes the redundant second authorization,
read, and approval-write pass. No pricing formula or ownership rule changed.

## Implementation commits

- `682dc7e`: canonical quantity synchronization foundation.
- `1867103`: local Object Detail draft boundary.
- `2150ed0`: first live component draft bridge, later rejected.
- `84a0b9f`: isolated quantity events from ordinary detail inputs.
- `4b0a3d2`: replaced both component rerun bridges with authenticated RPC paths;
  applied the additive production migration.
- `5f6360f`: fixed ordinary-material policy classification and removed the
  redundant changed-draft approval pass.

## Verification

- complete suite at `5f6360f`: 897 passed;
- `git diff --check`: passed;
- migration table exists in production:
  `public.rfq_object_detail_drafts`;
- production functions exist:
  `save_rfq_object_detail_draft` and `save_rfq_object_quantity`;
- application deployment was triggered by pushing `5f6360f` to `origin/main`;
- final authenticated production interaction acceptance: pending.

## Protected behavior

- accepted File Review, Objects, and Object Detail layout;
- navigation rail persistence and scroll-to-top behavior;
- accepted Back warning dialog;
- deterministic Materials, Labor, employer load, Overhead, VAT, and self-cost
  ownership;
- Delivery and Installation remain project-level sale-price additions;
- Fast Resume, membership checks, Sign Out readiness, browser-session clearing,
  hidden-sidebar session component, and Cloudflare topology;
- Estimation Agent, resolver, Pricing Policy, Projects, Final Approval, and PDF
  proposal behavior.

## Preserved dirty state

The checkpoint does not include or modify these pre-existing untracked paths:

- `.streamlit/`
- `db/sql/3_15_4_israel_global_catalog_v1_parts/`
- `tmp/`

## Acceptance needed to close 3.15.24

In one authenticated production session:

1. edit Objects quantity and confirm immediate saving feedback, persistence, and
   recalculated row/project totals without a full-page rerun;
2. open Object Detail and edit one material Unit Cost;
3. confirm the edited row and all untouched material rows remain nonzero;
4. edit one material Quantity and confirm the same;
5. Approve and confirm one clean transition to Objects, correct totals, approved
   state, navigation controls, and no broken intermediate screen;
6. reopen Object Detail and confirm persisted values.

