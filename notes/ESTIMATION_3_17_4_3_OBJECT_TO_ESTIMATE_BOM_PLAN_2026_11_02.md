# Estimation 3.17.4.3: Object-to-Estimate and approximate BOM plan

Status: active implementation, owner-approved on 2026-11-02. V4.14 replaces
the original wardrobe/cabinet recipe with a bounded structural composer. It is
not a claim of universal production-calculation coverage.

## Product rule

Estimation produces material purchasing cost only. Labor, manufacturing,
overhead, markup and sale price remain outside this work.

Every final material selection has one price authority:

- `C`: Company Catalog
- `I`: Israel Reference
- `A`: Assumption Fallback

`A` is not an error state and does not permit an unpriced material line. Every
material demand must have a monetary estimate. `A` therefore creates an
estimate-local Assumption Price immediately, even when no source could be
found. It carries the chosen amount and unit plus an explicit confidence and
reasoning trail. The possible evidence levels are intentionally broad: a
current Israel listing, a Global listing projected to Israel, an analogous
material, or an unreferenced estimator allowance such as `200 ILS`. Low
confidence does not remove the cost, block the result or ask the customer to
approve anything. It only records the source quality and silently creates work
to improve the source.

## Automatic cycle

1. **Evidence package.** Detection and File Review lock object identity and
   quantity, then save immutable pages, regions, OCR and original-file links.
   Detection does not need to publish external dimensions.
2. **Structural interpretation.** Read the complete evidence package to emit
   one document-unit context, cited dimensions, large physical assemblies,
   shown counts and material/finish clues. It does not rename the object or
   enumerate finished panels.
3. **Structural BOM Composer.** Apply deterministic, versioned assembly
   templates to that interpretation. A box carcass, drawer bank, panel stack,
   table or facade set becomes conventional facade, carcass, backing, shelf,
   drawer and fitting demands. It uses named standard-thickness and
   construction assumptions, but never calls approximate details source facts
   or claims a precision manufacturing cut-list.
4. **Material Demand.** Combine BOM details into net sheet area, linear length,
   pieces and required specifications, multiplied by finished-object quantity.
5. **Material resolution and price.** Select compatible Company Catalog
   material first, then Israel Reference. If neither can price the demand,
   create an Assumption Price with a complete amount, currency, unit and
   confidence/reasoning trace. It may later be informed by Price Research, but
   that tool is not a prerequisite for emitting a cost. Source selection and
   the fallback policy belong to Resolver and Material Engine, not to the
   model.
6. **Project purchasing.** The existing Material Engine combines compatible
   demands across every object, nests sheets, packs linear stock, rounds
   packages and allocates resulting purchase cost back to each object.
7. **Automatic audit.** Check material assignments, source evidence or
   declared assumptions, compatible physical formats, duplicate parts,
   purchase-plan reconciliation and all assumption traces. The audit is
   diagnostic and never withholds the material cost.
8. **Result and optional edit loop.** Render the material estimate with its
   C/I/A and confidence immediately. A voluntary user edit to dimensions,
   recipe choice, material role or quantity invalidates and reruns only steps
   3 through 7. It is never required to obtain a result.

## First witness

The 2026-11-01 three-page wardrobe proves why this is needed. Its source page
contains visual dimensions, including overall width, height, depth, module
widths and panel thicknesses. V4.2 preserves the page but extracts only
material identity and explicit hardware count; it persists no structured
geometry and zero parts. Object-to-Estimate must make that geometry available
to the BOM Composer without weakening Detection's evidence contract.

## Implemented first path

The V4 runtime now preserves the V4.2 evidence result and writes two new
immutable fact results for each new input: `estimation_object_to_estimate_v1`
and `estimation_approximate_bom_v1`. The geometry agent sees every supplied
private evidence page in bounded batches, and the deterministic builder either
retains a cited dimension/count or inserts a named construction default. The
first recipe creates facade, carcass, shelf and backing rectangles, and keeps a
shown finish or hardware role as a separate demand. Explicit shown fitting
counts are multiplied by finished-object quantity before project aggregation.

The Material Engine then selects C, I or the mandatory priced A fallback. Each
A line has a user-visible rationale and a silent, deduplicated Catalog Gap Job
plus an estimate-local assumption record. An internal job-write outage is
recorded in the plan, but never deletes or blocks the already priced material
line. A real production witness and SQL readback remain required before this
path can be accepted as production behavior.

## V4.14 structural composer

V4.14 keeps the same immutable fact-result contract, but uses a new active
agent version so a prior failed V4.13 object can be processed without mutating
its evidence. The visual contract no longer requires a model to invent every
cut part or thickness. It returns only the source-supported assembly topology
and dimensions. The composer owns conventional panel expansion and named
defaults. This is the needed boundary for approximate consumption: model
uncertainty is limited to visual interpretation, and equations, count
multiplication and sheet geometry remain deterministic.

Before Material Engine runs, the runtime now requires at least one successful
structural BOM. If none exists, each affected object terminates as
`structural_bom_failed`; no empty plan is persisted or displayed as a pending
price calculation. On a completed allocation, Object Detail stores and shows
only a compact `C`, `I` or `A` source marker beside unit cost. The material
name remains the selected or assumed material name, without an `Assumption:`
prefix.

## V4.9 simplification decision

For this estimation stage, a source naming Formica is normalized to ordinary
`melamine_faced_particleboard` (LDSP). The source name and an explicit
`formica_as_melamine_faced_particleboard` assumption remain visible, but the
system does not pursue a precise Formica format or compact-laminate recipe.

Paint, lacquer and Nirlat-like names are always a `finish`, never the board
behind a facade. In the absence of an explicit paint quantity, the recipe adds
one standard paint set per finished object. This is a bounded pricing norm,
not a coating-shop formula. It permits C/I selection when a paint offer exists
and otherwise emits the mandatory A price.

The evidence extractor may emit multiple `hardware` rows. The BOM preserves
each separately identified handle, hinge, drawer slide or leg as its own
purchase requirement and multiplies its shown count by object quantity.
Generic rails, connectors, hangers and fastening sundries are not individual
hardware demands in this material-only recipe.

## Deferred dependency: Price Research for A

When neither C nor I supplies a compatible material, the Resolver must first
emit an immediate Assumption Price, rather than leave the material unpriced.
The future tool receives a bounded natural-language research request and can
replace or improve that estimate with saved source candidates. The persisted A
record retains the product identity, chosen price, currency, unit, confidence,
reasoning, source URL/date when present, conversion inputs and any Israel
projection. An A without an external source is still valid, but explicitly
records that it is an estimator allowance. Every A creates or updates a
deduplicated team job to improve Company Catalog or Israel Reference coverage.

## Non-goals

- Reintroducing external dimensions as a Detection public requirement.
- Exact CNC-ready cut lists, hidden-gap calculations or millimetre-perfect
  production documentation.
- Model-selected catalog positions, prices, labor, overhead or sale pricing.
