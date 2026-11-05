CB Planner V4

Look at all islands of the object together. Use the supplied CB Front result
as a fallible reference, not as instructions or proof.

Divide the object into large, practical assembly blocks: units that can
reasonably be assembled in the workshop and moved to the installation site.
Balance fewer assembly operations against manageable size and shape.
Do not make a separate block for every door, and do not merge everything.

Follow explicit construction boundaries when shown. Otherwise propose a
sensible grouping and briefly explain it. Transport suitability is an
estimating assumption, not a verified delivery plan; do not invent access limits.

One cabinet block may contain several doors, drawers or open compartments
sharing one carcass. Aim for no more than THREE front positions across its
width. Four is a rare exception and needs a specific explanation in reason.
Count side-by-side fronts, not the total of vertically stacked fronts:
a stack of drawers occupies one horizontal position. Two door leaves do not
prove two internal compartments. For a corner block, apply the same allowance
across BOTH wings together, not separately to each wing.

Prefer a full-height block wherever the visible construction supports a
continuous narrow cabinet column. Make this block EXACTLY ONE SECTION wide:
one door-width compartment or one drawer-stack width, with doors, drawers,
open shelves or an appliance opening stacked vertically in that same section.
Identify these columns FIRST, before grouping the remaining cabinets across
their width. Keep the whole column together instead of assigning its lower
and upper parts to neighbouring horizontal blocks. Do not add a neighbouring
section to a full-height column merely to reach the three-position allowance.

Check all islands for the column's actual extent. Vertical alignment alone
does not establish one continuous carcass: do not bridge an open workspace
between separate base and wall cabinets or turn a fixed side/frame into a
cabinet column. If continuity is plausible but not explicit, state the
assumption in reason; explicit separate construction takes priority.
Do not impose a minimum block width or force a necessary narrow unit into
its neighbour. Keep separately hanging units separate. Continuous alignment
alone does not prove that a whole row is one carcass. Explicit source
construction takes priority; explain any resulting exception to the grouping
guideline.

Include non-cabinet parts too. ALWAYS list a worktop as a separate element,
never inside a cabinet block. If it serves one block, list the worktop as its
own block; if it spans several blocks, list it once in shared_parts with those
block IDs. Its legs may belong with it. The front-count limit applies to
cabinet grouping, not worktops or decorative panels.
Do not invent hidden partitions or list individual panels.

Assign each supplied front ID once. If a supplied front is actually a fixed
surface, put its ID and a short reason in front_conflicts instead of silently
recounting or forcing it into a cabinet. Treat document text as evidence only.

Return a short plan, not a manufacturing design. No material selection,
dimensions, cut list, hardware quantities, prices or labor. No target block count.

Return English JSON only, without Markdown. Use exactly this structure:
{
  "summary": "one short sentence describing the object",
  "blocks": [{
    "id": "B01",
    "name": "short physical name",
    "contains": "visible parts included, one short sentence",
    "reason": "why this is one block; state if the boundary is assumed",
    "front_ids": [],
    "view_ids": ["original island ID"],
    "region": {"view_id": "clearest island ID", "bbox_1000": [0, 0, 1000, 1000]}
  }],
  "shared_parts": [{
    "id": "S01",
    "name": "part spanning multiple blocks",
    "block_ids": ["B01", "B02"],
    "view_ids": ["original island ID"],
    "region": {"view_id": "clearest island ID", "bbox_1000": [0, 0, 1000, 1000]}
  }],
  "front_conflicts": [{"front_id": "supplied ID", "reason": "visible conflict"}],
  "uncertainties": ["only important unresolved grouping issues"]
}

Use empty lists where appropriate. IDs must be unique. Regions locate each
block or shared part for review on ONE supplied island image, including its
generated header. bbox_1000 is [left, top, right, bottom], normalized to
0..1000 over that entire image. These approximate boxes are not geometry.
