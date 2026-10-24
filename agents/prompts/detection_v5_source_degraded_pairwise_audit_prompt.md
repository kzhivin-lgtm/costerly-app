# DETECTION V5.29 - SOURCE-DEGRADED PAIRWISE FULL-PAGE AUDIT

You receive complete rendered pages and a neutral Island map. The page is
authoritative. The map is fixed navigation only, not an object decision. Do
not add, remove, split or merge its groups.

First assign exactly one role to every group.

- `assembly_view` is a complete fabricated assembly or an alternate projection.
- `component_detail` is an incomplete fragment and must name exactly one
  same-page `assembly_view` owner with a concrete visible relationship.
- `document_context` has no owner and never appears in an object partition.

Then return exactly one pair-ledger row for every unordered pair of
same-page `assembly_view` IDs. Do not skip a pair because it looks unrelated.

- `same_object`: use only a concrete positive basis, such as explicit author
  relation, alternate projection, matching non-generic structure, compatible
  visible dimensions or direct continuity.
- `different_object`: name a concrete separation: incompatible dimensions,
  distinct finished envelopes, explicit author distinction or physical
  separation. "Different configuration", detailed labeling, material, colour,
  generic frame type, proximity or page position are never a separation basis.
- `inconclusive`: use only when the complete page supplies neither positive
  identity evidence nor a concrete separation.

Finally partition assembly views. A partition may connect views only through
`same_object` ledger rows. Every assembly view appears once. Details and
context never appear in a partition. Return schema JSON only.
