# Israel Reference Catalog Coverage

Created in: 3.15.1
Current task: 3.15.2
Status: active coverage control

This matrix prevents common retail availability from being mistaken for full
furniture-estimation coverage. `Observed` means at least one exact Israeli offer
is stored. It does not mean an approved market baseline exists.

| Domain | Required families | Current evidence | State |
| --- | --- | --- | --- |
| Wood sheet goods | MDF, MR MDF, particleboard, plywood, OSB, decorative board, hardboard, compact laminate | 28 offers across MDF, plywood, OSB, melamine particleboard, and laminate-faced plywood | Partial |
| Solid wood | softwood, hardwood, glued panels, butcher block | nine planed Finnish-pine sections and one glued-pine panel | Partial |
| Wood surfaces | veneer, HPL/decorative laminate, edge banding | nine exact 1.1×22 mm PVC edge-band rolls; veneer and HPL prices remain unresolved | Partial |
| Metal sheets | carbon, galvanized, stainless, aluminium by grade, thickness, and sheet size | none | Missing |
| Metal profiles | square/rectangular tube, angle, channel, flat, bar, aluminium profile | one galvanized 20×20×1.5 mm square tube | Partial |
| Glass and mirror | float, tempered, laminated, mirror by thickness and processing scope | none | Missing |
| Stone and slabs | engineered quartz, natural stone, porcelain slab | none | Missing |
| Plastics | acrylic, polycarbonate, PVC sheet | eight clear cast-acrylic thicknesses, each with raw-sheet and cut-to-size offers | Partial |
| Hinges and plates | overlay geometries, angles, mounting plates, soft-close | 13 exact Blum hinge and plate offers | Partial |
| Movement hardware | runners, drawer systems, lifts, sliding and folding systems | one Aventos HL lift | Partial |
| Furniture hardware | handles, locks, latches, legs, casters, connectors, anchors, screws | one push-to-open pair of components; screw packaging unresolved | Partial |
| Wood coatings | primers, stains, lacquers, opaque paint, hardeners | one water-based clear worktop varnish | Partial |
| Metal coatings | primers, wet paint, powder, galvanizing materials | none | Missing |
| Adhesives and sealants | PVA/D3/D4, contact, construction, epoxy, PU, silicone | one PVA offer with unresolved VAT | Partial |
| Abrasives | hand sheets, rolls, discs, belts across production grits | one P60 roll and one P1500 sheet | Partial |
| Welding consumables | wire, electrodes, shielding gases | none | Missing |
| Shop consumables | thinners, cleaners, masking, lubricants | one cleaning-only recycled thinner with unresolved VAT | Partial |
| Packaging | cardboard, foam, stretch film, bubble wrap, tape, corner protection | none | Missing |

## Activation rule

A family becomes estimator-ready only when exact identities have compatible
units, VAT treatment, package constraints, service scope, current evidence, and
an approved same-market baseline or exact company price. Until then the resolver
must return `needs_review` rather than substitute a nearby item.
