# DETECTION V4 - NEUTRAL VISUAL REGISTRY

Build the visual representation map and the locked commercial-object registry in one response. Inspect the full pages and enlarged regions first. Then map visible representations, resolve commercial-object boundaries, prove every multi-view merge, and account for all Evidence pages. Keep representation mapping separate from commercial-boundary resolution.

## 1. Neutral visual representations

Each `visual_group` is one visibly distinct depiction: overview, plan, elevation, section, profile, perspective, detail, module, leaf, panel, track, cabinet bay, schedule, layout or assembly fragment. It is not automatically a commercial object, quote line, quantity, complete assembly, or component.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal `visual_description`, neutral `representation_kind`, and `representation_scope`.

`representation_scope` has only two meanings. `product_representation` means pixels depict some physical part, view, geometry, or configuration that can contribute to a fabricated product's identity. It includes a plan, elevation, section, profile, panel grid, narrow moulding, assembly fragment, module or detail. It does not declare a separate product, a complete envelope, or an owned assembly view. `document_context` means a title block, drawing frame, legend, schedule, note, sheet layout or other document navigation. It never supports an object's `visual_group_ids`.

Do not decide commercial ownership, completeness, independence, or component status while mapping a visual group. In particular, do not pre-classify a product representation as a `component_detail` merely because it is a section, a profile, a panel, or does not itself show the whole envelope. A finished product can be identifiable only from several such coordinated projections.

## 2. Commercial registry

Decide complete fabricated products a contractor would quote, fabricate, supply, install, replace, or price independently. Resolve objects from all `product_representation` groups together. Never create an object from `document_context`.

For every product representation, decide whether it supports a new product or another projection of a product already represented. Do not create one object per visual group by default. A change of projection may make the same product look unlike itself, so whole-silhouette similarity is not required. Conversely, a visually isolated depiction is not proof that it is an independent commercial product. Resolve the relation using the following evidence, in priority order:

1. Explicit document relation: the same code, callout, view reference, axis or label.
2. Matching construction topology: the order and count of bays, doors, supports, carcasses, frames, appliances, joints and other structural elements.
3. Dimensions that agree after a change of axes or depict compatible portions of one assembly.
4. Repeated unique geometric features: cut-outs, handles, posts, appliance locations, turning parts, mounting points, panel sequence or distinctive frame geometry.
5. Secondary supporting signals only: being on one sheet, colour, material, visual proximity and room name. These may reinforce a relation already supported above, but never establish it alone.

When the evidence establishes the same product, put every corresponding product representation in one object's `visual_group_ids` and state the cross-view evidence in `boundary_basis`. A referenced group becomes an `assembly_view` only after this registry is accepted. An unreferenced product representation remains supporting detail. This derived role must not be guessed earlier in the visual map. When positive identity evidence is absent, do not invent a merge solely because the views look stylistically related.

## 3. Pairwise merge-proof procedure

Start from separate candidate commercial assemblies. Before grouping two product representations under one owner, apply this comparison to that pair. Different finished envelopes, principal functions, or primary dimensions are affirmative evidence of separate commercial objects. A pair can merge only when the source overcomes that evidence.

Test commercial separability, not merely visual adjacency. Ask whether each finished assembly could reasonably be fabricated, transported, installed, replaced, or priced separately. A shared page, room title, project, material palette, visual proximity, L-shaped placement, lack of object codes, or generic furniture scope never proves a merge. A shared worktop, touching side panels, or an apparent continuous carcass is only a candidate physical connection. It does not prove one commercial object unless the drawing also shows why the two parts are commercially inseparable.

An explicit same code, callout, or view reference can prove identity on its own. Without one, a merge needs at least two independent evidence types and at least one identity-level comparison: matching construction topology, dimensions that agree after a change of axes, or repeated unique geometry. Direct shared structure may support a merge but cannot be its only evidence. Never infer a shared carcass or continuous construction from adjacency, an L-shaped layout, or matching finishes.

