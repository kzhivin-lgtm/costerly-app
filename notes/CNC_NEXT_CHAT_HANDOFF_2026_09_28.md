# Costerly AI: complete chat handoff, CNC / Laser next

Date: 2026-09-28
Next active task: 3.14.1, CNC / Laser costing foundation and Platform Admin interface
Authoritative checkout: `/Users/qb/Documents/Codex/2026-07-17/detection-gpt-detection-agent-ocr-gpt/work/costerly-progress`
Handoff workspace: `/Users/qb/Documents/ChatGPT/Costerly`

## 1. Purpose of this handoff

The next chat is dedicated to CNC and sheet-laser preliminary costing. It must
continue from the decisions and implementation state below without rebuilding
the architecture, expanding Machinery, or treating the current Estimation
scaffold as a benchmark.

This document also records the broader work completed during the chat because
several accepted UI, authorization, data, and design-system decisions constrain
the CNC work.

## 2. Current repository state

### Accepted production checkpoints relevant to this chat

- `d99a594`, task 3.12.1: fast Price Lists interactions, snapshot reuse,
  invalidation after mutations, lower Needs review headings, no duplicate
  fragment reruns.
- `1a2d7ca`, task 3.12.1: Price Source uploader checkpoint, one structured
  document at a time, multiple JPEG/PNG pages, previews, duplicate handling,
  deterministic drag rejection, persistent terminal feedback.
- `86fd769`, task 3.12.4: existing-email registration rejection and repeated
  validation behavior.
- `d8e0c8e`, task 3.13.1: accepted Platform Admin company matrix.
- `dcefabb`, task 3.13.4: accepted Price Lists empty-state geometry and exact
  vertical centering.
- Current repository `HEAD` when this handoff was written: `c16aa69`,
  `Record Price Lists alignment checkpoint`.

### Uncommitted state that must be preserved

At handoff creation, the checkout is intentionally dirty:

```text
 M agents/prompts/price_source_agent_prompt.md
 M notes/PRICE_SOURCE_AGENT.md
 M notes/PROJECT_MAP.md
 M notes/TODO.md
 M screens/company_profile.py
 M tests/test_price_sources.py
 M use_cases/price_sources.py
?? .streamlit
?? db/sql/2026_09_28_manufacturing_cost_parameters.sql
?? notes/CNC_LASER_COSTING.md
?? tests/test_manufacturing_cost_parameters.py
?? tmp/
```

The pre-existing Price Source changes and `.streamlit/` and `tmp/` belong to the
ongoing workspace. Do not discard, reset, or overwrite them. In particular,
`screens/company_profile.py` already contains unrelated Price Source B2 changes.
Inspect the diff before any edit to that file.

### New 3.14.1 files prepared in the last turn

- `notes/CNC_LASER_COSTING.md`: protected Machinery boundary, four-calculator
  architecture, Admin information architecture, scenario matrix, precedence,
  staged delivery, and non-goals.
- `db/sql/2026_09_28_manufacturing_cost_parameters.sql`: additive versioned
  parameter registry and Platform Staff-only read RPC.
- `tests/test_manufacturing_cost_parameters.py`: catalog preservation, migration
  safety, authorization, audit, and plan-contract tests.
- `notes/PROJECT_MAP.md`: references the new migration and architecture note.

The migration has not been applied to production. No current Estimation behavior
has been changed. The new focused suite passed 17 tests and `git diff --check`.

## 3. Product and working rules established during the chat

### Design system

- Reuse established Costerly AI components and geometry. Do not invent local
  approximations when Overhead Expenses or another accepted screen already
  solves the same pattern.
- Every table and table-like row value, label, action, and empty-state message
  must be vertically centered against the actual content box.
- Use full-height wrapper geometry and `align-items: center`. Do not use guessed
  `top`, `translateY`, negative margins, or visual offsets.
- For disputed alignment, inspect the real rendered DOM in the authenticated
  browser and compare the content center with the row center numerically.
- Preserve accepted gaps, paddings, borders, radii, and button geometry. Do not
  redesign adjacent sections while fixing one requested element.
