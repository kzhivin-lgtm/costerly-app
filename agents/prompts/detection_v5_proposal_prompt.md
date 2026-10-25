# DETECTION V5.10.12 - FULL-PAGE ISLAND DISCOVERY

Return only the complete visual-Island inventory and its classification. You do
not decide object membership, create packages, merge edges, quantities, names,
dimensions or prices. Runtime owns Dimension Fingerprints, Weighted Similarity,
graph and final package decisions. A separate Review call is the sole author of
multi-View membership hypotheses and their typed evidence.

Inspect all full PNG pages and enlarged regions before JSON. First enumerate
every visual Island and classify it. Stop after the inventory and classification.

Return every Island `core_bbox` and `bbox` in the per-page FUSION coordinate
frame supplied in the user context. Do not use the displayed JPEG pixel
dimensions. `core_bbox` tightly encloses the physically continuous drawing.
`bbox` is its evidence envelope: the core plus attached outer dimensions,
dimension baselines, labels and leader lines, with only the necessary blank
space between them. It must not absorb a different Island or title block.

An Island is one distinct depiction. Separately framed elevations, plans,
sections, details and perspectives are separate Islands even when they depict
one physical item. A geometrically continuous drawing, including its attached
panel, rail, support or extension, is one Island. Preserve sparse technical
details as Object Evidence. Classify title blocks, generic plans, schedules,
legends and administrative material as Document Context.

Candidate Regions and Q are recall aids, not identity decisions. Recheck every
Candidate Region. Return one concrete exception for each Region that has no
distinct Island. Return schema JSON only.

Return exactly one compact `page_coverage` record for every supplied page.
Reference every returned Island exactly once on its source page. A page cannot
be omitted because it has no Candidate Region: inspect its full PNG before
returning that page's Island ID list, including an empty list when appropriate.

Also return one `document_scope` observation. This is routing evidence only,
not an object decision: it cannot merge, remove or reclassify an Island. Use
`assembly_dossier_candidate` only when this PDF appears to document one
commissioned assembly through one overview or root set plus connected sections,
carcasses, modules, components or hardware. Name the root Island IDs and cite
at least one concrete hierarchy, cross-reference or visual component witness.
Common client/order metadata, date, material, title block, page numbering or
page count may support document continuity but can never establish an assembly
scope alone. Use `ordinary_object_set` for independently quotable products and
`unresolved` when the relationship is unclear. Different dimensions between an
overall view and its internal carcass, door, drawer, module or hardware detail
are non-comparable, not evidence against one assembly. Only two explicitly
incompatible finished overall envelopes are a scope conflict.

`representation_kind` describes the visual form, never its evidence class.
Use `floor_plan` for a whole architectural room-and-circulation layout, and
classify it as Document Context, not Object Evidence.
