# Costerly AI UI guidelines

These rules apply to every Costerly AI screen and workflow. A missing interaction
state is a product defect, not optional polish.

## Accepted workflow reference

The owner requested a full preservation checkpoint of current Objects V2.6 on
21November2026, runtime82d55026. Its [identity/evidence/restore guide](OBJECTS_V2_6_PRODUCTION_CHECKPOINT_2026_11_21.md)
preserves V2.5 Object Details and the accepted V2.4/V1.3.3/V3.2 foundations.
Unknown initial CI and screenshot triggers, plus manual production-acceptance
limits, are retained explicitly. This checkpoint adds no source behavior or
deployment and does not weaken the full mandatory release rule below.

The owner-accepted V1.3.3 baseline is pinned at
`estimation-labor-v1.3.3-2026-11-17` (`46aef079`). It preserves saved-estimate
reuse, ready-correlated screen navigation, old-wrapper compatibility and
Profile tab updates without a full-screen Opening. Save invalidation and
company/user/role isolation are part of the tested baseline. See the
[checkpoint and evidence](COMPANY_PROFILE_CHECKPOINT.md#v133-accepted-checkpoint-and-change-protection-proposal).
The initial startup fallback remains an open diagnostic, not an accepted
performance guarantee. On 17 November 2026 the owner approved implementing
persistent checks and an obligatory publication barrier. The implementation
and remote enforcement state are tracked in TODO and `tests/ui/README.md`.

On21November2026 the owner requested the full accepted Objects V2.4 presentation
checkpoint, runtimea8b08ba5 and tagobjects-v2.4-production-checkpoint-2026-11-21.
Its [identity, layout, evidence and restoration](OBJECTS_V2_4_PRODUCTION_CHECKPOINT_2026_11_21.md)
are additive to V1.3.3 behavior and V3.2 costing, which remain protected. Next
Object Details V2.5 presentation is approved below and preserves this checkpoint.

## Protected workflow behavior and release checks

Standing owner rule,21November2026: every deployment preserves previously
accepted product behavior and verified progress. New work does not supersede
earlier accepted requirements. Identify the affected checkpoints and regression
scenarios before editing; retain existing tests and verify both the new outcome
and protected behavior on the exact candidate. Only an explicit owner-approved
before/after decision can change a protected requirement. This applies to every
release without another reminder. Publication still requires the full mandatory
gate, actual remote enforcement and served Core/wrapper verification below.

- Saved File Review → Continue opens the original completed estimate and does
  not launch a new Parts Check or paid model call.
- Object presentation uses Detection's saved crop for the same company, run
  and object in both File Review and Object Detail. UI selection prefers an
  axonometric/perspective view, then an elevation, with top plans last.
  A missing crop keeps the existing placeholder; calculation pages are not a
  presentation fallback. Preserve the independent Naming magnifier selection
  and complete calculation evidence when changing preview behavior.
- Navigation is revealed only after its correlated ready result; departing
  and destination screens never appear together. Return routes, old open
  wrappers and cleared server session state remain covered.
- Profile main tabs update their content region while retaining the header.
  Prepared reads remain scoped to company/user/role; successful Save invalidates
  the affected resource. Failed writes keep an actionable error and allow retry.
- Expired sessions reach Login; changed access never exposes an owner-only
  control or another company's cached data.
- The permanent UI suite uses synthetic local data and production UI/handlers.
  Its full run is required for runtime, dependency, workflow, test or contract
  changes before publication. Local timings do not establish production speed.
- An intentional change to these behaviors requires a concrete before/after
  proposal, reason, affected routes/cache state, alternatives, verification and
  rollback, approved by the owner before implementation. Preserve tests and
  the remote gate when adding features; never silently weaken them to pass.

Use the exact-commit `UI release gate` and the verified publisher described in
[`tests/ui/README.md`](../tests/ui/README.md). The remote GitHub ruleset must
be active to enforce this independently of the agent. Check its real status;
do not infer activation from the presence of the workflow or ruleset template.

## Restored browser document and continuous shield,21November2026

The protected contract applies to every supported page route and Profile tab.
Admin-entry latency optimization remains deferred. A Core iframe document
navigation must not disable protection by replacing the wrapper referrer or
losing its original trace query. Retain only the verified parent origin/trace
as per-tab UI context, never authentication or pricing state. A new wrapper
trace takes precedence. Writes occur only on a validated existing host ACK,
once per changed context; no timer/request/worker is added.

Publication verification must require continuous full-screen coverage from
navigation acceptance until the matching Core-ready emission. Profile tabs
retain their accepted header and cover only content. Some covered frames and
zero simultaneous roots are insufficient: one unstyled outgoing screen is also
a failure. The full matrix includes two Core document navigations without the
trace query, lost server state, delayed Profile/Objects reads, header routes,
footer Back/Approve and sign-out. Preserve tenant/auth and saved-estimate tests.

## Objects V2.2 compatibility recovery, approved 21 November 2026

Unconfirmed/unsupported wrapper protocol must never silently permit a protected
page or Profile-tab navigation. Cancel the original event before its native
callback and retain a stable update/recovery screen. The owner may return to
the current page to save work. Update app is one explicit outer navigation,
retains browser sign-in, refuses an active upload/calculation or failed auth
persistence, and warns for explicit confirmation on editable pages. Never add
an independent draft writer or change input mechanics. No polling is added.
Compatible navigation retains the accepted cover and correlated ready path.

The exact shipped V1.2.23 wrapper and absent/unsupported ACK must be checked by
the same obligatory full release gate. Record compatibility, recovery and cover
start/end using the existing Core/wrapper channel; persist covered on click and
ready events. Historical wrappers cannot record new event types before update.
Each published UI release has a distinct public number and stamped build.

## Objects V2.3 presentation scope, approved 21 November 2026

Approved desktop mockup changes only stage copy/equal connectors, a local
owner-only metrics chevron and document controls beside fixed totals. Keep
title/table/object rows/ordinary inputs/totals/footer coordinates from V2.2.
Delivery/Installation fields become122px wide with focus only inside their
border; CSS selection scoping may correct native click-to-caret outside them.
Do not change any price normalization, calculation, persistence, confirmation,
generation, authentication or V2.2 compatibility/transition handler.
Project Summary remains its existing disabled export placeholder; Download
Proposal exposes the existing PDF URL, with no new exporter or request.
Metrics collapse stays local across existing progress markup updates, with no
timer, Python rerun, network request or persistent data write. Its one DOM
observer is restricted to the metrics subtree and disconnected on cleanup.

## Objects V2.4 approved desktop placement,21November2026

The owner approved the final V2.4 sketch and publication. Relative to V2.3,
retain the title and move the native menu to the upper right with its center
4px below the title center. Technical metrics are directly below with an8px
gap. Collapse retains the same arrow location. Raise all stages/table/summary/
footer actions together26px, retaining their internal x/width/height and gaps.
Stage2 is Set Prices. Stack document controls under Installation, each half
the Back to File Review width, with8px between them. Project Summary uses an
Excel icon, Download Proposal retains PDF and the existing URL behavior.
This approved placement supersedes only the V2.3 coordinate/copy assertions
it names. Service-field scope, original handlers, pricing, costing, approval,
generation, auth and V2.2 protection remain unchanged and mandatory. No new
timer, callback, observer, request or persistent write is required. Restore
runtime3a192b29 if this presentation experiment regresses protected behavior.

## Objects V2.6 metrics and feedback,21November2026

Objects V2.6 follow-up,21November2026: technical metrics use unbounded R1/R2/...
without object names. Keep one bounded line and its disclosure arrow fixed on
the right, retaining local collapse through refresh/navigation. Many entries
scroll only inside the metrics line. Revoke a historical timing receipt when
later row data is active; a running row has no ready-time metric. This only
changes telemetry observation, not worker/status/costing/persistence behavior.
Confirmed Set Prices uses existing Done green and loses it on price edits.
Render both checkmark strokes independent of font glyphs. Left-align the Excel/
PDF frames, grey while unavailable, green Excel/red PDF when available. Existing
export availability and body/header/input geometry remain unchanged. No new
runtime listener/observer/timer/request/rerun is required. The full gate now also
includes the existing estimation-cycle metrics suite with its resumed-work
regression; all nine browser suites and earlier checkpoints remain mandatory.

## Object Details V2.5 compact presentation,21November2026

The owner approved the compact sketch and deployment with240x164px preview.
Keep Object title/native menu coordinates and saved preview selection. Render
name/quantity on one row without AI Confidence. Materials, Labor and Overhead
start closed as white name+amount bands. Material rows stay flat; first Material
and Work column labels are empty. Preserve operation/Elements and Overhead group
nesting; an open nested summary uses the existing purple tint, closed ones white.
Self Cost (SC) shares the three final amounts' axis; VAT labels stay above their
amounts. Remove incomplete-calculation captions/Subtotal badges without changing
partial audit, missing numeric values, source data or any arithmetic.

This changes presentation and disclosure defaults only. Existing editors,
explicit Save/failed Save/retry/receipt/reopen/approval, Back and all header,
Profile/auth/tenant/protection paths remain mandatory. No new client runtime,
observer, timer, callback, request or writer. The full scenario matrix and
rollback are in the current Object Detail contract's V2.5 amendment. Earlier
open-by-default and partial-caption expectations are superseded only as named.

## V3.1 full object cost, approved 20 November 2026

The owner explicitly approved Materials + current Labor + restored Overhead in
both saved Self Cost and Objects. This supersedes the prior material-only SC
behavior and the former rule that saving Labor hours could not change SC.
Use the same accepted Labor hours/pay/one payroll load in UI and persistence.
Material cost comes from the existing purchase table, including its allocations
and policy rows. Overhead uses the preserved Profile monthly-hours allocation
and reserve formula. Divide the combined batch cost by object quantity once;
apply the configured VAT once to that per-item net amount. Delivery/Installation
remain separate project rows and saved manual sale prices stay authoritative.

Saved modern estimates refresh deterministically without AI. Store an idempotent
basis and complete component audit with previous totals for rollback. Profile
Overhead/Pricing saves invalidate only that company's visible cost caches. Saving
Labor overrides updates the full persisted sum and Objects; unknown work remains
an explicit subtotal. Preserve the existing failed-Save draft and retry behavior.
The existing parallel Labor fragment owns both cost blocks, with independent
placeholders so an overhead read never replaces Labor input nodes. One bounded
DOM observer reconciles a delayed Overhead with current edits; it disconnects on
resolution/error or editor teardown, without a timer or another Python rerun.

## Estimation9.44 explicit delta Save and consistent quantity display,23November2026

The owner requires Save to process only edited inputs and their dependent totals.
Front choices reprice the affected saved material baskets, preserving Parts,
geometry and Labor. Numeric material edits also reuse saved Labor unless object
quantity changes. A changed norm remains saved even when purchase rounding leaves
its cost unchanged. Whole-cycle validation/model calls are not part of Save.
The queued worker returns a projected receipt only after acknowledged persistence;
merge that receipt into the existing scoped card cache, preserving source preview
and immutable content. A committed modern material Save must not depend on a
second detail read. Existing ownership/validation, ordering and explicit Save stay.

Save stays on the card and turns green Saved after success, until another edit.
It never approves/navigates. Back still confirms unsaved edits, APPROVE alone
saves/approves then returns. Failure retains the draft and offers Retry save on
the existing button, without a second paragraph under the actions. Keep its
accessible status and diagnostic stage logging. Never show green success before
the writer acknowledges persistence.

Persisted Self Cost and Objects retain per-item prices. Object Detail sections and
bottom Self Cost all display the selected quantity's batch. Prefer the existing
exact batch audit, rather than multiply already rounded unit VAT. Apply configured
VAT once to the displayed batch net. This supersedes only the previous per-item
presentation at the card bottom, not costing formulas or Objects unit prices.

Privacy remains fixed. Retain the shared72px bottom reserve (46px fixed footer,
26px content gap). On short detail cards, keep Self Cost and actions together at
the viewport end. On long cards, the same gap applies at the scroll end. Remove
the invisible material bridge's layout gap without unmounting its iframe. Other
screen geometry, shared header/menu, source previews and all prior checks remain.

## Estimation9.45 configured unit price and terminal spacing,23November2026

Owner accepted9.44 Save and card totals, then explicitly corrected unit semantics:
commercial copy quantity must not divide the cost of the priced item. Supersede
V3.1's division and9.44's unit/batch distinction only for modern configured-item
cost. Sum the existing priced Materials + Labor + Overhead into the unit SC;
Objects quantity multiplies sale totals. Preserve the accepted card amounts,
material/Parts recipe and manual sale prices. Saved plan quantities retain the
physical pricing basis; merely changing commercial copies must not change Labor
or overwrite that basis during front/numeric material Save. Explicit physical
quantity edits retain their existing recalculation path. The basis fingerprint
changes once so saved modern estimates refresh without models or schema changes.

Front selector keys/matching/defaults are unchanged. Display labels are MDF Raw
and MDF Veneered. Keep LDSP, Plywood and explicit source alternatives.

Objects and completed File Review use the same26px closing gap before fixed
Privacy as Object Detail, at desktop/narrow widths and scroll end. Only terminal
actions' vertical position is superseded: keep all other frozen body coordinates,
footer x/width/height, field hit boundaries, confirmation, Save and navigation.
On short pages unused space goes above closing actions. Zero-height iframe and
screen-marker rows after actions remain mounted without consuming layout gaps.

## Estimation9.46 explicit Save navigation lock,23November2026

Owner reports explicit Save followed by Approve can leave the card. During a
non-preview Save, immediately mark footer navigation links aria-disabled, grey
and outside Tab order, and suppress both mouse/programmatic and keyboard click
activation. Do not queue approval from that rejected click. Restore only the
lock's attributes after a success, error, existing timeout or runtime teardown.
Keep Save on-card/green Saved/new edit, Back discard confirmation, direct Approve
with an unsaved draft and preview-time Approve queuing. This supersedes only the
previous explicit-Save→queued-Approve behavior. Use the existing Save lifecycle;
no new timer, polling, request or server callback. The new capture listener's
trigger is footer-link activation during persistence, scope is the current card,
constant2-link work per event, removed on editor teardown.

Shared loading typography is authored in ui/workflow_status.css, injected into
Core's existing base style and embedded byte-identically in wrapper HTML, with a
mandatory parity test. Updating app uses a span with that class, not mask default
system-ui16px. Recovery status uses the same class. The wrapper registers the
same existing Google font stylesheet once per document; browser resource cache
and native cancellation apply. No JS font waiter, loader timer or new API read.
New Estimate keeps the existing protected native callback/auth/uploader path;
the requested timing investigation does not authorise an alternate uploader.

## Preparation and Packing norms, owner approved 23 November 2026

Owner activates the existing fourth Labor stage. Before: Preparation and Packing
was an intentional read-only zero placeholder. After: it contains read-only Trial
Fit and Separation and Packing child rows with Hours, Labor Pay, Taxes/Social and
Total in the existing columns. Keep four direct stages, collapsed presentation,
footer layout and all existing editors/save/navigation behavior. No new notices.
S/M/L/XL use sorted inclusive limits600/600/400,1200/800/600,2000/1200/800mm and
beyond, with10/15/20/25 planned man-minutes; a complete sourced interface cycle
uses30. These are total worker effort, not elapsed crew time. Add no extra pace
or crew multiplier. Materials' Packaging allowance remains separate.

Known packing/checking contributes once to Labor, payroll, Overhead and full SC.
Editing old Sheet Processing/Block Assembly hours preserves both calculated new
leaves in the browser preview and saved totals. Existing override keys/meanings
and front-material Labor preservation remain. Commercial copies do not discount
the configured item's SC. Missing source evidence remains unknown/partial, not
zero work; legacy reports are not silently claimed to contain a connection graph.
Source views and reverse pair references merge evidence without repeating work.
No new model request or Detection/prompt change is part of this feature.
Verify boundaries/rotation, man-minutes, source/material invariance, failure
isolation, saved totals/reopen, old edits and the existing complete UI gate.
Rollback reference: accepted9.48/runtime862e28f0 and its full immutable checkpoint.

## Estimation9.48 Prices and four Labor stages,23November2026

Owner explicitly approved steps1/2 of the four-stage plan and requires every
Labor stage to remain visible, with0 for not-yet-implemented work. Materials,
Labor and Overhead retain their accepted collapsed root presentation. Labor
contains Part Production (existing Sheet Processing), Part Coating, Assembly
(Block Assembly + Additional Assembly), and Preparation and Packing. Coating,
Additional Assembly and Preparation/Packing show read-only0 hours/pay/taxes/total.
The existing sheet/assembly hours keep their persistence keys and meanings;
new parent rows aggregate them without extra writers or double counting. Existing
unavailable work stays unknown. These explicit new empty stages alone supersede
previous no-zero expectations. No new coating/packing/assembly norms or notices.
The configured-item, Overhead, manual sale, payroll/VAT and source contracts stay.
An explicitly in-house CNC route skips the alternate panel-saw calculation;
actual CNC/operator/edge work and other companies' existing routes stay intact.

Price Lists starts with collapsed native groups and prepares row controls only
for open groups, keeping an active editor mounted to preserve its draft. The
selected group is prepared before other open groups while visual header order
stays fixed. Existing four independent background projections no longer share a
first-render completion barrier. Pending catalog headers are usable before the
source library/review/supplier reads finish. Native count-label changes preserve
user open/closed intent independently, since label participates in widget identity.
Source library retains explicit user-action open-once behavior. Identity scopes,
upload/row-save/delete/review, failed-save retry, current drafts and other Profile
paths remain protected. Reuse existing bounded reads and existing completion
fragment. The only new callback is the user's native group toggle, once per
interaction, scoped to that Prices fragment; it records disclosure/priority only.
No new polling, backend reader pool or user-facing notification. Live responsiveness
and owner acceptance remain separate from the controlled browser evidence.

## Estimation9.47 Profile Save, Contacts and closed-cost spacing,23November2026

Owner explicitly replaces Profile's green bottom success blocks with an
acknowledged Saved state on the existing action. Retain actual persistence,
validation, failure/retry, actor isolation and reopen. Native and HTML Save
buttons show Saving only while their existing request runs, Saved only after a
fresh company/action-scoped server receipt, then the original label after2s or
new input. No additional write/price cycle or Profile rerun for presentation.
One save-scoped receipt observer and30s UI timeout are cancelled on result,
relevant tab/navigation/disposal; the2s Saved timer is likewise cancellable.
Do not mark edits made after submission as saved. Deletes retain the confirmed
row removal and an invisible receipt, without another success notice.

A stored Company Logo must not cause Contacts to draw outside its fragment.
Keep the native Change Logo picker/validation/storage behavior, fragment-owned
hidden guard, genuine ready result and regional Profile cover. Stored/missing
logo, warm/cold/Reload, mouse/keyboard, later tab navigation and error recovery
are required. An anonymous Login or a fixture without a stored logo does not
prove this owner-reported Contacts path works.

Only when Materials, Labor and Overhead are all collapsed, Self Cost follows
Overhead naturally instead of being pushed to the viewport bottom. This
supersedes the collapsed-state pinned terminal placement, not expanded geometry,
inputs or fixed Privacy. The prior26px clearance remains in expanded states;
collapsed content keeps clear of Privacy and may leave free viewport below it.
All eight collapse combinations must preserve amounts, actions and focus.

Overhead uses reported monthly hours of active Production employees from Labor
Costs. Keep company scoping and existing reserve/VAT formulas. Missing reported
hours may use the existing configured capacity only as an audited fallback;
failed reads are not fallback. Employee mutations invalidate company overhead
views, not saved Labor/Parts/material selection. The same capacity must reach
persisted cost and the visible Object Detail allocator.

## V2.9 one deployment event and retained login, approved 19 November 2026

Owner explicitly requires a page refresh with the user still signed in and
rejects periodic build polling. V2.9 replaces the V2.8 poll with one build
announcement from Core over the existing browser connection, after a real
ready receipt. No new timer, HTTP version request, worker or auth poll.

| State / action | Required result |
|---|---|
| Core announces a newer build | One outer reload at safe Upload/Login |
| Same or older Core during rollout | No reload, no repeated build announcement |
| Active file picker/transfer, calculation or unsaved edit | Finish current action, reload at safe Upload |
| Expired access token with valid refresh session | Rotate explicitly, synchronously persist newest session before reload, restore signed-in state in new server session |
| Older queued browser write | Ignore it, keep the latest rotated session |
| Browser cannot persist the session | Keep current page, postpone reload, offer client-side Retry; no extra Python rerun |
| Fast cookie rejected, this tab has a newer valid session | One browser bootstrap retry before Login; preserve workflow state and validate recovered tokens normally |
| Provider rejects available cookie and tab sessions | Existing Login recovery, no access bypass or retry loop |

The server SDK must not refresh tokens in its own background timer. Streamlit
owns refresh and passes its latest session write to the same ready component
which announces a deployment; browser writes complete before the announcement.
A rejected cookie triggers at most one native rerun/browser read on bootstrap,
without polling or clearing the tab session first. This does not add work to
normal valid-cookie startup or user clicks. One shared JS writer orders store/clear/cookie commands. Read replies remain
idempotent and write commands do not schedule a Python callback. Build IDs carry
a UTC `-bYYYYMMDDhhmmss-` stamp so an older Core cannot reload a newer wrapper.

## V2.8 forced deploy refresh, approved 19 November 2026

Owner requested simple forced refresh after deployment and explicitly assigned
V2.8. The refresh mechanism must not check auth, log out, clear tokens/cookies or
end a session. Existing server auth remains separate. Retain the earlier
requirement to avoid interrupting current calculations and unsaved edits.

| State | Action / result |
|---|---|
| Current published build | Continue immediately, no upload/version/auth gate |
| New public version, empty Upload or Login | One full outer reload, browser auth storage/cookies untouched |
| File picker, transfer, Processing, Calculation or unsaved edits | Keep current work, reload at the next empty Upload boundary |
| Already-open old wrapper, including Login | Existing correlated reload migrates it once |
| Version file unavailable | Keep working, retry later without blocking controls |
| Update still unavailable after reload or guard storage fails | One actionable Reload page state, no automatic loop |

The wrapper reads static /version.json once on start, every 30 seconds while
visible/online, and on visibility/online recovery. One request at a time;
pagehide aborts it and cancels its timer. This performs no Core/auth/model call
or Python rerun. Matching Core/wrapper builds are no longer an upload gate.
The old provider AuthApiError from the V2.7 live test is not claimed fixed.

## V2.7 safe version refresh, approved 19 November 2026

Owner approved automatic refresh on build mismatch, retaining login and the
current calculation, with Detection unchanged. Previously mismatch only logged
and waited for manual refresh. Use the existing ready/version handshake and
correlated reload command. Preserve tab auth storage and sealed resume cookies.

| Input / state | Action and visible result | Verification |
|---|---|---|
| Empty Upload, matching builds | Upload works immediately after ready acknowledgement | No reload or extra Python rerun |
| Empty Upload, mismatched or supported old wrapper | Show Updating app, one full reload, retain login, confirm matching builds before upload | Current wrapper and migrated old wrapper |
| File picker open or file transferring | Keep current action, defer refresh | Selection/drop survives mismatch |
| Processing, estimation, saved result or unsaved edit | Keep current screen and state, defer until empty Upload | No reload, value and active job retained |
| Repeated mismatch after reload, unavailable guard storage or missing acknowledgement | Block new Upload, show one actionable Reload page state | No automatic reload loop |
| Auth expired | Existing Login recovery, no fabricated authenticated state | Existing auth and resume checks |

No polling, background model call or refresh timer runs during calculations.
A single five-second acknowledgement deadline exists only on empty Upload;
reply, departure or controller disposal cancels it. A manual Reload page retry
is allowed after an unsuccessful automatic update. Browser and production
verification remain distinct from synthetic fixture results.

## Mandatory scenario-first workflow

Do not begin an interface layout or interaction revision from the happy path
alone. Before implementation, create one compact table with every reachable
input combination, action, local validation result, asynchronous result,
message, field state, loading state, and destination. Review that table with
the product owner and treat the accepted version as the screen contract.

Implementation and acceptance use the same contract:

1. Map all controls and state transitions, including empty and partial forms.
2. Define exact field borders, message copy, dismissal rules, button state, and
   navigation for every row.
3. Add regression coverage for deterministic rows.
4. Deploy the candidate and execute the full matrix in the real production
   session, including mobile or mail-client checks when those surfaces matter.
5. Record exceptions and unresolved rows. Do not call the screen complete from
   a successful happy path or from screenshots of only one state.

This scenario-first tester mode is mandatory for Sign in, registration,
invitations, password recovery, forms, uploads, and every future interactive
screen.

## Product-wide interaction contract

- Auth screens share one geometry template. The logo, heading slot, form start,
  panel width, and vertical gaps stay fixed while only the heading and panel
  contents change between Sign in, registration, verification, password, and
  Terms states.

- Every user action has four possible states: press, progress, completion, and
  error. Implement every state that the action can reach.
- A control must acknowledge pointer-down immediately. Hover alone is not
  feedback. Buttons need distinct default, hover, active, focus-visible,
  disabled, and loading states.
- Immediate press feedback must not wait for a server response or a Streamlit
  rerun. Use a small color, shadow, or scale response that does not move the
  surrounding layout.
- Any action expected to take longer than 500 ms must show a specific loading
  state immediately. Disable duplicate submission while preserving the user's
  entered data and current context.
- Loading labels must describe the current phase truthfully, for example
  `Checking file`, `Detecting objects`, or `Saving profile`. Do not say
  `Creating` while the system is still validating.
- Completion must be visible. Show the resulting state, navigate to the result,
  or display a concise success acknowledgement. Never leave a finished action
  looking as if it is still running.
- Failure must restore control immediately, preserve recoverable input, identify
  what failed, and state what the user can do next. Never leave a spinner or a
  disabled control behind after an error.
- Multi-stage progress must reflect measured work rather than equal fictional
  steps. Do not race to a high percentage and then stall near completion.
- Async work must be idempotent from the user's perspective. A double click,
  refresh, or retry must not create duplicate companies, RFQs, estimates, or
  writes.
- When a mutation has a safe local outcome, show that outcome immediately and
  persist it in the background. Keep enough local state to restore the prior
  item with a clear error if persistence fails. Do not make the user wait for a
  database round trip merely to see an already determined interface change.

## User-journey markers

Every important user-facing asynchronous journey must have a small, correlated
set of diagnostic markers. This is part of the interaction design, not
after-the-fact debugging. Mark the meaningful boundaries: action accepted,
truthful pending state shown, material dependency wait when one exists, write
accepted or rejected, and the resulting state rendered. Use the same action
correlation ID through those boundaries so latency can be assigned to a click,
server work, data refresh, or render.

Do not instrument every component render, hover, or trivial local state change.
Add markers where their absence would make a user-visible delay, duplicate
action, missing result, or recovery failure impossible to explain. Markers must
be asynchronous, private, and invisible to the user. They never justify an
extra rerun, poll, loading state, or layout shift.

## Form interaction states

- Numeric and percentage inputs use the shared end-caret contract. On pointer
  entry or keyboard focus, the caret is placed at the right edge of an existing
  value. A pointer must not place it inside or before that value. This prevents
  accidental leading-zero input such as `01` when the intended edit is `10`.
  Apply the contract through the shared input guard, never with a screen-local
  event handler. Formatting may update a derived companion field, but it must
  not move the caret or overwrite the value currently being edited.
- Default fields use the shared neutral border.
- Focus is always a quiet Costerly-purple border and ring. Focus is never an
  error and must never be red.
- Do not show framework keyboard hints such as `Press Enter to submit form`.
- Empty required fields become invalid only after the user submits the form.
- A non-empty value that can be validated locally may become invalid on blur.
  Email is the canonical example.
- After validation, an invalid state remains only while its condition is still
  unmet and clears immediately when the current value becomes valid.
- One submit validates every field. Do not stop at the first invalid value.
- Hidden validation markers must not reserve layout space or shift later fields.
- Use a red border as the primary field-level validation signal. Do not repeat
  obvious instructions such as `Enter an email address` beneath a clearly
  labelled Email field.
- Show text only when it adds recovery information the field itself cannot
  communicate, for example an existing account or a temporary service failure.
- Validation must never erase input values or move the user away from the form.
- Do not enter a loading state when local validation fails. Keep the user on the
  editable form and mark every invalid field instead.
- Use a truthful progress label. A server-side uniqueness check is `Checking`,
  not `Creating`; advance to creation only after that check succeeds. Any server
  validation error must immediately restore the editable form.

## Hierarchy and content

- Show the common path first. Put optional, advanced, or international settings
  one level deeper without hiding the primary task.
- Every element must earn its space. Remove redundant subtitles, repeated
  section names, framework instructions, and explanatory text that merely
  restates a clear label.
- Use direct, specific labels that describe the content or action. Prefer
  `Price Lists`, `Project Contact`, and `Save Details` over vague labels such as
  `Home`, `Settings`, or `Submit`.
- Group controls by the thing they affect. Proximity must communicate the same
  relationship as the data model.
- Every screen must make four things clear: where the user is, what is available,
  what the primary next action is, and how to leave or go back.
- Simplicity is not the same as removing context. Add short recovery or status
  text when it reduces uncertainty, but do not decorate obvious interactions.

## Motion and transitions

- Motion must explain state, location, causality, or progress. Do not animate an
  element only to make the interface look active.
- Frequently repeated actions should have little or no animation. Reserve more
  noticeable motion for occasional transitions where it improves orientation.
- Entering elements start promptly and settle with ease-out. Movement already
  on screen may use ease-in-out. Continuous progress indicators use linear
  motion. Avoid ease-in for interaction feedback because it delays the visible
  response.
- Prefer short transitions on `transform` and `opacity`. Do not animate layout
  properties when the same result can be achieved without reflow.
- User-controlled motion must remain interruptible and continue from its current
  visible position. Never force the user to wait for an animation to finish.
- Respect `prefers-reduced-motion`. Replace large movement, bounce, and parallax
  with a short fade or an immediate state change while preserving feedback.

## Accessibility and input methods

- Do not rely on color alone for important status. Pair it with shape, icon,
  label, or recovery text when the meaning would otherwise be ambiguous.
- Keyboard focus must remain visible and follow the same logical order as the
  page. Pointer-only and hover-only actions are not acceptable.
- Touch targets must be comfortably selectable on mobile. Do not shrink primary
  actions to fit a desktop layout.
- Text resizing must not clip labels, overlap controls, or hide actions. Use
  responsive sizing and spacing rather than assuming one fixed viewport.
- Loading and validation changes must be exposed as status to assistive
  technology without stealing focus unnecessarily.

## Visual consistency

- Use the shared light Costerly AI palette regardless of the browser or operating
  system theme until a complete dark theme is designed.
- Reuse shared input, button, spacing, focus, and error tokens before adding
  screen-specific CSS.
- Every checked checkbox uses the shared interaction blue `#4F8FCB`. The rule is
  global, including Auth, Terms, Company Profile and Machinery; red is reserved
  for an actual validation error or explicit negative status.
- Keep Streamlit sliders on their native geometry. Do not recolor a slider by
  replacing or filtering its generated track: React Aria and BaseWeb use
  different nested elements, and a color-only override can turn the thin track
  into a filled block. Until a theme-level color change is verified against both
  DOM variants, retain the native slider color rather than adding screen-specific
  CSS or a mutation observer.
- Company Profile content cards use the accepted 18 px outer radius and the
  same first-card gap below the tab rail. A tab must not introduce its own
  smaller outer radius or extra top offset.
- Every value, label, action, and empty-state message inside a table or
  table-like row is vertically centered against the row's actual content box.
  Center through the row and wrapper layout (`align-items: center` with equal
  top and bottom geometry), never with `top`, `translateY`, negative margins,
  or an eyeballed pixel offset. When Streamlit inserts wrapper elements, those
  wrappers must occupy the row height and must not retain framework margins
  that change the centered margin-box.
- Hover and active states should communicate interactivity without changing
  layout or moving surrounding content.
- Desktop and mobile versions use the same hierarchy, wording, and validation
  behavior; only dimensions and spacing may adapt.

## Review checklist

Before accepting a screen, verify:

1. The approved scenario matrix exists and every row has a test or production
   acceptance result.
2. Every clickable control responds on press, not only on hover.
3. Every network or agent action shows immediate and truthful progress.
4. Success, failure, retry, disabled, empty, and loading states all recover
   cleanly without layout jumps or lost data.
5. The primary action and current location are obvious without explanatory copy.
6. The screen works with keyboard, touch, narrow width, and reduced motion.
7. Repeated clicks and retries cannot duplicate persistent work.

## Design references

- Apple interface and motion principles distilled for the web:
  https://github.com/emilkowalski/skills/tree/main/skills/apple-design
- Emil Kowalski's broader design-engineering review principles:
  https://github.com/emilkowalski/skills/tree/main/skills/emil-design-eng

These references inform the rules above. They are not copied wholesale: Costerly AI
uses only the parts that improve clarity, responsiveness, accessibility, and
workflow reliability for its own product.

V2.9 legacy migration: retain cloudflare/version.json with the current build
for already-open V2.8 wrappers. Their final legacy check loads V2.9, whose
wrapper does not read the file or schedule polling. Removing the file before
those tabs migrate prevents their one-time update. New Core connections still
use the build event; no new timer, request, callback or auth check is added.

## Owner-approved historical rollback, 20 November 2026

The owner explicitly confirmed full production rollback to Labor V1.2.23,
`582343a125ab0ee32fefcc6b85aeeb3398dc649b`, to test fresh Ada before restoring
later releases incrementally. This deliberately returns navigation, auth,
Detection grouping and Materials-owned Self Cost to that version. Later
Overhead/full-SC/auto-refresh behavior is not retained. Existing database records
and provider configuration remain intact. Historical successful and failed Ada
runs both occurred on this source, so rollback is not a proven recognition fix.

The alternative, a selective speculative repair, was rejected by the owner.
All later contract and test definitions remain retained. The no-bypass remote
rule and exact-commit publisher remain required. The approved-rollback manifest
activates an exact-source and dependency-identity check plus original historical
regressions and publisher tests. It rejects every other runtime source. This is
an explicit historical baseline exception, not acceptance of V1.3.3-V3.1 behavior.
Remove the manifest before restoring later changes and use the full modern suite.
Fresh authenticated production acceptance belongs to the owner after deployment.
Rollback of this deployment is the prior V3.1 `f051b8cc`; stored totals are not
rewritten as part of this code deployment.

### Superseding V1.2.21 rollback approval

Later on 20 November the owner explicitly approved rollback to Labor V1.2.21,
`c84ece4c959c75be41271b2221807e3df6579297`, replacing V1.2.23 as the historical
control. The exact-source gate is repinned to this commit; newer test definitions
and the mandatory remote publication rule remain retained. V1.2.21 predates
Block Assembly and the V1.2.23 expired-progress-overlay recovery, so both return
to their original historical behavior. Sheet Processing/CNC and the per-piece
finished-mirror calculation remain. No database totals or provider configuration
are rewritten. Modern behavior restoration still requires removing the legacy
manifest and running the full modern suite. Fresh Ada and authenticated UI
acceptance remain pending, and failed fresh controls are not erased. Immediate
code rollback reference is the published V1.2.23 `447b4892`.

Owner-requested full9.46 checkpoint23November2026 preserves this contract and
all earlier accepted behavior. See[checkpoint](ESTIMATION_V9_46_PRODUCTION_CHECKPOINT_2026_11_23.md). No new runtime behavior
is introduced by preservation.

Owner accepted the achieved Estimation9.47 interface23November2026 and requested
full preservation. Existing9.47 amendments and all earlier protected scenarios
remain. This records acceptance, changes no test or threshold.
[Full checkpoint and restoration](ESTIMATION_V9_47_PRODUCTION_CHECKPOINT_2026_11_23.md).

## Labor2.11 disclosure and hours, owner approved23November2026

Expanded aggregate stages (Part Production, Assembly, Preparation and Packing)
keep only their name/toggle in their own summary. Hide hours/pay/taxes/total with
CSS visibility, preserving the DOM and calculation source. Collapsing restores
all four values. Leaf rows keep their editors/metrics while their evidence is
open. Root Labor shows total hours beside its amount, including when collapsed.
Exact total hours remain the existing once-only source for Overhead allocation;
round the display only. The screenshot's28.3h is correct, nested preparation is
already included. No allocation or payroll change.

Nested numeric axes follow the existing Materials Hours/Total reference and
uniformly spaced Labor Pay/Taxes axes. Center actual text in full-height cells;
indent only the nested title, never shrink the nested numeric grid. Reuse the
existing coalesced render/resize alignment guard on native Labor toggle events,
with listener cleanup. No new observer, polling, request, write or app rerun.
Verify desktop/mobile/old wrapper/restored document, disclosure restore, leaf
editing, Save failure/retry/reopen and shared exact hours with Overhead.
Rollback is the published2.10 runtime20e34aa1; accepted9.48 stays preserved.

Display boundary check: Python Overhead previously rounded100.25h to100.2h,
while Labor/JS showed100.3h. Use shared half-up one-decimal display for Labor
and Overhead, including saved/reopened rows; allocation retains exact100.25h
and all costs are unchanged. Tests cover100.25,140.75,1.15 and28.3h.

## Labor 2.12, owner approved24November2026

Preserve the full2.11 checkpoint before implementation. All operational paid
hours become editable through the existing draft/Save pipeline, including zero
coating/additional assembly, checking/packing and CNC operator/file preparation/
edge banding. Retain the old saved keys and source norms. The owner confirmed only terminal work rows are editable. Any row with
children and the root total remain computed. All terminal fields are editable, including unknown hours: preserve the unknown
state until explicit manual input. Never infer zero from an empty field. Tax header
states Taxes & Social +25%, one existing charge. Draft and saved/reopened totals
must feed the same Labor/Overhead/Self Cost/Objects pipeline, once per operation.

All Labor work summaries have equal row heights and contiguous row boundaries;
aggregate-body padding must not introduce extra gaps. Keep full-height centered
cells and title-only indentation. For explicit CNC route remove duplicate
in-house/subcontractor/material comparison and supplier-rate panels. Sheet
Processing retains Elements, operational labor-hour rows and CNC time breakdown.
Keep other machinery-route behavior. Overhead renders its column headings once,
before all groups, using one shared aligned grid. Native disclosures, current
editors, Save/retry/reopen, Front panels, scroll/footer/auth/navigation stay.
No new poll, callback, writer, model request or duplicated material charge.

Unknown-hour completion reuses the existing Save receipt and shared Overhead
renderer once when a previously pending host becomes ready. Ready Overhead
hosts keep their nodes/disclosure state, all hour editors remain mounted, and
response scope must match object/run/estimate. Clearing an unsaved unknown-hour
edit restores unknown, not0. No extra read/request/writer/callback is added.
Real partial receipt testing exposed section columns being lost in the detail
cache on Save/reopen. Merge new rows into the existing section metadata instead
of replacing its schema. Preserve geometry, source facts and all previous state.

## Labor 2.13 and Project presentation, owner approved24November2026

Keep Part Production (singular attributive Part), Sheet Processing, CNC and the
separate Operator/File Preparation/Edge Banding work. CNC, Elements and block
lists share compact42px disclosures, fonts, chevrons and open backgrounds.
Presentation-only disclosures are not paid-work nodes or hour inputs. Preserve
part tables, PDF links, native keyboard toggles, hour editors and financial tree.
The project-wide summary is Project, with Continue to Project/Back to Project;
internal objects routes, saved identity and the separate Projects page stay.
Align its logo's visible artwork to the content axis without moving other axes.

Approved offline design: the purple mark before Something went wrong., with
Are you connected to the internet? beneath, existing background/24px loading
font and fixed Privacy. Reuse the existing wrapper cover and browser offline/
online events; keep assets embedded for offline availability. No new polling,
observer, writer, auth request/logout/storage clear or reconnect path. Offline
blocks interactions with the disconnected iframe, does not unload it. Online
releases only this view and reuses existing reconnect guards, including busy
work. This does not replace Streamlit handling of a server-only disconnect while
the browser remains online. Earlier recovery, active-work and session guarantees
remain required. Chrome's native failed-document page itself is not restyled.

## Labor2.14 nested rollups, owner approved24November2026

CNC sits before reference Elements and is now a read-only rollup of Operator,
File Preparation and Edge Banding, not a new terminal operation or stored key.
Unlike the presentation-only2.13 CNC disclosure, its closed summary shows the
same existing Sheet Processing budget. Nested closed work aggregates show sums,
open ones hide their own metrics while showing child rollups/leaf editors. Keep
the original once-only payroll rounding and full financial source. Elements and
reference details follow work in Sheet Processing (including non-CNC/pending
routes); no duplicate reference list is added to unrelated groups.

Use Overhead's purple filled triangle, mono uppercase title and spacing for
nested Labor/CNC/Elements/block details. Keep42px rows, full-height text centers,
shared numeric axes and title-only nesting. Native keyboard disclosures remain.
Owner confirmed Trial Installation, label only, and All Projects for list-entry
buttons. Project remains the current summary; route IDs, storage and page
identities remain. Do not rename source keys or invalidate saved estimates.

Closed Overhead group summaries show summed monthly currency, their shared
current labor-hours/capacity allocation and allocated Cost. Reserve percentages
are not monthly currency: show — and Formula in those first two summary cells.
Expanded groups hide all summary metrics, preserving grid and leaf rows. Manual
hour preview/save/reopen must keep group allocation and Cost current, once.
No new writer, callback, observer, polling, model call or reconnect behavior.
Retain2.13 approved offline design and all financial/auth/persistence contracts.

## Labor2.16 Part Coating, owner approved25November2026

Owner authorized25-26November2026: Part Coating details use the same table
headers/rows/cells and keyed receipt reconciliation as Materials, not a separate
bullet list/client renderer. Show Finish, Coated area, Time norm, Hourly rate,
with40/45/35min/m² (no person). Preserve the common Labor disclosure/terminal
hour input, table and retained row nodes across receipt updates, Save/reopen and
APPROVE. Material formula rows, including Coating consumables, share51px minimum
cell height. Coating calculations, rates, scope and all earlier workflow remain
unchanged; this presentation requirement does not approve a new approval route.

Extend the existing Front panels selector to six choices, keeping the four old
stored IDs and adding only veneer-MDF oil and plywood oil. Labels specify the
finish. No second selector or extra gloss control. Same-substrate lacquer/oil
changes preserve the exact board offer and geometry. Only dependent coating
refreshes, all other Labor and manual overrides stay accepted/saved.

Coated physical area includes both faces and edges, without laminate layers or
stock waste. LKM22ILS/m² lacquer/oil,16 MDF enamel; separate coating consumables
10ILS/m². No additional old Paint consumables percent on new LKM. Existing
general consumables/packaging policies retain their bases. Initial norms are
40/45/35 person-min/m², spray batch30m² with4h setup inside the full norm,
oil strictly linear. Company in-house booth gates automatic spray hours.
Coating alone uses100ILS/h plus25% once, other Labor stays50. Thus the accepted
mixed105.8h manual control becomes6687.50 Labor/1058 Overhead/8745.50 SC.
Hour editors, zero/unknown behavior, disclosures, explicit Save, errors/retry,
navigation, commercial quantity invariance and saved reopen remain protected.

Use the existing full-cost audit for recipe/area/materials/hours/route evidence.
No schema migration, paid Parts call, worker, timer or new persistence path.
Synthetic browser scenarios cover1280/390 and the full old matrix. Longer
business tables use the shared existing page-bottom geometry probe, retaining
the exact26px fixed-Privacy gap and2px tolerance. Native scrollIntoView alone
does not establish that the viewport reached the actual bottom.

## Labor2.18, owner approved26November2026

Project title uses the saved File Review Project name verbatim, including A3;
empty/Unknown shows Project alone. This does not change recognition or identity.
Before Delivery, Production time uses the existing service-field editor and
authenticated queued writer. Accept only positive whole working days after
payment until ready for delivery. Delivery and installation are excluded. New
terms are blank, no illustrative15-day default. Show Working days after payment
and Delivery & installation excluded without final periods. Persist through
Review/Back/reopen and include the saved term in the approved snapshot/PDF.
Days never enter sale-price calculations. Failed override reads must not become
an apparently absent saved price or term.

Project Price and VAT figures use the same mono family/30px size as Project
Total, regular400 and black; Total stays purple/bold700. Existing financial
values, navigation and geometry remain except the added row and figure size.

Coating reference details supersede the2.17 table presentation: reuse the compact
Trial Installation/Packing list, with finish, coated m², min/m², hourly rate and
included batch preparation. Keep calculations, material scope and shared receipt
reconciliation unchanged. Genuine terminal work without details has no disclosure
or empty expanded space. Keep hour editors and all four top stages. Hide Edge
Banding only when the source has no such operation and no nonzero override;
an applicable operation manually set to0 stays visible and editable.

Management & Administration is the first readonly Overhead category in Profile
and objects. Sum active Management/Office total_monthly_cost, already employer
loaded, allocate using the same exact Labor hours / Production monthly capacity.
Do not apply employer load again or VAT to the salary row. Employee mutations
invalidate the existing company metrics context. No duplicate editable payroll
record, new writer, polling, or approval controller is introduced.


## Labor2.19, owner approved26November2026

Before changes preserve the full2.18 checkpoint, exact runtime8b1cc958 and
separate records0578c583,852 source files and independent byte-identical restore.
The owner's generally working calculation acceptance does not accept its
reported Project input/spacing/title issues. APPROVE latency is deferred.

Project numeric fields follow the same shared end-caret contract as Object
Detail/Profile, on pointer entry and keyboard focus. Keep the active field's
value/caret during older queued-write reconciliation. Preserve existing serial
writes, acknowledgement, failure/retry and navigation protection. Production
working days are positive integers only; reject fractional paste, retain centered
active/empty input and existing service-field border/hit area. No new writer,
observer, timer, callback, request or rerun. Helper/material descriptions display
lowercase. Reserve the same two-line helper region and133px minimum row interval,
including rows without description, preserving existing field axes/typography.
Long content can grow without clipping. Long Project names start below Project,
with the mark on the Project line; do not change saved names or identity.

Assembly contains Block Assembly, Hardware Fitting and Additional Assembly.
Hardware Fitting is installation and adjustment of fittings, separated from
already-counted Block Assembly operations. Existing source/norms and once-only
combined payroll rounding remain. Existing assembly overrides stay legacy whole
budgets, allocated over their old structural/hardware proportions. New terminal
keys block-assembly/hardware-fitting override only their share through the same
hours writer. CNC boring remains Sheet Processing; no double hardware charge.

Additional Assembly uses saved finished-unit evidence, provisional60min per glass
box, mirror and physical LED zone, including source repeats once. Do not count
glass walls, metres or purchase packages as separate assemblies. Owner confirmed
four physical LED zones in Ada, not two Kelvin/material types: Corner8+2+4=14h,
Console1+1=2h. Keep manual0, shared compact details, exact Labor/Overhead/SC/Project
integration and all former unknown/saved/reopen/failure behavior. No paid call,
Detection change, new material demand or schema migration is authorized here.

## Labor2.20, owner approved26November2026

Keep an acknowledged File Review Project name in the same run's prepared
Continue metadata/Project projection. Do not rebuild costs or poll for a title.
UI preview priority recognizes compound isometric/axonometric/perspective
classification traits, preserving raw Detection, Naming order and ownership.
Pricing Cost adds optional whole Advance payment0..100 below Default sale
markup. Blank persists asNULL and omits the proposal clause; explicit0 remains
distinct. Final approval freezes the current setting; price/VAT/total unchanged.
Profile primary actions reuse Contacts/Labor's60px/19px/700 presentation and
existing Saving/acknowledged green Saved/failure/reset behavior, with no new
notice or writer. At CSS viewport heights1500px and above, Project/Object
summary/actions follow content naturally, eliminating zoom25/33% stretch.
Normal viewport/footer axes and fixed Privacy remain protected. Required
scenarios and reasons are in LABOR_V2_20_PROJECT_PROFILE_2026_11_26.md.

## Labor2.21 calculation completion during navigation,26November2026

A worker finishing while Profile or File Review is mounted must reveal its
persisted terminal result on return to Project. Discard a matching prepared
progress snapshot when consuming that worker's terminal result, before it can
replace the dirty result cache. Preserve the same worker, input and estimate;
return navigation must not start a new paid calculation. Keep existing live
fragment refresh and tenant-scoped prepared navigation.

File Review retains240-character validation but hides character-count hints,
matching existing Profile input presentation. Profile Save cards retain their
normal bottom padding; invisible guard/fragment bridge slots must add no blank
footer. Actual errors, acknowledgement-driven Saving/Saved and fixed Privacy
remain visible and functional.

## Labor V3 PDF, owner approved 27 November 2026

Set Prices confirms saved commercial data once; Generate consumes that confirmed
basis without a second full estimate read/recalculation. Relevant edits invalidate
confirmation. Existing ownership/finalization checks remain. The first Generate
creates, durably saves and initiates a download; the existing Download Proposal
then stays available with its red PDF icon for repeat downloads without rebuilding.
Use one immediate disabled GENERATING… button state and restore retry on failure.
No new notice, polling, background worker or layout shift is authorized.
The proposal is native-text/vector white A4, matching the approved Ada layout,
with whole-ILS values, frozen Profile/project data, complete uploaded company logo,
conditional Client/Partner, no social links and intact Costerly footer lockup.
Existing old PDFs, navigation, price inputs, calculations and all prior gates remain.

Labor V3 owner footer correction: English/Hebrew terms share the physical right
edge. Attribution stacks estimated with above a smaller intact brand. Footer
company legal names are omitted; registration/bank details begin near the divider.

Labor V3.1 owner clarification: Project name/Partner/Client are optional. Omit
missing metadata in PDF/filenames; create no Unknown Partner or Untitled project
placeholder. Preserve IDs, immutable versions, company ownership and object
approval. Long Project text must clear the menu and technical dashboard with
admin metrics visible or collapsed, without changing the accepted short-title
axes or mobile flow. Reuse the existing alignment callback, no new observers.

## Labor V3.2, owner approved27November2026

Owner accepted the V3.1 Generate/download result, then requested V3.2:
- Proposal: English-only Commercial Proposal heading. Production time is one
  right-aligned block: English production-days/advance-start line and exclusion
  of delivery/installation from that period, then both Hebrew translations.
  No lead, separate Payment terms or inferred balance-on-completion statement.
  Saved NULL/zero are distinct, no illustrative days/percentage default.
- Reuse existing Profile logo normalization. Proposal artwork targets71pt visible
  height/48pt top/51pt left, width follows aspect. Contacts adapt if needed.
  Extremely wide art is bounded by A4 width rather than cropped or distorted.
- After durable Generate success and first download, the same footer action is
  an enabled green Download Proposal to the saved URL; Set Prices is ordinary.
  Keep the red secondary download, failed-generation retry, immediate pending,
  confirmed data/price invalidation, old PDFs and no regeneration on download.
- Closing actions follow content on File Review, Project and Object at every
  scale. This explicitly supersedes prior short-page viewport-fill/bottom pinning
  and the1500px-only exception. Keep fixed Privacy,72px bottom reserve and26px
  clearance at the scroll end. Short content may leave unused viewport below
  the completed content/actions, never a stretched gap before actions. Retain
  all other frozen axes/dimensions and mounted zero-layout runtime bridges.

No new callback, timer, observer, polling, request, schema or notification is
introduced. Native Download uses the existing browser URL operation without a
Python rerun. No already issued PDF is overwritten by a template update.

## Labor V3.3, owner approved27November2026

Any changed saved proposal input revokes Set Prices and both generated download
entry points immediately, using existing events. Set Prices waits for pending
writes, confirms the fresh saved basis, then enables Generate. A newly accepted
generation creates the next immutable project version, including unchanged inputs
when explicitly confirmed again. Technical retry reuses its request/number;
Download returns saved bytes. Reverted edits still require confirmation. Keep
Set Prices natively actionable after issuance; unchanged card viewing and progress
do not revoke a valid download. Profile success invalidates only that company.

Preserve optional Partner/Client/title. The existing All Projects page presents
Partner -> Project -> Source File -> Calculation -> immutable proposal versions,
objects and PDFs. Keep its header/navigation/latest-project row. Native disclosure
and download add no rerun; company-scoped collections are paginated and loaded
in parallel, PDF URLs signed in batches. No separate page or CRUD controls.
Partnerless/legacy history remains visible, identical filenames do not merge.
Content hash identifies a source within a project, changed content creates a new
file/object set, names are not identity. Explicit future project selection uses
an owned stable Project ID. Each issued version freezes complete calculation
inputs/results/source/Profile metadata. Date stays in the PDF/metadata; filenames
contain the version and optional names without date. Old issued files stay intact.

Production terms are one compact preliminary estimate paragraph in English,
then its conversational-business Hebrew translation; Installation is a second
sentence in the same paragraph. No final full stop. Both languages retain the
same right edge and18pt leading. The existing input label becomes Estimated
production time; caption says preliminary estimate in working days / installation
time not included. Preserve units, defaults/NULL/zero, input behavior and geometry.
No new notice, observer, timer, poll, writer or full pricing reload on Generate.
Database extension/publication is explicitly owner-approved after full checks.

Manual File Review names persist through a private tenant-scoped compare-and-set
RPC into the canonical record and working estimate mirrors. Late worker writes
retain the canonical name. Successful changed names revoke draft confirmation,
refresh affected cached/prepared names and require Set Prices for the next Vn.
A failed name write retains the current actionable state; old issued names stay.
