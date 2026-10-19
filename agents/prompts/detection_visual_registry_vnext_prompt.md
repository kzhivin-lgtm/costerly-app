# DETECTION V4 - VISUAL REGISTRY

Build the visual representation map and the locked commercial-object registry in one response. First inspect the full pages and enlarged regions, then map visible representations, then decide the commercial objects. Keep these two levels separate in the output. Use the Pairwise merge-proof procedure before linking multiple object-evidence groups to one commercial object.

## Visual representations

Each `visual_group` is one visibly distinct source depiction that can help a later stage understand an in-scope fabricated object: overview, alternate perspective, elevation, plan, section, detail, module, door leaf, panel, track, cabinet bay, schedule, or assembly fragment. It is not automatically a commercial object, quote line or quantity.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal visual `visual_description`, neutral `representation_kind`, and exactly one `evidence_class`. Keep descriptions terse. A group records only that one visible depiction. There are only two classes.

`object_evidence` is any graphical depiction or literal construction information that can help identify, construct or price an in-scope fabricated object. It includes complete or partial views, elevations, plans, perspectives, sections, close-ups, cutouts, component details, modules, panels, leaves, tracks, dimensions and material callouts. No form of object evidence is by itself a declaration that it is a new or independent commercial object. A detail stays object evidence, never document context, because it can be necessary Evidence for its parent object.

`document_context` is a narrow exclusion class: a title block, pure administrative text, legend, schedule, navigation-only floor plan, or a semantically headed table that contains no graphical or literal construction information for an in-scope fabricated object. A repeated grid, dimension string, repeated bays, slats, shelves or panel divisions is not a table by itself. Do not classify a plan, elevation, diagram, section or detail as document context merely because it is schematic, dense, shares a page with text or locates an object in a room.

Do not use the evidence class to decide whether two depictions are the same object. That decision belongs only to commercial package resolution.

## Commercial registry

Decide complete fabricated products a contractor would quote, fabricate, supply, install, replace or price independently from the full document. An `object_evidence` group never becomes a commercial object merely because it appears separately. A `document_context` never becomes an object.

Before creating any object, resolve identity across all relevant object evidence. For every evidence group, decide whether it proves a separately quoted product, another view of an existing product, or a supporting detail of an existing product. Do not create one object per visual group by default. A change of projection may make the same item look unlike itself, so whole-silhouette similarity is not required. Resolve the relation using the following evidence, in priority order:

1. Explicit document relation: the same code, callout, view reference, axis or label.
2. Matching construction topology: the order and count of bays, doors, supports, carcasses, frames, appliances, joints and other structural elements.
3. Dimensions that agree after a change of axes or depict compatible portions of one assembly.
4. Repeated unique geometric features: cut-outs, handles, posts, appliance locations, turning parts, mounting points, panel sequence or distinctive frame geometry.
5. Secondary supporting signals only: being on one sheet, colour, material, visual proximity and room name. These may reinforce a relation already supported above, but never establish it alone.

When the evidence establishes the same product or an object detail, put every corresponding `object_evidence` group in that object's `visual_group_ids` and state the cross-view evidence in `boundary_basis`. An object-evidence group may support several objects only when its visible content genuinely covers every one of them. When positive identity evidence is absent, do not invent a merge solely because the views look stylistically related.

## Pairwise merge-proof procedure

Start from separate commercial objects. Before grouping two `object_evidence` groups under one object, apply this comparison to that pair. Different finished envelopes, principal functions, or primary dimensions are affirmative evidence of separate commercial objects. A pair can link only when the source overcomes that evidence, or when one is a proved detail of the other object.

Test commercial separability, not merely visual adjacency. Ask whether each finished assembly could reasonably be fabricated, transported, installed, replaced, or priced separately. A shared page, room title, project, material palette, visual proximity, L-shaped placement, lack of object codes, or generic furniture scope never proves a merge. A shared worktop, touching side panels, or an apparent continuous carcass is only a candidate physical connection. It does not prove one commercial object unless the drawing also shows why the two parts are commercially inseparable.

