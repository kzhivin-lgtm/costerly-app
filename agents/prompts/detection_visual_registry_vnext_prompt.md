# DETECTION V4 - VISUAL REGISTRY

Build the visual representation map and the locked commercial-object registry in one response. First inspect the full pages and enlarged regions, then map visible representations, then decide the commercial objects. Keep these two levels separate in the output.

## Visual representations

Each `visual_group` is one visibly distinct depiction that could help a later stage understand an in-scope fabricated product: overview, alternate perspective, elevation, section, detail, module, door leaf, panel, track, cabinet bay, schedule, or assembly fragment. It is not automatically a commercial object, quote line or quantity. A shared schedule, title block, layout or multi-object context may remain an unassigned navigation group; it belongs in `page_coverage`, not in several object boundary lists.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal visual `visual_description`, neutral `representation_kind`, and only clearly visible `related_group_ids`. Keep descriptions terse. Empty `related_group_ids` when a relation is not visually clear.

## Commercial registry

Decide complete fabricated products a contractor would quote, fabricate, supply, install, replace or price independently. A visual group may be an overview, alternate view, elevation, section, detail, component, module, panel, door leaf or track. It must not become an object merely because it appears separately.

Merge representations only with positive evidence that they show the same physical assembly: a shared distinctive silhouette and structure, an explicit view relation, a common object code, or a matching unique envelope and panel sequence. A shared page, room title, project, material palette, visual proximity, lack of object codes, or generic furniture scope is never merge evidence.

Before creating the registry, account for every separately depicted complete assembly on overview, plan, elevation or render pages. Map it to one commercial object, or merge it only after identifying the specific physical integration that makes it one assembly, such as a continuous carcass, worktop, frame, track, common mounting structure, or an explicit same-object relation. Adjacent furniture with separate finished envelopes and different functions remains separate even when it appears on every sheet, shares finishes, or is presented together. A one-object `boundary_basis` that covers several complete assemblies must state that positive integration, never merely call them an integrated system.

Different complete envelopes, functions, silhouettes or construction systems are strong independent-product evidence even without an object code. A vertical shelving unit, a track-supported door system and a long storage console separately drawn on one furniture sheet are three objects. Repeated projections remain one object each. Never absorb them into a generic room-furniture assembly.

A kitchen, integrated cabinet wall or shelving wall is one object. Its blocks, modules, panels, fronts, carcasses, profiles, hardware and assembly sheets are construction detail, not objects. Several leaves on one continuous track are one Door system with quantity 1 unless the source establishes separate systems, tracks, deliveries or quote quantities.

`object_id` is ordered `object-001`, `object-002`, and so on. `transport_label` is an exact printed object code when present, otherwise `Object 1`, `Object 2`, and so on. `quantity` is complete physical units, defaulting to 1 when not explicit. `identity_pages` uses physical upload page numbers. `visual_group_ids` lists the exclusive groups that prove this object's commercial boundary. A group has exactly one commercial-object owner and must never appear in more than one object's `visual_group_ids`. If a shared page, schedule, title block or layout relates to several objects, assign every relevant object through `page_coverage` while leaving that context group unassigned. When one sheet visibly contains several complete assemblies, map them as separate groups before assigning ownership. `visual_identity` states the complete silhouette and views that prove it. `boundary_basis` records the factual reason this is one quote line.

## Evidence coverage

Evidence is the complete source context for the object, not a shortlist of pages that appear sufficient for a material calculation. For every physical upload page, return exactly one `page_coverage` entry. Put an object ID in `object_ids` whenever that page contains any visual, graphic, textual, layout, title, schedule, detail, plan, section, alternate view, assembly instruction or other source content that relates to that object. A page can belong to several objects. A render or picture is Evidence when it shows the object in another view. Do not omit a page merely because it lacks dimensions, material names, a crop-worthy region or an immediately calculable fact.

Use an empty `object_ids` only when the page contains no content related to any in-scope object. Give a brief factual `evidence_reason` for every page, including excluded pages. The runtime derives `estimation_evidence_pages` from this coverage, so it cannot silently discard an associated page. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or names. `boundary_basis` is the persisted decision audit: name the supporting visual groups or physical structure. If it merges separately depicted assemblies, state the specific positive integration that makes them one product. Never use a generic statement such as "one system" or "same sheet". Return schema JSON only.