- User-facing product copy uses `Coasterly AI`. Existing technical domains and
  the sender display name `Coasterly` remain unchanged.

### Implementation and acceptance

- Enter tester mode before UI implementation. Agree the scenario matrix, use it
  for deterministic tests, and then verify the real production scenarios.
- Source inspection and tests do not replace authenticated browser acceptance.
- Keep the last accepted checkpoint protected. A later experiment remains an
  experimental branch until its scenario matrix is verified.
- Fix the earliest supported cause. Do not stack CSS or state workarounds on an
  unresolved cause.
- Always state `How we verify` or `Как проверяем` in the final implementation
  summary.
- Do not commit or push unless the user explicitly requests it.

## 4. Broader chat chronology and settled decisions

### 4.1 Price Lists layout and interaction

The user iterated on Material Prices, Needs review, removal confirmation,
pagination, edit actions, and empty states.

Settled behavior:

- `Material Prices` is the outer heading above Wood.
- Wood is visually inside Material Prices. Metal and Coating remain separate
  cards with gaps.
- Material rows have no visual gaps. Needs review rows also have no visual gaps.
- Supplier behavior was explicitly protected and not changed during layout work.
- Existing selected-row highlighting stays where it already exists. Missing
  Source highlighting was not added.
- Edit `Cancel` sits close to `Save Price` and uses the established secondary
  treatment. Edit buttons use the accepted compact height.
- Removal `Remove` and `Cancel` are close enough to read as one action group and
  remain wide enough to show their labels.
- Needs review pagination is a compact group: Previous, Next, then page count,
  with small gaps, left and bottom inset, not distributed across the card.
- Needs review column headings align with the body columns and Review action.
- Empty `No active prices` rows use the normal row background and are vertically
  centered by the real wrapper geometry. The accepted fix removed the scoped
  negative bottom margin rather than adding another offset.
- The accepted empty-state checkpoint is `dcefabb`.

### 4.2 Price Source uploader

MVP ingestion contract:

- One PDF, XLSX, or CSV at a time.
- JPEG and PNG may be combined as multiple pages in one image flow.
- Mixed types do not become an independent mixed-document queue in this MVP.
- If a structured file is already accepted, dropping another structured file
  keeps the first file and rejects the second.
- Rejection turns only the occupied drop card outline red while the invalid file
  is over the zone. Leaving the zone clears the drag state correctly.
- The accepted file preview remains visible during rejection.
- A yellow guidance message appears only after an actual rejection. It does not
  reserve extra empty space in the zero state.
- A single structured file is displayed as a large centered preview. PDF, XLSX,
  CSV, JPEG, and PNG all have a recognizable preview treatment.
- Image pages use a grid, four per row, with scrolling after the bounded visible
  area.
- Repeated exact files must return explicit terminal feedback. A renamed file
  with identical bytes must not silently end after the spinner.
- A duplicate must not trigger another expensive extraction. Terminal feedback
  such as `Already processed`, unresolved count, time, and tracked cost remains
  visible.
- Loading state must begin immediately and terminate in success, duplicate,
  unresolved, or error. A button that stops spinning without feedback is a
  severe user-facing bug.
- Accepted uploader checkpoint: `1a2d7ca`.

### 4.3 Internal estimates and source normalization

The product must accept the customer's previous internal calculation sheets as
a high-value price source, even when supplier identity is absent.

Settled concept:

- Internal calculations are a distinct source origin, not a fake supplier.
- They may contain known paid or estimated prices without manufacturer or
  supplier information.
- Variants such as `10 mm plywood`, `plywood 1 cm`, different word order, and
  different languages must ultimately resolve to canonical material entities
  while retaining original source text and evidence.
- Repeated uploads should distinguish new, updated, unchanged, and unresolved
  rows rather than paying to recreate identical work.
- UI/taxonomy completion must remain separate from extraction quality. A clean
  interface does not mean a `0 prices` extraction is solved.

Current dirty Price Source files contain unfinished work in this area. The next
CNC chat must preserve them but should not mix them into task 3.14.1.

### 4.4 Registration and email validation

