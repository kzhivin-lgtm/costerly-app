# Labor construction templates v0

Status: deterministic object-to-work specification. These templates are the
only approved way for the future Estimation Agent to derive standard panel,
edge, joint, hardware, and work quantities from an architectural object.

They are not CAD drawings and do not claim fabrication-level exactness. A
template makes a stable, inspectable construction assumption. If an object does
not fit a template with sufficient evidence, it returns `review` rather than a
false detailed estimate.

## Required object facts

Every template requires: `quantity`, `width_mm`, `depth_mm`, `height_mm`,
`material_family`, `thickness_mm`, `visible_finish`, `installation_scope`, and
`route preference` where stated. Missing dimensions can use a declared size
class only when the source explicitly identifies that class. Otherwise: review.

## Connection profiles

Templates do not choose joinery ad hoc. A profile is selected by Company Profile
later, with `panel_screw_standard` as the global v0 baseline.

| Profile | Per panel-to-panel connection | Derived output |
| --- | --- | --- |
| `panel_screw_standard` | 2 screws, 2 face holes, 2 receiving holes | 2 hardware items, 4 drilling events |
| `confirmat` | 2 confirmats, 2 face holes, 2 receiving holes | 2 hardware items, 4 drilling events |
| `cam_dowel` | 2 cams plus 2 dowels | 4 hardware items, 6 drilling events |
| `dowel_glue` | 2 dowels and glue | 2 hardware items, 4 drilling events, glue-up flag |
| `metal_welded` | one welded joint | weld path and joint class required |
| `metal_bolted` | 2 bolts, holes and washers | 2 hardware items, 4 drilling events |

The default is not a hidden company fact. Every estimate records the selected
profile and marks default use as `inferred`.

## Derived primitives

Templates output only these primitives, which feed the formula catalog:

- `panel(width, height, count, edge_mask, material, thickness)`
- `solid_member(section, length, count, profile_class)`
- `sheet_metal_part(alloy, thickness, contour, bends, holes)`
- `metal_member(section, length, count, bends, weld_paths)`
- `front(width, height, count, hardware_family)`
- `drawer(width, depth, height, count, system)`
- `connection(profile, count)`
- `finish_surface(area, system, coats)`
- `purchased_component(type, dimensions, finish, installation_scope)`

The engine calculates surface, exposed edge, contour, drill, hardware, weld,
and finishing quantities from primitives. The extraction agent may identify a
primitive or select a template, but cannot return an arbitrary quantity that
does not reconcile to primitives.

## Panel furniture templates

| Template | Required specific facts | Deterministic primitives | Default operation consequences |
| --- | --- | --- | --- |
| `base_cabinet_open` | W, D, H, shelf count, toe-kick yes/no | 2 sides `D x H`, top `W x D`, bottom `W x D`, back `W x H`, `n` shelves `W x D`, toe-kick panels if selected | panel cutting, edge banding from edge masks, carcass assembly, connections `4 + 2n` |
| `base_cabinet_hinged` | base cabinet facts, door count 1 or 2 | `base_cabinet_open` plus fronts split by door count, 2 hinges per door by default | add front fitting, hardware installation, hinge-cup drilling |
| `base_cabinet_drawers` | W, D, H, drawer count | carcass plus `n` drawer boxes and `n` fronts | drawer assembly, runner hardware, front fitting |
| `wall_cabinet_open` | W, D, H, shelf count | 2 sides `D x H`, top/bottom `W x D`, back `W x H`, `n` shelves | carcass assembly, wall-anchor flag, connections `4 + 2n` |
| `wall_cabinet_hinged` | wall cabinet facts, door count | `wall_cabinet_open` plus fronts and hinge sets | add front fitting, hardware, hinge drilling |
| `tall_cabinet` | W, D, H, shelf count, door/drawer configuration | two full sides, top/bottom, back, shelves, selected fronts/drawers | panel route, carcass, front/drawer operations, installation anchors |
| `open_shelving_unit` | W, D, H, shelf count, back yes/no | 2 sides, top/bottom, `n` shelves, optional back | carcass assembly, connections `4 + 2n`, no front route |
| `sliding_door_wardrobe` | W, D, H, interior type, door count | carcass primitives plus 2 or 3 fronts and sliding track set | panel route, hardware install, door fitting, track drill pattern |
| `vanity_cabinet` | cabinet type, W, D, H, plumbing cutout yes/no | base template plus plumbing cutout primitive and countertop component | panel route, optional CNC/manual cutout, cabinet install, countertop external component |
| `reception_or_custom_counter` | W, D, H, return length, storage modules | decomposes into named base/wall/open modules plus counter panel | only accepted if modules can be enumerated, otherwise review |

