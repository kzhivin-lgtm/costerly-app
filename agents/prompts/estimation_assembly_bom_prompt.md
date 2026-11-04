# ESTIMATION CALCULATION V6.1, LOCKED CONSTRUCTION AND 2VN GEOMETRY

V6.1 composition_scope supplies the shared Analyze interpretation, palette,
source/legend evidence chains, locked material_roles, panel_groups and explicit
assumptions. Read this context together with the object images and OCR. Return
geometry and measured dimensions for each locked panel group. Do
not reselect material family, finish, thickness, layer count or alternatives.
Code restores the locked material roles. Record contradictions in omissions.
For each panel group return its exact group_id and dimensions.width/height
using the axis-value schema below. Measure its physical panel face, not the
screen envelope repeated for every rib. Cite measurements or label assumptions.
Support zones retain quantity/construction; linear_stock needs height. Do not
repeat supports in secondary_items. Preserve scope geometry_links.
When construction_version is supplied, omit repeated material_roles, counts,
front_groups and exposure from the response. Code supplies these locked values.
The legacy schemas below describe the optional fields for older scopes only.

The supplied object identity is fixed. Do not rename it, classify it as a
product type, or infer a catalog item, price, labour, manufacturing operation,
overhead or sale price.

Inspect every supplied page, its bounded OCR evidence and the Dimension Graph.
The graph contains source numbers and relation candidates only. A number is not
an object dimension unless its cited source context supports that use.

Return raw JSON only:

`{"batch_id":"...","pages":[...],"document_unit":{...},"view_interpretations":[...],"dimension_bindings":[...],"assemblies":[...],"secondary_items":[...],"coverage":[...],"omissions":[...]}`

`composition_scope` is a locked result of Estimation Analyze. It defines the
physical zones and their operability. Return one assembly with exactly each
`scope_id` as `assembly_id`, and the exact `assembly_role`, `counts` and
`front_groups` supplied for that zone. You may fill only dimensions, exposure,
view interpretation and dimension bindings. Never add a zone,
delete a zone, convert a fixed zone into a facade, or infer hardware that the
scope does not permit. When geometry is missing, provide a labelled
approximation rather than changing the scope.

`batch_id` and `pages` are optional response metadata. If included, a page is
`{"page_number":N}`. They never replace evidence references in an assembly.

First return exactly one document unit context:

`{"unit":"mm|cm|m","basis":"explicit_source|document_convention_assumption","evidence_refs":[...],"assumption_reason":"string|null"}`

Use `explicit_source` only when the unit is stated or unambiguously conventional in the drawing. A unitless drawing may use `document_convention_assumption`, with no evidence refs and one short reason. Infer that convention from the actual dimension lines and the physical scale of the depicted object as a whole. Ignore titles, labels and other non-dimensional text. This unit is the default for all dimensions unless a dimension explicitly overrides it.

`dimension_scale_gate` is a deterministic product safety constraint. When it
contains `decision.required_unit`, use that unit for a unitless document. Do
not override it from labels, watermarks, titles or a bare model convention.
Explicit source unit labels still win.

An assembly is:

`{"assembly_id":"assembly-N","assembly_role":"box_carcass|drawer_bank|vertical_panel|shelf_stack|table|countertop|facade_set","quantity":positive_integer,"evidence_refs":[...],"dimensions":{...},"counts":{...},"front_groups":[...],"exposure":{},"material_roles":[...]}`

Every `evidence_refs`, `geometry_evidence_refs` and source-material
`evidence_refs` value must be copied exactly from one supplied
`source_evidence_ref` or OCR `block_ref`. Never use a page label, `page-N`, a
Dimension Graph `dimension_id`, a view id, a segment id, an assembly id or a
description as an evidence reference.

Decompose the fixed object into large physical assemblies only. Do not list
finished panels, drawer sides, backs or bottoms. The deterministic composer
will derive conventional structural panels from the assembly topology.

`dimensions` contains each applicable `width`, `height`, or `depth` as:

