# Company Profile checkpoint

Version: v3.4.2 accepted Company Logo production checkpoint
Date: 2026-09-20

## v3.4.2 Company Logo completed UI

- Accepted production checkpoint: `32497dc`.
- Emergency rollback boundary for the v3.5 Labor Costs performance
  investigation: `86117ba`, which finalizes this checkpoint before the Labor
  Costs rewrite begins at `8ef2131`. This is a product rollback boundary, not a
  verified performance baseline.
- The owner view always keeps the Drop or Upload surface. With a saved or
  newly selected logo, the normalized preview forms the right side of the same
  two-column composition. Before the first selection there is no empty preview
  frame.
- The full-width action matches Save Contacts exactly. It reads Save Logo for
  the first logo and Change Logo for an existing company logo. Change Logo is
  active in the idle saved state and opens the same native file picker as the
  upload surface; once a valid replacement is pending, it performs the guarded
  server save.
- `--profile-action-gap` is the shared 32px design token for the accepted final
  content-to-action rhythm. Invisible interaction markers and Sidebar bridge
  components do not participate in main-page layout.
- Logo drag-over uses the Costerly purple focus treatment, not Streamlit's
  native red state. Logo success feedback renders above the action and visually
  dismisses after five seconds.
- The user accepted the complete production setup. Automated suite: 204 tests
  passed. Separate live PNG and PDF checks were not required for visual
  acceptance; both formats remain covered by deterministic conversion tests.
- Local rollback archive:
  `v3.4.2_company_logo_completed_production_checkpoint`, 520,271 bytes,
  SHA-256
  `343da7e34a197e27e9d8629381d1320134f74cc5b65dccdc44534d5a2160e4d6`.

## v3.4.1 Company Logo checkpoint

- Product checkpoint: `2a6ac0f`.
- Contacts owns a separate Company Logo card below its independent Save
  Contacts form. Upload and Detection interactions are isolated, so selecting a
  logo cannot activate the New Estimate processing shell.
- Owners may upload PNG, SVG, or first-page PDF sources. Standard SVG 1.1
  `DOCTYPE` declarations are removed before rendering, embedded PNG/JPEG/WebP
  artwork is accepted, and scripts, XML entities, HTML, event handlers, local
  files, and external resources remain blocked.
- The deterministic server pipeline trims the visible artwork and stores only
  the normalized private 1024px PNG plus its `companies.logo_url` reference.
  The raw source is not retained.
- The user verified the supplied SVG on production, including conversion,
  preview, save, and the persisted logo. Automated suite: 203 tests passed.
- Local rollback archive:
  `v3.4.1_company_logo_production_checkpoint`, 516,861 bytes, SHA-256
  `fe9f105127175e8847b411f11b12bcefca75be406ae2b0f20c9cc102af197120`.
- Follow-up UI work is intentionally outside this checkpoint: hide the empty
  preview frame, align the upload/preview row, replace the idle saved state with
  Change Logo, auto-dismiss success feedback, and standardize success placement
  above Save actions across Profile tabs.

## v3.2.5 Profile navigation checkpoint

- Product checkpoint: `b372d3d`.

- Header actions are ordered `Projects`, `New Estimate`, `Sign out`.
- Profile tabs prioritize costing configuration: Overhead Expenses, Labor
  Costs, Price Lists, Contacts, Company Details, Users.
- Tab restoration remains label/slug based, not position based.
- Streamlit and Cloudflare build versions are code-owned and checked for an
  exact match, so production no longer needs a manually updated build secret.
- The user accepted the production presentation and behavior. Automated suite:
  187 tests passed.

## v3.2.4 Transition identity correction

- The compact Profile actions retain the accepted v3.2.3 alignment.
- The transition observer binds the `profile_to_upload` action to its stable
  Streamlit key. Previous visible labels remain temporary compatibility
  fallbacks for browser tabs that were already open during deployment.
- The production result was accepted as part of the v3.2.5 checkpoint.

## v3.2.3 Compact Profile header

- Product checkpoint: `1f30416`.
- Top-level CSS and screen-marker wrappers no longer consume Streamlit's 16px
  vertical gaps before the visible header.
- The top page gap and visual title-to-tabs gap both measure 34px on Streamlit
  1.64.
- Projects is visible but disabled until its screen and persistence contract are
  defined. Upload and Sign out retain their existing behavior.
- Profile actions are actual 36px buttons. Their measured center is 78.14px,
  the brand mark center is 79.14px, and both align with the title's visual axis.
- The user accepted the rendered preview. Automated suite: 186 tests passed.

## v3.2.2 Users invitation link

- Product checkpoint: `dff220c`.
- The owner-only Team Invitation Link now reuses the existing Users table-card
  instead of a loose heading and Streamlit code block.
- Its uppercase table header matches EMAIL and ROLE, the URL remains a real
  clickable link, and the 12px gap matches the compact Labor Costs section gap.
- Non-owner behavior is unchanged and does not render or fetch an invitation
  URL.
- The user accepted the rendered preview. Automated suite: 186 tests passed.

## v3.2.1 Labor Costs continuation

