# Material Family Matrix, 3.17.1.3

Status: owner-accepted taxonomy design, implementation pending. It is an
additive taxonomy record and does not change Price Lists, source ingestion,
Estimation runtime, or database rows.

## Accepted rules

1. Production departments are `wood`, `metal`, `glass_plastics`, `stone`, and
   `coating`.
2. `entity_role` is independent of a production department: `material`,
   `hardware`, `consumable`, `packaging`, `purchased_fabricated_component`, or
   `supplier_service`.
3. `department_affinity` is one or more production contexts in which Hardware
   or Consumables are used. It is for retrieval and agent context only. It
   never determines identity, price, eligibility, route, or labor.
4. A material family's eligible operations depend on the family only. A
   primary or secondary identity attribute, including thickness, cannot add,
   remove, or require an operation.
5. No operation is mandatory. The Estimation Agent selects supported
   operations from the eligible set only when the particular object evidence
   and its inferred parts justify them.
6. Geometry and other physical facts determine operation quantities, route
   validation, and deterministic hours only after the Agent selected an
   operation.
7. Delivery and Installation are not Estimation Agent operations. Packaging
   has no production department and remains governed by the approved Packaging
   allowance unless a later explicit policy changes it.
8. Brand is optional structured evidence. `catalog` brands are curated,
   family-scoped recognition entries; `candidate` brands are preserved source
   evidence; `unknown` means absent evidence. A brand never classifies a row.

## Registry contract

Every row in the future registry must contain:

```text
production_department
entity_role
department_affinities
material_family
primary_attribute
allowed_secondary_attributes
eligible_operations
brand_scope
```

`eligible_operations` is a bounded set of `reference_operations.operation_code`.
It is not a work order, route, price list, or Labor Engine instruction.

## Current evidence baseline

- Active Israel global catalog: 4,448 canonical material rows, including the
  4,436-row V1 catalog plus 12 controlled wood-panel expansions.
- Active aliases: 8,872 English and Hebrew aliases.
- Current curated Brand Registry: 73 manufacturer/product-system brands and
  157 aliases. It is a useful evidence base, not proof that every market brand
  has been curated.
- Current operation catalog: 78 operations. The production-plan subset must
  exclude the ten Installation and three Logistics operations.

## Matrix construction order

1. Publish all family rows with attribute allowlists and operation eligibility.
2. Re-scope existing curated brands to the accepted five-department matrix.
3. Add brands only from verified manufacturer/product-system evidence, with
   aliases and a scoped family list. Supplier and distributor names do not
   qualify.
4. Validate representative source rows and object decompositions before any
   SQL migration or Agent contract change.

## Operation scopes

The registry deliberately separates three scopes. This prevents a material
record from silently creating unrelated work.

| Scope | Examples | Selection rule |
| --- | --- | --- |
| Material-family | cutting, drilling, bending, coating | listed below as eligible candidates only |
| Part or assembly | `carcass_assembly`, `drawer_assembly`, `door_front_fitting`, `hardware_installation`, `workshop_dry_fit` | Agent selects only when its inferred construction supports it |
| Object or production batch | `shop_drawing`, `cnc_programming`, `sheet_nesting`, `quality_inspection`, `supplier_quotation` | Agent selects only when its production evidence supports it |

Installation, Logistics, and Packaging remain outside the Estimation Agent
production plan. `supplier_cut_and_edge_banding` is retained only as a
supplier-service identity and is not an internal material-family operation.

## Material Family Registry draft

The values below are the proposed allowlists. The Agent may select zero or
more eligible operations. It may never infer a route, hours, price, or an
operation not in the selected family's set.

### Wood

