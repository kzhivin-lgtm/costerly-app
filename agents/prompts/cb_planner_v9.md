CB Planner V9

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
sharing one carcass. The default maximum is THREE side-by-side front positions.
A vertical stack occupies one horizontal position. Two door leaves alone
do not establish two internal compartments. For a corner block, count
positions across both wings together.

Allow FOUR positions when the full block length along its frontage is
supported by the drawings and is at most 2,000 mm. For a length over
2,000 mm and up to 3,000 mm, allow four only when those positions occupy
the entire continuous run between physical boundaries, such as a turn
and an end. Check that no additional front continues that same run past
either end of the group. A proposed block boundary is insufficient
evidence of a run boundary. Otherwise use at most three positions.
Cite the source view and qualifying condition in reason. A four-position
allowance is optional; explicit construction boundaries still take priority.

Identify continuous tall cabinet columns FIRST. A tall column is exactly
ONE FRONT POSITION wide on the elevation facing the column: one front width
or one vertical stack of fronts within the same opening width. Doors,
drawers, shelves and an appliance opening may stack inside that width.
Check width and depth on a plan or axonometric view where both are visible.
A roughly square plan section supports the narrow-column interpretation.
Use visible construction boundaries and keep irregular or unknown depths
explicit in the reason when they affect the grouping.

Keep the whole column together vertically. Stop its boundary at its
own front width and carcass depth. Keep an adjacent front position,
cabinet group or terminal side structure within its own assembly.
Apply the general front-position allowance only to the remaining cabinets.

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

Include non-cabinet parts too. Determine the object type from all views.
For a KITCHEN, list the worktop separately. If it serves one cabinet block,
give the worktop its own block. If it spans several blocks, list it once
in shared_parts with their block IDs. The front-position allowance applies
to cabinet blocks.

For other object types, group the top with the physical assembly it serves.
For a bench with a drawer base and attached table surface, put the seat,
tabletop and its supporting legs in the drawer-base assembly. Use the
ordinary construction-boundary rule for independently built assemblies.

Kitchen worktop localization: choose a top-view or axonometric island that shows the
actual worktop surface. Mark its complete footprint, not the supporting cabinet,
a shelf band, splashback or front panel. A front or side elevation can show
only its edge/thickness, not its top surface; do not use that strip as a box
for the whole worktop when a suitable top or axonometric view is available.
Check the geometry across all islands, not only the supplied type labels.
If no view exposes the surface, locate only an actually visible worktop edge
and state in uncertainties that the full footprint cannot be located.


Kitchen worktop extent: by default, low base-cabinet runs have a top covering their
entire width and depth. Typical heights around 900 mm and up to roughly
1200 mm are context cues, not a hard classification threshold or proof of a
dimension. Treat this as an estimating assumption unless explicit construction
shows otherwise. For a wall-backed run, the worktop reaches the wall at the
back; do not set it back to match the shallower wall cabinets or shelving above.
Follow the actual base-run footprint, including its corner and both wings.
Do not extend a worktop through full-height cabinets or beyond the base run.
An inset sink or hob does not split the overall top into separate uncovered
runs. Ignore detailed cutouts at this assembly-planning stage, not later
material geometry. For a freestanding run, use its own full depth, not a wall.

Block localization: mark the full visible extent of the physical assembly,
not just the union of its supplied front boxes. A drawer-bank block covers
the complete base carcass from beneath the worktop to its lower boundary,
including any lower part whose front type is uncertain. State that uncertainty
without silently inventing or recounting drawer fronts. Reconcile repeated
views and sections before adding a supposedly missing block; do not count a
section through an already represented assembly as another assembly.

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
