# DETECTION V4 - PROOF GRAPH REGISTRY

Build the visual representation map and commercial-object registry in one response. The output has a strict causal order:

1. identify object-specific visual groups,
2. state only evidence-backed pairwise merge proofs,
3. treat each connected proof component as exactly one commercial object,
4. describe that component and its complete page Evidence.

Do not declare an object owner first and add proofs afterwards. A group pair belongs to one object only when it is connected by an explicit proof edge. An unlinked group is a valid one-group commercial-object component.

## 1. Visual groups

Each `visual_group` is one visibly distinct, object-specific source depiction that can help Estimation: overview, alternate perspective, elevation, object plan, section, detail, module, door leaf, panel, track, cabinet bay or assembly fragment. It is not automatically a quote line or quantity.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal visual `visual_description`, and neutral `representation_kind`. It records only one visible depiction. Do not assign any object IDs or owners to a group.

Do not create a group for the cover/title page, title block itself, generic floor plan, room layout, electrical, plumbing or lighting plan, legend, administrative text, generic schedule or navigation diagram. Detection may use these internally for metadata, sheet codes and orientation, but they are not Estimation Evidence. Use `object_plan` only when a plan contains direct construction, identity or fabrication information for a specific in-scope object. `floor_plan` means generic non-object context and is discarded. A repeated grid, dimension string, repeated bays, slats, shelves or panel divisions is not a table by itself.

## 2. Proof graph

Start with every visual group separate. Emit a `merge_proofs` edge only when the two groups are positive evidence of the same independently quoted product, or one is a proved detail of that product. There is no edge for separate products. Do not use visual adjacency, same room, same page, colour, material, project, or an L-shaped layout as an edge.

Resolve a relation in this priority order:

1. `explicit_document_relation`: the same code, callout, view reference, axis or label.
2. `dimension_transform`: dimensions agree after a change of axes or describe compatible portions of one assembly.
3. `matching_topology`: matching order and count of bays, doors, supports, carcasses, frames, appliances, joints or structural elements.
4. `unique_geometry`: repeated cut-outs, handles, posts, appliance locations, turning parts, mounting points, panel sequence or distinctive frame geometry.
5. `direct_shared_structure`: a visible common frame, track, carcass, joint or other physical connection. It may support an edge, never establish one alone.

Secondary signals, including proximity, room name, colour, material and same-sheet location, can reinforce a proven relation but cannot create it. A change of projection can make one item look unlike itself, so whole-silhouette similarity is not required.

An explicit same code, callout or view reference can prove one edge on its own. Without it, an edge needs at least two independent facts and at least one identity-level fact: `dimension_transform`, `matching_topology`, or `unique_geometry`. Two dimension facts are independent only when they cite different dimensions or axes. Every proof carries `evidence_facts`; every fact has its own pages and concrete observation. `commercial_inseparability` states the concise factual reason the linked views are one quote line.

The graph must be a forest. For each connected component with N groups, return exactly N-1 edges. Never return a self-link, duplicate edge, placeholder or empty proof. Use `same_object_view` for two representations of the same product, `object_detail` for a detail, section or module that belongs to it. A singleton group contributes no edge.

Test commercial separability, not merely visual closeness. Different finished envelopes, principal functions or primary dimensions are affirmative evidence of separate objects. A shared worktop, touching side panels or apparent continuous carcass is only a candidate connection until the source proves commercial inseparability. Adjacent furniture remains separate unless a proof edge overcomes that evidence. Conversely, a kitchen, integrated cabinet wall, shelving wall or one continuous door-track system remains one component when the source proves one integrated joinery envelope.

## 3. Component registry

After the proof graph is complete, each connected component becomes exactly one object row. Its `component_anchor_group_id` must be one group in that component and must be used consistently by the matching page coverage. Do not return `object_id` or `visual_group_ids`: runtime derives the full component from the graph, selects its canonical ordering, and assigns `object-001`, `object-002`, and so on.

For every component, return one row with its anchor, exact printed `transport_label` when present, otherwise a neutral source label, `quantity`, `quantity_explicit`, `identity_pages`, `visual_identity`, and `boundary_basis`. Quantity defaults to 1 when the document does not establish another quantity. `visual_identity` describes the complete physical product across its views. `boundary_basis` states the factual reason that this proof component is one quote line. Do not use generic phrases such as "one system" or "same sheet".

If a sheet carries one shared literal code but depicts several separate finished assemblies, they remain separate components unless proof edges establish integration. If there are no child codes, preserve the literal base only as source context. Do not merge merely because the sheet code is shared.

## 4. Evidence coverage

Evidence is complete object-specific source context, not a shortlist of pages that appear sufficient for a material calculation. Return exactly one `page_coverage` entry for every physical upload page. Use `component_anchor_group_ids`, not object IDs. Include a component anchor whenever that page contains a visual group or other direct object-specific construction, identity, detail, plan, section, alternate view or assembly instruction for that component. A page can support several components.

Use an empty anchor list for a cover/title page, generic floor plan, room layout, electrical, plumbing, lighting, legend or another non-object-specific page. Those pages can guide Detection but are never Evidence for Estimation. Give every page a brief factual `evidence_reason`. The runtime derives each object's `estimation_evidence_pages`, so it cannot silently discard a qualifying page. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or final user-facing names. Return schema JSON only.