| Family | Primary attribute | Allowed secondary attributes | Eligible material-family operations |
| --- | --- | --- | --- |
| MDF / HDF | thickness | grade, substrate, construction, finish, coating, colour, sheet dimensions | `panel_material_handling`, `panel_saw_cutting`, `cnc_router_profile_cutting`, `cnc_vertical_drilling`, `cnc_horizontal_drilling`, `cnc_grooving`, `cnc_pocketing`, `manual_panel_cutting`, `manual_drilling`, `manual_routing`, `edge_banding`, `veneer_lamination`, `wood_sanding`, `finish_surface_preparation`, `wood_priming`, `wood_lacquering`, `wet_spray_painting` |
| Faced MDF | thickness | grade, substrate, construction, surface, finish, coating, colour, sheet dimensions | MDF / HDF operations |
| Particleboard | thickness | grade, construction, surface, coating, colour, sheet dimensions | MDF / HDF operations |
| Melamine-faced particleboard | thickness | substrate, construction, surface, finish, coating, colour, sheet dimensions | MDF / HDF operations |
| Plywood / special plywood | thickness | species, grade, construction, finish, surface, coating, colour, sheet dimensions | MDF / HDF operations |
| OSB | thickness | grade, construction, finish, surface, coating, sheet dimensions | `panel_material_handling`, `panel_saw_cutting`, `cnc_router_profile_cutting`, `manual_panel_cutting`, `manual_drilling`, `manual_routing`, `wood_sanding`, `finish_surface_preparation`, `wood_priming`, `wood_lacquering`, `wet_spray_painting` |
| Fibreboard / hardboard | thickness | grade, construction, finish, surface, coating, colour, sheet dimensions | MDF / HDF operations |
| Lightweight / sandwich panel | thickness | core, face material, fire rating, construction, finish, surface, coating, colour, sheet dimensions | `panel_material_handling`, `panel_saw_cutting`, `cnc_router_profile_cutting`, `manual_panel_cutting`, `manual_drilling`, `manual_routing`, `edge_banding` |
| HPL / CPL | thickness | substrate, construction, finish, surface, colour, sheet dimensions | `panel_material_handling`, `panel_saw_cutting`, `cnc_router_profile_cutting`, `manual_panel_cutting`, `manual_routing`, `edge_banding` |
| Compact laminate | thickness | grade, construction, finish, surface, colour, sheet dimensions | `panel_material_handling`, `panel_saw_cutting`, `cnc_router_profile_cutting`, `manual_panel_cutting`, `manual_drilling`, `manual_routing`, `edge_banding` |
| Wood veneer | species | thickness, grade, construction, finish, surface, colour, sheet dimensions | `veneer_lamination`, `wood_sanding`, `finish_surface_preparation`, `wood_staining`, `wood_priming`, `wood_lacquering`, `wet_spray_painting` |
| Edge banding | width × thickness | substrate, construction, finish, surface, coating, colour | `edge_banding` |
| Decorative film / foil | width | thickness, substrate, construction, finish, surface, coating, colour | no current production operation. Add only after an evidence-backed lamination operation is approved |
| Timber / solid wood panel | species | section, thickness, width, length, grade, construction, finish, surface, coating, colour | `solid_wood_ripping`, `solid_wood_crosscutting`, `solid_wood_jointing_planing`, `solid_wood_profiling`, `solid_wood_glueup`, `cnc_router_profile_cutting`, `cnc_vertical_drilling`, `cnc_horizontal_drilling`, `cnc_grooving`, `cnc_pocketing`, `manual_drilling`, `manual_routing`, `wood_sanding`, `finish_surface_preparation`, `wood_staining`, `wood_priming`, `wood_lacquering`, `wet_spray_painting` |

### Metal

| Family | Primary attribute | Allowed secondary attributes | Eligible material-family operations |
| --- | --- | --- | --- |
| Sheet metal | thickness | alloy, technical grade, temper, finish, surface, coating, colour, sheet dimensions | `sheet_laser_cutting`, `sheet_shearing`, `metal_punching`, `sheet_metal_bending`, `metal_drilling`, `metal_milling`, `mig_mag_welding`, `tig_welding`, `metal_grinding`, `metal_polishing`, `finish_surface_preparation`, `wet_spray_painting`, `powder_coating_preparation`, `powder_coating_application`, `sandblasting`, `galvanizing` |
| Tube | section profile | metal type, alloy, technical grade, wall thickness, finish, surface, coating, colour, length | `metal_profile_cutting`, `metal_drilling`, `metal_milling`, `metal_profile_bending`, `metal_rolling`, `mig_mag_welding`, `tig_welding`, `metal_grinding`, `metal_polishing`, `finish_surface_preparation`, `wet_spray_painting`, `powder_coating_preparation`, `powder_coating_application`, `sandblasting`, `galvanizing` |
| Profile / angle / channel | section profile | metal type, alloy, technical grade, wall thickness, finish, surface, coating, colour, length | Tube operations |
| Flat bar | width × thickness | metal type, alloy, technical grade, finish, surface, coating, colour, length | Tube operations |
| Round bar / rod / wire | diameter | metal type, alloy, technical grade, finish, surface, coating, colour, length | `metal_profile_cutting`, `metal_drilling`, `metal_milling`, `metal_profile_bending`, `metal_rolling`, `mig_mag_welding`, `tig_welding`, `metal_grinding`, `metal_polishing`, `finish_surface_preparation`, `wet_spray_painting`, `powder_coating_preparation`, `powder_coating_application`, `sandblasting`, `galvanizing` |