- Existing emails are rejected after submit on the original registration form.
- Invalid email syntax shows a specific inline message before the primary action.
- Existing-email validation must work repeatedly in one session, not only for the
  first occupied address.
- The confirmation screen must not open when validation fails.
- Shared email validation and error placement were unified across auth screens.
- Duplicate database/auth calls that caused two flashes were reduced to one
  stable transition.
- Accepted existing-email checkpoint: `86fd769`.

### 4.5 Platform Admin dashboard

Authorization:

- Company database roles remain `owner/member`.
- User-facing roles are `Company Admin/Team Member`.
- Platform access is independent through `platform_staff` with
  `platform_admin/platform_viewer`.
- Company registration or ownership never grants Platform Admin access.

Accepted dashboard columns:

- Company
- Stage: test, pilot, paid
- Users
- Sessions in rolling 7-day and 30-day windows
- Files
- Repeat files
- Detection count and tracked USD cost
- Estimation calls and tracked USD cost
- Price Lists sources and tracked USD cost
- PDFs, unavailable until proposal persistence exists
- Total AI cost in USD
- Factual operational status

The dashboard is a compact Overhead Expenses-style matrix. It has no period or
stage filters and no company-detail page in the accepted first version. Dollar
signs appear beside values, not in headings. Cross-company access is audited.

Accepted checkpoint: `d8e0c8e`.

### 4.6 Company reset, invitations, and new-company observations

During the chat, the user requested a clean test start by deleting three test
companies and their user/product data, then created a new company. The actual
current live database contents must be reverified before relying on that state.
Do not assume that the historical deletion or Platform Staff assignment still
describes production without a fresh read.

The user also observed an invalid or expired verification link returning to a
previously authenticated `core.costerly.ai` session and a brief Streamlit frame.
That behavior was discussed in the context of invitation and auth routing. It is
not part of CNC task 3.14.1 and must not be silently bundled into CNC changes.

### 4.7 Machinery profile and empty-state cleanup

The accepted Machinery and Price Lists work established that new-company and
empty states are first-class acceptance scenarios. The user specifically created
a clean company to expose bad zero-state geometry.

For future CNC Admin work, always test:

- no parameter rows;
- one row;
- multiple material/thickness scopes;
- long source names and URLs;
- viewer versus admin permissions;
- failed load and failed save;
- refresh and history view;
- narrow viewport;
- real authenticated production transition.

## 5. CNC / Laser problem definition

### 5.1 Business context

Costerly AI serves furniture and custom fabrication companies estimating a job
before they have won it. At that point they usually have architectural drawings,
specifications, PDFs, images, or approximate dimensions, but not production-ready
DXF/CAM files.

This is fundamentally different from a cutting bureau that receives a finished
DXF, nests it, calculates exact toolpath length, machine time, piercings, gas,
tool wear, and then quotes a production service.

Costerly AI must estimate the probable cost before exact production engineering
is economically justified. The output must therefore be useful and defensible,
but it must not pretend to have CAM precision.

### 5.2 Two production routes

For both woodworking CNC and sheet-metal laser there is an explicit route split:

- `in_house`: estimate the company's own resource cost.
- `subcontractor`: estimate the price a third-party supplier will charge,
  including its commercial margin, minimum, setup or file preparation, material
  inclusion, delivery, urgency, and secondary operations where applicable.

The four calculators are independent:

1. CNC Router, in-house
2. CNC Router, subcontractor
3. Sheet Laser, in-house
4. Sheet Laser, subcontractor

Do not average coefficients across these calculators. The cost structures differ.

### 5.3 No separate CNC agent

There is no separate CNC agent in the accepted architecture.

The future flow is:

```text
Customer documents
  -> Estimation feature extraction
  -> deterministic Manufacturing Route Resolver
  -> one of four deterministic calculators
  -> parameter snapshot and provenance
  -> P10 / P50 / P90 cost range, confidence, and explanation
```

The model extracts evidence and bounded manufacturing features. Deterministic
code owns route validation and arithmetic. This avoids repeated model calls,
untraceable calculations, and unnecessary token cost.

### 5.4 Current Estimation is not a benchmark

