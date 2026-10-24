# DETECTION V5.30 - SOURCE-DEGRADED PAIRWISE PRESERVATION AUDIT

You receive complete rendered pages and a neutral Island map. The complete page
is authoritative. The map is fixed navigation only. Do not add, remove, split
or merge its groups.

Assign one provisional role to every group.

- `assembly_view` is a complete fabricated assembly or an alternate projection.
- `component_detail` is an incomplete fragment. It must name exactly one
  same-page `assembly_view` owner.
- `document_context` is non-technical navigation, title-block, schedule or plan
  content and has no owner.
For `assembly_view` and `document_context`, return `owner_group_id` as an empty
string. It is meaningful only for `component_detail`.

Then return exactly one pair-ledger row for every unordered pair of same-page
technical groups. Technical groups are every `assembly_view` and
`component_detail`; do not exclude a detail from the ledger.

- `same_object`: use only a concrete positive basis, such as explicit author
  relation, alternate projection, matching non-generic structure, compatible
  visible dimensions or direct continuity.
- `different_object`: name a concrete separation: incompatible dimensions,
  distinct finished envelopes, explicit author distinction or physical
  separation. "Different configuration", detailed labeling, material, colour,
  generic frame type, proximity or page position are never a separation basis.
- `inconclusive`: use only when the complete page supplies neither positive
  identity evidence nor a concrete separation.

A `component_detail` may keep its owner only when its exact ledger pair is
`same_object` with either `direct_continuity` or `visible_author_label`.
If that proof is unavailable, use `assembly_view`; do not remove a technical
representation merely because materials, panels, frame style or dimensions look
similar. Runtime derives object partitions from the validated ledger. Return
schema JSON only.
