# Estimation 9 Parts Check from Upload

## Estimation 9.36 complementary overlay views

Work 3.17.4.6. Rollback is 9.35 at `3da89b8`.
Block selects one view when it covers all localized blocks, otherwise
selects a complementary pair when sufficient and keeps adding views
if more are needed. Among suitable views it prefers native axonometry
and front elevation. Front shows views with localized outlines and
suppresses partial support appearances when the full support count is
already visible. The two PDFs still publish in the background.

Fresh 9.35 Lev2 `run_033dc1bc8da746728907e45d8a550cd7` saved nine
Blocks and five drawer fronts. Its old PDF stopped at V03. Replay
with the archived same-source PDF and geometry verifies B01-B06 and
two drawers on V03, B07-B09 and three drawers on V04, and one crop per
PDF on both Adda objects. Lev1 kept three drawers and two legs in
the Front overlay across two views. No new model calls.

The fresh Lev2 run priced three unmeasured backs as HDF, 12 carcass
panels plus one divider as LDSP, and one unmeasured MDF worktop as
fallback pieces. B07-B09 are missing the full geometry envelope.
The sink cutout is present but has no resolved worktop family, so
it also received a fallback. This remains a separate calculation
investigation. The newly deployed PDF path needs a fresh authenticated
Upload for acceptance.

## Estimation 9.35 labels by material family

Work 3.17.4.6. Rollback is 9.34 at `9d41443`. Applies the approved
family matrix to Company Catalog, Israel Reference and Object Detail.
Use structured product attributes first. For legacy positions missing
an attribute, preserve an explicit functional label from the catalog
name or keep the canonical name available as evidence. Display labels
can coincide for compatible items; their stock, offer IDs, Pricing Keys
and exact prices are preserved. Ordinary plywood shows type and
thickness. Special boards, finishes and treatments remain identifiable.
Keep the stock format in Purchase Unit and the full chosen item name
available in the material label tooltip.

LED labels use the selected supplier rating, temperature and voltage.
Adda shows 4.8 W/m and 24 V. Its 6 W/m driver sizing allowance and
30 W/100 W selected drivers are unchanged. The 9.33 Adda replay
matched all 14 candidate IDs, amounts, prices and allocations.
Verified 3,945 Israel Reference positions and 48 Company Catalog
records, the saved production Adda data, 467 focused tests, and
browser fixtures at 1280 and 390 px. Authenticated production review
remains open.

## Estimation 9.34 material labels and quantity display

Work 3.17.4.6. Rollback is `estimation-v9.33-checkpoint`.
Company Catalog, Israel Reference and Object Detail share a compact
material label. Source names, pricing keys, IDs and stock dimensions
remain available. Sheet dimensions appear in Purchase Unit. A 12 V
and a 24 V LED strip can render separately. New plans carry the
selected strip's catalog voltage. Previously saved Israel Reference
lines recover it from their saved supplier price ID. An unknown
voltage stays unknown. Estimated W/m remains the same load basis used
by the driver calculation.

Required Material and Purchase Quantity use a precision chosen from
their physical unit. Discrete units render as integers; continuous
amounts use one decimal in initial markup, draft pricing, focus and
the save receipt. The exact values remain in the plan and edits.
The Adda replay preserved all part, purchase and cost signatures.
The catalog audit covered 3,945 active Israel Reference positions
and 48 Company Catalog material records from the production snapshot.
Browser fixtures at 1280 and 390 px verified the rendered labels,
12.936 m displayed as 12.9 m, the absence of edits on focus/blur,
and a staged 15.67 m edit saved at full precision.

## Review matrix for material labels by family

Owner-approved on 2026-11-14. The live Israel Reference audit
found 59 active policies, 3,945 positions and 55 populated families.
Use structured attributes evidenced for the chosen product. Exact
stock format stays in Purchase Unit. Functional dimensions may
identify the product. Prices alone cannot establish a material
attribute. The LED price anchor is 24 V and rated 4.8 W/m. Adda's
driver-sizing allowance is 6 W/m. The label shows the catalog rating
and the calculation retains the sizing allowance.


### Boards, wood and veneer

| Family | Proposed label attributes |
| --- | --- |
| `plywood` | Plywood + thickness; explicit required service class if applicable |
| `plywood_special` | Plywood + functional subtype (film-faced, anti-slip, flexible) + thickness |
| `mdf_hdf` | MDF or HDF + thickness; selected veneer, laminate, lacquer or functional grade |
| `melamine_faced_particleboard` | LDSP + thickness; exceptional grade or single-sided finish if selected |
| `particleboard` | Particleboard + thickness; functional binder or grade if selected |
| `fibreboard_hardboard` | Hardboard + thickness; selected oil-tempered or other functional grade |
| `osb` | OSB class (OSB/2, OSB/3, OSB/4) + thickness where known |
| `gypsum_board` | Gypsum board + thickness; moisture or fire grade if specified |
| `timber_solid_wood_panel` | Species + solid timber panel + thickness; construction if distinct |
| `wood_veneer` | Species + veneer; paper or fleece backing if selected |
| `aluminium_composite_panel` | Aluminium composite panel + thickness; fire class if specified |
| `composite_sandwich_panel` | Sandwich panel + thickness + core type |
| `lightweight_sandwich_panel` | Lightweight panel + thickness + core type |

### Glass, plastics and laminates

| Family | Proposed label attributes |
| --- | --- |
| `glass` | Glass + thickness + selected treatment, e.g. Tempered safety |
| `mirror` | Mirror + thickness; selected tint or safety backing where relevant |
| `acrylic_pmma` | Acrylic + thickness; Cast or Extruded where specified |
| `polycarbonate_petg_pvc_abs` | Actual polymer + thickness; functional grade if selected |
| `sheet_plastic` | Actual polymer or grade, e.g. HDPE + thickness |
| `hpl_cpl` | HPL or CPL + thickness; selected functional grade |
| `compact_laminate` | Compact laminate + thickness; core type only if relevant to selected variant |
| `edge_banding` | Actual material (ABS, PVC or Veneer) + width × thickness; décor match if required |
| `decorative_film_foil` | Film type + working width or finish when needed to identify the product |
| `vinyl_film` | Vinyl film + working width where it matters |

### Stone and worktops

| Family | Proposed label attributes |
| --- | --- |
| `natural_stone_slab` | Stone type + thickness; selected finish or price tier when applicable |
| `engineered_quartz_mineral_hybrid` | Quartz or mineral hybrid + thickness + selected price tier when applicable |
| `sintered_ultra_compact_surface` | Sintered surface + thickness + selected price tier when applicable |
| `porcelain_ceramic_slab` | Porcelain or ceramic + thickness + selected price tier when applicable |
| `solid_surface` | Solid surface + thickness; acrylic/polyester grade or price tier if relevant |
| `terrazzo_engineered_agglomerate` | Terrazzo or agglomerate + thickness; binder type if relevant |

### Metals

| Family | Proposed label attributes |
| --- | --- |
| `sheet_metal` | Metal + thickness + explicit functional type, such as galvanized or perforated |
| `round_tube` | Round tube + diameter; nonstandard parent metal and wall where needed |
| `rectangular_tube` | Rectangular tube + cross-section; nonstandard parent metal and wall where needed |
| `square_tube` | Square tube + cross-section; nonstandard parent metal and wall where needed |
| `angle` | Angle + cross-section; parent metal when nonstandard |
| `flat_bar` | Flat bar + width × thickness; parent metal when nonstandard |
| `metal_flat_bar` | No current positions. Flat bar + metal + width × thickness |
| `metal_profile_angle_channel` | No current positions. Profile type + metal + cross-section |
| `metal_round_bar_rod_wire` | No current positions. Rod, bar or wire + metal + diameter |
| `metal_tube` | No current positions. Tube type + metal + cross-section |

### Hardware and electrical

| Family | Proposed label attributes |
| --- | --- |
| `hardware_drawer_slide` | Mechanism or mounting type + nominal length; explicit load class or close/open feature |
| `hardware_hinge` | Hinge type + fitting geometry or opening angle as relevant; distinctive mechanism |
| `hardware_lift_system` | Lift type + force in N or load class when known |
| `hardware_door_system` | Mechanism type + necessary compatibility size or load |
| `hardware_drawer_system` | Drawer system type + nominal depth or side height when needed |
| `hardware_storage_system` | Storage system type + working size or capacity when needed |
| `hardware_furniture_system` | Furniture system type + compatibility dimensions when needed |
| `hardware_handle` | Handle type + hole spacing if applicable; finish when selected and relevant |
| `hardware_lock_latch` | Lock or latch type + operating variant when needed |
| `hardware_connector` | Connector type + fitting diameter or mating size |
| `hardware_fastener` | Fastener type + diameter × length; material or corrosion class when relevant |
| `hardware_mounting_part` | Fitting type + mating diameter or size when needed |
| `hardware_leg_caster` | Leg or caster type + height or wheel diameter; load rating where needed |
| `hardware_electrical_component` | LED strip: temperature + rated W/m + voltage. Driver: voltage + rated W. LED profile: form + diffuser. Other items: electrical or fitting spec that determines compatibility |

### Coatings, packaging and bought components

| Family | Proposed label attributes |
| --- | --- |
| `paint_lacquer_stain` | Coating system + selected clear or pigmented finish and gloss class when relevant |
| `primer` | Primer type + intended substrate where it matters |
| `powder_coating` | Coating system + selected finish or colour class when relevant |
| `filler_hardener_thinner` | Product function + compatible chemistry or system |
| `packaging_material` | Packaging format + grade or physical spec when necessary |
| `purchased_fabricated_component` | Component type + functional variant or fitting size as needed |

## Estimation 9.33 object purchase review and glass area

Work 3.17.4.6. Owner accepted the checkpoint on 2026-11-14.
`estimation-v9.33-checkpoint` pins `adaa7de9e9d44393f9b85af49c8656e6dda7155b`.
The private handoff archive is `backups/estimation-v9.33-checkpoint-2026-11-14`.
It holds the production artifacts, offline replay, Git bundle and checksum manifest.
The replay matches all 14 purchase lines and both HDF approval orders.
Rollback is 9.32 at `49d8e34`. Adda production run
`run_e6977dff98d64744becf450ea35ed4d7` confirmed the defect. The
Vanity unit displayed 6 estimate-wide sheets of HDF and 152.03 ILS
of prorated cost alongside 3.436 m² of its own demand.

Object Detail now shows net material, purchase unit, unit price, local
purchase quantity and local cost. Drafts price independently against
already approved purchases. Approving an object reserves the purchased
quantity and its charge so a subsequent object uses remaining stock.
A saved edit to an approved object returns it and the approvals that
depended on its stock to review. The material worker serializes approval
and quantity edits. A direct purchase override is scoped to its object.
The display and preview omit the shared stock bookkeeping.

Israel Reference and applicable Company Catalog glass and mirror area
rates now buy finished cut area, with no stock-sheet rounding. The
accepted LED estimate remains 6 W/m and displays that assumption and
colour temperature. The verified Nisko 4.8 W/m retail strip remains
the price anchor, 52.20 ILS including VAT per 5 m roll, 44.24 excluding
VAT. The material rule uses 25% capacity headroom, selecting the smallest
compatible catalog rating with no 40 W floor. A 2.900 m LED run needs
21.75 W and the existing catalog supplies one 30 W unit.

The production Parts replay estimates the Vanity unit at 2 HDF sheets
for 209.82 ILS, 3 runner sets for 216 ILS, one LED roll for 44.24 ILS,
two 2 m profile kits for 94.92 ILS, one 30 W driver for 55.93 ILS, and
1.4 m² mirror for 420 ILS, all excluding VAT. The corner's 3.460584 m²
of glass cost 1098.15 ILS at 317.33 per m². HDF allocates 2 + 4 sheets
in Vanity-first approval order or 5 + 1 in reverse order, six either
way. 128 focused tests passed, and the browser fixture verified local
price changes and a scoped Save at 1280 and 390 px. The production
Parts artifact was reused without model calls. Authenticated Save and
Approve after deployment require a live check.

