# 3.15.17 Company Pricing Policy

Date: 02.10.2026

## Product contract

Company Profile order:

1. Overhead Expenses
2. Labor Costs
3. Pricing Cost
4. Machinery
5. Price Lists
6. Contacts
7. Bank Details
8. Users

Pricing Cost uses the established Bank Details form pattern: a white card,
two-column percentage inputs and one bottom Save action. It contains these
owner-editable values with defaults:

- VAT: 18%
- Warranty reserve: 5%
- Management buffer: 5%
- Consumables: 5%
- Packaging: 1%
- Paint consumables: 10%
- Default sale markup: 30%
- Delivery: 3%
- Installation: 10%

Members can inspect the values but cannot change them.

## Calculation contract

- Warranty reserve and Management buffer remain in object self cost through the
  deterministic Overhead Engine.
- Consumables and Packaging are locked Materials rows calculated from primary
  material cost.
- Paint consumables are a separate locked Materials row calculated from the
  explicit `wood_coatings` and `metal_coatings` material subtotal. With no
  explicit coating material its amount is zero.
- Suggested object sale price is self cost excluding VAT plus Default sale
  markup. A user override remains authoritative.
- Delivery and Installation are project-level additions calculated from the
  objects' sale-price subtotal. They are not self cost.
- VAT is applied after Delivery and Installation to the complete project price.

## Persistence and migration

The existing `overhead_settings` row remains the single company policy record.
No existing columns or values move. Migration
`2026_10_02_company_pricing_policy.sql` adds only `consumables_percent`,
`packaging_percent`, and `paint_consumables_percent`, with bounded defaults of
5, 1, and 10. It does not delete rows, rewrite existing values, change RLS, or
modify production data beyond PostgreSQL filling the three new columns with
their declared defaults.

## Protected behavior

- Overhead monthly expenses retain their existing save and allocation paths.
- Existing VAT, Warranty, Management, markup, Delivery, and Installation values
  retain their column identities.
- Labor, Machinery, Price Lists, Contacts, Bank Details, and Users behavior is
  unchanged.
- Existing manual sale-price overrides are preserved.

## Verification gate

1. The additive migration was applied on 02.10.2026. A read-only production
   query verified both existing companies at Consumables 5%, Packaging 1%, and
   Paint consumables 10%.
2. Run the focused Profile and Estimation suites, then the complete suite.
3. Verify owner save, refresh persistence, member read-only behavior, zero and
   decimal input, and invalid values in the authenticated production Profile.
4. Run one Estimation object with coating and one without coating.
5. Verify Objects live editing uses the configured markup, Delivery,
   Installation, and VAT without replacing manual overrides.

Local implementation verification: 856 tests passed and `git diff --check`
passed. Authenticated production UI and calculation acceptance remain pending
after deployment.
