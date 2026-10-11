# Catalog Architecture and Phased Migration, 3.17.1.4

Status: owner-approved target architecture. Direct rebuild is authorised because
the current catalog is transitional and has no production users. SQL design and
implementation are next; no database migration has yet been applied.

## Decision

Do not wait for a complete material or operation universe. Build the new
canonical model now with the approved V1 catalogue, preserve a controlled gap
state for missing operations, and expand it through versioned changes. A gap is
`review_required`, never a similar operation with an invented time.

The new model replaces the old department semantics. We do not preserve the old
model as a product compatibility requirement. We only retain enough migration
evidence and checks to detect a broken internal reader before cutover.

## New canonical model

| Concept | Canonical representation | Meaning |
| --- | --- | --- |
| Production department | `reference_production_departments` | Exactly `wood`, `metal`, `glass_plastics`, `stone`, `coating` |
| Entity role | `reference_entity_roles` | `material`, `hardware`, `consumable`, `packaging`, `purchased_fabricated_component`, `supplier_service` |
| Material family | `reference_material_families` | Family identity, production department, entity role, primary attribute and lifecycle |
| Attribute contract | `reference_material_family_attributes` | One primary and ordered allowed secondary attributes, with type and validation contract |
| Family eligibility | `reference_material_family_operation_eligibilities` | Possible operations only, many-to-many to `reference_operations` |
| Department affinity | `reference_material_family_department_affinities` | Retrieval/context only for Hardware and Consumables, never identity, price, route, eligibility or labor |
| Material membership | `reference_material_family_memberships` | Versioned mapping from existing `reference_materials.material_id` to one family |
| Brand scope | `reference_material_family_brand_scopes`, `reference_brand_aliases` | Curated manufacturer/product-system recognition, scoped to family |

`packaging` is an entity role with no production department and no affinity.
Delivery and Installation do not enter the fabrication-operation model.

Hardware and Consumables can have one or more affinities, for example a hinge
can be Wood and Metal, or an abrasive can be Wood and Coating. Those affinities
only help the resolver and Agent find relevant items. They cannot change an
item's canonical identity, price class, family operation eligibility, route or
labor time.

## Existing data that remains useful

`reference_materials` is rebuilt as the canonical SKU-level material row under
the new model. Its current `specifications` remains source evidence and value
storage, but is no longer the definition of a family contract. Existing
`reference_operations`, drivers, aliases, market profiles, price identities
and offers remain. The new relations classify and validate them rather than
copying them.

The legacy `department` values (`hardware`, `consumable`, `packaging`, and
`glass_stone_plastic`) are replaced by the new roles/departments. They may be
removed or converted only after the current internal readers have been changed
in the same rebuild.

## Operations, recipes and machinery

`reference_operations` remains the stable operation identity.
`market_operation_models` becomes the route-specific versioned recipe record.
The additive recipe layer will declare `route_kind`, optional Machinery
capability, `batch_key_schema`, required evidence and drivers, and the four
stages `prepare`, `execute`, `finish`, `closeout`.

The existing time-component table keeps its numeric mechanics but gains a
recipe-stage assignment. Legacy V0 components stay visibly unclassified until
they are reviewed. A machine session can share prepare and closeout only within
one route and one machine capability. It never crosses panel saw and CNC.
External recipes create a purchased fabricated component or supplier service,
not duplicate internal labor.

## Operating principle: object to a costable production model

The system has four blocks. Only the middle two are Estimation reasoning;
the first locks evidence and the last calculates deterministically.

1. **Detection package.** Detection identifies a commercial object, its
   quantity and name, removes irrelevant pages and duplicate views, and creates
   one bounded evidence package. It contains OCR facts plus every relevant page,
   region or visual representation. Estimation may inspect this visual evidence,
   but it does not rerun Detection or full-document OCR.
2. **Object decomposition.** Estimation turns the evidence package into
   explainable intermediate part facts. It decomposes object -> part groups ->
   material or purchased-component requirements, with geometry, counts and
   evidence provenance. A Part is an intermediate planning fact in V1, not yet
   a universal persisted catalog entity.
