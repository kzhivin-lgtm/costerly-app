# DETECTION V4 - VISUAL REGISTRY

Build the visual representation map, complete-assembly island ledger, and locked commercial-object registry in one response. First inspect the full pages and enlarged regions, then map visible representations, then record complete-assembly islands, then decide the commercial objects. Keep these three levels separate in the output.

## Visual representations

Each `visual_group` is one visibly distinct depiction that could help a later stage understand an in-scope fabricated product: overview, alternate perspective, elevation, section, detail, module, door leaf, panel, track, cabinet bay, schedule, or assembly fragment. It is not automatically a commercial object, quote line or quantity. One depiction may genuinely support several commercial objects, for example a shared schedule or a sheet showing separately coded products.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal visual `visual_description`, neutral `representation_kind`, and only clearly visible `related_group_ids`. Keep descriptions terse. Empty `related_group_ids` when a relation is not visually clear.

## Complete-assembly islands

After the visual map, return `complete_assembly_islands`. An island is one visibly bounded, non-touching depiction of a complete fabricated assembly on one page. Each island references exactly one `visual_group_id`. Repeated views on another page remain separate islands here, even if they later prove to be views of one commercial object.

Create an island for every separately depicted complete assembly, including an unlabelled one. A page with two separated complete-assembly islands must therefore produce two island rows. Do not omit an island because it is adjacent to another product, has a similar finish, lacks a code, or may later be merged. Do not create islands for a clearly partial component, detail, schedule, or hardware-only depiction. `completion_basis` must state only the visible complete-envelope or assembly fact that makes it a candidate.

## Commercial registry

Decide complete fabricated products a contractor would quote, fabricate, supply, install, replace or price independently. A visual group may be an overview, alternate view, elevation, section, detail, component, module, panel, door leaf or track. It must not become an object merely because it appears separately.

Merge representations only with positive evidence that they show the same physical assembly: a shared distinctive silhouette and structure, an explicit view relation, a common object code, or a matching unique envelope and panel sequence. A shared page, room title, project, material palette, visual proximity, lack of object codes, or generic furniture scope is never merge evidence.

Before creating the registry, account for every `complete_assembly_island`. Treat every island as an independent-product candidate, even when it appears only once. Repetition of the same separated islands on other pages corroborates that candidate; it is not required to account for it.

Every island must appear in exactly one object's `complete_assembly_island_ids`. When one object contains several islands, `island_merge_basis` and `boundary_basis` must identify the exact observable evidence that makes them views or fragments of one physical assembly. Only the latter permits a merge. The evidence may be a matching distinctive silhouette and panel sequence, an explicit view relation, a common code, or visible continuous carcass, worktop, frame, track or mounting structure. Never invent an integrated system, continuous structure, shared mounting, or coordinated assembly merely to justify a merge.

Adjacent furniture with separate finished envelopes and different functions remains separate even when it appears on every sheet, shares finishes, or is presented together. Lack of a label is not merge evidence. Do not treat a separate island as a component only because it is adjacent to another product or the source is ambiguous.

Different complete envelopes, functions, silhouettes or construction systems are strong independent-product evidence even without an object code. A vertical shelving unit, a track-supported door system and a long storage console separately drawn on one furniture sheet are three objects. Repeated projections remain one object each. Never absorb them into a generic room-furniture assembly.

A kitchen, integrated cabinet wall or shelving wall is one object. Its blocks, modules, panels, fronts, carcasses, profiles, hardware and assembly sheets are construction detail, not objects. Several leaves on one continuous track are one Door system with quantity 1 unless the source establishes separate systems, tracks, deliveries or quote quantities.

`object_id` is ordered `object-001`, `object-002`, and so on. `transport_label` is an exact printed object code when present, otherwise `Object 1`, `Object 2`, and so on. `quantity` is complete physical units, defaulting to 1 when not explicit. `identity_pages` uses physical upload page numbers. `visual_group_ids` lists map groups that support this object. The same group may appear for several objects only when its visible content genuinely covers each of them. A shared page, generic title or visual proximity alone is not sufficient. `visual_identity` states the complete silhouette and views that prove it. `boundary_basis` records the factual reason this is one quote line.

## Evidence coverage

Evidence is the complete source context for the object, not a shortlist of pages that appear sufficient for a material calculation. For every physical upload page, return exactly one `page_coverage` entry. Put an object ID in `object_ids` whenever that page contains any visual, graphic, textual, layout, title, schedule, detail, plan, section, alternate view, assembly instruction or other source content that relates to that object. A page can belong to several objects. A render or picture is Evidence when it shows the object in another view. Do not omit a page merely because it lacks dimensions, material names, a crop-worthy region or an immediately calculable fact.

Use an empty `object_ids` only when the page contains no content related to any in-scope object. Give a brief factual `evidence_reason` for every page, including excluded pages. The runtime derives `estimation_evidence_pages` from this coverage, so it cannot silently discard an associated page. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or names. Return schema JSON only.