The current Estimation Agent is an early end-to-end scaffold. Its result,
weights, logic, and accuracy are not a baseline to preserve or tune. Legacy
machining-point weights are explicitly excluded.

Task 3.14.1 prepares reliable machinery and cost data before rebuilding the real
Estimation flow.

### 5.5 No assumed post-factum feedback

The first product version cannot assume customers will provide actual machine
time, final subcontractor invoices, DXF-derived totals, or explicit positive and
negative feedback after every estimate.

Therefore:

- do not make automatic learning a dependency for initial accuracy;
- use versioned reviewed parameters and honest uncertainty;
- preserve future fields for actuals and calibration, but do not claim those
  actuals exist;
- user satisfaction is not a substitute for verified cost data;
- estimate use or PDF generation may signal value, but it does not validate the
  numerical manufacturing model.

## 6. Protected Machinery boundary

### 6.1 Current Company Profile subset

The application stores 27 machine codes for compatibility and audit, but Company
Profile deliberately presents only 16 estimation-relevant capabilities.

Exact current codes and labels:

| Group | Machine code | Label |
| --- | --- | --- |
| Woodworking | `wood_cnc_router` | CNC router |
| Woodworking | `wood_panel_saw` | Panel cutting saw |
| Woodworking | `wood_edge_bander` | Edge bander |
| Woodworking | `wood_veneer_press` | Veneer or laminating press |
| Woodworking | `wood_solid_preparation` | Solid wood machining |
| Woodworking | `wood_wide_belt_sander` | Wide-belt sander or calibrator |
| Metalworking | `metal_sheet_laser` | Sheet laser cutter |
| Metalworking | `metal_press_brake` | Sheet metal bending |
| Metalworking | `metal_punch_press` | Metal press |
| Metalworking | `metal_profile_bender` | Tube / profile bending |
| Metalworking | `metal_rolling_machine` | Metal rolling |
| Metalworking | `metal_profile_saw` | Solid metal machining |
| Finishing | `finish_wet_spray_booth` | Spray painting |
| Finishing | `finish_powder_booth` | Powder coating |
| Finishing | `finish_sandblast_booth` | Sandblasting |
| Finishing | `finish_galvanizing` | Galvanizing |

### 6.2 Decision: do not expand Machinery

No machinery row is added in task 3.14.1.

`wood_boring_machine` exists in the 27-code storage catalog but intentionally
stays outside Company Profile. Hole count, shelf holes, hinge boring, grooves,
pockets, internal cutouts, and similar features are workload inputs. They do not
justify another mandatory machine question in the shortened company profile.

The route resolver will use:

- presence or absence of CNC router;
- presence or absence of panel cutting saw;
- presence or absence of edge bander;
- sheet laser and metal-forming capabilities;
- documented job geometry and operations;
- configured regular subcontractor routes;
- explicit uncertainty and `needs_review` when evidence is insufficient.

Potential future evidence might justify a new capability, but convenience or
calculation detail alone is not sufficient. Expanding the profile is a separate
consequential decision requiring explicit approval.

### 6.3 Important routing ambiguity

Absence of CNC does not mean every panel job goes to a CNC subcontractor.

Examples:

- Simple rectangular panels may be cut in-house on a panel saw.
- A job with many repeated holes, grooves, pockets, curved contours, or tight
  positional relationships is more likely to require CNC.
- A small company may batch several jobs into one subcontractor delivery, so a
  full delivery fee may not belong to one estimate.
- A subcontractor minimum may dominate a small order.
- A job may be mixed: panel saw for rectangular cutting, outsourced CNC for
  selected parts or internal features, then in-house edge banding and assembly.

The resolver must represent these as routes and uncertainty, not as an LLM guess
hidden inside a total-price multiplier.

## 7. Costing methodology

### 7.1 General method

Use a hybrid of:

1. feature and process-based workload estimation from customer documents;
2. time-driven activity-based costing for in-house work;
3. supplier-specific or market-curve pricing for subcontracted work;
4. future calibration against verified quotes and actuals when they become
   available;
5. a cost range and confidence rather than false point precision.

### 7.2 CNC Router, in-house

