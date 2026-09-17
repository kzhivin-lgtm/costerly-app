# Company Profile checkpoint

Version: v3.0.49
Date: 2026-09-17

## Accepted UI

- The shared full Costerly logo is hidden on Company Profile. The small C mark
  remains beside `Company profile`.
- The redundant Profile action is absent. Compact `Continue to upload` and
  standard icon-bearing `Sign out` actions live in the page header.
- The peer tabs are General, Contacts, Bank Details, Metrics, Users, and Price
  List. Repeated tab headings are not rendered inside their panels.
- General uses two rows: Company name / Legal name (Hebrew), then Company
  registration number / Legal name (English).
- Contacts contains Official email, Phone, Website, Street, Number, City,
  Postal code, Facebook, LinkedIn, and Instagram without redundant Address or
  Social links headings.
- Bank Details contains Bank name, Bank number, Branch number, Account number,
  IBAN, and SWIFT / BIC without a redundant International bank heading.
- Each editable section has one full-width primary `Save` action.
- Profile inputs follow the Sign in neutral-border and purple-focus contract.
  Streamlit's `Press Enter to submit form` instruction is hidden.

## Persistence contract

- Company-wide writes remain owner-only and recheck the live owner role.
- Each section sends only the fields it owns. Hidden `vat_file_number` and
  `address_country` values are not included in these updates and are preserved.
- `Legal name (English)` remains owned by General. Bank Details does not
  duplicate it. If banking requires a different beneficiary identity, add a
  separately named `Account holder name` field only after confirming the data
  requirement and migration.

## Protected behavior

- Auth and Upload code/layout remain byte-identical to v3.0.48.
- The rejected browser-session persistence experiment is not part of v3.0.49.
- Full browser refresh may still require Sign in. Resolve that as an isolated
  Auth architecture decision after this checkpoint.

## Verification

- User accepted the current local Profile direction after visual review.
- Automated suite: 127 tests passed before checkpoint documentation.
- `git diff --check`: clean before checkpoint documentation.
