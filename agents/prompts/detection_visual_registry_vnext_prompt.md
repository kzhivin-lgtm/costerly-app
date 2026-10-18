# DETECTION V4 - VISUAL REGISTRY

Build the visual representation map, representation packages and locked commercial-object registry in one response. Inspect the full pages and enlarged regions first. Decide the full-document measurement convention, visual roles, package membership, object IDs and required merge proofs before serializing. Then output in this order: document measurement context, visual groups, representation packages, pairwise merge proofs, commercial objects, page coverage. This is one request, but the levels have distinct meanings and must not be collapsed.

## Document measurement context

Return `document_measurement_context` with `unit` (`mm`, `cm`, `m`, `mixed`, or `unknown`), physical `evidence_pages`, and a factual `basis`. Determine it from repeated dimensions, scale labels and explicit unit marks across the entire document, not from one sheet. Use `mixed` when the document demonstrably uses more than one convention and `unknown` when no convention is supportable. This is internal visual-classification context only. It is not a Dimensions JSON and does not pass external dimensions to Estimation.

## Visual representations

Each `visual_group` is one visibly distinct depiction that could help a later stage understand an in-scope fabricated product: overview, alternate perspective, elevation, plan, section, detail, module, door leaf, panel, track, cabinet bay, schedule, or assembly fragment. It is not automatically a commercial object, quote line, quantity or representation package. A shared schedule, title block, layout or multi-object context may remain an unassigned navigation group; it belongs in `page_coverage`, not in several object boundary lists.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal visual `visual_description`, neutral `representation_kind`, exactly one `commercial_role`, and concise factual `role_basis`. A group records only that one visible depiction. `role_basis` is an inspectable decision record, not hidden reasoning: cite the visible facts that justify its role, and never use confidence language or a generic conclusion.

Before assigning roles, inventory every distinct drawing area on every sheet. On a dense sheet, create separate groups for each plan, full elevation, section, detail and document-context area. Do not collapse a multi-view sheet into one generic detail and one schedule. A fully bounded orthographic drawing of a finished envelope is an `assembly_view` when it has its own overall dimensions, a local code or callout, or another independent-product signal. This remains true when it is a frontal elevation, a dense grid, a repeated panel array, or contains construction annotations. Visual density, repetition and material layers alone never make a complete envelope a `component_detail`.

A bounded finished envelope with two overall dimensions that normalize under the document measurement context to at least 2 m on both axes is an `assembly_view` candidate, never a `component_detail`. It may still be merged into another projection at package stage. Do not apply this rule to an unbounded room plan, a schedule, or a section fragment. A local caption beside a drawing that describes or names the depicted product is evidence for that depiction, not document context. Only global title, revision and sheet-administration blocks are `document_context`.

`assembly_view` means a whole or plausibly whole view of one independently bounded finished assembly. It is a candidate view, not a declaration that it is a new or independent product. A front elevation, plan, section or axonometric drawing qualifies when it shows the product's complete outer envelope, principal functional whole, own overall dimensions, code, callout or another explicit independent-product signal. It does not need to be a perspective or show every construction detail. A separately dimensioned frontal view of a complete shelving, cabinet, counter, door system or other finished envelope is an `assembly_view`.

`component_detail` means a positively partial representation: an isolated component, close-up, section, cutout, leaf, panel, track, module, hardware or construction fragment. Do not assign this role merely because a view is flat, narrow, unrendered, lacks perspective, or omits some construction detail. When a view could reasonably show a complete separately fabricated envelope, use `assembly_view` and let the package step resolve its relation to other views.

`document_context` means a title block, sheet layout, schedule, legend or other document context. It cannot create an object or appear in an object boundary. A group records one representation only.

For `assembly_view`, `role_basis` must name the visible whole-envelope evidence, such as a complete outline, overall width and height, local code or callout, and an adjacent product-description note. State how the displayed dimensions use the document measurement context. Never invent `mm` when the document convention is `cm`, `mixed`, or `unknown`. For `component_detail`, name the positively partial fact, such as a cutaway, isolated profile, section fragment or hardware close-up, and the absence of a whole envelope. For `document_context`, state the context content and why it has no physical product outline. A repeated grid with a bounded full outline, overall dimensions, code or product note is not a schedule merely because it repeats.