## Estimation 9.32 materials and purchase quantities

Work 3.17.4.6. Rollback is the 9.31 runtime at `ae83ddd`. Object
Detail shows net consumption, the purchase unit, the price per purchase
unit and the quantity bought. Shared lines show the project consumption
and purchase cost alongside the object's allocated cost. Material Engine
still combines compatible demand across objects before rounding. A
2440 × 1220 mm sheet covers 2.9768 m². The existing 10% sheet allowance
still gives two sheets for 5 m² of combined net demand.

Parts distinguishes drawer runners and pull-out shelf runners. Two
physical runners are one purchase set for either role, per the owner's
final clarification. The editor, project purchase summary and unit price
use `set`. Editing required sets converts back to physical runner counts
for the saved norm. Editing purchase quantity leaves required sets
intact. The earlier single-runner trial listing was removed from the
active Israel Reference catalog before release.

LED strips keep the 5 m roll by temperature, profiles use 2 m bars with
diffusers, and each physical object has one sized power supply. The
editor packs profile cuts using the same order, cut allowance and stock
length as Material Engine. The saved Adda control grew from nine to
sixteen profile bars when the corner quantity went from one to two.
A saved Adda replay with production catalog data returned 3 console
runner sets and 14 corner sets at 72 ILS per set excluding VAT, nine
profile bars, five strip rolls, two power supplies and no assumptions.
The focused suite passed 107 tests. The browser fixture passed at 1280
px and 390 px for scoped Save, separate Required and Purchase edits,
and profile quantities. Fresh authenticated Upload and live approval
verification remain open.

## Estimation 9.31 LED takeoff and purchasing

The rollback is `estimation-v9.30-checkpoint`. The runtime previously
used a single plan span for each lit cabinet bay. Missing mirror lengths
could fall back to an unrelated part or the width of the owning block.

Parts now uses the front lengths of pull-out shelves attached to a
single lit scope. For mirrors it uses the glass perimeter, with a
straight full-height upright route estimated from the supported installed
height. These length estimates retain their lighting note and part or
dimension references. The existing source-backed plan span remains
available when this construction rule does not apply. An unresolved LED
length stays in review and cannot borrow another run's length.

Material Demand purchases standard strip in 5 m rolls by colour
temperature and transfers the individual shelf and mirror edge cuts
to Material Engine. It packs those cuts into 2 m U-profile and diffuser
bars, splitting longer edges at the stock length and reusing offcuts. One
supply per physical object uses all installed runs at 6 W/m with 25%
headroom and a 40 W minimum, and selects the smallest suitable stocked
driver rating. The source price remains attached to its actual rating.

The Adda replay used saved model outputs. The straight upright gave
2.900 m at 3000 K and a 40 W sizing requirement. The corner gave 7.300 m at
3000 K from two mirror perimeters (2.620 m and 4.680 m) and 5.636 m at
4000 K from two rows of four shelves (4 × 544 mm and 4 × 865 mm).
The corner needs at least 98 W. Non-lighting part roles, quantities and
dimensions matched the baseline. The saved Parts replay with production
prices selected a 60 W unit for the straight console and a 100 W unit
for the corner, both LEDON Click. It purchased nine 2 m profile kits,
three 3000 K rolls and two 4000 K rolls, with zero Assumption Fallback.
Two profile bars cover the straight console and seven cover the corner.
Exact feasibility checked that the joint set does not fit eight bars.

The evidence file `notes/evidence/estimation-v9.31-led/prices.json`
stores the dated retail observations and source pages. The profile is
56 ILS retail per 2 m (28 ILS/m at LedMaster). The standard strip anchor
is an Or-Shay Nisko 24 V 4.8 W/m reel, 52.20 ILS per 5 m in either
colour temperature. This is a price anchor and the load estimate
retains the 6 W/m budget. The seed `tools/seed_israel_led_prices.py`
updated strip pricing and installed 25 driver offers across ten actual
ratings from 30 W to 200 W and one profile kit. All 27 active price rows
were read back from production. Prices used by the Engine exclude VAT.
Fresh authenticated Upload remains open.

## Estimation 9.30 single-view Front and Block PDFs

The owner accepted the release on 2026-11-14. The protected runtime tag
`estimation-v9.30-checkpoint` identifies `a459aad7cae65dd5f234563e52992cc8522b9ed1`.
Production Core served `estimation-v9.30-detection-v8.4.29` with health
`ok`. The Cloudflare wrapper returned HTTP 200. Use this tag as the
starting point for subsequent Estimation work.

The owner approved the single-view Adda sample. The renderer builds one
Front and one Block PDF per object. Each fits one representative crop
on a single page. An axonometric view with usable geometry takes
priority over a front elevation. The original drawing retains its PDF
geometry and the overlays use the saved Front and Block Locator output.
The Front legend counts the elements shown on the selected view.

Block draws the closed outer boundary and uses source drawing lines to
recover visible edges between outer faces where they are supported.
Adjacent block borders are separated into parallel colored strokes.
Block labels retain their IDs, and Block uses the thicker stroke from
the approved sample. A footer identifies missing block marks on the chosen
view. An empty overlay uses the selected source crop and states that
the corresponding geometry is unavailable on that view.

The background worker uses no additional model calls. Prior saved
PDF links retain their format. The rollback baseline is the previous
production release `8d29c6e` (9.26).

Replaying frozen inputs for Lev1, Lev2 and both Adda objects created
eight single-page PDFs. The Adda V01 replay verified seven Block IDs,
three visible face-seam edges each for B01 and B04, and Front counts
of eight hinged doors, six drawers, eight pull-out shelves, two mirrors
and one open shelf. Median local generation took 39 ms for Lev1,
42 ms for Lev2 and 697 ms for both Adda objects, excluding storage and
link signing. Local browser checks at 1280 and 390 px passed for
readiness, opening both previews and retaining draft material edits.
The authenticated flow on a fresh Upload remains open.

The private archive `backups/estimation-v9.30-checkpoint-2026-11-14/`
preserves the Git bundle, source PDFs, exact renderer inputs, all eight
PDFs and PNGs, verification records and rollback instructions. The
archive replay matched all eight rendered pages pixel for pixel using
Lev1 V04, Lev2 V03, the straight Adda V02 and the corner Adda V01. The
checks cover the saved recognition output and rendering. A new Upload
would also exercise live recognition, storage and private link signing.
The checkpoint suite passed 34 checks. Its one failure,
`test_production_dependencies_are_exactly_pinned`, reproduced on 9.26:
the test's expected dependency list omits existing production entries.
The dependency manifests and the test are identical at both releases.

## Estimation 9.26 Object Detail overlay PDFs

The protected baseline is `estimation-v9.25-checkpoint` at `ff8436d`.
The Object Detail Elements header has separate Front and Block links.
They open private PDFs built from the original pages and the accepted
Front and Block Locator geometry. Native Front outlines retain their
shape. Block polygons render only their combined exterior, and a
Planner elevation bound is dashed when the exact shell is unavailable.
No overlay adds recognition, model calls, or quantities.

After Parts Check publishes, one background worker renders and uploads
the artifacts. Material calculation does not wait for it. The estimate,
run, Parts Check revision and object identify the artifact. Only the
Object Detail preview component checks its readiness. The check leaves
the Elements disclosure and unsaved inputs intact. Estimates without a
saved overlay revision retain their original Elements header.

Median local render time across five repeats was 1.218 s for both Lev1
PDFs, 0.051 s for both Lev2 PDFs and 0.608 s for all four Adda PDFs.
These timings exclude upload, link signing and browser download.
Rendered all 20 pages for visual inspection. Streamlit and Chrome
fixtures at 1280 and 390 px exercised pending to ready, unavailable,
old estimates, keyboard and mouse opening, and stable material inputs.
The authenticated production flow with a new estimate is tracked in TODO.

## Estimation 9.25 Finish evidence and compatible sheet purchasing

Work 3.17.4.6. Use the first live 9.24 Lev1 regression as the failure
witness and `estimation-v9.23-checkpoint` (`d00e5d9`) as the rollback
baseline. Preserve the source dimensions, part counts and locked blocks.
The owner requested the full checkpoint before the overlay work.
`estimation-v9.25-checkpoint` preserves deployed runtime `ff8436d`.
The private archive `backups/estimation-v9.25-checkpoint-2026-11-14/`
contains the bundle, source controls, exact Lev1 Upload result, and
fresh Adda Estimation results and request receipts.

Understanding records role-level finish alongside the surface geometry.
Parts retains explicit stock notes and conflicting visual evidence. It
rejects a broad uncorroborated raster side mark as a basis for changing
carcass stock. Across a unique connection in elevation, matching
visible decor can support a missing finish on the frame sides or base
cover. Adjacent dimensions and the visible cues remain in the part
trace. Parts estimates the unmarked central backing from the attached
carcass stock. When a corroborated exposed carcass side and the drawer
fronts use one decor, the side can use the nearby provisional face stock.
Parts recalculates adjoining cuts and drawer clearances. Printed
dimensions and explicit stock notes retain priority.

The 40 mm veneer estimate purchases two 20 mm cuts for each eligible
finished part. A plain tabletop and its substrate can be priced as MDF
with separate cut geometry. Material Engine shares one sheet allowance
inside an object where the catalog key, full specification, known decor,
price and stock format agree and each cut fits. It nests the actual cuts
and retains each requirement and its cost allocation. The original
Lev1 pair `cb-material-009` and `cb-material-013` reproduced one
2440 x 1220 sheet and 200 ILS in an isolated procurement test.

The repaired Lev1 plan has six sheet positions, one allowance for the
supports, and materials of 3,969.98 ILS excluding VAT. 9.24 had 11 sheet
positions, seven allowances and 3,751.72 ILS at production. The comparison
uses the archived catalog and no manual overrides. The repaired estimate
keeps one object, three blocks, three equal drawer fronts, two supports
and 29 Parts rows. The backing's 17 mm stock and the plain tabletop's
MDF substrate are construction assumptions. A final fresh Understanding
response took 25.537 s, 17,523 input and 1,391 output tokens. An earlier
fresh response and the replay of retained 9.24 finish evidence produced
the same procurement quantities and total with the final code. The two
model calls used only six saved Island PNG crops and the existing OCR and
Detection context. Other responses were frozen in these replays. Lev2 and
both Adda objects matched all parts, block envelopes and Front counts on
their saved inputs. Live Upload verification is tracked separately.

### Live Lev1 Upload

`run_8394e4fdaec540e2b5c26e3bae5f29fd` published the 9.25 Parts Check
and Material Plan without overrides. It kept three blocks, three
drawers, two supports and 29 Parts rows. Actual materials are 3,992.14 ILS
excluding VAT, with six sheet positions, 11 sheets in total and one
400 ILS allowance for both supports. The two positions that differ
from the offline procurement are 20 mm veneered MDF (five sheets
instead of four) and 17 mm LDSP (two sheets instead of three).
The live model described a matching grain behind the ribs, which led
Parts to assign the 2180 x 1530 mm central backing to the 20 mm veneer
position. That cut cannot fit the selected 2440 x 1220 mm sheet.
The 30 mm upright is projected, and the 40 mm upright retains its
explicit dimension. Both lower carcass sides remain 17 mm LDSP.
The current sheet estimator rounds up total net area with 10 percent
waste and does not establish that catalog cuts fit. The preceding
shared allowance check confirms one common estimated sheet quantity
and compatible source dimensions, not a generated cut layout.

### Adda fresh 9.25 on the accepted Detection input

Used the current runtime `ff8436d`, the original Adda PDF locally and the
immutable two-object inputs of the 9.17 production benchmark
`run_59e79abf1ba648da92382a809ec205a9`. All nine Estimation requests
were fresh. Detection and Upload were outside this run. The cycle took
89.46 s and used 61,283 input and 7,743 output tokens. No reviewed Parts
profile, saved model replies, or manual adjustments entered the fresh run.

