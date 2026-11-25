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
