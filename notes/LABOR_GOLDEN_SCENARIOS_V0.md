# Labor golden scenarios v0

Status: acceptance matrix for the future deterministic labor engine. These are
not benchmark prices and do not invoke the legacy Estimation Agent.

Every scenario verifies, in order: template selection, primitive derivation,
route selection, operation emission, labor role allocation, and exclusions.
The engine must retain each intermediate result as an explainable trace.

## S01: Base cabinet, internal panel-saw route

Input: one `base_cabinet_open`, W600 D560 H720, one shelf, 18 mm melamine,
5 mm back, `panel_screw_standard`, exposed front edges, company has panel saw
and edge bander but no CNC router, supply and installation are included.

Expected primitives: 2 sides, top, bottom, back, one shelf. Six structural
connections, 12 screws, 24 drilling events. Two site anchors.

Expected operations: panel handling, sheet nesting, panel-saw cutting,
manual drilling, edge banding, carcass assembly, hardware installation,
quality inspection, packaging, loading, delivery, site protection, cabinet
installation, site anchoring, final adjustment, cleanup.

Must not emit: any CNC operation, subcontracted CNC component, door fitting,
drawer assembly, countertop work.

## S02: Hinged wall cabinet, internal CNC route

Input: one `wall_cabinet_hinged`, W800 D320 H720, two shelves, two doors,
18 mm melamine, HDF back, `cam_dowel`, company has CNC router and edge
bander, no installation scope.

Expected primitives: carcass parts, 2 shelves, back, 2 fronts, 8 structural
connections, 16 cams, 16 dowels, 48 drilling events, 4 hinges.

Expected operations: sheet nesting, CNC router profile session, vertical
drilling, edge banding, carcass assembly, hardware installation, door/front
fitting, quality inspection and packaging.

Must not emit: panel-saw cutting, manual drilling, any subcontractor CNC line,
site work or installation hours.

## S03: Drawer vanity, panel saw with plumbing cutout

Input: one `vanity_cabinet`, W900 D500 H800, three drawers, 18 mm moisture-
resistant board, plumbing cutout explicitly shown, panel saw and edge bander,
no CNC router, stone top supplied by external fabricator, installation scope.

Expected operations: panel-saw cutting, manual drilling, edge banding,
carcass assembly, drawer assembly, runner hardware installation, external
stone countertop component including its cutout, packaging and installation.

Must not emit: internal stone cutting, internal stone cutout, CNC pocketing,
or a second countertop installation if supplier installation is selected.

## S04: Solid oak dining table

Input: one `solid_wood_table`, W1800 D900 H750, 40 mm top assembled from raw
oak staves, four 70 x 70 mm legs, apron, clear lacquer, internal solid-wood
preparation capability, manual finish route, delivery only.

Expected operations: solid ripping, crosscutting, jointing/planing, glue-up,
profiling where edge profile is explicit, sanding, table assembly, finish
preparation, lacquer coats, inspection, packaging, loading, delivery.

Must not emit: panel-saw cutting, edge banding, CNC operations unless an
explicit CNC profile is selected, installation work.

## S05: Carbon-steel welded table frame, powder coated

Input: one `metal_table_frame`, W1600 D800 H740, carbon-steel square tube,
welded construction, four legs, perimeter frame, two cross members, black
powder coating, company has profile saw and powder booth, installation absent.

Expected primitives: 4 legs, 4 perimeter members, 2 cross members, derived
mitre/cut list and weld-path list. Weld length must be traceable from the frame
joint geometry.

Expected operations: metal profile cutting, metal assembly, MIG/MAG welding,
structural grinding where specified, powder preparation and application,
inspection, packaging.

Must not emit: TIG, stainless polishing, laser cutting, press-brake bending,
or external powder component.

## S06: Visible stainless-steel frame

Input: one `metal_table_frame`, W1400 D700 H740, 304 stainless tube, welded,
brushed visible finish, four legs, perimeter frame, no coating, in-house
qualified welder but no declared stainless finishing capability.

Expected operations: profile cutting with stainless branch, metal assembly,
TIG welding, visible-weld grinding and polishing. The finishing route enters
`review` if the company lacks the required finishing capability.

Must not emit: carbon MIG defaults, powder coating, galvanizing, generic
carbon-steel grinding baseline.

## S07: Sheet-metal enclosure, external laser and internal press brake

Input: three `sheet_metal_box` parts, W400 D300 H200, 1.5 mm carbon steel,
closed box, two explicit cable cutouts each, company has press brake but no
sheet laser, powder coating is external.

Expected primitives per part: one unfolded sheet-metal part, perimeter, 4
bends, 2 cutouts. Across the batch: 12 bends, 6 cutouts.

Expected operations: one subcontracted laser purchased component, internal
sheet-metal bending, external powder component, incoming quality inspection.

Must not emit: internal sheet-laser labor or machine cost, sheet shearing,
manual drilling for laser-cut cable cutouts, or internal powder operations.

## S08: Stone top on installed cabinet base

Input: one `stone_top_on_base`, base cabinet W1200 D600 H850, quartz top,
one sink cutout, eased edge, supplier includes stone fabrication but not
installation, company installation scope includes cabinet and top.

Expected operations: base cabinet route, external stone component containing
cutting, edge and sink cutout, cabinet installation, two-person countertop
installation, site sealing, final adjustment.

Must not emit: internal stone cutting, edge processing, cutout, seaming, or
supplier countertop installation.

## S09: Glass and metal display cabinet

Input: one `glass_metal_display`, W1000 D400 H1800, powder-coated steel frame,
4 glass panels, company has profile saw, external glass supplier, installation
included.

Expected operations: metal frame route, external glass components, metalwork
installation, glass/mirror installation with crew escalation based on panel
area/weight, anchoring, final adjustment.

Must not emit: internal glass cutting, drilling or tempering; no duplicate
supplier and internal glass labor.

## S10: Delivery-only versus installation scope

Input A: S01 with `installation_scope = false`. Input B: identical object with
`installation_scope = true`.

Expected difference: B adds site protection, cabinet installation, anchors,
final adjustment and cleanup. A has packaging, loading and delivery only.
Fabrication labor and material quantities must be identical.

## Global acceptance invariants

1. Every emitted operation has one selected route, one baseline row, one
formula, one role allocation and a provenance marker.
2. No operation may appear twice through manual and machine, internal and
external, or supplier and company routes.
3. External components retain their required fabrication attributes, but emit
zero internal fabricator labor.
4. Every derived drilling, edge, weld and hardware quantity reconciles to a
template primitive and selected connection profile.
5. Changing only `installation_scope` cannot change workshop fabrication.
6. Missing dimensions, incompatible material, unsupported template, or absent
route produces a specific review reason, never a fabricated default.
