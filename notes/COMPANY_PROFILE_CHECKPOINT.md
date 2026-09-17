# Company Profile checkpoint

Version: v3.0.54
Date: 2026-09-17

## Accepted UI

- The shared full Costerly logo is hidden on Company Profile. The small C mark
  remains beside `Company profile`.
- The redundant Profile action is absent. Compact `Continue to upload` and
  standard icon-bearing `Sign out` actions live in the page header.
- The peer tabs are General Details, Contacts, Bank Details, Metrics, Users, and Price
  List. Tabs use the larger Profile navigation treatment. Repeated tab headings
  are not rendered inside their panels.
- General Details uses two rows: Company name / Company legal name (Hebrew),
  then Company registration number / Company legal name (English).
- Contacts contains Official email, Phone, Website, Street, House Number, City,
  Postal code, Facebook, LinkedIn, and Instagram without redundant Address or
  Social links headings.
- Bank Details contains Bank name, Bank number, Branch number, Account number,
  IBAN, and BIC without a redundant International bank heading. Company legal
  name (Hebrew) appears as a read-only half-width field before domestic bank
  details. Company legal name (English) appears as a read-only half-width field
  before IBAN and BIC.
- Every current and future editable Profile form uses the shared full-width,
  high-emphasis purple Save action with capital-letter text and a stronger
  purple hover.
- Profile inputs follow the Sign in neutral-border and purple-focus contract.
  Streamlit's `Press Enter to submit form` instruction is hidden.
- Metrics is a saved work-in-progress baseline. It exposes the company VAT rate,
  the twelve existing monthly overhead fields, warranty reserve, and management
  buffer. Monthly cost is the only editable money column. VAT and Total are
  derived whole-shekel values, and Arnona displays no VAT.

## Persistence contract

- Company-wide writes remain owner-only and recheck the live owner role.
- Each section sends only the fields it owns. Hidden `vat_file_number` and
  `address_country` values are not included in these updates and are preserved.
- Both company legal names remain editable only in General Details. Bank Details
  displays those same stored values but never writes them. If banking requires
  a different beneficiary identity, add a separately named `Account holder
  name` field only after confirming the data requirement and migration.
- Metrics writes only its three visible `overhead_settings` percentages and the
  twelve visible `overhead_monthly` fields. Monthly costs are persisted as whole
  shekels. The company-wide VAT rate is reused by deterministic Estimation totals.

## Protected behavior

- Auth and Upload screens and CSS are unchanged by the v3.0.54 Profile revision.
- Session persistence and first-click Profile navigation remain governed by the
  separately accepted v3.0.51 Auth checkpoint.

The separate v3.0.51 Auth checkpoint resolves refresh persistence and the
first-click Profile regression without changing this accepted Profile UI. Its
browser component is isolated in the hidden Sidebar; this document remains the
UI definition for the Profile screen.

## Verification

- User accepted the enlarged tabs and Bank Details grid, then selected General
  Details as the only editor for company legal names.
- User accepted the Metrics screen as a functioning work-in-progress checkpoint
  after a clean Streamlit restart removed the observed delay.
- Automated suite: 137 tests passed before checkpoint documentation.
- `git diff --check`: clean before checkpoint documentation.
