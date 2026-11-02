# ESTIMATION ASSEMBLY-FIRST BOM V1

The supplied object identity is fixed. Do not rename it, classify it as a
product type, or infer a catalog item, price, labour, manufacturing operation,
overhead or sale price.

Inspect every supplied page, its bounded OCR evidence and the Dimension Graph.
The graph contains source numbers and relation candidates only. A number is not
an object dimension unless its cited source context supports that use.

Return raw JSON only:

`{"batch_id":"...","pages":[...],"assemblies":[...],"omissions":[...]}`

`pages` must contain every supplied page exactly once as `{"page_number":N}`.

An assembly is:

`{"assembly_id":"assembly-N","evidence_refs":[...],"components":[...]}`

Every `evidence_refs`, `geometry_evidence_refs` and source-material
`evidence_refs` value must be copied exactly from one supplied
`source_evidence_ref` or OCR `block_ref`. Never use a page label, `page-N`, a
Dimension Graph `dimension_id`, a view id, a segment id, an assembly id or a
description as an evidence reference.

Decompose the fixed object into large physical assemblies first. Then enumerate
only the approximate material-bearing components required to build those
assemblies. A component is:

`{"component_id":"...","component_role":"...","quantity":positive_integer,"length_value":positive_number,"width_value":positive_number,"dimension_unit":"mm|cm|m","dimension_unit_basis":"explicit_source|document_convention_assumption","material":{"source_name":"...","family":"one allowed family code","specification":{"thickness_mm":positive_number},"basis":"source_evidence|construction_assumption","evidence_refs":[...]},"geometry_basis":"evidence|derived|assumption","geometry_evidence_refs":[...],"assumption_reason":"string|null"}`

`length_value` and `width_value` are the numeric values read from the drawing
or selected by an explicit construction assumption. `dimension_unit` is their
source unit. If the document convention is centimetres, return
`length_value=158`, `dimension_unit="cm"`; the system, not you, converts that
to 1580 mm. For unitless source dimensions, choose mm, cm or m only as an
explicit `document_convention_assumption` and state that choice in
`assumption_reason`.
Every flat structural panel must carry a positive `thickness_mm`, cited or
assumed. An empty material specification is invalid.

Use a component only when its broad construction is visible, stated, or a
bounded conventional inference. Do not manufacture tiny gaps, decorative
overlays, fittings, rails, fasteners, handles, hinges or slides that are not
explicitly shown. List such intentionally uncounted things in `omissions` as
short strings. If a visible fitting is explicitly countable, return it as a
component with its shown piece geometry only when both physical dimensions are
available; otherwise omit it rather than invent dimensions.

For `geometry_basis=evidence` and `derived`, cite exact source evidence refs.
For `assumption`, cite no geometry evidence and provide a concise
`assumption_reason`. A source material may use `source_evidence` only when the
document identifies it. Otherwise use `construction_assumption`, name it as an
assumption, and choose only from `allowed_material_families`.

Do not turn repeated visible elements into doors, drawers, shelves, or any
other semantic part unless their construction is supported by the source
context. Do not split a finished component merely to fit a purchasable sheet.
