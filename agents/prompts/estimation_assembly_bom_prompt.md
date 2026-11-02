# ESTIMATION STRUCTURAL BOM V4.17

The supplied object identity is fixed. Do not rename it, classify it as a
product type, or infer a catalog item, price, labour, manufacturing operation,
overhead or sale price.

Inspect every supplied page, its bounded OCR evidence and the Dimension Graph.
The graph contains source numbers and relation candidates only. A number is not
an object dimension unless its cited source context supports that use.

Return raw JSON only:

`{"batch_id":"...","pages":[...],"document_unit":{...},"assemblies":[...],"secondary_items":[...],"coverage":[...],"omissions":[...]}`

`pages` must contain every supplied page exactly once as `{"page_number":N}`.

First return exactly one document unit context:

`{"unit":"mm|cm|m","basis":"explicit_source|document_convention_assumption","evidence_refs":[...],"assumption_reason":"string|null"}`

Use `explicit_source` only when the unit is stated or unambiguously conventional in the drawing. A unitless drawing may use `document_convention_assumption`, with no evidence refs and one short reason. Infer that convention from the actual dimension lines and the physical scale of the depicted object as a whole. Ignore titles, labels and other non-dimensional text. This unit is the default for all dimensions unless a dimension explicitly overrides it.

`dimension_scale_gate` is a deterministic product safety constraint. When it
contains `decision.required_unit`, use that unit for a unitless document. Do
not override it from labels, watermarks, titles or a bare model convention.
Explicit source unit labels still win.

An assembly is:

`{"assembly_id":"assembly-N","assembly_role":"box_carcass|drawer_bank|vertical_panel|shelf_stack|table|countertop|facade_set","quantity":positive_integer,"evidence_refs":[...],"dimensions":{...},"counts":{...},"material_roles":[...]}`

Every `evidence_refs`, `geometry_evidence_refs` and source-material
`evidence_refs` value must be copied exactly from one supplied
`source_evidence_ref` or OCR `block_ref`. Never use a page label, `page-N`, a
Dimension Graph `dimension_id`, a view id, a segment id, an assembly id or a
description as an evidence reference.

Decompose the fixed object into large physical assemblies only. Do not list
finished panels, drawer sides, backs or bottoms. The deterministic composer
will derive conventional structural panels from the assembly topology.

`dimensions` contains each applicable `width`, `height`, or `depth` as:

`{"value":positive_number,"unit":"mm|cm|m|null","unit_basis":"explicit_source|document_convention_assumption|null","basis":"source|derived|assumption","evidence_refs":[...],"assumption_reason":"string|null"}`

For example, if a width label is `158` in a centimetre drawing, return
`{"value":158,"basis":"source","evidence_refs":[...]}`. Do not convert it.
Set `unit_basis=explicit_source` only when that individual axis prints its
unit. If its unit merely follows document convention, use
`document_convention_assumption`. A bare `unit="mm"` is not evidence by
itself.
Do not infer finished part dimensions or panel thicknesses. The system applies
named conventional construction assumptions after this response.

`counts` may contain only shown or strongly supported integers: `drawers`,
`shelves`, `facades`, `top_layers`, `legs`. Omit a count rather than guess it.

`material_roles` may contain only `visible_sheet`, `internal_sheet`,
`backing_sheet`, `worktop_sheet`, `finish`, `drawer_slide`, `leg`. Every role
is `{"role":"...","source_name":"...","family":"one allowed family code","specification":{},"basis":"source_evidence|construction_assumption","evidence_refs":[...]}`.
The model may select a construction-assumption family from the supplied allowed
families when the document has no material text. Do not emit a thickness unless
the drawing explicitly states it. Do not emit a material role that has no
physical use in the assembly.

Use `secondary_items` only for an explicitly countable shown fitting outside
an assembly: `{"secondary_id":"secondary-N","role":"drawer_slide|leg","quantity":positive_integer,"evidence_refs":[...],"material":{...}}`.
Do not manufacture rails, fasteners, handles, hinges, minor trim or decorative
overlays. List intentionally uncounted visible things in `omissions`.

Every supplied `region_id` must appear exactly once in `coverage`:

`{"region_id":"pN-region-NNN","disposition":"assembly|secondary_item|excluded","target_id":"assembly-N|secondary-N|null","reason":"..."}`

Use `assembly` for every visible material-bearing structural zone, including
drawers, fronts, tops, carcasses, panels, screens and legs. Use
`secondary_item` for a separately countable fitting. `excluded` is valid only
for `unshown_fasteners`, `minor_unmeasured_trim`, `reference_only` or
`non_material_annotation`. Never silently discard a material-bearing zone. If
its construction is unclear, create the closest supported approximate assembly
and state the construction assumption in that assembly rather than excluding it.

For source and derived dimensions cite exact source evidence refs. For an
assumption cite no dimension evidence and provide a concise reason. A source
material may use `source_evidence` only when the document identifies it.
Otherwise use `construction_assumption` and choose only from
`allowed_material_families`.

Do not turn repeated visible elements into drawers, shelves or facades unless
their construction is supported by source context. Do not split a finished
component merely to fit a purchasable sheet.
