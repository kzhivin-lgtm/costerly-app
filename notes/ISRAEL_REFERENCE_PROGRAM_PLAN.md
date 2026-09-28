# Israel Reference Data Program Plan

Program: 3.15 Israel Reference Data
Completed foundation: 3.15.1 at `1f8d6ab`
Current task: 3.15.2
Status: active master plan
Market: Israel (`IL`, `ILS`)

The executable foundation and Israel candidate evidence are deployed. Task
3.15.2 now continues Packages D, G, and the baseline-ready parts of F and J.
No accumulated catalog input may be discarded or silently reclassified.

## Objective

Deliver the complete verified data foundation required before Estimation v2:
canonical material identities, company-specific material overlays, source
evidence, Israeli market prices, work-time models, labor-role mappings, review
governance, and deterministic resolution. Preserve every accumulated source and
candidate while replacing incompatible or duplicated structures through
explicit migrations and mappings rather than deletion.

The work packages below form the 3.15 program. Foundation and candidate-data
deployment completed as 3.15.1. Baseline derivation, furniture-core completion,
and recognition expansion are now separately actionable as 3.15.2.

## Protected inputs

The following work remains in scope and must not disappear during
consolidation:

- every existing Israel material identity, alias, supplier offer, comparison,
  source register entry, and unresolved checklist cell;
- the fixed master coverage checklist and furniture-core priority view;
- raw supplier evidence and the distinction between candidate, reviewed, and
  active market data;
- the accepted Price Source upload, provenance, duplicate, revision, VAT,
  conversion, manual-review, and company-offer behavior;
- company-first pricing precedence and strict market isolation;
- the deterministic CNC and Sheet Laser routing and costing boundary from task
  3.14.1;
- the operation catalog, explicit time-component model, and labor-role catalog;
- the rule that Estimation extracts bounded facts while deterministic code owns
  identity resolution, price selection, arithmetic, and totals.

## Package A: Inventory and one authoritative state

Priority: P0
State: active

Work:

1. Inventory every reference SQL batch, table, enum, alias file, source record,
   coverage document, and test.
2. Define the only valid migration order and identify schema-name, field-name,
   enum, constraint, and duplicate conflicts.
3. Generate one coverage report from the actual seed data. Retire stale manual
   totals as authorities while retaining their history.
4. Classify every accumulated row as valid, repairable, duplicate, unsupported,
   or unresolved. Never silently discard a row.

Exit criteria:

- one reproducible inventory lists every retained input and conflict;
- one coverage report is authoritative;
- every current file has an explicit migration or retirement disposition.

## Package B: Shared domain contract and entity cards

Priority: P0
Dependency: Package A inventory

Work:

1. Finalize the four connected cards: reference material, company material,
   source offer, and identity candidate.
2. Finalize the separate anonymized market observation and market baseline
   records.
3. Unify departments, categories, canonical units, price scopes, source kinds,
   document types, VAT modes, statuses, reason codes, and confidence dimensions.
4. Define category-specific specification schemas and which attributes are hard
   identity constraints.
5. Define provenance, catalog-version, merge, split, deprecation, replacement,
   and audit fields.

Exit criteria:

- every field has one owner and one semantic meaning;
- raw evidence, identity, company overlay, commercial offer, observation, and
  aggregate baseline cannot be confused or stored as substitutes;
- Price Source, public-source ingestion, Estimation, and Admin can share the
  same contract without private-data leakage.

## Package C: Executable catalog foundation

Priority: P0
Dependency: Package B contract

Work:

1. Consolidate the foundation, taxonomy, aliases, and all Israel price batches
   into one valid migration chain.
2. Repair incompatible table names, columns, enums, normalized-value pairs,
   foreign keys, and seed ordering.
3. Preserve private company tables and add only compatible links and lifecycle
   fields.
4. Add candidate, observation, resolver-version, and audit storage without
   activating private-data learning.
