# Estimation 3.17.4.3: Object-to-Estimate and approximate BOM plan

Status: active, owner-approved on 2026-11-02. This plan is the design boundary
for the first material-only BOM increment, not a claim of implemented behavior.

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
confidence does not remove the cost. It keeps the estimate review-required and
creates the work needed to improve the source.

## Automatic cycle

1. **Evidence package.** Detection and File Review lock object identity and
   quantity, then save immutable pages, regions, OCR and original-file links.
   Detection does not need to publish external dimensions.
2. **Object-to-Estimate.** Read the complete evidence package to build a
   construction brief: object archetype, cited measurements when available,
   material and finish clues, visible-versus-internal roles, hardware facts and
   declared construction assumptions where a sketch lacks detail.
3. **Approximate BOM Composer.** Apply deterministic, versioned construction
   recipes to that brief. A wardrobe or cabinet recipe may create facade,
   carcass, backing, shelf, finish and hardware demands. It uses standard
   thicknesses and construction conventions, but never calls its approximate
   details source facts or a precision manufacturing cut-list.
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
7. **Automatic quality control.** Check complete material assignments, source
   evidence or declared assumptions, compatible physical formats, duplicate
   parts, purchase-plan reconciliation and all assumption traces.
8. **Result and edit loop.** Render the estimate only after QA. User edits to
   dimensions, recipe choice, material role or quantity invalidate and rerun
   only steps 3 through 7, followed by QA again. They are not a stage before
   quality control.

## First witness

The 2026-11-01 three-page wardrobe proves why this is needed. Its source page
contains visual dimensions, including overall width, height, depth, module
widths and panel thicknesses. V4.2 preserves the page but extracts only
material identity and explicit hardware count; it persists no structured
geometry and zero parts. Object-to-Estimate must make that geometry available
to the BOM Composer without weakening Detection's evidence contract.

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