The two objects retain the accepted V02/V03/V05/V07 and V01/V04/V06/V08
partitions, and match the 2/7 block envelopes, Front contour identities,
and all 24/133 part owners, roles, quantities and dimensions. A spelling
difference in the birch plywood note leaves the purchase material
unchanged. The current catalogs match all 11 benchmark purchase lines:
9,810.51 ILS ex VAT, with zero unpriced requirements or Assumption
Fallback. The 17 incomplete Parts dimensions remain.

Compared with the earlier reviewed Adda profile, lighting is still
incomplete. The runtime sees five lighting runs, leaves three lengths
open, and budgets 3.95 m at 3000 K and 2.825 m at 4000 K. The reviewed
profile budgets 8.700 m and 6.036 m respectively. The fresh run budgets
one 5 m coil per temperature and emits no power supply. The current
owner rule calls for one supply sized for the object's total length.
Ten finished cuts exceed the quoted stock format in both the production
benchmark and fresh 9.25 estimate. The agreed area-based estimate keeps
the catalog price for these cuts. Fabrication layout remains outside
the estimate. Fresh evidence and purchasing comparison are archived in
`output/estimation-v9.25-adda-comparison/` in the handoff workspace.

## Estimation 9.24 Finish and compatible sheet stock candidate

Rollback baseline `estimation-v9.23-checkpoint`. Understanding prefers the
coloured or axonometric view for finish and drawing dimensions for geometry.
It can report the visible underlayer of a tabletop and exposed carcass sides.
Parts supplements missing structured finish cues from explicitly observed
grain in the saved characteristics. Explicit source materials and thicknesses
retain priority. Nearby projected thicknesses still use the established
printed-anchor rule.

Parts reuses a compatible veneer sheet for a provisional drawer front when
the finish matches and a separate stock thickness is unnecessary. An
existing compatible 20 mm requirement stays in use. With no equivalent
20 mm requirement, a matching measured 30 mm panel can supply the drawer
fronts. Corroborated veneered carcass stock can supply compatible undimensioned
frame caps or backing before dependent sizes are calculated. Actual stocked
layers for thick finished panels remain pending.

Offline Lev1 replays using both the archived 9.17 and 9.16 Understanding
outputs produced three blocks, three drawers, two supports and 29 Parts.
The seat joins the ribs and right upright in one 40 mm veneered MDF
requirement. Total sheet positions are eight instead of nine in the latest
production witness. The left upright stays at 30 mm and the drawer fronts
share 20 mm with the frame caps. The saved evidence does not identify the
finish of the frame backing or tabletop underlayer. The Lev2 and Adda
replays produced identical object reports and source coverage. One fresh
visual reading remains to verify.

Approved experimental scope:

1. Understanding records an observation for each visible surface: its View,
   region or contour, visible finish cue, and corroborated links to surfaces
   with the same decor. Record an unclear finish explicitly. Keep the evidence
   on the part so it can be checked on an overlay.
2. Parts uses the material note bound to the surface first. In its absence,
   visible wood grain on a sheet part supports the veneered MDF estimating
   default. A plain colour alone is insufficient. Hidden parts use the
   construction stock rule. Retain the source and reason for each choice.
3. Parts chooses nominal thickness before deriving dependent cut dimensions.
   Preserve printed thickness. Use compatible printed evidence to resolve
   nearby vector projections and retain the original projection. For unknown
   thickness, reuse compatible stock already required by the object, or pick
   one construction default for the compatible group. Material, finish, fit,
   hardware, and construction must permit reuse. Record why separate stock
   is required. Derive fitted widths, clearances and other dependent sizes
   after stock selection.
4. Keep finished thickness in Parts. Pass actual layer requirements to
   Material Demand when an approved construction recipe applies. Each layer
   retains its stock specification and source part. Material Engine prices
   and nests compatible stock across the estimate.
5. Verify the finish overlay, Parts, and purchase positions together. Lev1
   should show the seat with the matching 40 mm veneered structure, assuming
   its visual cue is confirmed. Lev2's plain fronts must retain their finish
   and Adda's material callouts must retain their specified materials. Check
   that interchangeable assumptions consolidate, explicit dimensions and
   differing stock remain distinct, and part counts are preserved. These
   controls provide test expectations only.

Experimental implementation and evidence. Understanding validates up to 24
surface observations per object. A rectangle is kept in crop coordinates and
receives a native contour reference only on an unambiguous match. Parts can
keep two fronts with different finishes separate. Offline overlays write the
validated rectangles and their legend. Older saved replies keep role-level
finish evidence. The cut compiler now reads explicit role-based OCR stock
before deriving fitted dimensions and reuses compatible default veneer stock
in the covered frame and drawer constructions. Other unknown assemblies
retain their current construction defaults.

The estimating recipe for a 40 mm veneered seat or frame member specifies
two full 20 mm sheets per panel cut. The finished Parts rows remain 40 mm.
Material Demand counts two cuts per finished panel and combines them with
existing 20 mm veneer stock. With the same archived Lev1 catalog, the
pre-change control had nine sheet positions and 3,551.72 ILS in materials.
The experiment has seven sheet positions and 4,247.42 ILS. The cost rises
because the recipe consumes four catalog sheets at the matched 20 mm
price, replacing the earlier 40 mm allowance. Three Blocks, three drawers,
two supports and 29 Parts rows are preserved. The tabletop underlayer and
frame backing lack corroborated finish in the saved reply and retain their
existing stock. Lev2 and both Adda objects match the saved Parts reports.
The surface binder, overlay and layer handoff passed local regression tests.
The owner approved production deployment on 2026-11-14. GitHub main
contains `ce2408c`. Railway deployment `dd232100-147a-4ba3-928c-7b2bd2360307`
succeeded. The live Core and Cloudflare wrapper both report
`estimation-v9.24-detection-v8.4.29`, and Core health is HTTP 200.
Rollback target is `estimation-v9.23-checkpoint` at `d00e5d9`.

### First production Lev1 regression

Owner upload `run_3b2593ab751a4da5b552e19a5b41d20c` used the same
PDF and View boxes as the comparison. Detection returned one object.
The three Blocks, three drawers, two supports and all 29 sized Parts
rows survived. The saved 9.24 material plan has 11 sheet positions and
seven allowance lines. Repricing the previous production Parts on the
same archived catalogs without user overrides gives nine sheet positions,
five allowance lines and 3,893.42 ILS. The 9.24 plan is 3,751.72 ILS
excluding VAT. The earlier seven-position offline result used saved
finish evidence and did not exercise fresh surface recognition.

The surface marks retained in Parts Check omit the seat and the
`frame_side` role. The `carcass_side` mark describes the right side
of the slat panel, while Parts applies it to the cabinet below. Its
rectangle lies mostly outside that panel in the reconstructed overlay.
Parts uses that assignment to move the caps from 20 to 17 mm. The 40 mm
printed upright drops out of the veneer finish group and the ribs
consolidate at projected 36 mm. Parts carries no qualifying 40 mm
veneered rows into the approved estimating layup in this run. The
archive retains accepted Parts evidence. It cannot determine whether a
missing mark was absent in the raw model reply or was rejected in binding.

The two LDSP 40 mm rows are `cb-material-009` for the right frame upright
and `cb-material-013` for the lower table plate. They have the same
family, thickness, 2440 x 1220 fallback format and 200 ILS allowance.
Material Demand keys them separately as `visible_sheet` and
`internal_sheet`. Assumption Fallback then keeps separate requirement
keys because neither has a catalog candidate. A read-only diagnostic
combined only these two requirements, preserving geometry and rotation.
Both cuts nested on one sheet. This demonstrates the cost of splitting
the currently declared stock. It does not validate LDSP for the upright.
Preserve individual source requirements. Fix finish assignment before
coalescing compatible fallback stock for shared nesting.

## Estimation 9.23 Object Detail save latency

Work 3.17.4.6. Use `estimation-v9.22-checkpoint` as the baseline for an
edit to the purchase quantity of the 600 mm Lev1 drawer slides. Replay
the saved estimate through the real Streamlit component in headless
Chrome. Use an isolated copy of the production rows and observed read
latencies. Simulate write latency and keep it fixed across both builds.
Measure from click to the green Saved border. Compare the priced rows,
purchase override and all self-cost totals.

Run independent Object Detail validation and material worker reads in
parallel. Reuse object data from the worker in its totals calculation.
The receipt reads persisted material rows and totals. It skips overhead
settings, Parts presentation and preview signing. Preserve the scoped
Material Engine calculation, worker ordering and server-confirmed Saved
state. Add a browser performance entry with validation, pricing and
receipt timings for future authenticated Save measurements.

Five paired browser runs measured a median 3.53 s to the green button
on 9.22 and 2.77 s on 9.23, with 22 and 19 save-time database calls.
The request-to-override interval was 0.89 and 0.50 s. Override-to-plan
was 1.46 and 1.34 s. Plan publication to the final receipt read was
0.71 and 0.42 s. Both builds updated one manual purchase quantity and
returned identical Materials rows and self-cost totals. 101 focused
tests passed. Browser fixtures also covered failure and retry, approval,
return, editing and reverting on desktop and mobile. On 2026-11-14 the
owner confirmed that production Save worked correctly and felt faster.
The 2.77 s is the browser benchmark. There is no timed authenticated
production sample. Tag `estimation-v9.23-checkpoint` pins production
commit `d00e5d9` and Railway deployment
`20e418cc-49fe-42f6-ae7c-151fca829155`. Rollback baseline is
`estimation-v9.22-checkpoint`.

## Estimation 9.22 Object Detail save feedback

Work 3.17.4.6. Keep all three footer actions visible. Save changes starts
disabled, becomes available for a valid draft and turns green with the
label Saved once the server acknowledges the write. A new edit restores
Save changes. Reverting it restores the previous saved state. Save errors
remain visible, and the success announcement is available to screen
readers. The approval action reads APPROVE. The release uses the same
Detection and Parts Check code and the same Material Engine calculation.
Verification: 89 focused tests passed. Browser fixtures at 1280 and 390 px
verified the green state after confirmation, stable button width, new
edits, revert, failed save and retry, clean approval, approval with a
draft and return navigation. The owner accepted the Saved interaction in
production on 2026-11-14. The remote tag `estimation-v9.22-checkpoint`
pins `f7a56c4`, served by Railway deployment
`479e9f0e-c230-4b72-a877-49ec781e8b62` and Cloudflare. Authenticated
Approve remains open.

Save latency is open. The owner reported about 6 s from clicking Save
to seeing confirmation for a one-field Lev1 edit. Production run
`run_31435630873547c781ab00abc423a07a` persisted the 600 mm slide purchase
quantity as 30. The object total was updated 1.980 s after the override
write and the Material Plan 2.697 s after that same write. These are
database intervals. The authenticated fragment checks scope, object and
plan before submitting pricing. After pricing it reloads Object Detail
and reruns the fragment to deliver the receipt. There are no timestamps
for the click, worker queue delay or browser acknowledgement in this
witness. Measure each stage before optimizing. The Lev1 material audit
is deferred until the owner resumes it.

## Estimation 9.21 Object Detail and scoped material edits

Work 3.17.4.6. Start from production rollback `bdd0620`, the 9.17
runtime checkpoint. Restore the 9.18 footer and approval with the available
prices, plus the 9.19 decimal-area formatting and corroborated Front fix.
The 9.20 preparation was diagnostic only.

The browser previews an edit immediately and saves once through the
existing Object Detail bridge. Approve with a draft waits for that save.
A failed save retains the draft. Required Material shows area to one
decimal and keeps full stored precision when the user reverts a draft.