- v3.6.1 compact table checkpoint: `f334338`.
- Edit and Remove are stacked in a 38px action column. Table-only Pay Type
  values are `Hourly` and `Monthly`; Pay Details no longer repeats the
  employment factor. Controlled-value columns use compact widths and the table
  no longer enforces a 900px minimum.
- New selections use short Position labels. Cabinetmaker / Joiner and
  Purchasing Manager are retired from the selector; legacy stored codes remain
  readable, with Cabinetmaker / Joiner presented as Carpenter. The Labor Costs
  selectors keep their dropdown triggers but hide the optional clear control.
- The user accepted the production presentation. Automated suite: 217 tests
  passed in the subsequent v3.6.2 checkpoint.

- Current accepted Git checkpoint: `dfcf5ef`.
- Labor Costs is an owner-only employee cost register backed by
  `company_employees`, with one informal Worker name, controlled Department and
  Position values, Monthly Salary or Hourly Rate, and derived Monthly Bruto.
- Saved workers appear above the editor and open the same validated edit path
  through a compact pencil before each worker name.
- Streamlit 1.64 React Aria selectors match the 52px Profile input contract,
  center their text vertically, and use the Costerly purple focus border and
  ring. The older BaseWeb selectors remain for runtime compatibility.
- The user accepted the production pencil alignment and all selector states.
- The Add Worker card uses the same compact section spacing as the summary and
  worker table. Disabled Position placeholders remain regular weight, while
  calculated disabled text values retain their intended bold emphasis.
- Automated suite: 186 tests passed.

## v3.1.10 production continuation

- Current Git checkpoint: `9ab5814`. The prior accepted fast Auth checkpoint is
  `9a43cd3`; the lazy Profile rendering checkpoint remains `4c6d628`.
- The full-width Profile navigation rail is restored without reverting lazy
  tab rendering. The selected tab uses a white card and bold label. The React
  Aria red selection indicator is removed, and `Price List` is now
  `Price Lists`.
- Overhead Expenses terminology is consistent in the tab, singular table
  column `Overhead Expense`, `Save Overhead Expenses` action, success message,
  and save errors.
- The zero-height Save bridge and its outer Streamlit element wrapper are
  hidden from document flow. Save still works in production.
- Production screenshots confirm a small residual vertical offset below the
  navigation on Overhead Expenses compared with the other tab contents. This
  remains unresolved and prevents visual completion. The next pass must inspect
  live computed layout boundaries before changing CSS; do not mask it with an
  assumed negative margin.
- Automated suite: 165 tests passed for the current code checkpoint.

## Accepted UI

- The shared full Costerly logo is hidden on Company Profile. The small C mark
  remains beside `Company profile`.
- The redundant Profile action is absent. Compact `Continue to upload` and
  standard icon-bearing `Sign out` actions live in the page header.
- The peer tabs are Overhead Expenses, Labor Costs, Contacts, Company Details,
  Users, and Price Lists. Overhead Expenses is first. Tabs use the larger Profile navigation treatment.
  Repeated tab headings are not rendered inside their panels.
- Labor Costs is the separate second tab and follows the accepted v3.2.1
  owner-only employee cost contract above.
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
  VAT and Total immediately. A zero-height Streamlit component returns one
  owner-validated snapshot to an isolated fragment without URL navigation or a
  full-page query-parameter reload.
- Existing expense rows use partial `update` calls, preserving required hidden
  overhead settings. A company without expense rows receives a complete
  default-backed insert. This avoids PostgREST partial-upsert null expansion.

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
- User verified on the v3.0.59 local build that Save Expenses completes quickly
  inside the current screen and persists the edited values.
- User verified in production at `9ab5814` that the restored navigation rail,
  bold selected tab, plural `Price Lists`, removed red indicator, terminology,
  and Save Overhead Expenses behavior work. The remaining vertical offset is
  explicitly not accepted as finished.
- User verified in production at `1df98c5` that Labor Costs edit pencils align
  before worker names, selector text is vertically centered, and selector focus
  uses the purple Costerly border and ring.
- User verified in production at `dfcf5ef` that the final Add Worker spacing is
  consistent and the disabled `Select position` placeholder is not bold.
- User accepted the v3.2.2 rendered preview with the invitation link presented
  as a compact second Users table-card.
- User accepted the v3.2.3 rendered preview with equal 34px header spacing,
  aligned compact actions, and a disabled Projects placeholder.
- Live DOM verification measured 40px group bars, 51px cost rows, and 34px
  Monthly Cost inputs. A live edit from 2,000 at 18% produced VAT 360 and Total
  2,360.
- Direct Supabase verification confirmed that a partial `update` preserves the
  required hidden `overhead_settings` values for company 293.
- Automated suite: 186 tests passed before the v3.2.3 checkpoint packaging.
- `git diff --check`: clean before checkpoint documentation.

## Explicit next phase

- Measure and remove the remaining Overhead Expenses vertical offset using the
  live production DOM. Compare the active tab panel, fragment wrapper, outer
  element container, hidden bridge host, and metrics card top boundaries.
- Diagnose the user-observed duplicate page heading after Sign out. Preserve the
  accepted Auth session boundary and do not change Profile persistence while
  isolating that regression.
- Verify Contacts and Company Details remain on their selected tab after Save.
- Run a fresh full visual and interaction pass tomorrow before promoting this
  checkpoint to a stable release.
