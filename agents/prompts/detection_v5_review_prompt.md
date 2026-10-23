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

Each evidence row must be a concrete positive fact true of every connected
View. Use two evidence types unless an explicit author relation is direct. Cite
only IDs from `SRC`. For visual observations, cite
`registry_view:<View ID>` for every connected View. Never cite View IDs as
source facts. OCR source IDs are displayed as `[SF00202]` only for readability.
When citing, output the interior token `SF00202`, without brackets or quoted
text. Cite at most two exact source IDs per evidence row. Return schema JSON
only.
