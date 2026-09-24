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
| Machinery tab opens with no answers | Show the 16 estimation-relevant capabilities in Woodworking, Metalworking, and Painting & Finishing groups; do not create rows merely by viewing |
| Owner changes an availability-only row | Persist Yes, No, or Not answered immediately; do not open details or show Save |
| Owner chooses Yes | Reveal only the minimum capability questions for that machine; do not reveal subcontractor questions |
| CNC router is in-house | Ask working length, working width, maximum thickness, solid wood, horizontal drilling, 5-axis machining, and an optional machine rate per hour |
| CNC machine rate is blank | Store costing as not provided; do not ask for a separate costing-method choice |
| CNC machine rate is provided | Store it as the internal hourly machine rate; derive customer-facing per-part or whole-job prices from machining time plus material, programming, setup, tooling, and labor |
| CNC router handles standard sheet goods | Assume MDF, particleboard / LDSP, plywood, and melamine-faced board; do not ask the owner to confirm them |
| CNC router requires machining on both faces | Treat the second face as another setup; do not ask a vague two-sided-processing question |
| Sheet laser is in-house | Ask working length, working width, laser power, copper / brass, and bevel cutting; show both exceptional capabilities in the first detail column |
| Sheet laser handles common metals | Assume mild steel, stainless steel, and aluminum; do not ask the owner to confirm them |
| Sheet laser requires costing | Do not ask for a generic costing method in Machinery; derive the job from material, thickness, geometry, piercings, setup, gas, and the applicable laser cost profile or benchmark |
| Owner chooses No for an outsourceable operation | Hide in-house details and show one `Regular subcontractor` selector with no contractor, an existing contractor, or add new |
| Owner chooses No for an internal-support capability | Persist No immediately; hide in-house details, Save, and the detail chevron; do not ask for a subcontractor |
| Owner saves No without a subcontractor | Save the explicit absence and show `Market pricing`; later routing may use a regional benchmark with lower confidence |
| Owner saves No with a subcontractor name | Reuse or create the normalized company supplier and attach that service with quote-only pricing |
| Owner removes a regular subcontractor | Select `No regular subcontractor` and save; deactivate the current route without deleting its history |
| Required in-house field is missing | Keep the card editable, mark only the missing field, and do not save a partial confirmed capability |
| Optional value is unknown | Save the capability without inventing a value; show it as not provided |
| Owner selects a pricing method | Ask only the fields needed by that method, such as hourly rate, per-sheet rate, per-part rate, or quote-only |
| Owner selects quote-only | Do not require a structured rate; permit later quote evidence and history |
| Owner saves a valid card | Persist one company machinery profile, collapse its detail panel, show a one-line summary and retain the current tab and scroll context |
| Save is running | Disable that card's controls and save action; duplicate clicks cannot create duplicate rows |
| Save succeeds | Show a short success status without moving other cards or changing tabs |
| Save fails | Preserve every entered value, unlock the card, and show a neutral retryable error |
| Owner edits a saved card | Update the same row; do not create a second active record for the machine code |
| Owner uses the row chevron | Open or close the saved detail panel without changing persisted values |
| Owner changes Yes to No | Require confirmation when a saved in-house profile or pricing data would be deactivated; preserve historical data for estimate audit |
| Member opens Machinery | Show saved capabilities read-only; do not show save, supplier creation, or destructive controls |
| Database migration is not applied | Show one bounded unavailable message; the rest of Company Profile remains usable |
| Refresh, back, or tab switch after save | Reload the persisted state without duplication or loss |
| Narrow/mobile viewport | Cards remain one-column, labels do not clip, and controls retain touch-sized targets |
| Keyboard navigation | Yes/No, fields, supplier selection, and save follow logical focus order and work without pointer input |

### Accepted compact-layout revision

- The tab does not repeat a `Machinery` heading or introductory sentence.
- Technical inputs are arranged in rows of three when space permits and collapse
  naturally on narrow screens.
- Long dimensions such as working length and width are entered as decimal meters;
  thicknesses, tool diameters, and profile sizes remain millimeters. Canonical
  database values remain millimeters.
- Numeric capability inputs are plain text fields with explicit units, not
  number steppers. Both decimal point and decimal comma are accepted.
- A non-in-house outsourceable operation shows one compact `Regular
  subcontractor` selector. It can clear the route, reuse an existing company
  supplier, or reveal one name field for a new supplier. There is no additional
  Yes/No question, pricing method, or lead-time question. Internal-support
  capabilities do not ask for a subcontractor.
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
- Unanswered rows stay compact. Selecting `Yes` or `No` inserts that capability's
  detail panel immediately below its row and spans the full table width. Saving
  collapses it. A chevron reopens or closes a saved panel.
- Every detail panel uses three equal columns for capability, costing, or
  subcontractor fields. It does not introduce another narrow nested card.
- Detail descriptions are omitted. For CNC, row one contains working length,
  working width, and maximum thickness. Row two contains solid wood, horizontal
  drilling, and 5-axis machining. Solid wood and horizontal drilling share the
  first column, 5-axis machining uses the second, and `Costing method` remains
  fixed in the third column below maximum thickness. MDF, particleboard / LDSP, plywood, and
  melamine-faced board are system defaults rather than user questions.
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
  the Save action. Multi-value fields use selectable pills rather than the
  BaseWeb multiselect. Selected pills use the product blue palette, never the
  validation red palette.
- The `Available in-house?` heading starts on the same vertical line as the
  first availability button.
- `Costing method` exposes only `Not provided`, `Per machine hour`, `Per sheet`,
  `Per part`, `Per job`, and `Quote each job`. Existing internal-cost or
  customer-price provenance remains stored but is not repeated in the labels.
- CNC has no costing-method selector. One optional `Machine rate / hour` field
  stays in the third column. Blank means not provided; a value is stored as the
  internal hourly machine rate. Customer-facing per-sheet, per-part, and
  whole-job prices remain derived outputs rather than stored cost bases.
- Sheet laser does not ask for a generic costing method. Its minimum profile
  asks working length, working width, laser power, copper / brass, and bevel
  cutting. The two exceptional capabilities share the first detail column.
  Mild steel, stainless steel, and aluminum are treated as baseline materials;
  tube laser remains a separate capability rather than a checkbox.
- Only questions that materially change feasibility or price are shown.
  Panel cutting saw, edge bander, solid wood machining, wide-belt sanding, and
  solid metal machining, sandblasting, and galvanizing are availability-only. CNC retains working size,
  maximum thickness, three exceptional capabilities, and costing. Sheet laser
  cutting and size-dependent finishing retain their feasibility or maximum-size
  fields. Sheet metal bending, metal press, profile bending, rolling, and
  welding are availability-only. Polishing is manual-tool work and is not shown
  as Machinery. Labels use the shortest unambiguous wording.
- `Accept external work` is not an estimation input and is not asked anywhere.

## Catalog groups

### Woodworking

- CNC router
- Panel cutting saw
- Edge bander
- Veneer or laminating press
- Solid wood machining
- Wide-belt sander or calibrator

### Metalworking

- Sheet laser cutter
- Sheet metal bending
- Metal press
- Tube / profile bending
- Metal rolling
- Solid metal machining

### Painting and finishing

- Wet painting
- Powder coating
- Sandblasting
- Galvanizing

The database catalog keeps all 27 additive seed rows for compatibility and
historical estimate audit. The profile asks only the 16 capabilities above.

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
- 291 repository tests pass, including the reduced profile catalog,
  availability-only machines, collapsed saved rows, removable subcontractors,
  pills, and empty-state UI scenarios.
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
