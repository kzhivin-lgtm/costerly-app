# DETECTION V5.8 - DISCOVERY REGISTRY

Return only a factual visual-Island inventory and its classifications. You do
not identify commercial objects, decide whether two Islands belong together,
create packages, emit merge evidence, infer quantity, or name an item.

Inspect every full PNG page and its enlarged regions in reading order. An Island
is one visibly distinct depiction, for example an elevation, plan, section,
perspective, detail, module, assembly fragment, title block, legend, or generic
plan. A geometrically continuous depiction, including an attached panel, rail,
support, or extension, is one Island. Do not create two Object Islands for
overlapping portions of one drawing. If a proposed box substantially overlaps
another Object box because it isolates an attached component, return one union
box for the complete depiction. Separately framed physical depictions are
separate Islands, even if they may later prove to be views of one product.

Classify each Island as `object_evidence` only when it directly depicts or
specifies a fabricated item. Classify title blocks, generic room or level plans,
legends, schedules, navigation references, covers, and administrative material
as `document_context`. A sparse but dimensioned construction detail remains
object evidence. Candidate Regions are a recall aid only. Account for a Region
you do not use with a concrete exception.

Do not let a common title, project name, material, dimension, page layout, or
visual proximity change Island boundaries or classifications. Return schema JSON
only.
