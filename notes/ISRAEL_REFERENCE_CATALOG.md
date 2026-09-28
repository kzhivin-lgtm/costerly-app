# Israel Reference Catalog

Task: 3.15.1
Status: production foundation and candidate evidence deployed

## Production checkpoint, 2026-09-28

The reference-catalog foundation and Israel candidate evidence are deployed to
production. Verified production counts are:

- 1 reference market;
- 99 reference sources;
- 113 material categories;
- 280 reference materials and 280 Israel market profiles;
- 320 market offers, all with `candidate` status;
- 851 material aliases;
- 0 active material baselines.

Exact alias lookup is verified for both a technical material code and its
Hebrew Israel market name. This checkpoint does not activate fallback prices
for Estimation. Baseline derivation, review, approval, and resolver integration
remain separate work.

Ordered delivery plan: `notes/ISRAEL_REFERENCE_PROGRAM_PLAN.md`

## Objective

Build the verified fallback data required before replacing Estimation. Company
data remains the first choice. The reference catalog is used only when the
company has no exact compatible price or production standard.

The first release is `Israel Reference Catalog v1` with market code `IL` and
default currency `ILS`. The schema is multi-market, but no other country data
is inferred from Israel and no cross-market fallback is allowed.

## Separation of concerns

Global records define stable identities:

- material identity and technical specifications;
- production operation identity;
- labor role identity.

Market records define local facts:

- local names, specifications, availability, package formats, and units;
- observed supplier prices and VAT basis;
- approved low, typical, and high material-price baselines;
- operation-time models and their evidence;
- later, default labor costs and subcontractor rates.

The same global material may therefore have independent Israeli, American,
European, or other market profiles without duplicating its technical identity.

## Material price contract

An observed offer is evidence, not the platform fallback by itself. It records
the supplier price, source unit, package quantity, minimum order, VAT mode,
normalization basis, source date, region, confidence, and price scope. The price
scope distinguishes material only, cut-to-size material, fabricated components,
and retail packages. Included cutting, drilling, edge processing, delivery, or
other services remain explicit and are never silently treated as raw material.

An active market baseline must:

1. belong to the company's estimation market;
2. use the exact global material identity and a compatible unit;
3. expose low, typical, and high prices excluding VAT;
4. cite one or more observed offer identifiers;
5. use evidence with the same market and price scope;
6. state its aggregation methodology;
7. be approved and effective on the estimate date.

The resolver order will be:

1. exact active company offer;
2. explicitly compatible company offer with a deterministic unit conversion;
3. exact active baseline for the same market;
4. `needs_review`.

Similar-looking materials, unsupported dimensions, incompatible grades, and
other countries are never silent substitutes.

## Operation-time contract

There is no machining-points abstraction. Each operation model is composed of
explicit time components:

- `setup`: fixed preparation labor minutes;
- `throughput`: a documented quantity divided by units per hour;
- `auxiliary`: labor minutes per documented unit;
- `minimum_batch`: the minimum justified labor time for the batch.

Every component carries low, typical, and high values. It may identify the
responsible labor role and crew size. One operation may have multiple drivers,
for example parts, cut length, holes, tool changes, or coated area.

For direct time values, low to high follows elapsed labor time. For throughput,
the scenario is inverted during calculation: high throughput produces low time,
and low throughput produces high time. The resolver must make this transformation
explicit rather than treating throughput as a time value.

Operation identities are global. Productivity models are market-scoped so local
practice may differ without contaminating another country's estimates. Machine,
material, region, and other qualifiers remain explicit.

## Labor contract

An operation produces labor hours by role. It does not own a monetary labor
rate. The cost resolver later multiplies those hours by company Labor Costs. A
market labor fallback must be a separate sourced and versioned dataset when a
company has no compatible role cost.

Specialized roles are not silently collapsed into broad Company Profile
positions. An exact position may match automatically. A plausible broad
position, such as Carpenter for Wood Machine Operator, requires explicit
capability confirmation. Glass, stone, galvanizing, and other specialist work
has no automatic broad-position match when the current profile cannot establish
the qualification.

## Initial coverage boundary

The catalog will cover only the fabrication domains supported by the accepted
Machinery and product scope:

- woodworking and panel furniture;
- metal fabrication and sheet-metal work;
- glass, stone, acrylic, and related fabricated components;
- coatings and finishing;
- hardware, adhesives, abrasives, consumables, packaging, and installation.

"Complete" means every supported estimate feature resolves to either an exact
catalog item or an explicit `needs_review` state. It does not mean every SKU sold
in Israel.

## Delivery sequence

1. Foundation: schema, market isolation, evidence requirements, and legacy
   machining-points removal.
2. Taxonomy: controlled material, operation, role, unit, and driver lists.
3. Israel materials: source collection, normalization, and candidate baselines.
4. Israel operations: source-backed time models and role mappings.
5. Validation: representative projects, coverage report, and rejection cases.
6. Deterministic resolvers: company first, Israel fallback second, otherwise
   review.
7. Estimation v2: feature extraction only, with no agent-owned arithmetic.

Production migration, data activation, and Estimation integration are separate
checkpoints.

## Shared material identity and Price Source contract

Price Source, Estimation, company material catalogs, and public market-source
ingestion must use one Material Resolution Core. They must not maintain
independent material names, category systems, unit vocabularies, or alias
matching rules.

The core owns:

- reference material identities and category membership;
- category-specific specification schemas;
- canonical units and deterministic conversions;
- global, market, supplier, and company alias lookup;
- hard compatibility filtering and a maximum-five candidate shortlist;
- identity-match route, confidence, evidence, and catalog version;
- candidate creation when no compatible reference identity exists.

The data model keeps four records separate:

1. A reference material card defines what the material is. It contains the
   stable identity, canonical name, category, base unit, structured technical
   specifications, lifecycle status, and any replacement identity after a
   merge or deprecation.
2. A company material card defines how one company calls and uses that
   material. It may link to a reference material, retains the company's display
   name and private aliases, and never exposes company prices or purchasing
   terms globally.
3. A source offer card defines what one source stated at one point in time. It
   retains raw description, supplier SKU, price, currency, unit, package,
   quantity, discount, VAT basis, date, scope, included services, conversion
   evidence, provenance, and independently measured extraction, identity, and
   conversion confidence.
4. An identity candidate is the review buffer between unmatched private
   evidence and the reference catalog. It stores proposed category and
   specifications, linked evidence, possible duplicates, decision status, and
   the final reference identity when resolved.

Price Source reads the active reference catalog before creating a new identity.
An exact compatible match links the company material to `reference_material_id`.
An unmatched usable row creates a private company material immediately and may
also create an identity candidate. It must never create an active global
identity directly.

User confirmation creates a company-scoped alias immediately. A company alias,
supplier phrase, or private SKU becomes a market or global alias only after
review or independently corroborated evidence. New or changed reference
identities and aliases become available to subsequent Price Source and
Estimation resolution through a versioned resolver index.

Identity learning and price learning are independent. A source row may
contribute an anonymized market price observation only after its material
identity, unit conversion, VAT basis, price scope, and evidence eligibility are
confirmed. Market observations may propose a new versioned baseline, but never
replace an active baseline or expose a contributor's private terms without the
required review and approval.
