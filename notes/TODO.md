# TODO

DEFERRED, P1, USER DECISION, Detection external envelope dimensions: do not
make W/D/H extraction a Detection critical-path objective or an Estimation
precondition. Show only directly evidenced values as optional File Review
context and preserve unknown values otherwise. Trigger: a future dedicated
object-view and dimension-chain evidence architecture, approved separately.
The 04.10 original-OCR projection experiment is not a candidate implementation:
the current direct-PDF OCR result has no object-local drawing text to project,
the private evidence bucket accepts images rather than JSON, and the worker was
reverted. Before reopening, approve the object-local OCR evidence contract,
storage format and single-pass OCR profile, then test it without altering
Detection, quantity, deferred Naming or Preview publication.

DEFERRED, P2, USER REQUEST, Legal template research: review
https://github.com/General-Legal/legal-templates/ and identify reusable clauses,
document structures, drafting patterns, or process safeguards for Costerly's
future legal work. Recommend only evidence-backed adaptations that fit the
existing Terms, Privacy, Customer Content, and consent-release model. Do not
copy or implement templates automatically, and do not reopen the closed 3.11.1
legal release. Trigger: owner explicitly starts a new legal work block.

COMPLETED AND OWNER-ACCEPTED, 3.16.1 Partners workspace foundation: Partner is the required top-level entity.
Organizations use one company-scoped identity with Partner and Client roles;
one organization may hold both roles. A Project belongs to one Partner and may
reference one Client. Finalized estimates become immutable Project Versions.
The production interface is one Partners page with shared header navigation,
native expandable Partner rows, and nested Project rows showing Project,
Client, calculation date/time, total, and PDF. The current-page Projects action
is omitted. No Partner, Project, or Version detail routes belong in this stage.
Permanent records are not created before Final Approval.

COMPLETED AND OWNER-ACCEPTED, 3.16.2 Final Approval: replace Generate Proposal with one Final
Approval action available only after every object is priced and approved. The
action atomically matches or creates Partner and optional Client roles, matches
or creates the Project, assigns the next version number, and stores an immutable
JSON snapshot of Objects, project costs, and totals. Repeated approval of the
same estimate is idempotent. Final Approval remains on Objects and changes to a
pale green Approved state.

PENDING, 3.16.3 Processing handoff polish: after the current File Review
transition regression is removed, evaluate holding the completed Processing
screen slightly longer so the next fully styled File Review replaces it in one
perceived frame. Measure the existing Detection completion, server render,
target visible, and target styled boundaries first. Do not add a fixed delay
unless it improves the real production transition without increasing total
time unnecessarily.

COMPLETED AND OWNER-ACCEPTED, 3.16.4 Client Proposal PDF: Final Approval generates a private PDF from
the immutable approved snapshot. The header uses only populated Company
Contacts and the company logo. The commercial body contains Project, Partner,
optional Client, Objects with quantity and sale prices, Delivery, Installation,
VAT, and totals, with no self cost. Partners exposes the latest proposal through
a short-lived signed PDF link. The private production bucket was provisioned
and its upload, signed URL, and cleanup cycle verified. Remaining: authenticated
production acceptance of Final Approval and PDF download.
The owner refined the completion flow: Final Approval remains on Objects,
changes to an Approved state, and reveals a download row below Installation.
That row contains Client Proposal / Download PDF and Project Summary / Download
XLS. XLS remains disabled until the later consolidated project materials export
is implemented. The Partners header keeps shared navigation but omits the
current-page Projects action.
The approved Objects layout stacks each download action below its title. Client
Proposal stays in the first Objects column; Project Summary starts exactly at
the Installation input axis. The duplicate Project Summary label in the totals
footer is removed, and the Approved action uses a pale green completed state.
Project Price shares the exact Project Summary axis, Project Total retains the
rightmost axis, and VAT occupies the column between them.
VAT is centered between the unchanged Project Price and Project Total grid
lines. Proposal downloads use Project_Partner_YYYY-MM-DD.pdf as the external
filename while private storage paths remain immutable internal identifiers.

PENDING, 3.16.5 Project Summary XLS: generate a project-wide purchasing list
containing all materials assigned across approved Objects. The disabled
Project Summary / Download XLS control is the reserved UI entry point. Define
aggregation, duplicate-material merging, units, quantities, source prices, and
supplier fields before implementation.

DEFERRED, P1, USER REQUEST, 3.16.6 Unknown Partner completion path: a missing,
blank, or explicitly `unknown` Partner must never block Final Approval. Final
Approval must complete normally and store the finalized Project Version under
one company-scoped reserved Unknown Partner group in Partners. All unresolved
projects share that group until the user assigns a real Partner name. Renaming
or assigning the Partner must move the project to the matching real Partner
without changing its immutable estimate versions, proposal files, totals, or
approval history. Trigger: resume Projects and Final Approval completion work.

COMPLETED, OWNER-ACCEPTED, P0, USER REQUEST, 3.16.7 Price Lists rebuild:
replace the legacy
material-only Price Source flow with a source-first tool that keeps materials,
Material Jobs, excluded consumables, supplier identity, VAT,
review, and durable extraction state distinct. Stage 1 is the additive data
contract: retain source supplier spelling and aliases, link an operation-service
row to the existing global `reference_operations` catalog, and persist private
supplier operation offers separately from material offers. No existing source
or material offer is reclassified automatically. Detailed contract:
`notes/PRICE_LISTS_REBUILD_3_16_7.md`. The 2026-10-07 closure contract makes
supplier resolution, material and offer merging, VAT evidence, source lifecycle,
final-cycle UI, permanent deletion, and minimal Needs Review the P0 completion
scope. Owner accepted the ordinary-source extraction path on 2026-10-09.
Supported JPEG, PNG, PDF and mixed batches retain independent source handling
and merge only on the canonical supplier plus invoice identity. Price and Unit
are the only Review reasons. The scanned multi-invoice-PDF router remains
explicitly deferred in `notes/PRICE_LISTS_CHECKPOINT_3_16_7_2026_10_08.md`.
A later Estimation resolver consumes accepted offers only and is not a reason
to reopen frozen supplier ingestion behavior.

ACTIVE, P0, USER REQUEST, 3.17.1 Unified material taxonomy, identity, brands,
and Material Jobs: establish one bilingual, structured normalisation contract
for Price Source, company catalog, Israel Price List, Detection and Material
Jobs. Canonical display order is entity, primary attribute, brand, then ordered
secondary attributes. Supplier SKU remains supplier-scoped evidence only. The
work includes Hebrew/English aliases, OCR-tolerant variants, department-scoped
brand aliases and a Material Job route to reference operation plus supplier
operation offer, never a material offer. It must preserve the frozen 3.16.7
supplier, VAT, source lifecycle and UI paths. Contract:
`notes/MATERIAL_TAXONOMY_3_17_1.md`.
Pending owner decision within this work: whether low-cost discrete Hardware is
excluded as small consumables. Proposed policy is verified unit price at most
ILS 10 ex-VAT plus explicit package or line quantity at least 10. It must run
after arithmetic verification and must not reclassify the item away from
Hardware.

ACTIVE, IMPLEMENTATION CHECKPOINT `5f6360f`, P0, 3.15.24 canonical object quantity and durable Object Detail route:
make item quantity editable on File Review, Objects, and Object Detail. All
three screens share `rfq_detected_objects.quantity` as the canonical record;
the estimate row is its synchronously updated workflow read model, avoiding an
extra detected-objects query on every screen render. A change must preserve unit
self cost, recalculate commercial line and project totals, clear that object's
approval, and become visible on every screen without rerunning Estimation.
Objects Review keeps the fast live-session bridge, but its normal link must use
the durable company-scoped object route token so an expired Streamlit session
restores Object Detail instead of falling through to Upload. Acceptance covers
edits from both new inputs, cross-screen persistence, reapproval behavior, and
the expired-session Review scenario in authenticated production.
Object Detail follows its existing approval boundary: table edits and item
quantity remain a page-local draft until Approve Estimate persists one snapshot.
Back to Objects must ask before discarding a changed draft. Objects quantity is
an independent immediate-save field. Both quantity controls clear their current
value on focus so the first typed digit replaces, rather than appends to, the
displayed value. The Objects quantity input shares the Sale price input axis.
The native browser confirmation is not accepted UI. Use the Costerly-styled
discard modal. Changed-draft approval must submit through the live Streamlit
session, not the cold query-string snapshot reload. The component-rerun draft
bridge was rejected after two production failures because it exposed an
intermediate Object Detail render. The replacement stores the draft through the
authenticated `save_rfq_object_detail_draft` RPC and then triggers exactly one
native Approve callback; Objects quantity uses the authenticated
`save_rfq_object_quantity` RPC and updates the current DOM without a Streamlit
rerun. The additive migration was applied on 03.10.2026. Production acceptance
must compare both changed and unchanged Approve timing, confirm that quantity
save dims immediately, and confirm grouped money formatting and Materials totals
after editing any material row. The zeroed-Materials regression was traced to
ordinary rows rendering `data-policy-percent="—"`; the client calculator treated
every row as a pricing-policy row. Ordinary rows now render an empty attribute,
with a deterministic regression test. Changed-draft approval also writes the
recalculated totals and approved state together, removing the redundant second
authorization/read/write approval pass.

