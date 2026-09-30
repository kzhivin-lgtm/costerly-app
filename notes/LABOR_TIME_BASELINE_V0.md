# Global labor-time baseline v0

Status: working estimation baseline. This is not a universal production norm.
It supplies the first deterministic minutes for every active operation before
company observations exist. All values are productive elapsed minutes.

Each line is `setup + quantity * variable rate`. The engine charges setup once
per compatible batch, never once per part. Calendar waits such as glue cure,
powder cure, supplier queue, or delivery lead time are excluded from labor.

Evidence status:

- `R`: source-backed formula or observed process. Confidence 60.
- `E`: equipment-bound physical model, with setup or handling derived.
  Confidence 40.
- `D`: Costerly derived operating prior. Confidence 25. It is usable for a
  first estimate but must be superseded by measured company data.

The `Evidence` cell is a compact provenance marker for the entire row. Exact
source keys and URLs are below. A row never inherits confidence from a similar
operation, material, or machine.

The values below deliberately use a normal small custom-furniture workshop,
not a mass-production line. Automatic machinery routes use the machine where
the company profile has that capability. Otherwise route selection chooses the
manual or external component route.

| Operation | Standard unit | Setup min | Variable min/unit | Evidence | Basis |
| --- | --- | ---: | ---: | --- | --- |
| `site_measurement` | room zone | 15 | 20 | D | access, dimensions, photographs, documented exceptions |
| `estimate_review` | object | 4 | 8 | D | scope and evidence review |
| `shop_drawing` | unique object/module | 10 | 25 | D | fabrication drawing, part schedule, tolerances |
| `cnc_programming` | CNC batch | 10 | 12 | D | CAM preparation after template selection |
| `sheet_nesting` | sheet | 4 | 3 | R | nesting is distinct from machining in custom MDF/plywood production |
| `supplier_quotation` | supplier package | 5 | 8 | D | request, comparison, and recorded selection |
| `quality_inspection` | finished module | 3 | 4 | D | dimensional, finish, and hardware check |
| `panel_material_handling` | panel part | 3 | 0.8 | D | stage, label, move, and sort |
| `panel_saw_cutting` | cut sequence | 6 | 0.45 | E | saw positioning and cut, not sheet count |
| `cnc_router_profile_cutting` | contour metre | 12 | 0.35 | E | load/setup shared in router session, variable contour run |
| `cnc_vertical_drilling` | vertical hole | 12 | 0.12 | E | drill pattern and hole cycle, shared router session |
| `cnc_horizontal_drilling` | end hole | 10 | 0.20 | E | position, clamp, bore |
| `cnc_grooving` | groove metre | 12 | 0.45 | E | router pass with tool setup shared in router session |
| `cnc_pocketing` | pocket area 100 cm2 | 12 | 0.75 | E | router removal pass, depth class handled by recipe |
| `manual_panel_cutting` | cut sequence | 8 | 1.4 | D | low-volume straight cut with positioning |
| `manual_drilling` | hole | 6 | 0.45 | D | mark, position, drill, clear chips |
| `manual_routing` | routed metre | 8 | 1.5 | D | guided pass, repositioning, and inspection |
| `edge_banding` | edged metre | 8 | 0.55 | R | edge treatment is a separate panel-furniture stage |
| `veneer_lamination` | pressed panel m2 | 18 | 6 | D | substrate prep, glue spread, layup, press handling |
| `solid_wood_ripping` | linear metre | 8 | 0.55 | R | solid-timber cutting is separate from panel operations |
| `solid_wood_crosscutting` | cut | 6 | 0.65 | R | stock positioning and crosscut cycle |
| `solid_wood_jointing_planing` | linear metre | 10 | 0.9 | D | face and edge passes, section control |
| `solid_wood_profiling` | profiled metre | 14 | 1.15 | D | fence/tool adjustment, profile passes |
| `solid_wood_glueup` | glue joint metre | 12 | 2.2 | D | dry layout, glue, clamp, squeeze-out removal |
| `wood_sanding` | surface m2 | 8 | 12 | D | flat surface and accessible edges, grit class in recipe |
| `carcass_assembly` | cabinet module | 5 | 16 | D | standard 4-6 panel carcass, excludes fronts/hardware |
| `drawer_assembly` | drawer box | 3 | 11 | D | assemble, square, fasten, basic fit check |
| `door_front_fitting` | door or drawer front | 3 | 8 | D | mount, reveal adjustment, functional check |
| `hardware_installation` | hardware item | 3 | 2.5 | D | standard hinge, runner, handle, or connector |
| `workshop_dry_fit` | assembled module | 5 | 8 | D | trial fit and adjustment before release |
| `sheet_laser_cutting` | cut metre | 10 | 0.28 | R | 4 mm carbon steel reference: 3.6 m/min, plus separate pierce time |
| `sheet_shearing` | straight cut | 8 | 0.7 | D | station routine confirms separate load, shear and walking components |
| `metal_profile_cutting` | cut | 8 | 1.2 | D | measure, clamp, saw, deburr. Material-specific feed correction below |
| `metal_drilling` | hole | 8 | 0.6 | D | rigid jig, positive feed, coolant. Stainless correction below |
| `metal_milling` | milling path metre | 15 | 0.6 | D | toolpath and tool-change based. Stainless correction below |
| `metal_punching` | punched feature | 10 | 0.25 | E | stroke and reposition, setup shared by tooling |
| `sheet_metal_bending` | bend | 12 | 0.08 | R | 4-6 sec/bend, with a separate 3-4 sec flip event when required |
| `metal_profile_bending` | bend | 20 | 3.5 | D | die/radius selection, trial and controlled bend |
| `metal_rolling` | rolled part | 20 | 7 | D | radius setup, repeated pass, verification |
| `mig_mag_welding` | weld metre | 8 | 4.55 | R | 220 mm/min 4 mm fillet reference, tack/setup separate |
| `tig_welding` | weld metre | 12 | 12 | D | cosmetic or thin stainless route, intentionally slower than MIG |
| `metal_grinding` | weld metre | 5 | 2.8 | D | carbon-steel structural blend. Stainless correction below |
| `metal_polishing` | exposed surface m2 | 8 | 28 | D | carbon-steel or non-cosmetic finish. Stainless correction below |
| `metal_assembly` | fabricated subassembly | 8 | 10 | D | fit, align, tack or mechanically fasten frame elements |
| `glass_cutting` | straight cut | 8 | 0.7 | D | score, break, safe handling |
| `glass_edge_processing` | edge metre | 10 | 2.5 | D | grind/polish edge pass |
| `glass_drilling` | hole | 8 | 2.0 | D | locate, bore, cool, inspect |
| `glass_tempering` | glass batch m2 | 10 | 1.5 | D | rack/unrack only, external lead time excluded |
| `stone_cutting` | cut metre | 20 | 1.1 | R | bridge-saw reference is about 2 m/min, baseline includes handling allowance |
| `stone_edge_processing` | edge metre | 15 | 8 | D | profile and polish to standard edge |
| `stone_cutout` | cutout | 12 | 18 | D | set-out, CNC/waterjet path, finishing |
| `stone_seaming` | seam metre | 15 | 22 | D | align, bond, finish, inspect |
| `acrylic_cnc_machining` | contour metre | 10 | 0.45 | E | clamp/load plus controlled router pass |
| `acrylic_laser_cutting` | cut metre | 8 | 0.08 | E | setup, cut, protective-film handling |
| `acrylic_thermoforming` | formed part | 18 | 12 | D | heat, form, cool handling, excludes passive cooling |
| `finish_surface_preparation` | finish surface m2 | 8 | 11 | D | clean, fill, mask, final prep |
| `wood_staining` | finish surface m2 | 8 | 6 | D | apply, work in, wipe/equalize |
| `wood_priming` | finish surface m2 per coat | 10 | 7 | D | spray/application and rack handling |
| `wood_lacquering` | finish surface m2 per coat | 10 | 8 | D | coat, rack, gun clean allowance |
| `wet_spray_painting` | finish surface m2 per coat | 12 | 9 | D | booth setup, spray, rack handling |
| `powder_coating_preparation` | coated part | 8 | 3.5 | D | clean, mask, rack and un-rack |
| `powder_coating_application` | coated part | 10 | 2.5 | D | spray and oven loading, cure is calendar time |
| `sandblasting` | surface m2 | 10 | 7 | D | mask, blast, blow-down |
| `galvanizing` | external batch kg | 8 | 0.5 | D | dispatch, rack coordination, inspection only |
| `protective_packaging` | finished module | 3 | 7 | D | wrap, corner protect, label, stage |
| `vehicle_loading` | packed module | 5 | 3 | D | carry, load, secure |
| `delivery_trip` | route km | 15 | 1.4 | D | drive time baseline, traffic class applied separately |
| `manual_site_carry` | packed module / floor | 3 | 2.5 | D | carry from vehicle to work zone per floor equivalent |
| `site_protection` | work zone m2 | 8 | 1.2 | D | cover and tape accessible protection |
| `cabinet_installation` | cabinet module | 8 | 18 | D | set, level, connect, secure, excludes countertop |
| `countertop_installation` | countertop piece | 15 | 25 | R | standard installation uses two people and is typically half a day for kitchen |
| `metalwork_installation` | metalwork subassembly | 10 | 18 | D | position, level, secure |
| `glass_mirror_installation` | glass or mirror panel m2 | 10 | 15 | D | lift, position, fix, safe clean |
| `site_anchoring` | anchor | 5 | 2.2 | D | locate, drill, install, verify |
| `site_sealing` | seal metre | 5 | 1.1 | D | mask where required, dispense, tool, clean |
| `led_low_voltage_installation` | LED metre | 12 | 5 | D | profile, strip, wire, test, excludes mains electrical work |
| `final_adjustment` | installed module | 3 | 6 | D | align fronts, test hardware, record defects |
| `site_cleanup` | work zone m2 | 5 | 1.0 | D | remove debris and temporary protection |

