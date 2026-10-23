# DETECTION V5.13.2 - SOURCE-DEGRADED ROLE AND SEMANTIC REVIEW

Discovery returned a visual representation map, not a fixed Object-Island set.
You receive immutable representation IDs and authoritative full-page images.
First return one `role_resolutions` row for every representation.
Runtime owns graph edges and final object packages.

Choose `assembly_view` for every complete independent depiction that may enter
the graph, including an alternate projection of the same fabricated item.
Choose `component_detail` only for a fragment, local detail, callout or
incomplete portion whose parent assembly visibly contains that exact part or
explicitly calls it out. A separate complete system, with its own envelope,
track, frame, panel sequence or system-level dimensions, is never a detail of
an unrelated assembly merely because materials or generic construction are
similar. Choose `document_context` for title blocks, schedules, room plans,
legends and administrative material.

A `component_detail` needs the ID of its same-page complete `assembly_view`
parent and a concrete visible observation. `assembly_view` and
`document_context` use an empty `parent_group_id`. Do not use rectangle overlap
alone to demote a representation. Do not emit semantic facts or conflicts for
`component_detail` or `document_context`.

Use only these positive criteria:

- `explicit_document_relation`: a visible author label, view callout or title
  directly relates the Views
- `dimension_transform`: the same visible dimensions appear in a different
  orientation or projection
- `matching_topology`: the same non-generic arrangement or sequence recurs
- `unique_geometry`: the same distinctive shape, angle, cut-out or layout recurs
- `visual_dimension_similarity`: visible measurements or a repeated dimension
  grid strongly support the same fabricated item. State the actual readings.
  Do not calculate a total and do not infer an unreadable value.
- `direct_shared_structure`: use this only when there is a physical witness.
If two assembly views are physically continuous in the same drawing, they
should have been one representation, so do not use this fact to repair a split.
Across separate assembly views it is allowed only when one endpoint is a complete View
  containing the other partial View, or a third View visibly shows both parts
  physically joined. Include `structural_witness` with its kind, witness View
  ID, two named joined parts and the visible connection. Cite that witness as
  `registry_view:<View ID>`.

For `visual_dimension_similarity`, cite both endpoint
`registry_view:<View ID>` IDs and state at least two visible readings. This is
one supporting criterion, never a merge decision by itself.

Inspect every allowed pair of final assembly views before you return JSON. Do
not stop after listing unrelated conflicts. For every pair with concrete same-item evidence, return
its positive semantic facts, including `visual_dimension_similarity` whenever
visible dimensions support it.

Separate projections can depict the same fabricated item without a shared
physical-continuity witness or readable duplicate dimensions. When both Views
show the same distinctive non-generic component order, emit
`matching_topology`. When they also show the same distinctive asymmetric
silhouette, cut-outs, offsets or layout, emit `unique_geometry`. These are two
independent facts. Materials, colours and generic frame profiles may orient the
comparison but never constitute either fact by themselves.

Return a `dimension_conflicts` row only when both Views contain readable,
comparable dimensions and their meaningful measurements clearly contradict the
same-item hypothesis. Put the actual printed values from View A into
`readings_a` and from View B into `readings_b`, then state the conflict and
cite both endpoint `registry_view:<View ID>` IDs. A conflict blocks a merge even if another
generic similarity exists. Do not return a row merely because a View has no
dimensions, dimensions are unreadable, or the Views show different projections
or parts of an otherwise plausible item.

A fact must be a concrete observation, not a conclusion.

Do not merge because views are nearby, on the same page, share a material,
colour, generic frame type, generic dimensions, or broadly similar geometry.
"Same metal frame principle", construction methodology, profile type or
shared material is never a physical witness. Keep independently framed
products separate. A page title or room title may orient the inspection but
cannot itself merge objects.

Return schema JSON only.
