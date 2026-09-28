# Israel Reference Furniture Core

Created in: 3.15.1
Current task: 3.15.2
Market: Israel (`IL`, `ILS`)
Status: optimized Estimation coverage denominator

## Purpose

This is the completion denominator for the first furniture Estimation release.
It measures distinct pricing behaviours, not retailer SKUs. The broader
395-cell master checklist remains the long-term assortment map and must not be
used as the launch-readiness percentage.

A group exists only when it changes at least one of these estimation inputs:

- purchasing unit or normalized unit;
- price curve or material yield;
- quantity driver;
- routing or installation behaviour;
- commercially material quality tier.

Colours, decorative variants and ordinary fastener dimensions remain identity
attributes. They do not become separate completion cells unless they change the
price tier materially.

## Status rules

- `[x]` Representative exact Israeli offers cover the pricing behaviour.
- `[~]` Exact Israeli evidence exists, but a material tier, unit, scope or
  representative option is still missing.
- `[ ]` No usable exact Israeli offer is stored for this pricing behaviour.
- Candidate evidence and production baselines remain separate. `[x]` means
  reference-data coverage, not an activated baseline.

## A. Panels, surfaces and linear wood

- [~] C01 Standard raw MDF, by sheet or square metre with thickness.
- [~] C02 Moisture-resistant MDF, by sheet or square metre with thickness.
- [~] C03 Melamine-faced particleboard, by sheet or square metre and decor tier.
- [ ] C04 Raw particleboard, by sheet or square metre with thickness.
- [~] C05 HDF or hardboard backing, by sheet or square metre with thickness. Two current cut-to-size offers cover approximately 3 and 3.5 mm furniture-backing board; their displayed prices are configurable minima not tied to an auditable selected area, and raw full sheets remain missing.
- [~] C06 Commercial plywood, by sheet or square metre with thickness and grade.
- [~] C07 Birch plywood, by sheet or square metre with thickness and grade.
- [~] C08 Poplar plywood, by sheet or square metre with thickness and grade.
- [x] C09 OSB, by sheet or square metre with thickness.
- [~] C10 Glued panels and solid-wood worktops, by square metre with species and thickness.
- [~] C11 Planed softwood, by linear metre or cubic metre with finished section.
- [~] C12 Furniture hardwood, by cubic metre, square metre or linear metre with species and section. Exact kiln-dried Sucupira 19 x 90 mm and Jatoba 19 x 140 mm profiles are covered by linear metre; both are exterior-grade commercial profiles, while common furniture-grade oak, beech, ash, maple and walnut boards with grade and moisture remain missing.
- [~] C13 HPL and compact laminate, by sheet or square metre and price tier. One exact 1220 x 2440 mm, 17 mm MDF sheet with two-sided white HPL is covered; raw HPL sheets, compact laminate, decor tiers and separate pressing scope remain missing.
- [~] C14 Natural or engineered veneer, by square metre and species tier. One current configurable oak veneer-faced panel family covers crown and quarter cuts, three substrate options and two thicknesses; the displayed price range is not bound to a selected configuration, and raw veneer leaves, engineered veneer and backed formats remain missing.
- [~] C15 PVC, ABS or veneer edge band, by linear metre with width and thickness class.
- [x] C16 Clear cast acrylic, by sheet or square metre with thickness and raw/cut scope.
- [~] C17 Furniture glass and mirror, by square metre with thickness and processing scope. Three exact safety-backed frameless mirror products provide auditable package areas and retail prices; thickness, raw/cut scope, clear glass and processing remain missing.

## B. Functional furniture hardware