Material edits use the saved selected offer, purchase unit and allocations.
A Required Material edit replans its stock and dependent allocations.
A Purchase Quantity edit keeps required demand and reprices the purchase
and dependent allocations. Object quantity replans the materials that
object uses, including their shared stock, and preserves independent stock
and approvals. Fractional object counts use the saved Parts Check for the
affected object so the existing physical part rounding still applies.
The draft save does not rerun Detection, recognition, Parts Check or the
entire estimate. Pre-checkpoint material plans remain readable.
The quantity path also avoids a float round-trip in Assumption Fallback
that previously turned an exact two-piece demand into three purchases.

Verification: 295 focused tests passed. Browser fixture tests at 1280 and
390 px covered amount entry, dependent purchase preview, purchase-only
editing, reverting, failed save and retry, approval and return navigation.
Saved Lev1 and Adda matched full Material Engine results for sheet, LED,
mirror and fallback edits and object quantities 2 and 1.333. Saved Front
and Parts Check evidence preserved Lev2 and both Adda objects. Lev1
returned three Blocks, three drawers and two supports. All 12 archived
Lev1 Detection requests and partitions replayed identically to the
checkpoint, including the two known failures. The owner's third fresh 9.17
Upload, `run_423326c87f9c4768915a3930a3753d67`, published V01–V06 as one
object at 23:07 Israel time. GitHub main is `20e0288`. Railway
deployment `38951ba5-bed2-436d-93f4-495dcc0bf2a1` succeeded and the
Railway Core and Cloudflare markers both report `estimation-v9.21-detection-v8.4.29`.
Core health is HTTP 200. The first authenticated 9.21 Lev1 Upload
`run_88ad7350c5e34c8db8b06cf58c154828` kept V01–V06 in one object
and published 3 Blocks, 3 drawers, 2 supports and 29 complete Parts Check
rows. All row roles, quantities and dimensions match the saved 9.19
Front recovery control. The linked Material Plan published 11 priced
purchase lines, including 5 Assumption Fallback lines at 1,400 ILS.
Materials total 3,893.42 ILS before VAT. Self cost is 4,127.02 ILS before
VAT and 4,869.88 ILS after VAT. Detection Upload took 48.09 s, Parts
Check took 33.97 s, and the Material Plan was published 31.47 s later.
The plan is `needs_review` with 23 source/ownership findings and zero
unpriced requirements. The later authenticated save on the same estimate
changed the LDSP 20 mm purchase from two to four sheets. Its line cost
changed from 573.888 to 1,147.776 ILS and materials from 3,893.42 to
4,467.31 ILS. The plan was published 2.14 s after the override write.
The other ten purchase lines and Parts Check were identical. Authenticated
Approve remains to verify.

The owner's repeat Lev1 Upload `run_fa1d635b62434af58a103e34a27db8af`
returned one object with V01–V06 and the same View evidence as the first
9.21 Upload. Adda `run_a4ddf02ed4ae4aba9fcedc770c03e4f9` returned the
groups V01/V04/V06/V08 and V02/V03/V05/V07. The two repeats verify File
Review grouping. Their Estimation was not observed. The annotated remote
tag `estimation-v9.21-checkpoint` pins `20e0288`. The bundle, receipts,
source events, saved Parts and material plans are under
`backups/estimation-v9.21-lev1-production-verification-2026-11-13/`.

### Lev1 sheet material audit

The initial 9.21 plan has nine sheet purchase lines, including four LDSP
positions. The seat (39 mm from a scaled projection) and the worktop
underlayer (40 mm) reach Material Demand without a finish or material note.
The role-based fallback assigns LDSP and the exact stock thicknesses are
unmatched. The 17 mm LDSP is shared by the carcass, drawer boxes and
plinth. The 20 mm LDSP goes to the rear panel of the slatted assembly.
The grain evidence already reaches the drawer fronts, frame, ribs and
worktop. The handoff supports veneered MDF on those parts.

The smallest saved production plan, 9.16, shows two sheet lines, but
mislabels seven front openings and lacks dimensions on 29 of 45 Parts
rows. Some sheet demand ended up in piece allowances. The smallest plan
with complete part dimensions, 9.3, had four sheet lines and 28 Parts
rows. Parts has three drawer fronts and two supports in three Blocks.
Front records four drawers, so 9.3 is a material comparison and has a
known Front discrepancy. The 9.15 local control has eight sheet lines
with three Blocks, three drawers and two supports. It grouped the seat,
ribs and right upright into one 40 mm veneered MDF requirement. That
requirement still needed Assumption Fallback.

Pending: propagate corroborated finish and nominal thickness between
compatible panels, prefer already required compatible stock, and resolve
thick finished panels into available face layers and an optional core or
spacer. Keep the finished size in Parts Check and send actual layer stock
to Material Demand. Drawing specifications and explicit material breaks
take precedence. The assembly and catalog choices remain open. Replay
the verified Lev1 report and check Lev2 and both Adda objects before
changing pricing. The 9.22 release contains footer changes only.


On 2026-11-14, fresh Lev1 `run_2f324f89be3d4315be2bec33b6aee177`
and the two previous complete production reports had the same PDF hash,
three Blocks, three drawers, two supports and 29 Parts rows. All three
normalize projected rib thicknesses of 36 and 37 mm to the 40 mm marked
on the right upright. All three carry the seat at projected 39 mm without
`visual_stock` and purchase it as a separate 39 mm LDSP allowance. The
same seat state is present in production 9.17
`run_037c9562735b4213854d5fd44f7e611e` and two archived 9.15 trials.

The normalization code and Understanding finish instructions are
unchanged from 9.16. Replaying the saved 9.16 finish cues on current
geometry produced a single 40 mm veneered MDF demand for the seat, ribs
and right upright. Removing only the seat cue reproduced 39 mm without
finish evidence. Removing only its finish group retained veneer and kept
39 mm. Production logs do not retain the raw Understanding reply. An
omitted cue and a cue rejected by validation remain indistinguishable.
The tabletop underlayer stayed at 40 mm LDSP in the replay. It has no
material note and its role is outside the allowed finish cues. The
adapter uses finished thickness as stock thickness. A layer or spacer
recipe requires additional stock composition logic.

## Estimation 9.19 Scoped material edits and Front recovery

Production Lev1 `run_aefe2128a4dd472fb5995eb1a5735fcd` returned one
object with the same six View boxes and dimensional inventory as the
9.17 witness. It misread four contours on the side and rear projections
as drawer fronts. That yielded seven Blocks, seven drawers, 65 Parts
rows, 35 rows with missing dimensions and 16 purchase lines, including
10 Assumption Fallbacks. Repricing the saved report with the checkpoint
catalog and no override gave 8,469.86 ILS for materials. The persisted
148-piece drawer-slide norm changed the slide purchase from 7 sets to
74 sets and increased the materials total to 14,901.86 ILS. The edit
was persisted at 22:05:51 and the updated Material Plan at 22:06:33.
Production lacked substage timings for that 42-second interval.

A drawer-bank match now carries its host View when the supported top
is linked through Detection. Front and Planner use the same native
support evidence for either supported-top route. This prevents side
and rear profiles from expanding into false drawer blocks. Fresh model
replies on the saved failing Detection input yielded 3 Blocks, 3 drawers,
2 supports and 29 Parts rows with complete dimensions. The material
plan has 11 lines and costs 3,893.42 ILS. Finish and thickness variation
remains, including the seat material. Offline controls preserve Lev2
and both Adda objects. Detection code stays at V8.4.29.

Required Material shows square metres to one decimal in and out of focus.
Returning to the displayed baseline clears the draft while retaining the
original precise value. Approve with a saved total writes the approval and
returns through the existing Objects cache. A saved stock line can replan
a sheet, piece or direct norm using its selected offer and existing
allocations. Only affected material and object totals are republished.
Broader changes or lines without adequate saved pricing evidence use the
full existing recalculation. The allocation rule for shared stock stays
unchanged. On saved Lev1 and Adda, scoped repricing matched the full
calculation for the edited runner, LDSP sheet and shared mirror. Browser
checks at 1280 and 390 px covered decimal entry, revert and approval.

Private witness `backups/estimation-v9.18-lev1-material-regression-2026-11-13/`
preserves the production report, edit, purchases and replay comparisons.

## Estimation 9.18 Object Detail approval and material editing

Object Detail approves with the available prices. The Material Plan
status no longer replaces Approve or blocks the server action. Priced
allocations still publish the available totals if other requirements
are unpriced. Parts Check keeps its findings.

The footer shows Back to Objects and Approve, with Save changes between
them while a draft is pending. A save preserves the current screen and
does not approve. Approve with a valid draft saves it before approving.
If saving fails, the draft remains editable. Object quantity and material
edits can be sent together and queue one material recalculation from the
saved report. Unit Price and all displayed money use whole ILS. The
input keeps its exact saved baseline, hides its unit while focused, and
uses the shared end-caret rule on pointer and keyboard entry.

Verification before release: 170 focused tests passed. Headless Chrome at
1280 px and 390 px exercised the actual Object Detail markup and client
guard with a simulated save bridge, including validation, retry, reverting
an edit and saving before approval. Authenticated production approval on
an existing Adda estimate remains to be confirmed. Estimate-wide sheet
purchase and allocation rules are deferred to their separate task.

GitHub main published runtime `241ca27`. Railway deployment
`477f61b8-9e48-4278-bb16-ea7c8a77fa2c` reported success on 2026-11-13.
The anonymous core startup probe and Cloudflare wrapper both reported
`estimation-v9.18-detection-v8.4.29`.

## Estimation 9.17 Front and supported tabletop recovery

Work 3.17.4.6. Front and Planner share one unambiguous vector frame
match. A Detail crop can corroborate an elevation when the repeated
cells share their vertical edges with the continuous frame. Native
opening marks, a visible pull or a bound door callout protect the
frame from automatic classification as openings. Parts uses the same
corroborating pair. Supported worktop recovery first uses the existing
Detection route. The alternate route requires the top to contact the
side profile and visible supports, a unique attached plan outline, a
matching depth, a dimensioned height and a compatible host frontage.
Neither route changes the Detection partition or the Island Map label.

The archived failed production run did not retain raw model replies.
The staged replay used its PDF and Detection inputs, the fresh A/B
Island Map result with V06 marked Detail and the archived raw Front
response that called the frame cells doors. The first change removed
false doors and recovered the frame, leaving two blocks and six
drawer appearances. The second recovered the supported top, removed
duplicate drawer observations and restored three blocks, three drawers
and two physical supports across the elevations.

Fresh Estimation requests used saved Detection inputs. Lev1 used the
failed production partition and repeated the Detail label. It returned
the drawer case, the frame and a 1600 × 1150 × 750 mm supported table,
with 29 Parts rows and no missing dimensions. Lev2 returned the same
nine block assignments and Front contour IDs as its 9.16 control:
17 hinged doors, five drawers, two lift-up fronts and one unresolved
front on V04. Adda returned two blocks for the straight object (one
mirror and three drawers) and seven blocks for the corner object
(eight doors, six drawers, eight pull-out shelves, two mirrors and one
open shelf). Adda Parts counts match the accepted 24 and 133 row
controls. All three fresh replies were replayed on the final code.
The 9.17 check covers Estimation from the saved Detection handoff.

Owner approved the checkpoint and production deployment on 2026-11-13.
Tag `estimation-v9.17-checkpoint` pins runtime `2a4a548`.
Tag `estimation-v9.16-before-v9.17` pins the previous runtime
`c279799`. Railway deployment `086322ce-3c88-4fe2-b12c-70cb86d5ac20`
succeeded, the wrapper and core health returned HTTP 200, and the
Streamlit startup probe reported `estimation-v9.17-detection-v8.4.29`.
The private archive at
`backups/estimation-v9.17-production-checkpoint-2026-11-13/`
preserves the three control inputs and outputs, the staged failure
replay, the Lev1 catalog and purchasing plan, and both Git references.
The saved Lev1 control has 11 purchase lines totaling 3,551.72 ILS
before VAT and overhead.

