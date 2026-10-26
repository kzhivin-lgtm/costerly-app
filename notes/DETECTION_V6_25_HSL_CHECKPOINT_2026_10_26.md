# Detection V6.25 HSL checkpoint, 2026-10-26

## Status

Accepted as the current operational checkpoint by the owner. This records the
observed result and its limits. It does not claim that every commercial name is
a semantic-quality benchmark.

- Deployed code commit: `a34497b`, `fix(detection-v6.25): bind naming visual evidence`.
- Audited run: `run_2dceafe62d3440668ca56b6b74101cc8`.
- Source: `Hasolelim_Carpentry_Plan_Floor_07.pdf`, 11 pages.
- Route: ordinary Detection, 11-page Mistral OCR, deferred Haiku Naming.
- No extra title-block OCR, no new model call, no router change.

## Accepted run facts

| Measure | Result |
| --- | ---: |
| Detected objects | 9 |
| OCR pages and cost | 11, $0.044000 |
| Detection cost and duration | $0.158034, 50.072 s |
| Initial processing cycle | 69.777 s |
| Naming cost and duration | $0.028279, 22.423 s, deferred |
| Preview generation | 9 created, 0 skipped, 10.050 s |
| Naming validation | accepted, no violations |
| Measured Detection + OCR + Naming | $0.230313 |

The object count is an inventory result, not sufficient proof of product
quality on its own. Locked object identity, quantity, order, evidence pages and
object boundaries were not altered by Naming.

## Page 11 and previews

P11 is one locked object, `object-009`, with three evidence regions. Its source
regions correspond to `P11.V1 / view-031`, `P11.V2 / view-032`, and
`P11.V3 / view-033`. The deterministic presentation-source selector chose
`P11.V3 / view-033`; Preview created the resulting image successfully. The
owner visually accepted the front-oriented preview selection in this run.

## Naming result and limitation

The final persisted names were:

1. `Shelving unit`
2. `N57 Kitchen`
3. `N60 Shelving unit`
4. `N62 Kitchen`
5. `N68 Kitchen`
6. `N70 Shelving unit`
7. `Kitchen`
8. `N76 Kitchen`
9. `N76B Shelving unit`

V6.25 fixed the immediate publication failure: a visual cue is now bound
deterministically to the locked source crop only when its physical page matches.
All returned cues therefore have an object-local locked View id and validation
accepted all rows. The naming vocabulary remains a known limitation. No further
prompt or Naming-contract experimentation is authorised by this checkpoint.

## Decision record

Retain V6.25 for continuation of Detection work. Do not reopen naming merely
because a category is imperfect. Reopen it only as an explicitly approved,
separate quality work item with a defined naming benchmark and no changes to
locked Detection identity or membership.
