# ESTIMATION CALCULATION V6.1, 2VN RECONCILIATION

V6.1 material_roles and panel_groups are locked in composition_scope. Preserve
each exact group_id and measured dimensions. Never reselect materials, stock
thickness, layers, alternatives or support construction. Record conflicts in
omissions. Reconcile geometry observations under the shared Analyze plan.

`composition_scope` is a locked Estimation Analyze contract. Reconcile only
dimensions, exposure and material roles for its listed scope zones. Return the
same `scope_id`, role, counts and front groups. Do not create a new zone or
turn a fixed screen, divider or slat array into a door or facade.

The supplied object identity is fixed. Do not rename it or classify it as a
product type. You receive bounded observations from every source-page batch,
not the page images themselves.

Reconcile only observations that clearly refer to the same physical assembly.
Do not invent details that no batch observed. Keep source evidence references
from the observations. A Dimension Graph relation is a candidate, not proof of
an axis or construction.

Return raw JSON only:

`{"document_unit":{...},"view_interpretations":[...],"dimension_bindings":[...],"assemblies":[...],"secondary_items":[...],"coverage":[...],"omissions":[...]}`

Each assembly must use the exact structural schema from the visual pass:
`assembly_id`, `assembly_role`, `quantity`, `evidence_refs`, `dimensions`,
`counts`, `front_groups`, `exposure`, and `material_roles`. Do not enumerate
finished parts. Preserve only one front group per physical operable front from
the canonical elevation. A lower shallow drawer row remains a separate
`drawer_bank`; a decorative slat, divider or fixed vertical panel is not a
front group and never creates operating hardware. Missing dimensions must remain an explicit derived or
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

Preserve or reconcile `view_interpretations` and `dimension_bindings` from
the batch observations. A direct binding must retain the same supplied
Dimension Graph id, view id, physical axis and local orientation. Do not
invent a binding merely to complete an assembly. An unresolved dimension is an
allowed explicit derivation or assumption, because estimation must finish even
when the document is incomplete.
