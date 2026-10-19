# DETECTION V4 - REQUIRED PROOF-PARENT REGISTRY

Build the visual representation map and commercial-object registry in one response. The output has a strict causal order:

1. identify object-specific visual groups,
2. for every group, state whether it starts a new proof component or attaches to one earlier group, and why,
3. treat each connected proof component as exactly one commercial object,
4. describe that component and its complete page Evidence.

Do not declare an object owner first and add evidence afterwards. A group pair belongs to one object only through an evidence-backed attachment. Every group must contain a `proof_parent` decision. There is no optional global merge list.

## 1. Visual groups

Each `visual_group` is one visibly distinct, object-specific source depiction that can help Estimation: overview, alternate perspective, elevation, object plan, section, detail, module, door leaf, panel, track, cabinet bay or assembly fragment. It is not automatically a quote line or quantity.

Give each group a stable ordered `group_id`, physical `page_number`, short `location_hint`, literal visual `visual_description`, neutral `representation_kind`, and required `proof_parent`. It records only one visible depiction. Do not assign any object IDs or owners to a group.

Do not create a group for the cover/title page, title block itself, generic floor plan, room layout, electrical, plumbing or lighting plan, legend, administrative text, generic schedule or navigation diagram. Detection may use these internally for metadata, sheet codes and orientation, but they are not Estimation Evidence. Use `object_plan` only when a plan contains direct construction, identity or fabrication information for a specific in-scope object. `floor_plan` means generic non-object context and is discarded. A repeated grid, dimension string, repeated bays, slats, shelves or panel divisions is not a table by itself.

## 2. Required proof-parent decision, including why

Process groups in the output order. For **every** group, fill its `proof_parent` with exactly one of these actions:

1. `new_object_root`: this depiction begins a new proof component. Set `parent_group_id` to `ROOT`, `relationship` to `new_object_root`, and `evidence_facts` to `[]`. Set `dimension_assessment.status` to `not_applicable`, unless a confirmed dimension conflict is the reason it cannot attach, in which case set it to `confirmed_conflict`. Write a concise factual `decision_reason` answering: **why is there no positive proof that this group belongs to an earlier group?**
2. `attach_to_group`: this depiction belongs to one earlier emitted group. Set `parent_group_id` to that earlier `group_id`, use `same_object_view` or `object_detail`, provide the required typed `evidence_facts` and `dimension_assessment`, and write a concise factual `decision_reason` answering: **why do these two depictions form one independently quoted product?**

Never omit a decision, use a later group as parent, use an empty reason, or make an attachment without positive evidence. A root does not mean that the depiction is definitely a separately priced product in the abstract. It means that, from the available document evidence, it has no proved link to an earlier depiction and therefore begins its own candidate component. Every later group that has a proved relation must attach to one earlier group. This produces a forest without self-links, duplicate edges or cycles.

Resolve an attachment in this priority order:

1. `explicit_document_relation`: the same code, callout, view reference, axis or label.
2. `dimension_transform`: dimensions agree after a change of axes or describe compatible portions of one assembly.
3. `matching_topology`: matching order and count of bays, doors, supports, carcasses, frames, appliances, joints or structural elements.
4. `unique_geometry`: repeated cut-outs, handles, posts, appliance locations, turning parts, mounting points, panel sequence or distinctive frame geometry.
5. `direct_shared_structure`: a visible common frame, track, carcass, joint or other physical connection. It may support an attachment, never establish one alone.

Secondary signals, including proximity, room name, colour, material and same-sheet location, can reinforce a proven relation but cannot create it. A change of projection can make one item look unlike itself, so whole-silhouette similarity is not required.

