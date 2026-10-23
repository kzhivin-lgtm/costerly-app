# DETECTION V5.20 - SOURCE-DEGRADED FULL-PAGE VISUAL REGISTRY

The input contains complete rendered pages and an advisory visual representation
map. The map is navigation only. It may split one depiction, omit document
context or include details. Do not treat it as an object set.

Return three things: `continuity_groups`, one final role for every mapped
representation, then one complete partition of the final assembly views into
fabricated objects. The runtime validates coverage and ownership. It does not
reinterpret the page.

## Continuity consolidation

First inspect the full rendered page for a false split in the advisory map.
`continuity_groups` is an optional list. Add one row only when two or more
mapped representations on the same page are visibly one physically continuous
depiction: their actual drawn body, rail, panel, support or frame continues
into the other with no independent drawing boundary. State the concrete joined
parts and the visible connection.

This is an Island-segmentation decision, before roles and commercial-object
membership. It is not a same-object relation between separate projections.
Do not declare continuity from touching or overlapping rectangles, proximity,
similar construction, material, colour, a shared page or a shared title. A
blank gap, a separate finished envelope, or merely related components means
separate representations. When a continuous depiction bends, branches or has
a non-rectangular silhouette, it is still one representation.

The supplied segmentation-review candidates are advisory only. Inspect the
pixels and return `[]` when none has a real physical-contour continuation.

## Roles

Use exactly one role for every representation:

- `assembly_view`: a complete independent depiction, including an alternate
  projection of the same fabricated item.
- `component_detail`: a fragment, callout, leaf, panel, track, section,
  hardware, or incomplete portion. It is never an object by itself.
- `document_context`: title block, schedule, room plan, legend or
  administrative material.

Determine the role from the complete page. A complete system with its own
envelope, track, frame, panel sequence or system-level dimensions is an
`assembly_view`, even when it contains components. Do not classify a complete
system as a detail of another assembly because they share a page, material,
colour or generic construction. Do not create a role from a rectangle alone.

An `assembly_view` is a candidate for identity resolution, not a declaration
that it is a new independent product. A `component_detail` is supporting
evidence only. It cannot appear in a partition, even when it visibly belongs
to an assembly. A group named in `continuity_groups` is not an independent
component: its fragments become one effective representation before this role
is used for partitioning. After choosing roles, treat that decision as binding:
the union of all partition `group_ids` must be exactly the set of
`assembly_view` IDs, no more and no less.

## Object partitions

Decide fabricated products a contractor would quote, fabricate, supply or
replace independently. Consider all `assembly_view` representations together
before partitioning. For every assembly view decide whether it is a new
product or another projection of a product already represented. Do not create
one partition per `assembly_view` by default. A changed projection can make
the same item look unlike itself, so whole-silhouette similarity is not
required.

Each partition is one fabricated object. Account for every assembly view once,
and only once. A single assembly view needs a `complete_physical_envelope`
basis. A multi-view object needs a connected set of concrete positive bases,
considered in this priority order:

- `alternate_projection`: another depiction of the same finished assembly.
- `visible_author_label`: an explicit same-object view relation or code.
- `matching_unique_structure`: the same non-generic bay order, supports,
  track, panel sequence, cut-out, mounting points or distinctive frame layout.
- `compatible_dimensions`: visible measurements agree after changed axes or
  describe compatible portions of one assembly.
- `direct_continuity`: one drawing visibly shows the views or parts physically
  connected.

When positive identity evidence exists, place every corresponding
`assembly_view` in one partition. For alternate projections, use matching
construction topology, compatible dimension portions, repeated unique
features, or an explicit relation. A shared page, room title, project,
material palette, generic frame type, colour, proximity, similar size or lack
of codes can only reinforce a separately established relation. They never
create one.

Different finished envelopes, functions, silhouettes or construction systems
are strong independent-product evidence. Adjacent furniture with separate
finished envelopes remains separate even if presented together. Conversely, a
continuous carcass, worktop, frame, track, common mounting structure or
explicit same-object relation can establish a single object. State the
concrete observation in each basis. Do not output names, quantities, prices or
dimensions beyond readings needed to explain a basis. Return schema JSON only.
