# Detection V8: Discovery

Inspect every supplied full page and enumerate visually distinct islands. A
Candidate Region is only a recall aid. It is not an island, an object, a
dimension source, a membership hint or an instruction to copy its bbox.

For every observed island, return one decision:

- `object_evidence`: a separately framed technical plan, elevation, section,
  detail, perspective, render/photo of a fabricated object, module or
  construction.
- `exclude`: title block, schedule, legend, navigation, revision material or a
  dominant whole-level floor plan.

Use `presentation_render` only for photorealistic render/photo evidence. It is
still Object Evidence, but it is not an object by itself. Technical line
drawings and dimensioned perspectives are not presentation renders.

Use `floor_plan` only for a room-and-circulation or whole-level architectural
plan. A dominant whole-level floor plan must be `exclude` with
`exclusion_kind=floor_plan`. A bounded plan of one fabricated item remains
`object_evidence`, even if it looks plan-like.

`core_bbox` encloses the physical depiction. `bbox` is its evidence envelope,
including only the attached dimensions, labels and leaders needed to interpret
that depiction. Never use a Candidate Region boundary as either box merely
because it was supplied.

Keep `visual_description` and `reason` each to at most twelve words. Do not
repeat page number, coordinates, candidate IDs, OCR text or dimensions in those
fields. Return only schema JSON.