3. **Production composition.** Estimation selects supported physical operations
   and operation drivers for each requirement, then forms the reverse trace:
   materials/components + operations produce parts; parts produce the commercial
   object. This is not money or scheduling. It is a checkable manufacturing
   graph, including cut metres, holes, finish area, weld length and other
   quantity facts required by the deterministic engines.
4. **Deterministic calculation.** Material Resolver and Material Engine resolve
   purchase identity and purchasable quantity. Labor Resolver and Labor Engine
   resolve route/recipe/session and calculate time. Price Source supplies offer
   evidence, and the existing estimate calculation totals the result.

The Agent's responsibility ends with the evidence-backed manufacturing graph.
It must not invent money, minutes, rates, routes or totals. A missing catalog
fact produces a case-local provisional assumption and a Catalog Gap Job, so the
current estimate continues while the canonical catalog remains unchanged.

## Read boundaries

```text
source evidence -> Material Resolver -> family, role, attributes and aliases
object evidence -> Estimation Agent -> material requirements + selected operations
material requirements + part geometry -> Material Engine -> purchasable quantities
facts + selected operations -> Labor Resolver -> approved route / recipe
recipe + drivers -> Labor Engine -> Labor trace
purchasable quantities + Price Source offers -> estimate cost calculation
```

The Estimation Agent receives eligible operations and may choose zero or more.
It does not receive or calculate material purchase quantities, routes, machinery
availability, minutes, rates or money. Thickness can remain price-bearing
without changing eligibility.

`Material Resolver` resolves the Agent's material statement to a canonical
family and, where possible, a purchasable material identity. `Material Engine`
turns resolved part geometry into purchase quantity. For sheet goods it performs
cut-layout/nesting against purchasable sheet dimensions, saw kerf and approved
edge trim, then rounds the project demand up to whole sheets. Five tables with
two tables per sheet therefore purchase three sheets. It must not use a generic
waste percentage as a substitute for nesting. Offcuts are not valued or carried
to another project in V1 unless a later inventory policy explicitly adds that
capability.

`Labor Resolver` replaces the vague term "deterministic resolver". It resolves
selected operations to an approved route, recipe, machinery capability and
compatible session. `Labor Engine` then calculates the recipe's staged time.
`Price Source` is the evidence catalog of offers and prices. The existing
estimate cost calculation applies the selected offer to the purchasable material
quantity and then applies the approved commercial policy; it is not a separate
Pricing engine.

The review states are deliberately distinct:

- `material_resolution_review_required`: no reliable family/material identity,
  conflicting evidence, or a required primary attribute is missing.
- `material_supply_review_required`: material is identified, but no purchasable
  unit/dimension or availability is sufficient for the required geometry.
- `price_source_review_required`: material and quantity are known, but no approved
  price source matches them.
- `labor_review_required`: selected work has no approved route, recipe,
  machine capability or necessary geometric driver.

## Rebuild sequence

1. Create the canonical tables and replace the old department constraints with
   references to roles, five production departments and family membership.
2. Seed approved families, attribute contracts, roles, affinities and current
   V1 operation eligibility. Record every missing operation as a gap.
3. Reclassify existing catalog rows deterministically. Ambiguous rows remain
   `review_required`; no legacy default is silently carried forward.
4. Update every current internal resolver, Estimation catalog publisher and
   Price List reader to use the new canonical fields in the same change.
5. Run catalog integrity checks plus resolver and estimate-cost scenarios, then
   remove obsolete legacy columns, constraints and reader paths.

## Activation gates

- All five production departments and all entity roles are seeded.
- Each family has exactly one primary attribute.
- Every linked eligible operation exists and is active. Candidate
  `stone_edge_profiling` remains unlinked until its route, driver schema and
  recipe are approved.
- Every unresolved legacy row is visible, not silently defaulted.
- Every internal resolver, Estimation publisher and Price List reader has been
  changed to the new canonical model and passes its scoped scenarios.
- Glass, Stone and Acrylic stay `external_component` in V1.

## Deferred by design

- Expert expansion of the operation dictionary and all time priors.
- A persistent universal `Part` entity.
- Changes to commercial policy, Packaging allowance, Delivery or Installation.

## Next implementation task

Map these relations to exact current keys, RLS and Machinery capability
vocabulary, then implement the rebuild migration, seed data and reader changes
as one tested block. Applying it to the database is the deployment step, not a
separate product-direction decision.