5. Apply the complete chain to a clean disposable database, then apply it a
   second time where repeatability is promised.

Exit criteria:

- a clean database accepts the complete chain;
- foreign keys, checks, RLS, service-role boundaries, idempotency, and seed
  counts pass executable tests;
- no production migration has occurred without a separate approved checkpoint.

## Package D: Material Resolution Core

Priority: P0
Dependency: Packages B and C

Work:

1. Implement deterministic phrase, SKU, unit, dimension, language, and technical
   attribute normalization.
2. Resolve in order: exact supplier SKU, confirmed company alias, exact Israel
   alias, compatible hard-attribute query, then a maximum-five shortlist.
3. Use a model only to choose among two through five compatible candidates.
4. Create `new_identity_or_needs_review` when no compatible candidate exists.
5. Cache by company, market, supplier context, normalized evidence, hard
   attributes, and catalog version.
6. Persist the source phrase, extracted attributes, route, candidates, selected
   identity, confidence dimensions, and resolver version.

Exit criteria:

- exact confirmed identities require no model call;
- incompatible hard attributes cannot be overridden by a model;
- repeated evidence resolves consistently and audibly;
- a benchmark establishes false-match and unresolved rates before automatic
  linking is widened.

## Package E: Price Source integration and historical reprocessing

Priority: P0
Dependency: Package D

Work:

1. Preserve Price Source as the evidence-extraction layer and replace its
   independent name-based identity creation with the shared resolver.
2. Extend extraction output with structured identity attributes and independent
   extraction, identity, conversion, and eligibility confidence.
3. Link compatible company items to `reference_material_id`.
4. Create a usable private company item plus an identity candidate when no
   global match exists.
5. Keep source offers private and preserve accepted duplicate, revision,
   supplier-lane, VAT, unit-conversion, unresolved, Edit, Review, and Remove
   behavior.
6. Re-run identity resolution over historical rows without repeating OCR or
   agent extraction.
7. Convert confirmed company corrections into company aliases immediately and
   market/global alias candidates only through controlled promotion.

Exit criteria:

- Price Source and Estimation no longer maintain parallel material identities;
- unmatched imports remain useful to the company without polluting the global
  catalog;
- historical rows can be safely remapped after catalog improvements;
- the accepted production Price Source interaction checkpoint has no regression.

## Package F: Market observation and learning pipeline

Priority: P1
Dependency: Packages C through E

Work:

1. Define the eligibility gate for a private source row to become an
   anonymized market observation.
2. Require confirmed identity, explicit unit conversion, known VAT basis,
   compatible price scope, reliable date, usable net price, and permitted data
   use.
3. Separate invoice, quote, price-list, and public retail evidence and assign
   documented weights.
4. Deduplicate repeated documents, cap company and supplier influence, apply
   recency weighting, and use robust outlier treatment.
5. Require configurable minimum distinct-company, supplier, and observation
   counts before aggregation or display.
6. Produce candidate baseline versions with evidence membership, methodology,
   dispersion, freshness, confidence, approval, superseding, and rollback.

Exit criteria:

- no private price or commercial term is exposed globally;
- one company cannot materially control a market baseline;
- identity learning and price learning remain independent;
- legal and product authorization is verified before private observations are
  enabled for global learning.

## Package G: Israel material and price completion

Priority: P1
Dependency: Packages A through C; active baselines also depend on Package F

Work:

1. Preserve and normalize all already collected Israel evidence.
2. Close the furniture-core identities and aliases first, then the remaining
   master-checklist cells by estimate impact rather than raw SKU count.
3. Seek two or three comparable Israeli sources for high-impact baselines when
   available, while retaining honest single-source candidates.
4. Prioritize the materials that dominate representative furniture estimates:
   panels, solid wood, edge banding, core hardware, fasteners, adhesives,
   coatings, abrasives, consumables, packaging, glass, plastics, metal sheet,
   and profiles.
