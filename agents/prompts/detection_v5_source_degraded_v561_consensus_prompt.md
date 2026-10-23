# DETECTION V5.16 - V5.6.1 FULL-PAGE VISUAL PROPOSAL

Prepare a factual visual-membership proposal for deterministic object-package
construction. You do not create objects, packages, merge edges, quantities,
names, final dimensions, or prices.

This document has no usable coordinate-bearing PDF or OCR evidence. Inspect
only the complete rendered PNG pages supplied to you. There are no Candidate
Regions and no Dimension Queue in this route. Do not infer a relationship from
missing source text.

Before preparing output, inspect every full PNG page and internally identify
the complete fabricated products a contractor would quote. This is only a
membership proposal, never a package decision. Merge alternate depictions only
with a shared distinctive structure, explicit view relation, common object
code, or matching unique envelope and panel sequence. Never merge from a
shared page, room, material palette, proximity, generic furniture scope, or a
shared construction principle. Keep independent envelopes, functions,
silhouettes, and construction systems separate.

Complete the Island inventory and classifications before serializing
`object_hypotheses`. Map every complete candidate product onto final Island
IDs. Never omit, merge, or downgrade a technical Island merely to shorten a
later proof. When a local technical depiction is ambiguous, preserve it as
`object_evidence`; runtime can safely keep it standalone.

Sweep every page in reading order before returning JSON. Every separately
framed elevation, plan, section or lower/side technical panel is a separate
Island, even when it has little text. One continuous physical depiction remains
one Island even when it bends, branches, contains annotations, or has an
irregular silhouette. Its rectangular bbox is only a padded transport envelope.

Return exactly five arrays, in order:

1. `visual_groups`: every distinct graphical or documentary Island;
2. `classifications`: one `object_evidence` or `document_context` decision per
   Island;
3. `object_hypotheses`: only provisional multi-View physical items, each as a
   complete set of Island IDs, one concise visual reason, and 1-3 typed,
   concrete facts true of the whole set. Do not return singleton Islands;
4. `candidate_region_exceptions`: always an empty array;
5. `semantic_facts`: always an empty array.

## Islands

Two separately framed, separately dimensioned or separately positioned views
are separate Islands. One Island is one depiction: elevation, plan, section,
detail, module, assembly fragment, title block, legend or document plan. Keep
separately drawn projections separate even when they depict one product.
Include attached annotations and dimensions in that depiction's bbox, never a
neighbouring View.

Use `document_context` for covers, title blocks, generic floor or MEP plans,
legends, schedules and administrative/navigation material. Use
`object_evidence` for a depiction that directly constructs, specifies, or shows
a particular fabricated item. A whole-level or whole-room floor plan with
multiple rooms, walls, door swings, circulation or architectural layout is
always `document_context`.

Return one factual `classification_reason` for every classification.

## Object hypotheses

First inspect all Object Islands and return one complete provisional multi-View
item for each proposed physical item. Include every View you judge to belong to
that item, even when a View is sparse. Give each hypothesis 1-3 typed facts
that apply to the entire set, not pairwise facts. Use two distinct types unless
an explicit author relation is direct. Runtime, not you, expands evidence into
the smallest proof tree.

Do not split one item merely because a section lacks an individually repeated
label or dimension. Judge the complete set of page-local projections. A visible
dimension can support or contradict an identity claim, but this route does not
have a deterministic Dimension Engine.

Each hypothesis fact must be concrete for every listed View. Use an empty
`source_fact_ids` array because this route has no coordinate-bearing source
facts. A dimension-like visual resemblance alone does not prove object
identity.

Allowed types:

1. `explicit_document_relation`: an author label, callout, leader, view
   reference or code visibly designated as one item;
2. `matching_topology`: a matching constructive sequence, such as the same
   bays, door order, shelves, supports, carcass or appliance positions;
3. `unique_geometry`: a distinctive matching cut-out, handle layout, frame,
   post pattern, angle or other unusual feature;
4. `direct_shared_structure`: one literally shared physical member, not
   identical material, profile, hardware, specification or construction method.

Never use same page, same room, material, colour, generic frame type,
proximity or visual impression as positive identity evidence. Return schema JSON only.
