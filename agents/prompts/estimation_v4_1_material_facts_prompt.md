# ESTIMATION V4.1 BOUNDED MATERIAL FACTS

You receive one disjoint batch of private source pages from one commercial
object. Inspect every supplied page. Return raw JSON only, with exactly this
shape:

`{"batch_id":"...","pages":[...],"claims":[...]}`

`batch_id` must match the request. `pages` must contain every requested page
exactly once, each as `{"page_number":N,"material_signal":"yes|no|uncertain","claim_ids":[...]}`.
Use `yes` only when the source shows or states a physical material or purchased
hardware. Use `no` when it clearly does not. Use `uncertain` when the page may
contain a relevant signal but it cannot be safely interpreted.

Each claim is exactly `{"id","n","f","q","u","s","e"}`:

- `id`: unique only within this batch.
- `n`: literal English physical material or hardware group.
- `f`: one exact code from `allowed_material_families`.
- `q`: direct net physical quantity from the source, or `0` if none is
  explicitly stated. It is never a purchase quantity.
- `u`: neutral unit only when `q` is direct: `m²`, `m`, `mm`, `kg`, `l`,
  `piece`, or `sheet`.
- `s`: sparse proven specifications using only `specification_keys`.
- `e`: one or more exact `source_evidence_ref` or OCR `block_ref` values from
  this batch. Cite the smallest relevant set.

Do not infer cut parts, panel rectangles, areas, lengths, perimeters, material
consumption, or quantities from object envelope dimensions. Do not sum,
multiply, extrapolate, or turn a visual construction into a numeric demand.
If a material is evident but its quantity is not directly stated, return it
with `q: 0` and omit `u`.

Do not return price, supplier, catalog item, labor, machine, manufacturing,
overhead, VAT, margin, packaging, paint/lacquer/stain, primer, powder coating,
or fasteners. Do not invent material subtype, thickness, finish, profile,
species, mechanism, or compatibility. A drawing of a sliding system is not
evidence for a folding system.

Material completeness is required within the supplied pages. A page with a
material signal must list every directly supported distinct material or
purchased hardware group. However, do not assume that an item exists merely
because another page or a typical cabinet would have one. The server combines
batches and lets the deterministic Resolver and Material Engine handle
catalog selection and purchase formats.
