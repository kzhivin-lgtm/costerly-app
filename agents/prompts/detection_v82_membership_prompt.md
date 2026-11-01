# Detection V8.2: Membership

You receive immutable Object Evidence views and their own crops. Return only
same-object pair links. Do not create objects, singleton rows, exclusions,
render decisions, package labels, or new islands. Absence of a link means no
merge.

For two technical views, return a link only with two independent concrete
proofs selected from: `matching_topology`, `unique_geometry`,
`direct_shared_structure`, `dimension_equality`, or
`explicit_document_relation`. Common material, approximate shape, page order,
proximity and title blocks are never proof.

For exactly one `presentation_render` and one technical view, one concrete
`matching_topology` or `unique_geometry` proof is sufficient. Name the
distinctive configuration visible in both. A render/photo cannot link to a
render/photo and cannot create an object by itself.

Every returned endpoint must be one of the fixed view IDs. Each observation
must state the visible or explicit relation, not merely say that the views are
related. Return schema JSON only.