A recognized kitchen, integrated cabinet wall, shelving wall, or one continuous door-track system may remain one commercial object when the visual evidence establishes one integrated joinery envelope. Its modules, appliances, panels, fronts, and details are not separate objects. A worktop alone must not absorb adjacent non-kitchen furniture into that object.

`merge_proofs` is a compact flat audit, not a second analysis stage or an all-pairs graph. For every object with N `visual_group_ids`, return exactly N-1 proofs which connect those representations. Return no proof for a one-view object. Each proof contains its two group IDs, source pages, a concrete observed fact, controlled `evidence_types`, and the observed reason the parts are commercially inseparable. The group IDs may be linked in any order. Do not use generic statements such as "one system", "same room", or "continuous L-shape" as the observed fact or inseparability reason.

This rule also applies when no one depiction shows a whole envelope. For example, a labelled item may be represented by a plan/context view, a thin profile and a panel grid. If topology, dimensions, code or unique geometry establish one fabricated item, assign all three product representations to that object and provide two connecting proofs. If that evidence does not establish one item, keep them separate or unassigned. Never suppress the item solely because its views look detail-like in isolation.

## 4. Boundary and quantity rules

Before creating the registry, account for every separately depicted complete assembly on overview, plan, elevation or render pages. Map it to one commercial object, or merge it only after its pairwise proof clears the commercial-separability test. Adjacent furniture with separate finished envelopes and different functions remains separate even when it appears on every sheet, shares finishes, touches, or is presented together. A one-object `boundary_basis` that covers several complete assemblies must state the proof-backed integration, never merely call them an integrated system.

Different complete envelopes, functions, silhouettes or construction systems are strong independent-product evidence even without an object code. A vertical shelving unit, a track-supported door system and a long storage console separately drawn on one furniture sheet are three objects. Repeated projections remain one object each. Never absorb them into a generic room-furniture assembly.

A kitchen, integrated cabinet wall or shelving wall is one object. Its blocks, modules, panels, fronts, carcasses, profiles, hardware and assembly sheets are construction detail, not objects. Several leaves on one continuous track are one Door system with quantity 1 unless the source establishes separate systems, tracks, deliveries or quote quantities.

`object_id` is ordered `object-001`, `object-002`, and so on. `transport_label` is an exact printed object code when present, otherwise `Object 1`, `Object 2`, and so on. `quantity` is complete physical units, defaulting to 1 when not explicit. `identity_pages` uses physical upload page numbers. `visual_group_ids` lists the product representations that prove this object's commercial boundary. A group has exactly one commercial-object owner and must never appear in more than one object's `visual_group_ids`. A `document_context` must remain unassigned. If a shared page, schedule, title block or layout relates to several objects, assign every relevant object through `page_coverage` while leaving that context group unassigned. `visual_identity` states the complete physical product and its views, not one preferred image. `boundary_basis` records the factual reason this is one quote line. `merge_proofs` is always present, including as an empty list when every object has one representation.

## 5. Evidence coverage

Evidence is the complete source context for the object, not a shortlist of pages that appear sufficient for a material calculation. For every physical upload page, return exactly one `page_coverage` entry. Put an object ID in `object_ids` whenever that page contains any visual, graphic, textual, layout, title, schedule, detail, plan, section, alternate view, assembly instruction or other source content that relates to that object. A page can belong to several objects. A render or picture is Evidence when it shows the object in another view. Do not omit a page merely because it lacks dimensions, material names, a crop-worthy region or an immediately calculable fact.

Use an empty `object_ids` only when the page contains no content related to any in-scope object. Give a brief factual `evidence_reason` for every page, including excluded pages. The runtime derives `estimation_evidence_pages` from this coverage, so it cannot silently discard an associated page. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or names. `boundary_basis` is the persisted decision audit: name the supporting visual groups or physical structure. If it merges separately depicted assemblies, state the specific positive integration that makes them one product. Never use a generic statement such as "one system" or "same sheet". Return schema JSON only.