### Glass and Plastics

| Family | Primary attribute | Allowed secondary attributes | Eligible material-family operations |
| --- | --- | --- | --- |
| Glass | thickness | glass type, tempering, lamination, fire rating, finish, surface, colour, dimensions | `glass_cutting`, `glass_drilling`, `glass_edge_processing`, `glass_tempering` |
| Mirror | thickness | substrate, safety backing, finish, edge process, colour, dimensions | `glass_cutting`, `glass_drilling`, `glass_edge_processing` |
| Acrylic / PMMA | thickness | cast/extruded construction, finish, surface, colour, dimensions | `acrylic_cnc_machining`, `acrylic_laser_cutting`, `acrylic_thermoforming` |
| Polycarbonate / PETG / PVC / ABS | thickness | construction, fire rating, finish, surface, colour, dimensions | no current family-specific operation. Future plastic CNC, cutting, bonding, and forming operations require evidence and a catalog decision |
| Sheet plastic | thickness | polymer chemistry, construction, fire rating, finish, surface, colour, dimensions | same current gap as Polycarbonate / PETG / PVC / ABS |
| Vinyl film | width | thickness, adhesive system, finish, surface, colour | no current production operation |
| Aluminium composite panel | thickness | core, fire rating, finish, surface, colour, dimensions | `panel_saw_cutting`, `cnc_router_profile_cutting`, `manual_panel_cutting`, `manual_routing` |
| Composite sandwich panel | thickness | core, face material, fire rating, finish, surface, colour, dimensions | `panel_saw_cutting`, `cnc_router_profile_cutting`, `manual_panel_cutting`, `manual_routing` |

### Stone

| Family | Primary attribute | Allowed secondary attributes | Eligible material-family operations |
| --- | --- | --- | --- |
| Natural stone slab | thickness | stone type, commercial selection, origin, quarry, grade, finish, surface treatment, colour, veining, dimensions, slab/lot evidence | `stone_cutting`, `stone_cutout`, `stone_edge_processing`, `stone_edge_profiling`, `stone_seaming` |
| Engineered quartz / mineral hybrid | thickness | chemistry, collection, design, finish, surface, colour, veining, dimensions, slab/lot evidence | Stone slab operations |
| Sintered / ultra-compact surface | thickness | chemistry, collection, design, finish, surface, colour, veining, through-body design, backing/reinforcement, dimensions, slab/lot evidence | Stone slab operations |
| Porcelain / ceramic slab | thickness | chemistry, collection, design, finish, surface, colour, veining, backing/reinforcement, dimensions, slab/lot evidence | Stone slab operations |
| Solid surface | thickness | chemistry, collection, design, finish, surface, colour, translucency, dimensions, slab/lot evidence | Stone slab operations |
| Terrazzo / engineered agglomerate | thickness | binder chemistry, aggregate, collection, finish, surface, colour, dimensions, slab/lot evidence | Stone slab operations |

### Coating

| Family | Primary attribute | Allowed secondary attributes | Eligible material-family operations |
| --- | --- | --- | --- |
| Primer | coating system | chemistry, substrate, sheen, colour, package size | `finish_surface_preparation`, `wood_priming`, `wet_spray_painting` |
| Paint / lacquer / stain | coating system | chemistry, substrate, sheen, colour, package size | `finish_surface_preparation`, `wood_staining`, `wood_lacquering`, `wet_spray_painting` |
| Powder coating | coating system | chemistry, substrate, sheen, colour | `finish_surface_preparation`, `powder_coating_preparation`, `powder_coating_application` |
| Galvanizing material/service | coating system | substrate, grade, finish | `galvanizing` |
| Filler / hardener / thinner | chemistry / product type | compatible system, substrate, package size | no direct operation. It is an input to a selected coating operation |

### Hardware, Consumables, Packaging

