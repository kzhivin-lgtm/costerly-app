# DETECTION V5.32.1 - SOURCE-DEGRADED PAIRWISE STRUCTURAL ADMISSION AUDIT

You receive complete rendered pages and a neutral Island map. The complete page
is authoritative. The map is fixed navigation only. Do not add, remove, split
or merge its groups.

Assign one provisional role to every group.

- `assembly_view` is a complete fabricated assembly, a finished separable
  subassembly, or a complete alternate projection of one.
- `component_detail` is only an incomplete fragment: a cut-away, section,
  isolated construction detail or partial depiction that cannot itself be
  fabricated or supplied as a finished unit. It must name exactly one same-page
  `assembly_view` owner.
- `document_context` is non-technical navigation, title-block, schedule or plan
  content and has no owner.
For `assembly_view` and `document_context`, return `owner_group_id` as an empty
string. It is meaningful only for `component_detail`.

Do not call a finished door or door system, panel unit, shelf unit, frame, or
other separable fabrication `component_detail` merely because it has a related
material, panel, frame or plausible place in another assembly. Functional
proximity, shared material or a plausible installation relationship are not
ownership evidence. When a complete technical Island could be fabricated,
supplied or quoted independently, retain it as `assembly_view`. An owner claim
is retained in the audit, but runtime will not use it to remove the Island
unless it passes the same admission required for a graph edge.

Then return exactly one pair-ledger row for every unordered pair of same-page
technical groups. Technical groups are every `assembly_view` and
`component_detail`; do not exclude a detail from the ledger.

For every `same_object` row, return exactly two or exactly three
`identity_witnesses` of different types. One witness is never sufficient.
Each witness must state what is visibly shared by the two complete depictions.
Use only these types:

- `finished_envelope`: same whole outline, proportion, silhouette or continuous
  top-level envelope.
- `internal_layout`: same non-generic ordered or asymmetric arrangement of
  compartments, bays, openings, panels or end modules.
- `continuous_structure`: same continuous base, top, carcass or visible joining
  structure.
- `distinctive_dimension`: a matching visible, non-generic dimension.
- `visible_author_label` or `direct_continuity`: an explicit drawing relation.

`alternate_projection` is allowed only for two complete `assembly_view`s. It
must include `finished_envelope` plus one other independent witness.
`matching_unique_structure` must include `internal_layout` plus one other
independent witness. A material, colour, wood grain, generic metal frame,
proximity or page position is never an identity witness by itself.

- `same_object`: use only a concrete positive structural identity. A complete
  assembly cannot become a detail just because it shares a material, panel or
  frame principle with another Island.
- `different_object`: name a concrete separation: incompatible dimensions,
  distinct finished envelopes, explicit author distinction or physical
  separation. "Different configuration", detailed labeling, material, colour,
  generic frame type, proximity or page position are never a separation basis.
- `inconclusive`: use only when the complete page supplies neither the required
  positive identity witnesses nor a concrete separation. Return an empty
  `identity_witnesses` array for this and every non-positive row.

An unlabelled `direct_continuity` claim cannot remove a technical Island from
commercial object detection. Runtime derives object partitions from the
validated ledger. Return schema JSON only.
