# ESTIMATION ASSEMBLY-FIRST BOM RECONCILIATION V1

The supplied object identity is fixed. Do not rename it or classify it as a
product type. You receive bounded observations from every source-page batch,
not the page images themselves.

Reconcile only observations that clearly refer to the same physical assembly.
Do not invent details that no batch observed. Keep source evidence references
from the observations. A Dimension Graph relation is a candidate, not proof of
an axis or construction.

Return raw JSON only:

`{"assemblies":[...],"omissions":[...]}`

Each assembly and component must use the exact schema from the visual pass:
`assembly_id`, `evidence_refs`, and `components`; each component must contain
`component_id`, `component_role`, `quantity`, `length_mm`, `width_mm`,
`material`, `geometry_basis`, `geometry_evidence_refs`, and
`assumption_reason`.

Prefer fewer well-supported large assemblies to a fake complete shop drawing.
Do not split a finished component merely to fit a purchasable sheet.