### Fresh 9.17 Lev1 production verification

Run `run_037c9562735b4213854d5fd44f7e611e` published Parts Check on
2026-11-13 at 20:49 Israel time. Detection retained all six boxes but
restored the V01–V04 edge that the control lacked. The three Blocks
and all Block dimensions matched the control. Front reported three
drawers and two legs. Parts retained three 498 × 227 × 20 mm drawer
fronts, but carried only one support via `view-005:C04`. Planner's
existing Detection path still requires a direct relationship to the
view showing the second leg when attaching support contours. The
dimension-backed path used in the control also admits the corroborating
frame view. The raw production Front response was not saved.

Parts retained 29 rows with complete dimensions but four rows differed
from the control. The seat did not carry a wood-grain material decision
and used 39 mm LDSP. The two rib groups used 40 mm veneered MDF, while
the control used 37 mm veneered MDF for the seat and rib groups.
Seven of 11 purchase lines matched exactly. The 30 mm upright moved
from Israel Reference LDSP to veneered MDF (+341.70 ILS), and one fewer
support reduced the total by 200 ILS. Other changed rows netted to
zero. Materials were 3,693.42 ILS ex VAT versus 3,551.72 ILS in the
control. Production self cost was 3,915.02 ILS ex VAT and 4,619.72 ILS
including VAT. Production acceptance is partial.

### Fresh 9.17 Adda production verification

Owner Upload `run_59e79abf1ba648da92382a809ec205a9` published Parts
Check on 2026-11-13 at 20:54 Israel time. Detection returned the accepted
two sets of Views, 02/03/05/07 for the straight console and 01/04/06/08
for the corner cabinet. Front counts and the 2/7 Block split matched
the internal control. All 24/133 Parts rows matched by owner, role,
quantity, dimensions and material hint. Two straight and 15 corner
rows still have incomplete dimensions in Parts Check.

An offline Material Engine replay priced the archived internal Parts
Check and the fresh production Parts Check with the saved catalog.
Both replays matched all 11 persisted purchase lines by selection,
authority, quantity, unit price and total. The document total was
9,810.51 ILS for materials excluding VAT, with zero Assumption Fallback
and zero unpriced requirements. Allocated materials were 1,926.16 ILS
for the straight console and 7,884.36 ILS for the corner cabinet after
per-requirement rounding. Published self costs including VAT were
2,409.24 ILS and 9,861.76 ILS, respectively. No purchase overrides were
present. Both objects still require Review. The LED power supplies are
absent from the control and production Parts and purchasing, so the
agreement verifies repeatability on this run and leaves completeness open.

### Shared sheet purchasing and review status

Material Engine groups compatible requirements by resolved material across
the estimate. For area-based sheet demand, it adds the exact net areas of
all objects, applies the 10% allowance once, divides by the selected sheet
area and rounds the purchase quantity up. The net area remains per object.
The purchased line's cost is allocated back by each object's share of the
net area. An explicit demand in whole sheets is added as whole sheets.

Fresh Adda proves sharing. The straight console requires 1.4 m² of mirror
and the corner cabinet requires 1.680275 m². The 2440 × 1830 mm format
covers both with one shared sheet. Two separate estimates would buy one
sheet each. The shared purchase line costs 1,339.56 ILS excluding VAT.
Changing Required Material previews the new estimate-wide quantity from
the current purchase format. Save updates the shared plan using stored
Parts Check evidence. Editing Purchase Quantity changes the shared
purchase and allocated costs while preserving the net requirement.

The fresh Adda Material Plan has zero unpriced requirements and carries
`cb_parts_review_required`. The material plan adapter marks a plan
`needs_review` when Parts Check has findings, unresolved requirements or
estimated costs. Object Detail currently labels all of those conditions
`Material Plan Incomplete` and gates approval. Its detail counts 40
findings for the straight console and 71 for the corner cabinet. Those
counts are Material Demand review messages, distinct from the 17 Parts
rows with incomplete dimensions. Lev1 carries the same Parts Check
reason and also `assumption_fallback`. Both statuses were verified on
persisted plans from the two owner uploads.

## Estimation 9.16 Wood-grain material decision

Work 3.17.4.6. Understanding returns the chosen material per visible
part role alongside its Island and finish group. Visible wood grain on
sheet parts supports veneered MDF as an estimating assumption. A solid
wood choice requires a matching verbatim OCR note for the object that
explicitly specifies solid wood for the role. Explicit material callouts
take precedence. Parts carries the decision into Material Demand; no new
model call is added.

With saved Detection inputs and fresh Estimation responses, Lev1's
Understanding explicitly selected veneered MDF for the seat, drawer
fronts and frame members. Material Demand retained the 20, 30 and
40 mm requirements, with a single 40 mm requirement for the seat, ribs
and right upright. Lev2's plain green fronts and timber-coloured worktop
end generated no grain-based stock choice. Its nine Blocks and 110 Parts
rows matched the 9.15 control counts. The solid wood and imitation cases
are covered by automated contract tests.

Released to production on 2026-11-13. GitHub main and Railway deployment
`72afab55-468e-4fa3-8c73-1e4bf72beac0` agree on runtime commit
`c2797995620e3a37e54b5f0799798ac4b2191eda`. Production health and the
app wrapper returned HTTP 200, and an anonymous Streamlit run exposed
`estimation-v9.16-detection-v8.4.29`. Pre-deploy verification had 79
passes and one dependency-list assertion that also failed on 9.14
with identical dependency files. Rollback is
`estimation-v9.14-checkpoint` at `14605a4`. The prior Adda Front
discrepancy remains open.

### Fresh production Lev1 regression

Run `run_c085a65508e247349f6b2bb673a13d7d` published Parts Check at
19:58 Israel time on 2026-11-13. The PDF digest and the Detection
partition, including all six Island bounding boxes, match 9.14.
The first persisted discrepancy is in Front: seven openings in the
framed back, `view-004:C02` through `view-004:C08`, became hinged
doors. Block Planner produced eight Blocks instead of three. The
drawer frame retained three Front instances but was left without
geometry and without drawer parts. The supported side table was
replaced by a worktop with unresolved dimensions. Production published
45 Parts rows, 29 with missing dimensions, against 28 in 9.14 and 29
in the local 9.16 control. Production request logs contain usage and
stage names but no raw model response, so they do not distinguish the
initial Front reply from the subsequent Front role review.

Material Demand assigned a piece unit to 28 LDSP pieces and seven HDF
backs with unresolved dimensions. Assumption Fallback charged 200 ILS
per piece, totaling 7,000 ILS for these two lines. The seven false
doors also added 14 hinges at 17 ILS. Repricing the exact published
9.16 Parts Check with the archived 9.14 catalog reproduced every
production purchase line. Materials subtotal before VAT and overhead
was 7,933.85 ILS, versus 2,758.49 ILS on 9.14 and 3,493.42 ILS on
the local 9.16 control. Production self cost was 8,409.88 ILS before
VAT and 9,923.66 ILS including VAT. The fresh Lev1 acceptance failed.

An offline reconstruction from both production Detection witnesses gave
identical native geometry and byte-equivalent canonical initial Front
requests (SHA-256 `d98ea9539f2f1672507c4681c0a6b5c9df1db58dbd33de1bdc17d67008939448`).
The initial Front call runs independently of the changed combined
Island Map and Understanding request. An earlier saved raw Front
response already calls the frame openings doors. The native filter
removes them when it can match V04 and V06 as elevations. Changing only
V06 to a non-elevation lets the false doors survive in replay; the
production Island Map response was not retained, so this failure mode
is reproducible without establishing the exact production label.
One fresh A/B pair used the failed run's exact Detection input and
the same six clean crops. The 9.14 and 9.16 Island Map prompts both
returned `Detail` for V06, with identical labels across all six
Islands. Both fresh maps let false doors through when replayed against
the earlier raw Front response. This isolates a shared dependency on
the view label. It does not establish a change in error frequency or
prove which label the original production response used.

The fresh Detection run kept the same six Island boxes and V04–V06
match, but lost V01–V04. All three accepted production controls retained
that link. Removing only this link from the old context loses the
independently supported tabletop and introduces three false blocks,
while the frame openings remain filtered. Restoring only this link in
the fresh context restores all three expected Blocks when replaying the
archived Front and projections. Estimation's supported-extension rule
requires a graph path to V05 despite the native contact evidence.

## Estimation 9.15 Drawer runs and sheet thickness

Work 3.17.4.6. Parts gives visually similar drawers one size when they
form a horizontal row with a printed overall width and have no individual
printed dimensions. It retains each Front instance. Clear visible wood
grain supports a provisional veneered MDF stock choice in Material Demand.
Explicit stock notes retain priority. Nearby vector thickness projections
can share a nominal thickness only where the part construction and finish
agree. The original projection and the printed anchor remain traceable.

With Lev1's saved Detection partition and fresh Estimation responses,
three drawer fronts are 498 × 227 mm and three drawer bottoms are
600 × 478 mm. V04's external caption `4` binds 40 mm to the right
upright. The 39 mm seat and 36–37 mm ribs use 40 mm as a construction
assumption. The left upright remains a separate 30 mm projection.
The saved catalogs produce one 40 mm veneered MDF demand with two
allowance sheets and no exact catalog price. Lev1's materials subtotal
is 3,493.42 ILS excluding VAT, with four allowances. The estimate
continues to report open coverage findings.

A Lev2 repeat kept nine Blocks, two lift-up fronts and five drawer fronts.
The different heights in its vertical stack remain distinct. The fresh
repeat yielded 110 Parts rows and is not an exact match to the historical
107-row witness.

An Adda repeat kept all 133 rows for the corner object and reported 25
rows for the straight object. Front tagged two mirror contours on V02
for the straight object, which produced three Blocks instead of the two
in the accepted witness. This happened before Parts and remains open.
The three archived 9.12–9.14 Lev1 estimates still replay with their
original ten purchasing lines and 2,923.99 ILS self cost excluding VAT.
Estimation 9.15 remains a local candidate pending the Adda review.

## Estimation 9.14 production checkpoint

The owner accepted the Materials interface and the Lev1 material-cost
repeatability checkpoint on 2026-11-13, work 3.17.4.6. Tag
`estimation-v9.14-checkpoint` pins the runtime and rollback point
`14605a4bdb999952ea7fc10a3ca9de6a4bba43ff`. Railway deployment
`c04a13d9-ab7e-4314-b4f2-8b18f7c82291` reported success for this commit.

The three fresh production uploads use the same `Lev_1.pdf` with SHA-256
`56bfa63e0236c85a161a2fa95a8996b03003df8f2f01d54ac4236acb5a7287b8`.
Each Detection run assigns `P01.V1` through `P01.V6` to one object with
identical view bounding boxes. Each estimate has three Blocks, the same
28 part rows by role, dimensions and quantity (54 total units), ten
identical purchase lines and zero unpriced requirements.

| Local time (Israel) | Version | Run | Detection cycle | Detection tokens in / out | Detection API | Parts Check | Estimation tokens in / out | Estimation API | Parts Check to saved Material Plan |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 17:28 | 9.12 | `run_5a5362fcee2d445888bfab457f0ce5a2` | 42.546 s | 23,993 / 4,392 | $0.086973 | 49.277 s | 50,768 / 4,086 | $0.213594 | 30.717 s |
| 17:45 | 9.13 | `run_22aed17fe86e4cae8ea006fb4c266a98` | 43.872 s | 23,993 / 4,546 | $0.088079 | 61.536 s | 51,044 / 4,931 | $0.227097 | 30.877 s |
| 18:09 | 9.14 | `run_339be39b989242669a24ce9d2b631d20` | 51.091 s | 23,993 / 4,706 | $0.090442 | 52.187 s | 50,761 / 3,384 | $0.203043 | 34.131 s |