```text
material_cost
+ programming_time * programmer_rate
+ setup_time * attended_labor_rate
+ machine_run_time * machine_capacity_rate
+ attended_run_time * operator_rate
+ energy
+ tooling_and_consumables
+ loading_unloading
+ secondary_operations
+ expected_rework
```

The actual CNC operator salary should come from the company's Labor Costs when
available. Do not ask the company for the same salary again in Machinery. The
company-specific salary overrides a market wage fallback.

Separate machine capacity rate from labor rate to prevent double counting:

```text
machine_capacity_rate = annual_machine_capacity_cost / practical_machine_hours
labor_capacity_rate = annual_loaded_labor_cost / practical_labor_hours
```

Machine capacity cost may include depreciation or lease, finance, maintenance,
service, software, allocated floor cost, and insurance. Electricity and tooling
can remain variable when measurable.

### 7.3 CNC Router, subcontractor

```text
max(provider_minimum,
    bundled_sheet_or_material_charge
  + programming_or_file_preparation
  + cutting_charge
  + internal_feature_charge
  + edge_banding
  + secondary_operations)
+ allocated_delivery
+ rush_surcharge
```

Material inclusion, setup, minimum charge, delivery, VAT, and file-preparation
scope must be explicit. Do not add a supplier minimum after the calculated total
already exceeds it.

### 7.4 Sheet Laser, in-house

```text
sheet_material_cost
+ programming_and_nesting
+ setup
+ cut_time * machine_capacity_rate
+ pierce_time * machine_capacity_rate
+ attended_labor
+ assist_gas
+ electricity
+ nozzles_lenses_and_consumables
+ loading_unloading
+ deburr_and_secondary_operations
+ expected_rework
```

Cut speed depends on material, thickness, laser power, gas, nozzle, quality mode,
and machine class. Do not store one universal laser speed.

### 7.5 Sheet Laser, subcontractor

```text
max(provider_minimum,
    provider_setup
  + provider_cut_basis
  + material_if_not_included
  + file_preparation
  + secondary_operations)
+ allocated_delivery
+ rush_surcharge
```

Provider rates expressed per cut meter and per machine minute are different
commercial models. Do not average them into one rate.

## 8. Feature contract for future Estimation

The future Estimation extraction should return evidence, ranges, and uncertainty
for the following, without performing cost arithmetic:

- process candidate: CNC router, sheet laser, or neither;
- quantity or range;
- repeated part groups and counts;
- material family, grade, finish, and thickness;
- visible overall dimensions;
- estimated net panel or sheet area;
- part count low, typical, and high;
- rectangular perimeter;
- freeform contour length range;
- internal cutouts and approximate perimeter;
- holes by size band;
- grooves and pockets by count, length, area, and depth;
- number of faces or setups;
- bends, welding, deburring, coating, and other secondary operations;
- tolerance and edge-quality class;
- drawing completeness and source evidence;
- delivery location and urgency only when commercially relevant.

Missing material or thickness must reduce confidence or trigger review. It must
not be silently replaced by a convenient default.

## 9. Pre-DXF workload equations

### 9.1 Material utilization

```text
gross_sheet_area = net_part_area / nesting_yield
sheet_count = ceil(gross_sheet_area / usable_sheet_area)
```

Initial nesting values remain low-confidence platform priors, stored as ranges by
geometry class. They are not universal facts.

### 9.2 CNC time

```text
cut_minutes = effective_contour_length / effective_feed_rate * pass_count
drill_minutes = hole_count * seconds_per_hole / 60
pocket_minutes = pocket_area_or_length_model
machine_minutes = cut_minutes + drill_minutes + pocket_minutes
                + tool_changes + rapid_moves + non_cutting_cycle_time
job_minutes = programming + setup + sheet_handling + machine_minutes
```

Thickness, tool diameter, material, depth of cut, and number of passes affect
effective feed. A single speed for all wood products is invalid.

### 9.3 Laser time

```text
cut_minutes = sum(cut_length_by_material_thickness / effective_cut_speed)
pierce_minutes = sum(pierce_count_by_material_thickness * pierce_seconds) / 60
machine_minutes = cut_minutes + pierce_minutes + rapid_moves + sheet_exchange
gas_cost = gas_flow_per_cut_hour * gas_price * cut_hours
energy_cost = average_production_kw * electricity_price * production_hours
```