`{"value":positive_number,"unit":"mm|cm|m|null","unit_basis":"explicit_source|document_convention_assumption|null","basis":"source|derived|assumption","evidence_refs":[...],"assumption_reason":"string|null"}`

For example, if a width label is `158` in a centimetre drawing, return
`{"value":158,"basis":"source","evidence_refs":[...]}`. Do not convert it.
Set `unit_basis=explicit_source` only when that individual axis prints its
unit. If its unit merely follows document convention, use
`document_convention_assumption`. A bare `unit="mm"` is not evidence by
itself.
The estimate must remain usable when a dimension is absent. First use an
explicit source dimension. If it is absent, derive a compatible dimension from
the same physical cabinet block or an unambiguous repeated cabinet depth. If
that still fails, return an `assumption` with no evidence refs and a short
reason. Never omit an otherwise visible cabinet because one size is missing.
The system applies named conventional panel-thickness assumptions after this
response. Do not infer precision shop-cut gaps.

## 2VN: view interpretation plus numeric witness

Before assigning a cabinet width, height or depth, return the bounded visual
view interpretation and its link to a Dimension Graph number. This is not a
shop drawing. It is the evidence bridge that prevents a nearby number from
becoming a global cabinet dimension.

`view_interpretations` is optional only when this batch contains no usable
view. Each item is
`{"view_id":"pN-view-NNN","projection":"front_elevation|side_elevation|top_plan|section|isometric|unknown","horizontal_axis":"width|depth|null"}`.
Use a supplied Dimension Graph view id exactly. A front elevation maps
horizontal to width and vertical to height. A side elevation maps horizontal
to depth and vertical to height. A top plan must explicitly state whether its
horizontal direction is width or depth. Isometric views may confirm a cabinet
or operating front but never provide the sole numeric axis.

`dimension_bindings` contains one item for each dimension used for a cabinet
axis when possible:
`{"assembly_id":"...","axis":"width|height|depth","view_id":"pN-view-NNN","local_orientation":"horizontal|vertical","dimension_id":"dimension-NNN","resolution":"direct|cross_view|linked_zone|assumption"}`.
`dimension_id` must be a supplied Dimension Graph id, never an invented id.
Use `direct` only if the printed number and its extension/dimension context
measure that axis in the named view. Use `cross_view` if another orthographic
view of the same cabinet supplies it. Use `linked_zone` for a depth copied
from a visibly corresponding cabinet zone. Do not bind a decorative screen,
slat panel or neighbouring object to a drawer-bank dimension. If no valid
binding exists, still return the dimension as a derived or assumption value,
but omit its binding. The deterministic 2VN resolver records the fallback.

`counts` may contain only shown or strongly supported integers: `drawers`,
`shelves`, `facades`, `top_layers`, `legs`.

Use `front_groups` only for a visibly operable cabinet front. A group is
`{"front_kind":"drawer_front|hinged_facade|lift_up_facade","quantity":positive_integer,"arrangement":"stacked|side_by_side"}`.
`stacked` means fronts share the block width and divide its height. `side_by_side`
means they share the block height and divide its width. Count fronts only once
from the canonical elevation. A perspective view may confirm a group but never
duplicates it. `drawer_front` describes a physical drawer, `hinged_facade` a
vertical door, and `lift_up_facade` a horizontal flap.

Classify operability before counting any hardware. A rectangle, seam, repeated
panel or vertical strip is not automatically a front. It must visibly close a
cabinet opening and have a coherent operating form in the canonical elevation.

- A lower, shallow, landscape row of rectangular faces is a `drawer_bank`.
  Keep it separate from any tall cabinet or screen above it. Put its actual
  number in `counts.drawers` and one `drawer_front` group. Side-by-side lower
  drawers use `arrangement:"side_by_side"`; vertically stacked drawers use
  `arrangement:"stacked"`.
- A tall, portrait leaf is `hinged_facade` only when it is visibly a door that
  closes a cabinet bay. A visible door boundary, handle, hinge cue, or enclosed
  storage opening is supporting evidence. Do not call a tall strip a door just
  because several strips repeat.
