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

## Compact output is a correctness requirement

Do not repeat dimensions, title-block text, source facts, labels, or reasoning
already present in the input. Use short, factual phrases only: `location_hint`
must identify position, `visual_description` must identify the depicted form,
and classification or exception reasons must state only the decisive fact. Do
not narrate the inspection. `page_coverage` contains IDs only.

Return exactly one compact `page_coverage` record for every supplied page.
Reference every returned Island exactly once on its source page. A page cannot
be omitted because it has no Candidate Region: inspect its full PNG before
returning that page's Island ID list, including an empty list when appropriate.

`representation_kind` describes the visual form, never its evidence class.
Use `floor_plan` for a whole architectural room-and-circulation layout, and
classify it as Document Context, not Object Evidence.

Use the exact `representation_kind` `presentation_render` for a photographic
render or photo that presents a fabricated object. Do not use it for a
line-drawn or dimensioned technical perspective. A presentation render remains
Object Evidence when it depicts fabrication, but it is not itself a commercial
object or a quantity decision.

Before returning each page, make a dedicated visual pass for photographic or
photorealistic rectangular images. Every visibly distinct render or photo of a
fabricated object is its own Object Evidence Island with the exact
`presentation_render` kind, even when it has no dimensions, labels or OCR text
and even when it sits near a title block. Never describe such an image as
document administration merely because it lacks technical annotations.
