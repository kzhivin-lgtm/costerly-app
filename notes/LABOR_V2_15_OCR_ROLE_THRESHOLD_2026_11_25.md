# Labor2.15: accepted OCR stock-role threshold

Owner approved25November2026, existing work3.17.4.6. Base is the complete
Labor2.14 checkpoint: runtimefc3e5827, records2948fa8a. The owner requested
lowering only stock-role string similarity from0.78 to0.75 and publishing with
a new Labor version before his fresh Ada run.

The number is a SequenceMatcher role-label similarity, not OCR confidence.
Today OCR returned KapnycHbI instead of the previously accepted Kapnychbui.
The former scores0.7777778 and contains the same explicit16mm stock value.
Rejecting that label leaves carcass thickness unknown and prevents dependent
panel dimensions from being computed. Catalog defaults occur later and do not
rebuild those missing dimensions. The threshold was introduced in production
by88f261dd7 on12November2026 and retained through2.14.

## Exact scope and protected behavior

One runtime comparison changes from0.78 to0.75. Role uniqueness, contradictory
thickness rejection, second-word Material recognition, dimensional-expression
exclusion, input identity and evidence refs retain their existing checks.
No prompt, model, OCR payload, Detection, geometry formula, material price,
default, Labor norm, Overhead formula or UI interaction changes. The accepted
PDF is a separate local presentation artifact, not a product PDF generator.

Core, executable wrapper, wrapper metadata and version.json are stamped
`labor-v2.15-b20261125123857-ocr-role-075-detection-v8.4.29`.
The2.14 checkpoint stays immutable. Rollback uses the existing trusted exact-SHA
gate and publisher tofc3e5827, without rewriting saved OCR or estimates.

## Verification and acceptance boundary

Focused display-parts tests:9 passed. New retained fixtures cover today's OCR,
the exact0.75 boundary, below-boundary text and another construction word;
existing conflict, identity, material and geometry tests are unchanged.
Offline saved-Ada replay keeps the original OCR and all10 provider responses,
blocks network and compares every Parts row to the independently verified
one-word diagnostic. Historical same-SHA OCR inputs cover30 runs. Private
evidence is retained in the previous workspace's
outputs/labor-v2.15-20261125/saved-ada-replay/.

Before publication, require the complete local UI contract and exact-commit
GitHub UI release gate, active/no-bypass remote main protection and matching
served Core/wrapper builds. These checks do not claim a fresh paid OCR run.
Owner production acceptance follows his new Ada run after publication.

## Publication result

Published runtime `bae0e8998a7554bf2da53b04dedb4ca2ae67e803` on25November2026.
The full local gate passed1019 Python checks and all10 browser suites in384.128s
on the clean exact commit. The same trusted
[GitHub UI release gate](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/45616734770/job/139213955859)
passed the full contract in433.484s; artifact15023097056. No test, timeout,
layout assertion, protection rule or monetary tolerance was weakened.

The existing publisher separately verified the actual active/no-bypass main
ruleset27499066 and promoted only this SHA. A fresh public browser confirmed
Core, executable wrapper, metadata and version.json all serve the2.15 build.
These observations establish build identity. The owner's subsequent fresh Ada
run is recorded below as a separate production witness.

Saved replay used today's unchanged OCR and ten frozen provider responses with
network blocked. All Parts match the independently verified one-word diagnostic:
24/133 rows,20/89 rows with length and width. All64 latest object-input revisions
across30 same-file historical runs preserve their former stock interpretation,
except the intended recovery of today's16mm carcass note. No new paid call,
production estimate update or saved OCR mutation was made. Prior offline cost
for the matching recovered Parts is15051.32 ILS net; a fresh run may differ.

Full2.14 runtime/records tags and private archive remain unchanged. This release
is not a new owner-accepted full preservation checkpoint. Publication records
are committed separately on the release branch without another runtime deploy.

## Fresh owner Ada comparison, 25 November 2026

[verified] Owner run `run_a75c5dd7ff4a4b0882e785d73aaa6fbe`, uploaded 12:56:02 UTC
(14:56 Israel), produced estimate
`run_a75c5dd7ff4a4b0882e785d73aaa6fbe_estimate_20261125125614` on the exact 2.15
build above. Source PDF SHA256 remains
`09dc963c8b7c9aa341085ae4dbc1bbd31be606ad9f94c95136ecdc646183d4b3`;
native audit remains `e15ba74bb9709739f394baef3acb1ac67e5df0349c08f278364f87592503e8fd`.
Downloaded Parts artifact SHA256 is
`3bb09cd9ae3120d90dce06a23f302095e3e994552b6fbfb03da468ac0b787083`.
Both objects' Parts role/block/quantity/dimensions signatures match the prior
one-word-corrected offline control, 24/133 rows and 20/89 raw rows with length/width.
All monetary stages for each object match its forecast to the cent.

| ILS ex VAT | Prior full V3.2, 20 Nov | Failed Labor 2.14, 25 Nov | Fresh Labor 2.15 |
| --- | ---: | ---: | ---: |
| Materials | 11702.74 | 5712.60 | 11985.76 |
| Labor including payroll charges | 1381.94 | 1599.65 | 1825.40 |
| Overhead | 174.93 | 799.28 | 1240.16 |
| Self Cost | 13259.61 | 8111.53 | 15051.32 |

Current VAT is 2709.24, total 17760.56. Vanity counter is 3597.93 net;
Corner display cabinet is 11453.39 net. Cabinet Materials 9101.88 exactly match
the prior complete V3.2 snapshot. Both objects have no unpriced material
requirements; the material plan has no unresolved requirement IDs. Its remaining
review reason is `cb_parts_review_required`, not an unpriced-material issue.

Differences from V3.2 are separated from the repaired OCR rejection:

- Materials +283.02, entirely on the vanity. Its Plywood 18 per-object purchase
  projection changes 2 to 3 sheets, cost +267, with formula materials +16.02.
  Current Parts additionally include a 3035x100 mm plinth. The project-wide
  Plywood 18 line stays 3 sheets/801 in both snapshots. This comparison does not
  establish that the plinth alone caused the per-object allocation change.
- Labor +443.46, including 442.72 of newly included Preparation and Packing and
  0.74 in vanity Sheet Processing. Cabinet Sheet Processing and Assembly match
  V3.2 exactly.
- Overhead +1065.23. Saved capacity is now 1200h versus 2016h, and current snapshots
  include 3% Warranty and 3% Management buffer reserves, absent from old snapshots.
  Current reserves sum 851.96. Additional labor also enters allocation.

[verified] The specific material-loss mechanism is recovered in this fresh
production witness. This is one successful witness, not proof of future OCR
stability or independent validation of every drawing quantity. Cabinet packing
remains partial: `packing_dimensions_unresolved` for B02, B07 and closure-A05.
Review that separate gap before treating all Labor as complete. No further fix,
new paid call or production data write was made for this comparison. The owner
called the result more plausible, not blanket acceptance of every cost component.

Private evidence: previous workspace outputs/ada-labor-v2.15-owner-run-20261125/,
especially comparison-summary.json and immutable source snapshots. Existing 2.14
full checkpoint remains the last owner-requested full preservation checkpoint.