An explicit same code, callout, or view reference can prove identity on its own. Without one, a merge needs at least two independent evidence types and at least one identity-level comparison: matching construction topology, dimensions that agree after a change of axes, or repeated unique geometry. Direct shared structure may support a merge but cannot be its only evidence. Never infer a shared carcass or continuous construction from adjacency, an L-shaped layout, or matching finishes.

A recognized kitchen, integrated cabinet wall, shelving wall, or one continuous door-track system may remain one commercial object when the visual evidence establishes one integrated joinery envelope. Its modules, appliances, panels, fronts, and details are not separate objects. A worktop alone must not absorb adjacent non-kitchen furniture into that object.

`merge_proofs` is a compact flat list of edges, not a second analysis stage, per-object checklist, or all-pairs graph. For every object with N `visual_group_ids`, return exactly N-1 proofs which connect those distinct groups. A one-view object contributes zero entries. Never create a placeholder, self-link, empty proof, or `from_group_id == to_group_id` entry. Each proof has one `relationship`: `same_object_view` for two representations of one object, or `object_detail` for a section, node, module or detail that belongs to that object. Each proof contains its two different group IDs, source pages, a concrete observed fact, controlled `evidence_types`, and the observed reason they belong to the same object. The group IDs may be linked in any order. Do not use generic statements such as "one system", "same room", or "continuous L-shape" as the observed fact or relationship reason. A printed code, callout or reference that covers a detail is an explicit document relation. If a page contains only multiple details for one coded object, link those details with the applicable proof edges instead of omitting `merge_proofs`.

Before creating the registry, account for every `object_evidence` group. Link it to at least one commercial object, or mark it document context only when it truly contains no in-scope object evidence. Adjacent furniture with separate finished envelopes and different functions remains separate even when it appears on every sheet, shares finishes, touches, or is presented together. A one-object `boundary_basis` that covers several complete assemblies must state the proof-backed integration, never merely call them an integrated system.

Different complete envelopes, functions, silhouettes or construction systems are strong independent-product evidence even without an object code. A vertical shelving unit, a track-supported door system and a long storage console separately drawn on one furniture sheet are three objects. Repeated projections remain one object each. Never absorb them into a generic room-furniture assembly.

A kitchen, integrated cabinet wall or shelving wall is one object. Its blocks, modules, panels, fronts, carcasses, profiles, hardware and assembly sheets are construction detail, not objects. Several leaves on one continuous track are one Door system with quantity 1 unless the source establishes separate systems, tracks, deliveries or quote quantities.

`object_id` is ordered `object-001`, `object-002`, and so on. `transport_label` is an exact printed object code when present, otherwise `Object 1`, `Object 2`, and so on. `quantity` is complete physical units, defaulting to 1 when not explicit. `identity_pages` uses physical upload page numbers. `visual_group_ids` lists every related `object_evidence` group, including full views and details. A group may appear in more than one object's list only when it visibly supports each object. `document_context` must remain out of every `visual_group_ids`, but its page may be Evidence for several objects through `page_coverage`. `visual_identity` states the complete physical product and its views, not one preferred image. `boundary_basis` records the factual reason this is one quote line. `merge_proofs` is always present, including as an empty list when every object has one evidence group.

## Evidence coverage

Evidence is the complete source context for the object, not a shortlist of pages that appear sufficient for a material calculation. For every physical upload page, return exactly one `page_coverage` entry. Put an object ID in `object_ids` whenever that page contains any visual, graphic, textual, layout, title, schedule, detail, plan, section, alternate view, assembly instruction or other source content that relates to that object. A page can belong to several objects. A render or picture is Evidence when it shows the object in another view. Do not omit a page merely because it lacks dimensions, material names, a crop-worthy region or an immediately calculable fact.

Use an empty `object_ids` only when the page contains no content related to any in-scope object. Give a brief factual `evidence_reason` for every page, including excluded pages. The runtime derives `estimation_evidence_pages` from this coverage, so it cannot silently discard an associated page. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or names. `boundary_basis` is the persisted decision audit: name the supporting visual groups or physical structure. If it merges separately depicted assemblies, state the specific positive integration that makes them one product. Never use a generic statement such as "one system" or "same sheet". Return schema JSON only.
