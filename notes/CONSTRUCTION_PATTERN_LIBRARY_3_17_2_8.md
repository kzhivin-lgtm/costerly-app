# Construction Pattern Library, 3.17.2.8

Status: owner-approved initial design. This is a controlled Estimation input,
not a universal furniture ontology or a production work order.

## Purpose

The Estimation Agent must not freely invent hidden hardware or construction.
It may derive a hidden component only when an active construction pattern
explicitly permits it and the object evidence meets that pattern's conditions.

The library models recurring construction requirements, not every possible
object. A pattern emits a requirement such as `support_system`; the Material
Resolver then selects an allowed compatible family or records a case-local
assumption. It does not create a catalog record.

## Common contract

Each pattern contains:

- a stable code and human-readable name;
- object evidence required for activation;
- explicit exclusion evidence;
- one or more derived component requirements;
- permitted material-family alternatives for each requirement;
- quantity rule and confidence;
- fallback behavior when the construction choice is not evidenced;
- a required explanation in the estimate trace.

The Agent may not activate a pattern merely because the object is a rectangle.
It must identify the object class and the evidence for its mounting or support
condition. It may emit no hidden component when the evidence is insufficient.
If an estimate nevertheless needs an assumption, it is case-local, marked
`review_required`, and creates a Catalog Gap occurrence when appropriate.

## Initial patterns

### `floor_cabinet_support`

Activates for a cabinet or carcass identified as floor-standing.

Emits `support_system`:

- required functional component: adjustable cabinet leg;
- retrieval family: `hardware_leg_caster`, narrowed by the component
  requirement so a caster is never substituted for a cabinet leg;
- quantity: `4 ×` each recognised floor-standing cabinet module;
- trace: state that legs were derived from the floor-standing cabinet pattern.

A plinth confirms this pattern. It is ordinarily a cover concealing the
adjustable legs, not an alternative to them. The estimate includes the four
legs even when the drawing only shows a plinth, because adjustment is required
to level a countertop or run of cabinets.

### `wall_cabinet_suspension`

Activates for a cabinet identified as wall-mounted, suspended, or with a clear
absence of floor support.

Emits `wall_suspension_system`:

- permitted alternatives: cabinet hanger, hanging rail, concealed bracket, or
  another evidenced suspension system;
- no `hardware_leg_caster` requirement;
- quantity: derive only from explicitly recognised cabinet modules. Do not
  assume a particular hanger count from one elevation;
- fallback: retain the requirement as an unresolved provisional assumption,
  rather than silently pricing cabinet legs or a specific proprietary hanger.

### `tall_cabinet_support`

Activates for a tall cabinet or pantry unit that is evidenced as floor-standing.

Emits `support_system` with the same adjustable-leg requirement as
`floor_cabinet_support`, plus a separate `anti_tip_or_wall_fixing` requirement
only when the drawing or object context evidences it.

The pattern does not assume a fixed number of legs, wall fittings, shelves, or
drawer mechanisms. Those require their own evidence or later patterns.

### `table_support_structure`

Activates for a recognised table, desk, counter-height table, or freestanding
work surface with a load-bearing top.

Emits `support_structure`:

- permitted alternatives: legs, pedestal, cabinet bases, metal frame, or
  continuous side panels;
- select an alternative only when the drawing or specification supports it;
- do not substitute generic cabinet legs for a table leg, pedestal, or metal
  frame merely because all are supports;
- fallback: record an unresolved support-structure assumption for review.

## Non-goals and safety boundary

- The library does not choose a supplier SKU, brand, finish, or price.
- It does not prescribe routing, labor hours, or manufacturing method.
- It never turns a case-local research result into catalog data.
- It does not infer drawer slides, hinges, lift systems, handles, locks,
  fasteners, or internal fittings without a separate approved pattern or
  direct object evidence.
- A pattern may be activated only when its conditions and exclusions are
  evaluated and persisted in the estimate trace.

## Relationship to family impact

`estimation_impact` belongs to the Global Material Family Registry. It governs
how strictly a resolver may distinguish compatible variants after a pattern or
explicit evidence has established the required family. It never causes a
pattern to activate.

Initial conservative policy:

- `low`: generic compatibility may be allowed only through a named family
  compatibility rule. First candidate: adjustable cabinet legs within
  `hardware_leg_caster`.
- `medium`: a compatible match requires family plus material functional facts
  defined by that family.
- `high`: exact family contract and all price-bearing attributes are required.

The marker is not a proxy for unit price. A low-priced component can be high
impact when an incorrect variant changes feasibility or aggregate cost.
