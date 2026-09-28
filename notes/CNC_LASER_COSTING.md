# CNC / Laser Costing

Task: 3.14.1
Status: architecture and data foundation in progress

## Product boundary

This task prepares the parameter registry and Platform Admin interface used by
future preliminary CNC and sheet-laser estimates. It does not preserve or tune
the current Estimation scaffold, and it does not send these values to an agent.

The estimate stage is before DXF, CAM, nesting, or a supplier quotation exists.
The future Estimation flow extracts bounded manufacturing features from customer
documents. Deterministic routing and calculators select the production route and
perform arithmetic.

## Protected Machinery contract

The Company Profile remains the accepted 16-capability subset:

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

- Spray painting
- Powder coating
- Sandblasting
- Galvanizing

No machine is added for task 3.14.1. The 27-code storage catalog remains for
compatibility and historical audit, but it is not expanded in Company Profile.

In particular, `Boring machine` stays outside the profile. Hole count, hinge
boring, shelf holes, grooves, pockets, and other internal features are workload
inputs. The route resolver uses the existing CNC capability, panel saw, edge
bander, supplier route, and document evidence to decide feasibility. They are
not extra machinery questions.

## Demand-driven calculation strategies

The manufacturing engine does not run four calculations for every estimate.
It first determines whether the documented work requires CNC routing or sheet
laser cutting at all. Material alone is not sufficient: a metal part does not
activate laser cutting unless its required operations call for it.

For each required process, the Company Profile supplies one exclusive route:

1. CNC router, in-house or subcontractor
2. Sheet laser, in-house or subcontractor

Only the applicable strategy runs. A project may invoke more than one strategy
only when different documented parts require different processes. Parameters
and calibration remain separate between strategies. A shared value such as an
electricity tariff may be referenced by several strategies, but learned process
coefficients are never silently shared.

## CNC estimate level

The CNC row in Machinery owns one estimate level for its currently selected
route. If CNC is available in-house, the level applies only to the in-house
strategy. If CNC is not available in-house, the level applies only to the
subcontractor strategy. Both routes are never active at the same time.

`Estimate reserve` selects how much reserve is included in the CNC cost estimate:

1. Minimum reserve
2. Low reserve
3. Standard reserve
4. High reserve
5. Maximum reserve

The help text explains the direction in plain language: level 1 gives the
lowest estimate with the least reserve, level 5 gives the highest estimate with
the most reserve, and level 3 is the standard setting.

Level 3 is the effective default. Merely viewing or saving other Machinery data
does not turn that default into feedback. Only an explicit level change is
persisted as a calibration event. The event records company, user, active route,
previous level, selected level, and time. It does not contain estimate cost or
customer content.

This is behavioral calibration, not verified manufacturing truth. Aggregate
changes may identify a systematic bias worth reviewing, but they do not
automatically rewrite platform parameters. A later estimate-specific override
will remain separate from the Company Profile default.

### Accepted UI checkpoint, 2026-09-28

- Keep Streamlit's native thin slider geometry and native color.
- Show the current reserve name in muted gray beside `Estimate reserve`.
- Keep the question-mark help text operational.
- Do not add screen-specific track, fill, thumb, or mutation-observer styling.

## Admin information architecture

`Admin` receives one Platform Staff-only action named `CNC / Laser`.

The page is process-first because the user arrives to inspect one calculation
model:

1. `CNC Router`
   - `In-house`
   - `Subcontractor`
2. `Sheet Laser`
   - `In-house`
   - `Subcontractor`

Each route shows one table of parameters. Columns are:

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

Editing an active parameter creates a new version and archives the replaced
record. It never rewrites a value used by an older estimate. Company users do
not see this page and do not receive direct table access.

## Scenario matrix

| State or action | Expected behavior |
| --- | --- |
| Non-Platform Staff user | No `CNC / Laser` action exists; a direct route is rejected |
| Platform Viewer opens the page | May inspect all values, sources, confidence, status, and versions; cannot edit |
| Platform Admin opens the page | May inspect and open the edit action |
| No parameters exist for a route | Show a bounded empty row, not invented defaults |
| Parameter has low, typical, and high | Preserve `low <= typical <= high` and display all three |
| Parameter is a point value | Store and display the same value in low, typical, and high |
| Scope contains material or thickness | Display the scope explicitly; do not flatten it into the parameter name |
| Source is missing | Candidate may be saved, but cannot become Active |
| Platform Admin edits a parameter | Insert a new version, archive the previous Active row, and audit the change |
| Save fails | Keep the entered values and the previous Active record unchanged |
| Existing estimate references an old version | The old record remains immutable and resolvable |
| Calculator requests an unsupported scope | Return `needs_review`; do not choose the nearest value silently |
| CNC is available in-house | Show and use only the in-house estimate level |
| CNC is not available in-house | Show and use only the subcontractor estimate level |
| CNC estimate level remains untouched | Use effective level 3 without recording feedback |
| Owner explicitly changes the CNC estimate level | Persist the active-route level and append one bounded calibration event |
| Member opens Machinery | Show the saved active-route level read-only |

## Parameter precedence

1. Actual company value for the job, when later available
2. Configured company value
3. Comparable company history, when a future approved cohort model exists
4. Current named Israeli provider benchmark
5. Manufacturer or official technical benchmark
6. Explicit versioned platform prior

The first implementation stores only platform and market parameters. Company
overrides and actual-job calibration belong to the later Estimation block.

## Delivery sequence

1. Data foundation: versioned parameter records, strict calculator identity,
   provenance, confidence, status, Platform Staff authorization, and audit.
2. Read-only Admin page: `CNC / Laser`, four route tables, source links, and
   bounded empty/error states.
3. Controlled editing: create a replacement version, validate ranges, and retain
   history. Platform Viewer remains read-only.
4. Reviewed Israeli seed data: official inputs, named provider curves, and
   explicitly low-confidence priors. Conflicting provider models remain separate.
5. Four deterministic calculators and route fixtures. This begins only after the
   Admin data and sources are accepted.
6. Estimation integration: feature extraction contract, route resolver,
   parameter snapshot, cost range, confidence, and explanation.

## Non-goals for 3.14.1

- No additional Company Profile machinery rows
- No mixed CNC and laser calculator
- No separate CNC agent
- No use of legacy machining-point weights
- No direct calculation-table editing
- No impact on current Estimation results
- No automatic learning from unverified user satisfaction
