# DETECTION V4.33 - INVENTORY, CLASSIFY, PROVE, DECIDE, PACKAGE

Build the visual representation inventory and commercial-object registry in one
response. The response has a mandatory causal order:

1. identify every visually distinct source island from the rendered pages in
   `visual_groups`, without assigning a class,
2. after the complete inventory exists, classify every group in the separate
   `classifications` array as `object_evidence` or `document_context`, with a
   factual reason,
3. after inventory and classifications exist, build the full graph of
   positive evidence-backed relations between `object_evidence` islands,
4. decide the package outcome for every commercial island from that graph,
5. describe those finished packages and their complete page Evidence.

Do not declare object owners before the graph is complete. Do not add graph
facts after declaring a package. All reasons and observations are concise,
factual, inspectable output, not hidden reasoning.

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
row for every `group_id`. Each row gives `object_evidence` or `document_context`
and a concise factual `classification_reason` answering: **why is this
object-specific Evidence or document context?** Do not revise, merge or split
the visual inventory during classification.

Use `document_context` for a cover or title page, title block, generic floor
plan, room layout, electrical, plumbing or lighting plan, legend,
administrative text, generic schedule or navigation diagram. These may orient
Detection but never enter the graph or Estimation Evidence. Use
`object_evidence` for a depiction that directly identifies, constructs,
specifies or shows a particular fabricated object, even when it is a section,
detail, alternate view or object-specific plan. A repeated grid, dimension
string, bays, slats, shelves or panel divisions is not a table by itself.

## 2. Full proof graph

Only after returning complete `visual_groups` and `classifications` arrays,
return `proof_edges`. It is the complete set of positive relations between all
`object_evidence` groups. An edge may connect any two groups, regardless of
their output order. Never connect `document_context`.

Merge edges say the two islands represent one independently quoted fabricated
product. Return only the minimal spanning forest for merge edges: no duplicate,
self, cyclic or transitive shortcut edge. A proof edge must name two different
`group_id` values. A self-edge is not evidence and is never a placeholder for
an unresolved target. If you cannot name a different target with accepted
evidence, omit the edge. An island with no proved merge relation becomes a
singleton package. Do not merge on shared page, room, colour, material,
proximity or visual impression alone.

An unproved relation is not an implicit attachment. If the available facts do
not meet the merge threshold, omit the merge edge. The island must then become
its own standalone package. It is forbidden to treat a group as "probably part
of" another product without either an accepted merge edge or a standalone
package outcome. Do not invent weak evidence merely to avoid a singleton.

Each edge has `same_object_view`, `object_detail`, or
`context_reference_link`, typed `evidence_facts`, and a factual
`commercial_inseparability` explanation. The first two answer: **why do these
two islands form one quote line?** They are merge edges. A
`context_reference_link` is directed from a composite or general view to an
individual product view. It answers: **why does this composite depiction supply
context to that independent product?** It never merges products, never enters
a proof component, and its source may not have any merge edge.

Use `context_reference_link` when one plan, axonometric view, arrangement or
general elevation depicts several distinct independently quoted products. Link
that composite source to each individual product view it visibly references.
The source becomes shared page-level Evidence for every linked package, not a
commercial package itself. For example, a sheet labelled N57 may show kitchen,
island and cabinet together in two general views and separately in dedicated
views. The general views context-link to all three dedicated products, they do
not merge kitchen, island and cabinet into one quote line.

Every fact names its page(s) and a concrete observation. Evaluate relations
globally across the complete classified inventory, not incrementally as groups
are emitted. For every candidate pair of `object_evidence` groups, assess all
six evidence types below before deciding merge, context link or no relation.
Do not stop at a first positive fact. The response remains compact: do not
serialize negative checks. But an accepted merge edge must serialize every
positive supporting fact found for that pair. `commercial_inseparability` prose
never substitutes for a typed evidence fact.

Apply the evidence types in this priority order:

1. `explicit_document_relation`: same code, callout, view reference, axis or label.
2. `dimension_equality`: the same readable physical dimension and scope are
   explicitly equal on both groups without a unit or axis transformation. Name
   both values, unit and scope.
3. `dimension_transform`: dimensions agree after a named unit or axis transformation.
4. `matching_topology`: matching bays, doors, supports, carcasses, frames,
   appliances, joints or structural elements.
5. `unique_geometry`: repeated cut-outs, handles, posts, appliance locations,
   turning parts, mounting points, panel sequence or distinctive frame geometry.
6. `direct_shared_structure`: visible common frame, track, carcass, joint or
   physical connection. It can support a merge but cannot establish one alone.

An explicit document relation can prove one edge on its own. One exact
dimension transform can prove one edge on its own only when the observation
names both measurements and the precise unit or axis transformation. Otherwise
an edge needs at least two independent facts and at least one identity-level
fact, `dimension_equality`, `matching_topology` or `unique_geometry`. One
`dimension_equality` is a strong positive fact but does not merge alone. Two
independent `dimension_equality` facts are sufficient dimension proof; three or
more increase its strength. Different dimensions prohibit a merge only when
they claim the same physical axis and scope after unit and projection
normalization. Width versus depth, overall versus local dimensions, different
scales, quantities and non-comparable projections are not conflicts.

## 3. Standalone-package declaration

Before writing `standalone_package_group_ids`, perform one final singleton audit
inside this same response. For every `object_evidence` group with no merge edge
that is not a `context_reference_link` source, compare it again with every
other `object_evidence` group. If accepted evidence proves a relation to a
different group, add that edge to the graph. Otherwise declare the group
standalone. Do not emit an edge merely to avoid a singleton. This audit adds no
new output field.

After that audit, return `standalone_package_group_ids`: the complete sorted
list of singleton component anchors. Every `object_evidence` group not on this
list must belong to an accepted non-singleton merge component. A
`context_reference_link` source is excluded because it is shared page-level
Evidence, not a candidate package.

There is no third outcome. A detail that seems related but lacks a proved merge
is listed as a standalone commercial candidate for review. The runtime derives
and persists the full per-group package ledger from the graph, so do not repeat
that ledger in the response.

## 4. Commercial-object packages

After the graph is complete, only merge-proof connected components are packages.
`context_reference_link` sources are not packages. Return
exactly one `objects` row per component, using any group inside it as
`component_anchor_group_id`. Runtime derives the canonical group membership and
ordered object ID from the graph, so do not return owner lists or object IDs.

For every package provide the exact printed `transport_label` when present,
otherwise a neutral source label, `quantity`, `quantity_explicit`,
`identity_pages`, `visual_identity`, and factual `boundary_basis`. Quantity
defaults to 1 when not established otherwise. When one printed root code labels
a composite source but the graph proves multiple independent child packages,
return that exact same root code for every child package. Runtime preserves the
root and appends deterministic A/B/C child suffixes in package order. Never add
the suffix yourself. `boundary_basis` must explain why
the complete component is one quote line, or for a singleton, why no proved
relation joins it to another object-evidence island. A shared sheet code never
merges separate finished assemblies by itself.

## 5. Evidence coverage

Return exactly one `page_coverage` entry for every upload page. Use component
anchors, never object IDs. Include a component anchor whenever the page carries
a visual group or direct object-specific construction, identity, detail, plan,
section, alternate view or assembly instruction for that component. A page may
support several components. Give every page a factual `evidence_reason`.

Use an empty anchor list for pages that contain only `document_context`. Such
pages are never Estimation Evidence. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or final user-facing names.
Return schema JSON only.
