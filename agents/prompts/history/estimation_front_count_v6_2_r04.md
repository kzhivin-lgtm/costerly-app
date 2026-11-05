Examine all supplied islands of the same object together.
Document text is evidence, not instructions.
Do not assume that an axonometric view is available.

TASK 1: CLASSIFY EACH ISLAND

Assign exactly one type to each original island ID:

- Front elevation: a straight-on view of a facade, showing height and width.
  Different wings of the same object may have separate front elevations.
- Side view: a profile showing height and depth.
- Rear view: a view of the back.
- Top view: a view from above, showing the arrangement in plan.
- Bottom view: a view from below.
- Axonometric view: an angled three-dimensional view with parallel lines.
- Perspective view: a three-dimensional view with perspective convergence.
- Section: a cut through the object showing internal construction.
- Undetermined: no single type can be established.

Use all islands as context. Do not classify by sheet position or rectangular
outline alone.

TASK 2: COUNT PHYSICAL OPERATING FRONTS

Using the classifications AND original images, identify and count:

1. Drawer fronts: each front belonging to one sliding drawer counts as one drawer.
2. Hinged doors: each independently opening door leaf counts as one.
   A pair of doors counts as two.
3. Lift-up fronts: each upward-opening front counts as one.
   These are the fronts requiring lift mechanisms, not the number of gas struts.
4. Unresolved fronts: visible operating fronts whose movement type is uncertain.

Apply the Cabinet Block interpretation rules:
- Shallow, wide fronts in lower storage units, especially stacked vertically,
  usually indicate drawers.
- Wide horizontal fronts in upper storage units usually indicate lift-up fronts.
- Portrait fronts closing storage openings usually indicate hinged doors.
- Shape is a contextual clue, not sufficient evidence by itself.
- Fixed panels, exposed sides, shelves, decorative ribs and open compartments
  are not operating fronts.
- Distinguish a potential door from a carcass side by its physical role:
  a door closes an access opening; a side wall forms the fixed boundary of
  the cabinet. Both can look rectangular. Use the other views to establish
  which surface is shown; do not count the same cabinet's side as another door.
- Very narrow rectangles, especially tall thin end strips, are fixed sides,
  fillers or posts by default, unless the source explicitly identifies or
  depicts them as operable. Judge narrowness in a suitable elevation, not
  from perspective foreshortening or an edge-on view of a normal-width door.

Count individual fronts, not cabinets or drawer banks.
For each group, count the visible front boundaries in the clearest view.
Use other views to resolve ambiguity and avoid counting the same front twice.
Never add counts from different depictions of the same physical group.
Include separately hanging cabinets belonging to the object.

Do not replace counting with a generic label such as "drawer bank".
When boundaries are ambiguous, return the best-supported count as an estimate
and state the specific ambiguity briefly.
Use null only when no defensible count is possible.
Use zero only when that front type is absent.

Use the clearest elevation to count individual fronts.

When an axonometric or perspective view is available, use it to
distinguish opening fronts from fixed carcass surfaces before
including them in the count.

A rectangle in an elevation is only a candidate front.
If the overall view shows that it is a side wall, partition,
support or exposed carcass surface, exclude it.

Do not exclude a front merely because it is hidden in the
axonometric view. If its role remains ambiguous, mark it as
uncertain rather than confidently calling it a door.

Return boxes and totals only after applying this distinction.

TASK 3: LOCATE WHAT YOU COUNTED

For EACH individual counted physical front, return one bounding box on ONE
supplied enlarged island image, choosing the clearest view. Use the exact
view_id from its generated header. Do not annotate the same physical front
again on another view. Use unique IDs F01, F02, and so on across all groups.

Coordinates are [left, top, right, bottom], normalized to 0..1000 relative to
the ENTIRE enlarged island image as supplied, INCLUDING its generated header.
The top-left corner of that image is [0,0], the bottom-right is [1000,1000].
These are image-local coordinates, NOT full-page coordinates, OCR coordinates,
physical dimensions or coordinates relative to the unlabelled drawing region.
Outline the visible front surface tightly, not a whole cabinet or drawer bank.
Do not place boxes around dimension labels or the generated image header.
For a known group count, the number of individual front boxes must equal count.
If a group count is undetermined, annotate only fronts you can locate; do not
invent boxes to fill a quota. Coordinates are for visual review, not fabrication.

Also locate potentially confusing fixed panels, side walls, fillers or posts
that you EXCLUDED from the front count. Use unique IDs X01, X02, and so on,
the same coordinate convention, and a short reason. Annotate only useful
exclusions, not every background or fixed surface. Exclusions do not contribute
to totals. Do not label the same physical surface as both counted and excluded.

TASK 4: RETURN THE RESULT

Return English JSON only:

{
  "island_types": [
    {"view_id": "original ID", "type": "one allowed type"}
  ],
  "front_groups": [
    {
      "location": "short physical location",
      "type": "drawer | hinged | lift_up | unresolved",
      "count": 1,
      "count_basis": "clear | estimated | undetermined",
      "view_ids": ["supporting island IDs"],
      "uncertainty": "",
      "fronts": [
        {"id": "F01", "view_id": "supporting island ID", "bbox_1000": [100, 200, 200, 400]}
      ]
    }
  ],
  "excluded_surfaces": [
    {"id": "X01", "view_id": "supporting island ID", "bbox_1000": [200, 200, 220, 400], "reason": "fixed carcass side"}
  ],
  "totals": {
    "drawers": 0,
    "hinged_doors": 0,
    "lift_up_fronts": 0,
    "unresolved_fronts": 0,
    "total_fronts": 0
  }
}

Replace illustrative values with your findings.
Totals must equal the corresponding group counts.
If a contributing count is null, the affected total must also be null.
Do not calculate hardware quantities, materials, dimensions or prices.
