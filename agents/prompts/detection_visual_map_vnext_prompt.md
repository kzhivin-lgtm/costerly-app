# DETECTION V4 - VISUAL REPRESENTATION MAP

Return a map of fabrication-relevant visual representations only. This is not a commercial-object registry, quote, quantity decision, name, or evidence package.

Inspect the full pages and enlarged regions. Record each visibly distinct depiction that could help a later stage understand an in-scope fabricated product: overview, alternate perspective, elevation, section, detail, module, door leaf, panel, track, cabinet bay, or assembly fragment. Do not decide whether any depiction is an independent product, part of another product, or a quote line. Do not infer quantity.

Each `visual_group` is one representation, not one object. Give it a stable ordered `group_id`, physical `page_number`, a short visual `location_hint`, a literal visual `visual_description`, a neutral `representation_kind`, and a `representation_scope`. Use `product_representation` for any physical drawing, plan, elevation, section, panel, profile, module or detail that could contribute to product identity. Use `document_context` only for title blocks, sheet layout, legend, schedule or similar navigation. This scope does not decide whether a depiction is complete, independent, a component, or owned by a commercial object. A group records only that one visible depiction. Do not create a graph between groups; commercial-object assembly is decided separately from the full visual evidence.

The map is navigation evidence only. It cannot create, split, merge, name, count, price, or reject commercial objects. Return schema JSON only.
