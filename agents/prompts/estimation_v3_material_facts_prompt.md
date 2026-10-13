# ESTIMATION V3 MATERIAL FACTS

Analyse one supplied preview for each requested object. Return only evidence-backed
material requirements and optional rectangular cut parts. Do not return prices,
labor, operations, machinery, overhead, supplier, brand guesses, routes, VAT,
markup, sale price, packaging or consumables.

Return raw JSON only: `{ "objects": [...] }`. Include exactly one object for
every requested `id`. Each object contains only:

- `id`: exact target object ID.
- `d`: `[width_mm, depth_mm, height_mm]`, use `0` when not known.
- `m`: material demands. Each is `{ "id","n","f","q","u","s" }`:
  stable ID, literal English material name, a family from
  `allowed_material_families`, net total quantity for the requested object
  quantity, canonical unit, and sparse specification.
- `p`: optional rectangular parts `{ "id","m","q","l","w","r" }`:
  material ID, total quantity, cut length and width in mm, rotation `yes`/`no`.
  Include only geometry supported by visible evidence or a clear construction
  inference. Omit uncertain rectangles.

`f` is a purchasable physical form, never an alloy, grade, colour or coating.
For example use `metal tube` for a square hollow profile and `metal sheet` for
a perforated plate. Put an explicitly stated alloy only in `s.metal_type`.
Never invent a material grade, wall thickness or any missing attribute.

Use English and only canonical units: `m²`, `m`, `mm`, `kg`, `l`, `sheet` or
`piece`. Quantities already include the requested object quantity. Do not use
object templates or a catalog. The server resolves material identity and price.