## 10. Uncertainty and confidence

Each uncertain workload input is a distribution or low, typical, high tuple.
The deterministic calculator produces P10, P50, and P90 cost.

Initial uncertainty priority:

1. part count and dimensions;
2. material and thickness;
3. nesting yield and purchased sheet count;
4. holes, cutouts, grooves, and pockets;
5. setup and programming complexity;
6. machine class and effective process speed;
7. subcontractor minimum and inclusion boundary;
8. delivery, urgency, and secondary operations.

Do not apply a generic complexity multiplier to total cost. Complexity changes
specific workload drivers and prediction spread.

Confidence is derived from source quality, evidence completeness, similarity,
and range width. It is not a manually invented precise percentage.

Suggested classes:

- High: company-specific values and verified comparable evidence, with scope
  known.
- Medium: document drivers mostly known and only limited reviewed fallbacks.
- Low: several platform priors, unknown provider, missing geometry, or unclear
  inclusion boundary.
- Review required: unsupported operation, critical missing material, out-of-
  envelope part, compound machining, or critical tolerance.

## 11. Parameter precedence and versioning

Resolution order:

1. actual value or invoice for the company and job, when later available;
2. configured company value;
3. approved comparable company cohort, only if such a model is later accepted;
4. current named Israeli provider benchmark;
5. official or manufacturer technical benchmark;
6. explicit versioned platform prior.

Every estimate must store the exact resolved parameter IDs and versions. Editing
an Admin parameter creates a replacement version and archives the previous
record. Historical estimates remain reproducible.

The prepared schema stores:

- calculator identity;
- parameter key;
- country and optional region;
- material family;
- thickness range;
- machine and object family;
- structured qualifiers;
- low, typical, and high values;
- unit and optional currency;
- source type, name, URL, date, and evidence;
- confidence;
- candidate, reviewed, active, or archived status;
- version and superseded parameter;
- effective dates;
- creator and approver;
- approval timestamp and notes.

Active parameters require a source URL and explicit approval metadata. A partial
unique index prevents two Active rows for the same calculator and scope.

## 12. Israeli data already researched

The full research document is:

`/Users/qb/Documents/ChatGPT/Costerly/CNC_LASER_PRE_DXF_COSTING_RESEARCH_2026-09-28.md`

Important researched candidates:

### Official or technical inputs

- Israel uniform electricity variable tariff, January 2026: ₪0.5451/kWh.
- Employer National Insurance formula inputs: 4.51% below the reduced-rate
  threshold and 7.60% above it.
- Average wage under section 1, January 2026: ₪13,566/month. This is a fallback
  reference, not a CNC-operator salary.
- TRUMPF published production power examples and laser-process factors.
- Amana Tool and LMT Onsrud cutting-data references for feeds and chip load.
- TDABC references for capacity-cost rates and practical capacity.

### Wood CNC subcontractor candidates

Algolan Express publishes bundled panel material plus cutting prices excluding
VAT, including examples such as white melamine 17 mm at ₪220/panel, exposed
plywood 17 mm at ₪210/panel, birch plywood 18 mm at ₪280/panel, and green MDF in
several thicknesses. It also publishes internal operations at ₪12 per affected
part and edge banding at ₪6/m for 17 mm and ₪11/m for 28 mm.

This is a named provider candidate, not a universal Israeli market rate. Sheet
dimensions, delivery, publication date, and minimum conditions need explicit
treatment.

Bemida's broad DXF cutting range is only a low-confidence sanity check because
its inclusion boundary is unclear.

### Sheet-laser subcontractor candidates

Iron Laser publishes material- and thickness-specific per-cut-meter ranges and a
typical ₪200 to ₪400 minimum. It states material is usually included but this
must be confirmed per quote.

Laser Portal publishes a different model, approximately ₪20 to ₪40 per machine
minute with a ₪1,500 minimum, excluding VAT and file preparation.

