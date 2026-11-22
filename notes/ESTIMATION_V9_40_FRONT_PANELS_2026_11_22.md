# Estimation 9.40 Front panels live material recalculation

Status: implementation candidate, publication pending. Existing work3.17.4.6.
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
