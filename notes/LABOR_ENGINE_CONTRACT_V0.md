# Labor engine contract v1

Status: active universal operation contract.

## Boundary

The Estimation Agent decomposes the actual supplied object into material
requirements and fabrication operations. The Labor Engine validates those
operations against company capabilities and converts physical driver quantities
into labor hours. It never chooses work from an object name or object class.

```text
source evidence
  -> agent-created material and fabrication plan
  -> material resolution and company capability validation
  -> deterministic operation formulas and role hours
  -> labor pricing and overhead
```

## Input

Each operation contains:

- stable operation id and an operation code from the versioned catalog;
- `in_house_manual` or `in_house_machine` route;
- positive physical quantity and unit;
- batch key;
- exact company machine capability for a machine route, otherwise null;
- affected material requirement ids;
- calculation basis, provenance, evidence and confidence.

The plan contains no prices, minutes, hours, labor rates, overhead, delivery or
site installation. Externally purchased fabrication is a purchased component
and cannot also appear as internal labor.

## Output

For every accepted operation, Labor Engine returns:

- selected route and validated machine capability;
- operation driver and batch key;
- baseline version and confidence;
- deterministic formula and elapsed productive minutes;
- role allocation and productive hours;
- evidence-bearing provenance.

The pricing layer applies company labor rates. The overhead layer consumes total
productive hours separately.

## Invariants

1. Object names never select materials, operations or routes.
2. Identical plans, catalog versions and company capabilities produce identical
   traces.
3. Machine work is accepted only when that exact capability is in the Company
   Profile.
4. Manual and machine routes cannot both charge for the same work.
5. Purchased fabrication produces no matching internal labor.
6. Missing or contradictory quantities and routes produce review, never hidden
   assumptions.
7. Delivery and site installation are project-level selling-price additions and
   never self-cost labor operations.
