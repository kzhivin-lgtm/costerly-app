# Detection V8.2: Membership

You receive immutable Object Evidence views and their own crops. Return only
same-object pair links. Do not create objects, singleton rows, exclusions,
render decisions, package labels, or new islands. Absence of a link means no
merge.

The first image is a labelled board of the entire evidence set. Inspect it
globally before reviewing individual crops. A PDF page boundary, crop order,
proximity, or adjacency is never a grouping boundary. Deliberately compare
matching configurations across pages, including every presentation render
against compatible technical views.

The fixed `REQUIRED SAME-PAGE PAIRS` list is exhaustive. Return exactly one
decision for every listed pair, even when evidence is insufficient. Use
`same_object` only with the positive proof rules below. Use
`different_or_insufficient` with no proofs when the pair must not merge. Never
omit, duplicate, add, or substitute a listed pair. `cross_page_links` contains
only additional positive links whose endpoints are on different PDF pages.

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
