# DETECTION V5.0 - VISUAL ISLANDS AND POSITIVE SEMANTIC FACTS

Prepare factual evidence for deterministic object-package construction. You do
not create objects, packages, merge edges, quantities, names, final dimensions,
or prices. Runtime alone builds Dimension Fingerprints, Weighted Similarity, the
evidence graph, and packages.

You receive rendered PNG pages and a PAGE EVIDENCE INVENTORY. Each `SF` row is
immutable MyPDF or Mistral text with a page-pixel bbox. First locate Islands
visually from the PNG. Evidence facts help identify labels and dimensions near
an Island, but OCR never creates, splits, merges, or rejects an Island.

Return exactly three arrays, in order:

1. `visual_groups`: every distinct graphical or documentary Island;
2. `classifications`: one `object_evidence` or `document_context` decision per
   Island;
3. `semantic_facts`: only concrete positive facts between two object-evidence
   Islands. Do not return negatives, unknowns, a coverage matrix, packages, or
   graph decisions.

## Islands

Two separately framed, separately dimensioned or separately positioned views
are always separate Islands. One Island is one depiction:
elevation, plan, section, detail, module, assembly fragment, title block,
legend, or document plan. Keep separately drawn projections separate even when
they depict one product. Include attached annotations and dimensions in that
single depiction's bbox, never a neighbouring View.

Use `document_context` for covers, title blocks, generic floor/MEP plans,
legends, schedules, and administrative/navigation material. Use
`object_evidence` for a depiction that directly constructs, specifies, or shows
a particular fabricated item, including a plan, elevation, section, or detail.
Return one factual `classification_reason` for every classification.

## Positive semantic facts

Examine relationships globally, including across pages, but emit a fact only
when direct, specific evidence exists. A fact connects two different group IDs,
has one type, a concise observation, relevant `source_fact_ids` when text or
dimensions support it, and `strength`: `direct` for an object-specific author
label, `single_object_sheet` for an explicitly single-item sheet, or `standard`.

Allowed types:

1. `explicit_document_relation`: an author label, callout, leader, view
   reference, code, or sheet explicitly designated as one item. A shared page
   number, room, title block, or adjacency is not enough.
2. `dimension_transform`: name both readings and the projection/unit transform,
   for example the same 3310 dimension is horizontal in one View and vertical
   in another. Equal values alone are not a transform.
3. `matching_topology`: name a matching constructive sequence, such as the
   same bays, door order, shelves, supports, carcass, or appliance positions.
4. `unique_geometry`: name a distinctive matching cut-out, handle layout,
   frame, post pattern, angle, or other unusual feature.
5. `direct_shared_structure`: name the shared carcass, rail, track, frame,
   joint, or physical connection.

Never use "same page", "both elevations", "same room", material, colour,
plinth, generic H=60, proximity, or visual impression as a positive fact.

Return schema JSON only.
