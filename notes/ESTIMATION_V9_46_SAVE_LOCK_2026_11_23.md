# Estimation9.46 explicit Save lock and shared update loading

Status: candidate23November2026, existing work3.17.4.6. Deploy authorised by owner.
Checkpoint remains on hold. Preserve9.45 runtime1f872f01, its pending records and
all earlier accepted source/behavior. No Parts/material/cost/Detection change.

[verified] Object Detail prepareApproveSnapshot sets activeSave.approveAfterSave
when Approve is clicked while Save is pending. The receipt later consumes that
flag and navigates. Back was blocked logically, but links were not visibly grey
or excluded from Tab order. The new lock uses the existing non-preview Save
lifecycle: immediate aria-disabled/tabindex/background/color, a capture guard
against activation, and no queued approval from explicit-Save clicks. Success,
failure,90s timeout and teardown restore link attributes. Save itself stays on
card and green Saved only after receipt. Direct Approve on a dirty draft and
Approve during read-only material preview retain their accepted semantics.
No additional timer/poll/server callback or write. The listener is card-scoped,
constant-size, event driven and removed on teardown. All footer anchors cover
Back to Objects/APPROVE and future equivalent return links, without inventing a
new Back to Object Details control that does not exist in the current card.

[verified] Wrapper forceDeployRefresh wrote Updating app directly onto a mask
with system-ui16px. Core loaders use IBM Plex Mono24px/400/1.18 line height and
-0.045em spacing. Shared CSS now has one source ui/workflow_status.css; Core
injects it into the existing style and wrapper embeds it. A parity test rejects
drift. Wrapper/recovery statuses use the shared span class, with existing mobile
size rule. The wrapper registers the same existing Google font stylesheet once
per document, browser-cache/cancellation owned, no JS font wait or API request.

[verified] Existing New Estimate witness7ec536e1-359e-4469-86b2-5d7947e781d9
at14:11:35 Israel23November took3.7761s. Wrapper9.44 reconnected to Core9.45,
browser-session restored; auth0.687758s and platform-header0.505571s. Earlier
051a7656 took4.6189s, including1.001308s token refresh. These are deployment/
cold-session witnesses, not warm reset benchmarks. New Estimate resets local
session/file generation, clears route and renders a new native Streamlit file
input; no new analysis/model is launched. Immediate presentation and immediate
interactive uploader differ. No separate uploader/auth bypass was introduced.
Warm/cold staged measurement is retained as the next performance proposal.

Verification scope: actual production screens/wrapper with local synthetic data,
Save→Approve/Back mouse and keyboard while write delayed, success/failure/retry/
timeout cleanup, shared font style and old wrapper/auth recovery, and all previous
nine suites. No paid provider or production project mutation. Authenticated owner
acceptance remains distinct from these tests and anonymous live build identity.
Every corrective commit/deploy must include Estimation9.46 in its title. Failed
candidates must remain blocked; preserve exact-SHA gate/artifacts and source
comparison. No checkpoint tags/archive/bundle are authorised this iteration.

Initial candidatec47aacff was blocked in the new immediate-grey UI assertion.
Logical disabling worked, but existing140ms color/background transitions retained
the old first-frame paint, and link-state important colors overrode disabled text.
The scoped Save-lock state now disables that transition and wins the existing
important link color. No assertion or deadline is relaxed; failure logs retained.

Candidate079faac7 passed607 unit checks and all Save scenarios, but the new
wrapper style probe found the unavailable-storage recovery path replaced the
shared status span with a bare text node. Retain the same label for the retry
message, preserving its shared typography and the existing retry behavior.
No deadline/assertion is relaxed and no new observer/request is introduced.