COMPLETED AND OWNER-ACCEPTED, P0, 3.15.25 Processing to File Review handoff
latency: the first File
Review render must reuse the exact validated Detection payload already persisted
by Processing instead of repeating ownership, run, detected-object, and usage
reads. Refresh and restored sessions continue loading Supabase. The complete
marker must not begin a deliberately extended gray interval. The zero-delay
candidate was rejected because the browser observer missed the marker and
exposed intermediate Streamlit DOM. Use only the bounded 120 ms handshake needed
by the existing 80 ms watcher, while preserving Cloudflare target readiness.
Production acceptance completed: the transition is fast, intermediate fragments
are no longer exposed, and the owner accepted the remaining gray interval of
approximately 1-2 seconds. Checkpoint: `5c322bf`.

HISTORICAL, SUPERSEDED FOR NEW PERFORMANCE WORK, 3.15.23 P0 authenticated full-reload optimization: production telemetry
shows that a hard reload frequently takes 6-8 seconds and can reach the
wrapper's 8-second fallback. Preserve the accepted Fast Resume and `app-ready`
readiness contract. The first candidate removes the legal release lookup from
authenticated Fast Resume and repeated session reruns, records product activity
off the render path, and performs the first Platform Admin and Last Estimate
lookups concurrently. Sign In still performs the required Terms gate. Do not
add a polling fragment or a second full-page rerun merely to activate header
controls. Treat the separate server-ready to browser-received delay as a
distinct Streamlit transport/render investigation, not as proof of slow Python.
The active transition pass also covers Upload, Profile, Admin, Partners, File
Review, Objects, and Object Detail navigation. Acceptance requires every normal
transition to complete within 3-4 seconds, no intermediate broken DOM, and the
destination opening at the top. Current production evidence isolates three
defects: Last Estimate repeats an already completed latest-estimate lookup,
Object Detail transitions lack target-ready closure and masking, and first-load
Partners/workflow routes retain transport or data-load outliers above 4 seconds.
The approved repair sequence is: close masked internal transitions from the
destination `app-ready` event, then keep ordinary Objects to Object Detail and
Back navigation inside the live Streamlit session. Object Detail approval keeps
its snapshot-bearing reload until editable-line persistence is redesigned, but
must preserve the wrapper trace so the destination can close the transition.
Production acceptance must also verify the authenticated navigation controls on
File Review. Server telemetry confirms that `account_controls_render` ran, but
the owner observed the control rail missing visually, so DOM visibility remains
unknown and is not closed by server-side render evidence.
Production checkpoint `7c81a5a` is owner-accepted for the current transition
speed, scroll-to-top behavior, and authenticated workflow navigation rail. The
owner confirmed that the rail now survives File Review, Objects, and Object
Detail navigation. This remains an intermediate performance checkpoint because
post-fix p50/p95 and remaining initial-load outliers are not yet closed.
The first native Object Detail bridge candidate did not intercept production
links reliably: Object Detail still opened under a new trace and caused three
15-second wrapper timeouts. The second and final bridge attempt must resolve
the hidden button by both key and label. Target-side scroll reset must run after
the destination DOM is ready because the earlier pre-render reset was later
overridden by Streamlit scroll restoration.
Source inspection identifies the workflow header alignment guard as the narrow
leading cause of the missing File Review rail: it selected the first workflow
title in the document and could align the fixed controls to stale Streamlit DOM
from the departing screen. The repair must select only a connected, visible,
non-stale title and clear the previous inline transform before aligning the
current screen.
Production acceptance confirmed that selecting a visible non-stale title and
scoping each workflow guard to its screen-specific title repaired File Review,
Objects, and Object Detail return navigation while preserving fast transitions
and scroll-to-top.
The 2026-10-03 Profile to Last Estimate outlier began a File Review server run
within about 0.50 seconds and completed auth plus membership in 237 ms, but the
run never completed `server.screen_render` or emitted `app-ready`. Earlier Last
Estimate evidence completed in 864 ms with a 22 ms screen render. Treat this as
a likely File Review/Supabase I/O outlier, not a transition-wrapper diagnosis.
If it repeats, add scoped timing around File Review data loading and then a
bounded timeout/recovery based on that evidence.
The later File Review regression is now isolated more narrowly: initial render
keeps the navigation rail, but the deferred Naming or Preview publisher issued
`st.rerun(scope="app")` when an artifact became terminal. That full rerun
unmounted the shared rail during Streamlit reconciliation. The active repair
keeps the rail and summary outside the two-second File Review fragment; only
object cards refresh from the persisted deferred artifacts. The earlier
File-Review-only stale-Upload CSS override is removed because it addressed the
wrong phase. Pending owner production acceptance: one run must retain the rail
while both a preview and an object name replace their placeholders.

COMPLETED, P0, 3.18.1 authenticated Upload first paint, owner accepted 10.10:
instrumented the complete cold path and moved non-critical Platform Admin and
Last Estimate reads behind the first authenticated Upload reveal. The resulting
three owner production hard reloads were 3.05 s, 3.06 s and 3.23 s, median
3.06 s versus the immediately preceding comparable median 3.36 s. The server
critical-path median fell from 1.03 s to 0.28 s. Fast Resume remains one Python
run; RLS remains mandatory before authenticated content; no polling, second full
rerun, synthetic loading screen, or Price Lists behavior change was introduced.

COMPLETED, P0, 3.18.2 Profile first-paint and tab-latency measurement checkpoint,
owner accepted 10.10, depends on 3.18.1: live authenticated cold evidence records
the complete Upload-to-Profile and first-open tab path without changing the
owner-accepted Price Lists interaction contract. The production cold run measured
2.30 s Upload-to-Profile visible completion, with 2.27 s server work: 1.87 s
eager Profile import plus 0.37 s Overhead Expenses. First tab renders measured
Price Lists 0.49 s, Labor Costs 0.19 s, Company Details 0.19 s, Machinery 0.57 s,
and Users 0.64 s. The safe Price Lists projection-start hook did not produce a
confirmed pre-warmed Price Lists result in this owner trace, so this checkpoint
does not claim successful tab preloading. It preserves the 3.16.7 Price Lists
screen exactly: no callback, fragment polling, upload, Source, Review, DOM, toast,
or catalog-loading-contract change. Any renewed Profile performance work must use
this cold baseline and separately validate eager-import removal and tab warming.

COMPLETED, P0, 3.18.3 cold Sign in and authenticated bootstrap architecture,
depends on 3.18.1 measurements: optimise the worst customer path from Sign in
click through the first authenticated Upload reveal, and establish one measured
bootstrap architecture shared by cold Upload, Profile and Sign in. Record the
correlated browser, iframe, Streamlit-bootstrap, sign-in action, browser-session,
RLS, header-read, first-run and reveal timings. Do not count warm navigation as
acceptance. Prefer one coherent architecture over isolated wrapper micro-tweaks;
preserve Fast Resume, native authentication controls, one Python run where
possible, the accepted transition mask, and all protected 3.16.7 Price Lists
behavior. Owner acceptance on 10.10: Terms and membership gates now overlap only
after Supabase accepts the password, both remain mandatory before Upload, and
fresh Sign in to Upload traces reached 1.98 s, 2.46 s, 2.58 s and 2.98 s without
adding polling or a second Python run. Further wrapper/iframe bootstrap work is
deferred until a separately measured performance task.

DEFERRED, P2, USER REQUEST, 3.15.26 sleeping-session recovery feedback: when a
user refreshes Costerly after a long idle period and the application or session
must wake and restore authenticated state, replace the unexplained prolonged
gray screen with an explicit recovery state such as `Restoring your session`.
Show it only when wake or recovery is actually detected, not during ordinary
navigation or fast refresh. Preserve the accepted Fast Resume, authentication,
membership validation, transition masking, and no-intermediate-DOM contracts.
Acceptance requires a real long-idle production refresh, a truthful recovery
message while waiting, no broken screen fragments, and normal navigation once
restoration completes. Trigger: resume cold-start and session-recovery work.

COMPLETED AND OWNER-ACCEPTED, 3.15.23 Object Detail edit recovery: the
navigation rail remains protected by the accepted stale-state observer, and
material edits no longer collapse the full Materials section to zero. Browser
feedback is intentionally limited to the active row Cost. Enter or blur saves
the edit, and the server remains authoritative for policy rows, section totals,
VAT, and final self cost.
The first DOM-isolation candidate did not repair material recalculation: any
material edit still collapsed the whole Materials section to zero. The next
candidate removes formatted row-cost text as a calculation input and rebuilds
every material line deterministically from `unit_cost * quantity`, followed by
the locked policy percentages and section totals.
REJECTED: rebuilding client-side material totals from editable fields produced
the same zero-collapse. Stop the duplicate browser calculator. The accepted
recovery path saves the edited field on blur and lets the existing server
transaction recalculate lines, policy percentages, section totals, VAT, and
self cost before the refreshed Object Detail is shown.
RESOLVED: production evidence showed no line `updated_at` after an edit that had
not left the contenteditable field. Restore only current-row live Cost feedback
(`unit_cost * quantity`, or the equivalent Labor row formula), while blur or
Enter remains the single persistence and authoritative server-recalculation
boundary. Do not restore browser-wide section or final-total calculation.
DEFERRED, P2, 3.15.23 Approve transition optimization: production trace
`28dac1ea-5c35-40aa-9109-8246a22c2078` showed direct-link Approve creating a
new iframe/server session while the original transition reached its 15-second
timeout with zero Python runs. Reuse the accepted Streamlit bridge when the
Object Detail snapshot is clean. Retain the direct snapshot route only when
unsaved edits must be persisted atomically with approval. Code `89dda51` is
deployed and fully tested. Two clean production bridge cycles reached visible
Objects in 2.38 and 2.42 seconds and styled readiness in 3.41 and 3.44 seconds,
instead of the previous 15-second timeout. About 1.85 seconds consistently
passes before the destination Python run begins. When resumed, instrument
`_approve_current_object_and_return`, `approve_object_estimate`, deterministic
recalculation, and the approved-state write separately. If evidence confirms a
redundant full recalculation for a clean persisted snapshot, skip only that
duplicate work while retaining the atomic snapshot fallback. Trigger: owner
resumes transition-performance work.

