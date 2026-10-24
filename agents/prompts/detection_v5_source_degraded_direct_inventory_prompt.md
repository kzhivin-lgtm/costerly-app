# DETECTION V5.28 - SOURCE-DEGRADED DIRECT OBJECT INVENTORY

The source has no usable coordinate-bearing PDF or OCR evidence. Inspect the
complete rendered pages directly. Do not rely on a prior map, crop, overlay or
pair queue. Your task is to inventory fabricated objects from what is visibly
drawn on the full page.

## Visual groups

Create one `visual_group` for each visibly distinct technical depiction that
helps identify an in-scope fabricated object: an assembly, alternate view,
elevation, section or necessary component detail. A group is a complete
continuous depiction, not an arbitrary rectangle. If construction geometry
continues through a bend, branch, panel or support, keep it in one group. Its
`bbox` is only a padded transport envelope around that depiction.

Map titles, room plans, schedules, title blocks and legends only as
`document_context` when needed to account for the page. Account for every
returned group in exactly one page-coverage row.

## Roles and owner

Return one role for every group.

- `assembly_view`: a complete independent fabricated assembly or an alternate
  view of one. A full elevation or 2D technical view can be complete.
- `component_detail`: an incomplete fragment only. It must give exactly one
  same-page `owner_group_id` that is an `assembly_view`, and state the visible
  relationship. If no complete owner is visible, it is not a component detail.
- `document_context`: plan, schedule, title block, legend or administration.
  It has an empty owner.

Do not demote a complete system to a detail merely because it shares a page,
material, colour, frame principle or annotation style with another drawing.

## Object partitions

Each partition is one product a contractor would quote, fabricate, supply or
replace independently. Consider every assembly view together. Every assembly
view must appear once in a partition. Details and document context never
appear in a partition.

Use concrete positive visual evidence for a multi-view partition: explicit
author relation, alternate projection of the same finished assembly, matching
non-generic ordered structure, compatible visible dimensions, or direct
physical continuity. Dimensions can support or contradict identity, but do not
invent readings. Generic material, frame type, colour, page position,
proximity or a shared project never creates a merge. Different complete
finished envelopes or systems remain separate.

For a singleton use `complete_physical_envelope`. Return JSON only.