These sources must remain separate. Their commercial segments and inclusion
boundaries differ, so averaging them would destroy useful information.

### Activation policy

Potentially Active after review:

- official electricity tariff;
- official statutory formula inputs;
- actual company salary and machine inputs after validation.

Reviewed or Candidate:

- Algolan provider rates;
- Iron Laser curves and minimum;
- Laser Portal minute model and minimum;
- manufacturer technical tables.

Low-confidence platform priors:

- nesting distributions;
- setup and handling times;
- programming times;
- operator-attendance fractions;
- non-standard freeform CNC market rate.

Never activate:

- legacy machining-point weights;
- one universal CNC or laser hourly rate;
- a generic total-cost complexity multiplier;
- dated or inclusion-ambiguous material prices presented as current facts;
- averaged conflicting provider models.

## 13. Platform Admin CNC / Laser interface

### Navigation

The existing `Admin` screen receives one additional Platform Staff-only action:
`CNC / Laser`. It is not a global public navigation item and is not visible to
Company Admin or Team Member users.

### Information architecture

Process-first layout:

```text
CNC Router
  In-house
  Subcontractor

Sheet Laser
  In-house
  Subcontractor
```

Each route contains one compact table with:

- Parameter
- Scope
- Low
- Typical
- High
- Unit
- Source
- Source date
- Confidence
- Status
- Version
- Action

Platform Viewer is read-only. Platform Admin may later create replacement
versions through a controlled form. Neither role receives raw direct database
table editing.

### Scenario matrix

1. Non-Platform Staff sees no action and cannot open the direct route.
2. Platform Viewer sees all values and provenance but no edit action.
3. Platform Admin sees the same table and an edit action.
4. Empty route shows one bounded empty row, not invented defaults.
5. Point value displays the same low, typical, and high value.
6. Range validates `low <= typical <= high`.
7. Material and thickness scope remains explicit.
8. Candidate without sufficient evidence cannot become Active.
9. Edit inserts a new version and archives the old Active version atomically.
10. Failed save preserves inputs and the previous Active record.
11. History view resolves archived versions used by older estimates.
12. Unsupported scope returns `needs_review` rather than nearest-neighbor guess.
13. Load failure remains bounded and does not expose a traceback.
14. Refresh, route transition, and authenticated browser state remain stable.
15. All rows follow the accepted full-height vertical-centering rule.

## 14. Prepared SQL foundation

Migration:

`db/sql/2026_09_28_manufacturing_cost_parameters.sql`

It currently provides:

- additive `manufacturing_cost_parameters` table;
- four allowed calculator identities;
- strict range, thickness, date, currency, source, status, and approval checks;
- version and supersession references;
- one-Active-record-per-scope protection;
- RLS enabled and no direct public, anonymous, or authenticated table grants;
- service-role access;
- guarded Platform Staff read RPC;
- audit event for parameter viewing.

It deliberately does not yet provide:

- production seed rows;
- edit/version-replacement RPC;
- Admin route or UI;
- calculator code;
- Estimation integration.

The migration is prepared locally but not applied to production.

## 15. Delivery plan for the next chat

Retain task number 3.14.1 across these revisions. Do not invent a new block
number unless the user explicitly approves a block transition.

### Revision A: validate and apply data foundation

1. Reinspect current Git status and preserve unrelated dirty changes.
2. Re-read `notes/CNC_LASER_COSTING.md`, this handoff, the research document,
   `notes/MACHINERY_FOUNDATION.md`, and the SQL migration.
3. Validate migration against the real Supabase schema and existing
   `platform_staff` and audit tables.
4. Add any missing repeat-safety checks found during inspection.
5. Apply the complete migration once, using the established database workflow.
6. Verify table shape, constraints, RLS, grants, unauthorized rejection,
   Platform Viewer read, Platform Admin read, and audit event creation.

Success means the schema is live and empty, no company-facing behavior changes,
and current Estimation output remains untouched.

### Revision B: read-only Admin page

