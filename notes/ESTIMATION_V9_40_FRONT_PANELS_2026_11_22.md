# Estimation 9.40 Front panels live material recalculation

Status: published22November2026. Automated and deployment checks passed; owner authenticated UI acceptance pending. Existing work3.17.4.6.
Owner requested the visual correction and automatic row/cost rebuilding, then
confirmed missing thickness must use the existing fallback. Runtime baseV3.3
bcf9fdb4, records a7a6a405; protected release tags remain intact.

## Evidence and cause

Read-only evidence from the exact screenshot route is retained privately under
`outputs/front-panels-v3.4/production-witness.json`. Its Parts Check is saved;
there is no new model/OCR/Parts run. The source front stock's17mm thickness is a
construction assumption with no dimension refs. V3.3 copied that assumption as
an exact constraint when selecting another family/finish. There is no matching
17mm veneer position; the engine's generic200ILS assumption is rejected by the
V3.3 preview price guard. The picker retains the draft while old rows remain.
A network-blocked replay of the actual inputs/catalog reproduces this failure.

## Correction and approved scope

Keep the selector above Materials, alongside its label with16px gap. Draw its
chevron12px inside the right edge. No other table/input geometry changes.
For an explicit replacement, retain a thickness evidenced by the drawing; clear
only missing/assumed/default thickness in the effective material demand. Reuse
active Israel-backed Material Engine defaults for the chosen family/finish.
Use family/specifications as identity rather than requiring catalog names to
contain the English UI label. Original source Parts remain immutable.

A generic approved default must also fill a missing pricing fact when existing
facts already agree with that default. Existing logic rejected even matching
MDF/raw facts because they were outside the applicability map. Permit agreement
with the linked default; keep conflicting explicit thickness/board types rejected.
No price, catalog position, database schema or file-specific rule is added.
The applied catalog default is recorded in the material purchase trace; source Parts dimensions remain unchanged. Source restoration retains the exact original specification.

## Verification contract

Retain every V3.3 selector/save/approval case on1280/390px: four choices, explicit
other source, read-only preview, row/price/full-cost rebuilding, rapid changes,
failed preview/retry, Save/reopen, a newer draft during Save and APPROVE during
preview. Add16px label gap,12px chevron inset and document identity preservation.
Backend checks distinguish explicit and assumed thickness, matching generic
defaults and explicit conflicting facts. Replays compare all unedited Lev1/Lev2/
Adda stock signatures withV3.3. Exact-SHA local/remote full gate and actual served
Core/wrapper builds remain mandatory. Authenticated owner UI acceptance is open.

## Scoped update, clarified by the owner

The owner explicitly rejected a complete recalculation and the parallel full-
catalog experiment. That experiment is not shipped; its diff/timing are retained
only as diagnostic evidence. Use the original saved plan and explicit front
source facts. Resolve only the chosen material family, then only its linked
approved default positions when thickness is unknown. Material Engine receives
one changed front demand, not every object's materials. Replan only the source
and destination purchase baskets. Shared stock still removes/adds the front
quantity correctly. Unrelated purchase rows retain their complete saved values.

Do not read Parts Check inputs or run Detection/Analyze/Geometry/Parts/Labor on
selection. Existing Labor metrics are reused, totals and policy percentages are
updated by arithmetic. Save publishes only changed material facts/allocations
and the resulting snapshot. Future coating attaches to this same front group;
it remains unimplemented here. Manual norms and quantities retain their existing
incremental calculation path. Source restoration reproduces the original basket.

## Version correction

Git history's last Estimation cycle release is9.39 (15faa779). Later Labor V1-V3
versions were incorrectly used as the whole Estimation release number. Resume
the cycle sequence at Estimation9.40. Historical V3.2/V3.3 tags/records remain
unchanged. Internal agent/component versions and work3.17.4.6 are independent.
The unshipped V3.4 name is superseded; it was never published.

## Candidate verification

The exact saved production route passes a read-only server preview: only
mdf_hdf catalog records, unchanged persisted plan and unchanged source Parts.
Full Parts/material rebuild functions and Labor calculation are replaced by
throwing sentinels in this check. Final measured preview2.567s plus receipt0.591s
(21 reads), versus the rejected full path21.164s plus1.621s (63 reads).
Front stock resolves to approved Veneered MDF18mm, three sheets at692.58912ILS,
2,077.77ILS for that purchase line. Display formatting still uses whole money.
This is this saved witness, not a production write or a fresh recognition run.