## Representation packages

After every visual group has a role, collect related product depictions into `representation_packages`. A package is the explicit bridge between individual images and a commercial object. It is not a second provider call and it is not a visual crop.

Each package has `object_id`, `assembly_view_group_ids`, `supporting_component_detail_group_ids` and factual `package_basis`. The runtime assigns package IDs after the response. Do not output an ID for a package.

- Every `assembly_view` belongs to exactly one package.
- A package has at least one `assembly_view`.
- A `component_detail` may support one package only when its relation to that package is positively established. Otherwise leave it outside packages and preserve it through page coverage. Never make a component-only package or a placeholder package for unattached details.
- A `document_context` never belongs to a package.
- Every package is an independently quotable fabricated product. Set its `object_id` to the final ordered commercial object ID. Do not make non-commercial packages.

Build a package from the full document, not from silhouette similarity alone. Use code, callout, topology, compatible transformed dimensions, repeated unique geometry and direct construction relation. A change of projection may make one item look unlike itself. Conversely, do not merge separate finished envelopes merely because they are adjacent, share material, room, sheet or layout.

A package may contain one complete assembly view and supporting component details. Those details do not need pairwise merge proofs because they are not competing whole-object views. For example, a separately coded and dimensioned front elevation of a shelving unit is an `assembly_view`; its plan and profile details may support the same package. The package may become one commercial object.

## Commercial registry

Decide complete fabricated products a contractor would quote, fabricate, supply, install, replace or price independently. Create one commercial object for every representation package whose `object_id` is non-empty. The object's `visual_group_ids` must equal that package's `assembly_view_group_ids` exactly. `component_detail` supports package interpretation and Evidence, but never appears in an object's `visual_group_ids`. A `document_context` never becomes an object.

Before creating any object, resolve identity inside each package. For every assembly view, decide whether it begins a new package or is another projection of a package already represented. Do not create one package per `assembly_view` by default. A change of projection may make the same item look unlike itself, so whole-silhouette similarity is not required. Resolve the relation using the following evidence, in priority order:

1. Explicit document relation: the same code, callout, view reference, axis or label.
2. Matching construction topology: the order and count of bays, doors, supports, carcasses, frames, appliances, joints and other structural elements.
3. Dimensions that agree after a change of axes or depict compatible portions of one assembly.
4. Repeated unique geometric features: cut-outs, handles, posts, appliance locations, turning parts, mounting points, panel sequence or distinctive frame geometry.
5. Secondary supporting signals only: being on one sheet, colour, material, visual proximity and room name. These may reinforce a relation already supported above, but never establish it alone.

When the evidence establishes the same product, put every corresponding `assembly_view` in one package. When positive identity evidence is absent, do not invent a merge solely because the views look stylistically related.

## Pairwise merge-proof procedure

Start from separate commercial assemblies. Before grouping two `assembly_view` groups under one owner, apply this comparison to that pair. Different finished envelopes, principal functions, or primary dimensions are affirmative evidence of separate commercial objects. A pair can merge only when the source overcomes that evidence.

Test commercial separability, not merely visual adjacency. Ask whether each finished assembly could reasonably be fabricated, transported, installed, replaced, or priced separately. A shared page, room title, project, material palette, visual proximity, L-shaped placement, lack of object codes, or generic furniture scope never proves a merge. A shared worktop, touching side panels, or an apparent continuous carcass is only a candidate physical connection. It does not prove one commercial object unless the drawing also shows why the two parts are commercially inseparable.

An explicit same code, callout, or view reference can prove identity on its own. Without one, a merge needs at least two independent evidence types and at least one identity-level comparison: matching construction topology, dimensions that agree after a change of axes, or repeated unique geometry. Direct shared structure may support a merge but cannot be its only evidence. Never infer a shared carcass or continuous construction from adjacency, an L-shaped layout, or matching finishes.