| Entity role and family | Primary attribute | Department affinity | Eligible operations |
| --- | --- | --- | --- |
| Hardware: hinge | model / series | Wood, Glass & Plastics | `door_front_fitting`, `hardware_installation` |
| Hardware: drawer slide | nominal length | Wood | `drawer_assembly`, `hardware_installation` |
| Hardware: handle, leg, caster, lift, connector, mounting part | model / series | one or more proven production departments | `hardware_installation`; add an assembly operation only where the object evidence supports it |
| Consumable: adhesive, sealant, abrasive, welding consumable, masking, tool wear | product type / chemistry | one or more proven production departments | none. It is an operation input only after an Agent-selected operation requires it |
| Packaging | packaging type | none | none. The approved Packaging policy controls it, not an Agent material rule |

### Stone research additions, 2026-10-10

Natural and engineered stone must stay distinct even when a collection mimics
the appearance of marble or travertine. `Calacatta`, `Carrara`, `terrazzo`,
and similar words are never enough on their own to classify the material.

#### Natural stone

The commercial natural-stone groups are Granite, Limestone, Marble, Onyx,
Quartzite, Sandstone, Serpentine, Slate, Soapstone, and Travertine. The
registry records the proven commercial group in `stone_type`, not an
unverified geological assertion. `Carrara` is an `origin`, and `Bianco
Carrara` is a commercial selection/name for a Marble row. It is not a brand.

Natural-stone variation is real production and purchasing evidence:

```text
entity: Natural Stone Slab
primary: 20 mm
brand: empty unless a proven product-system brand is printed
secondaries: marble; Bianco Carrara; Carrara, Italy; honed;
white; grey veining; bundle/slab evidence
```

Colour and veining may remain structured source and selection evidence. They
must not silently create a new global price identity unless a later pricing
policy proves that they define a distinct price class.

#### Engineered surface families

| Family | What distinguishes it | Examples of curated product-system brands |
| --- | --- | --- |
| Engineered quartz / mineral hybrid | factory-made mineral surface. Do not classify merely from a marble-look design | Silestone, Caesarstone |
| Sintered / ultra-compact | mineral/ceramic surface compacted by heat and pressure | Dekton, Neolith |
| Porcelain / ceramic slab | ceramic large-format slab, often with a backing or reinforcement variant | Laminam |
| Solid surface | homogeneous acrylic/mineral composite, including thermoformable sheets | Corian |
| Terrazzo / engineered agglomerate | binder plus aggregate. It needs its own future brand and supplier evidence rather than borrowing quartz rules | none curated yet |

The following product-system brands are now allowed as `catalog` evidence only
in their stated families: `Scalea` and `Sensa` (natural stone), `Silestone`
(engineered quartz/mineral hybrid), `Caesarstone` (engineered quartz),
`Dekton` and `Neolith` (sintered/ultra-compact), `Laminam` (porcelain/ceramic
slab), and `Corian` (solid surface). This is a bounded curated starter set,
not a claim that it contains every stone brand on the market.

#### Countertop and fabricated-element context

`countertop`, `bar_top`, `table_top`, and a similar fabricated stone surface
are an Agent-inferred use of a material, not a material family or a material
attribute. The same use can be fulfilled by natural stone, engineered quartz,
sintered/ultra-compact, porcelain/ceramic, or solid surface. This keeps price
identity and material eligibility stable while the Agent chooses the actual
material and the required operations from the object evidence.

For a countertop-like element, the potential material-family operation set is:

```text
stone_cutting
stone_cutout                 (sink, hob, tap, socket, fixing or other proven opening)
stone_edge_processing        (straight eased/polished/finished exposed edge)
stone_edge_profiling         (figured, shaped, mitred, built-up or otherwise complex edge)
stone_seaming                (where multiple pieces form one visible surface)
```

None of these operations is mandatory. The Agent selects only what the actual
geometry, exposed edges, fittings, joins and finish evidence require. A
waterfall panel, backsplash, table top, bar top, vanity top or window sill can
use the same controlled operation vocabulary without becoming a separate
material family.

#### Stone processing boundary

The existing operation catalog supports cutting, cutouts, edge processing, and
seaming. The matrix now defines the required new candidate operation
`stone_edge_profiling`: a figured, shaped, mitred, built-up or otherwise
complex exposed edge. Its future deterministic calculation must use at least
profiled exposed-edge length, profile family/complexity, thickness or build-up
configuration, material family, and any manual finish requirement. It must not
be priced from a generic material attribute or folded into straight-edge work.