1. Add the `CNC / Laser` action inside Admin only.
2. Add an explicit route and guard it with fresh `platform_staff` access.
3. Reuse the Admin header actions and accepted table system.
4. Render CNC Router and Sheet Laser, each with In-house and Subcontractor.
5. Implement empty, loading, unavailable, populated, viewer, and unauthorized
   scenarios.
6. Audit the page view without exposing customer content.
7. Verify in the real authenticated production browser.

Do not add editing during this revision.

### Revision C: controlled versioned editing

1. Add a security-definer replacement RPC for Platform Admin only.
2. Validate parameter identity, scope, ranges, source, confidence, and approval.
3. Archive the previous Active row and insert the replacement in one transaction.
4. Write an audit event containing IDs and changed field names, not secrets.
5. Platform Viewer remains read-only.
6. Add history inspection and failed-save preservation.

### Revision D: reviewed Israeli seed set

1. Convert each researched source into explicit parameter rows.
2. Keep provider identities and inclusion boundaries separate.
3. Mark official values, reviewed market candidates, and platform priors
   distinctly.
4. Do not activate low-confidence hypotheses automatically.
5. Review the complete visible Admin tables with the user before any calculator
   consumes the data.

### Revision E: four deterministic calculators

1. Define typed input and output contracts.
2. Implement each route independently.
3. Resolve parameters through the approved precedence chain.
4. Store parameter IDs and versions in the calculation result.
5. Return line-item decomposition, P10/P50/P90, confidence, and review reasons.
6. Add fixtures for simple, mixed, irregular, minimum-dominated, repeated,
   missing-thickness, secondary-operation, and out-of-envelope jobs.

### Revision F: Estimation integration

Only after the parameter UI and calculators are accepted:

1. replace the current Estimation scaffold with the approved feature contract;
2. implement the deterministic route resolver;
3. pass only bounded extracted features into deterministic code;
4. retain source evidence and uncertainty;
5. compare latency and cost with the current end-to-end flow;
6. verify that CNC detail does not create an unnecessary extra agent cycle.

## 16. Verification contract for 3.14.1

Every implementation summary must include `Как проверяем`.

Minimum automated verification:

- exact 16-code profile remains unchanged;
- no `wood_boring_machine` profile regression;
- additive migration contains no destructive operations;
- four calculator identities only;
- low, typical, high ordering;
- one Active row per exact scope;
- Active source and approval requirements;
- unauthorized RPC rejection;
- viewer read and admin read;
- audit events;
- replacement version atomicity once implemented;
- current Machinery and Platform Admin suites still pass;
- `git diff --check`.

Minimum real acceptance:

- Company Admin and Team Member do not see `CNC / Laser`;
- Platform Viewer sees read-only tables;
- Platform Admin sees permitted actions;
- direct unauthorized URL fails safely;
- zero-state page is complete and aligned;
- source URL, long scope, ranges, confidence, and version are readable;
- one failed load and one failed save are bounded;
- refresh and navigation show no stale Streamlit screen;
- rows are vertically centered by measured container geometry;
- no current Estimation result changes before Revision F.

## 17. Immediate next action

The next chat should not begin with more market research or Machinery expansion.
It should begin by inspecting the prepared 3.14.1 files and validating the SQL
foundation against the current database contract. If the migration remains
sound, apply and verify Revision A, then continue directly to the read-only Admin
page.

## 18. Reference files

Authoritative implementation and product notes:

- `notes/CNC_NEXT_CHAT_HANDOFF_2026_09_28.md`
- `notes/CNC_LASER_COSTING.md`
- `notes/MACHINERY_FOUNDATION.md`
- `notes/PLATFORM_ADMIN.md`
- `notes/PROJECT_MAP.md`
- `use_cases/machinery.py`
- `use_cases/platform_admin.py`
- `screens/platform_admin.py`
- `db/sql/2026_09_24_machinery_foundation.sql`
- `db/sql/2026_09_28_manufacturing_cost_parameters.sql`
- `tests/test_machinery.py`
- `tests/test_manufacturing_cost_parameters.py`
- `tests/test_platform_admin.py`

Detailed external research:

- `/Users/qb/Documents/ChatGPT/Costerly/CNC_LASER_PRE_DXF_COSTING_RESEARCH_2026-09-28.md`
