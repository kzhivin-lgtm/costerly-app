# DETECTION V4 - VISUAL REGISTRY

Build the visual representation map and the locked commercial-object registry in one response. First inspect the full pages and enlarged regions, then map visible representations, then decide the commercial objects. Keep these two levels separate in the output.

## Visual representations

Each `visual_group` is one visibly distinct depiction that could help a later stage understand an in-scope fabricated product: overview, alternate perspective, elevation, section, detail, module, door leaf, panel, track, cabinet bay, schedule, or assembly fragment. It is not automatically a commercial object, quote line or quantity. A shared schedule, title block, layout or multi-object context may remain an unassigned navigation group; it belongs in `page_coverage`, not in several object boundary lists.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal visual `visual_description`, neutral `representation_kind`, and exactly one `commercial_role`. Keep descriptions terse. A group records only that one visible depiction. Do not create a graph between groups: decide alternate views and product boundaries directly from the full visual evidence in the commercial registry.

`assembly_view` means the depiction shows enough of a whole, finished assembly to take part in object-identity resolution. It is a candidate view, not a declaration that it is a new or independent product. Only this role may appear in an object's `visual_group_ids`. `component_detail` means an isolated component, close-up, section, cutout, leaf, panel, track, module, hardware or construction fragment. It is evidence for the relevant assembly through `page_coverage`, but can never itself create a commercial object or appear in `visual_group_ids`. `document_context` means a title block, sheet layout, schedule, legend or other document context. It cannot create an object or appear in `visual_group_ids`. A visually isolated region is not automatically an `assembly_view`: use that role only when it shows a complete finished envelope or has explicit independent quote evidence. Conversely, a complete separately depicted assembly remains an `assembly_view` even without OCR or a code.

## Commercial registry

Decide complete fabricated products a contractor would quote, fabricate, supply, install, replace or price independently. Start only from `assembly_view` groups. A `component_detail` never becomes a commercial object merely because it appears separately. It remains supporting evidence on its page for the parent assembly. A `document_context` never becomes an object.

Before creating any object, resolve identity across all `assembly_view` groups. For every assembly view, decide whether it is a new product or another projection of a product already represented. Do not create one object per `assembly_view` by default. A change of projection may make the same item look unlike itself, so whole-silhouette similarity is not required. Resolve the relation using the following evidence, in priority order:

1. Explicit document relation: the same code, callout, view reference, axis or label.
2. Matching construction topology: the order and count of bays, doors, supports, carcasses, frames, appliances, joints and other structural elements.
3. Dimensions that agree after a change of axes or depict compatible portions of one assembly.
4. Repeated unique geometric features: cut-outs, handles, posts, appliance locations, turning parts, mounting points, panel sequence or distinctive frame geometry.
5. Secondary supporting signals only: being on one sheet, colour, material, visual proximity and room name. These may reinforce a relation already supported above, but never establish it alone.

When the evidence establishes the same product, put every corresponding `assembly_view` in one object's `visual_group_ids` and state the cross-view evidence in `boundary_basis`. When positive identity evidence is absent, do not invent a merge solely because the views look stylistically related.

Merge representations only with positive evidence that they show the same physical assembly: a shared distinctive silhouette and structure, an explicit view relation, a common object code, or a matching unique envelope and panel sequence. A shared page, room title, project, material palette, visual proximity, lack of object codes, or generic furniture scope is never merge evidence.

Before creating the registry, account for every separately depicted complete assembly on overview, plan, elevation or render pages. Map it to one commercial object, or merge it only after identifying the specific physical integration that makes it one assembly, such as a continuous carcass, worktop, frame, track, common mounting structure, or an explicit same-object relation. Adjacent furniture with separate finished envelopes and different functions remains separate even when it appears on every sheet, shares finishes, or is presented together. A one-object `boundary_basis` that covers several complete assemblies must state that positive integration, never merely call them an integrated system.

Different complete envelopes, functions, silhouettes or construction systems are strong independent-product evidence even without an object code. A vertical shelving unit, a track-supported door system and a long storage console separately drawn on one furniture sheet are three objects. Repeated projections remain one object each. Never absorb them into a generic room-furniture assembly.

A kitchen, integrated cabinet wall or shelving wall is one object. Its blocks, modules, panels, fronts, carcasses, profiles, hardware and assembly sheets are construction detail, not objects. Several leaves on one continuous track are one Door system with quantity 1 unless the source establishes separate systems, tracks, deliveries or quote quantities.

## Boundary-review mode

When the user message declares `BOUNDARY REVIEW MODE`, a deterministic preflight has found an unlabelled document with multiple large drawing areas. It does not decide any boundary, and it is not itself evidence that views are separate. It requires a more careful identity pass.

Before returning JSON in this mode, make a complete inventory of all visibly complete finished envelopes. For every `assembly_view`, assign exactly one commercial-object owner. If a depiction is not a complete fabricated product, classify it as `component_detail` or `document_context` and say only what is visibly shown. Never leave an `assembly_view` without an owner.

For every object that merges two or more `assembly_view` groups, its `boundary_basis` must identify the matching group IDs and the specific positive relation, such as matching bay topology, dimensions after axis change, a distinctive cutout or a shared continuous frame. Do not use a project name, room name, shared sheet, common finish or generic furniture type as the relation. If that positive relation is absent, retain separate objects.

If a later correction message identifies unowned assembly-view IDs, discard the earlier ownership decision for those views, re-read the pages and return a complete replacement registry. Do not assign a view arbitrarily merely to satisfy coverage.

`object_id` is ordered `object-001`, `object-002`, and so on. `transport_label` is an exact printed object code when present, otherwise `Object 1`, `Object 2`, and so on. `quantity` is complete physical units, defaulting to 1 when not explicit. `identity_pages` uses physical upload page numbers. `visual_group_ids` lists only `assembly_view` groups that prove this object's commercial boundary. A group has exactly one commercial-object owner and must never appear in more than one object's `visual_group_ids`. A `component_detail` or `document_context` must remain unassigned. If a shared page, schedule, title block or layout relates to several objects, assign every relevant object through `page_coverage` while leaving that context group unassigned. When one sheet visibly contains several complete assemblies, map them as separate `assembly_view` groups before assigning ownership. `visual_identity` states the complete physical product and its views, not one preferred image. `boundary_basis` records the factual reason this is one quote line.

## Evidence coverage

Evidence is the complete source context for the object, not a shortlist of pages that appear sufficient for a material calculation. For every physical upload page, return exactly one `page_coverage` entry. Put an object ID in `object_ids` whenever that page contains any visual, graphic, textual, layout, title, schedule, detail, plan, section, alternate view, assembly instruction or other source content that relates to that object. A page can belong to several objects. A render or picture is Evidence when it shows the object in another view. Do not omit a page merely because it lacks dimensions, material names, a crop-worthy region or an immediately calculable fact.

Use an empty `object_ids` only when the page contains no content related to any in-scope object. Give a brief factual `evidence_reason` for every page, including excluded pages. The runtime derives `estimation_evidence_pages` from this coverage, so it cannot silently discard an associated page. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or names. `boundary_basis` is the persisted decision audit: name the supporting visual groups or physical structure. If it merges separately depicted assemblies, state the specific positive integration that makes them one product. Never use a generic statement such as "one system" or "same sheet". Return schema JSON only.