PROPOSED, P1 background Terms reacceptance: authenticated Fast Resume does not
block initial rendering on the legal release lookup. Add a later background
version check and a blocking in-product modal that requires the current Terms
checkbox before the user continues. Preserve immutable acceptance evidence and
document that enforcement of a newly published version is delayed until that
background check runs.

COMPLETED AND OWNER-ACCEPTED, 3.15.22 Objects Estimation live result refresh:
replace the removed
React-DOM progress writer with a server-side Streamlit fragment that polls the
persisted per-object rows while the Estimation future is active. Preserve the
fast seeded first render, stop polling on terminal completion, and do not change
Cloudflare, authentication, workflow routing, or transition readiness. Local
candidate now also clears stale process-local progress, suppresses Streamlit's
stale-fragment dimming, and keeps Delivery, Installation, and Project Summary
visible with blank values until every object has a terminal priced result.
Production acceptance and the 861-test suite passed at `8b18fc3`. Full record:
`notes/OBJECTS_LIVE_ESTIMATION_CHECKPOINT_3_15_22_2026_10_03.md`.

Current owner-approved execution order:

ACTIVE, P0, 3.15.27 Anthropic token-cost accounting: record the cost of every
successful Anthropic model request from the usage fields returned by the model,
using the configured per-token pricing and preserving the existing request,
run, company, agent and model identity. The Platform Admin Detection,
Estimation and Price Source totals must include every such recorded request,
regardless of agent version or company. This is an application-calculated
usage cost, not a claim of an invoice-level provider debit. Mistral OCR is
explicitly excluded from this task and must remain unpriced rather than being
estimated from a public list price. Acceptance: nonzero Anthropic calls in all
three categories appear in the matching company row and in its total, while
zero, failed or unavailable events are visibly distinguished from a known zero.

DEFERRED, P1, USER REQUEST, 3.15.28 full provider billing reconciliation:
create a billing system that reconciles Costerly's request ledger with official
provider billing data, records reconciliation status and time window, and
never represents a local token calculation as an exact account debit. Design
the provider credentials, access controls, retention, aggregation boundary,
credit/adjustment treatment, and Mistral ingestion before implementation.
Trigger: after 3.15.27 is accepted and provider billing-data access is
available.

ACTIVE, 3.15.19 File Review editable project metadata: render Project name,
Partner, and Client as compact inputs using the accepted 52 px Overhead input
geometry. Persist edits only to the current RFQ run, keep drafts scoped by
run, and save the final visible values before Continue to Objects. Do not
create permanent Partner, Client, or Project catalog entities before Final
Approval. Local implementation and the 868-test suite pass. Remaining
acceptance: production deployment and owner verification of editing,
persistence, and unchanged File Review to Objects transitions.

COMPLETED AND OWNER-ACCEPTED, 3.15.18 Machinery session draft restoration:
restore the previously
accepted `722b6c6` interaction contract on the current performance baseline.
Machinery changes remain in the Streamlit session across Profile tabs and write
to Supabase only through one bottom Save action. Preserve the approved machinery
capability subset and existing domain model. Production acceptance must confirm
draft retention, one-save persistence, failure retention, member read-only
behavior, and the softer selected Yes/No colors. Production acceptance passed
at `1e1edaa`; full record:
`notes/MACHINERY_SAVE_AND_INITIAL_LOAD_CHECKPOINT_2026_10_03.md`.
The owner rejected the additional checkbox for changing a persisted in-house
capability to No: the explicit bottom Save action is the confirmation. Save must
not partially persist earlier rows and then stop on that removed UI barrier.

PROPOSED, P1 Machinery atomic batch persistence and Save visual polish: replace
the sequential multi-row persistence loop with one transactional RPC so a
transport or database error cannot leave a partial Save. Remove the single
fragment flash observed after an otherwise successful Save while preserving the
accepted session draft, success notice, and one-action contract.

ACTIVE, 3.15.17 Pricing Cost restoration on the accepted `d3e83bd`
performance baseline. The Pricing persistence and deterministic calculation
contract are restored without the later transition experiments. The Profile tab
is named Pricing Cost, follows Labor Costs, uses the Bank Details white
two-column form and one Save action, and keeps the compact eight-tab rail.
Local implementation verification passes. Remaining acceptance: deploy, verify
owner save and member read-only behavior, then repeat the protected production
transition timings before restoring Machinery or File Review metadata.

ACTIVE, 3.15.7 Labor reference-model foundation: checkpoint recorded in
`notes/LABOR_FOUNDATION_3_15_7_CHECKPOINT_2026_09_30.md`. Time baselines,
roles, drivers, source links, confidence markers, material-specific metal
routes, formulas, construction templates, crew rules, golden scenarios, and
the Labor Engine contract are prepared. Deterministic implementation is active:
five templates are implemented and 40 targeted tests pass. Next: complete the
remaining approved templates, batch aggregation and all ten golden scenarios.
The Estimation Agent replacement remains a later task. Full continuation is in
`notes/MATERIALS_LABOR_NEXT_CHAT_HANDOFF_2026_09_30.md`. This priority does not
cancel 3.15.4 through 3.15.6; they remain pending at their recorded checkpoints.

ACTIVE, pending Railway deploy, auth regression: pressing Enter while focused
in the Sign in password field must submit Sign in, never trigger Forgot
password. The local 29.09 observation proved that Streamlit selects the first
form submit button, which was Forgot password. The local implementation is
complete. Preserve recovery and verify it in the real authenticated production
browser after Railway becomes available.

UI follow-up, local Price Source: inspect and correct the observed green-on-green
status treatment. Reuse the accepted production status-token hierarchy, then
validate the actual rendered local and production states. Do not infer the
cause from the local screenshot alone.

0. Backlog, cross-agent failure observability: record every attempted run before
   network, file, model, or persistence work begins. Keep an internal failure
   record with agent name, company-safe correlation ID, input type and URL/file
   metadata, stage, bounded diagnostics, timing, model/provider metadata, and
   sanitized error. Build an internal review queue with retry, evidence view,
   grouping by failure signature, and alerting for repeated or systemic failures.
   Scope: Detection, Estimation, Price Source, Material Identity, and future
   agents. This is internal only, must not expose one company's content to
   another, and must not slow the happy path. The current Tsidky URL fetch
   failure is the first acceptance case.

1. Finish 3.15.4 Price Source integration with the shared Material Resolution
   Core. Detailed checkpoint: `notes/PRICE_SOURCE_MATERIAL_RESOLUTION_3_15_4.md`.
2. Run the first representative production Price Source through the resolver
   and accept exact, shortlist, and unmatched behavior with real evidence. The
   second Tsidky run is not accepted: service separation improved, but canonical
   resolution and the bounded Identity Agent failed their acceptance criteria.
3. Build the internal material identity review interface as task 3.15.5. Staff
   must be able to inspect the source evidence and bounded shortlist, link an
   existing reference material or create a reviewed new identity, preserve an
   immutable decision audit, and publish a confirmed alias for future imports.
   This is an internal Admin workflow, not a required company-user action.
4. Optimize Price Source end-to-end latency as task 3.15.6. Benchmark URLs,
   PDFs, spreadsheets, and photos separately; measure fetch or upload, parsing,
   model time, legacy material and offer persistence, identity resolution, and
   final UI refresh. Batch remaining row and offer writes, avoid repeated reads,
   preserve accuracy and audit behavior, and add honest stage progress or a
   recoverable background workflow for genuinely long runs. The first URL
   baseline was more than two minutes: 60.6 seconds in the model, about 31
   seconds in legacy persistence, and about 36 seconds in the original
   sequential identity stage. The identity stage is already batched; its new
   production timing remains to be measured.
   Coatings pricing coverage is a separate deferred input task: seek an
   evidence-backed Israel B2B catalog or invoice from a professional factory
   coatings channel, beginning with Sayerlack through its Israeli professional
   representative. Do not seed Israel baseline prices from retail suppliers or
   foreign retail prices. Preserve real purchase-pack prices. A price-per-liter
   figure may only be a comparison fact inside a comparable product line, never
   the estimation fallback price.
5. Complete operations, labor, machinery, and subcontractor reference models.
6. Replace the legacy Estimation Agent only after those inputs are verified.

