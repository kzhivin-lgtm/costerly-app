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

Decompose the fixed object into large physical assemblies first. Then enumerate
only the approximate material-bearing components required to build those
assemblies. A component is:

`{"component_id":"...","component_role":"...","quantity":positive_integer,"length_mm":positive_number,"width_mm":positive_number,"material":{"source_name":"...","family":"one allowed family code","specification":{},"basis":"source_evidence|construction_assumption","evidence_refs":[...]},"geometry_basis":"evidence|derived|assumption","geometry_evidence_refs":[...],"assumption_reason":"string|null"}`

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
