# DETECTION V5.10.12 - FULL-PAGE MEMBERSHIP REVIEW

You receive a fixed visual-Island inventory, full-page images with immutable
Island IDs, and individual View crops. Determine multi-View membership against
the actual complete pages.

Return the complete revised set of multi-View `object_hypotheses`, not a list
of comments. You may reject or correct a draft proposal, combine its Views
differently, or omit it when every View is standalone. You cannot create,
remove, split, reclassify or rename an Island. Do not emit singleton
hypotheses.

Treat a draft as untrusted. Confirm a grouping only when the full page and
crops show the same physical fabrication through a shared distinctive envelope,
construction sequence, explicit view relation, unique geometry or literal
object-specific label. Keep independently framed products separate even when
they share a page, material, rail, frame type, or generic geometry. Include a
physically continuous drawing and its attached extension in one hypothesis if
Discovery preserved them as separate fixed Views.

For `direct_shared_structure`, matching frame type, material, profile or
construction principle is not proof. If physical continuity is visible inside
one depiction, it is an Island-boundary defect, not pair evidence. Across
separate Views, emit this type only with `structural_witness`: either one
endpoint is a complete View containing the other partial View, or a third
fixed View visibly shows both named parts physically joined. Include the
witness View ID, two joined-part labels and its visible connection in
`structural_witness`. The runtime cites that witness automatically.

Each evidence row must describe one concrete pair, named explicitly by
`group_id_a` and `group_id_b`. If A matches B and C, return separate rows for
A-B and A-C, each with its own image-based observation. Never use a pooled
three-View row. Use two evidence types unless an explicit author relation is
direct. Optional `source_fact_ids` are only for printed OCR source IDs
from SRC; the runtime adds the two registry_view citations automatically.
A third physical witness belongs in `structural_witness`, not in the pair.
Printed OCR IDs displayed as `[SF00202]` must be cited as `SF00202`, without
brackets. Cite at most three printed source IDs per row. Return schema JSON only.

V6.37 ADA COVERED PAIR-LOCAL MEMBERSHIP CONTRACT:
Document title blocks, project identity, author, sheet sequence and a common fabrication package are context only. They are never positive merge evidence, so do not emit explicit_document_relation. For every positive evidence row, name its exact two distinct endpoints in group_id_a and group_id_b. Do not use a fact from one proposed object to support another proposed object. Complementary local pairs within the same object hypothesis are allowed. For non-document visual evidence use strength "standard". For a hypothesis with more than two Views, provide at least two local pair facts and ensure every declared View appears in at least one of those facts. The facts may be complementary and need not form a chain. Never invent an extra bridge merely to connect the graph. If a View has no local evidence inside the hypothesis, split it out.
