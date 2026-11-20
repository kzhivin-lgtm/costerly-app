# V3.2: source-owned labels and arrow contact

Owner approved V3.2 and immediate gated publication on20November2026. Restore
latest functional V3.1 (`f051b8cc`), including Materials+Labor+Overhead and the
accepted authentication/grouping behavior. Detection matches V3.1 exactly.
This is an Estimation release label, not reuse of a Profile work number. Retire
the temporary V1.2.21 rollback manifest and restore the normal complete UI gate.

## Problem and final change

A missing or wrongly owned direct mirror label changes the native Block plan.
The corner geometry requires one mirror-upright region, so a wrong neighbouring
contour can leave the whole cabinet without usable geometry. Prompt-only review
was insufficient: a fresh request exactly matching the earlier8/8 experimental
variant still assigned C14 instead of C19 and produced zero cabinet dimensions.
A preliminary expanded packet also added an extra mirror. Both approaches were
rejected before publication. Internal contact metadata no longer inflates the
model's original geometric packet.

The final ownership pass reads original PDF pixels independently for every
closed native contour. It receives a high-resolution crop masked to that
polygon, with its geometric ID supplied outside the pixels. It cannot establish
ownership from a label visible only in a neighbouring panel or the overview.
The original full drawing, model readings and all other source evidence remain
available and are retained. The original direct-label claims are saved for
comparison; the contour-owned transcription controls active direct bindings.
Leaders and opening-stroke readings remain unchanged.

Every supplied contour must be recorded as reviewed. There is no expected
mirror quantity, file-specific name or fixed C-ID in the algorithm. Native
panels are covered in batches of at most90 plus two contextual reference images,
within the documented API image limit. Crops use the existing3x PDF zoom, capped
at1200px per side. For Ada there are89 contours and one extra Haiku request.
No additional OCR, provider change, timer or polling is introduced. The pass
runs within the current calculation, using the existing120s provider timeout;
there is one pass per batch, no retry loop. It does not run on saved-estimate
reopening or on routes without a marked native view.

Unresolved ownership uses the existing front_role_review_pending and partial
material-cost path. It does not fabricate a complete cost. Additional non-mirror
transcriptions, such as an open-shelf note, are retained separately in the audit
rather than dropped or converted to mirrors. Full provider-response diagnostics,
initial readings, per-contour polygons and image hashes are preserved.

Native arrow tips now explicitly admit both interior hits and boundary contact,
using the existing0.75px snap tolerance. On a shared edge, the local incoming
shaft side supplies ownership, or a uniquely entered face when the shaft is
outside. Genuine ambiguity retains every candidate without an arbitrary owner.
The same rule serves component-callout Block ownership. On saved Ada geometry,
all122 former hits remain and9 additional edge contacts receive owners.

## Native shell ownership

A subsequent complete fresh trial had correct direct labels but still lost
geometry: Native Locator assigned panels from a neighbouring display cabinet
to the return-door Block. A singleton model claim previously occupied those
contours before geometric growth could attach them to the actual cabinet.

The final source admission checks return-band additions against the existing
native assembly plane. An outside-plane claim needs positive native contact;
otherwise it remains recorded as a proposal while native contact growth can
ground the contour to its actual owner. Existing positive side contact remains
valid, and established core members are not changed. The original model proposal
and grounding review are persisted in Parts Check. The0.04 span margin and
contact thresholds reuse the existing growth rules, without Ada-specific IDs.

The failed fresh reply set and two successful sets were replayed through this
deterministic admission. All10 prepared requests in each replay exactly match
the captured fresh requests. All three final results are7Blocks/19dimensions/
133parts with no unpriced materials and identical material totals. A separate
completely fresh run of the final code is recorded before promotion. The rejected
direct-contact-only experiment made no ownership changes and was not published.

## Verification and publication

Synthetic tests cover shared/sloping edges, native pixel masking, complete
contour coverage, bounded batches, recovery from an empty reading, correction
of a neighbouring-panel claim, preserved original evidence and honest ambiguity.
Two full frozen-response controls with the actual new model reply restore both
empty and wrongly owned readings to7blocks/19dimensions/133parts, with no
unpriced materials. The three-panel source inspection confirms C14 is blank
while C16/C19 actually contain the printed word. Saved LF1/Lev2 native packets
have no leader tips; their stored bindings are unchanged. This is not a fresh
LF1/Lev2 recognition acceptance claim.

Final full Ada trials and the expanded normal UI gate are recorded in private
release evidence. Do not pool rejected prompt-only trial results with final
contour-owned trials. The first local UI launch failed because Node was missing
from PATH; existing Node24 and locked UI dependencies resolved the environment.
An earlier normal gate passed447 Python checks and all seven suites; the final
gate adds the relevant Parts/geometry/material checks and ownership tests.

Use exact-SHA GitHub UI release gate and the verified publisher before main.
Check actual Core/wrapper builds after deployment. The release receipt and full
private evidence live in outputs/estimation-v3.2-20261120 in the task workspace.
A new production Ada estimate and owner acceptance remain distinct from local
and CI checks. Saved old estimates retain their original recognition results.
No accepted production checkpoint is claimed before owner acceptance.

Service constraints were checked against [Anthropic's vision documentation](https://platform.claude.com/docs/en/build-with-claude/vision).

Backup validation: the complete source snapshot with DEFLATE level9 exceeded
the unchanged5MiB limit by19,366 bytes. It was rejected by the helper. The same
complete source is repackaged through the helper with lossless ZIP/LZMA, keeping
the exclusions, required-file and size validation and checking extracted bytes.
No source files are removed to meet the limit.
