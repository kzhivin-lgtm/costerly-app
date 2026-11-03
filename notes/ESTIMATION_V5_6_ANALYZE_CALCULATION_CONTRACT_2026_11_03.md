# Estimation V5.6: Analyze to Calculation contract

Status: implemented locally, pending production witness on `Lev_1.pdf` and `Lev 2.pdf`.

`Estimation Analyze` receives the complete pending Estimation input set for one
file. It receives deduplicated original evidence pages and the immutable
Detection object registry. It produces one `estimation_composition_scope_v1`
per immutable object input. A scope has physical zones, their assembly role,
operability, exact shown front topology and explicit assumptions. It selects no
catalogue item, material, price, thickness, labour or manufacturing route.

`Estimation Calculation` remains one bounded vision call per object. Its
request includes that object's normalized scope, the object geometry graph and
the evidence pages. It may fill dimensions, exposure and material roles only.
The deterministic scope gate removes invented zones, restores the locked role
and front groups for each scope zone, and removes model-injected slide, hinge
and lift secondary items. The final fact result retains `composition_scope`
and `calculation_handoff`, the inspectable second-call contract. Analyze usage
is recorded separately, while the Scope is stored with the BOM it constrained.

2VN change: an axis binding rejected for an invalid view-orientation mapping is
removed before composition. The composer therefore uses a compatible peer or a
bounded construction default instead of retaining the rejected number. A
section's declared horizontal width/depth axis is now valid 2VN input.

Acceptance witness for Lev 1: Analyze must identify three drawer fronts in the
lower storage zone and a fixed screen/divider zone. Calculation handoff must
contain exactly those topology constraints. The resulting structural facts
must request three `Drawer slide` sets at 600 mm and zero hinges or gas lifts.
