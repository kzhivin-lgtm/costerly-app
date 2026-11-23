# Labor 2.10: checking interfaces and packing

Owner-approved feature, 23 November 2026. Base: accepted Estimation 9.48,
runtime `862e28f0`, existing formal work reference 3.17.4.6. The owner requested
Labor 2.x. Historical 2.8/2.9 tags are occupied; 2.10 is the next available minor,
checked on GitHub. Old versions and checkpoints are not renamed or reused.
Status: published and verified; owner production acceptance pending.

## Approved behavior

| Class | Maximum sorted sides, mm | Planned man-minutes |
| --- | --- | --- |
| S | 600 x 600 x 400 | 10 |
| M | 1200 x 800 x 600 | 15 |
| L | 2000 x 1200 x 800 | 20 |
| XL | Beyond L | 25 |

Choose the smallest inclusive three-axis class, independent of orientation.
One complete trial mating/checking/separation cycle uses 30 planned man-minutes.
Norms are total worker effort: 25 man-minutes means 12.5 elapsed minutes for two
workers. No second crew, pace or working-share multiplier. Existing 50 ILS/hour
and one 25% payroll charge remain shared. Materials' Packaging allowance remains.

The fourth Labor stage contains read-only Trial Fit and Separation and Packing
rows in existing Hours/Pay/Taxes/Total columns. Four stages, collapsed roots,
old Sheet Processing/Block Assembly editors, Save/Saved and navigation stay.
Browser draft preview keeps both new fixed leaves exactly once when old hours
change. The same calculation feeds Labor, Overhead, full Self Cost, Objects and
Object Detail. Front material replacement preserves saved Labor, including new
preparation data when present and legacy snapshots when it is absent.

## Source evidence and limits

No Detection, recognition prompt, model selection or paid request change.
After the existing Parts pipeline, save additive preparation evidence in the
immutable report. Reuse explicit structural/component attachments and the
existing native shared-edge utility. At least 4 crop pixels of shared boundary
qualifies; a point touch does not. Retain view/contour IDs and contact length.
This is a budget geometry basis, not a workshop fastener specification.
Do not infer all pairs from a shared component or use block count minus one.
Reverse/repeated sources merge all proofs into one work unit. Explicit distinct
interface IDs remain separate. Missing representation remains partial.

Legacy reports without this evidence keep checking unknown. Opening them never
reruns recognition or reconstructs a missing graph through another paid call.
New Parts runs retain the graph automatically. Packing reads saved envelopes;
side depth plus front thickness can fill a missing depth. One known side above
2000 mm proves XL without inventing the remaining axes. Loose object-level parts
remain identified bundles using their saved dimensions and physical quantities.
Unknown units stay listed with unknown time. No Parts/envelope/material demand
is rewritten to fit the new labor calculation, and no new UI warnings are added.
New component failures are isolated using the existing error-boundary pattern.
No new callback, timer, poll, reader pool or separate Save operation.

## Verification and retained failures

Evidence: `outputs/labor-preparation-packing-20261123/`.
Focused tests cover all class boundaries/rotations, missing/invalid geometry,
man-minutes, quantities, loose bundles, unknown-row retention, edge versus point
contact, repeated/reverse evidence, distinct interfaces, additive pipeline/failure
isolation, old manual keys and one inclusion in full Self Cost. Calculation adds
the real M/15min row and retained fixed costs during old-hour edits/reopen at
1280/390. Previous error/retry, blur, Front panels, copy-quantity, layout and auth
assertions remain. Labor-ready scenarios intentionally gain packing; unchanged
legacy snapshot/fresh-worker scenarios retain their original exact amounts.

Offline saved Ada replay blocks network. Native evidence took 127.226 ms in that
run. Object 1: one interface/30min and packing75min. Object 2: six interfaces/
180min and packing140 known minutes. B02, B07 and closure-A05 have unresolved
packing geometry and remain listed with unknown time. Removing the additive
field returns identical Parts, and full Material Plan before/after is identical.
No paid/model call or production-data write was made.

The first browser failure exposed Pandas3 rejecting a fractional1018.13 cost in
an integral Objects money column. Only integral money columns now convert to
float before assignment. A regression test uses the actual matching-source
precondition. The existing26px footer assertion saw the failed transition and
was retained; no CSS repair or relaxed tolerance was used. Legacy Front panels
and fresh-worker fixture amounts were distinguished from matching-Labor-ready
amounts instead of changing their old expected results. An overlong draft build
ID was shortened under the unchanged80-character limit. Failed artifacts remain.

Full local/remote gates, validated source backup, protected promotion and actual
Core/wrapper/meta/version receipts must pass before publication. Publication is
not an accepted checkpoint until owner production acceptance. Rollback reference:
accepted9.48/runtime862e28f0 and its full immutable checkpoint.

## Local candidate evidence

Build: `labor-v2.10-b20261123184340-prep-pack-detection-v8.4.29` (55 characters,
all four Core/wrapper markers match, unchanged80-character observability limit).
Full local gate passed991 checks and all ten browser suites in436.242s:
`full-local-02/gate-report.json`. Afterward a narrow invalid-interface guard
was tightened: invalid/conflicting quantities remain unknown and all conflicting
source refs are retained, rather than a confirmed zero or guessed charge.
The complete Python list then passed994 checks in16.946s. Normal-input browser
paths were unchanged by that guard; exact-SHA remote CI will repeat all ten suites
against the final candidate. Initial failures and unit/browser logs remain under
the same private evidence root. Desktop/mobile Labor screenshots were inspected.

## Publication receipt

- Runtime: `20e34aa1c208f0c97b22a87afe80a9f272078992`. Build: `labor-v2.10-b20261123184340-prep-pack-detection-v8.4.29`.
- Exact-SHA clean remote [UI release gate](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/45243888030/job/137935456073) passed 994 Python checks
  and all ten browser suites in 362.833s, artifact 14853916450.
- Protected publisher verified active no-bypass main ruleset27499066 and promoted
  that exact commit. Remote enforcement is separate from the local checks.
- Actual Core, executable wrapper, meta and version.json match at
  2026-11-23T19:08:50.531617+00:00; static version endpoint returned HTTP200.
  This is a read-only build probe, not an authenticated owner workflow.
- Candidate source backup:834 files/4,764,460 bytes, existing helper exclusions
  and5MiB cap preserved, all archived source bytes compared.
- CI artifact, logs, source backup receipt, promotion, deployment and actual served
  identities remain under the private evidence root. Initial failures are retained.
- No paid call, production-project test write or accepted-checkpoint replacement.

Owner should validate a fresh Estimate on app.costerly.ai. New Parts reports retain
physical interface evidence; historical reports lacking it cannot supply that
new checking field. Existing saved dimensions can already feed packing. Unknown
packing geometry remains visible and unpriced rather than invented or omitted.
