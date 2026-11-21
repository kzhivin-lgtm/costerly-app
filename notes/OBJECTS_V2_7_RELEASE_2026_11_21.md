# Objects V2.7: overlapping Profile ready signals

Status: approved candidate, not yet published.
Base runtime: `82d5502689d83dfc8b75f3d41f50e350334c2815`, Objects V2.6.
Records/full checkpoint: `1a1b8f7f12872f5ca60a251a433e615594998642` and the
published V2.6 checkpoint tags/archive. No new hierarchical work block assigned.
Build: `objects-v2.7-b20261121215044-profile-ready-estimation-v3.2-detection-v8.4.29`.

The owner explicitly approved fixing only the diagnosed ready mechanism,
preserving transition protection and all other working behavior, then full
mandatory checks, successful exact-SHA GitHub gate and a new-number deployment.

## Change and protected behavior

Only `ui/workflow_transition.js` changes application interaction behavior.
Keep one observer and pending animation-frame check for an active transition,
retain receipts by run ID and select the receipt matching the actual render.
Profile additionally matches the existing metrics.profile_tab to the selected
native tab. Require the same current nonstale target and two stable frames.
Use that accepted receipt consistently for displayed state, completion and
build announcement. Do not cancel/replace a watcher for each arriving receipt.

No new observer, timer, request, polling loop, callback/rerun, worker or database
writer. Keep existing full/regional covers, timeout/reload recovery, controller
upgrade, host/protocol/trace/source checks, auth persistence and version refresh.
Objects/Object Details layout, all input handlers, Add Worker write/reset/cache
behavior, saved estimates, prices, proposal and V3.2/Detection code are unchanged.
The only other runtime-file edits synchronize the three build markers.

## Approved scenario matrix and verification

The earlier diagnosis and owner-approved proposal cover these deterministic
orders and readiness boundaries. They extend the existing Profile Save suite;
all nine original suites, original assertions/deadlines and142 navigation cases
remain required.

| Case after a persisted Add Worker | Required visible result |
| --- | --- |
| Worker-ready then Pricing-ready before a frame executes | One current Pricing completion, regional cover until ready |
| Pricing-ready then delayed worker-ready | Current receipt wins, old receipt does not strand Loading |
| Repeated old/new receipts | Exactly one correlated completion and one employee write |
| Ready before current DOM replacement | Keep cover, reveal only after matching render arrives |
| Stale nodes still present | Keep cover until obsolete nodes are removed |
| Receipt for a different render | Keep cover until current receipt arrives |
| Worker render present while Pricing tab selected | Do not accept worker completion for another tab |

Each forced case uses genuine fixture server receipts and production UI/handlers.
It checks employee persistence/reopen, preserved header, zero uncovered samples
before the actual Core-ready timestamp and one completion with the click ID.
Test-only delivery/DOM controls are absent from production. Fixture state and
ready/DOM failure evidence are retained in the normal UI artifact.

Before publication: syntax/focused cases, old-controller negative control,
clean exact-commit full local gate and full Linux GitHub gate. Publish only
with the existing verified publisher and active no-bypass remote rule, then
wait for actual served Core/wrapper/version/controller equality.

Private evidence: `.ui-artifacts/profile-ready-v27-release/`.
Focused canonical Profile Save and all7 forced cases passed in45.226s. All
cases recorded zero uncovered-before-ready samples and one employee write.
The exact V2.6 controller substituted only in fixture memory fails worker-first
at the unchanged10s deadline after the old happy path and successful employee
write,29.829s total. This proves the regression exercises the actual defect.
The initial focused setup run stopped before injection when a picker option
lay behind the unchanged embed footer. Only the new test helper now centers
that native picker; no footer/input/app change, assertion removal or timeout
increase. The initial failed setup artifact is retained separately.
Source isolation:614 other non-Markdown base files byte-identical. The three
metadata files match the base after only the literal build replacement; app.py,
company_profile.py and js_guards.py are unchanged. Full gates still required.

Initial candidate2c4ad23b passed the clean full local535/nine gate in268.222s.
CI44954109356 failed the pre-existing Objects Set Prices color assertion after
editing1850: the price was persisted and Generate Proposal disabled, but the
computed background still equalled the old green. No Profile failure or missing
write is claimed for this run. This candidate was blocked, never published.
An isolated browser probe using the unchanged actual base140ms background
transition and confirmed-color CSS, without a workflow controller, reproduces
the same immediate old color after stage2 changes to current; the color then
settles to white (204ms observed). The visual assertion must observe completed
CSS rendering, just as its existing enter-green check already does.
Only the test now waits up to1s for the full recorded unconfirmed color before
its unchanged not-green assertion. Original5s price receipts, immediate generate
invalidation and all layout/input/price assertions remain. No price/color/input
application code changes. Full final exact-commit gates remain required, not an
unchanged retry to ignore the failure. Evidence includes the first CI artifact
and `color-assertion-reproduction.json`. The final app source is byte-identical
to2c4ad23b; only test/records change. Final isolation excludes this additional
changed test and therefore retains613 other non-Markdown base files identical.
[Diagnostic evidence and historical uncertainty](PROFILE_LOADING_DIAGNOSTIC_2026_11_21.md).
The old CI's exact receipt order remains unknown. A forced reproduction is not
a retrospective packet trace, and a synthetic gate is not authenticated owner
production acceptance. No paid call or production project write is planned.