- 3.15.4 Price Source Material Resolution integration: active, P0. The
  implementation candidate routes every activated Price Source row through the
  shared resolver after extraction, so historical rows can be processed without
  repeating OCR. Exact identity links the private company material to the
  reference catalog. Shortlists and unmatched identities remain private and
  enter the review buffer. Resolution events are append-only, same-version
  batch reruns are idempotent, and resolver failure does not invalidate a
  completed price import. Production currently has zero Price Source rows, so
  the historical pass correctly examined zero rows. The first production URL
  then extracted 47 rows: 41 price-ready, one unresolved, and five excluded;
  identity resolution produced two exact links and 39 bounded shortlists. That
  run exposed a latency regression: sequential identity writes added about 36
  seconds after the 60.6-second agent call and about 31 seconds of legacy row
  persistence. The resolver candidate now batches candidate, source-row, and
  audit writes. A 40-row regression test enforces one write per destination
  table. Full suite: 657 passed. Production timing acceptance remains pending.

  P0 production acceptance blocker from the second Tsidky run on 29.09: v5
  extracted 51 rows, with 37 active prices, five evidence-based unresolved rows,
  and nine operation-service rows correctly excluded. This fixes the earlier
  error where four edge-banding application rows became materials. Preserve and
  regression-test this rule for cutting, drilling, machining, edge-banding
  application, assembly, installation, and delivery on similar supplier pages.
  Canonical resolution is not accepted: zero rows linked, 36 returned
  `no_compatible_identity`, and one returned a shortlist. The resolver currently
  treats a canonical material's missing stored specification as a conflict with
  every extracted attribute, so useful candidates disappear before the agent.
  Change retrieval so only explicit contradictory hard attributes reject a
  candidate; missing canonical attributes reduce confidence and remain visible
  to bounded comparison. Add controlled family-to-category retrieval for sheet
  materials and solid timber without widening automatic-link rules. Correct
  Israeli timber section notation such as `5/2.5` to an evidence-based 50 x 25
  mm section instead of `5 x 2.5 mm` or diameter. The bounded Identity Agent
  produced no recorded decisions in this run; stop swallowing that failure,
  record its error and timing, call it only for rows with useful bounded
  candidates, and preserve the 90 confidence plus no-hard-conflict auto-link
  gate. Reprocess the persisted source rows through the corrected resolver
  without repeating URL extraction, then accept service exclusion, candidate
  recall, automatic links, review routes, latency, and immutable audit together.

- 3.15.3 Material Resolution Core: completed, P0. The deterministic candidate
  resolves exact supplier SKU, company alias, market alias, hard attributes,
  then a maximum-five shortlist. The production read-only benchmark returned
  797/797 correct unique alias matches and 201/201 correct unique supplier-SKU
  matches, with zero false resolutions across five collision keys. The additive
  schema migration is applied to production. The active resolver is
  `material_identity_v1`; all four protected tables were verified through the
  service role before 3.15.4 began.

- 3.15.2 Israel material baselines and furniture-core completion: active, P0 by
  owner direction. The production activation checkpoint is verified: 280
  active v1 baselines cover 280 distinct materials, retain 331 evidence links,
  have complete approval metadata, and expose confidence 10 to 65. The next
  checkpoint is also complete: the isolated company-first resolver handles
  VAT-exclusive normalization, compatible units, multiple supplier ranges,
  price-scope separation, baseline fallback, and explicit review results. A
  production batch resolves all 280 active catalog materials, but production
  has no company material offers yet. Next, Price Source must link recognized
  company items to `reference_material_id`. Automatic Estimation fallback,
  widened identity linking, and private-data market learning remain separate
  decision gates.

- 3.15.1 Israel Reference Catalog foundation: completed at `1f8d6ab`.
  The ordered master plan is `notes/ISRAEL_REFERENCE_PROGRAM_PLAN.md`. Its
  Packages A through J preserve the accumulated material and price work and add
  the approved shared Price Source, identity-candidate, market-learning,
  operations, review-governance, and Estimation-readiness sequence. Production
  now contains the verified schema, identities, profiles, candidate offers, and
  aliases recorded in `notes/ISRAEL_REFERENCE_CATALOG.md`; continuation moved
  to 3.15.2.
  Replace the empty legacy material, work-time, and machining-points foundation
  with a multi-market reference architecture. Global material, operation, and
  labor-role identities remain separate from market-specific prices, local
  specifications, and productivity standards. Israel is the first explicit
  market (`IL`, `ILS`), and cross-market fallback is forbidden. Company data
  remains first priority; an exact Israel baseline is second; unsupported scope
  returns `needs_review`. The schema candidate deliberately contains no invented
  price or time seeds. The candidate taxonomy now contains 82 material
  categories, 43 physical drivers, 77 operation identities, and 29 labor roles.
  The first seven sourced Israel batches add 76 exact material identities and
  85 observed offers: 24 panel offers, 16 fixed-price Blum hardware offers, one
  galvanized steel stock-length offer, five coating/consumable offers, and 14
  solid-wood/OSB offers, nine PVC edge-band offers, plus sixteen acrylic offers
  covering eight raw sheets and eight cut-to-size equivalents.
  `notes/ISRAEL_REFERENCE_MASTER_CHECKLIST.md` is now the fixed coverage
  denominator: 395 materially distinct estimation cells across wood, metal,
  glass, stone, plastics, hardware, fasteners, coatings, consumables,
  upholstery, electrical components, installation, and packaging. Current
  evidence closes 2 cells and partially covers 21; 372 remain empty.
  None is promoted to an active market baseline from a single or incomparable
  source. Continue source coverage and independent-source comparison before
  activation. Before additional broad source harvesting, integrate the accepted
  shared Material Resolution Core contract with Price Source. Ordered backlog:
  (1) define the shared reference, company, source-offer, and identity-candidate
  cards; (2) unify category, specification, unit, alias, scope, provenance, and
  confidence vocabularies; (3) add the candidate lifecycle and immutable review
  audit; (4) route Price Source through exact SKU, company alias, Israel alias,
  hard filters, and a maximum-five shortlist; (5) link matched company items to
  `reference_material_id` while keeping unmatched usable items private; (6) add
  a separate eligibility gate for anonymized market observations; (7) make
  reviewed identities and aliases available to future imports through a
  versioned resolver index; (8) specify merge, split, deprecation, remapping,
  and historical reprocessing behavior; (9) build the staff review tool after
  the lifecycle and permissions are verified; (10) apply the complete migration
  chain to a clean database and test idempotency, tenant isolation, rejection
  cases, and reprocessing before activation. The review tool is explicitly in
  backlog and is not part of the current schema-contract revision. Contract:
  `notes/ISRAEL_REFERENCE_CATALOG.md`.

- 3.14.1 CNC / Laser costing foundation: active, P0 by owner direction. The
  owner promoted this task to the highest current priority on 28.09. Follow
  `notes/CNC_LASER_FINISH_PLAN_2026_09_28.md`. C1 production schema is verified;
  C2 read-only Staff Admin has a tested implementation candidate awaiting live
  acceptance. The material catalog remains preserved but paused until the CNC
  subsystem reaches its production checkpoint. The calculation engine is
  demand-driven and runs only a required process for one
  homogeneous part group. CNC `Yes` means in-house. CNC `No` uses a narrow
  panel-saw plus manual route only for simple low-volume rectangular work and
  otherwise uses a CNC subcontractor. Sheet laser `No` defaults strictly to a
  subcontractor; rough basic in-house cutting is a rare explicitly confirmed
  exception. The active CNC route has one explicit estimate level
  from 1 to 5; level 3 is the effective untouched default and is not feedback.
  Explicit changes append a bounded behavioral-calibration event without
  estimate cost or customer content. The local candidate passes 514 tests.
  `db/sql/2026_09_28_cnc_estimate_levels.sql` and the broader manufacturing
  parameter migration were applied to production on 28.09. The isolated
  deterministic router, exclusive calculator dispatch, four pure calculators,
  reserve-level selection, supplier-minimum handling, inclusion boundaries,
  parameter snapshot IDs, and scenario fixtures are implemented and pass the
  full suite locally. Active parameter resolution now enforces exact scope,
  containing thickness bands, provider isolation, units, currency, effective
  dates, approval, provenance, and explicit missing or ambiguous review states.
  It never selects the nearest unsupported scope. None of this is connected to
  current Estimation results. Continue with Revision A migration review and the
  read-only Admin parameter library.

