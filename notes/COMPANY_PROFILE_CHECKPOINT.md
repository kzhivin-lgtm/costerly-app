# Company Profile checkpoint

Version: v3.0.58
Date: 2026-09-18

## Accepted UI

- The shared full Costerly logo is hidden on Company Profile. The small C mark
  remains beside `Company profile`.
- The redundant Profile action is absent. Compact `Continue to upload` and
  standard icon-bearing `Sign out` actions live in the page header.
- The peer tabs are Overhead Expenses, Labor Costs, Contacts, Company Details,
  Users, and Price List. Overhead Expenses is first. Tabs use the larger Profile navigation treatment.
  Repeated tab headings are not rendered inside their panels.
- Labor Costs is reserved as a separate second tab and currently renders only a
  placeholder until its personnel model is approved.
- Contacts contains Official email, Phone, Website, Street, House Number, City,
  Postal code, Facebook, LinkedIn, and Instagram without redundant Address or
  Social links headings. Israeli phone input is normalized to the
  `+972 53 400 0000` presentation.
- Company Details combines identity and banking data in five rows: Company name /
  Company registration number, Company legal name Hebrew / English, Bank name /
  Bank number, Branch number / Account number, and IBAN / BIC.
- Every current and future editable Profile form uses the shared full-width,
  high-emphasis purple Save action with capital-letter text and a stronger
  purple hover.
- Profile inputs follow the Sign in neutral-border and purple-focus contract.
  Streamlit's `Press Enter to submit form` instruction is hidden.
- Overhead Expenses is a visual work-in-progress baseline. It exposes the company VAT rate,
  the twelve existing monthly overhead fields, a new Other spendings row,
  warranty reserve, and management buffer. Monthly cost is the only editable
  money column. VAT and Total are derived whole-shekel values, and Arnona
  displays no VAT. VAT, Warranty reserve, and Management buffer are grouped
  below the expense table without a Project Reserves heading.
- Overhead Expenses reuses the actual Object Detail HTML-grid and CSS primitives,
  rather than approximating them with Streamlit columns. Its group bars are
  40px high, editable Monthly Cost fields are 34px high, and rendered cost rows
  are 51px high, exactly matching the measured Object Detail table geometry.
- The Expense, Monthly Cost, VAT, and Total axes, 13px typography, separators,
  group treatment, and compact input treatment now come from the shared Object
  Detail design contract. The last row in each group has no separator before
  the next group bar.

## Persistence contract

- Company-wide writes remain owner-only and recheck the live owner role.
- Each section sends only the fields it owns. Hidden `vat_file_number` and
  `address_country` values are not included in these updates and are preserved.
- Company Details is the single editing surface for company identity and banking
  values. One form submits those fields together.
- Metrics writes only its three visible `overhead_settings` percentages and its
  visible `overhead_monthly` fields. Monthly costs are persisted as whole
  shekels. The company-wide VAT rate is reused by deterministic Estimation totals.
- `other_spendings_cost` is wired into Company Metrics and deterministic Object
  Detail pricing, with its SQL migration stored in
  `db/sql/2026_09_18_other_spendings_overhead.sql`. The user applied this
  migration to the live Supabase schema before the v3.0.58 checkpoint.
- The Metrics table keeps only Monthly Cost editable. Its browser guard updates
  VAT and Total immediately, then submits one owner-validated snapshot through
  the existing server save function. The narrow `screen=account` query route
  returns a full-page snapshot submission to Company Profile without changing
  the normal Profile button or Auth session flow.

## Protected behavior

- Auth and Upload screens and CSS are unchanged by the v3.0.58 Profile revision.
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
- User explicitly accepted the v3.0.56 Company Metrics table after it was moved
  to the same implementation and measured geometry as Object Detail.
- User accepted the v3.0.57 visual continuation with Company Metrics first,
  phone formatting, bottom percentage controls, equalized vertical spacing,
  and Other Spendings present in the table.
- User accepted the v3.0.58 information architecture with Overhead Expenses
  first, Labor Costs second, Contacts before one combined Company Details form,
  and both legal names aligned on its second row.
- Live DOM verification measured 40px group bars, 51px cost rows, and 34px
  Monthly Cost inputs. A live edit from 2,000 at 18% produced VAT 360 and Total
  2,360.
- Automated suite: 145 tests passed before checkpoint documentation.
- `git diff --check`: clean before checkpoint documentation.

## Explicit next phase

- Saving Contacts or Company Details currently reruns the page onto the first
  tab. Preserve the active tab after submit.
- Overhead Expenses saving is not accepted in this checkpoint. Repair it only as
  the next isolated phase, then verify confirmation plus persistence through a
  logout, sign-in, and reload cycle.
