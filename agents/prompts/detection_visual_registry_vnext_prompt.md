# DETECTION V4.39 - INVENTORY, CLASSIFY, COMPLETE GRAPH, DECIDE, PACKAGE

Build the visual representation inventory and commercial-object registry in one
response. The response has a mandatory causal order:

1. identify every visually distinct source island from the rendered pages in
   `visual_groups`, without assigning a class,
2. after the complete inventory exists, classify every group in the separate
   `classifications` array as `object_evidence` or `document_context`, with a
   factual reason,
3. after inventory and classifications exist, inspect literal dimensions in the
   rendered page and OCR source, then build the complete six-criterion graph
   between `object_evidence` islands,
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
A generic floor plan or room layout remains `document_context` even when it
shows placements. It cannot be `reference_link` or shared Evidence. An
object-specific plan needs a concrete product identity, construction detail, or
evidence-backed relation to a particular fabricated package.

## 2. Complete graph, not a sparse graph

Only after returning complete `visual_groups` and `classifications`, inspect
every readable literal dimension in the rendered page and source OCR that can
bear on a cross-view relation. Do not return a separate dimension transcript:
the full source OCR and rendered pages remain the canonical record. Return the
complete undirected graph across every unordered pair of
`object_evidence` groups. The canonical pair order is lexicographic over the
sorted `group_id` list: `(G001,G002)`, `(G001,G003)`, and so on. Return exactly
one seven-character string in `pair_relation_states` for every pair. The first
character is the resulting relation: `N` no relation, `P` positive relation
that is not selected into the minimal proof tree, `S` same object view, `D`
object detail, `R` shared reference link. The other six characters have
this exact criterion order: explicit document relation, dimension equality,
dimension transform, matching topology, unique geometry, direct shared
structure. For each criterion write `Y` positive, `N` checked-negative, `C`
comparable conflict, or `U` unreadable or not comparable.

This state ledger is mandatory for every pair, including a pair with no
positive relation. It is how the runtime verifies that all six criteria were
actually examined.

For every state string that contains `Y`, return exactly one
`pair_relation_facts` row with that pair's zero-based index, every positive
typed `evidence_facts` observation, and a concise factual
`commercial_inseparability`. Do not return a facts row for an all-negative,
conflicted or unreadable pair. Every `Y` must have one or more matching typed
facts. A `dimension_equality` observation names both literal dimensions, their
unit and physical scope. Two matching dimensions are sufficient merge evidence.
Three or more are very strong evidence. A conflict is `C` only when both values
claim the same physical axis and scope after unit and projection normalization.

The graph is undirected. `S` means `same_object_view` and `D` means
`object_detail`; both are merge relations. `R` is a
`reference_link`: the depictions are related without one quote line, it never
merges packages and has no source, target, direction or information-transfer
meaning. A group in `shared_reference_group_ids` has `R` links to at least two distinct proven commercial packages and no `S` or `D` relation. Generic floor
plans, room layouts, dimension strings, local construction details and panel
grids cannot be shared Evidence merely because they relate to another depiction.

Only after all pair states and positive facts are complete, select only the
necessary `S` or `D` relations for the minimal proof forest. Record any other
positive but redundant relation as `P`, never as `N`, so the full evidence graph
remains inspectable without cycles. Do not use a transitive shortcut or self
relation. If no proved merge relation joins an island, it is a singleton
package. Do not merge on shared page, room, colour, material, proximity or
visual impression alone. Do not invent weak evidence to avoid a singleton.

Every fact names its page(s) and a concrete observation. Evaluate every pair
globally across the complete classified inventory, never incrementally as
groups are emitted. Do not stop at the first positive fact. An explicit
document relation can prove one merge on its own. One exact dimension transform
can prove one merge only when its observation names both measurements and the
precise unit or axis transformation. Otherwise an `S` or `D` relation needs at
least two positive facts, including an identity-level fact: dimension equality,
matching topology, dimension transform or unique geometry. A single shared
structure cannot establish a merge on its own.

## 3. Singleton-package audit

Perform one final singleton audit inside this same response. For every
`object_evidence` group with no merge edge that is not in
`shared_reference_group_ids`, compare it again with every other
`object_evidence` group. If accepted evidence proves a relation to a different
group, add that edge to the graph. Otherwise leave it unmerged. Do not emit an
edge merely to avoid a singleton. Runtime derives every singleton package from
the completed graph, so do not return a second standalone-ID list.

There is no third outcome. A detail that seems related but lacks a proved merge
is a standalone commercial candidate for review. The runtime derives and
persists the full per-group package ledger from the graph.

## 4. Commercial-object packages

After the graph is complete, only merge-proof connected components are packages.
Groups in `shared_reference_group_ids` are not packages. `objects` is optional
descriptive metadata for already proven components, never a package decision.
When supplied, return at most one row per component, using any group inside it
as `component_anchor_group_id`. Runtime derives canonical group membership and
ordered object ID from the graph, so do not return owner lists or object IDs.

For every package provide the exact printed `transport_label` when present,
otherwise a neutral source label, `quantity`, `quantity_explicit`,
`identity_pages`, `visual_identity`, and factual `boundary_basis`. Quantity
defaults to 1 when not established otherwise. When one printed root code labels
a composite source but the graph proves multiple independent child packages,
return that exact same root code for every child package. Runtime preserves the
root and appends deterministic A/B/C child suffixes in package order. Never add
the suffix yourself. `boundary_basis` must explain why the complete component
is one quote line, or for a singleton, why no proved relation joins it to
another object-evidence island. A shared sheet code never merges separate
finished assemblies by itself. If complete descriptive metadata is unavailable,
omit that `objects` row. Runtime creates a quantity-one review candidate with
Evidence from the proven component rather than inventing a merge or failing the
document.

## 5. Evidence coverage

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