- 3.12.1 Price Source Agent accuracy: historical tracking, superseded by active
  3.16.7 for current implementation and acceptance. Preserve the following
  revision history as evidence, but record all new Source Agent work only under
  `notes/PRICE_LISTS_REBUILD_3_16_7.md`. Improve real supplier-source
  extraction, material-type classification, unit normalization, confidence,
  and ready-versus-unresolved decisions while protecting the accepted 3.10.1
  Price Catalog UI checkpoint `d18b533`. The approved v3 candidate adds row-level
  Material Type, document number and totals, VAT evidence, semantic duplicate
  protection, and Source Details timing and TC. Automated verification and a
  representative production evidence pass remain required. Revision 2 now
  separates extracted and active counts in the completion notice, shows time
  and TC immediately, removes manual Price Source reruns, and restores native
  file-delete hit testing. Revision 3 removes confidence as an activation gate,
  blocks only price-critical VAT and package-conversion uncertainty, standardizes
  normalized names, and adds row-level Review, Edit, and Remove. Revision 4 moves
  those actions into the main catalog, exposes unresolved rows in a visible Needs
  review block, removes whole-source deletion, and repairs the client-only stuck
  Extracting prices state. Revision 5 treats repeat uploads as row-level update
  checks: exact duplicates skip the agent, changed inputs report new, updated,
  unchanged, and unresolved counts, unchanged offers are not rewritten, and
  missing rows are preserved. It also restores the accepted compact catalog
  geometry after the row-action visual regression. Revision 6 opens only the
  original source from Source/View, paginates Needs review for responsive row
  actions, marks only activation-blocking fields, removes duplicate editor
  headings and row gaps, and suppresses non-informational hover tooltips.
  Revision 7 preserves that geometry, lowers the Needs review labels by 3 px,
  removes duplicate fragment reruns, and reuses a tenant-scoped read snapshot
  for fast UI-only actions while invalidating it after every data mutation.
  The owner accepted revision 7 in production at `d99a594` as the fast working
  Price Lists interaction checkpoint. Visual polish is not final, but further
  agent-accuracy work must preserve this version. Revision 8 adds internal
  source-family and revision metadata for recurring files and URLs while
  retaining exact-duplicate short-circuiting and row-level new, updated,
  unchanged, and missing behavior. Revision 9 prevents invalid multi-document
  selections from entering processing. Revision 10 block A adds first-class
  internal-estimate and customer-sale provenance, keeps internal rows reviewable
  until their isolated offer lane exists, and deterministically excludes selling
  prices from material costs. Revision 11 adds an explicit server completion
  marker so a completed run cannot leave the optimistic Extracting prices state
  behind. Revision 12 makes that marker processing-cycle aware, so an old idle
  marker cannot immediately cancel the next click's progress state, and removes
  the misleading zero unchanged count from unresolved-only duplicate results.
  Revision 13 establishes the MVP uploader contract: multiple JPEG/PNG pages
  remain one logical document, while PDF, XLSX, and CSV keep only the first
  selected document. In a mixed selection, the first file selects the route:
  photo-first keeps all JPEG/PNG pages, document-first keeps only that first
  document, and a compact note explains the rule when files are rejected.
  Photos retain a four-column, two-row scrollable grid; a single document gets
  a centered enlarged card with a readable name. Revision 14 block B1 adds a
  first-page PDF preview and structural XLSX/CSV template identity so renamed or
  value-updated workbooks remain auditable revisions of one source family.
  Revision 15 extends real previews to XLSX, CSV, JPEG, and PNG, blocks a second
  PDF/spreadsheet against the document already rendered in the uploader rather
  than only filtering the latest picker batch, and keeps every completed
  Extract result visible until the next Extract attempt. Sequential JPEG/PNG
  pages remain supported as one photo document. Revision 16 isolates the
  invalid-second-document drag state: the accepted chip and preview stay
  visible, only the existing card border turns red, leaving the zone clears the
  red state immediately, and the yellow explanation appears only after reject.
  The owner accepted the complete uploader behavior in production at
  `1a2d7ca`; this is the rollback checkpoint for upload selection, previews,
  repeat-result feedback, and occupied-zone drag indication.
  Revision 17 block B2 is now a tested production candidate. Internal estimates
  activate only when VAT and package conversion are resolved, stay in the shared
  Material Prices catalog without a fake supplier, and version within their
  recurring source-family lane. Supplier, unknown-supplier, unrelated internal,
  and reviewed-row offers remain isolated. The full suite passes with 403 tests.
  Production acceptance remains pending for one internal workbook, its changed
  revision, and coexistence with a supplier offer for the same material. After
  that evidence, source-level VAT confirmation is block C. Mixed-document
  queueing remains deferred under 3.12.3, and resolver priority remains deferred
  until both offer lanes have production evidence.
  Revision 18 block C1 is now a tested candidate. Needs Review can apply one
  explicit currency and VAT basis to a persisted internal source without another
  agent call. Complete positive unit prices can enter the B2 internal lane even
  when line quantity is zero; unresolved units or conversions stay in review;
  deterministic non-material cost rows are excluded. The full suite passes with
  407 tests. Production acceptance on the latest internal workbook remains
  required before C1 becomes a checkpoint.
  Contract: `notes/PRICE_SOURCE_AGENT.md`.

- 3.12.2 Cross-agent Token Cost observability: pending, P1 after the Price
  Source Agent cost display establishes the shared convention. Show compact
  `TC X.XXX` per completed run and total cycle from persisted provider usage
  without double counting. Preserve model, prompt version, input/output tokens,
  configured pricing source, and unavailable-cost state. Apply to Detection,
  billable OCR, Naming, Estimation, and future agents.

- 3.12.3 Batch Price Source ingestion: deferred after MVP, P2. Let an owner drop several
  independent PDF, spreadsheet, and image documents in one action, split them
  into logical sources, and process them through a bounded sequential queue.
  Each source needs its own validation, progress, result, retry, duplicate or
  revision decision, timing, and TC so one bad document cannot block or obscure
  the others. Preserve the existing rule that several JPEG/PNG pages may form
  one logical document; grouping mixed photos into documents needs an explicit
  user or deterministic grouping contract before implementation.

- 3.12.4 Existing email registration guard: tested candidate, P1. After an
  invitation signup is submitted, treat Supabase's obfuscated existing-user
  response and explicit `email_exists` response identically. Keep the signup
  form open, mark Email, and show `This email already has a login. Sign in or
  use another email`. Do not create a pending legal registration, legal event,
  company, or membership, and do not consume the invitation. The full suite
  passes with 409 tests. Production acceptance with one existing address and
  one fresh address on the same unconsumed invitation remains required.

- 3.9.1 Machinery and production routing foundation: active, P1. Add a compact
  16-capability profile across woodworking, metalworking, and finishing while
  retaining the 27-row database catalog for compatibility and history,
  with wood CNC and metal laser cutting as separate first-class capabilities.
  Company owners record explicit in-house availability, minimum technical
  limits, costing basis, and optional regular subcontractors only for operations
  that are realistically outsourced. Saved rows collapse to a summary and
  multi-value capabilities use selectable pills. The additive Supabase migration was applied on 24.09:
  all five new tables are available, the catalog contains 26 active rows, new
  company tables are empty, anonymous catalog access is denied, and all 124
  prototype `company_machines` rows remain untouched. The owner/member Profile
  UI, deterministic production-context snapshot, and automated scenario
  coverage are implemented locally and 291 tests pass. The real owner/member
  production pass, mobile/keyboard pass, commit, deployment, and acceptance remain pending. The production
  context is not sent to Anthropic until the owner explicitly approves transfer
  of private machinery, supplier, and pricing data or approves a sanitized
  payload contract. Continue from `notes/MACHINERY_FOUNDATION.md`.

- 3.8.1 Railway hosting migration: accepted production checkpoint. Preserve
  production checkpoint `bbb8297` and retain the Streamlit Cloud deployment as
  rollback while the existing Cloudflare wrapper runs against Railway at
  `app.costerly.ai`. The
  wrapper selects the Railway backend only for the staging hostname and uses
  the selected backend origin for all transition handshakes. Acceptance
  requires clean hard refresh, Sign in, Upload to Profile, Profile to New
  Estimate, Profile to Upload, and Sign out cycles without gray, white,
  unstyled, or mixed-screen frames, plus complete correlated runtime telemetry.
  Direct Railway testing is not visual acceptance because it bypasses the
  Cloudflare transition wrapper. The owner explicitly approved switching the
  production wrapper backend to Railway after confirming the direct Railway
  runtime was materially faster. The owner completed repeated Sign in, Profile,
  New Estimate, return, and Sign out cycles and accepted the result as fast and
  production-ready. Trace `a6152e2d-517a-4faa-a125-311c46faa3ef` measured the
  initial Auth reveal at 4.011 seconds; accepted warm styled reveals were mostly
  0.677-1.356 seconds with one Python run. Known acceptance gap: one first
  Profile cycle after a repeated Sign in hit the five-second mask timeout and
  reached ready at 10.869 seconds, and the owner observed one negligible broken
  frame. Retain both as follow-up evidence rather than claiming zero visual
  defects. Verification: 238 tests passed. Checkpoint commit: `4b8b24a`.
  Protected production checkpoint: `bbb8297`.