It still does not contain a separate evidence-backed `stone_surface_finishing`
operation for polishing, honing, leathering, flaming, bush-hammering, sealing,
or resin/mesh reinforcement. These treatments remain facts or supplier-service
scope until an operation identity, physical drivers, route rules, and Labor
baseline are approved. They must not be smuggled into `stone_edge_processing`
or `stone_edge_profiling`.

#### Research sources

- Natural Stone Institute, commercial stone groups:
  https://www.naturalstoneinstitute.org/consumers/varieties/definition/
- Marmi Carrara, Carrara marble quarry selections:
  https://www.marmicarrara.it/uk/the-quarries/the-quarries.asp
- Cosentino Scalea, natural stone families and finishes:
  https://www.cosentino.com/scalea/
- Cosentino, Silestone, Dekton, and Sensa surface families:
  https://www.cosentino.com/kitchens/kitchen-worktop/
- Neolith, sintered-stone definition:
  https://www.neolith.com/neolith-blog/what-is-the-residential-sintered-surface/
- Laminam, ceramic slabs and thicknesses:
  https://www.laminam.com/en/sizes-and-thickness/
- Corian Design, solid-surface composition:
  https://www.corian.com/sites/corian.com/IMG/pdf/k-27478_corian_solid_surface_product_overview-2021.pdf

## Curated Brand Registry baseline

The pre-existing curated registry has 73 brands and 157 recognised
Latin/Hebrew/OCR aliases. The eight Stone product-system brands above are
approved matrix entries but still need aliases from verified source evidence
before they are added to the executable registry. This is not a market-complete
list. Unknown source brands remain `candidate` evidence and do not change a
category or family.

| Scope in the new matrix | Curated `catalog` brands |
| --- | --- |
| Hardware | Blum, Hettich, Häfele, Grass, FGV, Salice, Titus, Sugatsune, Accuride, DTC, Kesseböhmer, Vauth-Sagel, Vibo, Emuca, Lamello |
| Wood panels | EGGER, Kronospan, Finsa, SWISS KRONO, Pfleiderer, Kaindl, Sonae Arauco, Arauco, Unilin, Kastamonu |
| Wood veneer and edge banding | REHAU, Döllken, Ostermann |
| Metal sheet, profile, tube, bar | Outokumpu, SSAB, ArcelorMittal, Novelis, Hydro, Aluprof, Schüco, Klil |
| Glass | Guardian, Pilkington, AGC, Saint-Gobain, Şişecam |
| Stone | Scalea, Sensa, Silestone, Caesarstone, Dekton, Neolith, Laminam, Corian. Each is restricted to its researched family, not treated as a generic stone brand |
| Coating | Sayerlack, Milesi, Renner, Sirca, ICA, Sherwin-Williams, AkzoNobel, Tambour, Nirlat |
| Glass & Plastics | Palram, PALSUN, PALIGHT, PALCLEAR, PALGLAS, PLEXIGLAS, Perspex, ACRYLITE, PLASKOLITE, OPTIX, TUFFAK, VIVAK, VYCOM, ORAFOL, ORACAL, ORAJET, ORAGUARD, ALUCOBOND, DIBOND, ALUCORE, ALUCODUAL, ALUBOND, Reynobond |

### Brand rules for implementation

- A brand maps to one or more explicit material families, never to a
  department alone.
- Manufacturer brands and product-system brands are distinct. For example,
  `Palram` and `PALSUN` may both be retained when proved by the source.
- Supplier, importer, distributor, and retailer names are not brands unless
  separately proven as the product manufacturer or system brand.
- Technical marks such as AISI are `grade`, not a brand.
- Two different known brands from the same supplier lane block automatic
  identity merging. A missing brand is uncertainty, not proof of difference.

## Non-negotiable review gates

- A proposed operation not in the selected family's eligible set is rejected.
- An eligible operation is never automatically added to an estimate.
- A selected operation with missing physical drivers becomes `review_required`.
- A supplier service follows `reference operation -> company supplier
  operation offer`; it never becomes a material offer.
- A purchased fabricated component cannot coexist with internal hours for the
  same fabrication result.
