# Objects V2 scoped interface contract

Owner approved the final desktop drawing and publication as Objects V2 on
21 November 2026. This is an interface release over accepted Estimation V3.2,
not a new Detection, costing, procurement export or revision-storage design.

Approved change: preserve the Objects Estimation title. Move the existing
navigation rail below it, with the existing Total lap / TC / R1 / R2 metrics
immediately after Sign out (24px gap). Show three stages on the next row.
Keep exactly three equal-width bottom actions across the existing content
width: Back to file review, Set prices, GENERATE PROPOSAL. Hide the diagnostic
Parts Check action on this screen. Add no Example project / Draft,
Calculation dashboard, Next or Review all objects instruction.

Protected: original object rows, headings, quantity/sale inputs, original
Delivery/Installation axis and dimensions, summaries and subtotal/VAT/total
layout; calculation/source bindings/Detection; saved estimate reuse;
tenant access; existing navigation callbacks and the existing proposal
finalization/version operation. No speculative new version model or XLS.

| State/action | Result | Verification |
| --- | --- | --- |
| Empty or calculating estimate | First stage current, later actions unavailable | No invented completed review/cost, no paid call from header |
| Ready objects, incomplete review | Actual reviewed count; Set prices/generate unavailable | Existing Review and Approve routes retained |
| Last object approved | First stage done, Set prices available | Original card approval persists, returns to same estimate |
| Set prices | Confirm the current saved pricing basis | Original price write path remains unchanged; callback reads saved basis |
| Editing price after setting | Invalidate price confirmation and generation | No change to input appearance, normalization or costing |
| Generate proposal | Footer revalidates saved basis, calls unchanged final_approval | Existing ownership/idempotence/snapshot/PDF behavior retained |
| Failed confirmation/generation | No false completed stage; retry available | Existing native callback/error state; original input behavior retained |
| Back/header navigation | Existing callback and ready-correlated transition | No second navigation rail, extra model run or title movement |
| Saved finalized estimate | Third stage done; existing finalized operation disabled | Existing proposal availability preserved |
| Narrow viewport | Controls remain reachable | Desktop is the design target; existing regression paths remain covered |

Header metrics and stage placeholders reuse the existing Objects fragment's
refresh. No new polling loop, request or worker is introduced. The new header /
footer observes existing input events only to invalidate its price confirmation.
Original input handlers, requests, normalization, pricing rows and the existing
finalization/PDF use case are byte-identical to the accepted V3.2 source.

Owner reiterated this strict boundary during implementation. An experimental
pending-write tracker, serialized price writes and new submit acknowledgement
were discarded before publication. Their intermediate results do not establish
accepted behavior. This deployment does not repair or redesign central price
persistence. Protected body geometry is compared with accepted V3.2 at the same
viewport, including absolute document coordinates.

The prior accepted V3.2 tag is the rollback source. Local synthetic/browser
and exact-SHA GitHub UI gate are required before the protected publisher.
Matching live Core/wrapper builds are checked after publication. Owner
production acceptance remains separate from automated checks.

Local scope witness: at1440x1000 and2536x1244, the title, table/header, all
object/project rows, quantity/sale inputs and summary rectangles match V3.2
exactly (x/y/width/height). Bottom actions retain their original document y.
The table renderer, original input JS, estimation loader and finalization use
case are byte-identical. Existing pricing CSS before the appended header/footer
rules is unchanged. Screenshots/measurements: outputs/objects-v2-release-20261121
in the owner's Costerly handoff workspace.

The release synchronizes the wrapper's formerly stale HTML metadata with its
executable build. Auth-resume's synthetic wrapper must replace all occurrences
of that build, including metadata and the script constant, rather than only the
first. Only that fixture substitution changes; its auth assertions and production
auth behavior are unchanged.

Deployment verified21November2026: runtime4825750f, local exact-SHA full gate
531 checks/eight suites160.508s, GitHub531/eight172.31s. Required check:
https://github.com/kzhivin-lgtm/costerly-app/actions/runs/44895552737/job/136820313324
The publisher verified active ruleset27499066 without bypass actors and promoted
the checked SHA. Railway GitHub deployment7962256799 succeeded10:46:55UTC;
Cloudflare Pages494fda24-6c93-4a60-abc8-3f652c503ce3 delivered the wrapper.
The actual Core ready/build event, public wrapper script, HTML metadata and
version.json all reported objects-v2-b20261121102935-estimation-v3.2-detection-
v8.4.29 at10:47:22UTC, wrapper/health HTTP200. Verification used fresh Login;
owner authenticated saved-project acceptance remains pending. No new accepted
checkpoint and no model calls. Complete receipt: owner workspace
outputs/objects-v2-release-20261121/release.json.
