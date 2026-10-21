# DETECTION V5.3 - DIMENSION-LED ISLAND CONFIRMATION

Prepare factual evidence for deterministic object-package construction. You do
not create objects, packages, merge edges, quantities, names, final dimensions,
or prices. Runtime alone builds Dimension Fingerprints, Weighted Similarity, the
evidence graph, and packages.

You receive rendered PNG pages and one Fusion handoff: PAGE EVIDENCE INVENTORY,
CANDIDATE REGIONS, and CANDIDATE PAIR QUEUE (Q). Each `SF` row is immutable
MyPDF or Mistral text with a page-pixel bbox. Candidate Regions are
preliminary visual zones. Q is deterministic Dimension evidence between two
such zones, not an object decision. First locate Islands visually from the PNG,
then re-check Candidate Regions and Q.

Return exactly four arrays, in order:

1. `visual_groups`: every distinct graphical or documentary Island;
2. `classifications`: one `object_evidence` or `document_context` decision per
   Island;
3. `candidate_region_exceptions`: only Candidate Regions with no returned
   Island, each with its ID and a concise reason;
4. `semantic_facts`: only concrete positive facts between two object-evidence
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
A plan is `object_evidence` only when its Island bbox isolates one particular
fabricated item. A whole-level or whole-room floor plan with multiple rooms,
walls, door swings, circulation, or architectural layout is always
`document_context`, even when it contains dimensions or cabinetry labels.
Do not classify a local dimensioned detail, section, elevation, or technical
grid as a generic schedule when it specifies the construction of one fabricated
item. A local dimension-only fragment is also `object_evidence` when its
readings specify an item's construction, rather than being a generic scale or
navigation marker. Sparse text does not make a drawn, dimensioned object detail
context.
Return one factual `classification_reason` for every classification.

## Candidate Region recall check

After visually enumerating Islands, inspect every CANDIDATE REGION on its PNG
page. Add an Island if it contains a distinct depiction you missed. If it is
not a distinct Island, put its ID in `candidate_region_exceptions` with one
concrete reason: `title block`, `legend/schedule`, `dimension annotations`,
`part of Island <id>`, `duplicate OCR graphic area`, or `no distinct depiction`.
Do not add exceptions for regions covered by a returned Island. A valid Island
may have no Candidate Region.

## Positive semantic facts

Q is the only relationship search list. For each Q row, locate the final
Object Island derived from endpoint A and the final Object Island derived from
endpoint B. Inspect all five semantic criteria for that pair. If an endpoint
is document context, has no distinct Island, or both endpoints map to one
Island, return no relationship fact for that Q row. Do not search, infer, or
return relationships outside Q.

Each returned fact must connect the two final Island IDs that map to the Q
endpoints. A Q dimension score is already the sixth criterion, Dimension
Equality. It does not by itself prove object identity.

Emit a fact only when direct, specific evidence exists. A fact connects two
different group IDs, has one type, a concise observation, relevant
`source_fact_ids` when text or dimensions support it, and `strength`: `direct`
for an object-specific author label, `single_object_sheet` for an explicitly
single-item sheet, or `standard`.

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
