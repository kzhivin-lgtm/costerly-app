# DETECTION V4.41 - INVENTORY, CLASSIFY, COMPLETE COMPACT GRAPH, PACKAGE

Build the visual representation inventory and commercial-object registry in one
response. The response has this mandatory causal order:

1. identify every visually distinct source island in `visual_groups`, without
   assigning a class,
2. classify every group in the separate `classifications` array as
   `object_evidence` or `document_context`, with a factual reason,
3. inspect the complete classified inventory globally, record the six-factor
   result for every pair in `pair_relation_runs`, then return the factual
   detail only for positive criteria in `pair_relation_facts`,
4. after the graph is complete, describe the resulting commercial packages and
   their complete page Evidence.

Do not declare object owners before reviewing the graph. Do not add graph facts
after declaring a package. All reasons and observations are concise, factual,
inspectable output, not hidden reasoning.

## 1. Complete visual-island inventory

Each `visual_group` is one visibly distinct graphical or documentary island:
an overview, alternate perspective, elevation, object plan, section, detail,
module, door leaf, panel, track, cabinet bay, assembly fragment, floor plan,
title block, legend or framed document text. It is one depiction, never yet a
quote line or quantity.

First enumerate islands directly from rendered pages. Then use `OCR GRAPHIC
REGION INVENTORY` only as a passive recall aid. If an OCR coordinate may hold a
missed island, re-inspect it and add a group only when the page confirms a
distinct island. OCR cannot create, split, merge, delete or invalidate a group.
Visual islands without a matching OCR region remain valid. OCR IDs are never
returned and never enter classification, graph, quantity or Evidence.

Give every group a stable ordered `group_id`, physical `page_number`, short
`location_hint`, literal `visual_description`, and neutral `representation_kind`.
One group records exactly one visibly distinct depiction. Never combine two
side-by-side elevations, several views, or a dimension annotation and a facade
into one group merely because they occupy one visual block.

## 1a. Classification

After the complete `visual_groups` array, return exactly one `classifications`
row for every `group_id`. Each row gives `object_evidence` or
`document_context` and a concise factual `classification_reason` answering:
**why is this object-specific Evidence or document context?** Do not revise,
merge or split the visual inventory during classification.

Use `document_context` for a cover or title page, title block, generic floor
plan, room layout, electrical, plumbing or lighting plan, legend,
administrative text, generic schedule or navigation diagram. These may orient
Detection but never enter the graph or Estimation Evidence. Use
`object_evidence` for a depiction that directly identifies, constructs,
specifies or shows a particular fabricated object, including a section, detail,
alternate view or object-specific plan. A repeated grid, dimension string, bays,
slats, shelves or panel divisions is not a table by itself.

## 2. Complete compact relation graph

Only after the inventory and classifications exist, inspect every unordered
pair of `object_evidence` groups globally across the complete document. Assess
all six criteria for each pair:

1. `explicit_document_relation`: same code, callout, view reference, axis or
   label;
2. `dimension_equality`: the same readable physical dimension, unit and scope
   are literally equal without conversion or axis remapping;
3. `dimension_transform`: dimensions agree after a named unit conversion or
   axis remapping between projections;
4. `matching_topology`: matching bays, doors, supports, carcasses, frames,
   appliances, joints or structural elements;
5. `unique_geometry`: repeated cut-outs, handles, posts, appliance locations,
   turning parts, mounting points, panel sequence or distinctive frame geometry;
6. `direct_shared_structure`: visible common frame, track, carcass, joint or
   physical connection.

Generate the exact lexicographic pair order from the `object_evidence`
`group_id`s: first every pair beginning with the first group, then every pair
beginning with the second group, and so on. Each pair has a seven-character
state. Character one is the relationship: `N` none, `P` positive non-merging
relation, `S` same object view, `D` object detail, or `R` reference link. The
next six characters are the six criteria above in that exact order. Use `Y`
positive, `N` checked-negative, `C` conflict, or `U` unreadable/not comparable.

