# DETECTION V5.15 - SOURCE-DEGRADED ONE-SHOT VISUAL REGISTRY

The document has no usable coordinate-bearing PDF or OCR evidence. Inspect the
complete rendered pages visually. In one response, first build a neutral map of
visible representations, then decide their roles and the final fabricated
objects. Keep those three levels separate.

## Visual representation map

Each `visual_group` is one visibly distinct depiction that can help identify an
in-scope fabricated product: overview, alternate projection, elevation,
section, detail, module, leaf, panel, track, bay, schedule or assembly
fragment. It is not automatically an object, quote line or quantity. Record
only that depiction with a stable ID, page, literal description, kind and
padded rectangular transport bbox in the stated rendered-page pixel frame.

Map a continuous physical depiction as one group even if it bends, branches or
contains annotations. Its bbox is merely a padded transport envelope, never a
claim that every rectangle is an independent item. Titles, layouts and
schedules may be mapped as context. Return exactly one `page_coverage` entry
for every supplied page and account for every mapped ID there.

## Final roles

Choose exactly one role for every mapped group:

- `assembly_view`: enough of a complete finished assembly to take part in
  object-identity resolution. It is a candidate view, not automatically a new
  object.
- `component_detail`: a fragment, callout, leaf, panel, track, close-up,
  section, hardware or incomplete portion. It supports an assembly but never
  appears in a partition.
- `document_context`: a title block, schedule, room plan, legend or
  administrative context. It never appears in a partition.

After role assignment, it is binding. The union of partition `group_ids` must
be exactly the set of `assembly_view` IDs, once each. No component or context
may appear in a partition.

## Exclusive object partitions

Each partition is one product a contractor would quote, fabricate, supply or
replace independently. Before writing a partition, resolve every assembly view
globally: decide whether it is a new product or another projection of an
already represented product. Do not create one partition per `assembly_view`
by default. A changed projection can make the same item look unlike itself, so
whole-silhouette similarity is not required.

For a singleton use `complete_physical_envelope`. For a multi-view partition,
give a connected set of concrete positive bases. Evidence priority is:

1. `visible_author_label`: the same code, callout, view reference or axis.
2. `matching_unique_structure`: matching non-generic ordered bays, supports,
   doors, tracks, joints, mounting points, cut-outs or distinctive frame layout.
3. `compatible_dimensions`: visible values agree after a changed axis or
   describe compatible portions of one finished assembly.
4. `alternate_projection`: a second depiction of the same completed envelope.
5. `direct_continuity`: one drawing visibly shows the portions physically
   connected.

Different finished envelopes, functions, silhouettes or construction systems
are strong independent-product evidence. A continuous carcass, worktop, frame,
track, common mounting structure or explicit same-object relation can establish
one object. Shared page, room title, project, material palette, generic frame
type, colour, proximity, similar size or a missing code never creates a merge.
State the concrete observation for each basis. Do not output names, quantities,
prices or dimensions beyond readings needed to explain a basis. Return schema
JSON only.
