# Provisional Estimate and Catalog Gap Contract, 3.17.1

Status: owner-accepted semantic contract, implementation in progress.

## Purpose

Every object receives a numerical provisional estimate even when a required
catalog fact is missing. The provisional decision belongs only to that estimate.
It is not a candidate catalog record and has no effect on later estimates.

## Case-local assumption

One assumption records one answer to one unresolved question for one object
estimate. It contains the unresolved kind, chosen value, confidence, source
references, calculation impact and the exact evidence/Agent version that
produced it.

Allowed kinds are:

- `material_identity`
- `material_supply`
- `price_source`
- `operation`
- `labor_route`
- `labor_recipe`

The fallback order is exact approved catalog evidence, then bounded research
for this case, then a named comparable assumption. The final fallback must
still be numerical, but is visibly provisional. It may not be written to any
canonical catalog relation.

## Catalog Gap Job

A job groups repeat occurrences of the same unresolved catalog question. Its
deduplication key is produced from normalized gap type, market, material or
operation statement and route-critical attributes. It stores no automatic
catalog answer. It links to occurrences, which link back to case-local
assumptions and source evidence.

Lifecycle: `open` -> `research_pending` -> `staff_review` -> `resolved` or
`rejected`. A staff member may later create an authoritative catalog entry in a
separate, audited catalog action. Resolving a job never mutates historical
estimate assumptions.

## User-facing effect

The estimate remains priced and marked provisional. It displays the assumption,
reason, confidence and source provenance. A user never has to resolve a Catalog
Gap Job to receive an estimate.

## Catalog readers and user interfaces

The V2 model is a shared contract, not a database-only change. Price Source
ingestion, Price Source review/list screens, Company Catalog, Estimation/Object
Detail and the Staff Admin Inbox must read the same family, role and attribute
definitions. A production department or family is shown in Price Source only
when it has at least one eligible material row to display. Thus `stone` does
not create an empty visible section; after a Stone source row is resolved to a
canonical V2 material, it appears under Stone with its V2 category and family.
No interface may recreate a parallel category map or infer a department from a
display name.
