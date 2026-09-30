# CNC / Laser Costing

Task: 3.14.1
Status: production schema verified; read-only Admin implementation candidate complete

Ordered production finish plan:
`notes/CNC_LASER_FINISH_PLAN_2026_09_28.md`

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

For each required process, the Company Profile supplies the primary machine
availability. The deterministic router then selects one route for each
homogeneous part group:

1. CNC available: CNC router in-house
2. CNC unavailable, panel saw available, simple low-volume rectangular work:
   panel saw plus manual processing in-house
3. CNC unavailable and the manual gate fails: CNC subcontractor
4. Sheet laser available: sheet laser in-house
5. Sheet laser unavailable: sheet laser subcontractor by default
6. Sheet laser unavailable, explicitly confirmed rough straight cutting only:
   basic sheet cutting in-house as a rare exception

Only the selected strategy runs. A project may invoke more than one route only
when different documented part groups require different processes. The four
CNC and laser calculators remain separate. The two narrow fallback routes use
ordinary cutting and labor costing rather than pretending that CNC or laser was
used. Parameters and calibration remain separate between strategies. A shared
value such as an electricity tariff may be referenced by several strategies,
but learned process coefficients are never silently shared.

### Deterministic routing gates

The wood manual route requires a panel saw, rectangular parts, single-face
processing, standard operations, low part count, low hole count, and explicit
evidence that no freeform contour, internal cutout, pocket, horizontal or end
drilling, repeated hole pattern, or tight positional relationship exists.
Missing evidence returns `needs_review`; a failed gate selects the CNC
subcontractor.

The metal fallback is intentionally much stricter. Without an in-house sheet
laser, subcontracting is the default even for apparently simple work. Basic
in-house cutting is allowed only when it is explicitly confirmed for the job,
all cuts are straight and edge-to-edge, the result may be rough, material and
thickness are supported, volume is very low, and there are no holes, internal
features, shaped edges, or precision and repeatability requirements. The
router does not infer a guillotine from another metal capability because the
compact Machinery profile does not expose one.

Initial volume limits are versionable routing policy, not manufacturing facts.
The candidate defaults are at most 6 wood parts and 12 holes, compared with at
most 2 rough metal parts and 4 straight cuts. These values require later
calibration and do not affect current Estimation results.

Each routing decision records `manufacturing_route_decision_v1`, the routing
policy version, reason codes, one costing strategy, and at most one specialized
calculator identity. Manual fallback routes use the ordinary material and labor
costing strategy. `not_required` and `needs_review` do not authorize a CNC or
laser calculator.

## Deterministic calculator contract

The four specialized calculators are pure deterministic functions:

1. `cnc_router_in_house`
2. `cnc_router_subcontractor`
3. `sheet_laser_in_house`
4. `sheet_laser_subcontractor`

The route also controls the economic classification of the result. In-house
calculators create manufacturing labor and machine-cost lines. Subcontractor
calculators create `purchased_fabricated_component` material-like lines with
`price_scope = fabricated_component`. For the customer company, the purchased
deliverable is an input cost even when the supplier's invoice consists mostly
of labor. The estimate must not add the same external labor or machine time a
second time. Material remains separate only when the selected provider model
explicitly excludes it.

The dispatcher accepts the routing decision and refuses inputs for every
calculator except the one selected by that decision. Current Estimation does
not call this dispatcher.

Every calculator returns:

- low, typical, and high net cost;
- one selected cost for estimate reserve level 1 to 5;
- auditable cost components;
- subcontractor inclusion and minimum-charge details where applicable;
- the immutable parameter record identifiers used for the calculation.

Levels 1, 3, and 5 select low, typical, and high respectively. Levels 2 and 4
select the midpoint of their adjacent scenarios. These are estimate scenarios,
not statistically validated P10, P50, and P90 claims. A probabilistic label may
be introduced only after actual-job calibration supports it.

All calculated monetary values use decimal arithmetic and six-decimal storage
precision. Supplier minimum is applied as `max(provider subtotal, minimum)`
before delivery and rush charges. Material and cutting are not added when the
provider base charge explicitly includes them.

## Runtime parameter resolution

The runtime reads only Active records for the selected calculator and country.
Resolution is deterministic and produces
`manufacturing_parameter_resolution_v1`.

For every required parameter it applies these rules:

1. calculator, country, parameter key, unit, and currency must agree;
2. named scope fields may match exactly or use an explicitly unscoped fallback;
3. a scoped material, machine class, object family, region, or provider model
   is never selected when that input is unknown;
4. thickness must fall inside the stored band; the nearest band is never used;
5. a more specific scope wins over a general fallback;
6. a narrower containing thickness band wins only after the named scope is
   equally specific;
7. source precedence breaks a remaining tie between different source classes;
8. two equally ranked records remain ambiguous and return `needs_review`;
9. Candidate, Reviewed, future, expired, unapproved, or source-less records
   cannot enter a calculation.

Provider models are isolated through qualifiers. Iron Laser and Laser Portal,
for example, cannot be averaged or silently substituted for one another. A
complete resolution exposes exact immutable parameter IDs, which the selected
calculator carries into its result snapshot.

## CNC estimate level

The CNC row in Machinery owns one estimate level for its configured CNC route.
If CNC is available in-house, the level applies only to the in-house CNC
strategy. If CNC is not available in-house, the level applies only when the
router selects the CNC subcontractor. It does not turn simple panel-saw and
manual work into subcontracted CNC work, and it is not applied to the manual
labor fallback. Both CNC strategies are never active at the same time.

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
| CNC is not available in-house | Show the subcontractor estimate level; use it only when the router selects CNC subcontracting |
| CNC is unavailable; panel saw and all manual gates pass | Select panel saw plus manual processing; do not run the CNC subcontractor calculator |
| CNC is unavailable; any manual hard gate fails | Select the CNC subcontractor |
| CNC is unavailable; manual evidence is incomplete | Return `needs_review`; do not guess the manual route |
| Sheet laser is unavailable | Select the sheet-laser subcontractor by default |
| Sheet laser is unavailable; rough internal cutting is explicitly confirmed and every strict gate passes | Select basic in-house sheet cutting without running a laser calculator |
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
5. Four deterministic calculators and route fixtures. The pure local candidate
   is implemented; connection to active Admin parameters waits until the Admin
   data and sources are accepted.
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