## Tables and free-standing wood furniture

| Template | Required specific facts | Deterministic primitives | Default operation consequences |
| --- | --- | --- | --- |
| `panel_table` | tabletop W/D/thickness, leg count, apron yes/no | one tabletop, selected legs, optional apron members, connection count by leg count | panel or solid route, edge/finish, assembly |
| `solid_wood_table` | tabletop W/D/thickness, leg section, apron configuration | glued top staves or purchased laminated panel, 4 legs, apron members | solid preparation, glue-up if raw stock, profiling, sanding, finish, assembly |
| `bench_panel` | W, D, H, support count | seat panel, 2 or more supports, optional stretcher | panel cutting, edges, connections, assembly |
| `solid_wood_bench` | W, D, H, leg section, stretcher | seat members, legs, stretchers, joints | solid preparation, joinery profile, sanding, assembly |
| `wall_shelf` | W, D, thickness, bracket type/count | shelf panel plus bracket hardware and anchor count | panel route, edge, hardware, site anchoring if install scope |

## Metal and mixed-material templates

| Template | Required specific facts | Deterministic primitives | Default operation consequences |
| --- | --- | --- | --- |
| `metal_table_frame` | W, D, H, profile section, welded/bolted, top type | 4 legs, perimeter/apron members, cross members when selected, joint paths | profile cutting, assembly, MIG or TIG by alloy/finish, grinding/polishing, coating, tabletop route |
| `metal_shelf_frame` | W, D, H, shelf levels, profile section | uprights, front/back/side rails per level, shelf supports | profile cutting, joints by levels, welding or bolting, coating, panel shelf primitives |
| `sheet_metal_box` | W, D, H, alloy, thickness, open face yes/no | one flat sheet-metal part with derived perimeter, `4` bends for closed box, holes/cutouts only if explicit | laser or shear, press-brake, optional weld/grind, coating |
| `metal_bracket` | dimensions, alloy, thickness, bends, anchors | one sheet-metal part, bend count, anchor holes | laser/punch, press-brake, coating, site anchoring if install scope |
| `glass_metal_display` | W, D, H, frame section, glass panel count | metal frame plus purchased glass components | metal route, purchased glass, assembly, glass installation when scoped |
| `stone_top_on_base` | countertop geometry, material, sink/cooktop cutouts, base template | purchased stone component with edge and cutout requirements plus cabinet base | external stone component, base-cabinet route, countertop install if scoped |

## Template selection protocol

1. Extraction returns candidate template, object facts and evidence references.
2. Deterministic validator checks dimensions, required facts, material and
   compatible construction profile.
3. Validator either emits primitives or `review` with missing/contradictory
   facts. It never silently changes a template.
4. Route engine selects in-house, manual, external, or site work for each
   primitive.
5. Formula engine converts only emitted primitives into labor hours.

## Explicit V0 limits

- Upholstered furniture, curved/freeform joinery, rattan, complex carved work,
  electrical mains work, and unsupported mechanisms return `review`.
- A photo or rendering without dimensions cannot generate panel cut lists.
- The templates do not replace a company shop drawing. They make a documented
  estimating assumption suitable for custom-furniture quotation.
