# DETECTION V4 - VISUAL REGISTRY

Build the visual representation map and the locked commercial-object registry in one response. First inspect the full pages and enlarged regions, then reconcile the supplied visual-island attention targets, then map visible representations, then decide the commercial objects. Keep these two levels separate in the output, and keep the island attention inventory separate from both.

## Drawing title blocks and visual-island attention

Architectural and fabrication drawings often have a structured title block, usually near the lower-right corner. It describes the document, project, author, sheet or revision. Treat text in this area as document context, not as an object code or product name, unless the drawing explicitly labels it as an item/object code and the same code is visibly anchored to the depicted physical assembly elsewhere.

The input includes a `VISUAL ISLAND ATTENTION MANIFEST` and enlarged crops for its entries. They were generated only from disconnected drawing geometry outside the title-block area. They are not object detections and do not establish quantity. They are mandatory visual questions: each might be a complete product, a second view of a product, a component/detail, or non-product drawing content.

Return one `visual_island_assessments` entry for every manifest island, in manifest order. Give a literal `literal_visual_identity`, choose its classification, and use `related_island_ids` only for actual visual relationships. A project name, sheet title, visual proximity, matching finish, or lack of labels cannot make two islands related.

When an island depicts a separate finished envelope or function, treat it as a `complete_assembly_candidate` unless a specific positive physical relationship proves it is a view or component of another assembly. Different views of one TV console, cabinet or kitchen may be related only when their distinctive silhouette, panel sequence, frame, track, worktop or explicit view relation matches. Never suppress a second finished assembly just because it appears next to the first one on every sheet.

## Visual representations

Each `visual_group` is one visibly distinct depiction that could help a later stage understand an in-scope fabricated product: overview, alternate perspective, elevation, section, detail, module, door leaf, panel, track, cabinet bay, schedule, or assembly fragment. It is not automatically a commercial object, quote line or quantity. One depiction may genuinely support several commercial objects, for example a shared schedule or a sheet showing separately coded products.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal visual `visual_description`, neutral `representation_kind`, and only clearly visible `related_group_ids`. Keep descriptions terse. Empty `related_group_ids` when a relation is not visually clear.

## Commercial registry

Decide complete fabricated products a contractor would quote, fabricate, supply, install, replace or price independently. A visual group may be an overview, alternate view, elevation, section, detail, component, module, panel, door leaf or track. It must not become an object merely because it appears separately.

Merge representations only with positive evidence that they show the same physical assembly: a shared distinctive silhouette and structure, an explicit view relation, a common object code, or a matching unique envelope and panel sequence. A shared page, room title, project, material palette, visual proximity, lack of object codes, or generic furniture scope is never merge evidence.

Before creating the registry, account for every separately depicted complete assembly on overview, plan, elevation or render pages. Map it to one commercial object, or merge it only after identifying the specific physical integration that makes it one assembly, such as a continuous carcass, worktop, frame, track, common mounting structure, or an explicit same-object relation. Adjacent furniture with separate finished envelopes and different functions remains separate even when it appears on every sheet, shares finishes, or is presented together. A one-object `boundary_basis` that covers several complete assemblies must state that positive integration, never merely call them an integrated system.

Different complete envelopes, functions, silhouettes or construction systems are strong independent-product evidence even without an object code. A vertical shelving unit, a track-supported door system and a long storage console separately drawn on one furniture sheet are three objects. Repeated projections remain one object each. Never absorb them into a generic room-furniture assembly.

A kitchen, integrated cabinet wall or shelving wall is one object. Its blocks, modules, panels, fronts, carcasses, profiles, hardware and assembly sheets are construction detail, not objects. Several leaves on one continuous track are one Door system with quantity 1 unless the source establishes separate systems, tracks, deliveries or quote quantities.

`object_id` is ordered `object-001`, `object-002`, and so on. `transport_label` is an exact printed object code when present, otherwise `Object 1`, `Object 2`, and so on. `quantity` is complete physical units, defaulting to 1 when not explicit. `identity_pages` uses physical upload page numbers. `visual_group_ids` lists map groups that support this object. The same group may appear for several objects only when its visible content genuinely covers each of them. A shared page, generic title or visual proximity alone is not sufficient. `visual_identity` states the complete silhouette and views that prove it. `boundary_basis` records the factual reason this is one quote line.

For every object, `visual_island_ids` lists its in-scope manifest islands. Across all objects, every in-scope manifest island must appear exactly once. `island_merge_basis` is a concise factual account of why the listed islands form one physical assembly or why the object has no listed island. When one object contains separate islands on the same page, this field must cite the positive visual evidence that connects them. Do not use title-block or project text as that evidence.

## Evidence coverage

Evidence is the complete source context for the object, not a shortlist of pages that appear sufficient for a material calculation. For every physical upload page, return exactly one `page_coverage` entry. Put an object ID in `object_ids` whenever that page contains any visual, graphic, textual, layout, title, schedule, detail, plan, section, alternate view, assembly instruction or other source content that relates to that object. A page can belong to several objects. A render or picture is Evidence when it shows the object in another view. Do not omit a page merely because it lacks dimensions, material names, a crop-worthy region or an immediately calculable fact.

Use an empty `object_ids` only when the page contains no content related to any in-scope object. Give a brief factual `evidence_reason` for every page, including excluded pages. The runtime derives `estimation_evidence_pages` from this coverage, so it cannot silently discard an associated page. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or names. Return schema JSON only, in this order: `visual_island_assessments`, `visual_groups`, `objects`, `page_coverage`.
