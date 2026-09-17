# Company Profile checkpoint

Version: v3.0.52
Date: 2026-09-17

## Accepted UI

- The shared full Costerly logo is hidden on Company Profile. The small C mark
  remains beside `Company profile`.
- The redundant Profile action is absent. Compact `Continue to upload` and
  standard icon-bearing `Sign out` actions live in the page header.
- The peer tabs are General Details, Contacts, Bank Details, Metrics, Users, and Price
  List. Repeated tab headings are not rendered inside their panels.
- General Details uses two rows: Company name / Company legal name (Hebrew),
  then Company registration number / Company legal name (English).
- Contacts contains Official email, Phone, Website, Street, Number, City,
  Postal code, Facebook, LinkedIn, and Instagram without redundant Address or
  Social links headings.
- Bank Details contains Bank name, Bank number, Branch number, Account number,
  IBAN, and SWIFT / BIC without a redundant International bank heading.
- Every current and future editable Profile form uses the shared full-width,
  high-emphasis purple Save action with capital-letter text and a stronger
  purple hover.
- Profile inputs follow the Sign in neutral-border and purple-focus contract.
  Streamlit's `Press Enter to submit form` instruction is hidden.

## Persistence contract

- Company-wide writes remain owner-only and recheck the live owner role.
- Each section sends only the fields it owns. Hidden `vat_file_number` and
  `address_country` values are not included in these updates and are preserved.
- `Company legal name (English)` remains owned by General Details. Bank Details does not
  duplicate it. If banking requires a different beneficiary identity, add a
  separately named `Account holder name` field only after confirming the data
  requirement and migration.

## Protected behavior

- Auth and Upload screens and CSS are unchanged by the v3.0.52 Profile revision.
- Session persistence and first-click Profile navigation remain governed by the
  separately accepted v3.0.51 Auth checkpoint.

The separate v3.0.51 Auth checkpoint resolves refresh persistence and the
first-click Profile regression without changing this accepted Profile UI. Its
browser component is isolated in the hidden Sidebar; this document remains the
UI definition for the Profile screen.

## Verification

- User accepted the renamed fields and requested the shared maximum-emphasis
  Save treatment for every Profile form.
- Automated suite: 133 tests passed before checkpoint documentation.
- `git diff --check`: clean before checkpoint documentation.