Detection tokens and API cost include deferred Naming. Cost includes
Mistral OCR at $0.004 per sheet. The Detection cycle timer ends before
Naming, which finished 54.459 seconds after the start of the 9.14 cycle.
Each Parts Check recorded five Sonnet 4.6 requests with zero cache reads.
Detection plus Parts Check API cost was $0.293485 on 9.14.

| Purchase | Source | Unit | Quantity | ILS per unit | ILS excluding VAT |
| --- | --- | --- | ---: | ---: | ---: |
| MDF 50 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| LDSP 36 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| LDSP 37 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| LDSP 39 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| LDSP 40 mm | Assumption Fallback | sheet | 1 | 200 | 200.00 |
| Furniture leg | Assumption Fallback | piece | 1 | 200 | 200.00 |
| 600 mm roller runner | Israel Reference | piece | 3 | 96 | 288.00 |
| HDF 6 mm | Israel Reference | sheet | 1 | 104.91024 | 104.91 |
| LDSP 17 mm | Israel Reference | sheet | 2 | 295.84512 | 591.69 |
| LDSP 20 mm | Israel Reference | sheet | 2 | 286.944 | 573.89 |

Materials cost 2,758.49 ILS excluding VAT. Assumption Fallback accounts
for 1,200.00 ILS. Consumables add 137.92 ILS and packaging adds 27.58 ILS.
Paint consumables are zero. Self cost is 2,923.99 ILS excluding VAT and
3,450.31 ILS including 526.32 ILS VAT. None of the three plans has a
manual purchase override. The three plans stay in Review with 31, 28
and 29 open findings, respectively. The earlier 9.11 Lev1 run
`run_f837297d641e489880b162626eaf5916` had 55 part rows and a saved manual
purchase quantity of 60 runners. The acceptance covers repeatable Lev1
pricing across the three recorded runs. The outstanding material choices,
part counts and older divergence remain tracked in TODO.

Private archive `backups/estimation-v9.14-lev1-production-checkpoint-2026-11-13/`
contains the source PDF, exact Detection and usage events, immutable
File Review inputs, Parts Check reports, original plans and object totals,
catalog and policy replay inputs, a Git bundle, a receipt and SHA-256
checksums. The replay recalculates each saved report with the archived
catalog and settings. It matches every purchase line, the part signature,
the per-requirement costs and the published totals. It verifies Detection
against the saved partitions and bounding boxes.

## Estimation 9.14 Materials quantity edits and display

Purchase Unit and Unit Price wrap to two lines. The quantity fields are
wider and display whole values (positive quantities below half a unit show
`<1`). The preview and saved plan keep the exact quantities.

Editing Purchase Quantity changes only the purchase and its cost.
Editing Required Material returns that row to calculated purchasing,
including when a manual purchase was already saved. A manual purchase
entered after a required edit still wins for that draft. The browser
updates immediately; Save sends one batch. The material engine accepts
the canonical piece unit for Assumption requirements as well as catalog
requirements.

The saved Lev1 Assumption sheet rate is 200 ILS per sheet, an allowance.
The separate LDSP 17 mm and 20 mm Israel Reference lines cost 295.85 and
286.94 ILS per sheet, respectively. Material selection is unchanged.
Local Chrome verified both edit orders and persistence on saved Lev1
at 1280 px and Adda at 390 px. The focused suite passed 83 tests.
Authenticated production interaction remains open.

## Estimation 9.13 Materials unit price and quantity editing

Materials shows the price per purchase unit as a read-only column
between Purchase Unit and Purchase Quantity. Formula rows show no unit
price. Quantity inputs are narrower and keep the centered alignment.

The 9.12 preview rewrote untouched purchase fields using a baseline that
existed only after JavaScript initialization. With those attributes
absent, the saved Lev1 control reproduced the blank fields in Chrome.
The server now renders each editable field with its baseline. The local
preview only restores a purchase input when the preview previously
changed that field. Preview and batch save behavior remain the same.
Chrome verified the repair against the missing-baseline reproduction on
saved Lev1 at 1280 px and Adda at 390 px, including two edits in one save.
The focused suite passed 82 tests. Authenticated production interaction
remains open.

## Estimation 9.12 Object Detail draft and save

The owner’s Lev1 purchase edit saved successfully in 9.11 but held all
material inputs for 42 seconds while the plan rebuilt. In 9.12, entering
a quantity updates a local cost preview and leaves the page in place.
Save changes sends the whole draft once, and the server reconciles the
preview without replacing the input nodes. A failed save keeps the draft.
Required Material previews use the current stock format; the saved plan
still owns catalog selection and exact packing.

Purchase-only saves update prices and allocations from the existing plan.
Changes to Required Material rebuild the material plan from the saved
Parts Check, with no recognition calls. Neither path changes the Parts
rows. The Lev1 material selection and part-count audit is separate.

The focused suite passed 82 tests. Local Chrome used the saved Lev1
estimate at 1280 px and the saved Adda estimate at 390 px. Both verified
no request during input, draft persistence after a failed save, continued
editing during a save, and preserved input nodes. Adda also verified the
updated shared purchase in the second object. Authenticated production
interaction remains open.

## Estimation 9.11 Object Detail material edits

Required Material and Purchase Quantity have centered headings and values.
Leaving either field saves the changed value and refreshes the affected
purchase rows, formula costs, VAT and object totals. Required Material is
the net demand for this object; Purchase Quantity is the shared purchase
amount for the estimate. The Material Engine uses the published Parts Check
and existing purchase rules. It makes no model calls and does not rerun
Parts Check. An unchanged edit triggers no rebuild.

The saved Adda control exercised both fields in Chrome, using the real
Material Engine and local persistence fixtures. Checks covered 1280 px and
390 px alignment, keyboard and pointer blur, a failed rebuild and retry,
and the shared purchase after navigating to the second object. The focused
suite passed 81 tests. The rollback
tag is `estimation-v9.10-checkpoint` (`b86906d`). Authenticated production
interaction remains for the owner to verify on an editable estimate.

## Estimation 9.10 Object Detail Materials and Elements

Materials displays panel stock before glass and mirrors, followed by
other materials, hardware, LED, and the locked formula rows. Required
Material uses a common numeric alignment and shows the piece unit only in
Purchase Unit when both units are pieces.

Elements opens a table with the same styling as Materials. Its rows group
the same part role and dimensions, including thickness, across all Blocks
of the object. Estimated dimensions retain their indicator, and incomplete
panel sizes remain separate. The saved Adda estimate rendered 14 and 56
rows from 24 and 133 Parts rows with the same total quantities. Local
Chrome checked both objects at 1280 px and 390 px, keyboard and pointer
interaction, purchase quantity editing, and return with unsaved edits.
The rollback checkpoint is `estimation-v9.9-checkpoint`.
The focused suite passed 33 tests. Railway confirmed production commit
`b86906d`, deployment `820051af-38bd-4498-ad3d-32e19a33c9a5`. The
owner's production screenshot confirms the reordered Materials and the
collapsed Elements section. Tag `estimation-v9.10-checkpoint` pins this
runtime before changing the material editors.

## Estimation 9.9 Objects Estimation review and subtitles

Advance the Estimation release number in the runtime and this record for
every production Estimation release, including small interface fixes.

The owner reported that Review stayed disabled for a ready object after
returning from Object Detail. The completed table used prefetch readiness
to disable the link and had no refresh to observe the pending read finish.
Review now follows the object estimate status. Object Detail reuses a
finished prefetch or makes its normal authorized read with a loading
indicator. The subtitle uses the main facade stock by allocated area and
includes LED, mirror and glass boxes only when present. The self-cost cell
shows the same amount without the approximation sign.

Local Chrome with the saved Adda Material Plan verified both navigation
orders with cold, warm and failed prefetch, mouse and keyboard use, narrow
layout, the running object state, and return after a failed detail read.
The focused suite passed 32 tests. Railway confirmed Estimation 9.9 at
`d291888`, deployment `b82b99c5-8b53-42d5-a952-43f047b970c1`. On 2026-11-13
the owner confirmed Review works on production Adda and accepted the
Objects Estimation changes. The screenshots also capture the existing
Materials and Elements presentation. Tag `estimation-v9.9-checkpoint`
pins the accepted runtime for rollback.

## Estimation 9.8 stock inheritance

Work 3.17.4.6. Parts uses the printed material and finish for an individual
panel when an indexed leader binds it to that panel. A hidden mirror backing
inherits the object's carcass stock when there is no local specification.
Plinth pieces inherit the object's facade stock unless an explicit part
callout specifies another material. An explicit local thickness wins. A
local note with matching facade material and finish can inherit its stock
thickness, with both sources retained. Front reads material callouts in the
existing component request. The rollback reference is `c705688` (9.7).

Adda verification combined one fresh Front component request with frozen
remaining provider responses. Front read the plywood and finish note at
`view-002:A04`; the native leader terminates on panel contour `C04`. The
straight panel and both plinths priced as 18 mm plywood, and the hidden
corner panel as 16 mm plywood. The replay retained 157 Parts rows (24 and
133). Pricing against the active catalogs yielded 11 sheets of 16 mm
plywood, 3 of 18 mm, no LDSP, and no Assumption Fallback. Purchase cost:
9,810.51 ILS excluding VAT, down from 10,363.92 ILS in the owner 9.7 run.
An autonomous repeat from the same saved Detection evidence used nine new
model responses and reproduced the same material selections, Parts counts
and purchase total. The seven relevant test modules passed (69 tests).
Railway reported a successful production deployment for commit `7cf9207`,
deployment `5db90e3c-01fe-4fd3-80c5-920090a87375`.

Fresh production Upload `run_9dddd6c9088945c08c234e2597f2f7e2` produced
estimate `run_9dddd6c9088945c08c234e2597f2f7e2_estimate_20261113120235`
with a new Detection event. Both groups exactly matched the accepted
partition: V02/V03/V05/V07 for the straight object and V01/V04/V06/V08
for the corner cabinet. The straight object's displayed name was
`Vanity unit`. Parts Check 9.8 completed in 96.5 seconds and published
157 rows (24 and 133), matching the 9.7 role and quantity counts. Both
plinths and the straight backing used 18 mm plywood, with the latter bound
to `view-002:A04` and `C04`. The corner backing used 16 mm plywood.
Twenty demands received catalog prices, with zero unresolved requirements
and zero Assumption Fallback. Purchase cost reproduced 9,810.51 ILS
excluding VAT. Both objects remain in Review for open Parts findings.
The straight shelf, additional corner plinth spans and LED power supplies
remain outstanding.

Work 3.17.4.6. The owner confirmed the production release on 2026-11-12.
The release starts from Detection V8.4.27 at
`379f91f5760dbacb1652da2a6d0b379d17745586` and ports the Parts Check
checkpoint `391ac35`. Detection code and locked dependencies are identical
to the release base.

Upload the PDF, review the accepted objects in File Review and select
Continue. The existing worker persists the immutable Estimation inputs.
The Parts Check worker uses the same accepted partition and published
Detection evidence. Pricing uses its established route. In Objects,
select Parts Check and download the report when ready. The button refreshes
the result on demand. Report storage is private and bound to the company,
upload and estimate. The document includes sheet coverage, the part rows
and the open dimensions, quantities and ownership issues.

Local acceptance uses the saved Adda inputs and archived provider readings.
It exercises new native crops, Analyze, Block Geometry, Parts, Parts Check,
and a simulated private publication and readback. It covers both objects,
all four sheets and 149 rows. A repeated immutable handoff reuses the
report. A foreign company cannot load it. The archived V8.4.27 Floor 07
audit checks the published Detection contract, including normalized
dimensions and zero-level datum annotations. Forty-one focused tests pass.
The pre-existing dependency-list assertion is stale at the Detection
base. The runtime dependency list, lock and Dockerfile remain identical.