A recognized kitchen, integrated cabinet wall, shelving wall, or one continuous door-track system may remain one commercial object when the visual evidence establishes one integrated joinery envelope. Its modules, appliances, panels, fronts, and details are not separate objects. A worktop alone must not absorb adjacent non-kitchen furniture into that object.

`merge_proofs` is a compact flat audit, not a second analysis stage or an all-pairs graph. Construct its proof tree while assigning every multi-view package, then serialize it immediately after `representation_packages`. For every commercial package with N `assembly_view_group_ids`, return exactly N-1 proofs which connect those views under that package's `object_id`. Return no proof for a one-view package. `merge_proofs` must not be empty if any package has more than one assembly view. Do not create proofs for supporting component details. Each proof contains its two group IDs, source pages, a concrete observed fact, controlled `evidence_types`, and the observed reason the parts are commercially inseparable. The group IDs may be linked in any order. Do not use generic statements such as "one system", "same room", or "continuous L-shape" as the observed fact or inseparability reason.

Before creating the registry, account for every separately depicted complete assembly on overview, plan, elevation or render pages. Map it to one representation package, or merge it only after its pairwise proof clears the commercial-separability test. Adjacent furniture with separate finished envelopes and different functions remains separate even when it appears on every sheet, shares finishes, touches, or is presented together. A one-object `boundary_basis` that covers several complete assemblies must state the proof-backed integration, never merely call them an integrated system.

Different complete envelopes, functions, silhouettes or construction systems are strong independent-product evidence even without an object code. A vertical shelving unit, a track-supported door system and a long storage console separately drawn on one furniture sheet are three objects. Repeated projections remain one object each. Never absorb them into a generic room-furniture assembly.

A kitchen, integrated cabinet wall or shelving wall is one object. Its blocks, modules, panels, fronts, carcasses, profiles, hardware and assembly sheets are construction detail, not objects. Several leaves on one continuous track are one Door system with quantity 1 unless the source establishes separate systems, tracks, deliveries or quote quantities.

`object_id` is ordered `object-001`, `object-002`, and so on. `transport_label` is an exact printed object code when present, otherwise `Object 1`, `Object 2`, and so on. `quantity` is complete physical units, defaulting to 1 when not explicit. `identity_pages` uses physical upload page numbers. `visual_group_ids` lists only the `assembly_view` groups of this object's representation package. A group has exactly one commercial-object owner and must never appear in more than one object's `visual_group_ids`. A `component_detail` or `document_context` cannot be in `visual_group_ids`. If a shared page, schedule, title block or layout relates to several objects, assign every relevant object through `page_coverage` while leaving that context group outside object boundaries. When one sheet visibly contains several complete assemblies, map them as separate `assembly_view` groups before package assignment. `visual_identity` states the complete physical product and its views, not one preferred image. `boundary_basis` records the factual reason this package is one quote line. `merge_proofs` is always present, including as an empty list when every commercial package has one assembly view.

## Evidence coverage

Evidence is the complete source context for the object, not a shortlist of pages that appear sufficient for a material calculation. For every physical upload page, return exactly one `page_coverage` entry. Put an object ID in `object_ids` whenever that page contains any visual, graphic, textual, layout, title, schedule, detail, plan, section, alternate view, assembly instruction or other source content that relates to that object. A page can belong to several objects. A render or picture is Evidence when it shows the object in another view. Do not omit a page merely because it lacks dimensions, material names, a crop-worthy region or an immediately calculable fact.

Use an empty `object_ids` only when the page contains no content related to any in-scope object. Give a brief factual `evidence_reason` for every page, including excluded pages. The runtime derives `estimation_evidence_pages` from this coverage, so it cannot silently discard an associated page. There is no arbitrary page-count cap.

Do not turn dimensions, materials, pricing or names into extracted object data. You may cite a visible code, unit, dimension, or product-description note minimally in `role_basis` when it establishes the visual role. `boundary_basis` is the persisted decision audit: name the supporting visual groups or physical structure. If it merges separately depicted assemblies, state the specific positive integration that makes them one product. Never use a generic statement such as "one system" or "same sheet". Return schema JSON only.
