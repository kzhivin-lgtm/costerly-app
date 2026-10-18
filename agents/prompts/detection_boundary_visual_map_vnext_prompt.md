# DETECTION V4 - BOUNDARY-SENSITIVE VISUAL MAP

Build a complete visual representation map for a later boundary resolver. This is not a commercial-object registry, quote, quantity decision, name, or evidence package.

Inspect every full page and enlarged region. Record each visibly distinct depiction relevant to an in-scope fabricated product. A depiction may be an overview, alternate perspective, elevation, plan, section, detail, module, door leaf, panel, track, cabinet bay, schedule, or assembly fragment.

Each `visual_group` records one visible depiction only. Give it an ordered `group_id`, physical `page_number`, short `location_hint`, literal `visual_description`, neutral `representation_kind`, and exactly one `commercial_role`:

- `assembly_view`: a complete finished envelope that can take part in product-identity resolution. It is a candidate view, not an independent product claim.
- `component_detail`: an isolated component, cutout, section, leaf, panel, track, module, hardware or construction fragment.
- `document_context`: title block, legend, schedule, layout, room label or other document context.

Do not decide whether assembly views are the same or different physical products. Do not create correspondence groups, commercial objects, quantities, names, or page ownership. In particular, document context and component details cannot by themselves create an object. A separately depicted finished envelope remains an `assembly_view` even when OCR supplies no code.

Return schema JSON only.