Build marker `estimation-v9-detection-v8.4.27`. The owner will upload a
fresh Adda after the marker appears in production. Check the actual
report and source coverage before claiming fresh Adda acceptance.
`ESTIMATION_V9_PARTS_CHECK=false` disables the report route and button.
The Detection rollback reference is
`detection-v8.4.27-same-sheet-render-matching-production-2026-11-12`.

## Fresh production Adda witness

Acceptance remains open for work 3.17.4.6. Upload
`run_c226c39adb364b30a5c3d8d26c91dd2b` used Detection event
`9abd27ad-b865-48e9-9cee-9b91e4d44665`. Detection retained all eight View
boxes and grouped the corner cabinet as before. It split the straight
cabinet into `Vanity unit` (P1/P3) and `Console cabinet` (P2/P4). The three
immutable Estimation inputs retain that partition. The live Detection event
confirms ADA routing with Haiku 5.5 Discovery and Sonnet 4.6 Membership Review.

The pricing route took 182 seconds from estimate creation to the last
object update: 48 seconds before Analyze, 25 seconds in shared Analyze,
95 seconds in sequential Calculation through final BOM persistence, and
14 seconds for publication and pricing. Detection took 65 seconds in a
separate upload phase. The two straight-cabinet entries reached
`materials_costed`. The corner cabinet failed at `calculation_agent`
before `2vn_geometry`. No detailed failure trace was recorded. The checked
SQL stage constraint omits `calculation_agent`, a possible reason for the
missing trace. The underlying Calculation exception is unknown.

At 13:09 local time, roughly 15 minutes after estimate creation, the
estimate had no Parts Check report in its private storage prefix and no
Parts Check status or request events in the database. The production
handoff data could be read, but the last stage reached by the background
job and its underlying exception remain unknown. Railway runtime logs
require an authenticated session. No new model request or upload was made.

Estimation 9 wrote the final status and model metrics in a single PostgREST
insert. The live schema requires `input_tokens` and `output_tokens`. The
request rows provide both counts, and the terminal row omits them. The
installed client sends the union of columns without `missing=default`.
A mixed insert therefore violates the token column constraints and can
discard a failure record along with every request record. This explains
how the journal can be empty. The missing storage artifact has a separate
cause because upload precedes the insert.

Parts Check has one background worker and no job-wide deadline. Each model
request has a 120-second limit. The four original sheets are reviewed in
sequence, allowing up to eight minutes for Inventory Check alone after the
earlier calls. The prior two-object Adda archive contains nine request
records totalling 116.761 provider seconds. This is a reference, not a
measurement of this production job. Pending, P0: use runtime logs to
identify the stop if available.

## Estimation 9.1

Work 3.17.4.6. Build marker `estimation-v9.1-detection-v8.4.27`. Parts
Check writes its terminal status separately, with
explicit zero token counts. Rejected model metrics are logged without
invalidating the status. Regression tests cover both a saved report and
a recorded pipeline failure when metrics persistence fails. Existing
production jobs have no recoverable status from this change.

Pending, P0: establish a bounded Inventory Check before relying on the
production report flow. Preserve the all-sheet check and record the job
start, current stage, and outcome. Proposed approach: reconcile existing
Detection, OCR and Offline Vector evidence on every sheet against Object
Inventory. Send unresolved material candidates or uncovered drawing regions
as one bounded request and report unresolved evidence explicitly. Parts
Check itself stays a deterministic reconciliation of Parts with the checked
inventory. Verify recall on archived findings and measure the whole path
before setting a production latency target. The proposal has no runtime
changes in this repair.

## Estimation 9.2

Work 3.17.4.6. Build marker `estimation-v9.2-detection-v8.4.27`.
Offline Vector feeds Island Map and Understanding, then Front, Block
Planner and Block Locator. Object Inventory and Inventory Check precede
Block Geometry. Parts uses its measured block envelopes. Parts Check
now includes those envelopes and their source references.

The Adda production witness `run_60b71cf1428b4f8cb93ecc51098a186b`
had 33 RapidOCR numeric readings and an empty canonical dimension
inventory. Estimation 9.2 validates the saved coordinate readings against
each frozen View and uses them when the primary measurements yield no
printed spans. The casework resolver can corroborate owned orthographic
views by their drawer bank or by matching both elevations to one plan.
Glass box base estimates reuse the corresponding shelf size, and the
standard backing recipe uses 6 mm when no thickness is available.

An offline replay used the exact production Detection and OCR payloads,
the matching original PDF and archived Analyze and Inventory Check model
responses. All nine block envelopes had at least one axis, 22 of 27 axes
were resolved, and five blocks had all three axes. The report contained
149 rows and 75 rows with an unresolved dimension. Eight glass bases
had estimated footprints and 40 panes were represented. The earlier
production report contained 147 rows and 139 dimension gaps. New upload
acceptance and full detail sizing remain open. Remaining work includes
front face boundaries, glass wall heights, LED routes, partial block
depths and standalone dimensions. Model responses in the replay were
archived, so its output is a control for the handoff and local compilation.
Two saved Lev1 and three saved Lev2 Block Geometry runs reproduced
exactly. The Lev2 Parts result also matched the Estimation 9.1 control.
Thirty-three focused tests passed.

## Estimation 9.3

Work 3.17.4.6. Combined build `estimation-v9.3-detection-v8.4.28`.
The saved successful Block Geometry results remain the comparison baseline.
The Parts compiler measures individual fronts, display glass, mirrors,
visible plinth runs, and closures on corroborated source boundaries.
The shared kitchen worktop carries its plan envelope and still requires
seam, edge and cutout confirmation.

The former three-object Adda input `run_b6da521544bb40fba48fb40c73cd0d54`
reproduced the 9.2 failure. The Front Role Review used all 4,000 output
tokens and returned truncated JSON. A second failure was an out-of-frame
contour ID in Block Locator. The role review now binds a compact schema
to eligible contour IDs and exposes missing or rejected decisions in Parts
Check. Block Locator retains valid additions to the locked Planner output
and flags scopes with rejected references. The request ledger records the
stop reason and validation failure type.

Front component review runs alongside Island Map and initial Front.
Inventory Check still reviews every original sheet independently, with
up to three requests in parallel. Indexed callout crops bind LED labels
to the original vector leaders. Plan strokes provide route extents for
the two 4000 K lights on the two-object Adda control.

| File | Detection witness | Fresh provider time, end to end | Final compiled control |
| --- | --- | --- | --- |
| Lev1 | `run_1cba0b2491dc413c9a3be2fdd526226b` | 53.51 s | 3 Blocks, 28 Parts rows, zero dimension gaps. Block Geometry matches the saved control |
| Lev2 | `run_189150ebf62447fc958f7c23cc34e3bb` | 45.42 s | 9 Blocks, 107 Parts rows, zero empty part-dimension fields after the plan-envelope compilation. Four lower carcass depths still use the worktop proxy |
| Adda | `run_090b2315dc6a4036a0932bfbaf9ec319` | 79.46 s | 9 Blocks, 149 Parts rows, 18 rows with missing dimensions. 9 drawer fronts, 8 door fronts, 8 pull-out shelves, 40 panes and 5 LED runs |

The table measures Parts Check from the frozen Detection input through
local compilation. The final deterministic measurements were also run
against archived responses from those same source PDFs. The failed
three-object Adda witness completed with a fresh compact review after
reusing the exact initial responses; the extra object still lacks a
source-grounded Block. The second fresh two-object run proposed an overlapping
second mirror on the mounting-panel contour. The exact-response replay now
retains this proposal as an unresolved identity finding and publishes one
mirror on that assembly. Thirty-one focused tests passed. The private
report publication and download contract were replayed for all three files.

Active, P0: confirm the final report on a fresh production Upload and
reconcile open Inventory Check findings. On Adda, three lower carcass
depths, mirror stock thicknesses, three 3000 K route lengths, and hidden
construction remain open. Verify quantities, profiles and seams before
using the estimates for fabrication. Material selection and pricing are
outside the Parts Check scope.

## Estimation 9.4

Work 3.17.4.6. Build `estimation-v9.4-detection-v8.4.28`.
Previous release and rollback reference `78ad867038eca4b498786758dc76cdd1b9e65194`.

The first Lev2 production run contained 106 Parts rows. It matched 53 of
107 control rows and left 53 rows with missing dimensions. Substituting only
its accepted Detection observations into the frozen control reproduced the
missing block envelopes. Both plan-to-elevation links used `unique_geometry`,
which Estimation had excluded from the plan alignment. The second production
run contained 105 rows and matched 100 of 107 control rows. Its relation type
passed the gate, but two omitted fixed panels reduced the measured spans.

Planner and Block Geometry now accept both geometry-backed link types.
The native span match still gates selection of the plan and elevation.
Cross-view depth still requires calibrated drawing scales and matching
boundaries. On the aligned elevation, an unclaimed full-height rectangular
panel can extend the uniquely adjacent block at an outer edge or a closed
seam. Contours already claimed by Front keep their ownership. The recovered
contour is recorded in Object Inventory and used by Block Geometry and Parts.
The rule uses drawing geometry and no file names, contour IDs or target counts.
The Detection implementation and legacy BOM costing are unchanged.

| Saved production input | Fresh Parts Check | Elapsed | Comparison |
| --- | --- | --- | --- |
| Lev2 `run_da0b26c5a03742118490aa193e7d15db` | 9 Blocks, 107 rows | 49.70 s | 107/107 matching control rows |
| Lev2 `run_b5c3bfdf65f44e64bc949b6bcb79c632` | 9 Blocks, 107 rows | 50.85 s | 107/107 matching control rows |
| Lev1 run prefix `run_16d850` | 3 Blocks, 28 rows | 44.58 s | 28/28 matching control rows |

The fresh provider tests used the original PDF, saved Detection partition
and OCR from those Uploads. Comparison uses object, block, role, source
instance, quantity, unit and dimensions. Controlled replays deliberately
omitting the lost panel reads also reproduced all 107 Lev2 rows. B02 returned
to 690 × 650 × 1150 mm and B04 to a width of 990 mm. The shared worktop
returned to a plan envelope of 2480 × 3005 × 30 mm. Parts Check contains zero
empty dimension fields on both Lev controls. Four Lev2 lower carcass depths
still use the explicitly assumed 600 mm derived from the worktop proxy.
The exact worktop cut outline remains open. Front on fresh Lev1 reported
four drawer observations. Parts retains the three distinct V04 drawer fronts.

On the same archived model responses and inputs, the two-object Adda replay
matches 9.3 for all nine Block envelopes, Front counts, and 149 Parts rows.
Eighteen Adda rows still have missing dimensions. Forty-four focused tests
and two subtests passed. Production acceptance requires a new Upload and
confirmation in Objects. The legacy costing agent failure is tracked separately.

### Fresh Lev2 production Upload

Run `run_6096a134aae24951ac6f36a54500c21d`, Detection event
`15536d54-5d96-4c43-bc60-c72fcd4cf43c`, Parts Check event
`7a79d15e-df4a-43cd-87c3-3beda4e6d402`. Detection took 53.384 seconds and
published one object. Parts Check `estimation-v9.4-parts-check` succeeded
in 57.094 seconds. The Objects report reader returned `ready` for that
estimate. The downloaded report hash matched the event. All 107 rows
matched the saved control by identity, quantity, unit and millimeter
dimensions. It retained nine blocks, the B02 and B04 panels, and the
2480 × 3005 × 30 mm worktop envelope. Four lower carcass depths use the
explicit 600 mm estimate. Inventory Check remains open for the worktop
and unresolved element identities or ownership.

The separate legacy costing pipeline reached `estimation_analyze` and
failed at `calculation_agent` in event
`c60a2348-f5ff-4857-ac4b-8b50a82f7d91`. The stored reason is generic and
does not retain the provider exception. The 9.4 Parts Check report was
already saved when costing failed.

### Lev2 Parts Check checkpoint

