# DETECTION V4 - PHYSICAL ASSEMBLY CORRESPONDENCE GRAPH

This is a narrow pre-registry visual task. The input consists only of masked
figure-layout maps, masked isolated drawing figures, stable representation IDs
and physical PDF page numbers. It deliberately excludes the file name, OCR,
project name, room title and title block. Do not infer identity from information
outside the supplied figures.

Each white background in a masked figure is not part of that figure. A red
frame in a page-layout map identifies one detected figure's location. Frames
and neighbouring positions never prove a physical connection.

## Step 1: classify every figure

For every representation, return `complete_assembly` only if it visibly shows
a complete physically unified fabricated assembly. Otherwise return
`supporting_view_or_detail`. `visible_identity` must describe visible form
only, never a product name, room name, quantity, price or dimensions.

## Step 2: compare every pair independently

For every pair in the manifest, return exactly one relation:

- `same_assembly` only when direct visual correspondence proves these are
  different views of the exact same finished physical envelope. State the
  matching envelope, unique panel sequence, shared frame, continuous worktop,
  track, mounting structure or explicit view relation that proves this.
- `separate_assemblies` when the figures can coexist as two independent
  finished products, or their envelopes, proportions, carcasses, bases,
  mounting structures or distinctive panel sequences are different.
- `insufficient` when neither conclusion has direct visible proof.

Similarity of finish, room, scale, repeated furniture vocabulary, or the fact
that two figures look like parts of an L-shaped room composition is never
direct proof of `same_assembly`. Do not construct a larger composition from
nearby figures. A `same_assembly` relation is a high bar: reject it unless the
two figures can be mapped to one exact physical envelope from different views.

This is not naming, quantity, pricing, evidence selection or commercial-object
classification. Account for every supplied representation and every unordered
pair exactly once. Return schema JSON only.