- [~] H01 Standard concealed hinge, per unit with overlay and soft-close class.
- [~] H02 Wide-angle, corner and other special concealed hinge, per unit.
- [x] H03 Concealed-hinge mounting plate, per unit and fixing geometry.
- [~] H04 Butt, piano and pivot hinge, per unit or linear metre. One exact 3-inch butt-hinge pair is covered; piano and pivot forms remain missing.
- [~] H05 Standard roller or ball-bearing runner pair, by length and load class.
- [~] H06 Concealed undermount runner pair, by length and mechanism.
- [~] H07 Complete metal drawer box or drawer system, per set. Exact low, medium and high 60 x 60 cm soft-close MAXIMERA drawers are covered; economy and premium trade systems remain missing.
- [~] H08 Lift and flap mechanism, per complete set and power class. Evidence covers economy gas springs at 80, 100 and 120 N plus a premium Aventos HL mechanism, but gas-spring bracket inclusion is not confirmed.
- [~] H09 Sliding, folding and pocket-door mechanism, per complete set. One exact two-door PYRAMID sliding set with four dampers and 80 kg per-door capacity is covered; folding and pocket systems remain missing.
- [~] H10 Knob and pull handle, per unit with standard and premium tiers.
- [~] H11 Furniture lock and latch, per unit and mechanism class. Three exact magnetic forms are covered; mechanical and keyed furniture locks remain missing.
- [x] H12 Push-to-open mechanism, per unit or compatible set.
- [~] H13 Cabinet and sofa leg, per unit with height and material tier.
- [~] H14 Table leg or base, per unit or set with height and material tier.
- [~] H15 Furniture caster, per unit with diameter, brake and load class.
- [x] H16 Felt, plastic, rubber or PTFE glide, per unit or pack.
- [~] H17 Shelf pin, support or glass clamp, per unit or pack.
- [~] H18 Cabinet suspension bracket and wall rail, per set and linear metre. One exact 2 m galvanized METOD rail is covered; cabinet brackets and covers remain missing.
- [~] H19 Worktop connector, corner brace and support bracket, per unit.
- [~] H20 Wardrobe rail and supports, per linear metre and set. One exact 1 m round nickel-plated rail is covered; oval and rectangular rails, supports and load classes remain missing.
- [~] H21 Cable grommet, cable tray and ventilation grille, per unit or linear metre. Exact 60 mm metal grommet and stainless ventilation grille are covered; cable trays remain missing.
- [~] H22 Pull-out basket, waste-bin and specialist storage mechanism, per complete set. Exact basic 16 l and premium split 52 l pull-out waste systems are covered; baskets and corner/pantry systems remain missing.

## C. Fasteners and furniture connectors

- [~] F01 Ordinary wood and chipboard screw consumption, by kilogram. Exact retail and trade packages cover 17 common 3 to 5 mm diameter combinations from 20 to 80 mm; package mass or verified pieces-per-kilogram is still required for weight normalization.
- [~] F02 Ordinary machine fastener mix, by kilogram. Exact packs cover furniture-handle M4 screws at 25, 30 and 40 mm; package mass, head and finish data plus wider metric families remain missing.
- [~] F03 Nails, brads and staples, by kilogram. Exact packages cover Type 53 staples from 6 through 14 mm, an 18 mm upholstery staple and 15/25 mm brads; package mass needed for kilogram normalization remains missing.
- [~] F04 General installation anchors and plugs, by normalized installation allowance. One exact mixed 175-piece galvanized-screw and polyamide-plug set covers common 6 and 8 mm plugs; load classes, specialist anchors and the project allowance rule remain missing.
- [~] F05 Wooden dowel, by unit or package with diameter class.
- [~] F06 Confirmat and Euro connector screw, by unit or package. One exact 7 x 50 mm confirmat pack is covered; Euro screws and additional confirmat sizes remain missing.
- [~] F07 Minifix, cam and Rafix connector, per complete connection set. Exact Minifix bolt and cam components are covered, but a verified complete compatible set and Rafix remain missing.
- [x] F08 Biscuit and loose-tenon connector, per unit.
- [x] F09 Concealed knock-down connector, per complete connection set.
- [~] F10 Hinge, runner and system-specific screw, per unit or package. Three exact 1000-piece Euro-screw listings cover 6.3 mm system screws at 11 and 13 mm plus a 9-15 mm selectable family; one price is a non-specific starting price and two captured combinations were unavailable, while hinge- and runner-brand-specific screws remain missing.
- [~] F11 Connector cover cap and decorative plug, per unit or package. One exact pack of 100 black 5 mm cabinet-hole covers is covered; confirmat and Minifix decor families remain missing.