Tag `estimation-v9.4-lev2-parts-check-2026-11-12` points to the deployed
runtime commit `52f2f8356edcae860be442cc49ef121e5d61c3b9`.
Two independent repeats ran the production Parts Check pipeline with
fresh Sonnet responses and the exact saved PDF, Detection result, OCR and
File Review inputs from `run_6096a134aae24951ac6f36a54500c21d`. The source
PDF SHA-256 is `b69e132814531862c1abbf2ea3910e0221ab013dd2d0fb184400149d6ec02b1d`.

| Test | Time | Matching Parts rows | Block envelopes | Open Inventory Check items |
| --- | --- | --- | --- | --- |
| Fresh production Upload | 57.094 s | 107/107 | 9/9 | 9 |
| Repeat 1 on the saved Detection input | 45.08 s | 107/107 | 9/9 | 8 |
| Repeat 2 on the saved Detection input | 41.98 s | 107/107 | 9/9 | 11 |

Both repeats retained all expected part identities, quantities, units and
millimeter dimensions. Apart from the owner source references on two rows,
the Parts data also matched the production report. Front observation counts
and Inventory Check findings varied. The final counts stayed at 17 doors,
5 drawer fronts and 2 lift-up fronts. Four 600 mm lower carcass depths are
still assumptions. Replaying each captured model response set without new
requests reproduced its full Parts Check JSON byte for byte. Report SHA-256
values for the two repeats are
`784e555e47a93f2272c7cf618c5eff84b3e0ba48c7c5049aa1cbac9925950ed4` and
`e420a6b99e1338a4a8863c44a5dc76fff5e801481fb1aba96756c5396fd09c24`.

This checkpoint covers the Lev2 Parts Check results. The two repeats reused
Detection and File Review, so the test isolates model variability within
Parts Check. Inventory Check gaps, exact countertop geometry and the legacy
costing failure remain open.

### Legacy Calculation diagnosis and Material Demand handoff

The three Lev2 production inputs have a saved Dimension Graph and no
saved structural BOM, successful `assembly_first_bom` usage event, or
detailed failure trace. The checked-in trace constraint accepts
`assembly_agent`, while runtime sends `calculation_agent` and catches
trace insert errors. This can hide the error type from the detailed trace.

One isolated replay used the saved 9.4 Lev2 object input, Dimension Graph
and source page. A fresh Haiku Analyze response supplied nine scope zones.
The Haiku Calculation request returned `stop_reason=max_tokens` at 8,000
output tokens after 32.991 seconds. The runtime passed the incomplete
response to `JSONDecoder.raw_decode`, which raised `JSONDecodeError` at
the end of the returned text. This reproduces a cause of the production
symptom. The historical responses were unavailable for comparison.

Legacy Calculation extracts assemblies, sizes, counts and material family
hints or assumptions. The structural composer calculates parts and
requirements before catalog selection and project-wide purchasing. The
production Material Plan still reads that legacy BOM. A dry run of the
existing CB Parts adapter against the checked Lev2 repeat produced seven
material requirements and 55 cut part rows. It reported 28 unsupported
carcass rows because it maps sides, tops, bottoms and the divider to
`carcass_sheet`, which has no family preference in that adapter's lookup.
The dry run stopped at Material Demand and made no production writes.

### Parts Check to Material Demand adapter

The adapter consumes saved Parts Check reports and retains each row in a
material requirement or a review item. It uses the existing internal-sheet
family preferences for carcass sheets when a material note is absent.
Recognized stock notes carry their original text and source references.
Unresolved notes, ownership conflicts and quantities stay with the source
row. The shared worktop envelope remains a review item for cut geometry.
Quantity multipliers are carried from the original scope when present.

| Saved report | Source rows | Rows in demand | Rows held for review |
| --- | --- | --- | --- |
| Lev1 | 28 | 28 | 0 |
| Lev2 | 107 | 106 | 1 |
| Adda | 149 | 62 | 87 |

The Lev2 replay uses the archived provider responses and reaches the
existing Material Engine through the experimental material-context entry
point. All 107 Parts Check rows and all nine Block envelopes match the
checkpoint. The 28 carcass rows are included. Lev2 needs review because
the 2480 × 3005 mm worktop dimensions describe an envelope. The Adda review
rows preserve the unresolved stock notes, missing dimensions, glass
treatment, lighting specifications and the unsupported interior skin.
The verification used a saved catalog snapshot and did not publish pricing.
Seventy-one focused tests passed.

### Worktop area from plan contours

The experimental branch compiles the outline from Offline Vector after
Block Geometry. It joins linked plan faces and calibrates both axes from
printed dimensions. Separate surface requirements need a seam in the plan
and finish evidence in Understanding. Parts Check keeps the original part
and its envelope; Material Demand receives the area of each surface.

A fresh Lev2 Estimation run reused the original Detection output. Five
Sonnet calls took 41.3 seconds end to end, with no extra call for the worktop.
All nine Block envelopes and 107 Parts Check rows matched the checkpoint.
The gross area is 3.0 m²: 2.8 m² of main surface (artificial stone by
assumption) and 0.2 m² of the contrasting beveled end (material unresolved).
Parts Check displays one decimal place. Machine-readable output retains
calculation precision. The end material remains open.

Worktop material purchasing uses the complete outline without deducting
appliance openings. Understanding locates openings on one source Island;
Parts Check keeps the crop location on the worktop part. Material Demand
records each opening as a separate supplier service, in pieces. Stone
worktops use the existing `stone_cutout` operation code. Appliance type
from visual recognition is a hint only. The supplier offer is still
pending; the stock planner does not treat the service as a material.
Fresh Lev2 recognition found one opening on V02 in 50.4 seconds with five
existing Sonnet calls. Replaying those responses through the final adapter
emitted one `stone_cutout` and the same gross areas, with all nine Block
envelopes and 107 Parts Check rows still matching the checkpoint.

### Lev2 worktop Material Demand checkpoint

Owner accepted the experimental checkpoint on 2026-11-12, work 3.17.4.6.
Tag `estimation-v9.4-lev2-worktop-demand-2026-11-12` preserves
`5479af3bf759bddcb6e219692437fb835be993f7`. The run reused the saved
Detection and File Review inputs from `run_6096a134aae24951ac6f36a54500c21d`.
Acceptance covers 3.0 m² of gross worktop area split across the two surface
requirements, one `stone_cutout` service sourced to V02, and parity with the
previous Lev2 Parts Check. The fixture subtype and contrasting end material
remain unconfirmed. Supplier service pricing and production acceptance
remain open.

Final replay SHA-256 values for `parts-check.json` and `cb-materials.json`
are `8d9e3edccebbfeb4b5d5570cbe1a360bc24b6fb6fde2bc4ac9367060e64cb3bb`
and `7d3acee381384e9cbf0c61735593d5b96d59c3b3f3607cdc196deb19dff7d203`.

### Estimation 9.5

The estimate worker saves Parts Check before building Material Demand and
calling Material Engine. The second geometry and BOM pipeline is removed
from the launch. Repricing reads the saved, hash-checked report and its
exact File Review input revisions. Objects and Object Detail read the same
material plan. Unpriced requirements remain visible and an incomplete plan
cannot publish a final self cost.

Supplier services can enter the engine as per-piece Company Catalog offers.
The saved Lev2 replay against current Supabase catalogs retains 107 parts
across nine Blocks. Seven of ten purchasing requirements receive prices,
including the drawer slides. Three requirements still need evidence or
a source price: MDF finish, the contrasting worktop end and the cutout
service. Missing prices enter Assumption Fallback as gaps. Automated price
research remains open.

Parts Check now makes one bounded repair pass for unowned fixed-shelf
findings with distinct near-isometric planes and a unique matching native
elevation. It adds one part per visible plane to its Block, rechecks the
reconciled inventory and passes the result to Material Demand. It adds no
model calls and preserves findings without a defensible match.

On the saved Lev2 production input `run_6096a134…`, Front observed an open
shelf stack in V02; the inventory had no owner for it and Parts Check only
reported the gap. The repair matched V02 to the B02 lateral bay in V03
and emitted three separate shelf rows, each provisionally 206 × 206 × 17 mm.
The adjacent facade supplies the scale; the carcass supplies the assumed
thickness. The original 107 rows and nine Block envelopes are unchanged.
All three rows are allocated to sheet stock (127,308 mm² of cut parts).
The result has 110 rows, with the other Inventory Check issues still open.

Railway deployed production commit `820b5669677871c842f8cdeb5e410674d6510453`
on 2026-11-12 (deployment `47743a48-2824-43b7-88b1-c6ae5a5377ab`).
Core health returned HTTP 200. The owner applied the SQL migration. A
replay of the 110-row Lev2 report against the live catalog priced all ten
purchasing requirements, including one Israel Reference cutout at 400 ILS
excluding VAT. The material plan stays in review while the inventory has
open findings. A fresh authenticated production Upload is pending.
Release checks passed 48 tests; the dependency-list assertion also fails
against the unchanged 9.4 inputs because it predates the Detection
dependencies. This release did not change the runtime dependencies.

Fresh production Adda run `run_d5519c70ba9342f1873b0719749c6ed3`
published Parts Check 9.5 in 91.89 seconds: two objects, nine Blocks and
149 part rows (24 and 125). Material Engine allocated 2,955.31 ILS ex VAT
to nine of the ten admitted requirements. Object 001 has an open LDSP
20 mm assumption; Object 002 priced all five admitted requirements.
The demand adapter still holds all 24 glass-box part rows (including
4 mm tempered parts) and the LED strip rows. Inventory and dimension gaps
also remain. The server wrote `review_required` and null self-cost totals
for both objects, so Objects displays Review without a final price.
This confirms the production handoff and exposes incomplete costing.
Fresh Lev2 Upload verification remains pending.

The owner authorized a production Israel Reference position for two-sided
P2 LDSP, 20 mm. Its typical rate is 98 ILS/m², interpolated one third of
the way from 96.20 ILS/m² at 19 mm to 101.60 ILS/m² at 22 mm. Both anchors
share the 2400 × 1220 mm catalog format. The live loader returned the new
position. A saved Adda replay matched it, but the current sheet calculator
accepted the 2850 × 1000 mm panel on that 2400 mm stock by area alone.
Treat this allocation as invalid until the engine checks the physical fit.

The Parts-to-Demand audit accounts for all 149 source rows. 62 entered
the ten requirements. The remaining 87 were recorded only as review items
and skipped: 43 unresolved stock notes, 24 glass-box holds, 14 dimension
gaps, five LED holds and one unsupported role. Missing mirror thicknesses
never reached the live 4 mm mirror default. The runtime also disables the
priced estimator allowance for requirements which reach Material Engine.
Replace this handoff systematically. Preserve each identified part and its
source, separate missing attributes from identity, and expose assumptions
and true duplicates for review. Do not bypass review using per-role
exceptions. Israel Reference already contains 5 m LED strips, drivers,
2 m recessed and surface-mounted profiles and a diffuser. An experiment
showed that the electrical family's empty pricing key and default can
select cable for a strip unless the catalog identity is preserved.

### Estimation 9.6

Every identified part becomes a material requirement. Missing information
is kept with its source and can be filled from a matching dimension, an
owning block span, or an approved catalog default. Unresolved material or
stock goes to priced Assumption Fallback. Duplicate evidence remains under
review so it is not costed twice. Exact material name evidence constrains
catalog matching before pricing. Sheet candidates must fit the part in a
permitted orientation. A total computed with open findings is marked
provisional on Objects and the estimate retains Review status.

Verified with the saved Adda, Lev1 and Lev2 inputs and live catalog data:
all 149, 28 and 110 Parts Check rows, respectively, reached priced
requirements. Adda's three mirrors used the 4 mm catalog default,
tempered glass resolved to Israel Reference, and ambiguous LED strip
requirements received allowances instead of cable prices. The 2850 mm
LDSP part used a format allowance. Lev2 retained three shelves and the
400 ILS cutout service. The replay verifies costing and the published
status contract. A fresh authenticated Upload is pending.