Calculation browser checks pass39.318s at1280/390px. The fixture now seeds a
genuinely completed estimate's saved Labor before opening the card, rather than
calculating Labor during its first material preview. All previous Save/failure/
retry/rapid-choice/Approve assertions remain. The initial incomplete fixture
failed and is retained under focused-incremental; no assertion was relaxed.
Unedited saved Lev1/Lev2/Adda stock signatures matchV3.3. Actual paid calls:0.
Final local/exact-SHA gate and deployment evidence are recorded after completion.

The active card retains one trusted server-side preview, scoped by estimate/
object and the exact persisted-plan hash. Rapid changes patch that draft; Save
reuses its already-priced result instead of resolving the catalog again. New
purchase rows can be edited before Save. A stale base is rejected and repriced
against the current saved plan. No client-supplied plan, new polling or database
table is introduced. Existing numeric drafts remain incremental. Regression
checks cover fresh/stale preview reuse and a new purchase row in the same Save.

Initial commit15e1fa16 was blocked before publication: its new build label
exceeded the existing80-character observability contract. Local units had
562 passes/one marker failure. Shorten only the shared Core/wrapper label; retain
the same limit/test and every calculation change. The corrected exact SHA must
pass the entire gate. Production stayedbcf9fdb4 throughout.

## Publication,22November2026

Runtimef99d17b3ccaf65596b2c6e574d102064edb19fc2, release tag
`estimation-v9.40-2026-11-22`. Build:
`estimation-v9.40-b20261122101923-fronts-objects-v2.7-detection-v8.4.29`.

- Clean exact-SHA local563 checks/nine browser suites passed251.807s.
- Exact-SHA GitHub563/nine passed320.540s: run45011971041, job137176043571,
  artifact14750540556, retained in `ci-f99d17b3/`.
- Existing publisher verified the trusted success and active no-bypass remote
  ruleset27499066 before advancing main frombcf9fdb4 to f99d17b3.
- Railway/Core deployment7977386711 succeeded10:28:23UTC. Actual executable
  Core/wrapper, meta and version endpoint matched10:28:34UTC, HTTP200.
- Evidence: `outputs/estimation-v9.40-front-panels/`. Earlier private diagnostic
  attempts, saved controls and guarded real read-only preview remain under
  `outputs/front-panels-v3.4/`; that was the superseded candidate label.
- Source backup:813 files,4,654,216bytes, exact byte/CRC check; SHA256
  `18736f6f7ee138a35891612004106b98142c0d624a88172ce66a814339741c14`,
  `backups/estimation-v9.40_front_panels_marker_fix/`.

Objects V2.7 workflow/profile code and all original required UI cases remain
protected. No Detection prompt/model route or source Parts report was changed.
No paid call or production-project write was used for verification. Public
browser proof is anonymous Login; the actual estimate backend was exercised
read-only and the interactive matrix used the real local UI with synthetic data.
Owner should use the same saved estimate: switch Front panels, inspect the
changed stock/amount, edit the new row if needed, Save/reopen and APPROVE.
A new upload or model run is unnecessary. No new accepted checkpoint is declared.
Coating remains the next separate block, with its rules/rates still to agree.

## Owner-approved diagnostic rollback,22November2026

The owner requested exact V3.3 production restoration before another fresh
full Lev2 run. Restore application and test source frombcf9fdb4, including its
original build identity, without a Git history reset or forced main push.
Retain9.40 runtime/tag/records and the remote mandatory gate. This rollback is
the same work3.17.4.6, not a new9.41 feature release. Objects V2.7 is the next
owner-selected baseline only if this fresh control fails. No speculative fix,
model prompt change or new loading overlay is included in this experiment.

Read-only evidence: last priced Lev2run_e030ad3ba80a4fec9ac410b3e5bb0a83
(21November16:49UTC) has110 Parts/nine blocks/no unpriced demands/no assumptions;
newrun_f4eb3f589fcb4f18a0d548e3a6a7127d(22November10:33UTC) has102 Parts,
unbound block depths and worktop area, two unpriced demands and two slide
assumptions. Both are reproduced offline with saved provider responses and
network blocked. Source PDF, numeric Detection inventory and the Front request
fingerprint match; Front responses differ, including omittedC11 in the failed
run. Geometry source is byte-identical across the two runtime versions. Failure
is observed on9.40, but introduction by9.40 is not established. Private evidence
is underoutputs/estimation-v9.41; this directory name does not assign a release.
The requested Changing material overlay remains pending after this diagnostic.

Publication requires a new fast-forward rollback commit with exact V3.3 runtime,
clean local/full exact-SHA CI gates, the existing verified publisher and actual
Core/wrapper identity. Fresh recognition acceptance remains the owner's next
test; old saved controls alone cannot establish it.