An explicit same code, callout or view reference can prove one attachment on its own. One exact `dimension_transform` can also prove an attachment on its own, but only when its observation names the measurements on both groups and the exact axis or unit transformation that makes them agree. A vague statement that dimensions are "compatible", a similar scale, or one number appearing in both drawings is not a dimension transform. Without an explicit document relation or an exact dimension transform, an attachment needs at least two independent facts and at least one identity-level fact: `matching_topology` or `unique_geometry`. Two dimension facts are independent only when they cite different dimensions or axes. Every fact has its own pages and concrete observation. `decision_reason` must state the factual commercial basis, not generic phrases such as "one system" or "same sheet".

## 2a. Mandatory dimension comparison before every attachment

Before an `attach_to_group` decision, compare every readable explicit dimension on the candidate and its proposed parent. Normalize the document's units first, then account for the stated projection and axis transformation. Fill `dimension_assessment` with one status and a concise factual observation:

1. `confirmed_match`: at least one same-scope dimension agrees after a stated unit or axis transformation. A `dimension_transform` fact requires this status.
2. `not_comparable`: dimensions exist but address different axes or scopes, for example plan depth versus elevation width, a local section detail versus an overall envelope, or a repeated module versus a complete assembly.
3. `insufficient_dimension_evidence`: one or both depictions have no readable explicit dimension for comparison.

`confirmed_conflict` is a critical no-merge finding: if two readable dimensions claim incompatible values for the same scope and physical axis after unit normalization and allowed projection transformation, do not attach them, even if a code, sheet or proximity appears shared. Make the candidate a `new_object_root`, set `dimension_assessment.status` to `confirmed_conflict`, and name the earlier group and conflicting measurements in its observation and `decision_reason`. Different dimensions alone are not a conflict. Width versus depth, overall envelope versus local component, different axes, quantities, scales, or genuinely different views are `not_comparable` unless the drawing proves they claim the same physical measure.

Test commercial separability, not merely visual closeness. Different finished envelopes, principal functions or primary dimensions are affirmative evidence of separate components. A shared worktop, touching side panels or apparent continuous carcass is only a candidate connection until the source proves commercial inseparability. Adjacent furniture remains separate unless an attachment overcomes that evidence. Conversely, a kitchen, integrated cabinet wall, shelving wall or one continuous door-track system remains one component when the source proves one integrated joinery envelope.

## 3. Component registry

After every required proof-parent decision is complete, each connected component becomes exactly one object row. Its `component_anchor_group_id` must be one group in that component and must be used consistently by the matching page coverage. Do not return `object_id` or `visual_group_ids`: runtime derives the full component from the parent links, selects its canonical ordering, and assigns `object-001`, `object-002`, and so on.

For every component, return one row with its anchor, exact printed `transport_label` when present, otherwise a neutral source label, `quantity`, `quantity_explicit`, `identity_pages`, `visual_identity`, and `boundary_basis`. Quantity defaults to 1 when the document does not establish another quantity. `visual_identity` describes the complete physical product across its views. `boundary_basis` states the factual reason that this proof component is one quote line.

If a sheet carries one shared literal code but depicts several separate finished assemblies, they remain separate components unless attachments establish integration. If there are no child codes, preserve the literal base only as source context. Do not merge merely because the sheet code is shared.

## 4. Evidence coverage

Evidence is complete object-specific source context, not a shortlist of pages that appear sufficient for a material calculation. Return exactly one `page_coverage` entry for every physical upload page. Use `component_anchor_group_ids`, not object IDs. Include a component anchor whenever that page contains a visual group or other direct object-specific construction, identity, detail, plan, section, alternate view or assembly instruction for that component. A page can support several components.

Use an empty anchor list for a cover/title page, generic floor plan, room layout, electrical, plumbing, lighting, legend or another non-object-specific page. Those pages can guide Detection but are never Evidence for Estimation. Give every page a brief factual `evidence_reason`. The runtime derives each object's `estimation_evidence_pages`, so it cannot silently discard a qualifying page. There is no arbitrary page-count cap.

Do not extract dimensions, materials, pricing or final user-facing names. Return schema JSON only.
