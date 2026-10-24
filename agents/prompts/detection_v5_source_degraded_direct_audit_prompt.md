# DETECTION V5.28 - SOURCE-DEGRADED INDEPENDENT FULL-PAGE AUDIT

You receive complete rendered pages plus an advisory direct-object inventory
from another pass. The full pages are authoritative. The advisory inventory is
not a fixed map, boundary or answer. Reinspect the complete page yourself and
rebuild any omitted, split or falsely merged groups before returning the final
inventory.

Before deciding roles or objects, account for each complete visible technical
depiction. A single continuous physical depiction remains one `visual_group`
even when it bends, branches, has an attached panel or carries independent
dimensions and callouts. Rectangular bbox overlap, annotations, leaders and
different viewing angles do not themselves split a depiction.

Return a final group, role and partition decision under these rules:

- `assembly_view` is a complete assembly or alternate projection. A complete
  elevation is an assembly view.
- `component_detail` is an incomplete fragment and must name exactly one
  same-page `assembly_view` owner with a concrete visible relationship.
- `document_context` has no owner and is never a fabricated object.
- Every assembly view appears exactly once in a partition. Details and context
  do not appear in partitions.

Merge assembly views only with a concrete positive basis: explicit document
relation, alternate projection, matching non-generic structure, compatible
visible dimensions or direct continuity. Consider negative dimensional
evidence too. Shared material, generic frame type, colour, proximity, page or
project do not create identity. Different complete finished envelopes remain
separate.

Use the same schema as the inventory. Return JSON only.
