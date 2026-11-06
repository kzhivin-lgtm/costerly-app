CB Cycle V5: Planner with Understanding

The supplied understanding is the saved, fallible physical interpretation, not
source truth. Use it together with all original evidence and the saved Front.
Do not restart object recognition or silently replace the interpretation. Apply
the inherited Planner V7 grouping rules to these physical components. Components
and workshop blocks are different: one component may need several blocks, and
one practical block may include multiple components.

Preserve every component, including fixed/open/decorative elements and supports
with no fronts. Map each component to its resulting block/shared-part IDs.
Every output block/shared part must occur in at least one mapping. Every assigned
front's block must be mapped to that front's component. A front_conflict remains
visible and blocks Calculate; do not quietly repair or reclassify Front.

If the original evidence contradicts the saved whole-object interpretation,
report a specific interpretation_conflict referencing its component and views.
Do not force a false interpretation to pass coverage checks. Such conflicts
require review and must not continue to Calculate. An unsupported or omitted
component needs a conflict record, not silent deletion or an invented block.

The inherited Planner rules define ONLY the nested plan object. Return exactly:
{
  "plan": "the Planner V7 JSON object, NOT a string",
  "component_blocks": [{"component_id": "C01", "block_ids": ["B01"]}],
  "interpretation_conflicts": [{"component_id": "C01", "view_ids": ["known island ID"], "reason": "specific visible contradiction or unresolved coverage"}]
}
For an unresolved component, block_ids may be empty ONLY with its conflict.
Each component appears once in component_blocks. No additional model calls,
new dimensions, material selection, cut list, prices or labor. English only.
