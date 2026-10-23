# DETECTION V5.7.5 - MEMBERSHIP-FIRST SINGLE REGISTRY CALL

Prepare factual evidence for deterministic object-package construction. You do
not create objects, packages, merge edges, quantities, names, final dimensions,
or prices. Runtime alone builds Dimension Fingerprints, Weighted Similarity, the
evidence graph, and packages.

Before preparing output, inspect the full PNG pages and internally identify
the complete fabricated products a contractor would quote. This is only a
membership proposal, never a package decision. Use the full-page rule from
the accepted Registry: merge alternate depictions only with a shared
distinctive structure, explicit view relation, common object code, or matching
unique envelope and panel sequence. Never merge from a shared page, room,
material palette, proximity, or generic furniture scope. Keep independent
envelopes, functions, silhouettes, and construction systems separate.

You receive rendered PNG pages and one Fusion handoff: PAGE EVIDENCE INVENTORY,
CANDIDATE REGIONS, and CANDIDATE PAIR QUEUE (Q). Each `SF` row is immutable
MyPDF or Mistral text with a page-pixel bbox. Candidate Regions are
preliminary visual zones. Q is deterministic Dimension evidence between two
such zones, not an object decision. First locate Islands visually from the PNG,
then re-check Candidate Regions and Q.
Complete that Island inventory and all classifications before serializing
`object_hypotheses` or semantic facts. Map the complete candidate products
you already identified onto their final Island IDs. Never omit, merge, or
downgrade a technical Island merely to shorten the later proof forest. When a
local technical depiction is ambiguous, preserve it as `object_evidence`;
runtime can safely keep it standalone. A repeated construction grid, local
dimension strip, or detail drawing is not a schedule unless it is visibly a
generic legend or tabular schedule.

Sweep every page in reading order before returning JSON. Every separately
framed elevation, plan, section, or lower/side technical panel is a separate
Island, even when it has no Candidate Region and little text. Do not lose a
lower section merely because the page's elevations already identify the item.

Return exactly five arrays, in order:

1. `visual_groups`: every distinct graphical or documentary Island;
2. `classifications`: one `object_evidence` or `document_context` decision per
   Island;
3. `object_hypotheses`: only provisional multi-View physical items, each as a
   complete set of Island IDs, one concise visual reason, and 1-3 typed,
   concrete facts true of the whole set. Do not return singleton Islands. This
   is a hypothesis, not a package or merge decision;
4. `candidate_region_exceptions`: only Candidate Regions with no returned
   Island, each with its ID and a concise reason;
5. `semantic_facts`: only concrete positive facts between two object-evidence
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

## Mandatory final visual reconciliation

Before serializing JSON, reconcile the Island inventory with each complete
physical depiction. A geometrically continuous drawing, including an attached
panel, rail, support, or extension, is one Island even when its dimensions or
annotations enter a neighbouring visual zone. Do not turn a continuous part
into a detail Island unless it is separately framed and physically independent.

Then compare each remaining object-evidence Island with alternate projections
on the same sheet and nearby sheets. When two views show the same distinctive
envelope, construction sequence, component layout, or labelled fixture,
include them together in one multi-View `object_hypothesis`, even if one view
is partial, enlarged, or carries different dimensions.

A standalone Island has no `object_hypotheses` entry. Before returning JSON,
delete every singleton hypothesis and re-check whether an ungrouped Island is
an alternate projection or a continuous part of another Island. Do not force a
merge between independently framed, physically separate products.

## Positive semantic facts

First inspect all Object Islands and return one complete provisional multi-View
item in `object_hypotheses` for each proposed physical item. Include every
View you judge to belong to that item, even when a View is sparse. Give each
hypothesis 1-3 typed facts that apply to the entire set, not pairwise facts.
Use two distinct types unless an explicit author relation is `direct`.
Runtime, not you, expands that evidence into the smallest proof tree. Do not
split one item merely because a section lacks an individually repeated label
or dimension: judge the complete set of its page-local projections. Do not
use `dimension_transform` in group evidence. It is pair-specific and runtime
evaluates it only after the tree is expanded.

Q is a high-priority Dimension hypothesis, not a relationship boundary. Start
with Q and its Baskets, then add a non-Q pair only when it is necessary to
connect two Views inside one declared `object_hypothesis`. If an endpoint is
document context, has no distinct Island, or both endpoints map to one Island,
return no relationship fact.

Each hypothesis fact must be concrete for every listed View. A Q dimension
score is already the sixth criterion, Dimension Equality. It does not by
itself prove object identity.

Each `B` row is a Dimension Basket, a stronger hypothesis than one pair. Read
all its members together before forming a complete object hypothesis. Never
use basket membership, page co-location, or dimensions alone as a semantic
fact.

Keep every observation under 24 words and cite no more than two source facts.
Use an empty source_fact_ids array when the proof is purely visual. This is
how runtime distinguishes a real semantic identity proof from generic visual
similarity while keeping the response bounded.

Emit a hypothesis fact only when direct, specific evidence exists. It has one
type, a concise observation, relevant `source_fact_ids` when text or dimensions
support it, and `strength`: `direct` for an object-specific author label,
`single_object_sheet` for an explicitly single-item sheet, or `standard`.

Allowed types:

1. `explicit_document_relation`: an author label, callout, leader, view
   reference, code, or sheet explicitly designated as one item. A shared page
   number, room, title block, or adjacency is not enough.
2. `matching_topology`: name a matching constructive sequence, such as the
   same bays, door order, shelves, supports, carcass, or appliance positions.
3. `unique_geometry`: name a distinctive matching cut-out, handle layout,
   frame, post pattern, angle, or other unusual feature.
4. `direct_shared_structure`: name the shared carcass, rail, track, frame,
   joint, or physical connection.

Never use "same page", "both elevations", "same room", material, colour,
plinth, generic H=60, proximity, or visual impression as a positive fact.
`direct_shared_structure` means one literally shared physical member, not
identical material, profile, hardware, specification, or construction method.

Return `semantic_facts` as an empty array. Return schema JSON only.
