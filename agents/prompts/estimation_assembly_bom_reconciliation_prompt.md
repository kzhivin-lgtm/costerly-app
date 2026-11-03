# ESTIMATION STRUCTURAL BOM V5.1 RECONCILIATION

The supplied object identity is fixed. Do not rename it or classify it as a
product type. You receive bounded observations from every source-page batch,
not the page images themselves.

Reconcile only observations that clearly refer to the same physical assembly.
Do not invent details that no batch observed. Keep source evidence references
from the observations. A Dimension Graph relation is a candidate, not proof of
an axis or construction.

Return raw JSON only:

`{"document_unit":{...},"assemblies":[...],"secondary_items":[...],"coverage":[...],"omissions":[...]}`

Each assembly must use the exact structural schema from the visual pass:
`assembly_id`, `assembly_role`, `quantity`, `evidence_refs`, `dimensions`,
`counts`, `front_groups`, `exposure`, and `material_roles`. Do not enumerate
finished parts. Preserve only one front group per physical front from the
canonical elevation. Missing dimensions must remain an explicit derived or
construction assumption, never a reason to discard the cabinet.

`coverage` is optional audit metadata. Preserve valid batch entries when they
are useful, and retarget them only to a reconciled `assembly_id` or
`secondary_id`. Its absence never invalidates an assembly. Preserve a deterministic `dimension_scale_gate` constraint when it
requires a unit for a unitless document.

Every evidence reference must be an exact original `storage://...` source
reference or OCR `block_ref` preserved in a batch observation. Do not return a
page label, graph id, view id or segment id as evidence.

Prefer fewer well-supported large assemblies to a fake complete shop drawing.
Do not split a finished component merely to fit a purchasable sheet.
