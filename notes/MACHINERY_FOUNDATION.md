# Machinery and Production Routing Foundation

Task: 3.9.1
Status: Supabase migration verified, application deployment and production acceptance pending

This document is the scenario-first contract for the Machinery profile and the
production context later supplied to Estimation. The pre-existing
`company_machines` rows are an archived prototype and are not the catalog or
source of truth for this implementation.

## Product boundary

- The first scope is furniture production across woodworking, metalworking,
  and painting/finishing.
- Wood CNC routing and metal laser cutting are separate first-class machine
  types with separate capability and pricing questions.
- The default interaction asks only whether a capability exists in-house.
  Technical and pricing questions appear only after `Yes`.
- When a capability is not in-house, the owner may connect an existing supplier
  or create one supplier record and attach a service to it. There is no second
  supplier directory.
- A supplier rate is optional. A quote history or later regional benchmark may
  supply pricing when no explicit rate exists.
- Manual fallback is never inferred for panel materials or precision metal
  processes. It must be explicitly enabled for a compatible route.
- Estimation receives a versioned application-built snapshot. The model does
  not query Supabase directly. It may select and explain a route from the
  supplied machines, supplier services, and price provenance; deterministic
  code validates feasibility and owns arithmetic.

## Machinery UI scenario matrix

| State or action | Expected behavior |
| --- | --- |
| Machinery tab opens with no answers | Show Woodworking, Metalworking, and Painting & Finishing groups with unanswered Yes/No cards; do not create rows merely by viewing |
| Owner chooses Yes | Reveal only the minimum capability questions for that machine; do not reveal subcontractor questions |
| Owner chooses No | Hide and clear unsaved in-house details; ask whether a regular subcontractor is used |
| Owner chooses No and no subcontractor | Save the explicit absence; later routing may use a regional benchmark with lower confidence |
| Owner chooses No and has a subcontractor | Allow selecting an existing company supplier or creating one supplier, then attach the relevant service |
| Required in-house field is missing | Keep the card editable, mark only the missing field, and do not save a partial confirmed capability |
| Optional value is unknown | Save the capability without inventing a value; show it as not provided |
| Owner selects a pricing method | Ask only the fields needed by that method, such as hourly rate, per-sheet rate, per-part rate, or quote-only |
| Owner selects quote-only | Do not require a structured rate; permit later quote evidence and history |
| Owner saves a valid card | Persist one company machinery profile, show a compact saved state, and retain the current tab and scroll context |
| Save is running | Disable that card's controls and save action; duplicate clicks cannot create duplicate rows |
| Save succeeds | Show a short success status without moving other cards or changing tabs |
| Save fails | Preserve every entered value, unlock the card, and show a neutral retryable error |
| Owner edits a saved card | Update the same row; do not create a second active record for the machine code |
| Owner changes Yes to No | Require confirmation when a saved in-house profile or pricing data would be deactivated; preserve historical data for estimate audit |
| Member opens Machinery | Show saved capabilities read-only; do not show save, supplier creation, or destructive controls |
| Database migration is not applied | Show one bounded unavailable message; the rest of Company Profile remains usable |
| Refresh, back, or tab switch after save | Reload the persisted state without duplication or loss |
| Narrow/mobile viewport | Cards remain one-column, labels do not clip, and controls retain touch-sized targets |
| Keyboard navigation | Yes/No, fields, supplier selection, and save follow logical focus order and work without pointer input |

### Accepted compact-layout revision

- The tab does not repeat a `Machinery` heading. Its introductory sentence is
  the single large heading.
- Technical inputs are arranged in rows of three when space permits and collapse
  naturally on narrow screens.
- Long dimensions such as working length and width are entered as decimal meters;
  thicknesses, tool diameters, and profile sizes remain millimeters. Canonical
  database values remain millimeters.
- Numeric capability inputs are plain text fields with explicit units, not
  number steppers. Both decimal point and decimal comma are accepted.
- A non-in-house capability asks only whether a regular subcontractor is used.
  `Yes` reveals one free-text subcontractor name. There is no Existing/New split,
  supplier dropdown, supplier pricing method, or typical lead-time question.
- Entering the same normalized subcontractor name reuses the existing
  `company_suppliers` identity. Replacing a regular subcontractor deactivates the
  previous route without deleting its history.
- The capability catalog uses three full-width grouped tables, not a vertical
  stack of machine cards. Each table header contains its group name in the first
  column and `Available in-house?` in the second. Machine names use the same row
  position as Rent or Electricity in Overhead Expenses.