Return the complete sequence losslessly in `pair_relation_runs`, not as one
JSON row per pair. Every run has `count` and `state`, represents that many
consecutive pairs in canonical order, and adjacent equal states must be merged
into one run. The expanded runs must contain exactly one state for every pair.
This ledger is mandatory. It is the proof that every pair and every criterion
was considered, not a prose exercise. A `Y` criterion requires exactly one
corresponding factual row in `pair_relation_facts`; do not return a facts row
for a pair with no `Y`. Each facts row names its zero-based `pair_index`, all
positive `evidence_facts`, and a concise factual `commercial_inseparability`.
For `P`, the commercial basis may be blank because the fact is retained for
audit only. For `S`, `D`, or `R`, it must state why the relationship is usable.
The graph is undirected. Cycles and redundant positive edges are valid, because
they preserve evidence rather than decide package membership directly.

An exact `dimension_equality` fact names both literal dimensions, unit and
physical scope. An exact `dimension_transform` fact names both literal
dimensions and the unit or axis transformation. The same pair may have both:
equality records a direct same-axis match, while transform records an additional
match after changing axes or units. Return every observed positive equality and
transform fact, including redundant facts, so the graph remains inspectable.

Use `same_object_view` or `object_detail` only when the two islands are
candidates for one commercial package. An explicit document relation may prove
one merge. One exact dimension transform may prove one merge only when both
measurements and the exact transformation are named. Otherwise a merge needs at
least two independent facts and at least one identity-level fact:
dimension equality, matching topology, dimension transform or unique geometry.
Two independent dimension equalities are sufficient dimension proof. One
equality is strong support but is not enough alone. A single shared structure
cannot establish a merge alone.

Use `reference_link` when depictions are related as Evidence but must not become
one quote line, for example an object-specific general plan showing several
objects and their dedicated views. A reference link never merges packages. It
is not directional and cannot suppress a standalone candidate. Do not use a
generic floor plan or room layout as `reference_link`: it is `document_context`.

Do not merge on shared page, room, colour, material, proximity or visual
impression alone. A printed sheet-level root code alone is not enough to merge
independent finished assemblies. If a connection is not proven, leave the
groups unmerged. Runtime will create review-required standalone packages rather
than discard them.

Perform one final singleton audit after the complete ledger is emitted. For
every `object_evidence` group with no merge candidate, compare it again with
every other object-evidence group. Add a relation only when the cited evidence
supports it. Never invent a merge merely to avoid a singleton.

## 3. Commercial-object packages

Runtime derives package membership only from accepted `same_object_view` and
`object_detail` edges. Every group without an accepted merge remains a
quantity-one review-required standalone package. `reference_link` pages are
attached as Evidence to their linked packages but do not alter their boundary.

`objects` is optional descriptive metadata for the graph-derived components,
never a package decision. When supplied, return at most one row per component,
using any group inside it as `component_anchor_group_id`. Do not return owner lists or object IDs. If metadata is unavailable, omit its row rather than
inventing a merge.

For every described component provide the exact printed `transport_label` when
present, otherwise a neutral source label, `quantity`, `quantity_explicit`,
`identity_pages`, `visual_identity`, and factual `boundary_basis`. Quantity
defaults to 1 when not established otherwise. Set `quantity_explicit` true only
when the source literally establishes a count for that finished assembly. A
code, repeated view, repeated dimension, cabinet module count, page count or
similar-looking custom kitchen/cabinet is not an explicit quantity. A bespoke
kitchen, cabinet, counter or similar finished assembly remains quantity one
unless the source proves multiple identical finished assemblies. A shared sheet
code does not by itself merge independent finished assemblies. It may remain
one package when the positive graph proves that single commercial boundary.

## 4. Evidence coverage

Return exactly one `page_coverage` entry for every upload page. Use component
anchors, never object IDs. Include a component anchor whenever the page carries
a visual group or direct object-specific construction, identity, detail, plan,
section, alternate view or assembly instruction for that component. A page may
support several components. Give every page a factual `evidence_reason`.

Use an empty anchor list for pages that contain only `document_context`. Such
pages are never Estimation Evidence. There is no arbitrary page-count cap.

Do not infer or publish final external object dimensions, materials, pricing or
final user-facing names. Use literal source dimensions only to assess graph
criteria and record them in positive dimension facts.
Return schema JSON only.
