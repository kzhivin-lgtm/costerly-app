# Labor2.16: Part Coating

Owner-authorized implementation25November2026, existing work3.17.4.6.
Base productionbae0e899 (Labor2.15), complete2.14 checkpoint unchanged.
Candidate build: `labor-v2.16-b20261125154845-part-coating-detection-v8.4.29`.
Implementation verification and publication pending. No paid model call needed.

## Approved calculation

| Surface/system | LKM ILS/m² | Person-min/m² | Batch/setup |
| --- | ---: | ---: | --- |
| Veneer/plywood lacquer | 22 | 40 | 30m²,4 person-hours inside full norm |
| Raw MDF enamel/lacquer | 16 | 45 | 30m²,4 person-hours inside full norm |
| Veneer/plywood oil | 22 | 35 | Linear, no small-batch surcharge |
| LDSP | 0 | 0 | Prefinished |

All coatings add separate abrasives/other consumables10ILS/m². Coated area is
finished parts' `q*(2*L*W+2*t*(L+W))`, both faces and edges. No purchased-stock
waste or laminate-layer multiplier. Existing physical object and assembly-scope
quantities count once. Source facts/evidence and recipe arithmetic are saved in
the existing full-cost JSON audit, not a second payable overhead line.

Coating pay100ILS/person-hour, existing payroll25% once. Other Labor stays50.
Owner-approved manual coating1.2h therefore changes75 to150ILS including payroll;
all other old work/norm/override behavior remains protected. The protected105.8h
mixed-edit control changes Labor6612.50 to6687.50 and SC8670.50 to8745.50 for
this explicit rate change alone. Overhead allocation remains105.8h.

For spray finishing, Q=30, full hours B=Q*minutes/60, F=4, variable hours per
m² `(B-F)/Q`. Complete batches use B, a nonempty residual r uses `F+r*(B-F)/Q`.
Lacquer30m²=20h,45m²=32h,70m²=49.3333h. Oil is always `area*35/60`.
These are approved initial estimating norms, not measured industry averages.
Spray labor requires company Machinery `finish_wet_spray_booth=in_house`.
Other routes remain unknown/manual, never silently zero. Oil uses hand application.

Single evidenced LKM modifiers: gloss×2, veneer patina×2, profiled facade×1.1.
Only part-local material-note evidence can activate them, no page-wide matching.
They do not multiply area, consumables or the approved basic labor norm.
Combined effects remain unapproved and retain an unknown material price;
no new selector, warning or status badge is introduced.

## Dependencies and accepted interactions

The existing Front panels selector has six choices: LDSP, MDF Veneered Lacquer,
MDF Veneered Oil, MDF Raw Enamel/Lacquer, Plywood Lacquer, Plywood Oil. Four old
stored identifiers remain unchanged, two oil identifiers added. Original custom
stock choices remain available. No separate finish selector. Unfinished saved
non-front veneer/MDF/plywood panels use their own substrate; prefinished backing
does not become coated merely because it is plywood.

Oil/lacquer on the same substrate keeps the exact saved board offer, price,
layout and allocations, no catalog read or Parts/model call. Other material
changes reuse the existing scoped stock repricing. Only coating's dependent
hours refresh; saved CNC, assembly, preparation and their overrides stay intact.
All terminal hour editors, pending feedback, explicit Save, failure/retry,
disclosure state and saved reopen retain the accepted behavior.

The existing material projection adds LKM and flat coating consumables. The old
Paint consumables percent applies only to remaining legacy coating costs,
never additionally to the new LKM. General Consumables5% and Packaging1% retain
their existing primary-material basis, including new LKM. Materials, Labor,
Overhead, Self Cost and Objects use the same once-only projection. Coating's
recipe, rate, hours, geometry references and company route are persisted in the
existing full-cost audit. No schema migration or new writer/timer/worker.

## Verification matrix

| Outcome | Evidence |
| --- | --- |
| Six choices, old IDs/source retained | Front panels Python and calculation browser suite |
| Both faces/edges, scope/count/layup once | `tests/test_part_coating.py` |
| Full/residual boundaries, oil linear | Same pure calculator tests |
| Unknown geometry/route and evidenced modifiers | Same tests, no guessed zero |
| Finish-only exact board offer, no catalog/replan | Existing real material patch fixture |
| Independent coating refresh, other saved work unchanged | Full cost integration test |
| Flat consumables and percent bases, no double charge | Material projection integration test |
| Manual100/hour, payroll, shared Overhead and reopened cost | Calculation suite1280/390 |
| All prior auth/navigation/save/Prices/layout scenarios | Complete UI contract and exact-SHA remote gate |

Local evidence resides in `/private/tmp/coating-ui-complete/`; final receipts
will identify the actual successful candidate and served versions. Public
production acceptance follows the owner's fresh run, separate from synthetic
checks. Rollback uses the trusted exact-SHA gate/publisher tobae0e899, preserving
all saved input/evidence and prior checkpoints.
