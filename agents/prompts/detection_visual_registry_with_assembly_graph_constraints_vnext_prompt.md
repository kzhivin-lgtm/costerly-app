## Locked assembly graph constraints

When the input contains `LOCKED ASSEMBLY GRAPH CONSTRAINTS`, they come from a
preceding title-agnostic masked-figure correspondence graph. They are neither
names, quantities nor evidence lists. They constrain, but do not replace, your
full-document commercial-object registry judgment.

`assembly_candidates` are direct positive visual matches. Each candidate ID
must map to exactly one registry object, and each registry object may contain
at most one candidate ID. Do not merge or split candidates.

`must_separate_representation_pairs` are direct negative visual matches. The
two representation IDs in each pair must never occur in the same registry
object. An `insufficient` relationship is intentionally absent from these
constraints. Use the complete drawing package to assign each such uncertain
view to the object it actually represents.

Every supplied representation in `representation_manifest` must occur exactly once across
`graph_representation_ids`. The IDs are spatial navigation keys, not product labels. Preserve
all of the normal commercial-object, quantity and full Evidence page-coverage rules.

The `assembly_candidate_ids` and `graph_representation_ids` fields are required
for every registry object. Return schema JSON only.
