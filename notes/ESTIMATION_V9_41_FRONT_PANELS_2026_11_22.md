# Estimation 9.41 Front panels and immediate material feedback

Status: published22November2026, owner authenticated UI acceptance pending.
Existing work3.17.4.6. The owner approved
bringing the agreed material-selection changes onto the successful V3.3 base,
with the requested Changing material cover and no unrelated changes.

## Base and protected outcome

Production rollbacka6158588 restoresbcf9fdb4 V3.3 exactly. Its fresh owner
Lev2run_44832c1b2f014a07a3b17ec7bb21be99 has nine blocks/110 Parts, no missing
part dimensions, no unpriced demand or Assumption Fallback. Numeric part facts,
full block envelopes and purchase quantities/prices match the prior priced
control. Base materials10761.85ILS, policy-inclusive materials11407.56ILS,
full self cost12940.29ILS ex VAT. Preserve this source; no manual repair or
benchmark count enters the pipeline. V3.3 remains the independent rollback.

The9.40 fresh failure and V3.3 success do not establish release causality.
Front/Block Planner/Geometry/Detection code is byte-identical between them.
The failure's missing Front contour prevented plan binding; this release does
not claim to have removed all model variation or repaired that separate
recognition dependency. Keep this distinction in owner-facing results.

## Approved changes

Reuse the already reviewed9.40 point-update implementation and its regressions.
Keep Front panels beside its selector(16px gap, chevron12px inset), four material
choices and the exact source when outside those choices. Apply approved catalog
fallback only to an unknown/assumed thickness; preserve evidenced dimensions.
Original Parts stay immutable. Family/specifications identify replacement stock.

Only the selected front demand and its source/destination purchase baskets are
repriced. Saved Labor and unrelated rows stay intact; totals/policy amounts use
arithmetic. Save reuses the trusted preview and rejects stale bases. No new
Analyze, OCR, Parts, Geometry, Labor or all-catalog call on selection. The future
coating position remains deferred until its rules are agreed.

Show one dark Changing material… status synchronously when the existing preview
starts or a newer material is queued during Save. Reuse that request's state;
no new callback, timer, observer, worker or polling. Keep the same cover through
superseded replies and remove it only after the current rows/totals reconcile,
or on error, existing90s timeout or card cleanup. Preserve the draft/error/retry
and existing rapid-selection/APPROVE behavior. The cover adds visual feedback,
does not trap focus or disable those controls, and uses a polite status role.

## Verification

Protected pipeline files, Objects V2.7 Loading, source geometry/counts, unrelated
materials, numeric editing, Save/reopen, approval, auth and navigation retain
their existing gates. Use the complete nine-suite local/exact-SHA GitHub gate,
trusted no-bypass publisher and actual executable Core/wrapper verification.

Initial focused Python checks:121 passed. Real local UI Calculation checks pass
48.783s at1280/390px. Assertions cover immediate full-viewport cover, one status,
success removal, failure removal, rapid choices, a new choice during Save,
APPROVE while previewing, accelerated existing-timeout cleanup and retry with
the draft retained. No production timer or deadline changes. Retain screenshots
underoutputs/estimation-v9.41/focused/browser/.

Network-blocked comparison runs the complete saved material calculation in
separate V3.3 and candidate module trees. All original purchase signatures and
costs match on Lev1(29 Parts), Lev2(112), both Adda objects(24/133) and the new
owner Lev2(110). Reports are byte-unchanged in memory. These are saved-evidence
regressions, not fresh model-recognition tests.

Read-only actual-owner Lev2 previews price all four choices. Full-cycle/Parts/
Labor functions are replaced by throwing sentinels; PostgREST rejects every
write. Existing source Parts and all unrelated purchase rows remain identical.
Preview/receipt: LDSP0.848/0.680s, veneer2.593/0.672s, MDF1.995/0.665s,
Plywood2.146/0.651s. Replacement previews read only19 resources. Persisted plan
is unchanged. No paid call or production-project edit. Evidence:
outputs/estimation-v9.41/real-readonly-previews.json and material-controls-comparison.json.

Candidate build: estimation-v9.41-b20261122111449-fronts-objects-v2.7-detection-v8.4.29.
Authenticated owner UI acceptance is separate from local synthetic UI and
read-only backend verification. Keep records/tags of9.40 and the diagnostic
V3.3 restoration.

## Verified publication

Runtime077264c004dcbc70e5c369d1c776658981684db0, release tag
estimation-v9.41-2026-11-22. All606 protected non-Markdown files remain identical
to the published V3.3 source; no source recognition/geometry/Loading change.

- Clean exact-SHA local563 checks/nine suites passed319.126s.
- Exact-SHA GitHub563/nine passed321.986s: run45016775451,
  job137190674163, artifact14752457309, retained inci-077264c0/.
- Existing publisher checked active no-bypass ruleset27499066 and the trusted
  exact-SHA success, then advanced main froma6158588 without force.
- Core deployment7978005541 succeeded11:27:15UTC. Actual executable Core/
  wrapper/meta/version match9.41 at11:27:53UTC; health and wrapperHTTP200.
- Source archive814 files/4,663,099bytes, byte/CRC verified, SHA256
  95b79b5109c81c8fbb366e73463a24c466597734fd2bcf79f109b6fabe749f45.
  Private backup record: runtime-backup.json underoutputs/estimation-v9.41.

No failed candidate or relaxed gate. Full saved controls and guarded actual
four-choice previews passed; no paid model call or production-project edit was
used for verification. Public browser proof is anonymous Login. A fresh full
recognition run on9.41 and the owner's authenticated UI trial are still separate
acceptance checks. The owner can first reuse the existing completed Lev2,
switch Front panels, inspect updated stock/totals, Save/reopen and APPROVE.
Coating remains unimplemented. This is a verified release, not an owner-accepted
full checkpoint or proof that the latent Front omission cannot recur.