## Mandatory interpretation rules

1. A setup applies once to a batch key, not once to every unit.
2. A company with the relevant machine uses its in-house route. Without it,
   the engine uses an approved external component or manual route. It does not
   charge both routes.
3. `R` evidence validates the operation structure or physical driver. It does
   not make a foreign factory's observed productivity a global promise.
4. `D` values are v0 calibration priors, not claims of measured facts. They
   must be replaceable by company observations without changing the formula.
5. The estimator will use `typical` values first. Low and high bounds are the
   next task, derived from material, complexity, access, and evidence quality.

## Provenance registry

| Marker | Confidence | Applies to | Exact origin |
| --- | ---: | --- | --- |
| `D` | 25 | Every row marked `D` | `D-01`, Costerly derived prior v0, decomposed from the named unit, setup and handling actions. No external minute norm is claimed. |
| `E` | 40 | Every row marked `E` | `E-01`, Costerly equipment-bound model v0. Formula driver is physically defined but setup and attendance are priors. |
| `R` | 60 | `sheet_nesting`, `edge_banding` | `R-01`, [panel furniture production process research](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0339912), supplemented by [custom kitchen machining study](https://www.sciencedirect.com/science/article/pii/S2351978919310534) |
| `R` | 60 | `solid_wood_ripping`, `solid_wood_crosscutting` | `R-02`, [solid-timber motion study](https://ojs.uajy.ac.id/index.php/JTIMR/article/view/7034). It validates operation separation, not the exact global minute coefficient |
| `R` | 70 | `sheet_laser_cutting`, carbon 4 mm row | `R-03`, [laser-cut formula and worked example](https://eziil.com/job-costing-custom-metal-fabrication-free-calculator/) |
| `R` | 70 | `sheet_metal_bending`, carbon-steel row | `R-03`, same source, 4-6 seconds per bend and 3-4 seconds per flip |
| `R` | 70 | `mig_mag_welding`, carbon-steel row | `R-03`, same source, 220 mm/min fillet-weld example plus setup |
| `R` | 60 | `stone_cutting` | `R-04`, [European Commission countertop fabrication process](https://susproc.jrc.ec.europa.eu/product-bureau/sites/default/files/contentype/product_group_documents/1581681927/PR_v1-0_14-11-2018.pdf), bridge-saw feed reference |
| `R` | 60 | `countertop_installation` | `R-05`, [countertop fabrication and installation benchmark](https://www.stonify.io/industry-knowledge/fabrication-process-overview) |

### Material-specific evidence modifiers

These sources do not turn a `D` row into a measured minute norm. They explain
why the stainless route is distinct and why its baseline is slower.

| Key | Applies to | Source |
| --- | --- | --- |
| `M-01` | stainless drilling and milling | [British Stainless Steel Association](https://bssa.org.uk/bssa_articles/speeds-and-feeds-for-drilling-and-reaming-stainless-steels/), work hardening, rigid workholding, positive feed, depth-related reduction |
| `M-02` | stainless TIG, grinding, polishing, tube work | [World Stainless finishing guide](https://worldstainless.org/wp-content/uploads/2025/02/MechanicalFinishing_EN.pdf), decorative TIG route and controlled post-weld finishing |
| `M-03` | laser, bending, loading and welding-cell structure | [2024 production-system study](https://mdpi-res.com/bookfiles/book/11170/Design_and_Optimization_of_Manufacturing_Systems_2nd_Edition.pdf?v=1751635879) |

## Metal material and route corrections

These rows replace the generic metal value whenever the material and route are
known. They are not additive. `carbon_steel` includes ordinary mild and
low-alloy structural steel. `stainless_304_316` is the architectural-furniture
baseline. Other grades require review.

| Operation | Material and route | Setup min | Variable min/unit | Evidence | Reason |
| --- | --- | ---: | ---: | --- | --- |
| `sheet_laser_cutting` | carbon steel, 4 mm, fiber laser | 10 | 0.28 min/lm + 0.01 min/pierce | R | 3.6 m/min and 0.6 s/pierce published custom-fabrication example |
| `sheet_laser_cutting` | stainless 304/316, thin sheet | 12 | 0.40 min/lm + 0.015 min/pierce | D | conservative slower baseline pending laser power, gas and thickness table |
| `metal_profile_cutting` | carbon steel, bandsaw | 8 | 1.2 min/cut | D | clamp, cut and deburr sequence |
| `metal_profile_cutting` | stainless 304/316, bandsaw | 10 | 1.6 min/cut | D | lower cutting speed and coolant discipline to avoid work hardening |
| `metal_drilling` | carbon steel, drill press | 8 | 0.6 min/hole | D | locate, clamp, drill, deburr |
| `metal_drilling` | stainless 304/316, drill press | 10 | 0.9 min/hole | D | rigid jig, positive feed, chip clearing and reduced deep-hole feed |
| `metal_milling` | carbon steel, manual or CNC mill | 15 | 0.6 min/lm | D | toolpath-driven, excludes setup duplication |
| `metal_milling` | stainless 304/316, manual or CNC mill | 18 | 0.9 min/lm | D | lower cutting speed, coolant and work-hardening control |
| `sheet_metal_bending` | carbon steel, press brake | 12 | 0.08 min/bend + 0.06 min/flip | R | published 4-6 s/bend and 3-4 s/flip range |
| `sheet_metal_bending` | stainless 304/316, press brake | 15 | 0.11 min/bend + 0.06 min/flip | D | slower positioning and springback control prior |
| `metal_profile_bending` | carbon steel, known die/radius | 20 | 3.5 min/bend | D | material, section and radius specific |
| `metal_profile_bending` | stainless 304/316, known die/radius | 25 | 5.0 min/bend | D | higher springback and tool-control allowance |
| `metal_rolling` | carbon steel, known radius | 20 | 7 min/part | D | multiple passes and verification |
| `metal_rolling` | stainless 304/316, known radius | 25 | 10 min/part | D | conservative additional passes and surface protection |
| `mig_mag_welding` | carbon steel, structural fillet | 8 | 4.55 min/lm | R | 220 mm/min published model |
| `mig_mag_welding` | stainless, non-cosmetic | 10 | 5.5 min/lm | D | lower productive speed, gas and heat control |
| `tig_welding` | stainless, visible or thin work | 12 | 12 min/lm | D | TIG is the specified precision route for decorative stainless, slower than MIG |
| `metal_grinding` | carbon steel, structural | 5 | 2.8 min/lm | D | weld blending only |
| `metal_grinding` | stainless, visible weld | 8 | 5.5 min/lm | D | controlled localized dressing to protect surrounding finish |
| `metal_polishing` | carbon steel, non-cosmetic | 8 | 28 min/sqm | D | ordinary surface preparation |
| `metal_polishing` | stainless, brushed/satin visible finish | 12 | 55 min/sqm | D | progressive manual blending and matching of surrounding finish |
| `metal_assembly` | carbon steel frame | 8 | 10 min/subassembly | D | fit, align, tack and check square |
| `metal_assembly` | stainless visible frame | 12 | 16 min/subassembly | D | protected handling, fit-up and cosmetic-weld access |

## Sources used for formula structure and sanity checks

- Gawronski, 2012, https://link.springer.com/article/10.1007/s10479-012-1233-z
- Machining Operations for Components in Kitchen Furniture, 2019,
  https://www.sciencedirect.com/science/article/pii/S2351978919310534
- PLOS One, `A practical optimization method for enhancing drilling efficiency
  in panel furniture manufacture`, 2025,
  https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0339912
- Uysal et al., 2019, https://bioresources.cnr.ncsu.edu/resources/manufacturing-feasibility-analysis-and-load-carrying-capacity-of-computer-numerical-control-cut-joints-with-interlocking-assembly-feature/
- Eziil sheet-metal formula guide, 2025,
  https://eziil.com/job-costing-custom-metal-fabrication-free-calculator/
- Kruk et al., `Design and Optimization of Manufacturing Systems`, 2024,
  https://mdpi-res.com/bookfiles/book/11170/Design_and_Optimization_of_Manufacturing_Systems_2nd_Edition.pdf?v=1751635879
- British Stainless Steel Association, drilling and reaming guidance, 2026,
  https://bssa.org.uk/bssa_articles/speeds-and-feeds-for-drilling-and-reaming-stainless-steels/
- World Stainless, `The Mechanical Finishing of Decorative Stainless Steel
  Surfaces`, 2025,
  https://worldstainless.org/wp-content/uploads/2025/02/MechanicalFinishing_EN.pdf
- European Commission countertop process description, 2018,
  https://susproc.jrc.ec.europa.eu/product-bureau/sites/default/files/contentype/product_group_documents/1581681927/PR_v1-0_14-11-2018.pdf