Ordinary screws are not estimated piece by piece. The Estimation layer predicts
a bounded consumption mass or project allowance, then multiplies it by the
company price per kilogram. Exact supplier dimensions remain evidence for
source auditing, but do not expand this denominator.

## D. Adhesives, finishing and abrasives

- [x] A01 PVA wood adhesive, by kilogram or litre and moisture class.
- [~] A02 One-component polyurethane wood adhesive, by kilogram or litre.
- [x] A03 Contact adhesive, by litre and application form.
- [~] A04 EVA or PUR edge-banding hot melt, by kilogram. Three exact 25 kg industrial edge-machine hot-melt offers are covered at auditable package and per-kilogram prices; the current offers do not explicitly identify EVA versus PUR, and verified chemistry tiers remain missing.
- [x] A05 Two-part epoxy adhesive, by kilogram or kit.
- [x] A06 Cyanoacrylate adhesive, by kilogram or bottle class.
- [x] A07 Construction adhesive, by cartridge, kilogram or litre.
- [~] A08 Silicone and elastic sealant, by cartridge and chemistry.
- [~] A09 Mirror-safe adhesive, by cartridge. Exact white and clear 290 ml polymer cartridges explicitly suitable for mirrors are covered; additional trade chemistry and package tiers remain missing.
- [~] A10 Clear furniture lacquer or varnish system, by litre and finish tier.
- [~] A11 Wood primer and sanding sealer system, by litre. One exact 2.5 litre synthetic wood primer is covered; sanding sealer and water-based tiers remain missing.
- [~] A12 Stain, oil and wax finishing system, by litre or kilogram. Exact clear-gloss 2.5 l, teak-tone 5 l and food-contact-approved indoor 250 ml wood oils are covered; stains and hardwax oils remain missing.
- [~] A13 Opaque furniture paint system, by litre and finish tier. Exact 4.5 litre glossy synthetic furniture enamel in base A and pastel base is covered; water-based and PU tiers remain missing.
- [~] A14 Wood filler and finishing additives, by kilogram or litre. Exact 200 g black and walnut wood-filler pastes are covered; chemistry and larger workshop packages remain missing.
- [~] A15 Furniture sanding system, by disc, belt, sheet or area allowance.

## E. Shop and packaging consumables

- [~] S01 Cleaning thinner and surface-cleaning solvent, by litre.
- [~] S02 Masking tape, paper and film system, by area or project allowance. Two exact general paper masking rolls are covered; masking paper, film and specialist tape remain missing.
- [~] S03 Saw blade, router bit and cutter wear, by operation allowance. One exact Bosch 7.25-inch 40-tooth woodworking blade is covered; router bits, CNC cutters and verified life-per-operation rules remain missing.
- [~] S04 Corrugated cardboard protection, by square metre.
- [~] S05 Bubble wrap and protective film, by square metre.
- [~] S06 Stretch film, by kilogram or roll with verified net content.
- [~] S07 Packing tape, labels and small packing consumables, by package allowance. Two exact clear carton-sealing rolls are covered; labels and reinforced tape remain missing.

## Scope boundary

The 72 groups above are the launch-blocking woodworking and cabinet-furniture
core. Metal fabrication, glass processing, stone, upholstery, integrated
electrical systems and specialist kitchen or bathroom equipment stay in the
395-cell master catalog. Until their own priced modules are activated, a
detected requirement in those domains must route to subcontractor quotation or
`needs_review`; it must not silently use a furniture-core fallback.

## Current coverage

- Total Estimation pricing groups: 72.
- Covered with representative exact evidence `[x]`: 12, or 16.67%.
- Partially covered `[~]`: 59, or 81.94%.
- No exact evidence `[ ]`: 1, or 1.39%.
- Breadth with any exact evidence `[x] + [~]`: 71, or 98.61%.

The operational completion metric is 16.67%. The 98.61% breadth metric shows
where research has started, but it must not be described as complete coverage.