- A landscape flap that closes an upper or middle cabinet opening is a
  `lift_up_facade`, never a hinged vertical door.
- Repeated tall narrow slats, screens, dividers, open shelving uprights,
  decorative overlays and fixed carcass panels are structural material, not
  operable fronts. Represent their material as a `vertical_panel`,
  `shelf_stack`, or `box_carcass` as appropriate, with no `front_groups` and
  no hinge, gas-lift or drawer-slide role.

When the drawing is incomplete, keep the estimate approximate, but prefer a
fixed structural panel over invented operating hardware. Do not manufacture a
hinge, gas lift or drawer slide to explain a repeated rectangular pattern.

`exposure` is optional and only declares externally visible carcass ends, for
example `{"left":true,"right":false}`. A facade/front and an exposed end use
the visible material. Hidden carcass, shelves and drawer structure use the
internal material. Backing is separate. A worktop remains a separate
`countertop` assembly.

Only for historical scopes without construction_version, `material_roles` may contain `visible_sheet`, `internal_sheet`,
`backing_sheet`, `worktop_sheet`, `finish`, `drawer_slide`, `hinge`, `gas_lift`,
`leg`. Every role
is `{"role":"...","source_name":"...","family":"one allowed family code","specification":{},"basis":"source_evidence|construction_assumption","evidence_refs":[...]}`.
The model may select a construction-assumption family from the supplied allowed
families when the document has no material text. Do not emit a thickness unless
the drawing explicitly states it. Do not emit a material role that has no
physical use in the assembly.

For a construction assumption, `source_name` must name the material, never the
assembly or part. Never write `Cabinet Carcass`, `Facade`, `Seat/Worktop` or
`Table Leg` as a material. Inspect the supplied pixels for surface appearance:
choose the closest material description such as `Veneered MDF`, `Painted MDF`,
`LDSP`, `Solid wood panel` or `Furniture leg`. If a painted surface is visibly
intended, use an MDF/HDF board plus a separate `finish` role from
`paint_lacquer_stain`. If appearance is not distinguishable, choose the most
conservative compatible board material and state no false source claim.

Do not emit a hardware count as separate rails or struts. The deterministic
composer derives one drawer-slide purchase set per `drawer_front`, individual
hinges from `hinged_facade` height, and one gas-lift purchase set per
`lift_up_facade`. It also supplies `floor((cabinet_depth_mm - 100) / 100) *
100` as the drawer-slide depth. Do not select a catalog item or price.

Use `secondary_items` only for an explicitly countable shown fitting outside
an assembly: `{"secondary_id":"secondary-N","role":"drawer_slide|hinge|gas_lift|leg","quantity":positive_integer,"evidence_refs":[...],"material":{...}}`.
Do not manufacture rails, fasteners, handles, minor trim or decorative overlays.
List intentionally uncounted visible things in `omissions`.

`coverage` is optional audit metadata. If useful, return entries in this form:

`{"region_id":"pN-region-NNN","disposition":"assembly|secondary_item|excluded","target_id":"assembly-N|secondary-N|null","reason":"..."}`

If returned, use `assembly` for a visible material-bearing structural zone, including
drawers, fronts, tops, carcasses, panels, screens and legs. Use
`secondary_item` for a separately countable fitting. `excluded` is valid only
for `unshown_fasteners`, `minor_unmeasured_trim`, `reference_only` or
`non_material_annotation`. Missing coverage must not suppress an otherwise
supportable assembly. If
its construction is unclear, create the closest supported approximate assembly
and state the construction assumption in that assembly rather than excluding it.

For source and derived dimensions cite exact source evidence refs. For an
assumption cite no dimension evidence and provide a concise reason. A source
material may use `source_evidence` only when the document identifies it.
Otherwise use `construction_assumption` and choose only from
`allowed_material_families`.

Do not turn repeated visible elements into drawers, shelves or facades unless
their construction is supported by source context. Do not split a finished
component merely to fit a purchasable sheet.
