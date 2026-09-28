# Israel Reference Source Register

Task: 3.15.1
Status: initial source discovery, not approved catalog data
Retrieved: 2026-09-28

This register records candidate evidence sources before values enter the
reference catalog. Discovery does not make a source active. Every individual
offer still requires exact identity, unit, VAT, package, inclusion, date, and
availability review.

## Initial verified candidates

| Domain | Source | Evidence value | Required treatment |
| --- | --- | --- | --- |
| Panels and CNC service | [Algolan Express](https://algolan-express.co.il/) | Lists board types, thicknesses, prices, edge-banding prices, and extra-operation charges; explicitly states that listed prices exclude VAT and board prices include cutting | Store board rows as `cut_to_size`, not `material_only`; preserve cutting as an included service; treat extra operations as service evidence |
| Cut-to-size panels | [Hayozrim MDF 17 mm](https://hayozrim.com/products/mdf-brown-17mm) | Identifies MDF type, thickness, price per square metre, supported dimensions, and included cutting | Store as `cut_to_size`; VAT remains unresolved until the checkout or terms establish it |
| Board supplier listings | [Camisa MDF](https://www.camisa.co.il/product/%D7%9E%D7%93%D7%A4-mdf-%D7%9C%D7%95%D7%97-%D7%9E%D7%AA%D7%95%D7%A2%D7%A9/) | Provides board families, thickness range, and some purchasable panel examples | Candidate identity and offer source; verify exact dimensions, VAT, and service inclusions per row |
| Furniture hardware | [Gerassi Blum hinges](https://gerassi.co.il/blum-hinges) | Provides named Blum models, variants, and current ILS retail prices | Store exact model or kit identity as `fabricated_component` or `retail_package`; do not average "starting from" variants |
| Wood coatings | [Isralak nitro lacquer](https://isralak.co.il/%D7%9C%D7%9B%D7%94-%D7%A0%D7%99%D7%98%D7%A8%D7%95-2) | Provides product purpose and a price explicitly marked as VAT included | Store as `retail_package`, normalize VAT out, and verify package size before activation |

## Rejected uses

- A finished kitchen or installed-cabinet price is not material-price evidence.
- A cut-to-size panel price is not a raw-board price.
- A "starting from" hardware price is not an exact offer until the selected
  model, dimensions, and package contents are known.
- Old PDFs may support taxonomy or specifications but cannot establish a current
  active price baseline.
- Search-result snippets are discovery aids, not persisted evidence. Activation
  requires opening the source and recording the exact page evidence.

## Coverage still required

- raw MDF, particleboard, plywood, melamine board, laminate, veneer, edge band,
  and solid timber;
- steel, stainless steel, aluminium, profiles, tubes, and sheet formats;
- glass, mirror, stone, compact laminate, acrylic, and other plastics;
- drawer systems, runners, lift systems, handles, connectors, fasteners, and
  installation hardware;
- primers, paints, lacquers, powder, thinner, hardener, adhesives, sealants,
  abrasives, welding consumables, gases, and masking materials;
- packaging and market-specific subcontractor services.

Each domain needs at least two independent current sources where the market
supports them. One source may be retained with lower confidence when the item is
specialized and the absence of alternatives is documented.

## Batch 1 result

`db/sql/2026_09_28_israel_reference_prices_panels_v1.sql` records 23 exact
global material identities and 24 observed Israeli offers:

- six standard MDF thicknesses from Camisa;
- four birch plywood thicknesses from Camisa;
- eight commercial plywood thicknesses from Camisa;
- one coloured melamine particleboard and one two-sided decorative
  laminate-faced plywood from Camisa;
- three moisture-resistant green MDF cut-to-size offers from Algolan Express;
- one standard MDF cut-to-size offer from Hayozrim.

No baseline is created. Camisa and Hayozrim product-page VAT is unresolved, and
Algolan's cut-to-size sheet dimensions are not stated. All 24 offers therefore
remain Candidate until the missing evidence is resolved or a compatible second
source supports an approved baseline.

## Batch 2 result

`db/sql/2026_09_28_israel_reference_prices_hardware_v1.sql` records 16 exact
Blum furniture-hardware identities and 16 observed Gerassi retail offers:

- ten hinge mounting plates;
- three hinges with explicit geometry or application;
- one Aventos HL lift mechanism;
- one push-to-open mechanism and its separate adapter;

Only fixed displayed prices are retained. Listings marked "starting from" or
requiring an unresolved model selection are omitted. Gerassi's site regulations
state that site prices include VAT unless noted otherwise, and the Israeli VAT
rate is evidenced as 18% from 1 January 2025. Each retail price is therefore
preserved gross and normalized to ILS per item excluding VAT. The offers remain
Candidate because they currently represent one retailer, not an independent
market range.

## Batch 3 result

`db/sql/2026_09_28_israel_reference_prices_metal_v1.sql` records one exact
galvanized square-steel tube: 20×20×1.5 mm in a 6 m stock length from Amrusi.
The 65.80 ILS price includes VAT. Cutting costs extra and delivery is separate.
The candidate is normalized to 9.293785 ILS per linear metre excluding VAT,
while the purchasable package remains a 6 m stock length. Variant ranges whose
dimensions could not be deterministically paired with prices were rejected.

## Batch 4 result

`db/sql/2026_09_28_israel_reference_prices_coatings_consumables_v1.sql` records
five exact packages: Sundec water-based worktop varnish 0.5 l, P60 red sanding
roll 10 m, Starcke Matador P1500 hand sheet 220×270 mm, Tambour 305 PVA wood
glue 3.7 l, and recycled thinner 21 for cleaning in a 5 l container.

The Amrusi and Autostore offers have explicit VAT evidence and are normalized
excluding VAT. Pivin and Gideon Oils product pages do not state VAT, so their
gross observations remain unnormalized. The recycled thinner is explicitly a
cleaning material and is not silently treated as a compatible paint thinner.

## Batch 5 result

`db/sql/2026_09_28_israel_reference_prices_solid_wood_v1.sql` records 14 exact
Israeli offers from Gagot Avitan: nine planed Finnish-pine sections priced per
linear metre, four OSB thicknesses in 2440×1220 mm sheets, and one glued Finnish
pine panel 2440×1220×18 mm. Prices include VAT and exclude delivery.

Planed timber identities preserve both nominal pre-planing dimensions and the
supplier's approximate finished dimensions. Sheet prices are normalized to
square metres excluding VAT, while original purchasable sheet geometry remains
explicit. All observations remain Candidate pending independent comparison.

## Batch 6 result

`db/sql/2026_09_28_israel_reference_prices_wood_surfaces_v1.sql` records nine
exact 100 m PVC edge-band rolls from Naaman Center. Every identity preserves the
1.1×22 mm geometry and its decor or supplier code. The retailer terms confirm
that displayed prices include VAT and delivery is separate, so each offer is
normalized to ILS per linear metre excluding VAT.

The source still represents one supplier and one edge-band geometry. All nine
observations remain Candidate. Veneer and HPL listings without an exact retail
price were not converted into estimates or baselines.

## Batch 7 result

`db/sql/2026_09_28_israel_reference_prices_plastics_v1.sql` records eight exact
clear grade-A cast-acrylic identities from Acrylicut at 2, 3, 4, 5, 6, 8, 10,
and 15 mm. Each identity has two deliberately separate offers: an uncut
1220×2440 mm full sheet and a 1000×1000 mm laser-cut piece.

The source explicitly states that prices include VAT and delivery is separate.
Both scopes are normalized to square metres excluding VAT without averaging
the cutting premium into raw material. All sixteen observations remain
Candidate pending an independent compatible source.

Professional Israeli sheet-metal suppliers were also checked in this research
pass. Their public catalogs expose useful alloy, finish, thickness, size, and
SKU identities, but show `0.00 ILS` with quote-only purchasing. Those zeroes
were rejected as non-prices and no metal-sheet offer was fabricated from them.