- 3.8.2 Password recovery: closed by owner on 24.09 without further production
  acceptance work. The working flow and email changes remain preserved at
  checkpoint `f1de50e`; do not treat the former Gmail and full-matrix follow-up
  as active unless the owner explicitly reopens it. The historical contract and
  unresolved verification record remain in `notes/AUTH_PASSWORD_RECOVERY_HANDOFF.md`.
  The completed implementation added a user-visible
  Forgot password flow using the existing Supabase Auth account and the final
  branded application origin. Reuse the accepted Sign in visual and transition
  system, keep account-existence responses neutral, use a single-use expiring
  recovery link, and enforce the registration password policy on reset. Verify
  the actual Supabase recovery-mail transport and redirect contract before
  implementing the production send path. The recovery email and browser-session
  handoff now reach the Reset password form. Production password submission
  was verified by the owner on 23.09: the form changed the password, returned
  to Sign in, and the new password authenticated successfully. The remaining
  active scope is production visual acceptance of the Sign in feedback layout:
  Password and Forgot password share one label row, feedback appears only when
  needed below the input, moves the primary button by one compact line, and
  disappears immediately when the user resumes editing. Production recovery
  acceptance must cover partial Sign in input, syntactically invalid email,
  wrong credentials, recovery immediately after a failed Sign in, and reset
  validation in strict order: password policy first, password match second.
  Server-rendered field markers must replace stale client validation state, and
  every new feedback response must become visible even when Streamlit reuses
  the previous DOM container. Production verification of this sequence remains
  pending. The production recovery mail must also use the repository subject
  template
  `Reset your Costerly AI password [{{ .TokenHash }}]` so every
  request has a distinct subject and mail clients do not thread separate
  recovery attempts together. The HTML template must remain in its light
  Costerly AI palette in dark-mode mail clients, using email-compatible color
  declarations rather than relying on client theme defaults. The hosted
  Supabase template is external state and both changes must be verified
  independently after applying the repository values. The 24.09 Gmail iOS
  screenshot verified that the light background and logo survive dark mode,
  but Gmail still inverted the main paragraph to white. The repository
  template now applies the Gmail blend-mode text guard and removes the nested
  gray page, bordered card, and rounded card treatment in favor of one flat
  white message surface. Production verification remains pending after the
  updated HTML is copied into Supabase and a new recovery message is generated.
  Continue from `notes/AUTH_PASSWORD_RECOVERY_HANDOFF.md`. The owner established
  a mandatory scenario-first UI rule on 24.09: every interface revision begins
  with a complete agreed behavior matrix, and implementation, automated tests,
  and production acceptance must follow that same matrix. Do not resume 3.8.2
  through isolated visual patches.

- 3.8.4 One-time team invitations and access removal: completed and accepted in
  production. The owner confirmed the additive Supabase migration was applied
  on 22.09. Each freshly generated bearer link is not tied to an email, expires
  after 24 hours, and is consumed atomically by the first successful membership
  creation. The Users tab lets only the owner generate a link and remove a
  member after confirmation; the owner cannot remove themself. Removal deletes
  only the `company_members` relationship, not the Supabase Auth user. The
  legacy `company_join_links` table remains untouched as a rollback surface but
  is no longer read by the new application path. Verification covered one
  successful registration, rejection of the consumed link, member removal,
  fresh access denial for that member, and preservation of Profile -> Users
  after link generation. The owner-facing raw token is plain text with a
  dedicated Copy action, never a navigable link. The Join registration screen
  reuses the accepted Sign in heading, full-width submit geometry, validation,
  loading spinner, and retained-screen transition behavior, without the
  redundant explanatory subtitle. The owner accepted the production result on
  22.09. Implementation commits: `013a67b` and `15d5aea`. Railway required a
  manual Deploy Latest Commit because the expected GitHub autodeploy did not
  trigger; that deployment-integration defect remains a separate follow-up and
  does not invalidate the accepted invitation behavior. Verification: 244 tests
  passed.

- 3.8.5 Railway GitHub autodeploy reliability and build timing: completed, P1.
  GitHub `main`
  accepted commits `b9f27d4` and `785d828`, and Cloudflare Pages deployed the
  same source automatically, but Railway did not create a deployment until
  `Deploy latest commit` was triggered manually. Verify the service Source is
  connected to `kzhivin-lgtm/costerly-app` on `main`, Autodeploy is enabled,
  Wait for CI is disabled while no GitHub Actions workflow exists, Watch Paths
  are empty, and Deployments has no skipped or approval-waiting pushes. Then
  prove the repair with one harmless GitHub commit that produces a Railway
  deployment without manual intervention. The baseline deployment exposed
  approximately 112 seconds of build work, including 51 seconds for pip, while
  Railway displayed more than four minutes end to end. The current experiment
  replaces `requirements.txt` with the standard `pyproject.toml` plus `uv.lock`
  path recognized by Railpack 0.39.0 and Streamlit Community Cloud. Local cold
  dependency preparation completed in 7.49 seconds and installation in 0.197
  seconds. Commit `bf0581d` proved the repair: Railway created deployment
  `4dec029a-5989-419c-8be8-751f1e41c954` automatically 16 seconds after the
  push timing mark, selected uv on Railpack 0.39.0, passed its healthcheck, and
  reported success after 193 seconds. Explicit build steps fell from about 113
  seconds to about 72 seconds, a reduction of roughly 41 seconds or 36 percent.
  Approximately 114 seconds before server start remain outside the itemized
  build steps and belong to Railway scheduling and deployment orchestration,
  not dependency installation. Verification: 263 tests passed and both the
  direct Railway health endpoint and `app.costerly.ai` returned HTTP 200.

- 3.6.2 Hard-refresh Sign in reveal stability: preserve the accepted in-button
  spinner and one-run Sign in while preventing partial Upload DOM from appearing
  after Command-Shift-R. Production trace
  `eaf99421-c863-4886-ac74-e34f8d56298b` measured Sign in at 1.106 seconds with
  one Python run, target visibility at 1.077 seconds, and app-ready only 29ms
  later. Replace the insufficient two-frame release criterion with 120ms of DOM
  quiet and a 450ms fail-open. Status: accepted production checkpoint at
  `fb1ad97` (v3.6.2). The user confirmed fast Sign in, the accepted in-button
  spinner, and no partial screen in the tested hard-refresh cycle. Protected
  rollback points: v3.5.11 (`aa05a5d`) and v3.6.1 (`f334338`).

- 3.6.1 Labor Costs table compaction: fit the complete worker summary table
  inside the Profile content width without horizontal clipping. Stack Edit and
  Remove vertically in a narrow action column, show `Hourly` and `Monthly` only
  in the table, omit the employment factor from Pay Details, and size the
  controlled-value columns around their longest supported labels. Shorten the
  managed Position labels, remove Cabinetmaker / Joiner and Purchasing Manager
  from new selections, and hide the optional clear control in the three Labor
  Costs selectors without changing their dropdown action. Existing archived or
  active records retain their stored codes; the retired cabinetmaker code is
  presented as Carpenter. Status: accepted in production at `f334338`
  (v3.6.1); the user confirmed the compact table result. Protected rollback
  checkpoint: v3.5.11 (`aa05a5d`).

- 3.5.2 Profile and Auth performance stabilization: keep v3.4.2 (`86117ba`)
  as the emergency rollback boundary without treating it as a measured speed
  baseline. Split the first Profile path into lazy module import, Profile shell,
  styles, header, tabs, and active content. Use complete production traces to
  identify the earliest slow boundary before changing behavior. Restore warm
  Profile and Auth transitions to the previously accepted range, retain native
  Streamlit actions, encrypted Fast Resume, sessionStorage fallback, route
  restoration, and the Cloudflare transition mask, and accept only after two
  complete user-visible cycles show no broken intermediate screen.
  Production evidence for candidate 3.5.6 identified and removed a redundant
  Upload-to-Profile rerun: navigation now changes screen state in the native
  Profile button callback before the next script render. Acceptance remains
  pending a deployed full-page reload with matching wrapper/server build and
  two clean cycles. The next isolated target is the 1.9-second synchronous
  browser-session store measured during Sign in.
  Regression protection now includes a shared callback-safe screen setter, a
  source test rejecting widget navigation followed by explicit rerun, a
  wrapper/server build handshake with one guarded reload, and per-transition
  Python-run counts. Production acceptance must show matching builds and
  `python_runs=1` for both Profile directions. Status: accepted production
  checkpoint at `aa05a5d` (v3.5.11). The user confirmed satisfactory behavior,
  the in-button Sign in spinner, and clean transitions. The first cold Upload
  to Profile remains somewhat slower than repeated transitions and is accepted
  for this stage rather than retained as an active defect.

- 3.1.12 Refresh route persistence: after browser refresh, restore the same
  authenticated product screen and, where applicable, the same nested tab.
  Apply one explicit navigation-state contract to Profile, File Review,
  Objects, Object Detail, Registration, Company Setup, Auth, and future screens.
  Preserve authorization checks and never restore a company-scoped resource
  without revalidating access. The current revision mirrors only safe route
  state into the outer Cloudflare URL, forwards it to each new Streamlit iframe,
  restores the selected Profile tab and persisted RFQ/estimate/object context,
  and reuses the existing Supabase ownership checks before rendering protected
  resources. Auth and invite-driven screens remain derived from their existing
  authorities. Active Processing intentionally fails safe to Upload because its
  file bytes and futures are not durable yet. The first production revision
  restored Profile after shared account controls had already rendered, causing
  duplicate `company_sign_out` keys. The corrected revision restores Profile
  and its tab before account controls render. The Cloudflare transition layer
  now covers both Profile to Upload and Upload to Profile while the restored
  screen is assembled. Status: accepted production checkpoint at `e48bb71`;
  the user confirmed refresh preserves Profile and its selected tab, no
  duplicate-key error remains, and both transition directions are clean.

