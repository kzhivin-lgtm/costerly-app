# ESTIMATION V3 MATERIAL FACTS

Analyse one supplied preview for each requested object. Return only evidence-backed
material requirements and optional rectangular cut parts. Do not return prices,
labor, operations, machinery, overhead, supplier, brand guesses, routes, VAT,
markup, sale price, packaging or consumables.

Return raw JSON only: `{ "objects": [...] }`. Include exactly one object for
every requested `id`. Each object contains only:

- `id`: exact target object ID.
- `d`: `[width_mm, depth_mm, height_mm]`, use `0` when not known.
- `m`: material requirements. Each is `{ "id","n","f","q","u","s" }`:
  stable ID, literal English material name, a family from
  `allowed_material_families`, optional net physical quantity, its neutral
  unit (`m²`, `m`, `kg`, `l`, `piece`, or `sheet`), and sparse specification.
  Return `q: 0` and omit `u` only when no net quantity can be supported.
- `p`: optional rectangular parts `{ "id","m","q","l","w","r" }`:
  material ID, total quantity, cut length and width in mm, rotation `yes`/`no`.
  Include only geometry supported by visible evidence or a clear construction
  inference. Omit uncertain rectangles.

MATERIAL COMPLETENESS IS REQUIRED. The target carries an evidence-backed
object handoff in its `evidence_backed_object_handoff` field, containing
`dimensions`, `description`, and `detected_materials`.
Return one `m` entry for every distinct physical material group explicitly
stated there or visible in the supplied preview. Do not omit a material merely
because its exact Pricing Key, final finish, or full cut list is absent. Such a
gap is handled downstream as review, but the material demand must be present.
For example, a 20×20 metal frame, perforated metal backing, MDF panels, and
wood boards are separate demands when the handoff states all four.

`f` is a purchasable physical form, never an alloy, grade, colour or coating.
For example use `metal tube` for a square hollow profile and `metal sheet` for
a perforated plate. Put an explicitly stated alloy only in `s.metal_type`.
Never invent a material grade, wall thickness or any missing attribute.

`q` and `u` are net material demand, not a supplier purchase format. Use
evidence-backed direct quantities, or a clear construction inference from the
object dimensions and stated construction. For sheet material, use `m²` when
you know the net area but not individual panels. For a stated linear frame,
use `m` when its visible geometry supports a linear estimate. Never label a
net demand as a supplier sheet, stock-bar, pack, or price.

`pricing_key_fields_by_family` lists the sparse `s` facts needed by the
Resolver for each family. Search the supplied evidence specifically for those
facts and include every explicitly shown one. If a listed fact is not proven,
omit it. It is a review condition, never a reason to guess.

For a bare `MDF` or `HDF` material, use that literal name in `n`. Do not put
an object's paint colour, such as white matte or colour-matched, into `s.surface`:
it is not evidence of a faced board. A manufactured board face must be stated
explicitly in the evidence.

`family_alias_context` is the authoritative multilingual intake grammar for
the allowed families. It contains English, Russian and Hebrew family names,
plus labels for each permitted Pricing Key field. Use it to recognise the
family and the role of a stated dimension, but never treat an alias as proof
of an absent number or material value. For example, `20 x 20`, `20 на 20`,
`20×20 мм` and `20×20 מ״מ` can all be a profile section only when the source
also proves the profile family.

Do not return a purchase format or price. The server resolves the concrete
material and purchasable unit after this extraction. Use English. Do not use a
catalog.
