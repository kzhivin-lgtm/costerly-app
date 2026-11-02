# OBJECT-TO-ESTIMATE GEOMETRY BRIEF V1

Inspect every supplied private source page. Return raw JSON only:

`{"batch_id":"...","pages":[...],"object_kind":"wardrobe|cabinet|unknown","dimensions":[...],"counts":[...],"material_roles":[...]}`

`pages` must contain every requested page exactly once as
`{"page_number":N}`. `batch_id` must equal the request.

Each measurement claim is
`{"key":"width|depth|height","value":positive_finished_mm,"confidence":0..100,"evidence_refs":[...]}`.
Use finished dimensions, not paper-space millimetres. Apply a visibly stated
drawing scale when present. Cite only exact `source_evidence_ref` or OCR
`block_ref` values from this batch. Do not estimate a missing dimension.

Each count claim is
`{"key":"bay_count|door_count|shelf_count_per_bay","value":positive_integer,"confidence":0..100,"evidence_refs":[...]}`.

Each material role is
`{"role":"visible_facade|internal_carcass|backing|finish|hardware","source_name":"...","family":"one allowed family code","specification":{},"quantity":positive_number_or_null,"unit":"piece|set|m|m²|kg|l|null","evidence_refs":[...]}`.
Return a role only when its source identity is shown or stated. Do not select a
catalog item, price, labor, manufacturing operation, overhead, sale price or
hidden precision detail. Set quantity and unit only when the source explicitly
states a count or measured consumption for that role. If a page contains no usable geometry or construction
fact, include it in `pages` and return no claim for it.