- 3.1.11 Profile to Upload transition integrity: identify and remove the
  intermediate stale or partial screen visible after Continue to upload.
  Preserve the accepted Profile and Upload layouts, native button behavior,
  transition telemetry, and the v3.1.10 navigation callback. Production logs
  confirm a 0.712-second click-to-ready transition with only 0.291 seconds of
  server work and a 1.3ms Upload render; the visible defect is Streamlit's
  incremental client DOM patch while the old Profile marker is still present.
  The current revision reuses the Cloudflare startup mask only for this
  transition, reveals the iframe on the correlated Upload `app-ready`, and has
  a five-second fail-open timeout. Status: accepted production checkpoint at
  `4738cb3`; the user confirmed no intermediate screen in either direction
  between Profile and Upload.

- 3.1.10 Company Profile navigation and Overhead Expenses copy: restore the
  accepted v3.0.57 full-width tab rail on the current stateful, lazy-rendered
  tabs without reverting the v3.1.8 performance improvement. Use Overhead
  Expenses consistently in the table heading, save action, success message,
  and save errors. Remove the current React Aria selection underline, emphasize
  only the active tab, and remove the zero-height save bridge from document
  flow, including its outer Streamlit element wrapper, so Overhead Expenses
  starts at the same height as Contacts. Rename Price List to Price Lists.
  Preserve the working expense persistence path and defer Sign out sizing,
  Save Contacts, and Save Company Details. Status: production work-in-progress
  at `9ab5814`. The rail, active-tab bold treatment, plural `Price Lists`,
  Overhead Expenses copy, working Save, and removal of the red React Aria
  indicator are visually confirmed. A small residual vertical offset remains
  between the Overhead Expenses card and the other tab contents. Do not add a
  guessed negative margin. The accepted rollback boundary is `b58b1f5`, restored
  without history rewriting at `6a403b0`. Production telemetry then confirmed
  that the remaining whole-page jump is not scrolling or tab CSS: the transient
  zero-height `scroll_parent_to_top()` component occupies one 16px root layout
  gap on the first Profile render and disappears on the tab rerun. The current
  revision moves that utility component into the hidden Sidebar while preserving
  its scroll-reset behavior. The remaining Expenses-only offset was addressed by
  limiting `@st.fragment` to the save bridge instead of wrapping the complete
  tab. Profile to Upload navigation now changes screen state in a pre-render
  callback, preventing a partial Profile delta before the Upload rerun. Status:
  accepted production checkpoint at `3f8c80a`; the user confirmed the page no
  longer jumps, the Expenses alignment is correct, and Save remains functional.

- 3.1.9 Auth transition integrity: execute Sign in and every Sign out through
  native Streamlit callbacks before the next script render. Remove the
  intermediate Login/Profile render that can expose a broken screen or two
  logos. Preserve the current cookie, sessionStorage fallback, telemetry,
  native click behavior, and accepted layout. Status: functional production
  acceptance at `8182c51`. Clean Sign out measured 0.75-1.22 seconds and clean
  Sign in measured 1.29 seconds, with no broken screen observed. A telemetry
  follow-up closes failed Sign in transitions so later successful timings do
  not inherit stale correlation IDs.

- 3.1.8 Profile latency optimization: preserve the accepted six-tab geometry
  and working Save Expenses path, but render only the selected tab. Reuse the
  company access already verified in the current Python run and load the
  company profile row only for Contacts or Company Details. Status: accepted
  production checkpoint at `4c6d628`. Repeated Upload to Profile improved from
  3.36 seconds to 1.06-1.12 seconds, with server time reduced from 2.36 seconds
  to 0.29-0.30 seconds. The first cold transition improved from 4.23 seconds
  to 2.66 seconds.

- 3.1.7 Internal transition telemetry: measure Sign in, Upload to Profile,
  Profile to Upload, and Sign out from the browser click to the next rendered
  screen. Correlate each result with auth network time, company access lookup,
  Profile load, screen render, and Python reruns. The browser observer is
  passive and bubble-phase only. It must never cancel, delay, disable, or
  replace a native Streamlit click. Status: production measurements complete.

- 3.1.6 Streamlit runtime regression test: production was observed on unpinned
  Streamlit 1.64.0 while the verified local environment uses 1.58.0. Pin 1.58.0,
  rebuild production, and compare the same deep iframe startup boundaries. If
  startup does not improve or protected behavior regresses, revert the pin.
  Status: rejected. The first 1.58.0 Login took 7.06 seconds, followed by four
  iframe-only traces that never reached the auth component and timed out after
  8.26-8.39 seconds. Production is pinned back to 1.64.0 to prevent drift.

- 3.1.5 Deep iframe startup telemetry: split the embedded Streamlit startup
  gap into component script, component render, browser storage read, callback,
  and final app-ready boundaries. Record production Python, Streamlit, and
  Supabase versions before deciding whether to pin currently floating runtime
  dependencies. Status: implementation ready for production verification.

## Working rule
- A broken core layer must be repaired and validated at its actual integration point. Disabling or bypassing it is not an acceptable primary fix; fallback behavior is only an additional production safety mechanism.
- Every new two-file benchmark cycle starts two fresh instances on separate unused ports and opens both Chrome tabs automatically so `page-23.pdf` and `Металл (1).pdf` can run in parallel under the same code version. Keep older benchmark servers and result screens available for side-by-side comparison; stop them only on explicit request or when resource/port conflicts require cleanup.

## Active
- 3.1.2 Pilot Fast Resume: remove the initial browser-session rerun with a
  30-minute encrypted partitioned resume cookie, retain sessionStorage as the
  compatibility fallback, and keep Supabase as the authority for user and
  company access. Ship disabled first, then verify production enablement,
  fallback, expiry, tamper rejection, and two Sign out / Sign in cycles.
- 3.1.1 Production Observability Foundation: persist correlated browser and
  server timing boundaries without blocking render, changing UI geometry, or
  recording credentials, PII, file names, or RFQ content. Apply the Supabase
  migration and Cloudflare Function secrets before production verification.
- Company Profile follow-up after the v3.0.59 Save Expenses checkpoint:
  diagnose the duplicate heading observed after Sign out, then verify Contacts
  and Company Details remain on their selected tab after Save. Recheck the full
  sign-in, upload, profile, save, logout, sign-in, and reload cycle before
  declaring the checkpoint stable. The Other Spendings migration is applied.
  Do not change the accepted table geometry or the working Expenses save path.
- 3.2.1 Labor Costs: replace the placeholder with an owner-only employee cost
  register. The first production candidate uses one informal `Worker name`
  field, managed Department and Position lists, Monthly Salary or Hourly Rate,
  Average Hours per Month for hourly workers, and a derived Monthly Bruto total. The
  personnel records live in `company_employees`, separately from the Estimation
  `labor` catalog. Net salary, tax, pension, National Insurance, and total
  employer burden remain deliberately out of scope until their calculation
  contract is defined. The initial production version at `b6a3cd8` is an accepted
  rollback point. The current revision moves saved workers above the form, uses
  the Overhead Expenses typography, uses three-column role and hourly rows,
  removes numeric steppers, resets every field after Add, and opens owner-only
  editing from a small pencil beside the worker name. The rejected native-grid
  rewrite was reverted. The pencil is now before the name so edit controls form
  one vertical column. The selector fix targets Streamlit 1.64 React Aria groups,
  inputs, buttons, and option states while retaining the older BaseWeb rules.
  Status: accepted production checkpoint at `1df98c5`; the user confirmed the
  pencil alignment, vertically centered selector text, and purple focus states.
  The current minor candidate removes the extra Add Worker card top margin and
  limits bold disabled styling to calculated text inputs so the disabled
  `Select position` placeholder stays regular weight. Status: accepted
  production checkpoint at `dfcf5ef`; the user confirmed the final spacing and
  selector presentation.
- 3.2.2 Users invitation link: replace the loose heading and code block with the
  existing Users table-card design, keep the owner-only link clickable, and use
  the same compact 12px inter-section gap as Labor Costs. Status: visually
  accepted and pushed at `dff220c`; 186 tests passed.
- 3.2.3 Compact Profile header: remove accumulated Streamlit gaps above the
  visible header, equalize the page-to-title and title-to-tabs spacing at 34px,
  use actual 36px Profile action buttons, align their visual axis with the logo,
  and expose Projects as a disabled placeholder pending its route and data
  contract. Status: visually accepted and pushed at `1f30416`; 186 tests passed.
- 3.2.4 Profile transition compatibility: keep the accepted v3.2.3 action
  alignment and bind the existing Profile-to-Upload transition curtain to the
  stable `profile_to_upload` key instead of visible copy. Status: accepted in
  production as part of v3.2.5.
- 3.2.5 Profile navigation priority: rename the file-workspace action to
  `New Estimate`, keep `Projects` first and `Sign out` last, and prioritize the
  profile tabs as Overhead Expenses, Labor Costs, Price Lists, Contacts,
  Company Details, and Users. Remove the manually maintained build-version
  secret override and enforce matching Streamlit/Cloudflare versions in tests.
  Status: accepted in production at `b372d3d`; 187 tests passed.
- 3.3.1 Authenticated home composition: preserve the accepted Upload logo size
  and position exactly, reduce the three-line product credo, place compact
  Projects, Profile, and Sign out controls between the credo and native upload
  card, and keep Projects visibly disabled until its route exists. Status:
  accepted in production at `cf35d9b`; the full Sign out label is visible, the
  two lower gaps are code-defined at 32px, and 188 tests passed.
