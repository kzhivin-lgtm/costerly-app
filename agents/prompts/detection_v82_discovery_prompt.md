# Detection V8.2: Discovery

Inspect every supplied full page. Return each visually distinct island once.
Candidate Recall Regions are source observations only. They never determine an
island bbox, an object, a merge, or a split.

For each island choose exactly one decision:

- `object_evidence`: a separately framed technical plan, elevation, section,
  detail, perspective, render/photo of a fabricated object, module or
  construction.
- `exclude`: title block, schedule, legend, revision material, navigation,
  document context, or a dominant whole-level floor plan.

Use the enumerated `representation_kind` values exactly. A whole-level room,
circulation or architectural floor plan is `floor_plan`, `exclude`, and
`exclusion_kind=floor_plan`. A bounded plan of one fabricated item is
`technical_plan` and remains `object_evidence`.

`presentation_render` means a photorealistic render or photograph only. It is
ordinary Object Evidence, never an object by itself. Do not call technical line
drawings or dimensioned perspectives presentation renders.

`core_bbox` encloses the physical depiction. `bbox` is only that depiction plus
its attached dimensions, labels and leaders. Do not copy a Candidate Recall
Region bbox. Keep `visual_description` and `reason` concise. Return schema JSON only.