5. Activate only exact, comparable, reviewed baselines. Keep unsupported
   dimensions, grades, scopes, and units as explicit gaps.
6. Replace simple breadth percentages with impact-weighted estimate coverage,
   baseline readiness, source depth, freshness, and confidence metrics.

Exit criteria:

- representative Israeli furniture projects resolve their material identities
  and important prices without invented substitutions;
- every remaining gap is visible and prioritized;
- broad SKU harvesting resumes only when a benchmark demonstrates material
  estimate impact.

## Package H: Operations, labor, machinery, and subcontractor references

Priority: P1
Dependency: shared taxonomy and executable foundation

Work:

1. Complete the operation catalog with setup, throughput, auxiliary, and
   minimum-batch components.
2. Map every operation to capable labor roles, crew size, supported material
   and machine constraints, and explicit quantity drivers.
3. Build sourced Israel productivity models and separate company-specific
   machinery and labor overrides.
4. Preserve the accepted CNC and Sheet Laser route resolver, exclusive in-house
   versus subcontractor choice, and deterministic calculators.
5. Add versioned subcontractor observations and baselines without confusing
   fabricated-component prices with raw material prices.

Exit criteria:

- operations produce auditable labor hours by role;
- company labor and machinery settings override market fallbacks correctly;
- unsupported capability or scope returns review instead of a guessed route.

## Package I: Staff review and governance tools

Priority: P1 after backend lifecycle verification
Dependency: Packages B through F

Work:

1. Review identity candidates and possible duplicates.
2. Link to an existing identity, approve a new identity, reject, merge, split,
   deprecate, or remap with mandatory rationale.
3. Review alias promotion separately from material identity approval.
4. Review observation eligibility and baseline versions separately from identity
   review.
5. Display source evidence, conflicting attributes, downstream impact, and the
   records that will be reprocessed before a consequential action.
6. Enforce Staff-only permissions and immutable audit history.

Exit criteria:

- every consequential catalog mutation is reviewable and reversible;
- no interface action bypasses lifecycle, privacy, or evidence requirements;
- accepted decisions trigger bounded deterministic reprocessing.

## Package J: Deterministic costing and Estimation v2 readiness

Priority: P1 after required catalog checkpoints
Dependency: Packages D through I as applicable

Work:

1. Implement company-first material-price selection, exact Israel fallback, and
   explicit review when neither is compatible.
2. Resolve operation time, labor role and rate, machinery or subcontractor cost,
   overhead allocation, and source snapshots deterministically.
3. Keep the five-level cost reserve outside raw price evidence and apply it only
   after base cost calculation.
4. Validate kitchen, wardrobe, cabinet, table, upholstered furniture, glass,
   metal-frame, and mixed-material scenarios, including missing and conflicting
   data.
5. Define the bounded evidence contract that the new Estimation Agent must
   extract. Only then replace the legacy Estimation Agent.

Exit criteria:

- every cost line states whether it used a company value, Israel baseline, or
  review state;
- arithmetic is reproducible from immutable source and parameter snapshots;
- benchmark projects establish useful accuracy and expose remaining catalog
  gaps;
- Estimation v2 can be built without inventing identities, prices, time, or
  arithmetic.

## Decision gates

Explicit approval is required before:

1. freezing the shared entity-card contract;
2. applying the consolidated migration to production;
3. widening automatic identity linking beyond benchmarked exact routes;
4. enabling private-source observations for global learning;
5. activating the first market baselines;
6. performing catalog merge or split operations with downstream remapping;
7. replacing the legacy Estimation Agent.

## Current next action

Execute 3.15.2 from
`notes/ISRAEL_REFERENCE_BASELINES_3_15_2.md`: generate the reproducible
readiness report, derive non-active candidate baselines, close high-impact
furniture-core gaps, and expand deterministic recognition. Do not activate a
baseline, global private-data learning, or Estimation fallback without the
corresponding decision gate.