- 3.4.1 Company logo normalization: rename the Profile tab to Bank Details and
  add a separate owner-only Company Logo card below Save Contacts. Accept PNG,
  safe self-contained SVG, and first-page PDF sources, normalize them without AI to
  a private 1024px square PNG card, retain only its private Storage reference,
  and instrument conversion, upload, database update, cleanup, and load.
  Status: accepted production checkpoint at `2a6ac0f`; the supplied SVG was
  converted, previewed, saved, and persisted in production, and 203 tests
  passed. Separate PNG and PDF production checks remain pending.
- 3.4.2 Company Logo saved-state UI: hide the empty right-side preview frame,
  keep Drop or Upload available for replacements, align the two-column saved
  composition, use a full-width active Change Logo action backed by the native
  picker, apply the shared 32px Profile action gap, keep drag-over purple, and
  dismiss the success notice after five seconds. Status: accepted in production
  at `32497dc`; 204 tests passed. Closed.
- Profile success-message consistency: move success feedback above Save actions
  across the remaining Profile tabs and use a common dismissal rule without
  changing persistence handlers. Status: deferred to a future block; Company
  Logo already follows the intended placement.
- Auth UI follow-up: improve Sign out press/progress/completion feedback without changing the accepted Sidebar session component, adding JavaScript click interception, `pointer-events: none`, capture handlers, or focus-based infinite spinners. Preserve v3.0.51 refresh persistence and verify two consecutive Sign out / Sign in cycles.
- Unified Detection/OCR experiment sequence — quality first; every step must preserve the stable 3-object and 15-object boundaries before the next step begins:
  1. Make benchmark run IDs unique so repeated runs cannot overwrite prior object results. Direct PDF OCR remains the default one-PDF/one-request flow. Naming is text-only and receives locked Detection facts plus OCR snippets, never the PDF again.
  2. Validate the restored core Direct PDF OCR route on `mistral-ocr-4-0`. Structured vision annotation is excluded from the critical path because it changed a 2–3 second request into a 37–90+ second request. Record OCR completeness, p50/p95, dimensions, tokens, and total time.
  3. Continue the dimensions work already started. Bind every external dimension to the same object index, evidence page, and OCR region; never promote a component size to the whole-object envelope; when axes conflict, return unknown plus a concise clarification instead of guessing. Do not add another full-document pass.
  4. Make Naming text-only. Keep the separate Naming Agent and immutable object list, but stop sending it the PDF again. Pass indices, evidence pages, relevant OCR snippets, and locked Detection facts. Preserve current naming quality and target 2–3 seconds.
  5. Parallelize the first document stage. Start the single Direct PDF OCR request and visual-only commercial object locking at the same time. Join once both finish, then reconcile OCR evidence against the locked object IDs without a second full-document analysis.
  6. Parallelize the post-lock stage. After object IDs and order are immutable, start short Naming and technical OCR enrichment as parallel branches. Neither branch may add, remove, merge, split, or reorder objects.
  7. Completed in v3.0.35: File Review waits only for OCR, Detection, and the authoritative result save. Naming v4 now runs in the background, updates only unchanged provisional names, and no longer blocks the user; full OCR and runtime diagnostics also remain outside the critical path.
  8. Completed in v3.0.40: Processing uses measured Golden stage weights, an ease-in Detection curve, and OCR page-count pacing buckets; the early sprint and slow finish are removed without changing backend work.
  9. Run the acceptance benchmark. Use fresh files and at least three cold runs per file; compare object boundaries, names, dimensions, OCR completeness, p50/p95, tokens, cost, and total user-visible time.
  10. Prepare production concurrency later. Add organization-wide limits, backpressure queueing, 429 handling, and visual-only Detection fallback. Keep one PDF as one OCR request; do not restore per-page fan-out.
- Closed routing experiments:
  - Rendering pages while earlier pages entered OCR produced about 3.5 seconds of overlap on the 11-page file, but is superseded by Direct PDF because the main route no longer renders pages.
  - The 4-versus-6 page-worker experiment is retired. Future concurrency control applies across whole PDF requests from different users, not inside one document.
- Objects Estimation: manual sale price override should stay authoritative after self-cost changes, with manual label and SC-changed notice.
- Add overhead calculation layer after object material/labor pricing.
- Add deterministic delivery and installation pricing from project subtotal / overhead settings.
- Improve catalog matching: save matched material/labor rows and mark weak matches as `needs_review`.
- Run estimation for all detected objects, not only the first object.
- Design Objects Estimation status refresh without Streamlit stale-DOM fragments.
- UI copy: enforce the product rule that the final sentence in a user-facing
  text block has no trailing period. Preserve internal periods and meaningful
  question marks, exclamation marks, and other punctuation. Password recovery
  and shared Auth validation copy now follow this rule; the remaining product
  copy still needs an audit.
- Upload: continue first app/file-load optimization; warm refresh now uses the grey screen/app-ready path, but cold start after reboot can still show one Streamlit skeleton.
- Upload performance follow-up: lazy-load screens and cleanup are done; revisit `.streamlit/config.toml`, cold-start behavior, and optional post-deploy/reboot prewarm.
- Processing: review processing-screen text wording and keep its current position as the layout benchmark.
- Objects Estimation: reduce the large vertical gap between subtitle and pricing table column headers.
- Objects Estimation: add a small blue spinner next to the running Self Cost per Unit percent.
- Objects Estimation: format object quantities as whole units, not 1.0, after estimation completes.
- Objects Estimation: Delivery and Installation should not show Self Cost pending state or Pending review buttons; keep review/status area empty for project-level rows.
- Objects Estimation: keep Delivery and Installation as project-level percentage allocations and show their sale price inputs without fake object status.
- Object Detail: show AI Confidence when available.
- Object Detail: implement Object Preview image capture/display.
- Object Detail to Objects Estimation navigation: remove stale screen fragment flicker on return.
- Object Detail approve action: remove stale screen fragment flicker after clicking Approve.

## Later
- Large-PDF Detection routing: prevent Claude HTTP 413 before starting expensive work. Estimate the complete Messages payload size, including Base64 expansion, OCR context, prompt, and schema; never retry a non-retriable 413 through the fallback model. When the inline payload would approach the 32 MB Messages limit, upload the PDF once through the Anthropic Files API and pass its `file_id` instead of Base64. If the referenced document still exceeds the model context, split it into controlled page groups and reconcile one package-level object set. Persist OCR, upload, Detection, and failure timings for unsuccessful cycles.
- Audit and replace brittle layout code in Objects pricing rows and Upload dropzone when the current estimation/overhead flow is stable.
- Polish negative/error states with project button styles.
- Add XLS proposal export.
- Add missing-object second-pass detection flow.
- 3.7.1 Company Price Sources: retained historical agent/import work, with the
  source-first UI superseded by active task 3.10.1. Production candidate adds one-source upload or
  public-URL ingestion, optional department selection with automatic material-type classification, automatic supplier and
  document classification, unit-preserving normalization, private versioned
  offers, unresolved-row quarantine, source inspection, and private source
  storage. The owner applied the additive database migration before deployment;
  `233 passed` on the production candidate. Verify one photographed invoice and
  one static public supplier page on production. Existing `materials` and the
  current Estimation resolver remain unchanged until import evidence is accepted.
  First production URL test exposed output truncation on the 15k-character
  Rotenberg catalog page; the extraction budget was raised from 8,192 to 32,768
  tokens and explicit max-token failure handling was added. The same page then
  exposed a model arithmetic mismatch, so ready-row normalized prices are now
  calculated deterministically. The final no-write diagnostic completed in
  48.252 seconds with supplier `Rotenberg 1929`, document type `price_list`, and
  48 of 48 rows validated as ready. Production persistence still requires a
  user-visible retest after the hotfix deployment. A later production URL test
  failed before the agent: the page returned only 190 bytes and no readable HTML
  text. Script-only or protected pages now receive a specific instruction to
  upload a PDF, screenshot, or photo. A no-write automatic-category diagnostic
  on the Tsidky page inferred `Sheet Materials`, identified the supplier, and
  validated 39 of 42 rows as ready. Production still needs the exact failing URL
  to determine whether a safe dynamic-page importer is justified. Production
  user testing on checkpoint `4a5fd9a` confirmed that Sign Out no longer reveals
  an unstyled Auth screen and that two automatic-category URL imports completed
  in 22.9 and 9.5 seconds. Both persisted as `partial`, with zero ready prices:
  one returned 27 unresolved rows, the other 6 unresolved and 1 excluded row.
  Price ingestion therefore remains active work, not an accepted completion.
  The preceding session measured Upload to Profile at 3.65 seconds. Its Profile marker
  reached the DOM after 0.68 seconds and its server work was about 0.72 seconds;
  roughly 2.97 seconds were spent waiting for the late general `app-ready`
  component before the Cloudflare transition mask was removed. Checkpoint
  `a626462` reuses the verified styled-target event path for both Upload to
  Profile and Profile to Upload. It verifies screen-specific computed styles before
  revealing either target and leaves the general `app-ready` event unchanged for
  final server-run telemetry. Production trace
  `3ae650ed-7e9e-4b15-b333-3e4691e4c227` measured two Upload to Profile styled
  reveals at 704ms and two Profile to Upload styled reveals at 663ms and 895ms,
  each with one Python run. The user accepted the navigation speed. No further
  transition change is pending unless a new production regression is observed.
