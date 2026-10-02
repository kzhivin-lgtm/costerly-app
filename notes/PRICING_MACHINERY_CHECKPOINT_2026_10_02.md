# Pricing and Machinery checkpoint, 2026-10-02

Work: 3.15.17 and 3.15.18

Status: implementation checkpoint saved before continuing product work.

## Checkpoint commits

- `053c66d`: company Pricing Policy, persistence and runtime integration.
- `89dbde2`: compact eight-tab Profile navigation without horizontal scroll.
- `722b6c6`: Machinery session draft with one explicit Save action.

At checkpoint creation, `HEAD`, `origin/main` and `origin/HEAD` all point to
`722b6c6`.

## Pricing architecture

The Profile contains eight peer tabs in this order: Overhead Expenses, Labor
Costs, Pricing, Machinery, Price Lists, Contacts, Bank Details and Users.

Pricing owns nine company percentages stored in `overhead_settings`:

1. VAT, default 18%.
2. Warranty reserve, default 5%.
3. Management buffer, default 5%.
4. Consumables, default 5% of primary material cost.
5. Packaging, default 1% of primary material cost.
6. Paint consumables, default 10% of explicit coating material cost.
7. Default sale markup, default 30% over object self cost excluding VAT.
8. Delivery, default 3% of the project sale-price subtotal.
9. Installation, default 10% of the project sale-price subtotal.

Warranty and management remain part of self cost. Delivery and installation
are applied only after sale price and are not self cost. VAT is applied after
the project pricing additions. Persisted user price overrides remain
authoritative over later suggestions.

The additive SQL migration is applied in production. Production rows for the
two inspected companies contain all nine values. The Estimation composer and
Objects totals read the company policy instead of relying on the former fixed
percentages.

## Machinery architecture

Machinery retains the existing catalog, company capability, supplier routing
and pricing model. The UI interaction boundary changed, not the domain model.

- The first Machinery render loads the persisted machinery, suppliers and
  service snapshot.
- Control changes update only a session-scoped draft.
- The draft survives navigation among Company Profile tabs in the same
  Streamlit session.
- One bottom Save action validates the complete draft.
- Save writes only routes whose persisted values changed.
- A successful save refreshes the persisted snapshot and draft.
- A validation or persistence failure keeps the draft available for correction.
- Ending the session without Save discards the draft and leaves Supabase
  unchanged.

This removes the previous full-page persistence cycle after each selector
change while preserving the existing Machinery data model and authorization.

## Protected behavior

- No File Review, Objects or Object Detail layout was redesigned.
- Estimation remains company-policy driven and object results remain editable.
- The exact approved Company Profile Machinery capability subset is unchanged.
- `.streamlit/` and `tmp/` remain local and uncommitted.
- The duplicate 12-part SQL directory
  `db/sql/3_15_4_israel_global_catalog_v1_parts/` remains local and uncommitted.
  Every file was byte-compared with its tracked counterpart in `db/sql/`.

## Verification at checkpoint creation

- Full automated suite: 857 passed, 25 warnings in 8.59 seconds.
- `git diff --check`: passed.
- Backup: `v3.15.18_pricing_machinery_checkpoint`, 3,441,233 bytes, validated
  after creation. SHA-256:
  `68a680b4f8e501ba3dadca93233a89f884761679e8b6ed518989e8d47d70210d`.
- Real authenticated production acceptance of Pricing edits and Machinery draft
  interaction remains pending. It must not be inferred from tests or deployment.

## Active queue after this checkpoint

1. P0, 3.15.9 Active RFQ navigation recovery, especially browser Back and
   Upload recovery for a persisted active run.
2. P0, complete 3.15.8 Estimation runtime stability without terminal domain
   failures.
3. P0, 3.15.11 Israel Price List taxonomy and pricing identity normalization.
4. 3.15.10 internal Review Required workspace.
5. 3.15.12 coatings and consumables separation.
6. 3.15.13 Labor Engine functional and quality review.
7. 3.15.14 RFQ cancellation and Project finalization.
8. Deferred 3.15.16 header controls scroll stability.

The authoritative details and acceptance requirements remain in `notes/TODO.md`.