- The three group tables have a deliberate vertical gap. Their compact status
  controls use pale yellow for Not answered, pale green for Yes, and pale red
  for No.
- Unanswered rows stay compact. Selecting `Yes` or `No` inserts that machine's
  detail panel immediately below its row and spans the full table width.
- Every detail panel uses three equal columns for capability, costing, or
  subcontractor fields. It does not introduce another narrow nested card.
- Detail descriptions are omitted. For CNC, row one contains the three
  technical dimensions, row two contains `Materials` and `Costing method`, and
  row three contains the two boolean options. Selected material tags use the
  product purple-neutral palette; red remains reserved for negative status and
  validation/error feedback.
- Machinery has no introductory heading below the Profile tabs. Its first
  group starts at the same vertical offset as the Overhead Expenses content.
- Machine rows form one continuous bordered table inside each group. The
  availability control stays centered in a fixed-width column and its three
  options have an 8 px gap.
- Unselected availability options use very pale semantic tints. The selected
  option uses a stronger tint, stronger border, and bold text, so selection is
  distinguishable without relying on color alone.
- A selected `Yes` or `No` has a two-pixel outer indicator that does not change
  button dimensions. `Not answered` remains pale. The indicator is driven by a
  server-rendered state marker rather than an unstable Streamlit DOM attribute.
  Machine names and availability controls share the same vertical center line.
- Expanded machine details use an 18 px vertical gap between field rows and
  the Save action. Selected material tags and the focused material selector use
  the product blue palette, never the validation red palette. The multiselect
  has the same 52 px control height as text inputs and select boxes.
- The `Available in-house?` heading starts on the same vertical line as the
  first availability button.
- `Costing method` exposes only `Not provided`, `Per machine hour`, `Per sheet`,
  `Per part`, `Per job`, and `Quote each job`. Existing internal-cost or
  customer-price provenance remains stored but is not repeated in the labels.

## Catalog groups

### Woodworking

- CNC router
- Panel cutting saw
- Edge bander
- Boring machine
- Veneer or laminating press
- Solid wood preparation line
- Wide-belt sander or calibrator
- Case clamp or assembly press

### Metalworking

- Sheet laser cutter
- Tube laser cutter
- Press brake
- Sheet shear or guillotine
- Punching or hydraulic press
- Tube or profile saw
- Tube or profile bender
- Plate or section rolling machine
- Welding capability
- Deburring or grinding machine
- Drill or tapping station

### Painting and finishing

- Wet-paint spray booth
- Drying or curing chamber
- Powder-coating booth
- Powder-curing oven
- Sandblasting booth
- Washing or degreasing line
- Polishing or buffing station

## Routing price precedence

1. Current approved supplier offer or quote
2. Company-specific supplier quote history
3. Confirmed in-house pricing profile
4. Regional market benchmark with date, region, unit, and confidence
5. `needs_review` when no responsible basis exists

An estimate must retain which level supplied the price. A market benchmark is
never presented as a real supplier quotation.

## Current verification state

- The additive migration and 26-item seed are implemented locally.
- The seventh Company Profile tab implements owner editing and member read-only
  behavior without reading or rewriting the prototype `company_machines` rows.
- In-house cost rates and supplier charges retain distinct rate provenance.
- The deterministic production snapshot is implemented locally.
- 284 repository tests pass, including the new Machinery domain and empty-state
  UI scenarios.
- The owner applied the live Supabase migration on 24.09. A service-role read
  verified five new tables, 26 active catalog rows split into 8 woodworking,
  11 metalworking, and 7 finishing capabilities, and zero company machinery,
  supplier service, offer, or benchmark rows. The 124 prototype
  `company_machines` rows remain untouched. An anonymous-key read is rejected
  with PostgreSQL permission error `42501`.
- Authenticated member-read and owner-write behavior still requires a real
  production session after application deployment; service-role verification
  does not prove those RLS paths.
- The production snapshot is not sent to Anthropic. That would disclose private
  machinery capabilities, supplier identities, and pricing, so it requires an
  explicit owner decision or a separately agreed sanitized payload.
- Production owner/member, persistence, error, refresh, keyboard, and mobile
  acceptance remain pending and must follow the matrix above.
- The first deployment audit found that the new tab slug was missing from both
  application and Cloudflare route allowlists. The same 3.9.1 branch now maps
  `machinery` in both places and protects refresh/back persistence with a
  regression test.
