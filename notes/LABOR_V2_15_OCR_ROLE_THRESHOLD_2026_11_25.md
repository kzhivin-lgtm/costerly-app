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
These observations establish build identity, not fresh authenticated Ada
acceptance. The owner's next new Upload is still required.

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
