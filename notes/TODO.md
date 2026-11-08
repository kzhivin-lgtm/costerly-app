# TODO

PENDING LIVE VERIFY, V6.57, P0, ordinary Discovery output envelope:

The 2026-10-27 HSL failure reached the existing 8,192-token Discovery ceiling
while emitting valid JSON fields, then stopped inside `page_coverage`. The
nearest successful HSL Discovery had the same route, 1,073 source facts,
37 Candidate Regions, 11 page images, 86,995 input tokens and 123,572
context characters, but returned 7,451 output tokens. This is an intermittent
response-expansion boundary, not evidence that Fusion, routing or page recall
changed. Owner approved a minimal repair: keep the same ordinary Discovery
contract, make its output ceiling deterministic from Candidate Region count,
and make its existing reasons/descriptions explicitly compact. Do not add a
general JSON retry, change models, routing, Fusion, Membership Review,
Evidence ownership or accepted object boundaries. Verify focused Discovery
schema, prompt and call-budget tests before deployment, then run the protected
HSL benchmark.

HSL budget witness passed on `run_99b433940dcc4fd9abbe0587dc56fb12`: one
ordinary Discovery call selected 12,288 tokens for 37 Candidate Regions and
used 7,464 without a retry or JSON failure. This confirms the capacity repair,
not lower cost, lower output volume or object-boundary quality. Preserve its
ledger in the V6.58 checkpoint and audit its nine-object evidence separately
before accepting any Detection-quality conclusion.

Do not infer that a Detection response failure is a progress-bar fault. Add a
safe request-content digest to future Discovery diagnostics before attributing
any remaining output variation to provider behaviour; never store raw document
content in the ledger.

CHECKPOINT, V6.58, P0, Processing progress root-cause:
The progress bar must have one visible bar, begin at zero, never reset or move
backward, advance continuously before Fusion, recalibrate only forward from
real stage signals, and reach File Review without a completed-bar grey delay.

V6.58 investigation: the server replaces the Processing stage subtree on each
stage signal. Its newly-created fill starts at the server floor, while the
browser controller restores its higher in-memory value on the following tick.
That produces a visible backward flash. A legacy upload-shell controller can
also survive a Streamlit deployment in the parent browser document and remove
the persistent shell when the server marker appears. The approved repair is a
one-time V6.58 browser-runtime reset, one persistent client-visible shell for
the whole lap, and server markup used only as stage and forecast data. The
server may move the floor forward, never backward. Before Fusion, movement is
zero-origin and page-shaped without a hard cap. Keep Detection, provider calls,
router, Fusion, Evidence and File Review data unchanged. Verify focused tests,
then require a live HSL interaction check before accepting the UI result.

ACTIVE, V6.59, P0, File Review handoff visual isolation:
The V6.58 owner-run HSL interaction accepted Processing pacing but showed one
brief frame where the outgoing upload shell and incoming File Review screen
were composited together. Trace the transition shell's removal and the File
Review styled-ready signal. Repair only that handoff, without changing the
accepted V6.58 progress controller, forecast, Detection cycle, File Review
data readiness, routes or provider calls. Acceptance: no overlap and no blank
or grey delay between a completed bar and the fully rendered File Review.

Diagnosis update, 2026-10-27: the persistent Processing runtime already has
`reportFileReviewStyled()`, but nothing calls it when the terminal Processing
stage is rendered. The mutation observer therefore removes the shell as soon
as it sees the raw File Review marker, before the card and navigation controls
have painted. V6.59 must arm `processing_to_file_review` from the explicit
`data-processing-complete` stage and release only after the existing styled
predicate, with two animation frames. It also starts the existing process-wide
Mistral HTTP warm-up while an authenticated user is still on File Review,
Objects, Account, Projects, or Admin. This warm-up is non-blocking and does
not change Detection or Upload rendering correctness.

Regression found immediately after deployment: the temporary V6.58 browser
runtime migration forced `parentWindow.location.reload()` on first Upload.
Its production timeline produced an 8-second grey fallback and duplicate auth
reruns before Upload became usable. This is a client-shell failure, not a
Detection delay. Remove the forced reload entirely. Existing runtimes may
upgrade only on an ordinary browser refresh or a new tab, never as a result of
New Estimate or file selection.

Diagnosis update, 2026-10-28: the one-page `Стеишен и поддон.pdf` run reached
Detection completion in 21.514 s, but the client kept a hard `1.15%/s` cap
after Fusion. The bar could therefore show only about 25-30% when the real
result was ready. The terminal transition then released after a stale generic
File Review DOM predicate, leaving a measured 3.434 s handoff. V6.60 must
retain forecast pacing plus real stage floors, remove the false cap, use a
bounded finishing segment under the shell, and release only after the target
File Review marker carries the exact completed `run_id`. The header's `Last
Estimate` route must use the latest succeeded `rfq_processing_cycle`, not
`rfq_estimates`, because a File Review exists before Continue creates an
estimate shell. Preserve Detection, OCR, route selection, Fusion, objects and
Evidence unchanged. Live acceptance: a short one-page run reaches 100% before
the matching File Review appears, with no blank frame or backward movement;
`New Estimate → Last Estimate` reopens that most recently completed Detection
run.

ACTIVE, V6.61, P0, short-file pacing and immediate Last Estimate:
The V6.60 cap removal was necessary but insufficient. Its cold stage model
still budgeted a one-page file as roughly 40 seconds, and forecast pace could
cross unfinished stage ranges. The result was an initially slow bar followed
by a large final catch-up. V6.61 keeps all Detection work unchanged, lowers
only transparent cold-start work-unit timings, and combines continuous forecast
pace with exact stage floors and per-stage ceilings. Before Fusion, page count
sets a faster zero-origin preparation curve for a one-page file. Each actual
stage signal may move progress forward, never backward; its unfinished range
limits the forecast so later work cannot be displayed early. Preserve the
latest completed File Review payload in the browser-session cache across
`New Estimate`, and update the header route immediately when that run completes.
Acceptance: a short ordinary file makes steady progress into the 85-90% range
before its terminal handoff, does not jump from a low percentage to completion,
and `Last Estimate` returns the same completed review from cache without a
multi-second grey load. Detection, OCR, Fusion, router, objects, Evidence,
Naming, Preview and provider calls are protected.

CHECKPOINT, V6.67, P0, mandatory post-Discovery same-page full-criteria comparison:
Base: owner-accepted V6.63, with all subsequent V6.64-V6.66 Fusion, bbox,
halo, scoring, routing and classification experiments excluded. After Discovery
has fixed retained `object_evidence` Islands, build the exact unordered pair
set independently for each page and require Membership Review to inspect every
pair against identifier, topology, geometry, dimensions and construction. The
new queue is comparison-only, not merge evidence, and never creates cross-page
all-to-all work. Preserve V6.63's Dimension scoring, Candidate Q cross-page
behaviour, Mistral anchors, routers, File Review, Naming and quantity policy.
Acceptance met for the pairing mechanism: the review handoff and audit prove
an exhaustive pair set for each page's retained Object Evidence inventory; every
queue pair is subject to the five-criterion review contract; no document-context
or discarded floor-plan group enters the queue. Floor 06 live verification
returned 15 packages from 49 retained final Views and 125 required same-page
pairs. This checkpoint protects the queue only. It is not final Floor 06
quality acceptance because P09/P10/P11/P14 exposed the separate false
`floor_plan` exclusion defect, recorded as V6.68 below.

INVALID EXPERIMENT, V6.68, P0, floor-plan classification gate:
The downstream soft gate was coupled with a Discovery prompt rewrite. On the
Floor 06 live run, the model returned a materially weaker semantic evidence
set and the deterministic merge gate produced 39 packages instead of the V6.67
run's 15. Do not use V6.68 as a checkpoint or as the base for further work.

ACTIVE, V6.69, P0, isolated floor-plan soft gate:
Base: exact V6.67 Discovery prompt and same-page Review checkpoint. Apply only
the deterministic downstream soft gate: retain a technical Island classified
as `object_evidence` even when its neutral `representation_kind` is
`floor_plan`; discard only confirmed `document_context`. Keep V6.67's prompt,
same-page queue, Candidate Q cross-page selection, Dimension scoring, router,
Naming, quantity and preview policy byte-for-byte unchanged. Acceptance: a
genuine whole-level plan remains `document_context`, technical object views
mislabelled `floor_plan` survive, and Floor 06 retains V6.67-grade merge
behaviour rather than reproducing V6.68's split into 39 packages.

ACTIVE EXPERIMENT, V6.73, P0, page-scale guard for forced floor-plan demotion:
Base: V6.72 rollback, which restores the V6.69 code path. No Discovery prompt,
Fusion recall, BBox, Halo, candidate queue, Dimension score, router, Naming or
merge-contract change. Keep the existing plan-like semantic cue, but force an
`object_evidence` Island to `document_context` only when it is the sole raw
Island on that page or its physical `core_bbox` covers at least 75 percent of
the measured Fusion page frame. The wider evidence envelope is explicitly not
used for this test. Acceptance: a whole-page architectural layout is still
discarded; a bounded object plan on a multi-Island page remains Object Evidence;
Floor 06 live run changes only this classification outcome, not recall or Q.

ACTIVE BASELINE, V8.4, P0, exact protected V7.14 runtime:
Base: protected `detection-v7.14-conflict-membership-2026-10-30` (`39eb723`).
No functional Detection change: Discovery, Candidate Regions, Conflict Resolver,
Membership, render handling, dimension ownership, router, Naming and UI remain
byte-for-byte V7.14. Only the persisted telemetry label is
`detection_v8_4_exact_v7_14_baseline`, so the next run is auditable as V8.4.
Acceptance: same V7.14 behavior, including its known one extra floor-plan
package if it occurs; no V8.x floor-plan exclusion experiment is active.

COMPLETED, V8.4.1, P0, Page 23 presentation and terminal Processing error:
Base: V8.4 exact V7.14 Detection runtime. Scope is deliberately outside
Discovery, Candidate Regions, Conflict Resolver, Membership, router and object
assembly. First, source-degraded native-graphic Registry output receives a
one-use, post-Registry bbox transport only while materializing File Review
previews, so Page 23's locked three objects can produce them. The original
route payload remains unchanged for Naming.
Second, a failed processing worker marks the current stage as terminal, stops
the client timer and reveals the recoverable File Review error instead of
leaving a stale progress shell. Acceptance: Page 23 retains exactly three
objects and exposes presentation bboxes, while a forced Detection validation
failure visibly stops Processing and presents its actual error.

ACTIVE, V8.4.2, P0, bounded Cabinet render-decision normalization:
Base: V8.4.1 (`59177dc`). The V7.11 adapter remains strict for actual
`presentation_render` Views: every actual render still requires exactly one
valid decision, and unknown IDs, duplicate rows, attachments from a non-render,
unresolved non-render rows, malformed rows, and incomplete render coverage still
fail. Only a known Object Evidence View that is not a `presentation_render` may
be ignored when the model emits a semantically inert `no_match` row with no
technical target and evidence type `none`; that ignored row stays in the audit.
No prompt, Discovery, Candidate Region, Conflict Resolver, router, Membership,
object assembly, Naming, UI or Page 23 logic changes. Acceptance: the Cabinet
run reaches Registry and preserves its historical one-object P1-P6 package,
while the audit records the ignored material-sample row.

COMPLETED AND OWNER-VERIFIED, V8.4.5, P0, global batched assembly scope:
`4c9ff38` restores the pre-existing V6.11 document-scope observation only
after V6.41 has merged every Discovery batch into one fixed Object Evidence
inventory. It runs only for a non-anchor `assembly_set` with active V6.41
batching, sends only fixed Object Evidence crops and bounded local facts, and
returns only the established scope schema. Existing V6.11 validation and the
existing V6.26 compiler remain the sole authority for document-wide
compilation. Candidate Regions, Discovery Islands, classifications, Conflict
Resolver, Membership, render decisions, dimensions, router, Naming, previews
and UI are unchanged. Missing crops, provider failure, invalid JSON or an
unknown Island fail closed to the prior ordinary scope without stopping the
cycle. Targeted Detection suite: 153 passed. The owner reran
`24-215. Кухня. СБ.pdf` and confirmed one final commercial object. Protected
tag: `detection-v8.4.5-global-batched-assembly-scope-production-2026-11-01`.
Before widening Estimation behaviour, audit that successful run's persisted
single object, `estimation_input_v4`, OCR event and private source-page
artifacts read-only. Full record:
`notes/DETECTION_V8_4_5_GLOBAL_BATCHED_ASSEMBLY_SCOPE_CHECKPOINT_2026_11_01.md`.

PENDING, P0, USER INCIDENT, Lev 2 candidate-exception contract failure,
2026-11-05 (Detection repair not yet approved/numbered):
Owner requested rollback to a protected Detection checkpoint or diagnosis.
[verified] Company 610 event a937a9fd-e729-41da-a5e7-b1bc683b0324,
2026-11-05T09:30:34.501402Z, Lev 2.pdf, failed visual_registry validation.
Discovery returned four groups and accepted CR-P001-001 through CR-P001-004,
but candidate_region_exceptions used OCR source ID SF00001 for footer text.
The validator requires an actual candidate-region ID, so it rejected this row.
Saved-response replay reproduced the exact exception without a model call;
removing that row in memory only made this narrow audit pass, with all four
candidates covered. This is diagnostic isolation, NOT an accepted repair or
end-to-end Detection result. Membership had already consumed a provider call
before the malformed exception was rejected.
[verified] Remote main remains e608f37; protected V8.4.5 tag resolves to
4c9ff38. Registry adapter, detector, schemas and Detection prompts on main
match that checkpoint. Rolling these back would not change the failing rule.
No code rollback, production write or deployment performed; unrelated local
TODO edits retained. Estimation V6.2 remains unpublished.
AGENT PROPOSAL, pending owner approval: bind exception IDs to supplied CR IDs
in the request contract and validate them before Membership, preserving strict
coverage/ownership checks. Do not silently discard unknown references. Verify
saved failure, malformed/duplicate IDs, then a real Lev 2 cycle and protected
Detection regressions before release. Number the repair only after checking
the authoritative Detection work block; do not renumber Estimation 3.17.4.5.
Owner requested causal analysis before any repair. Follow-up read-only audit:
[verified] The exception validator dates to 57086a8 (2026-10-21), not recent
UI/Estimation work. The provider schema accepts any string in candidate_region_id;
runtime later requires membership in the supplied CR inventory. The request
contains both SF text facts and CR regions. For this run all four CR anchors
were accepted, but the model additionally used an SF ID as a rejected region.
Anchor admission checks required decisions/rejections but did not reject this
extra exception; strict exception validation ran only after Membership.
[verified] Company 610 persisted history contains one exact matching error.
The returned Lev history (limit 50, spanning Oct 26-Nov 5) has successful Lev_1
responses with empty exception lists; only one exact Lev 2.pdf event was found,
the failure. Prior successful production Lev 2 execution is not established.
[likely] This exposed a pre-existing reference-type/contract-boundary weakness,
not a new UI regression. Precise model motivation remains unknown. The model
called SF00001 footer text, but the failed run has no persisted OCR event or
complete source-fact inventory here, so that source reading is not independently
verified. Do not infer that absence of earlier failures proves robustness.
Earlier enum/early-validation remedy remains a proposal, not an approved fix;
early validation alone saves wasted Membership work but cannot prevent the
invalid response. No runtime edits or additional model calls in this audit.

BENCHMARK, P0, Hasolelim Floor 06 manual Object Evidence island inventory:

This is the owner-provided visual inventory, separate from final package count
and Naming. P01 title block and P02 whole-level floor plan are document context,
not benchmark Object Evidence islands. P13's additional photograph is reference
context, not a seventh Object Evidence island.

| Page | Expected Object Evidence islands |
| --- | ---: |
| P03 | 11 |
| P04 | 4 |
| P05 | 6 |
| P06 | 3 |
| P07 | 8 |
| P08 | 3 |
| P09 | 6 |
| P10 | 3 |
| P11 | 4 |
| P12 | 3 |
| P13 | 6 |
| P14 | 3 |
| P15 | 3 |

V6.73 live audit (`run_ffe9eae79b15430698d9bae23dad76da`): P03=11,
P04=4, P05=6, P06=3, P07=6, P08=3, P09=3, P10=1, P11=2, P12=3,
P13=6, P14=3, P15=3. Mismatches are P03, P07, P09, P10 and P11.
Do not treat matching 15-package output as evidence that this island benchmark
has passed.

ACTIVE, P0, Floor 06 Candidate Region source-union repair:

The V6.73 Floor 06 audit proves a source-recall defect before Discovery, not a
floor-plan classification or Membership error. On P10, MyPDF extracted 99 text
spans and 14,252 vector primitives, but `vector_cluster_recall` was skipped at
the 9,284-path limit. Mistral emitted only two near-identical graphic blocks,
which Candidate Regions treated as one covered region. Discovery consequently
received one Candidate Region (`CR-P010-001`) and emitted one Object Evidence
Island, `v641-b02-004`. It did not discard two Islands as `object_plan` or
`document_context`: the sole Island remained `object_evidence` despite its
`floor_plan` representation label.

The root contract gap is that Candidate Regions currently creates MyPDF
text/dimension clusters only when Mistral has no graphic region anywhere on the
page. A Mistral graphic block therefore suppresses distinct MyPDF evidence on
the same page even when it leaves that evidence uncovered. The next experiment
must preserve the V6.73 checkpoint and change only recall: form bounded MyPDF
candidates from native-PDF source facts whose centres lie outside every Mistral
graphic candidate. V7 implementation `d1f0b60` initially admitted four P10
MyPDF clusters, including the revision table and title block. The correction
`67624fc` requires two substantial native dimension literals, so its P10 local
audit yields exactly one Mistral region plus the two lower object-view clusters.
V7.1 is rejected despite that local count: it promoted every supplemental
MyPDF region into a pre-Discovery `object_evidence` proxy, Dimension Fingerprint
and Candidate Q, and caused an observed 50-60 object explosion. V7.2 `4050111`
retains the same three P10 Discovery candidates but assigns the two MyPDF
regions `coverage_only`: Discovery must inspect/account for them, while only
ordinary candidates seed pre-Discovery dimensions, Q, Membership and packages.
V7.3 `20c1e31` is rejected and reverted by `b2bce47`: it added a required
`coverage_region_decisions` schema field to the first Discovery request. Live
Floor 06 trace reached `Discovery batch 1 of 2` in 16.5 seconds and emitted no
later stage, whereas the V7.2 control reached batch 2 in about 45 seconds. The
only changed request surface was the V7.3 structured coverage contract. Do not
repeat that schema or force a second required response array into Discovery.
Any next Coverage Acceptance experiment must retain the ordinary Discovery
schema and measure a conditional post-Discovery correction separately.
V7.3's later `21d8d8a` retry of the complete batch for an unresolved
`coverage_only` candidate is superseded: it repeats the same Discovery
structure, adds a second full-page request, and still skips any target that
has a first-pass exception. Do not restore it.

ACTIVE EXPERIMENT, V7.5, P0, independent visual conflict resolver:

Base: `21d8d8a` with the ineffective V7.3 full-batch coverage retry removed.
After ordinary Discovery has completed, build a bounded target only for a
Candidate Region with no overlapping retained `object_evidence` Island: either
a `coverage_only` MyPDF region or an original Mistral graphic region. This is
source-conflict routing, not a second page inventory. The resolver receives
only a neutral raster crop, a small page-orientation image and a local crop
pixel coordinate frame. It receives no Candidate Region role, source facts,
OCR text, prior Discovery classification, exception or object hypothesis.
The runtime alone translates its local geometry into Fusion coordinates.

The resolver may emit exactly one of `admit_object_evidence`,
`document_context`, or `unresolved` for each target. Only a visually observed,
non-proxy bbox overlapping the target is added to the ordinary Discovery
ledger. It cannot create graph seeds, Candidate Q, Membership decisions,
packages, quantities or source facts. It runs only when targets exist, has a
12-target maximum per request, and fails open to the ordinary Discovery result
with an audit if its request, JSON or geometry is unavailable. The ordinary
Discovery schema and normal no-conflict path remain unchanged.

Acceptance: Floor 06 P10 starts from its existing three candidates and one
graph seed, then admits only independently visible lower Islands. The same
trace must show resolver targets and decisions for every covered source
conflict, no V7.3 full-batch retry, no candidate-box geometry, and no
50-60-object explosion. This experiment is designed to address observable
source conflicts on P07/P09/P10/P11. It does not claim to discover P03's
fully silent omission; that remains a separate recall problem. Compare the
full 64-island page inventory, final packages, provider tokens, cost and stage
durations with V7.2 before accepting it.

The local P10 contract is 3 Discovery candidates and 1 graph seed; the V7.5
source-conflict and Candidate Region suite passes 22 focused tests. It remains
active until the complete Floor 06 benchmark establishes that the bounded candidates improve recall
without duplicate regions or object explosion. Do not
reintroduce V6.70's unbounded source union, broad Halo, candidate-box authority,
or any changes to Discovery, floor-plan classification, Q, dimensions, merge,
router, Naming, UI, or model choice. Acceptance starts with P10 producing
three candidate regions before Discovery, while the Floor 06 benchmark pages
with already-correct counts do not gain duplicate candidates.

ACTIVE EXPERIMENT, V7.10, P0, isolated Conflict Resolver results:

Base: published V7.8 rollback `c771806`. V7.9 `37d6642` is rejected: its
direct presentation-render instruction changed the entire ordinary Discovery
response and produced 23 packages in Floor 06. V7.10 leaves the Discovery
prompt, Candidate Regions, geometry, Q, dimensions, technical merge rules,
router, Naming and UI unchanged.

Repair only the bounded V7.5 fallback. Validate each returned target decision
independently, preserve valid decisions when a neighbouring row is malformed,
and retry only invalid targets once. A fallback render/photo is explicitly
labelled `presentation_render`; it remains subject to V7.8's no-render-only
object partition. An admitted `floor_plan` or `location_plan` becomes
`generic_plan` document context only when its supplied region or independently
observed core covers at least 75 percent of the Fusion page, so a bounded
object plan stays admissible.

Acceptance: no invalid V7.5 row erases another valid verdict. Floor 06 keeps
P02 as document context, restores only independently admitted source-conflict
islands, has P03=11, and creates no render-only or broad package increase.
Compare page inventory, package composition, provider tokens, cost and duration
against V7.8 before accepting.

ACTIVE EXPERIMENT, V7.8, P0, presentation render/photo membership:

Base: published V7.7 rollback `76e96fb`, with protected V7.6 dimension-bbox
checkpoint `5c01195`. Define the existing Object Evidence
`representation_kind` `presentation_render` for a photographic render or
photo, never a technical perspective. It may join a technical View only on one
concrete, pair-local `matching_topology` or `unique_geometry` fact that cites
both fixed Views. Colour, finish, material, room context, proximity and pixel
proportions are not identity evidence. A component made only of presentation
renders/photos is retained in audit but excluded from the final object registry;
it cannot create a standalone commercial object. No Candidate Regions, Conflict
Resolver, Discovery geometry, Q, dimensions, ordinary technical merge rules,
router, Naming or UI behaviour may change.

Acceptance: a focused P03 audit labels the presentation images with the exact
kind, connects their demonstrated triangular-shelving topology to the relevant
technical component when the visible evidence supports it, and creates no
render-only object. First pass: focused code tests covering single-fact visual
admission and orphan-render exclusion. Then run Floor 06 and compare island
inventory, page-by-page package composition, total packages, provider tokens,
cost and duration against V7.6. Reject the experiment on any broad package
increase or a missed technical component caused by the new rule.

COMPLETED EXPERIMENT, V7.13, bounded existing Membership Review:

Commit `cb84daa` restored V7.11's membership contract after the rejected V7.12
full-Q response and limited the existing initial and retry Review streams to 90
seconds. Floor 06 run `run_34f77878a83d475f85abdc4ff9ec9818` completed in 84.4
seconds with a 35.4-second Review. It reproduced V7.11's 16 objects, including
the unresolved three P10 packages. It is a stability guard, not an accepted
Detection-quality checkpoint.

ACTIVE EXPERIMENT, V7.14, P0, targeted conflict-admission membership:

Base: V7.13 commit `cb84daa`, with protected V7.11 checkpoint `0f4ecb6`
(`detection-v7.11-render-membership-2026-10-30`). The P10 failure is now
located: V7.5 independently admits its two missed technical regions as Object
Evidence and they enter the existing 157-pair same-page Q, but the ordinary
Review omits their positive membership evidence. Do not restore V7.12's full
Q disposition string, add another provider call, change Conflict Resolver,
Candidate Regions, Discovery, dimensions, general technical merge criteria,
floor-plan policy, router, Naming or UI. In the same existing Membership Review,
require one V6.8-style, evidence-backed decision only for every pair of
same-page technical V7.5 admissions. Presentation renders retain V7.11's
dedicated path and floor plans remain outside this matrix. Positive decisions
need two independent existing evidence types; negative decisions carry none.

Acceptance: Floor 06's P10 V2-to-V3 pair receives exactly one audited decision.
If its visual proof is positive and validates through the existing semantic
ledger, the two admitted technical views merge into one package without merging
the floor plan. The complete Review must return or fail visibly within 90
seconds. Compare island inventory, P03/P04 render attachment, other page
packages, tokens, cost and duration with V7.13. Reject on a broad package
increase, a non-P10 technical regression, or a Review response that omits the
targeted row.

DEFERRED, P2, Anthropic prompt-cache experiment after Detection contract stabilizes:
Do not enable cache_control while Discovery, Review prompts, models, or Evidence
contracts are still changing. The current V5 Registry route records zero cache
creation and cache-read tokens. When Detection has a stable accepted checkpoint,
run one isolated experiment that preserves model behaviour: create an explicit
5-minute cache breakpoint after an identical immutable source-page prefix shared
by Discovery and Membership Review, then keep stage-specific instructions,
Fusion handoff and crops after that prefix. Measure cache_creation_input_tokens,
cache_read_input_tokens, provider latency, output quality and actual TCC on HSL
and Morbergs. Update the cost ledger before enabling it, because current TCC
calculation does not price cache writes and reads separately. Do not treat the
Anthropic email's 48% account-level estimate as a product forecast. The first
write costs more, and cache is useful only for an identical prefix reused within
its TTL, especially Discovery to Review and a same-context retry.

CHECKPOINT, V6.63, P0, retained File Review integrity and explicit caption quantity:
The accepted V6.62 Progress controller and File Review handoff remain protected.
The `New Estimate -> Last Estimate` cache preserved an early review payload but
discarded its deferred Naming state while leaving Streamlit's old empty input
values alive. A return could therefore submit a stale blank value against the
durably saved name, show a name-conflict error, and later present blank cards.
Restore the retained cache by clearing only its object-name widget state and
hydrating the one durable Naming publication before constructing object edits.
The `Стейшен и поддон.pdf` run also proved that `04 / ПОДДОН 5 ШТ` sits just
above the mesh View, outside its normal envelope. Preserve the existing
caption-bound quantity policy, but admit an explicit quantity only from a
unique bounded top caption halo. Acceptance: restored names remain canonical
through repeated New Estimate and Last Estimate navigation, and the printed
PODDON quantity publishes as five without assigning nearby dimensions or
another object's caption.

Owner acceptance, 2026-10-28: deployed from `main` at `e97933f`. A live rerun
returned the printed PODDON quantity as five. Repeated `New Estimate -> Last
Estimate` navigation retained names and did not recreate the name-conflict
banner. Focused verification remains `78 passed, 1 deselected` (the deselected
case is the pre-existing static source-order test). Protected checkpoint:
`notes/DETECTION_V6_63_FILE_REVIEW_RESTORE_QUANTITY_CHECKPOINT_2026_10_28.md`.

ACTIVE, V6.62, P0, versioned browser progress controller:
Live V6.61 evidence invalidates further coefficient-only tuning. The deployed
page retained V6.59's closure, including its 1.15%-per-second limiter: a
26-second one-page cycle therefore displayed about 30% progress despite newer
server code. The same trace shows `Last Estimate` can reach a generic client
transition timeout with `python_runs=0`, so a server-session cache cannot be
the first fix. Replace the progress runtime with a versioned controller that
can dispose its observers and timers. Migrate the one non-disposable V6.59
runtime through exactly one idle Upload/File Review reload, never during an
upload or Processing. The controller owns one monotonic bar, recalibrates its
remaining forecast only forward from observed completed-stage duration, and
keeps explicit File Review handoff time in the plan. Remove `Last Estimate`
from the generic outer transition overlay so its native Streamlit callback and
the retained File Review cache can operate directly. Require production
evidence of the controller version, stage-plan receipt, stage transitions,
cache hit and exactly one Python callback before accepting.

IMPLEMENTED locally, pending production upload witness, V6.62 upload callback
ordering repair, 2026-11-03:
[verified] The production trace `1acb8b63-3c60-4c7b-91d0-ebd6e498a770`
recorded `browser.rfq_upload_selected` from `drop`, followed by
`browser.transition_click` for `upload_to_processing` and a 15.3-second
timeout with `python_runs=0`. There was no `server.rfq_upload_accepted`, no
`server.rfq_processing_queued`, and no Detection usage event, so the document
never entered Detection. The repair keeps the first file-selection visual
acknowledgement local and non-intercepting. It starts the outer
`upload_to_processing` transition only when the real server Processing marker
appears. If that marker never arrives, the local shell is removed after 18
seconds, the native uploader remains available for retry, and
`browser.upload_callback_timeout` is persisted. Local verification: five
targeted controller, upload-boundary, and runtime-event tests passed, plus
`py_compile` and `git diff --check`. Pending acceptance: one authenticated
drag-and-drop upload must emit exactly one server upload acceptance and one
real Processing transition, with no callback-timeout event.

IMPLEMENTED locally, pending production witness, Estimation V5.3 2VN geometry
and front topology, 2026-11-03:
[verified] Lev 1 V5.1 run `run_b1752d1c73cc4f64be117984d98eb74e` classified
the tall fixed screen as six `hinged_facade` fronts, which produced 12 hinges,
and missed the lower three-drawer bank. V5.3 requires 2VN geometry resolution:
a visual view interpretation is verified against immutable Dimension Graph
number/view/vector candidates before an axis becomes direct source geometry.
The visual Cabinet Block then establishes operability before hardware: lower shallow drawer rows are
separate `drawer_bank` assemblies, upper/middle landscape flaps are lift-up
facades, and repeated slats, dividers and fixed panels are structural rather
than operating fronts. The deterministic Lev 1 fixture expects three 600-mm
drawer-slide sets, zero hinges and zero gas lifts. Pending acceptance: a fresh
Lev 1 and Lev 2 production runs with persisted V5.3 facts, 2VN witness audit,
material plan and Object Detail inspection. Contract:
`notes/ESTIMATION_V5_3_2VN_GEOMETRY_CONTRACT_2026_11_03.md`.

IMPLEMENTED locally, pending production witness, Estimation V5.6 Analyze to
Calculation composition contract, 2026-11-03:
[verified] V5.3 left visual semantics and construction decomposition in one
model request. The fresh Lev 1 witness could therefore use a rejected 20-cm
depth and reclassify a fixed screen as hinged facades despite a front-topology
prompt. V5.6 adds one whole-file Estimation Analyze pass that creates an
immutable `estimation_composition_scope_v1` for each object, then passes that
scope to the per-object Calculation call. A deterministic gate permits the
second call to fill only geometry and material roles of locked zones. It also
removes an invalid 2VN-bound dimension before conventional fallback, rather
than retaining the invalid raw value. Pending acceptance: deploy `Estimation
V5.6`, run fresh Lev 1 and Lev 2 witnesses, inspect the persisted
`calculation_handoff`, and verify Lev 1 has three 600-mm drawer-slide sets,
zero hinges and zero gas lifts. Contract:
`notes/ESTIMATION_V5_6_ANALYZE_CALCULATION_CONTRACT_2026_11_03.md`.

IMPLEMENTED locally, pending production witness, Estimation V5.6.1 Scope
persistence repair, 2026-11-03:
[verified] The first V5.6 live witness reached the new Analyze response but
the facts table only allows established BOM contract versions. V5.6.1 keeps
Analyze usage as its own immutable usage event and stores the normalized Scope
and exact Calculation handoff in the final existing assembly-BOM fact it
constrained. This preserves the inspectable contract without weakening the
database contract allowlist or adding a partially persisted intermediate row.
Pending acceptance: repeat Lev 1 from its immutable input, inspect its
Calculation handoff and resulting hardware facts.

IMPLEMENTED locally, pending production witness, Estimation V5.6.2 2VN Scope
binding repair, 2026-11-03:
[verified] The first successful V5.6.1 Lev 1 witness locked the correct three
drawers and zero doors, but Calculation returned generic assembly ids. Scope
renamed them after 2VN, so the accepted 720-mm depth witness was detached and
the 600-mm fallback selected 500-mm slides. V5.6.2 remaps compatible
Calculation assembly ids and their dimension bindings to Scope ids before 2VN
resolution. Pending acceptance: fresh immutable Lev 1 witness must retain the
720-mm drawer depth and return three 600-mm drawer-slide sets with zero hinge
or gas-lift demand.

IMPLEMENTED locally, pending production witness, Estimation V5.6.3 Calculation
fact-version transition, 2026-11-03:
[verified] V5.6.2 corrected Scope-to-2VN remapping but retained the V5.6
Calculation fact version. Existing V5.6.1 facts would therefore be reused for
the same immutable input and conceal the repaired code. V5.6.3 advances the
Calculation fact version, so a controlled replay writes a separate immutable
fact and the active material/object-detail readers select it. Pending
acceptance: the fresh Lev 1 V5.6.3 witness must expose the corrected 600-mm
slide-set result.

ACTIVE, P0, USER REQUEST, 3.17.4.5 Estimation V6.2 whole-object understanding
(local implementation, live acceptance pending):
One shared Analyze must interpret all available Detection evidence (images,
OCR, notes and indexed legends), lock large assemblies and explain material
assignments/assumptions. Object Calculation resolves geometry; deterministic
composition preserves repeated members, front arrangement, layers and edge
material. Compare allowed hidden-material alternatives in the existing
project Material Engine after C/I/A resolution, with whole-sheet rounding.
Do not claim geometric offcut reuse from aggregate area. Labor is excluded.
Base: e608f37. Acceptance and bounded scope:
`notes/ESTIMATION_V6_1_CONSTRUCTION_PLAN_2026_11_04.md`.
CURRENT HSL/N68 RESEARCH CHECKPOINT, 2026-11-05, same 3.17.4.5, P0:
Owner requested complete preservation, not acceptance of failed runs.
Restart record: notes/ESTIMATION_V6_2_HSL_N68_CHECKPOINT_2026_11_05.md.
Tag: estimation-v6.2-hsl-n68-research-checkpoint-2026-11-05.
Selected Front V2 + Planner V4; V5/V6 candidates retained, V6 not promoted
after N68 scope loss. 166 tests pass on final restored-default tree.
All baseline/candidate results and private replay archive are preserved.
Next recommendation: rotation-aware input transport; independent N68 omission,
Front format/count failures and Planner truncation remain pending below.
No main merge, deployment, materials-cycle acceptance or new fix authorization.

HISTORICAL OWNER FRONT CHECKPOINT, 2026-11-05, same 3.17.4.5, P0:
Front interpretation r03 is accepted as a provisional working baseline with
known visual errors, not production-ready estimation. Exact r03 prompt restored;
r04 retired from the active route and preserved in prompt history and evidence.
Checkpoint: notes/ESTIMATION_V6_2_FRONT_COUNT_CHECKPOINT_2026_11_05.md.
Tag: estimation-v6.2-front-count-r03-checkpoint-2026-11-05.
Verification: 106 focused tests pass; dependency suite 54 pass / 3 fail.
All 3 failures reproduce on clean pre-change f20e343, not new regressions.
Deferred, P1: door/side ambiguity and broader visual benchmark validation.
Pending, P0, USER REQUEST: continue with major physical assemblies using all
Detection evidence; reuse the existing components contract. No new provider
stage, schema expansion or block/work number has yet been approved. Agree the
minimal next contract before implementation. Materials only, no labor/pricing.
Completed here: checkpoint preservation, not the overall V6.2 product objective.
The dated experimental reports below are retained history; older active/next
labels do not override this current checkpoint and next-step decision.
Completed diagnostic, USER REQUEST, 2026-11-05, same 3.17.4.5: test Lev1
classification and drawers on unchanged r03 before major-assembly work.
One Haiku 5.5 call, 8.236 s, 13744 input / 1607 output tokens (878 thinking).
Immutable input db175c9d-b911-434e-a3ed-de612640f96f; full page + six islands,
no Naming hint or new Detection call. All six semantic view classes match
visual review: 001/003 axonometric, 002 top, 004 front, 005 side, 006 rear.
Three side-by-side drawers, zero doors/lift-up fronts; fixed ribs excluded.
Original strict validation FAILS because model emits shortened enum labels
(axonometric/top/front_elevation/side/rear). An in-memory diagnostic spelling
expansion passes the remaining contract, but is NOT applied to runtime or
saved original. Annotation visual accuracy was not separately verified here.
Original: /private/tmp/estimation-v6-2-lf1-haiku55-front-count-r03-01.json.
Durable evidence: notes/evidence/estimation-v6.2-front-count-2026-11-05/lf1-r03-evidence.json.
Pending P1: exact enum-output compliance before production integration; no
automatic prompt revision, rerun, silent normalization or production release.
This confirms this sample's semantic classification/count only, not general
robustness, large-assembly decomposition, material accuracy or full cycle.
Major-assembly design discussion, USER REQUEST, 2026-11-05, same 3.17.4.5:
Status pending contract approval, P0. Cabinet Block must distinguish a physical
assembly/carcass from its internal compartments and operating fronts. Owner
prefers practical larger workshop assemblies with shared internal partitions,
not a separate double-sided cabinet behind every front. Two lift-up compartments
in one carcass can have two outer sides + one shared partition instead of four
sides in two separate cabinets. A door pair does not by itself prove two bays
or a required central partition. These are construction hypotheses unless
explicit source evidence defines the assembly boundaries.
Owner Lev2 reference: eight assemblies: separately hanging cabinet; three
lower assemblies (chamfered-end group, drawer/corner group, remaining lower
run); upper corner door/open-shelf unit; combined two-lift-up unit; tall unit
with two drawers/appliance opening/two doors; remaining upper two-door/end
structure. This is a preferred, subjective decomposition, not a mandatory
model target. Lev1 reference is THREE assemblies: lower carcass with drawers,
decorative vertical construction, worktop WITH legs. Supersedes the earlier
assistant's four-part suggestion as this owner's top-level grouping example.
AGENT PROPOSAL, not implemented: extend/reuse existing components contract
with parent membership, front ownership and compartment/shared-part topology;
record source/visual/assumption basis and one short grouping reason. Preserve
one shared countertop spanning several carcasses without duplicating material.
Prefer practical grouping, not unlimited merging for minimal wall count;
respect explicit construction and plausible support/handling constraints.
Evaluation proposal: full physical coverage, each front assigned once, no
duplicated shared parts, distinguish bay count from front count, explain
assumed boundaries, inspect grouped overlay. Judge justified alternatives,
not exact eight/three totals. No example counts/IDs in generic model prompt.
Keep r03 checkpoint intact; no paid call, runtime/schema change or added
provider stage authorized by this design discussion. Labor remains excluded.
Owner clarification: Cabinet Block is ONE authoritative rulebook with TWO
sections consumed by the respective interpretation/planning tools, not two
independent libraries or an instruction to add provider calls. Owner-selected
short names: Cabinet Block Front (drawer/hinged/lift-up versus fixed surfaces,
counting and existing hardware mapping) and Cabinet Block Planner (shared carcasses,
compartments, partition ownership and assembly boundaries). The latter consumes
front interpretation rather than maintaining a competing classification policy.
These short names supersede the proposed Front Interpretation / Assembly Planning names.
Runtime extraction/wiring and the assembly output contract remain pending.
OWNER-APPROVED SIMPLIFICATION / CB Planner V2, 2026-11-05, same 3.17.4.5:
The preceding pending contract/wiring restriction is superseded ONLY for the
bounded Planner experiment. Front display name is CB Front V1, mapping to the
unchanged r03 technical prompt/hash. Planner V1 was the unexecuted chat draft;
V2 is the simplified prompt. Prefer large units that can reasonably be assembled
before moving them, balancing assembly effort and transport practicality.
No hidden partition inventory or detailed construction at this stage.
Implemented via existing understanding agent/probe and shared CB_RULEBOOK;
not a replacement production pipeline. One Planner call per file consumes
saved Front plus identical source pages/inputs, no new Front or Detection call.
Exact fixture equality prevents foreign Front handoff; existing failed Front
enum status remains visible as fallible context, never silently repaired.
V2 SHA256 d5e1b0de71d1053f89ba97cfeecc2352ac4ee126b54f9e8b245ce8df733c7335.
Live results: Lev1 8.864 s, 2 blocks; Lev2 18.404 s, 4 blocks + shared worktop.
Both complete normally and pass scope/reference/box validation, but semantic
acceptance FAILS. Lev1 merges the base with the tall decorative structure,
calls the item a booth bench, and loses one of two table legs. Lev2 groups
entire lower/upper runs and a tall structure into broad assemblies, calls the
L-shaped kitchen U-shaped, and explicitly leaves upper open shelving unassigned.
F24 ambiguity stays assigned as a hinged front instead of a front_conflict.
It also inserts unsupported mm into one uncertainty despite the prompt ban.
Review overlays inspected: Lev2 B03 box includes separately assigned B04;
the shared-worktop box does not cover the complete L footprint. No manual
coordinate corrections. This is not a pure block-count mismatch: physical
scope and geometric interpretation are wrong. No automatic V3 prompt retry.
Artifacts: /private/tmp/cb-planner-v2-lev1-01.json and
/private/tmp/cb-planner-v2-lev2-01.json; same prefixes with -assembly_plan-raw.txt,
-overlay-page.png, -overlay-details.png and -overlay-coordinates.json.
Durable final outputs/reviews: notes/evidence/cb-planner-v2-2026-11-05/.
Status: completed experiment, not accepted, P0. Front r03 checkpoint remains
valid within its accepted limits; Planner is opt-in diagnostic only. No main
merge/deployment/Calculation. Next proposal: review the actual grouping with
owner, then test physical module boundaries rather than another vague request
for large blocks. This proposal is not an approved V3 implementation.
Verification: 128 focused tests pass, including unchanged Front fingerprint,
Planner prompt hash, one-call/source preservation, ownership/conflict checks,
invalid boxes/references, truncation recording and non-mutating overlay export.
Full suite/live product integration were not tested. Structural tests do not
override the two semantic failures recorded above.
OWNER ACCEPTED / COMPLETED segmentation abstraction stage, 2026-11-05,
same 3.17.4.5, P0: for the examined simple objects, two or three Lev1 assemblies
are both acceptable when all physical elements remain represented. A combined
base-and-screen assembly is not itself a regression. Three is convenient, not
a canonical target. This changes interpretation of the earlier 2-versus-3
comparison, not its recorded model output. Owner selects CB Front V2 with legs.
V2 is now the default Front diagnostic; --front-v1 explicitly replays protected
V1/r03, and --front-supports remains an explicit V2 alias. Prompt bytes unchanged.
Acceptance is for conceptual segmentation, not exact dimensions, material BOM,
every front classification, full-cycle reliability or production deployment.

Completed Lev2 regression probe, USER REQUEST; full-cycle status PENDING:
Front V2: 27.005 s, 14261 input / 6163 output tokens. Exact island enums and
original contract pass. Five drawers, two lift-up fronts, 15 hinged doors plus
two unresolved fronts; zero standalone legs, carcass-supported worktop.
Do not equate 15 with semantic benchmark success: known false F01 side remains,
and F10/F11 include the appliance opening among unresolved operating candidates.
Front overlay reviewed without normalization/coordinate changes. Same evidence
and settings as r03; only system changed. Drawer/lift-up counts are retained;
no causal effect of support rules established from this single comparison.
Planner V4: 29.591 s, 15151 input / 6000 output (4124 thinking) tokens.
stop_reason=max_tokens; original status failed before JSON acceptance. Partial
eight-block text is NOT a completed plan, shared_parts/remaining JSON truncated.
Same Planner prompt/settings/images/OCR; only saved Front context differs.
No automatic retry, output-budget change, JSON salvage or causal attribution
to support rules. Evidence: notes/evidence/cb-front-v2-2026-11-05/lev2-*-evidence.json.
Next proposed technical work: isolate Planner output-budget/verbosity failure;
historical Lev1 island enum reliability also remains open. Neither is silently
marked fixed by owner acceptance of segmentation. No production deploy.
Verification: 166 focused tests pass, including selected V2 default, explicit
V1 replay, exact prompt hashes, Lev2 Front result and rejection of truncated
Planner output. git diff --check passes. Protected r03 tag remains unchanged.

N68 owner follow-up, 2026-11-06, same 3.17.4.5, P0:
IMPLEMENTED CANDIDATE, CB Planner V7. Initially unrun; the later controlled
N68 experiment below remains unaccepted. Owner asks
that the worktop cover the complete low-base run, full depth to the wall;
do not offset it by the depth of hanging shelving/cabinets. Approximate base
heights around 900 mm / up to 1200 mm are context, not a hard threshold.
Express coverage as an estimating default with explicit-source exceptions;
do not cover tall cabinets, extend freestanding tops to imaginary walls, or
split an overall top for an inset sink at this stage. Preserve V5/V6 rules.
Owner considers the latest V6 generally reasonable and identifies a crossed
region as a section of an already represented element, not a missing assembly.
The previous agent claim of a lost appliance column therefore needs targeted
identity revalidation, not automatic restoration of an extra block. This is
not proof that the crossed region and the previously named column are identical.
Verified raw V6 already assigns four drawer IDs F12-F15 to B06, from the saved
Front's four-drawer group. Its box only spans the upper part of the lower run.
OWNER CORRECTION in the same discussion: the correct drawer total is SIX,
not the earlier accepted four. Two lower drawer fronts are omitted already
in Front, which describes two columns of two rows and questions the lower
bands. Planner propagates those four IDs. Extending B06 alone will not fix
the count or hardware demand. Preserve raw four; do not manually rewrite it
to six or add example-specific counts to prompts. Current benchmark:
notes/evidence/hsl07-v62-2026-11-05/n68-owner-benchmark-2026-11-06.json.
V7 asks for the complete carcass box, not just union of supplied front boxes,
and reconciliation of repeated views/sections without duplicate assemblies.
Whether the worktop setback was caused by hanging-shelf depth is UNKNOWN;
the saved response gives no causal explanation. Initial preparation made no
model calls. V7 remains unpromoted; runtime selects Front V2 / Planner V4.
Prompt: agents/prompts/cb_planner_v7.md; SHA256
d3271d697f5398e699511d8a261f3f8734bf744835b52b894188d37d819cd848.
Priority next proposal after owner's correction: investigate/fix Front's
omitted lower row before claiming complete N68 counts. Planner-only V7 replay
can test top/block localization but cannot validate six-drawer recognition
while consuming the old four-ID Front. The subsequently authorized V3/V7
experiment is recorded below, without rewriting this earlier diagnostic.
26 Planner tests pass including the corrected benchmark fixture. These tests
preserve the known two-drawer mismatch, not prove it fixed. Checkpoint
6952b4e and raw V4/V5/V6 witnesses remain intact.

N68 Front V3 / Planner V7, USER-APPROVED experiment, 2026-11-06,
same 3.17.4.5, P0, COMPLETED experiment / NOT ACCEPTED:
Front V3 adds only generic complete-stack/larger-bottom-front versus plinth
guidance, retaining unresolved/excluded alternatives and all V2 tasks/schema.
No N68-specific count or example is in the prompt. SHA256
2530993b653575e5445eced53b34ed6b9393eb73c30428c2bac28d641d49429b.
One Front call (36.453 s): six drawers, seven hinged doors, five lift-ups.
The six drawer boxes include both taller bottom fronts, inspected on the exact
overlay. However, the base door to the right of the central pair on p7-view-003
(old Front F06) is omitted, rather than marked unresolved/excluded. The at-run
review used six drawers / eight doors. Latest owner correction supersedes it:
TEN door-like rectangular fronts (five tall, two under sink, one dishwasher,
two in the tall appliance column), separately SIX drawers. V3 covers seven
of ten, missing the dishwasher and two column fronts. V2 also missed the two
column fronts. This does not make the crossed sectional region another object.
The dishwasher opens down; ten rectangles do not imply ten ordinary hinged
doors or gas-lift demand. Preserve raw results and the dated at-run review.
Five inferred lift-ups remain unaccepted. Pending P0: complete front coverage;
hardware classification for appliance fronts needs separate contract review,
not an unapproved schema change or automatic new prompt experiment.
Original Front status failed on snake_case island enums; only display labels
were normalized by the existing diagnostic overlay flag. Raw response, IDs,
coordinates and counts were not changed. Unsupported 10 mm plinth also appears
in its uncertainty. No causal certainty is claimed from this single comparison.
One Planner V7 call (30.261 s) consumed this unchanged failed Front explicitly
as a fallible reference. It hits max_tokens=6000 (3884 thinking), truncating
inside uncertainties. Partial S01 text is NOT an accepted complete plan;
no JSON salvage, completed-plan overlay or verified worktop result. Total two
calls, 66.714 s summed stage time, no retry/budget increase/DB writes/deployment.
Exact N68 inputs/images unchanged; Front request changes only system versus
V2. Planner changes system and saved Front context versus V6; settings unchanged.
Default remains Front V2 + Planner V4. V3/V7 retained as experiments only.
Evidence: notes/evidence/hsl07-v62-2026-11-06/n68-front-v3-planner-v7.json.
Full witnesses and display-only Front overlay: /private/tmp/hsl07-saved-replay-20261105-01/,
object-005-front-v3-20261106* and object-005-planner-v7-front-v3-20261106*.
Next proposal: resolve Planner completion without adding recognition rules;
separately retain the Front enum and three-front omission blockers. No further
repair or model call authorized by this record. The six-page rotation issue
is not implicated in N68's unrotated page and remains pending independently.
Verification: 170 focused tests pass, including current ten-front/six-drawer
benchmark, unchanged defaults, exact candidate identity and rejection of both
failed responses. These checks do not establish semantic acceptance.

N68 Front V4, USER-APPROVED experiment, 2026-11-06, same 3.17.4.5,
P0, COMPLETED experiment / REJECTED for promotion:
Question: does locating every front before movement classification restore
coverage in one existing call? Pass target: ten door-like fronts plus six
drawers with correct individual boxes, no duplicates or fixed-side additions.
V4 adds a facade sweep, location before type, and retention of uncertain or
unsupported appliance movements as unresolved. Existing schema, lower-row
rules, supports, images and settings unchanged; only system differs from V3.
One Haiku 5.5 call, 29.632 s, end_turn; original status failed on the same four
invalid island enums. Raw totals: drawers 4, hinged 3, lift_up 3, unresolved 2.
Overlay confirms regression: five of ten target door-like fronts (3 storage,
2 fridge); both sink doors, dishwasher and two column fronts absent. Each
lower drawer box combines middle and bottom rows, counting four instead of
six. Three alleged lift-ups box triangular shelf marks, not accepted fronts.
Thus location-first wording did not meet the objective on this sample; a
single result does not establish why. No further prompt variation/retry.
Raw evidence: notes/evidence/hsl07-v62-2026-11-06/n68-front-v4.json.
Prompt: agents/prompts/cb_front_v4.md, SHA256
73c4a28213be22631eccf0c0253db1f71631057bdb8d3059a6a2e5047e78d4bd.
Private witness/overlay: /private/tmp/hsl07-saved-replay-20261105-01/object-005-front-v4-20261106*.
No Planner run, schema change, deployment or DB write. Default remains Front
V2 + Planner V4, protected checkpoint 6952b4e unchanged. V3 stays historical,
not a newly accepted default. Pending P0 coverage issue remains open.
DEFERRED proposal after owner rollback request: inspect model-facing image
readability/scale and input budget; image quality is not a confirmed cause.
Verification: 173 focused tests pass, including exact V4 identity, system-only
request change, unchanged defaults and preserved rejection of the raw result.
git diff --check passes; tests do not establish visual acceptance.

Lev2 Front V2 rollback/repeat, USER REQUEST, 2026-11-06, same 3.17.4.5,
P0, COMPLETED diagnostic / acceptance FAILED:
Owner requests rollback and Lev2 on the older version. Stop Front V3/V4
experimentation; retain selected CB Front V2 (r05) + Planner V4. They never
changed globally, so no runtime reversal or destructive Git revert is needed.
Preserve candidate files and raw failures as history, not active selections.
One Front-only replay of /private/tmp/cb-front-v2-lev2-01.json, originating
from saved Detection run_189150ebf62447fc958f7c23cc34e3bb via the established
local-input bridge. No Detection rerun, Planner call, DB write or deployment.
Exact request object equals the prior V2 request: system, images, text and
settings unchanged. Haiku 5.5, 30.653 s, end_turn. New totals: five drawers,
18 hinged doors, two lift-up fronts, zero unresolved; no invented legs.
Owner benchmark: five drawers, two lift-ups, 15 preferred / at most 16 doors.
Page/detail overlays inspected: known side/appliance-opening candidates remain
counted as doors (F11, F08, F25, run-local IDs). No semantic acceptance.
All four intended island classes emitted in invalid snake_case; original
validator rejects. Display aliases only, no response normalization or retry.
Prior identical V2 request returned 15 hinged + two unresolved and passed enum
validation. This is evidence of output variation at fixed application input,
not proof of its provider-level cause. Do not attribute all regression to V4
or treat a previous single passing result as established reliability.
Evidence: notes/evidence/cb-front-v2-2026-11-06/lev2-rollback-repeat.json.
Private witness/overlays: /private/tmp/cb-front-v2-lev2-rollback-20261106*.
Pending P0: output-enum contract reliability and separate semantic variability.
Next PROPOSAL: isolate exact-enum output compliance before another recognition
prompt revision. No automatic schema change or silent output repair approved.
Verification: 174 focused tests pass; exact default/hash, identical request
and preserved failed response checked. git diff --check passes. No claim that
passing tests resolves visual recognition or provider output reliability.

Owner-approved continuation: THREE fixed-request Lev2 V2 controls, same
3.17.4.5, 2026-11-06, COMPLETED diagnostic / NOT ACCEPTED as reliable.
Exactly three calls, independent probes launched concurrently, no automatic
retry or winner selection. Every request object and source input equals the
baseline V2, including system, images, text and settings. No prompt revision.
Control 1: drawers 5, hinged 17, lift-ups 2, unresolved 1; valid format, 32.889 s.
Control 2: drawers 5, hinged 16, lift-ups 2, unresolved 1; valid format, 34.119 s.
Control 3: drawers 2, hinged 11, lift-ups 2, unresolved 0; invalid enums, 28.799 s.
Exact overlays inspected: the long-run lower side candidate is counted in all
three; the appliance-opening candidate switches hinged/unresolved/hinged.
The tall end side switches unresolved/excluded/unannotated. Control 3 omits
ALL counted fronts on view 004, including its three drawers, four base fronts
and two upper doors. Its raw uncertainty explicitly notices three drawers but
suppresses them due to possible overlap with the perpendicular wing. It has
the correct intended view class, so classification alone cannot prevent this.
This establishes a concrete unsupported-deduplication failure in the output,
not the model's hidden reasoning or a production error rate. Count 16 in
control 2 is not semantic acceptance: known false surfaces remain. Control 1
also shifts return-wing boxes vertically. No result is selected as a new truth.
Evidence: notes/evidence/cb-front-v2-2026-11-06/lev2-three-controls.json.
Private raw/overlays: /private/tmp/cb-front-v2-lev2-control-20261106-0[1-3]*.
Pending P0 now localized further: physical-front identity across views,
fixed-side/opening discrimination, and independent exact-enum compliance.
Next proposal was subsequently approved: one bounded same-object correspondence
rule before suppressing a different wing as a duplicate, tested below as V5.
Stop after the agreed three calls; default Front V2 / Planner V4 unchanged.
Verification: 177 focused tests pass, preserving all three differing raw
responses, exact request identity, format failures and view-004 omission.
git diff --check passes; semantic reliability remains unaccepted.

CB Front V5 identity experiment, USER APPROVED, same 3.17.4.5, 2026-11-06,
P0, COMPLETED single trial / causal result INCONCLUSIVE / NOT PROMOTED:
Built directly from V2, not the rejected V3/V4. Only added rule: duplicate
suppression requires a specific counted physical-front match on another view,
not possible overlap; ambiguous identity retains a best-supported estimate.
Same schema, models, settings, images and text. Real request comparison confirms
only system changed. Prompt SHA256 aeff1956341d1c42c1f0ae88a683e8580bdfc958ce8dfb4a3175762ae7584ae1.
One call, 33.906 s, exact format passes: drawers 5, hinged 16, lift-ups 2,
unresolved 1. Both wings retained: view 003 two drawers; view 004 three drawers,
four base doors and two upper doors. Exact overlay inspected, no duplicated
cross-view boxes. Targeted whole-wing omission did not recur in this trial.
Known false lower side candidate F11 remains hinged; appliance-opening F08 is
unresolved. Tall right side is unannotated, not explicitly excluded. Minor
vertical box offsets remain. Full semantic acceptance is not established.
IMPORTANT: V2 control 2 already had the same counts and retained both wings.
One V5 response does not prove the new rule improved reliability. The model's
statement that 3 vs 2 drawers are separate is not universal identity proof.
Evidence: notes/evidence/cb-front-v5-2026-11-06/lev2-identity-trial.json.
Private witness/overlay: /private/tmp/cb-front-v5-lev2-identity-20261106-01*.
Defaults remain Front V2 / Planner V4. No retry, Planner, Detection rerun,
schema change, DB write or deployment. V5 is retained only as a candidate.
Next PROPOSAL: fixed-request V5 control repeats before considering promotion,
not another stacked prompt revision. Further paid calls await approval.
Verification: 180 focused tests pass, including exact V2-to-V5 delta,
system-only request change, retained two-wing coverage and non-promotion.
git diff --check passes; these checks do not establish model reliability.

Lev2 Front V3 + Planner V7, USER-APPROVED three paired runs, 2026-11-06,
same 3.17.4.5, P0, COMPLETED diagnostic / acceptance FAILED;
OWNER-REQUESTED CHECKPOINT PRESERVATION with known defects:
Exactly six calls: three fresh Front V3 results, each passed to its own Planner
V7. Independent pairs ran concurrently; no retries or winner selection. Same
saved Lev2 Detection-derived input/pages and Haiku 5.5 low settings. Front
requests identical across the three runs and differ from V2 only in system.
Planner sees original evidence plus its own raw parsed Front/status. Failed
Front enums are explicitly flagged, not normalized; this is diagnostic
continuation, not a successful production chain. No schema/budget changes.
All three Front outputs: 17 hinged, 5 drawers, 2 lift-up, 0 unresolved.
Both wings retained. Side candidate and appliance opening remain counted as
hinged, so equal counts do not establish correct semantics. Front format
passes only run 2; runs 1 and 3 fail snake_case island enums.
Planner 1 and 2 truncate at max_tokens=6000, with 4151 and 4975 thinking
tokens respectively; unparseable, no salvage or accepted plan/overlay.
Planner 3 completes (5712 output tokens) with 9 blocks + 1 separate worktop.
Its source Front failed validation, so ZERO complete pairs pass both formats.
Summed stage times: 61.529 / 66.051 / 61.744 seconds, not serial batch latency.
Exact Front overlays and valid Planner overlay inspected. In Planner 3,
B08 assigns drawer IDs but its box covers only the adjacent door; B06 covers
only part of the hanging pair; B01's box misses its lift-up fronts. B09 treats
the tall end side as a cabinet column while admitting the fixed-panel option.
S01 is on Top view and separate from cabinets, but misses the terminal
chamfered end of a base wing. Empty interior of its rectangular L-footprint
locator is NOT itself an error; these boxes are not material geometry.
All supplied front IDs are assigned once; this syntactic check does not prove
physical scope or box accuracy. Full-depth worktop/whole-carcass acceptance
therefore remains open. No claim that V3 is generally stable from three calls.
Evidence: notes/evidence/lev2-v3-v7-2026-11-06/three-paired-runs.json.
Private witnesses/overlays: /private/tmp/lev2-front-v3-planner-v7-20261106-0[1-3]-*.
Defaults remain Front V2 / Planner V4. No Detection rerun, DB write, promotion,
deployment or further calls. Next PROPOSAL: isolate Planner completion in a
bounded output-contract experiment, separately from Front enum/recognition;
no budget increase or schema change approved by this result.
Verification: 183 focused tests pass. Regression fixtures preserve exact
stage failures, raw truncated responses, three identical Front totals, zero
full-chain format passes and the B08 assigned-drawer/box mismatch. Defaults
remain unchanged; git diff --check passes. This is not semantic acceptance.

Owner now requests a separate checkpoint labelled PARTIALLY COMPROMISED
("частично скомпрометирован") for the exact Front V3 + Planner V7 pair.
Preservation is completed, not repair or full-cycle acceptance. In the reviewed
Planner 3, B08 includes door F21 and drawers F22-F24: the grouping is permissible,
but its box misses the drawers. Do not record this as an omitted drawer block.
Restart and known-defect record:
notes/ESTIMATION_V6_2_FRONT_V3_PLANNER_V7_PARTIALLY_COMPROMISED_CHECKPOINT_2026_11_06.md.
Tag: estimation-v6.2-front-v3-planner-v7-partially-compromised-2026-11-06.
Private full-input/output archive outside /tmp contains 32 byte-verified files,
including six witnesses, overlays, unchanged baseline input and source PDF.
All prompt hashes, archive SHA256 and recovery instructions are in the record.
Ordinary defaults remain V2/V4; V3/V7 selection is explicit/process-local.
No model calls, main merge, deployment or defect repair in this preservation.
Older tags and 50 unrelated TODO lines retained. Stop further experiments until
the owner chooses the next task; outstanding quality defects remain pending P0.

Block-to-parts tool, USER REQUEST, 2026-11-06, 3.17.4.6, P0, PENDING full-object geometry; research checkpoint preserved:
ACTIVE, P0, OWNER DIRECTION, 2026-11-07: Estimation V7 Analyze structure.
IMPLEMENTATION ITERATION, 2026-11-07, same work 3.17.4.6:
LATEST OWNER STEERING / TWO SIMPLE-FILE TRIALS, 2026-11-07:
OWNER REVIEW / NEXT V7 ITERATION REQUEST, 2026-11-07:
OWNER-APPROVED AUTHORITY BOUNDARY / PARTS DISCUSSION, 2026-11-07:
LATEST OWNER-APPROVED IMPLEMENTATION / EXPERIMENT, ESTIMATION V7.2,
2026-11-07, same 3.17.4.6, P0, FULL-OUTPUT ACCEPTANCE FAILED:
LATEST OWNER REVIEW / HISTORICAL REUSE AUDIT, 2026-11-07:
LATEST OWNER-APPROVED IMPLEMENTATION/TRIAL, V7.3, 2026-11-07, 3.17.4.6:
COMPLETED local experiment; NOT ACCEPTED as replacement, P0 remains PENDING.
OWNER REVIEW / INCREMENTAL DIRECTION, same work, 2026-11-07:
LATEST OWNER WORKING BASE / FRONT REVIEW, 2026-11-07:
ACTIVE, P0, same 3.17.4.6. Owner selects ORIGINAL V7.2 with explicit
thinking=disabled and output_config.effort=medium as the working research base,
and requests a complete explanation/inspection of CB Front before tuning.
This accepts the research configuration, not physical output or production
promotion. Ordinary run_analyze still defaults to low; medium remains the
saved replay configuration. No new provider calls or prompt/schema/runtime
changes in this inspection. Front tasks 2-4 from cb_front_v3.md run within the
same shared Analyze, not a separate stage/API call. Exact saved medium Lev2
boxes rendered on the exact request crops without corrections:
/private/tmp/lev2-v7-2-disabled-medium-front-review-20261107-01-overlay-details.png
(page and coordinate JSON share the prefix). VERIFIED: multiple boxes miss
drawn fronts; F14-F16 lie above the actual lower drawer bank. Front structural
validation passes but does not test physical box placement or complete visual
coverage. Keep counting/type errors distinct from localization errors; their
common cause is UNKNOWN.

OWNER-APPROVED FRONT-ONLY TRIAL, 2026-11-07, same work 3.17.4.6, P0:
COMPLETED diagnostic, NOT ADOPTED. Replay revision V7.2-medium-front-locate-first. For both
saved original disabled/medium requests, verified the sole difference is CB
Front tasks 2 and 3: locate and mark surfaces, then classify and count. Task 4,
other Analyze sections, schema, evidence and request settings stay identical.
56 focused tests pass. Owner explicitly authorized sending the two saved
image/OCR/Detection payloads to Anthropic; one call per document, both
end_turn, zero thinking tokens, no retries, Calculation, DB or production change.
Lev1: 3 drawers/2 legs preserved; new V4 drawer boxes lie entirely below
their surfaces. The existing thickness mismatch remains; independent Front
validation passes and independent Planner reference validation regresses.
Lev2: doors/drawers/lifts 12/6/3 to 7/3/2 vs owner 15/5/2; both structural
checks pass. Lift count improves, but its boxes remain above the intended
fronts; V4 drawer boxes still miss the row. V4 lower door group and V3 drawer
group disappeared. Blocks 6 to 4. No gain in visual coverage in this trial;
effect not established across repeated runs. Keep original 7.2 medium as
working control; do not promote this Front prompt. P0 remains ACTIVE.
New private capsules: /private/tmp/{lev1,lev2}-v7-2-medium-front-locate-first-20261107-01.json.
Uncorrected comparison overlays: lev1-front-comparison.png and
lev2-front-comparison.png in the thread visualization directory.

OWNER FOLLOW-UP, P0 ACTIVE, same work 3.17.4.6: diagnose Front coordinate
grounding vs physical recognition and compare saved intermediate versions.
Offline evidence: notes/evidence/estimation-v7-2-retrospective-2026-11-07/front-coordinate-audit.json.
Verified Lev2 V4 original medium: all nine boxes nearly match their faces if
read as native crop pixels, not as the declared 0..1000. Locate-first still
has this mismatch for V4 drawers and V3 lifts, and genuinely omits V4 lower
doors. Do not bulk-convert: other F boxes exceed native image bounds. Lev1
already receives the three-drawer count from Detection; new boxes miss under
either interpretation. Saved standalone Front V2/V3 show materially better
V4 drawer placement in multiple runs, but also miss/shift fronts in others.
Cause of the change across configurations remains UNKNOWN.

OWNER-APPROVED FRONT PIXEL TRIAL, same work 3.17.4.6, P0:
COMPLETED diagnostic; NOT ADOPTED. One Lev2 call from original 7.2 medium,
not locate-first. The sole request change is the Front coordinate convention:
exact crop sizes, bbox_px for Front only; deterministic bounds check and
conversion to canonical bbox_1000. All images, messages, provider settings,
non-coordinate instructions and Planner coordinates are unchanged. No retry,
Calculation, database write or production change. 65 focused tests pass.
V4 on the same measured reference: before 0/9 and after 7/9 localized with
one-to-one IoU >= 0.5. All seven match type (3 drawers, 2 lower doors, 2
hanging doors), IoU 0.805..0.987. Lower doors 3 and 4 are unannotated. All
18 Front and two exclusion pixel boxes convert in bounds; model declares
14 hinged vs 13 in groups, so unchanged full validator rejects. V3 loses
lift-up classification. Geometry signal improved for the returned V4 boxes;
coverage and full Front acceptance remain open. Keep original medium control.
Evidence: notes/evidence/estimation-v7-2-retrospective-2026-11-07/front-pixel-trial.json.
OWNER FOLLOW-UP, offline V4 lower-door diagnosis (no rerun or coordinate
change): original Front counted the entire V4 base door bank F10-F13 even
though Island Map mentioned two doors. Pixel trial Island Map mentions two
left doors, three drawers, and a right door; it does not identify door 3
before the drawers. In the raw Front, only F17/F18 (the two lower doors
directly under the hanging pair) survive in the group 'Base run left of
corner (doors)'; the drawers remain a separate group. Door 3 and the right
door have no F/X/unresolved entry or documented cross-view correspondence.
The right door is therefore acknowledged in Island Map but omitted by Front.
Planner B02 reflects the two-door result, not a downstream deletion.
LIKELY visible failure is incomplete horizontal coverage of the lower run,
not coordinate conversion; internal cause (including implicit deduplication)
is UNKNOWN. Owner clarification: any next completeness check must be generic
across object forms and layouts; no Lev2-specific, kitchen-row or expected-count
instructions. Proposed (not implemented): review all relevant visible regions
for candidate operating surfaces, including outside already-found groups;
reconcile candidates mentioned elsewhere in Analyze against the source.
Count distinct physical fronts, exclude only with evidence, and deduplicate
only a positively matched depiction. Lev2 V4 remains a benchmark, not prompt
input. Original 7.2 medium and coordinate experiment unchanged.

OWNER-SELECTED RESEARCH CHECKPOINT, P0 ACTIVE, 3.17.4.6, 2026-11-07:
Freeze original 7.2 disabled/medium plus Front pixel coordinates as
`estimation-v7.2-medium-front-pixels-experimental-2026-11-07`. This selects
the research configuration only, not physical coverage, whole Analyze
acceptance, or a runtime default. Keep the locate-first trial as history.
Generic completeness rule remains proposed, not included in this checkpoint.
Replay revision V7.2-medium-front-pixels on the two original private
`/private/tmp/lev{1,2}-v7-2-disabled-medium-20261107-01.json` capsules.
Verified replay request SHA-256: Lev1
`cada76a8a875e1bd62d6ab766ce34eb52e0ea5d2c7d99b23214ac0cd77dfbb1e`; Lev2
`8d5cf572f014b5002318412392e6c86dafeb2063d35dd31c08f998b31d26eca1`.
Owner-requested pair after checkpoint `453cff5` COMPLETED, one call per
document, no retries, repairs, Calculation, deployment or push. Lev1 V4
3/3 drawer boxes matched (IoU 0.950..0.962), but one leg instead of two and
the existing normalized thickness mismatch. Lev2 exact replay of the pixel
pilot: V4 9/9 matched with correct type (IoU 0.947..1), versus pilot 7/9.
No coverage rule was added; the improvement across identical requests is
observed variation. Full Lev2 validation fails on out-of-crop X02 on V3;
declared 9 hinged vs 11 grouped, and lift-up faces still misidentified on
V3. Both runs end_turn, zero thinking, independent Planner refs pass. Keep
the tagged experimental configuration; full physical acceptance stays open.
Evidence: notes/evidence/estimation-v7-2-retrospective-2026-11-07/front-pixels-checkpoint-trials.json.
OWNER-REQUESTED LEV2 EXACT REPEATS, 3.17.4.6, COMPLETED diagnostic: two more
calls, both verified identical to the previous pixel requests; no changes,
retry or repair. V4 scores across four: 7/9, 9/9, 8/9, 9/9, all matched types
correct. Latest 02 misses the lower door right of the drawers; its V3 real
lift pair is matched but three upper doors are also called lifts. Model totals
9 hinged vs 11 grouped; full validation fails. Latest 03 passes structure and
V4, but omits the actual V3 lift pair and still calls three doors lift-ups.
One of four full structural passes, no whole-object physical acceptance.
Keep experimental tag unchanged. Evidence:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/front-pixels-lev2-repeatability.json.
OWNER OVERLAY CORRECTION: rightmost lower V4 panel immediately right of the
drawers is a fixed side wall, not an operating door. Supersedes the old
nine-face interpretation and prior 'missing end door' finding. Revised V4
operating-front coverage in the four exact requests: 7/8, 8/8, 8/8, 8/8.
Checkpoint-01 and repeat-03 counted the fixed side as hinged; repeat-02
did not miss a door there. Retain original raw responses and measurements;
the total Lev2 hinged benchmark is not independently reconciled here.
OWNER-REQUESTED ADDA BENCHMARK, P0 ACTIVE, 3.17.4.6: one completed authorized
call on the exact saved protected Adda run `run_4e47c1226af946698779203ca31ff705`
using 7.2 medium + Front pixels. Object-002 V1/V4/V6/V8 and object-001
V2/V3/V5/V7 both retained. Four pages and eight crops; no Detection rerun,
Calculation, DB write or deployment. Probe now accepts a checked local
preflight without requiring a prior paid baseline; old requests unchanged.
66 focused tests pass. Front 4 and 6 estimated drawers respectively, but
zero F boxes for either, so both independently fail box-count validation.
Useful Block outline: two for L-shaped display, one for straight counter.
Source review: V2 is axonometric; the straight counter's glazed vitrine
claim is unsupported (the visible glazing label points to a neighboring
fragment), and its second drawer row is unsubstantiated. V8 plan 2000 length
misreported as height. No physical
acceptance or further authorized call. Evidence:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/adda-front-pixels-trial.json.
OWNER ADDA REVIEW / FRONT FOLLOW-UP, same work 3.17.4.6, P0 PENDING:
Owner reference, not prompt input: V1/V4/V6/V8 object has 6 drawers, 8
specified pull-out shelves, 8 doors, 2 mirrors, glazed vitrines and a fixed
open shelf (do not count as operable). V2/V3/V5/V7 object: 3 drawers, mirror.
User requests general recognition of X opening symbols as door evidence,
interpreted in drawing context; do not hardcode Adda or treat every diagonal
cross as a door. Explicitly indicated pull-out shelf is a distinct moving
element in Front, one slide set per shelf; do not infer it from generic shelf
geometry, conflate it with a drawer or count a fixed open shelf. Representation
and downstream hardware contract pending; not shipped.
Offline Front-box diagnosis: raw Adda response already has fronts=[] for
both nonzero estimated groups, while it emits one pixel X box per object.
Finished end_turn at 4083/14000 output, not a conversion or rendering loss.
Earlier CB Cycle V5 counter-only response emitted three F boxes on the same
page images, with different input format and an incorrect stacked topology;
neither proof of correct old localization nor isolated cause. Further offline
comparison: exact pixel system prompt matches Lev1 and four Lev2 samples
except crop-size list; provider settings identical. Lev2 repeat-02 includes
5 F boxes for 5 estimated fronts, so estimated status alone does not explain
empty lists. Adda differs in source/complexity and shared response for 2
objects (12 images/44122 input vs 5-7 images/25246-26600 input for Lev).
OWNER PRIORITY: isolate cause before any semantic or schema change. Proposed
diagnostic step 1 completed with owner authorization: exactly one repeat of
the same Adda request, 17.671 s / 4725 output / zero thinking, end_turn.
Both original memberships retained; object-002 again estimates 4 drawers
with no F boxes, object-001 again estimates 6 with no F boxes. Raw omission
reproduced, both independently fail the existing count/box check. No runtime,
prompt or schema changes. Step 2 COMPLETED: one authorized call requested
only object-001, retaining all 12 images, OCR, both objects' Detection
context and the original Front rules/settings. Verified sole request change
is output scope; the response contains only object-001. End_turn, 10.439 s,
2342 output, zero thinking. Estimate changed 6 to 3, explicitly inferred
from three bays; F boxes stay zero and the same validation error remains.
One-result scope alone is insufficient; two requested results are not a
necessary condition. Do not infer input-load cause or split Analyze from
this. 67 focused tests passed for opt-in probe only; no runtime changes.
V02 callout diagnostic COMPLETED, one authorized call on the exact single
V02 crop, no count hint, same model/medium/thinking settings; main prompts
unchanged. Three arrow tips within about 2.3 px of visually read references.
Only 1/3 corresponding face boxes good: first box is on the adjacent middle
drawer (its own tip outside), second extends below the drawer, third matches
the right drawer (IoU 0.912). This isolates a visible tip-to-face association
and boundary error, not proof of why the shared Analyze omitted all F boxes.
Exact raw and overlay references are in adda-front-pixels-trial.json.
NUMERIC COUNT RULE DIAGNOSTIC, owner-approved, COMPLETED: one full Adda
7.2 medium + pixels request differing in one sentence only, explicitly
including estimated numeric counts in one-box-per-front requirement.
Both objects returned 3 estimated drawers and 3 F boxes (prior 0 F);
full structural validation passes. V02 has 0/3 localized to its indicated
faces (best IoU per box 0.068..0.098), V04 F06 spans two panel outlines.
Supports prompt wording affecting emission, not correct recognition or
stable cause. No prompt/runtime adoption, retry or further call. Evidence
and overlays in adda-front-pixels-trial.json. Probe ran from archived
ac3d953 code; active temporary checkout lacks Git metadata/dependencies.
OWNER-REQUESTED LEV CONTROLS, COMPLETED: same one-sentence variant, one
Lev1 and one Lev2 call on unchanged pixel-checkpoint inputs/settings. Lev1
3/3 drawer boxes (IoU 0.914..0.937), two legs, independent Front passes;
thickness mismatch and independent Planner reference error remain. Lev2
structural pass but V4 6/8 using owner-corrected reference: two hanging
doors missing and F15 wrongly counts the fixed side. True V3 lifts absent.
No retry, promotion or main prompt change. Evidence:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/lev-numeric-boxes-trial.json.
OWNER FOLLOW-UP: LF2 missed-front diagnosis, offline. New response's Island
Map V3 calls the three upper surfaces doors, but Front X01 covers the same
band as fixed 'in this estimate context'. Prior pixel runs localized those
surfaces (wrongly typed as lift-ups). V4 upper pair is explicitly named as
two doors in Island Map, and Planner keeps its cabinet, but Front emits
neither F nor X for the pair. Real V3 lift pair also absent; checkpoint-02
located both. No coordinate/box loss after generation. LIKELY failure is
inconsistent physical-role/coverage decisions across the shared response,
with Front counting only lower groups. Cause of variability not established;
one new sample versus varying exact repeats cannot establish no regression
from the numeric count sentence. Proposed next isolated, universal check:
before finalizing Front, reconcile source-supported operating candidates
across relevant Islands (including beyond found groups); do not silently
drop a candidate or exclude a whole band without surface-specific evidence.
Unresolved movement on an identified operating face remains unresolved,
not fixed. No counts, kitchen topology or LF2 identifiers in production
instruction; no coordinate, schema or hardware changes in this diagnosis.
OWNER ISLAND MAP CONTRACT: strict categorization only, no generated
`islands[].observation`; Description remains in Understanding. Detection
accepted_observations are input evidence and unchanged. One authorized
Lev2 trial on prior 7.2 medium + pixels + numeric-boxes, removing only the
observation instruction/key, strict validator in isolated probe. Four
categories returned unchanged, no comment; full structural validation passes.
Understanding includes the separate hanging cabinet, still mislabels bare
readings as mm. Front 7 hinged/3 drawers/0 lifts; V4 5/8 (two hanging doors
returned, three lower doors omitted, fixed side not counted). V3 lifts and
drawer bank absent. One run does not establish impact on recognition.
No retry, default promotion or checkpoint move. Evidence:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/lev2-strict-islands-trial.json.
LF2 HISTORICAL COVERAGE COMPARISON, offline: latest broader pixel witness
checkpoint-02 localizes corrected V4 8/8, real V3 lift pair and upper-right
trio, but mislabels trio as lifts and fails totals. Earlier standalone Front
V3 run-02 types those measured surfaces correctly, but F21 counts fixed
V4 side as door. Current strict-islands misses V4 three lower doors and
V3 upper groups. Same input/settings vs pixel witness; only numeric count
sentence and Island Map observation differ. No accepted all-front LF2
baseline or causal attribution. Use these as visual references, not an
automatic rollback. No new call or code change.
Exact request diff verified: checkpoint-02 -> numeric variant changes only
"known group count" to "any numeric group count, including estimated";
numeric -> strict Islands removes only the observation instruction/key.
Front template is identical in all three pixel requests. Separate Front V3
Tasks 2-4 recognition rules are the same apart from pixel encoding and this
count sentence; standalone Task 1 island_types moved to Island Map, Task 5
totals/null prose not carried into the combined template. Old task scope,
evidence context and thinking/effort differ, so no cause inferred. Proposed
single-factor diagnostic COMPLETED after owner authorization: one Lev2 call
restored only the old count wording, with strict Islands, pixels, medium
and thinking disabled. Structural pass; V3 gets 2 drawers and all 5 target
upper surfaces, but the real lift pair is typed hinged. V4 drops all 8.
Coverage shifts, not a recovery. Not adopted, no retry or schema change.
Evidence appended to lev2-strict-islands-trial.json.
OWNER-REQUESTED LANDMARK CONTROLS, COMPLETED: one Lev1 and one full Adda
call with the same strict Islands + landmark/nullable bbox Front as Lev2.
Lev1 3 named/3 boxed (V4 IoU 0.926..0.938), one leg instead of two, legacy
thickness and Planner reference errors. Adda object-001 3 named (left/centre/
right V3), object-002 4 estimated entries across V4 bays; all seven bbox_px
null. This is direct named-but-unmarked output, not proof of their physical
identities. Both Adda diagnostic Front/Planner checks pass independently;
full validation fails foreign Understanding source refs. No retries,
prompt changes or promotion. Evidence:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/front-landmarks-lev1-adda-trials.json.
OWNER-REQUESTED ADDA LEGACY WORDING COMPARISON: one call, only known count
qualifier restored; same per-front records, landmarks, nullable bbox and
checks. Straight counter 3 named/3 boxed unresolved, all miss indicated drawer
faces; L display 3 estimated named/3 boxed vs control 4/0, not accepted.
Full structural pass, no new checkpoint or repeat. Evidence in same JSON.
OWNER RETAINS CLARIFIED NUMERIC WORDING for the diagnostic variant. Two
requested exact repeats completed, one each Lev1/Lev2, no prompt change.
Lev1 3 named/3 boxed, one leg and existing thickness failure. Lev2 12
named/12 boxed, no null; V4 again 5/8 with three lower doors missing, fixed
side no longer counted; V3 two upper doors return, real lift pair absent.
Lev2 format passes, not physical acceptance. No retry or checkpoint move.
Exact witness paths in front-landmarks-lev1-adda-trials.json.
OWNER-SELECTED FULL RESEARCH CHECKPOINT, P0 ACTIVE, same work 3.17.4.6:
`estimation-v7.2-medium-front-landmarks-experimental-2026-11-07` on
`codex/estimation-v7-2-front-landmarks`; prior pixel tag 453cff5 unchanged.
Selected: strict Island Map, medium/Thinking disabled, bbox_px -> bbox_1000
when non-null, per-front landmark, and explicit numeric count-to-entry rule.
This is a reproducible diagnostic starting point, not accepted geometry,
production defaults or permission for more runs. 89 focused tests and five
exact saved request comparisons; no new provider calls for checkpoint.
Open P0: Lev2 complete coverage/types and Adda locating named faces; legacy
wording comparison on Lev1/Lev2 with this exact schema remains PENDING, not
approved. Pending separately: X evidence and explicitly indicated pull-out
shelves/slide sets. No mandatory Island report or Thinking. Manifest:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/front-landmarks-checkpoint.json.

COMPLETED owner-requested offline vector diagnostic, same 3.17.4.6.
Source PDF paths produce closed contours for 8/8 Lev2 V4 reference fronts,
including all three lower doors missed in the landmark repeats. The fixed
side also closes; role classification and cross-view deduplication remain
open. Adda V02 has three native leaders with one root and three separate
drawer faces. Each tip maps to its own face after 0.75 px endpoint snapping
in the 1100 px crop; at 0.25 px the left tip has no matching closed face.
“Ящики” was verified visually and is absent from the saved OCR. Results
are scoped to these vector PDF views, with zero provider calls and no runtime
change. Overlays and coordinate audit in the thread visualization directory:
`lev2-v4-offline-vector-overlay.png`, `adda-v02-offline-vector-overlay.png`,
`estimation-offline-vector-fronts-evidence.json`.
Owner-requested expansion COMPLETED offline across all 18 Islands (Lev1 6,
Lev2 4, Adda 4+4, frozen Detection memberships). Lev1 V04 localizes three
drawers, V06 two supports. Lev2 V04 repeats 8/8; V03 localizes the two lifts,
three upper-right leaves, four lower reference doors and two drawers,
with additional surface roles still open. Adda V02 localizes three drawers
and the mirror; V01 maps six drawer and eight pull-out shelf arrows to
distinct candidates and four X groups to eight leaf candidates, with two
visually identified mirrors. Labels were read visually. Lev1 V01/V03
and Lev2 V02 are raster; the current vector method gives no faces there.
Adda V06/V07 retain merged contours. No model call, runtime change,
automatic semantic acceptance, or validated Blocks/Parts output.
Four object overlays and `estimation-offline-all-islands-evidence.json`
in the thread visualization directory.
OWNER-ACCEPTED OFFLINE GEOMETRY CHECKPOINT, COMPLETED, 3.17.4.6:
`estimation-v7.2-medium-offline-vector-experimental-2026-11-07`.
Private local archive and validated replay, with 9 byte-identical files:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/offline-vector-checkpoint.json.
P0 ACTIVE for the existing Front acceptance objective. Owner stopped the
V7.3 cache and contour-label path after the three-file diagnostic. Retain
it on `codex/estimation-v7-3-knowledge-base` at `907f7be`.
Continue from protected V7.2 Offline Vector `067bf63` on
`codex/estimation-v7-2-opening-marks`. The optional `--opening-marks`
replay adds only per-leaf swing marks, a full-X cut or continuation cue,
and text leader tip binding to the Front prompt. Five baseline request
comparisons and 37 focused tests passed. Owner-approved three-file replay
COMPLETED: Lev1 retains 3/3 drawer boxes and misses the second support;
Lev2 names 21 fronts with zero boxes; Adda emits no individual front records.
Full-object acceptance remains PENDING. Evidence:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/opening-marks-trials.json.
Owner returned to the deterministic Offline Vector replay. Restored all
18 Islands from the protected archive and reproduced nine files plus the
original Adda V01 swing-mark JSON and overlay byte-for-byte. The exact mark
rule detects eight Adda V01 leaves and no marks on the other 17 views.
COMPLETED full local V01 review: 8 hinged leaves by native swing marks,
6 drawers, 8 pull-out shelf positions and 1 fixed open shelf via native
leaders with visually read labels, plus 2 mirrors. Two glazed zones, two
LED 3000 callouts and one window closure are visible. The latter's outline
has a 1.69 px endpoint gap and was recovered separately. Pane counts,
internal fixed shelves and physical LED strip counts remain unresolved.
Saved OCR lacks the callout text; local Vision did not return results.
Zero Anthropic calls in that offline replay. Visual evidence in the thread
visualization folder under `offline-marks-replay/`.
Owner requested model-only interpretation on V01. COMPLETED one Haiku 5.5
medium/no-Thinking call on the source crop and neutral C/A IDs. No human
role labels or expected counts in the request. The model read all ten leader
groups, including two LED 3000 callouts, in 8.114 s. Raw role-to-contour
selection matched 0/8 hinged leaves, 0/6 drawers, 7/8 pull-out shelf positions
with 14 extras, and 1/1 fixed open shelf. All eight hinged leaves were called
drawers. Model-chosen leader IDs with native tip binding recovered 6 drawers,
8 pull-out shelves and 1 open shelf offline without manual role labels.
Raw model output and separate comparison in `adda-v01-model-inventory/` in
the thread visualization folder. Private provider witness:
`/private/tmp/adda-v01-model-inventory.YKkuoCFk/model-result.json`.
OWNER-REQUESTED V7.4 FRONT REPAIR, P0 ACTIVE, 3.17.4.6:
Keep V7.2 Offline Vector and V7.3 on their existing refs. The model-only
failure was expansion from correctly read leader groups to unrelated contours.
The opt-in V7.4 probe separates leader semantics, per-leaf stroke semantics
and labels inside contours. Code binds each typed leader by native tip to a
unique contour, deduplicates and surfaces conflicting evidence.
Two completed Haiku 5.5 medium/no-Thinking Adda V01 trials: the first matched
8 hinged leaves, 6 drawers and 4 of 8 pull-outs. It misread A03 as a mirror
label. Adding localized source-caption crops matched all 8 pull-outs and 6
drawers, but the model called all 8 swing marks cut/fixed. Offline composition
of the two untouched model responses by evidence channel matched the exact
reference IDs: 8 hinged leaves, 6 drawers, 8 pull-outs, 1 fixed open shelf and
2 mirrors, with zero extras or binding conflicts. No manually supplied roles
or counts. This establishes the binding behavior, with the two inputs picked
retrospectively. It does not establish repeatability or a single-pass result.
Evidence: notes/evidence/estimation-v7-4-front-evidence-2026-11-07/adda-v01-local-replay.json.
Private witnesses: /private/tmp/estimation-v74-adda-v01.EeGLMa5H/.
2026-11-08: One explicitly authorized combined Adda V01 request completed
with caption crops and isolated stroke tiles. Exact IDs for 8 hinged leaves,
6 drawers, 8 pull-outs and 1 fixed open shelf, with no extra contours in those
classes. Two glass zones, two LED callouts and the window closure were read
as annotations. Mirror count was 2, but only C16 matched. The model read the
label and chose the adjacent C14 instead of C19. No manual role corrections.
Runtime 3.268 s, 7,632 input and 594 output tokens, zero Thinking tokens.
Evidence: notes/evidence/estimation-v7-4-front-evidence-2026-11-07/adda-v01-single-run.json.
The narrow Front classification repair passed V01. Full-view acceptance is
partial. Direct text-to-contour ownership and Adda V02/full Adda model
validation remain pending.

2026-11-08, owner-requested Lev1/Lev2 transfer trial, COMPLETED (partial).
These views have no native leader groups or per-leaf swing pairs. The
visual-only companion probe sent all frozen clean Islands and neutral
contour maps once per file, medium/no Thinking, no reference labels.
Lev1 V4: 3/3 drawer contours, grouped into one physical record. V5: 1/1
support appearance; V6: 0/2 support contours. Lev2 V3: 9/11 typed contours;
both lift-ups omitted. V4: 5/8, with both upper doors and all three drawers
localized; three lower doors omitted, fixed side excluded, two plinth
contours mislabeled support legs. Model grouped distinct same-view faces
in both files. Offline validation now preserves appearances but suppresses
the physical total when the grouping contract is violated.
Evidence: notes/evidence/estimation-v7-4-front-evidence-2026-11-07/lev-visual-front-runs.json.
OWNER-SELECTED V7.4 RESEARCH CHECKPOINT, COMPLETED, 2026-11-08:
`estimation-v7.4-front-evidence-experimental-2026-11-08` freezes both probe routes, the raw
witnesses and partial benchmark. notes/evidence/estimation-v7-4-front-evidence-2026-11-07/front-evidence-checkpoint.json.
P0 ACTIVE, V7.5, same work 3.17.4.6. Diagnose same-view grouping first.
Verified in the raw model responses before binding: Lev1 V4 C32/C33/C34 are
three drawer contours in one drawer item. Lev2 V4 C05/C06 share one hinged
item, and V3 C27/C28 plus V4 C19/C21/C22 share one drawer item. Each file's
frozen Detection membership contains one object. These are Front record
groupings. Separate recognition misses remain, including the V3 lift pair
and three V4 lower doors. In V7.4, an item combines physical identity and
an array of appearances. Likely the model used that array for a bank of
adjacent faces. The schema hypothesis requires a controlled live check.
V7.5 opt-in `--per-island` now prepares one flat record per face per Island.
It derives no document total or cross-view identity. Preflight on both
frozen files verified that only the output instructions and shape in
the system block differ. Old hashes reproduce exactly, and offline
flattening preserves all 10 Lev1 and 18 Lev2 raw appearances.
2026-11-08, owner-authorized Lev1 control, COMPLETED (partial). Exactly
one request, system block only changed relative to V7.4. The model returned
three separate V4 drawer rows (C30/C33/C31), versus one row with C32/C33/C34
in V7.4. Row separation passed, exact ownership matched 1/3. C30 encloses
the first and middle drawers, including the separately selected C33.
C31 nearly coincides with the right drawer C34 (bbox IoU 0.928).
Both V6 support contours C26/C28 matched. Binding issues were empty;
the binder checks contour identity, not nested geometric overlap.
One run does not establish repeatability. Next: distinguish composite
outlines from individual face contours and evaluate ownership separately
from row separation. Lev2 remains pending. The protected V7.2 geometry
and V7.4 experimental tag remain the baselines.
Evidence: notes/evidence/estimation-v7-5-front-identity-2026-11-08/lev1-per-island.json.
Private witness: /private/tmp/estimation-v75-lev1.NxQR6LSM/result.json.

2026-11-08, owner-requested V7.5 Front run on Lev2 and full Adda,
COMPLETED, partial benchmark. The unchanged per-Island prompt used one
request for all four Lev2 Islands and one per frozen Adda object
(001: V02/V03/V05/V07; 002: V01/V04/V06/V08). All three responses completed
with individual rows and no binding issues. Lev2 matched all 11 reviewed
V3 contours and all 8 reviewed V4 contours. V4 also labeled the fixed side
as a hinged door and two plinth sections as legs. Adda 001 matched all
three drawers and the mirror on V02, with four extra drawer contours.
V03 matched the same three drawers in another projection. Adda 002 V01
matched only 1/25 exact role and contour pairs (mirror C16); C52 was
labeled as a fixed shelf instead of a hinged leaf. Adda 002 V04 matched
mirror C14. No cross-view physical totals were generated.
Evidence: notes/evidence/estimation-v7-5-front-identity-2026-11-08/lev2-adda-per-island.json.
Private witnesses: /private/tmp/estimation-v75-full-bench.ooddu9PG/.
Keep the typed V7.4 evidence control for Adda V01. The V7.5 run tests flat
per-Island rows without typed leader/caption and isolated swing evidence.
That comparison does not isolate a schema-only effect for Adda.

COMPLETED, 2026-11-08, same work 3.17.4.6: Lev1 support attribution
diagnosed offline. V7.2 Front explicitly chose the one visible support on
V05 and assigned both V06 posts to the bench. V03 and V06 establish two
tabletop supports; V7.5 marked both. Independent Front validation passes
on its own count and box consistency. Owner-approved full-answer review
format and material assumption are recorded in handoff section 39.
Future acceptance: reconcile support ownership and physical count across
projections and repeat the resolved count consistently in Analyze. No
new run or prompt/schema change in this review.

P2 DEFERRED by owner until the first standard Detection → Analyze →
Calculation cycle is complete and stable. Optimize context, cost and
reuse using measurements from that accepted baseline.
- Version and persist accepted stage outputs and source links so a
  Calculation-only revision can reuse an unchanged Analyze result. Include
  evidence identity and stage version in reuse decisions.
- Keep a compact, versioned Markdown rules source. Select relevant sections
  by stage and object type. Benchmark provider prompt caching separately
  with identical prompts and inputs, tracking cache writes, hits, cost and
  latency. V7.3 recorded 7,107 cached input tokens on Lev2 and Adda;
  quality and caching effects were not isolated in that comparison.
- Consider semantic retrieval when the reference corpus outgrows explicit
  section selection. Evaluate source relevance and coverage against direct
  lookup before adding an embedding index.
- Extend existing typed relationships from Islands to Front and Parts for
  source traceability. Revisit a dedicated graph store only if concrete
  queries exceed the existing structures. No infrastructure work before
  the stable cycle.

After V01, check source-label reading and constrained tip binding on Adda
V02. Preserve the separate swing-mark evidence. Then verify dimension ownership
on Lev1 using existing 2VN bindings, including mark 20 normalized to
200 mm. Link an explicit section/detail marker to its parent and
verify one physical block across views. Raster recovery and Blocks/Parts
remain pending.

OWNER REFINEMENT: do not require a status report for every Island. The next
diagnostic question is recognition of a distinct physical face versus its
annotation in the same response. The 8/8 V4 and V3 lift-pair evidence belongs
to a prior invocation that DID emit boxes, not an earlier phase of the
current invocation. Current Front has no per-face record independent of its
box, so absence alone does not separate not recognized from not marked.
Proposed (not run): one Front-local candidate list (stable ID, source Island,
short physical landmark/type), plus bbox or explicit unlocalized outcome per
ID. Compare against source; no mandatory per-Island ledger, Thinking or
additional provider stage. Prepared per-view ledger probe was not sent.
OWNER-APPROVED FRONT LANDMARK DIAGNOSTIC, COMPLETED: one L2 with the strict
Islands numeric-count control, Thinking disabled. Only individual landmark
and nullable bbox_px contract changed. 13 F named, all 13 boxed, zero null.
Three actual lower V4 doors have no F record. V3 real lift pair covered by
fixed exclusion X02; distinct classification failure, not lost coordinates.
V4 5/8 correct plus fixed side F09 falsely counted; full fails 9 declared
hinged vs 10 grouped. No observed named-but-unmarked front in this sample.
66 focused tests plus local nullable-box checks; no retries or promotion.
Evidence appended to lev2-strict-islands-trial.json.

LATEST OWNER RETROSPECTIVE / STABILIZATION REVIEW, 2026-11-07:
COMPLETED read-only review, same 3.17.4.6. Owner asked to analyze all work since V7.2 and
recommend a way out of resource/quality instability. Read-only investigation,
no new model calls, prompt/schema/runtime changes or deployment authorized.
Audited original private capsules: 20 paid calls in 10 configurations, one
sample per document/configuration, ZERO exact-request replications. V7.3.1
reused outputs and adds no calls. All 20 use identical source inputs/pixels/
Detection context per file. Total 511306 input /146576 output tokens, of which
77711 thinking. Five responses truncated; counting them as cheap successful
Analyses would be wrong. Full machine-readable audit:
notes/evidence/estimation-v7-2-retrospective-2026-11-07/audit.json.
Verified limits of conclusions: no accepted full physical result or stability
estimate; observed setting differences do not establish deterministic causal
effects. 'Full thinking' was adaptive at effort=low, not max. Bundled V7.3
changed multiple policies; schema pass/fail alone is not visual acceptance.
Prompt hints did not demonstrate saving; shared cap reduces output but can
consume all allowance on thinking. Disabled medium/high give complete cheap
responses and improve Lev1 supports, but neither resolves Lev2 topology.
Repeat defects span settings: source-reading vs physical-role attribution,
door/side/filler identity, repeated wing depictions, tall-column/fridge-opening
ownership, then downstream Blocks grouping. Matching 15-door or 8-block totals
alone does not establish correct physical membership. Existing historical
overlay reviewed for source context, not adopted as ground truth:
/private/tmp/lev2-front-v3-planner-v7-20261106-03-front-overlay-page.png.
INPUT OBSERVATION VERIFIED: Detection narrative already calls Lev1 mark 20
'panel thickness', claims five slat columns and Lev2 chamfer 'at the junction';
normalized inventory separately contains 20->200 mm and 4->40 mm. These
interpretations can conflict with source/owner benchmark. Hypothesis: prior
narrative anchors later estimates. Causation has NOT been isolated; do not
silently edit Detection membership/normalization or declare this the sole cause.
NEXT PROPOSED RESEARCH DIRECTION, PENDING owner approval:
1. Freeze disabled/medium ORIGINAL V7.2 as an economic research control, not a
   production promotion or proven best setting (particularly not for Lev2).
2. Evaluate per-physical-front membership and type with existing source boxes,
   not totals alone; retain fixed-side/exclusion and repeated-view identities.
   Keep numerical reading/unit/physical thickness ownership as a separate issue.
3. First bounded experiment: two additional identical Lev2 disabled/medium
   trials give three samples including the saved one. No changes between them.
   This measures repeatability, not a production three-call/voting pipeline.
4. If the same wrong faces recur, isolate one interpretation/evidence-authority
   issue; if faces vary, diagnose visibility/correspondence and coverage before
   another policy rewrite. Any authority-packet ablation must retain correct
   frozen membership, correspondences and normalized values; seek approval.
5. Only after physical improvement is repeatable, reassess budget and broader
   examples. No new model/extra-stage architecture/schema or speculative paid
   sweep approved by this retrospective. Model/one-call capability ceiling is
   still unknown, not established impossible or guaranteed fixable by prompts.

LATEST OWNER-APPROVED EFFORT SWEEP WITH THINKING OFF, 2026-11-07:
COMPLETED four-call experiment, same 3.17.4.6, P0 acceptance remains PENDING.
Owner explicitly authorizes effort medium then high with thinking=disabled;
this overrides the preceding prompt-only/no-effort-change restriction for this
experiment. Original V7.2 prompt/schema/source/model/max_tokens=14000 retained.
Existing tool adds --revision V7.2-disabled-medium / V7.2-disabled-high. Both
derive directly from the original disabled/low saved control, not from a
modified prompt or the medium output. ONLY output_config.effort differs.
Medium Lev1: end_turn, 14.857 s, 26542 input /3447 output, thinking=0.
Three drawers, two legs (two annotated boxes), two blocks (panel/base, table
with legs). Full structural check hits existing 20 vs normalized 200-mm
thickness mismatch; independent Front/Planner checks pass. V6 Rear remains.
Medium Lev2: end_turn, 18.197 s, 25204 input /4895 output, thinking=0.
Full structural pass; 12 hinged/6 drawers/3 lifts, 6 blocks plus shared top.
Not benchmark 15/5/2 and 8 cabinets. Explicit erroneous 265-mm source-height
prose and excessive block grouping remain. No quality acceptance from schema.
High Lev1: end_turn, 12.854 s, 26542 input /3099 output, thinking=0.
Three drawers/two estimated legs/two blocks. However Description says one leg,
Front says two and supplies no leg boxes, unlike medium. Existing source
thickness mismatch remains; independent Front/Planner checks pass. V6 Rear.
High Lev2: end_turn, 18.149 s, 25204 input /4446 output, thinking=0.
Full structural pass; 15 hinged/3 drawers/0 lifts, 4 blocks plus shared top.
Door total 15 is NOT correct membership: two drawers and both lifts omitted,
separate hanging scope merged, tower fronts unresolved/excluded. Do not call
this benchmark success because one aggregate number coincides.
Low controls: Lev1 10.873 s/2604 output, 3 drawers/1 leg, one block plus invalid
single-owner shared top. Lev2 17.176 s/4742 output: group sums 16 doors/6
drawers/0 lifts (raw totals incorrectly 14 doors/20 total), 5 blocks plus top.
All four new responses end_turn, no thinking blocks and measured zero thinking
tokens. Effort affects the answer even with thinking disabled; no monotonic
quality/latency claim from one sample per file. Useful Lev1 signal: medium
keeps richer supports/annotation at materially less latency than adaptive
thinking control. Neither medium nor high solves Lev2 Front/Blocks.
NEXT RECOMMENDATION, not automatic implementation: do not globally promote
high; use disabled/medium as a Lev1 review candidate, inspect concrete Lev2
Front membership errors rather than increasing effort further.
119 focused tests pass, exact-request/source checks and diff check pass.
Four authorized calls only; no retry/repair/Calculation/DB write/default change,
model switch, main integration, push or deployment. Raw and independent checks:
notes/evidence/estimation-v7-2-disabled-effort-2026-11-07/simple-object-trials.json.
Private full capsules/reports:
/private/tmp/lev[1,2]-v7-2-disabled-[medium,high]-20261107-01.*.

LATEST OWNER-APPROVED DIRECTION / REASONING PROMPT V2, 2026-11-07:
ACTIVE, P0, same 3.17.4.6. Owner explicitly chooses PROMPT-ONLY regulation
of thinking on original V7.2. Do not change schema, boxes, materials, Islands,
Understanding, Front/Blocks requirements, model, effort or total-output cap.
Earlier compact-output, model-switch and additional-call architecture proposals
are NOT approved. V7.3 optimization research stays frozen separately.
Implemented explicit --revision V7.2-prompt-v2 on the existing saved-request
probe. Guidance file: agents/prompts/estimation_v7_2_reasoning_prompt_v2.md.
It is the agreed five-sentence instruction: no separate extended analysis per
section, direct reuse of Detection correspondence/normalized readings, brief
reasoning only for ambiguous fronts/supports, no alternative construction
search/repeated full analysis, same complete JSON without reasoning prose.
Original V7.2 Thinking prompt preserved in full; only this paragraph appended.
Exact request checks verify unchanged messages/pixels/OCR/Detection/schema and
provider settings, including effort=low, max_tokens=14000, no retries.
Two calls completed. Lev1 end_turn/full structural pass: 35.582 s vs 32.040,
26669 input /7734 output, 4119 thinking vs 3488. Three drawers/two legs and
Front 1/2 retained; three assembly blocks instead of control two. Seven ribs
and unsupported 20-mm interpretation remain. Structural pass is not acceptance.
Lev2 max_tokens: 65.417 s vs 64.602, 25331 input /14000 output, 9615 thinking
vs 8352. Lower thinking than first soft prompt (10361), but above original
control and still incomplete. Visible complete Front subobject says 13 hinged,
2 drawers, 2 lifts, 3 unresolved versus owner 15/5/2; Planner cuts off after
three blocks. Complete Front subobject decoded as partial evidence only, with
no document repair or claim of a completed Analyze.
Resource saving against original control NOT OBSERVED in this pair; repeated
samples would be needed to separate wording effects from output variability.
Two qualitative prompt variants now tested without the intended saving; stop
this automatic reword-and-rerun approach, not another cosmetic third trial.
NEXT PROPOSAL, PENDING owner decision: a controlled reproducibility check of
unchanged V7.2 versus this fixed prompt, before attributing variable thinking
length to the wording. No such repeat calls authorized/executed here.
110 focused tests pass, raw replies and exact deltas preserved. No automatic
repair/retry, model/cap/schema changes, DB writes, Calculation, push or deploy.
Evidence: notes/evidence/estimation-v7-2-reasoning-prompt-v2-2026-11-07/simple-object-trials.json.
Private capsules/reports:
/private/tmp/lev[1,2]-v7-2-reasoning-prompt-v2-20261107-01.*.

LATEST OWNER REQUEST / ENFORCED RESOURCE CUT, 2026-11-07, 3.17.4.6:
ACTIVE, P0, usable intermediate-thinking objective remains unresolved. Owner
rejects another wider soft-steering result and requests a genuinely smaller,
faster output. Announced and executed one isolated hard-total-budget pair:
original V7.2 Thinking, max_tokens 14000 -> 5000 ONLY, no Front-soft hint,
no V7.3 changes. Existing tool --revision V7.2-cap5000. Guards require original
prompt/low effort/completed control; exact request/pixels/messages checks pass.
Lev1: 25.147 s vs 32.040; output 5000 vs 6858, thinking 3210 vs 3488.
Actual latency -21.5%, output -27.1%. Text contains Islands/Understanding but
ends inside material assignment, BEFORE Front and Planner. stop=max_tokens.
Lev2: 27.740 s vs 64.602; output 5000 vs 13953, thinking 5000 vs 8352.
Actual latency -57.1%, output -64.2%. ALL generated tokens spent on thinking;
no answer text at all. stop=max_tokens. No completed Front/Blocks to evaluate.
Result: enforced cut demonstrably reduces both measured time and output here,
but does not provide a usable intermediate Analyze or reserve final-answer
space. This is a TOTAL output cap, not a separate thinking-only cap; do not
describe this as successful selective Front reasoning. No repair/retry.
Two calls only, 104 focused tests pass, diff check passes. Source prompt,
default provider route, V7.3 frozen research, main and production unchanged.
Evidence: notes/evidence/estimation-v7-2-cap5000-2026-11-07/simple-object-trials.json.
Private files: /private/tmp/lev[1,2]-v7-2-cap5000-20261107-01.*.
NEXT DECISION: do not stack more shared-output caps or qualitative hints.
To test a dedicated reasoning allowance, changing to a model with a separate
manual thinking budget is a proposal requiring owner approval, not authorized
by this cap experiment. Official legacy extended-thinking docs describe a
minimum 1024 budget_tokens, separate from max_tokens, but call it a TARGET,
not a strict cap; do not promise exact hidden-token enforcement or equal quality.
https://platform.claude.com/docs/en/build-with-claude/extended-thinking
Haiku 4.5 is one documented manual-thinking model; no call/config/model change
has been made. An extra Front model call is another architecture change and
also needs approval. Current one-Analyze/model constraints remain in force.

LATEST OWNER DIRECTION / V7.2 FRONT REASONING CONTROL, 2026-11-07:
ACTIVE, P0, same 3.17.4.6. Owner freezes V7.3 prompt-optimization research
separately and returns to ORIGINAL V7.2 for gradual thinking reduction. The
earlier V7.3.1/2/3 sequence changed normalization/totals/material, NOT reasoning
allowance; it does not answer this objective. Preserve its raw history.
Completed first paired test, V7.2-front-soft trial 01: original saved V7.2
Thinking request plus ONE appended instruction for brief reasoning only on
Front ambiguities (front boundaries/movement/duplicates/legs); other sections
should answer directly without extended deliberation but retain full coverage.
This is prompt steering, NOT enforced per-section isolation or a token cap.
Input/pixels/OCR/Detection/messages/provider settings unchanged. Original
response template INCLUDING model totals and old material defaults retained;
no V7.3 improvements carried into this request. V7.3 files unchanged at 82e4f51.
Lev1: end_turn, full structural pass, 32.934 s vs control 32.040; 26780 input,
7176 output, 3776 thinking vs 3488. Three drawers/two legs and Front 1/2 remain.
Three blocks (base/back panel/top with legs) versus control two, a grouping
alternative requiring review. Seven ribs and 20-mm panel/normalization conflict
remain, material alternatives remain. Passing references does not fix these.
Lev2: max_tokens, 64.443 s vs 64.602; 25442 input /14000 output, 10361 thinking
vs 8352. Visible raw Front totals 17 doors/5 drawers/2 lifts, no unresolved;
these are partial-text observations, not a completed parsed Analyze result.
JSON ends in Planner summary. No reliable full Blocks result, no repair/retry.
Interpretation: resource-saving effect NOT OBSERVED in this pair; quality partly
retained, overall completion lost for Lev2. No proof of a universal effect or
that all internal reasoning was actually confined to Front. Do not call model
adherence or unsupported per-section budget verified. Controls already use low
effort; 'maximum/full thinking' is an informal comparator, not an API maximum.
Two paid calls only. 98 focused tests pass, exact request delta checked, diff
check passes. No Calculation/DB writes/default changes/deployment. Evidence:
notes/evidence/estimation-v7-2-front-soft-2026-11-07/simple-object-trials.json.
Private capsules: /private/tmp/lev[1,2]-v7-2-front-soft-20261107-01.*.
NEXT PROPOSAL, PENDING owner review: contrast the qualitative hint with an
explicit small advisory reasoning target (e.g. 1000 tokens) on the SAME V7.2
control, acknowledging it is still soft guidance, not a guaranteed budget.
Do not rewrite other prompts, silently lower total-output cap, change model or
split Analyze into more calls. Those alternatives require separate approval.

OWNER-APPROVED INCREMENTAL EXECUTION, 2026-11-07, 3.17.4.6, P0:
COMPLETED 7.3.1/2/3 experiments; quality/resource assessment remains ACTIVE.
Owner approved these three stages, then gradual thinking resource experiments.
tools/probe_estimation_v7_2_thinking.py adds explicit --revision selectors,
transforming immutable saved requests, not rebuilding from changed prompt files.
7.3.1: code-only normalization display on saved V7.2 Thinking output; zero
provider calls, exact request/raw reuse. 14 Lev1 /15 Lev2 source measurements.
Inherited output/usage/timing clearly distinguished from new provider work.
7.3.2: ONLY remove Front totals template field and add matching instruction;
code derives totals on a copy, existing validators remain. Two calls, end_turn.
Lev1 49.187 s, 26547 input /10740 output, 6675 thinking: 3 drawers, 2 legs,
Front 1/2, 3 assembly blocks; normalized 200 mm wrongly assigned panel thickness.
Lev2 58.209 s, 25209 input /12909 output, 7372 thinking: 15 hinged, 5 drawers,
2 lifts AND 2 unresolved fronts, 10 blocks plus shared top. Not an exact match
to benchmark despite matching the three main numeric totals. Group membership,
false left tall cabinet and tower/fridge interpretation still need review.
7.3.3: ONLY add unspecified kitchen artificial-stone fallback to 7.3.2 prompt.
Lev1 end_turn, 35.907 s, 26610 input /7720 output, 4267 thinking: 3 drawers,
2 legs, Front 1/2, same three-block scheme. Non-kitchen top remains laminate
30 mm. Seven ribs and guessed 20-mm thickness/source-conversion conflict remain.
Lev2 max_tokens, 68.870 s, 25272 input /14000 output, 11476 thinking. Text ends
inside Front; no completed Front totals or Planner. Stone default appears in
partial material text, not a completed response. No JSON repair or paid retry.
Verified unchanged inputs/pixels/Detection/messages/settings at every step;
only the intended system transformation differs for 7.3.2/3. Resource reduction
is NOT established by one sample per file; thinking variation is substantial.
93 focused tests pass; diff check passes. Four new calls total, no Calculation,
DB writes, runtime default changes, main integration, push or deployment.
Raw/usage/version-chain hashes and summaries:
notes/evidence/estimation-v7-3-incremental-2026-11-07/simple-object-trials.json.
Private capsules/reports: /private/tmp/lev[1,2]-analyze-v7-3-[1,2,3]-20261107-01.*.
IMPORTANT VERIFIED MODEL CONSTRAINT, official docs checked 2026-11-07:
Haiku 5.5 uses adaptive thinking; manual thinking.enabled/budget_tokens returns
400. All saved thinking controls ALREADY use output_config.effort=low, the
lowest supported effort level, not full/max thinking. effort is soft guidance;
max_tokens=14000 caps thinking AND final JSON, not thinking separately.
Sources: https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide
and https://platform.claude.com/docs/en/build-with-claude/effort
and https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost.
Task budgets beta supports Haiku 5.5 but is advisory, minimum total 20000;
not a dedicated small thinking cap. Source:
https://platform.claude.com/docs/en/build-with-claude/task-budgets.
NEXT DECISION: manual small thinking caps are unavailable on this model.
Recommend a separate original-V7.2 control with brief economical-thinking
guidance at existing low effort; this is soft steering, not guaranteed N tokens.
Alternative total-output cap risks truncating JSON as already observed.
Do not silently substitute either for an exact thinking-token budget. No such
additional calls made; obtain owner direction on this changed assumption.

Do not collapse results into a binary contract verdict. Report useful findings,
omissions, reference/arithmetic validity and resource use separately. A validator
error is a technical defect, not proof that all interpretation is worthless;
a structural pass is not proof of visual completeness. V7.3 remains useful
experimental evidence with a faster response, correct stone fallback and
deterministic normalization/totals, alongside substantial scope omissions.
Owner requests incremental adoption of V7.3 changes onto V7.2 instead of
another bundled rewrite. No new paid calls authorized in this planning turn.
EARLIER PROPOSAL, now approved for stages 7.3.1/2/3 above: use saved V7.2 with thinking as quality
control; keep provider settings/pixels/Detection unchanged while introducing
one change per experiment. First code-only normalization display (no call),
then code-owned Front totals with only matching schema/instruction changes,
then kitchen-material default, then one redundant prompt section at a time.
Evaluate quality/resources after each step; retain or roll back attributable
changes only. Test thinking reduction separately after the prompt changes,
not simultaneously. New runs must be explicitly approved; no stability claim
from one output per file. Preserve both old baseline variants and V7.3 raw data.

Owner approved unified concise Analyze, code-derived totals and normalization,
material defaults and explicit Front/Blocks boundaries, followed by Lev1/Lev2
without thinking. agents/estimation_analyze_v7_3_agent.py and its single prompt
are opt-in through existing probe --revision V7.3. Old versions/defaults stay.
Prompt 11657 characters versus V7.2 22369. Only system differs from the V7.2
disabled-thinking requests: identical messages/pixels, Detection context,
model/settings/max_tokens=14000, timeout=120, SDK retries=0. This is a bundled
prompt experiment, not isolation of each individual policy improvement.
Raw front omits totals; code derives them without changing groups/boxes and
validates the enriched copy with existing gates. Raw response stays immutable.
Code normalization display copies original_text/unit_basis/value_mm and saved
unit provenance, including image-only islands; no new unit heuristic.
Lev1: end_turn, 7.773 s, 23025 input /1797 output, zero thinking. Full rejection:
20-mm specified thickness references Detection 200 mm. Three drawers, one leg
despite seeing a second; V6 remains Rear; five-to-seven ribs; unresolved
material alternatives. Independent Front format passes; Planner fails shared
element with only B01. One block plus full-image shared-top box, not accepted.
Lev2: end_turn, 9.454 s, 21687 input /2456 output, zero thinking. Full STRUCTURAL
pass, semantic failure: 7 hinged, 3 drawers, 0 lifts versus 15/5/2. Three blocks
plus top, extensive omitted scope, V4 Side not Front 2. Worktop wrongly shared
with tall B03; its bbox covers whole image. Raw prose still gives source 265
without normalized unit; Characteristics omit material assignments/finishes.
Kitchen artificial-stone default 30 mm is correctly returned in materials.
Reduced prompt/latency/output did not preserve thinking-control Front quality.
Keep V7.3 rejected and isolated; do not use it as next quality checkpoint.
The V7.2 thinking control remains a fallible comparison, NOT accepted fallback.
Production checkpoint V5.8.2 and protected research checkpoints unchanged.
86 focused tests pass; diff check passes. No DB writes, extra calls, retries,
Calculation, main integration or deploy. Raw evidence and exact comparisons:
notes/evidence/estimation-v7-3-2026-11-07/simple-object-trials.json.
Private files: /private/tmp/lev[1,2]-analyze-v7-3-20261107-01.{json,raw.txt,html}.
NEXT RECOMMENDATION, not authorized: isolate Front reasoning/resource control
against saved V7.2 thinking evidence after checking supported model settings;
do not try another broad prompt rewrite or add automatic paid retries.

OWNER-APPROVED CONTROLLED THINKING REPLAY, 2026-11-07, same 3.17.4.6:
COMPLETED experiment, P0 quality/acceptance remains PENDING. Exactly two
authorized provider calls, no retries: tools/probe_estimation_v7_2_thinking.py
replays each saved request with only thinking={type:disabled} removed, matching
historical provider-default configuration. Verified identical system/messages,
inputs, pixels, Detection context and all other request fields. Actual thinking
blocks present in both responses. Production agent/defaults remain unchanged.
Lev1: end_turn, 32.040 s vs 10.873; 26543 input /6858 output, 3488 thinking.
Front now 3 drawers/two legs; V6 Front elevation 2; Planner two valid blocks,
no invalid shared top. Independent Front/Planner contracts pass. Full output
fails foreign Understanding source refs (island IDs used as source refs).
Still seven slats instead of owner's six; 20-mm inference ignores normalized
200 mm, falsely treats cm-to-mm conversion itself as a source conflict.
Lev2: end_turn, 64.602 s vs 17.176; 25205 input /13953 output, 8352 thinking.
Full structural validation passes, but semantic acceptance FAILS: 17 hinged
instead of 15, correct 5 drawers (2+3) and 2 lifts. Eight blocks plus worktop
does NOT match owner's eight-block topology: upper lift/corner merged, false
left tall unit, fixed tall side instead of doors, missing fridge-opening scope.
Raw prose still uses unnormalized source numbers; laminate worktop remains
because changing this default was intentionally excluded from this experiment.
No causal stability claim from one sample per object; thinking helped selected
outputs at roughly 3x/3.8x latency and 2.6x/2.9x total output tokens. No
automatic rerun or V7.3 implementation. Next: owner reviews these outputs,
then choose V7.3 policy/configuration. 75 focused tests and diff check pass.
Tracked raw replies, usage, exact-request checks and independent validators:
notes/evidence/estimation-v7-2-thinking-2026-11-07/simple-object-trials.json.
Private full capsules: /private/tmp/lev[1,2]-analyze-v7-2-thinking-20261107-01.*.

Owner requests analysis and a reuse recommendation before another change/run.
Name comparison in actual capsules: first V7 "Slat back booth seat" (4 words),
V7.2 "Slatted Bench Seat" (3). Owner accepts the latter Description generally;
the phrase about protruding from the seat side is unclear, physical leg count
must remain two. Combined Lev1 veneered structure/base is an acceptable block.
Stable kitchen-top, material default and detailed Lev2 benchmark decisions
recorded in existing ESTIMATION_V5_1_CABINET_BLOCK_CONTRACT_2026_11_03.md,
section Current owner clarifications: 15 hinged, 5 drawers (3+2), 2 lift-up,
preferred 8 cabinet blocks + one shared worktop. No benchmark counts in prompt.
Add code-rendered normalization provenance to Islands, using saved Detection
values, not another model unit decision. Source example 265 -> 2650 mm.
[verified] V7.2 already loads policy sections from CB Front V3 / Planner V7;
no missing-file explanation for the regression. Front V3 differs from V2 only
by heading and a lower-drawer reading paragraph. Planner V7 already includes
V4 rules plus worktop localization/extent and tall-leaf limits from V5/V6.
[verified] Better historical control: Front V2 (036afd8), Lev1 two distinct
legs and 3 drawers (enum fail), Lev2 15 hinged +2 unresolved /5 drawers/2 lift-up
(format pass). Later exact-request repeats vary: 18 hinged, and a control drops
one wing. Do not call this stable perfect recognition.
[verified] Planner V3 (695e376) gives 9 cabinet blocks +top but duplicate F24
assignment; V4 (e8bcf5c) gives 10 +top and better full-height column grouping,
yet false tower/incomplete scope; V7 reviewed snapshot gives 9 +top with bad
boxes and two of three planners truncated. Old good grouping is useful partial
evidence, not a ready fully accepted model to restore wholesale.
NEW MATERIAL CONFIGURATION DIFFERENCE, verified from actual saved requests:
historical Front V2 request did not disable thinking; response used 3448
thinking tokens. Front V3 control used 4297; Planner V4 used 3615; Planner V7
completed control used 3783. V7.2 explicitly thinking=disabled, zero thinking.
Thus policy text reuse did NOT reproduce historical request conditions.
Combined tasks/context also differ. Causal contribution not isolated.
RECOMMENDATION, not yet implemented: use Front V2 and Planner V4 as historical
controls; retain justified V3 lower-drawer and V5-V7 top/column rules, without
whole-response prompt stacking. First isolate the thinking setting on the
unchanged V7.2 request before attributing the regression to those rule versions.
Then revise only the demonstrated gap; maintain one Analyze/document and one
Calculate/object. New material default/provenance display are accepted scope,
but no automatic provider call authorized in this analysis-only turn.

Owner approved full first-call output now: Islands, Description,
Characteristics, CB Front and CB Planner Blocks, then one saved Lev1 and
one saved Lev2 trial. This supersedes the earlier Island-Map-only scope.
Terminology: CB Planner -> Blocks in Analyze; Calculation/CB Parts -> Parts.
Decision: reuse saved Detection normalized measurements and unit provenance;
do not implement 80-percent/200 heuristic. Reuse established membership and
correspondences; resolve only concrete conflicts, no new pairwise proof.
Implementation: opt-in agents/estimation_analyze_v7_2_agent.py and
estimation_analyze_v7_2.md / estimation_analyze_v7_2_output.json. Reuses existing
CB Front V3 and CB Planner V7 policy sections with ONE explicit outer response
template; validators are existing validate_front_count/validate_assembly_plan.
V7.2 reuses prior input preparation/pixels; new numbered front elevations,
mandatory sheet thickness/kind, optional source thickness measurement ID,
strict equality against Detection value_mm. Source export opt-in adds
dimension_inventory, unit_context/provenance and dimensional correspondences.
Existing V7 and earlier selectors/prompts remain available and unchanged.
CLI: tools/probe_estimation_analyze_v7.py --revision V7.2 --execute.
Exactly one Haiku 5.5 call per file, low/thinking-disabled, max_tokens=14000,
timeout=120, SDK retries=0. Front and Planner are sections, not extra calls;
Calculation/Parts not invoked, no DB writes, no new Detection or render.
Both end_turn, same prompt SHA256:
53b65a011c7e06e915a64b5258032e4cedade6143b2ea0b95876adc1724d446e.
Lev1: 10.873 s, 26542 input / 2604 output tokens. Full validation fails:
20 mm source thickness cites view-005-D001 which is 200 mm in Detection.
Independent Front contract passes (3 drawers, 0 hinged, 0 lift-up); one leg
still chosen despite explicitly seeing two. V6 remains Rear view, five slats,
material alternatives and 17-mm worktop remain. Planner contract fails:
shared S01 references only B01; actual list one block + one shared element,
despite summary claiming three blocks. No automatic repair/normalization.
Lev2: 17.176 s, 25204 input / 4742 output tokens. Full/Front validation fails:
groups sum to 16 hinged +6 drawers =22; raw totals say 14 +6 =20. Lift-up=0.
Owner benchmark 15/16 hinged, 5 drawers, 2 lift-up not met. Planner references
pass independently: 5 blocks + shared worktop, all 22 F IDs assigned once.
This does not establish grouping quality: base runs overgrouped; worktop box
is the full axonometric island; tall fronts excluded rather than resolved.
Numbered front views and worktop-stop description improved in this sample;
refrigerator opening/material finish differentiation remain incomplete.
Both outputs semantically not accepted; no reruns, retry or promotion.
Tracked raw/usage/independent section checks:
notes/evidence/estimation-v7-2-2026-11-07/simple-object-trials.json.
Private capsules/raw/HTML: /private/tmp/lev[1,2]-analyze-v7-2-20261107-01.*.
Inputs, source pages and every actual image block match V7 byte-for-byte.
Local focused suite 73 passed; git diff --check passed. This verifies contracts,
reference protection and raw preservation, not visual acceptance. Keep old
research checkpoints protected; V7.2 is an opt-in rejected experiment, not a
replacement checkpoint or deployment. Next: owner review of the displayed
outputs; no speculative paid follow-up authorized by these failures.

Analyze accepts Detection membership and reuses established island relations;
it does not redo membership/pairwise proofs or emit a second merge rationale.
Resolve only concrete conflicts encountered while interpreting the item.
Owner asks what Calculation/CB Parts should receive once assembly blocks exist.
[verified] build_detection_v5_dimension_fingerprints stores per-island numeric
occurrences with original_text, value_mm, unit_basis, occurrence_id, source
fact refs, local bbox and ambiguity slot. compile_detection_v5_dimension_graph
matches occurrences within 2 percent, scores size/precision/rarity/repetition
and produces supporting relations; it does not assign block/part W/D/H.
[verified] Saved Lev1 and Lev2 audits ALREADY infer effective unit cm, reason
nonstandard_100_to_600_value. Explicit document-unit profile remains unknown.
Lev1 inventory includes 4 -> 40 mm, 20 -> 200 mm, 72 -> 720 mm;
Lev2 includes 416 -> 4160 mm, 300 -> 3000 mm, 151 -> 1510 mm.
The current V7 exporter passes hypotheses/observations/OCR maps but omits
dimension_inventory and effective unit profile/reason. This is a confirmed
handoff omission; not proof that delivering it alone fixes physical ownership.
The proposed 80-percent/below-200 unit heuristic is not implemented and must
not become a competing scale authority before reconciling this existing policy.
AGENT RECOMMENDATION for V7.1, not yet implemented: reuse the same source
measurement inventory/scale provenance in Analyze and Calculation; normalized
values should be copied/resolved by code instead of re-converted by the model.
Parts receives per-object frozen assembly blocks/front topology/material
assignments, linked source islands/images/OCR and indexed measurements, plus
only relevant cross-island correspondence/measurement refs and conflicts.
Full Detection comparison scores, rejected alternatives and membership-proof
prose stay in the audit, not repeated as a Calculation task. Block ids and
scalar dimensions alone are insufficient to recover internal geometry.
Dimension correspondence is supporting evidence, not guaranteed same-part
identity. Analyze need not bind every internal panel dimension; Calculation
assigns relevant source measurements to parts within fixed block scope.
Current source inspected: ordinary Calculation already receives scope/images/
OCR/Estimation Dimension Graph; experimental Parts V3.3 reuses saved Front/
Planner and source images, V4.1 additionally uses measurement packet. None is
implemented V7.1. Preserve one shared Analyze then one Calculation per object;
no extra per-block model call proposed. No prompt/model/runtime change here.

Owner accepts Lev1 projection classification broadly, but requests neutral
numbered front elevations when front/back or wings are not meaningfully
distinguishable: Lev1 V4/V6 and Lev2 V3/V4. Keep genuine profile projections
distinct; representation changes must not alter Detection membership/IDs.
Lev1 supports: two physical legs, visible jointly in V3 and V6. Owner counts
six internal ribs excluding side walls; previous five/seven model counts are
not accepted. Required Characteristics for every sheet-material role: chosen
material, finish/coating/colour and thickness, including distinct finishes
within one object. Use explicit source or labelled estimation/default; no
unresolved material alternatives or unmarked assumed species (oak was example).
Owner requests trial scale heuristic with tunable thresholds: if >80 percent
of known dimension values are <200, assume centimetres. Exact input population,
handling of explicit units/thicknesses/details/mixed-scale drawings and safe
precedence remain to be specified; furniture plausibility is not universal
proof of units. No numeric implementation has been made in this review turn.
Lev2: worktop ends before the full-height cabinet; 45-degree cut is at one
terminal end, not the wing junction. Identify the refrigerator opening and
include material assignments in visible Characteristics. Next version requested
within Estimation V7 (V7.1 candidate label); no new work/block number assigned.
IMMEDIATE REQUEST: first show exact Detection relationship grounds received by
both trials, before another implementation/model run. Inspected actual request
capsules: Lev1 has five observations (three matching_topology, two
unique_geometry) covering six islands; Lev2 has two matching_topology facts
covering three technical islands plus one validated render-to-plan attachment.
Payload also includes the original accepted hypothesis_reason, source aliases,
exact OCR mappings and images. No material specification is established by
these relationship observations. Detection already mentions one visible leg
in V1 and two in V3, five slat columns, 20 as panel depth/thickness, and Lev2
45-degree junction: these are prior model claims, not guaranteed source facts.
Detection observations do not append mm to the bare 20/416/300 readings;
the erroneous explicit mm conversion appears in Analyze's returned result.
Show these raw grounds with provenance and distinguish them from later
Analyze claims. No new model calls or prompt changes in this review turn.

Owner explicitly approved sending saved images/OCR/Detection context through
the configured paid API, then selected Lev1 and Lev2 before complex Ada.
Prior automatic approval blocker is resolved for these two calls; Ada was
not executed. Stable output terminology: Island Map produces Islands
(objects[].islands); Description is description, Characteristics is
characteristics, short item name is name. Existing technical IDs retained.
Extended saved-context export to exact SF-to-OCR block_ref mapping using the
original OCR event and validated presentation-render attachment decisions.
Read-only snapshot fetched existing Detection/OCR events, no Detection rerun:
/private/tmp/lev1-lev2-detection-context-v7-20261107-01.json.
Lev1 event 50354659-58dd-4f57-8efe-f61c38d3e395, six islands, seven images;
Lev2 event 8fd1c7f0-2f36-42bd-b7ae-537460324445, four islands, five images.
Exactly two Haiku 5.5 calls, low effort, thinking disabled, zero SDK retries,
one per file. Both end_turn. Same system prompt SHA256:
130f027bf93cde9577a17d2c4007406592f9a2098090dd6cc936f328e8043098.
Lev1: 8.347 s, 17480 input / 1769 output tokens. Contract FAIL: four-word
name. Raw also contains unconverted SF refs, one leg despite a second leg in
its own island observations, 20 mm thickness, 4 mm offset, conflicting slat
counts, non-thickness dimensions and unresolved/null material defaults.
Lev2: 7.945 s, 15859 input / 1704 output tokens. Structured contract PASS;
semantic NOT ACCEPTED: 416/300 called mm, corner-cut ownership wrong,
detached hanging unit not explicit, invented 18-mm facade default and
laminate/stone material alternatives. Non-thickness numerical output persists.
Neither semantic result accepted. No automatic retry, prompt repair or
downstream calls. Responses preserved before validation; failed-contract HTML
can display original parsed content with an explicit FORMAT FAILURE warning.
Final focused verification: 61 tests passed; git diff --check passed.
Tracked raw/usage/hash/review evidence:
notes/evidence/estimation-v7-analyze-v1-2026-11-07/simple-object-trials.json.
Private capsules/raw/HTML: /private/tmp/lev[1,2]-analyze-v7-v1-20261107-01.*.
These private capsules have not been included in a requested backup archive.
Not a controlled V1/V2 comparison: enrichment, global island labels and output
contract changed together. Repetition of Detection mistakes suggests an
influence hypothesis, not established causality. Next proposal: owner review
of the exact outputs, then isolate inherited observation influence before
another paid prompt revision. No deploy/main integration, full Analyze,
Front/Planner/Components/Parts acceptance claimed.

Owner approved local V7 Island Map + Understanding implementation and one
test on the saved Ada two-object Detection witness. Front/Planner/Parts are
subsequent sections; Components remains a separate design/validation topic.
Output clarification: table of island/projection/content-role, short item
name, critical bullet points, later Front counts and assembly-block list.
Existing names retained: CB Planner creates blocks inside Analyze; CB Parts
decomposes them inside Calculation. Lift-front count and gas-lift kit count
remain distinct (deterministic hardware policy).
Implemented opt-in agents/estimation_analyze_v7_agent.py with one shared
document call, prompt estimation_analyze_v7.md, seeded extensible 17-code item
type catalog, strict object/island/source-ref validation and raw-before-parse.
use_cases/estimation_detection_context_v7.py exports accepted normalized
hypotheses/observations and raw-ID aliases from saved event audit; currently
supports hypothesis-review route explicitly, not every Detection route.
tools/probe_estimation_analyze_v7.py prepares locally by default; --execute
enables one Haiku 5.5 low/thinking-disabled call with max_retries=0, 120 s
timeout, 12000 output ceiling. Saves private capsule/raw/HTML; no DB write.
Source witness verified: run_4e47c1226af946698779203ca31ff705,
event b5d218b9-ccee-4c58-8c62-d144be246381; object-001 V2/V3/V5/V7,
object-002 V1/V4/V6/V8. Six accepted observations, two accepted hypotheses.
Local preflight /private/tmp/adda-analyze-v7-v1-preflight-20261107-02.json:
two objects, eight islands, four unchanged source pages + eight labelled crops.
Initial preflight exposed portrait page-profile frame vs rotated Ada pixels.
V7 now uses the saved Detection mistral_page_dimensions frame 2339x1654
explicitly, through optional visual-helper args; original inputs untouched.
All eight actual request crops visually inspected. No inferred rotation or
replacement PDF render. Full-page context and nearby other-object fragments
remain visible; locked membership and labelled source IDs define scope.
Verification: 58 focused tests passed (V7, existing visual evidence,
Understanding V1/V2, module-understanding routes); git diff --check passed.
Tests cover exact/ambiguous ID mapping, run isolation, raw capture before
rejection, one call/no retries, foreign refs and explicit Detection frame.
EXECUTION BLOCKER: automatic approval review rejected the API command before
process launch, requiring explicit approval to send images/OCR/Detection
context to the configured provider using credentials and incurring API cost.
No live model call or model response occurred. Do not bypass this rejection.
Await that approval for exactly one document-level Haiku 5.5 trial on both
objects. Semantic quality remains unknown. No deploy or main integration.

Owner explicitly names the next product iteration Estimation V7 and focuses
current work on Analyze / Understanding. Existing work reference 3.17.4.6 is
retained for continuity; no new hierarchical major/block number assigned.
Use stable names: Analyze is the first document-level call containing Island
Map, Understanding, CB Front and CB Planner; Calculation is the second,
per-object call containing CB Parts. These are logical sections, not separate
mandatory provider calls. Components are physical elements in Understanding;
Planner groups them into practical assembly blocks. Preserve that distinction.
Understanding requirements: concise item type/name (1-3 words), followed by
the critical whole-object characteristics, layout, separate assemblies,
supports/openings and major material/finish/thickness assignments, especially
fronts and visible sides. Interpret all owned islands jointly with OCR,
legends and cross-island observations. Distinguish specified/inferred/default.
Owner requests an extensible item-type catalog: prefer an existing code; on
no suitable match preserve a proposed type for review rather than force a
wrong category. Search found no such catalog in the inspected Estimation path.
No automatic catalog expansion or proposed-type promotion has been approved.
Island Map terminology is established; technical fields remain island_types,
view_id and known_views. Existing enum has nine projection types and excludes
render/context/detail roles. Proposal: distinguish projection from content
role, since a rendered image or component detail can also be axonometric.
Do not silently expand enums or rename persisted identifiers.
[verified, source inspection] Detection records positive_relation_edges,
accepted_merge_edges, reference_links, rejected_relation_candidates and
semantic_ledger_audit in diagnostics, persisted before File Review. Its schema
has dimension_equality/dimension_transform plus explicit_document_relation,
matching_topology/unique_geometry/direct_shared_structure; the additional
visual_dimension_similarity is route-specific. Do not require all criteria
to be present on every accepted edge.
[verified, source inspection] build_estimation_input does not carry this
relationship audit; _page_refs retains page/label/regions only, _page_manifest
projects object fields, and prepare_content forwards images/manifests/OCR.
Dimension Graph creates local pN-view-NNN IDs from regions. P0 dependency:
design and implement a bounded Detection-to-Analyze relationship handoff with
source event/version, original island IDs and explicit local-ID mapping,
accepted evidence observations/reference links and relevant conflicts.
Owner requests this contract gap be addressed if confirmed. Start from the
persisted Detection audit; no Detection grouping/model change is implied.
Current iteration is inspection and contract discussion. Runtime, catalog,
prompt, DB and production changes are pending a concrete reviewed contract.
Agent correction: the preceding chat's proposal to move every dimension
binding into Analyze was not an owner-approved requirement. Keep the exact
Analyze/Calculation geometry boundary open while structuring Understanding.
FOLLOW-UP, USER REQUEST, 2026-11-07: prepare V7 using successful saved
Detection runs, without deployment. Components needs separate design and
validation; prior useful kitchen Planner grouping is not general acceptance.
CURRENT QUESTION: how Detection should supply relationship justifications.
[verified] Existing tools/probe_v62_lev2_detection.py already constructs
upstream_grouping_context with detection_event_id, exact view_id_mapping,
source_fact_mapping, object_hypotheses and presentation_render_decisions,
then explicitly appends it to the diagnostic request. Private witness:
/private/tmp/estimation-v6-2-lev2-detection-01.json, run_189150ebf62447fc958f7c23cc34e3bb,
event 8fd1c7f0-2f36-42bd-b7ae-537460324445: four mapped islands, 18 mapped OCR
facts, two matching_topology observations and one attached render decision.
Correction: relationship transport is absent from the common handoff and
latest standalone route, not from every historical Estimation diagnostic.
[verified] Ada saved snapshot /private/tmp/adda-saved-replay-20261106-01/
saved-detection-snapshot.json retains event b5d218b9-ccee-4c58-8c62-d144be246381
and review/proposal/registry/semantic audit; accepted_merge_edges is empty.
An edges-only exporter would therefore lose successful hypothesis-based proof.
AGENT RECOMMENDATION, contract pending review: extend the existing upstream
grouping context into a versioned object-scoped handoff derived from final
Registry membership plus its route-specific validated proof/audit. Retain
original observations and IDs, explicit local-ID/OCR mapping, event/run/version
and content hash, render attachments and reference links. Keep accepted,
rejected/unknown and model-authored observations distinguishable; no inference
of source truth from merge acceptance. Store full audit privately; provide
bounded relevant observations to Analyze without another model summary call.
Validate exact mapping, same-run/object scope and all referenced witnesses;
missing/ambiguous mapping is explicit, never nearest-box guessed or silently
dropped. Do not require graph connectivity of accepted_merge_edges when the
route establishes membership with validated hypotheses or render attachments.
Next implementation: local export/validation on saved Lev2 and two-object Ada,
then attach to the experimental V7 Analyze input. No new Detection/model call,
DB mutation or deployment is required for this validation stage.

OWNER-REQUESTED HANDOFF UPDATE completed, 2026-11-06:
Existing ESTIMATION_V6_FULL_CHAT_HANDOFF_2026_11_06.md reconciled through V1/V2,
including sections 34-35, raw-evidence paths, exact V2 prompt, commits, measured
comparison and non-acceptance. Stale current/restart statements corrected.
Documentation only; no further call, prompt change, new acceptance or deploy.
LATEST APPROVED EXPERIMENT, Understanding V2, 2026-11-06:
Owner approved the bounded focus-only change: no non-thickness sizes in the
answer, focus on construction/materials/supports and visible leg count.
understanding_v2.md preserves V1 except the heading and one added paragraph.
--understanding-v2 is opt-in; V1 and all established routes remain available.
One Haiku 5.5 call per saved V1 packet: Lev1 6.044 s, Lev2 6.263 s. Only system
differs; exact inputs/pages/messages/settings preserved. No downstream calls.
Lev1 now has two legs and explicitly no upholstery, but its title still says
Upholstered-style; 20 is again wrongly assigned as 20 mm top/back thickness,
and the 4 cm rib evidence is missed. Lev2 still invents/overstates features
(glazed-looking front, between-wall installation) and leaves material options.
Both exceed the two-sentence description limit. Neither is semantically
accepted; one run each cannot prove improvement or stability. No promotion.
Evidence: notes/evidence/understanding-v2-2026-11-06/simple-object-trials.json.
NEXT, P0, PROPOSAL, not authorized execution: stop broad prompt polishing;
inspect exact saved image payload for recurring Lev1 thickness failure, then
isolate source-value/element/unit attribution in a bounded diagnostic.
This does not add a production call or implement Understanding V3.
PREVIOUS APPROVED EXPERIMENT, Understanding V1, 2026-11-06:
Owner reviewed the mixed V5 prompt and approved running the replacement text
shown in chat. Saved verbatim in agents/prompts/understanding_v1.md, separate
version lineage, not a rewrite of the failed CB Cycle V5 prompt. Existing probe
--understanding-v1 makes one prose-only Haiku 5.5 low/thinking-disabled call.
No inherited Front schema, JSON demand, Planner, Calculate or new production
stage. Defaults and exact prior prompt hashes preserved. Raw text saved before
review, not silently converted to a successful structured interpretation.
Lev1 5.291 s and Lev2 5.164 s, one each, end_turn. Inputs/pages/messages and all
request settings unchanged versus their V5 baselines; ONLY system differs.
Lev1 retains three drawers but invents upholstery, one leg instead of two,
cm-scale dimensions as mm, and wrong source-thickness attribution. Lev2 names
the main kitchen elements and 17/30 mm defaults, but exceeds two sentences,
misstates chamfer/layout and leaves some material choices unresolved.
Both readable, neither semantically accepted; no automatic retry or promotion.
Evidence: notes/evidence/understanding-v1-2026-11-06/simple-object-trials.json.
The proposed focused Understanding V2 was approved and tested above; removing
numerical geometry did not resolve the source-thickness interpretation failure.
The earlier merged-schema proposal below is paused by this standalone trial;
document-wide Analyze/Front/Planner integration and final Parts remain pending.
OWNER-REQUESTED FULL CHAT HANDOFF completed, 2026-11-06:
notes/ESTIMATION_V6_FULL_CHAT_HANDOFF_2026_11_06.md preserves the full V6.1/V6.2
experiment history, current raw Understanding prompt, benchmark corrections,
accepted approximations, failed trials and exact checkpoint/recovery identities.
Latest discussion names the block Understanding. Island Map -> Understanding ->
Front -> Planner is the proposed logical Analyze order, NOT four model calls.
Planner currently consumes Front, so moving Front after it is not implemented.
Separating the prompt sections/one explicit response schema remains a proposal;
no new prompt, paid replay, runtime promotion or deployment in the handoff turn.
LATEST OWNER DECISION: restore explicit whole-object understanding as the
foundation of the next experimental cycle, V5. Implemented as CB Cycle V5,
NOT a product-major rename and NOT replacement of historical CB Front V5 or
CB Planner V5 prompts. Product remains Estimation V6.2, same work 3.17.4.6.
One existing first-stage call now emits Understanding + Front (V3 rules): short
whole-object and construction descriptions, physical components, view evidence,
cross-view links, uncertainties, front/support-to-component mappings. Planner
(V7 rules) consumes that SAME interpretation and maps components to blocks.
Missing/reparented references are rejected. Interpretation conflicts stay
visible and block Calculate; structural checks do not certify visual meaning.
Calculate keeps frozen Front/Planner scope and the V3.3 parts compiler, with the
same understanding attached. V4/V4.1 independent regrouping is disallowed here.
Experimental CLI switches --cycle-v5, Parts additionally --parts-version V3.3.
No extra understanding call: current diagnostic count remains Understanding+
Front, Planner, Calculate, three calls per object if all stages proceed. This
is NOT the original target of one Analyze for the document plus one Calculate
per object. Document-wide batching/combined Analyze and live UI are pending;
do not imply they are implemented. Material hypotheses are not a resolved
project palette; dimension association/volatility remains unresolved.
423 focused tests pass. One Ada first-stage call, 10.415 s, complete provider
reply but FAILED schema and semantic review: the scoped counter is combined
with the separate L-shaped display, and Front is a flattened group rather than
the required container. Planner/Calculate NOT called; no repaired response,
retry, promotion or deploy. The explicit description exposes the scope error,
but reference validation alone cannot automatically detect semantic merging.
Raw witness: notes/evidence/cb-cycle-v5-2026-11-06/adda-object-001-trial.json.
SIMPLE-FILE TRANSFER, owner requested, 2026-11-06: unchanged V5, one first-stage
call each on saved Lev1 and Lev2 evidence, 8.760 / 8.327 s. Both end_turn replies
FAILED the Front schema. Lev1 describes three drawers but supplies no Front
rows/boxes and dangling F01-F03/T01 mappings. Lev2 returns empty groups and null
counts. No Planner/Calculate, repair, retries or production changes. Inputs,
pages and prepared request evidence match their replay sources exactly.
Raw evidence: notes/evidence/cb-cycle-v5-2026-11-06/simple-object-trials.json.
NEXT, P0, PROPOSAL: replace the competing inherited/outer response descriptions
with one explicit merged output schema, then repeat the same simple inputs.
Prompt composition is a hypothesis, not a proven cause; this test establishes
that failure is not specific to Ada complexity. Whole-object semantic quality
also remains unaccepted. Ada scope presentation (full pages contain both objects,
no detail crops) remains a separate untested hypothesis. Preserve full-page
legend/context and unchanged Detection membership. Earlier isolated measurement
proposal below is deferred while the owner prioritizes whole-object understanding.
PREVIOUS OWNER DECISION: name the next contract CB Parts V4 (not V3.x and not
an Estimation product-major rename). Try geometry before workshop grouping,
then the measurement-preparation direction. Worked-example teaching is not
selected. This remains the same sized material-bearing parts objective.
V4 IMPLEMENTED, EXPERIMENTAL / NOT ACCEPTED: one Calculate call from saved Front
and unchanged complete source context; old Planner groups/boxes are not consumed.
Model describes physical runs/columns, reusable dimensions and weighted bays,
then assembly groups and a material palette. Code derives widths and front
heights before grouping, reuses the V3.3 carcass compiler and existing assembly
BOM builder. Final parts retain IDs, role, quantity, face size, thickness and
material; stock layers multiply sheet area, not finished part count. Explicit
worktops, frame members and supports stay separate. No full template library.
Three unchanged-prompt Haiku trials, no retries or manual repairs: Lev2 12.983 s,
Lev1 8.706 s, N68 12.203 s. All complete provider replies, all rejected. Lev2
omits 9/24 input front IDs and still assigns 151 cm to a whole partial-width
run. Lev1 turns three adjacent drawers into a vertical stack, uses mm for the
centimetre-scale drawing and supplies foreign material refs/zero support stock.
N68 retains only 5/18 input fronts, uses an implausible mm-scale kitchen and
claims a drawing dimension without its label. Evidence:
notes/evidence/cb-parts-v4-2026-11-06/three-object-trials.json.
283 relevant tests pass; full visual/material objective 0/3 accepted. Stop
V4 prompt variants. This combined new contract is not a single-factor proof
that geometry-before-grouping caused these failures or can never work.
Limits: current saved Analyze has no project material palette, so V4 interprets
materials in Calculate for this diagnostic; integrated Analyze and project
palette are pending. All geometric/material claims remain unverified, not 2VN
certified. Finish/edge intent retained, separate consumable demand not compiled.
Direction 2 IMPLEMENTED / TESTED, CB Parts V4.1, same 3.17.4.6, NOT ACCEPTED.
Reuse existing Dimension Graph/evidence-map raster extraction and scale policy,
filter line candidates to two supported endpoints/one nearby numeric label,
map coordinates to the exact Front detail image including padding/header.
Source dimensions are references only; code copies values and units. Explicit
estimates remain separate. Same-view interval contradictions are rejected, not
silently repaired. No extra model call; original images/text remain unchanged.
Important limit: raster lines and Front boxes are candidates, not ownership
proof; source scale is a cm estimating convention, not printed-unit evidence.
N68 extraction reports truncation; absent candidates are not proof of absence.
Three unchanged-prompt trials, one Haiku call each, no repair/retry: Lev2 8.445 s,
Lev1 10.168 s, N68 14.628 s. Source references valid 26/26 with code-owned values,
but whole-object acceptance 0/3. Lev1 now has 1580 x 430 x 720 base geometry and
three adjacent drawer bays; still replaces ribs by a panel and assigns 1150 mm
to leg diameter, with invalid material provenance/zero support stock. Lev2
retains only 11/24 fronts and includes F18/F19 outside its selected 1510 span;
also extra estimate field. N68 retains 13/18 fronts, assigns plan dimension
1820 to base height, leaves two bays ungrouped and uses an invalid material basis.
325 relevant tests pass, not visual acceptance. Original replies, measurement
packets, source-reference and coverage audits:
notes/evidence/cb-parts-v4-1-2026-11-06/three-object-trials.json.
Stop full-contract prompt retries. The new evidence shows numeric transport
works, but the model still misassigns physical ownership and drops known parts.
NEXT PROPOSAL, P0, NOT APPROVED: isolate source-span-to-existing-section binding
with the new independent measurements and fixed topology, without materials or
parts generation in that diagnostic. This differs from V3.5, which lacked the
independent endpoints and copied unit conversion. It is a diagnostic proposal,
not approval for a new production stage. Integrated Analyze/project palette,
complete acceptable parts and repeatability remain pending. Main, production,
ordinary selectors and protected V3.3 research checkpoint remain unchanged.
Ada transfer check, USER REQUEST, P1, PENDING within this objective: replay
Front/Planner on a correctly grouped multipage two-object Adda package before
further Parts changes. Located protected run run_4e47c1226af946698779203ca31ff705;
DB confirms two objects, four pages each, no persisted Estimation inputs.
Prepared local inputs via the existing HSL build_estimation_input path using
saved Detection/OCR and source-hash-verified PDF, unchanged membership, no DB
writes. Private capsule: /private/tmp/adda-saved-replay-20261106-01.
V5 ran one first-stage call on object-001, failed as recorded above. Each input
has four full-page images and no detail crops; verify visual scope/transport.
Owner approved returning to explicit whole-object understanding within the
first existing call, not a separate extra production stage. Existing protected
pair/defaults remain unchanged; V5 is opt-in and unaccepted.
Earlier approved diagnostic: CB Parts V3.5 freezes bay/front membership
from the original first V3.3 reply, withholding all its dimension estimates.
Same complete Lev2 evidence, five images, no changed locators or manual repair.
One width-association call only, not an extra stage in production. Exact evidence
and Front/Planner identity checked before freezing; failed upstream status kept.
One trial 5.256 s, 1181 output tokens. Association FAIL: 151 cm assigned to all
five B07/B08 bays, although F18/F19 are left of its declared start; equal weights
would yield 302 mm each and B08=604 mm. Fixing topology alone did not solve the
association error. Also eight fallback widths null; whole response rejected.
Raw reply and diagnostic arithmetic (not accepted parts):
notes/evidence/cb-parts-v3-5-2026-11-06/lev2-fixed-topology-trial.json.
248 relevant tests pass. Semantic objective NOT ACHIEVED, no blind retry or
prompt variant. Prior checkpoint/defaults/main/production unchanged; diagnostic
is opt-in only. Next proposal, NOT APPROVED: deterministic same-view consistency
check between declared span endpoints and referenced front intervals, reject
contradictions without silently changing memberships. This detects the observed
contradiction; it does not prove source OCR, visual locators or unseen geometry.
Earlier approved experiment: CB Parts V3.4 associates
labelled horizontal spans with endpoints and cross-block bay intervals. Model
returns relative weights; code conserves each total, converts units and passes
derived bay widths to the unchanged V3.3 parts compiler. Unanchored numeric
fallbacks stay visibly assumed. Reject duplicate allocation, numeric width plus
span, unknown references or null widths without anchors; no source proof is
implied by internal arithmetic. Same complete Lev2 input, no fixture dimensions
inserted in the prompt, no additional stage or model, explicit V3.4 selection.
One trial 9.270 s, 2415 output tokens: all declared span totals conserved, but
151 cm assigned to the wrong interval membership/weights. B07 three doors
collapsed to one bay (weight 3), B08 door plus drawers to one bay (weight 1.3),
giving B08 only 456.5 mm. Side-by-side topology regressed; B06 pair also collapsed.
Whole reply fails B01 heights. Do not present the allocation audit as accepted
parts. Evidence: notes/evidence/cb-parts-v3-4-2026-11-06/lev2-span-trial.json.
221 relevant tests pass; semantic objective NOT ACHIEVED. V3.3 checkpoint/tag
and ordinary defaults unchanged. No new checkpoint or deploy. Subsequent owner
approval authorized the fixed-topology V3.5 diagnostic recorded above, not a new
production stage or promotion of the failed V3.4 output.
Prior owner preservation decision: run two more unchanged V3.3 calls, then create the full
checkpoint immediately. Preservation accepted with known limitations; it is
not production or complete-object geometry acceptance. Do not resume experiments
merely because pending defects remain. No deploy has occurred for this work.
COMPLETED PRESERVATION: estimation-v6.2-cb-parts-v3.3-research-checkpoint-2026-11-06.
Restart: notes/ESTIMATION_V6_2_CB_PARTS_V3_3_CHECKPOINT_2026_11_06.md.
All four requests identical. New runs 9.473/9.674 s; B08 door+drawer widths
350+270=620 and 500+500=1000 mm, one derived partition each. Earlier runs
450+450=900 and 400+400=800. B08 arithmetic/partition 4/4; dimension stability
not established. Whole-object validation 0/4 (height conflicts; run 3 also
omits B09 and has a drawer-body/facade conflict). Raw evidence:
notes/evidence/cb-parts-v3-3-2026-11-06/four-run-checkpoint.json.
201 relevant tests pass. Private recovery archive: 22 files, byte-verified,
hash/path in checkpoint document. Fifty unrelated TODO additions preserved
outside the commit and privately backed up. Main, selectors and production
unchanged. STOP at checkpoint; future height/coverage work needs owner direction.
Prior approved work: locator ablation then CB Parts V3.3 bay contract. The
owner approved moving straight-carcass width/common panels and mounting walls
to deterministic code, retaining one Calculate per object and coarse part list.
1. V3.2 without ONLY B08 region: 13.744 s, B08 300+300=600 mm, S01 omitted,
   whole reply fails coverage. Request equality verified apart from that region.
   Removal alone did not produce acceptable output; causal contribution remains
   inconclusive, not proved absent. Historical input/response left untouched.
2. V3.3 two identical requests with original complete evidence/locators:
   8.190/9.282 s, 2210/2412 output tokens. Model gives side-by-side bays and
   stacked front membership; code derives common panels, fronts, five drawer
   body panels, shelves and exactly one shared wall at drawer-bay boundaries.
   B08 isolated audit: 450+450=900 and 400+400=800 mm, one wall both times,
   one door/three drawers, full-width top/bottom/back now coherent by construction.
   Both WHOLE OBJECT replies still FAIL: B02 front heights exceed carcass
   height (1600>1210 and 1940>1840 mm); second B06 also 1150>750 mm.
   First B06 height 720 contradicts printed 1150 despite passing shape checks.
   Width estimates remain variable. Do not present isolated B08 audit as a
   successful complete object, stable geometry or automatic source validation.
Evidence: notes/evidence/cb-parts-v3-3-2026-11-06/locator-and-bay-trials.json.
200 relevant tests pass. V3.3 remains explicitly selected experimental route;
no default promotion, checkpoint, deployment, DB writes or extra Analyze stage.
Architecture decision recorded in CB contract. Geometry for nonrectangular or
stepped blocks remains explicit model-authored, outside straight-bay guarantees.
NEXT recommendation, not executed: isolate source height association and
vertical extent consistency before accepting a full-object parts result.
No more unchanged paid retries or blind prompt edits for the repeated height
failure. Do not silently stretch, scale or replace raw model dimensions.
PRIOR OWNER REQUEST: accepted coarse equal bays and the interpretation that
two adjacent 500 mm bays imply about 1000 mm overall, then requested a full
checkpoint. Before preservation, owner explicitly paused it to request two
more identical V3.2 trials. No tag/archive/checkpoint was created meanwhile.
REPEATABILITY CHECK, two new paid calls, no prompt/input/code changes:
trials 1/2/3 = 15.041/14.519/15.339 seconds; all request objects exactly equal.
B08 door and drawer widths = 500/600/760 mm, overall width = 500/600/760 mm,
partition quantities = 1/0/1. One door plus three drawer fronts retained in
all three. Trial 3 replaces full top with narrow stretcher. Other inferred
widths vary (B09 350/940/940); printed B06 width/height remain 840/1150.
Stability NOT ESTABLISHED. Equal subdivision is still accepted, but full sized
geometry is not repeatable or additively consistent. Do not reinterpret the
owner's earlier approval as acceptance of these newly observed variations.
Evidence: notes/evidence/cb-parts-v3-2-2026-11-06/three-run-repeatability.json.
CHECKPOINT PENDING OWNER DIRECTION after reporting these results; no production
promotion or new default. Preserve exact raw responses. Do not continue paid
repetitions or blind width-comment edits without a new diagnostic question.
LATEST V3.2 EXPERIMENT, USER APPROVED: added a generic same-run bay sum,
whole-carcass-panel propagation, equal-subdivision fallback and one shared
mounting partition reminder. No schema, arithmetic, evidence or upstream change.
One Haiku call, 15.041 s, 4185 output tokens. Format PASS; targeted bay sum FAIL:
B08 width=500 mm, adjacent door=500 and drawer bay=500. Partition PASS: one
shared mounting wall returned. Equal division itself is acceptable to the owner.
Raw witness: notes/evidence/cb-parts-v3-2-2026-11-06/lev2-sized-parts.json.
Not accepted/promoted. Two consecutive width-comment revisions failed to fix
the same mismatch: STOP this prompt-only approach pending new evidence.
Historical diagnostic recommendation (executed above): same V3.2 request without only
the conflicting B08 locator, retaining its front IDs, composition and all
images. Test whether that locator contributes to the one-bay interpretation;
do not infer causality from these trials. No new prompt or data-schema change
authorized by this recommendation. Existing V3 default/checkpoints retained.
OWNER CLARIFICATION after V3.1: equal subdivision is acceptable at this stage
when the source does not clearly establish interval sizes. Do not reject an
estimate solely for equal bays or require precise visual ratios. This is an
accepted estimating method, not proof of specific dimensions or approval of
the entire V3.1 result. Adjacent bay widths must still sum to the block width;
two assumed 500 mm bays require about 1000 mm overall, not 500 mm. The known
dimension span still constrains the total of all included intervals. Missing
drawer mounting partition remains unresolved. No additional prompt/run made
for this clarification; do not manually overwrite the saved model response.
PRIOR APPROVED EXPERIMENT: CB Parts V3.1 adds exactly one generic paragraph
about distributing a labelled span across visible intervals, including adjacent
blocks, then summing the target block intervals. No Lev2/B08 numbers or special
case in the instruction. Original V3 prompt/default and raw trial are retained.
One unchanged-evidence Haiku trial: 13.439 s, 3840 output tokens, format PASS,
targeted semantic check FAIL. B08 whole width=500 mm, door=500 mm and drawer
bay=500 mm, so two side-by-side bays cannot fit the returned block. Shared
partition disappears; drawer front heights remain identical. Mentions 151 cm
without the requested interval allocation. No manual repair or default promotion.
Evidence: notes/evidence/cb-parts-v3-1-2026-11-06/lev2-sized-parts.json.
NEXT recommendation, NOT APPROVED: make bay widths and their block sum explicit
within the same response, with a deterministic consistency check. This requires
a small contract change, not another unstructured comment or additional call.
Single-run output variation is not proof of a specific causal mechanism.
V3 APPROVED AND TESTED: compact sized rows, one Haiku Calculate for all of Lev2,
same five images and saved V3/V7 scope as V2. 16.529 s, 4498 output tokens,
no thinking tokens. All nine blocks and shared top pass shape/coverage; code
converts declared units, applies 17/30 defaults and drawer-depth arithmetic.
B08 adds the shared divider and preserves three drawers, but assigns only
600 mm total width, equal 300 mm bays and three equal 220 mm drawer fronts.
These do not match visual proportions/heights; 720 mm carcass height is an
unresolved generic assumption. V2 shelf is omitted. B09 still invents a door.
Status: NOT ACCEPTED, no production promotion or integrated Analyze claim.
Evidence: notes/evidence/cb-parts-v3-2026-11-06/lev2-sized-parts.json, unchanged
raw response and separate numeric conversion. V1/V2 remain selectable.
Prior recommendation to isolate width interpretation led to the approved V3.1
one-comment trial above. Existing checkpoints remain protected.
LATEST OWNER OUTCOME: CB Parts must itself deliver the discussed practical
parts breakdown WITH quantities and dimensions for ALL objects, grouped by
object/block. The assistant's manual B08 estimate illustrates the desired
result; it is not a model benchmark. Quantity-only V2 was an intermediate
experiment, not the final deliverable. Keep one Calculate per object, following
one document-wide Analyze; aggregation across objects is deterministic.
NEW OWNER DEFAULT: finished worktop thickness 30 mm when unspecified. Specific
source/context thickness (for example 40 mm) takes priority. Other ordinary
LDSP panels retain 17 mm fallback; worktop thickness does not choose its material.
APPROVED V3 SCOPE (implemented in the diagnostic route): retain compact part rows
and add size/thickness; interpret all views to infer coarse block/bay geometry,
derive constituent panels, retain explicit estimating assumptions where sizes
are absent. Reuse code for unit conversion/arithmetic and drawer depth. Include
the approved divider rule and optional 600 mm clearance fallback. Do not restore
V1's verbose combined material/evidence/formula output or add a model call.
Acceptance must use actual unedited model output for the complete object, not
assistant-authored dimensions. Current trial above fails semantic acceptance.
OWNER REVIEW, 2026-11-06: accepts the discussed B08 coarse parts/quantities,
subject to adding one internal divider between the drawer bay and adjacent
door bay. This does not verify all nine blocks, B09 or stability. The manual
B08 dimensions (1100 width, 800 height etc.) came from the assistant, NOT the
CB Parts V2 model. Do not cite this review as a successful model dimension run.
APPROVED RULE TO APPLY in the next numbered Parts prompt: a conventional
side-mounted drawer bay needs mounting walls on both sides. Within one carcass,
add/count ONE shared vertical divider at each boundary between a drawer bay
and an adjacent bay. Existing carcass sides or an already counted divider
provide that support and must not be duplicated. Vertically stacked drawers
share the same mounting walls; do not add a divider per drawer or treat a
single drawer bay with both outer sides as needing another internal wall.
Save alternate explicitly specified construction as an exception.
APPROVED FUTURE DIMENSION ASSUMPTION: clearance from worktop top surface to
underside of wall cabinets is usually about 600 mm. Use only when unspecified
and visually compatible, not as a printed dimension or universal requirement.
Owner infers about 900 mm worktop elevation on Lev2. With tops aligned, the
source 2650 overall height minus 1150 hanging-unit height minus assumed 600
clearance gives 900. This is the worktop TOP elevation, not automatically the
carcass panel height; plinth/support and top thickness are separate when present.
No prompt selector change or new model run in this record-only iteration.
HISTORICAL V2 EXPERIMENT: response is ONLY a list of major parts and quantities.
CB Parts V2 stays inside Calculate, one call per object. No dimensions,
materials, formulas, 2VN bindings, explanatory output or additional stage.
Return original block/shared IDs with name/quantity rows. Whole-object images
and saved Front/Planner remain available; numeric graph/material constraints
are not appended for this count-only task. V1 prompt/code/raw failures remain
available by explicit selection. Size/material work is deferred, not removed
from the eventual estimation objective. The detailed V1 contract below is
historical, not the current V2 output requirement.
V2 first Lev2 trial: one Haiku 5.5 call, thinking disabled, 5.676 s, 15811
input / 1272 output tokens. Exact same source inputs/pages/images as V1;
numeric graph/material context removed, prompt/output simplified. Returns all
9 blocks plus shared worktop with name/quantity rows only. Format PASS.
Five drawer bodies produce 10 sides, 10 end panels and 5 bottoms, plus 5 fronts.
Remaining semantic work: no internal partitions (including B08, correction
now explicitly approved by the owner),
uniform carcass expansion, unverified shelf counts, and an additional B09 Door
despite no assigned front. Total 17 Hinged door + 1 Door exceeds even the
upstream 17, not the owner 15/16 benchmark. No silent repair or invented success.
Evidence: notes/evidence/cb-parts-v2-2026-11-06/lev2-counts.json.
160 relevant tests pass; a single response is not a stability benchmark.
V2 is the explicit Parts diagnostic selector; Front/Planner defaults and
protected checkpoints unchanged. No production or integrated Analyze change.
Outcome: derive component quantities and dimensions from the large assembly
blocks, preserving the partially compromised V3/V7 checkpoint. This is the next
functional stage, not permission to repair or promote the prior stages.
Name: CB Parts V1. Next task within existing Estimation work block: 3.17.4.6;
remote branch/main rechecked at 7b48d7f/8eb87f1 before assignment, no reuse.
OWNER APPROVAL, 2026-11-06: implement CB Parts inside Calculate, not Analyze.
Target remains one Analyze call for all document objects, then one Calculate
call per object covering all its blocks. Withdraw the agent proposal for an
additional standalone CB Parts call. Front, Planner and Parts are logical
responsibilities, not automatically separate model calls. Recent Front/Planner
paired experiments are not verification of the integrated document-wide Analyze.
Approved placement: coarse parts inside Calculate, consuming block/front IDs,
original whole-object Detection evidence and dimension/material context from
Analyze. Reuse deterministic arithmetic and 2VN where suitable.
Output: block ID, part role, quantity, finished length/width/thickness, source
or derivation or explicit assumption. Approximate estimation, not CNC-ready cuts.
OWNER REQUIREMENTS: estimate large panels and drawer bodies, not fine joinery;
ignore gaps and clearances. Default to LDSP 17 mm absent contrary evidence;
specific material/thickness evidence (for example 40 mm) overrides the fallback.
Drawer depth follows the slide rule: cabinet depth minus 100 mm, rounded down
to a 100 mm step (720 -> 600). New opt-in CB Parts expansion uses that helper;
legacy structural expansion is unchanged. Shared internal partitions counted once. Never derive
physical size from Planner overlay boxes or silently trust incorrect front IDs.
Existing use_cases/estimation_structural_bom.py expands conventional panels,
but also selects material defaults/hardware and uses fixed topology assumptions;
reuse relevant helpers only after contract review, not the full behavior blindly.
No labor, prices, catalog selection, stock nesting or sheet purchasing in this
new stage. First diagnostic uses the entire saved Lev2 plan (nine blocks plus
shared worktop), including B08's three drawers + adjacent door and all views.
Implementation is opt-in via existing Calculate entry point, one request even
for multiple pages. Prior Front V3/Planner V7 and ordinary selectors unchanged.
Verification: 146 relevant tests pass; three paid calls, zero accepted results.
01 timed out at 60.342 s without returned answer. 02 with 120 s transport bound
returned max_tokens at 69.568 s: 13971/14000 output tokens were thinking, only
68 visible characters. 03 changed ONLY thinking=disabled, same prompt/input:
16.921 s, end_turn, 4816 output tokens, zero thinking, but malformed JSON.
Unrepaired visible answer also has cm-valued numbers in mm-only axes, facade
groups charged at whole-block size, wrong front/block assignments and incomplete
L-worktop geometry. Not merely a formatting defect. No semantic acceptance or
promotion. Full raw visible output/usage/request-difference record:
notes/evidence/cb-parts-v1-2026-11-06/lev2-calculation.json.
Private original requests/responses: /private/tmp/lev2-cb-parts-v1-20261106-0[1-3].json.
Provider documentation confirms Haiku 5.5 thinking is on by default and may be
disabled at low effort: https://platform.claude.com/docs/en/build-with-claude/thinking.
Do not keep increasing tokens or silently repair outputs. AGENT PROPOSAL for
next revision: source-unit dimensions converted by code, explicit size groups
for unequal fronts and strict structured output; no added model call. Not yet
implemented/accepted. Integrated document-wide Analyze and production acceptance
remain pending. Protected upstream checkpoint and production remain unchanged.

HSL saved-package replay, USER REQUEST, 2026-11-05, same 3.17.4.5,
P0, COMPLETED diagnostic replay; acceptance FAILED: owner explicitly requests existing
Detection packages, not a locally rebuilt fixture. Latest matching Floor 07
run found: run_99b433940dcc4fd9abbe0587dc56fb12, 2026-10-27T21:14:59Z,
nine objects, 34 persisted view_evidence_packages in Detection event
ba7c98b2-2ad6-44a6-8e8b-cba525d67518. No immutable
rfq_estimation_object_inputs exist for this run. The 40 inspected Floor 06
runs contained no nine-object match. Current Front/Planner consumes immutable
Estimation input_payload plus page bytes, not raw Detection island packages;
the production handoff creates that payload at Estimation start. Do not claim
Detection packages are missing or rerun Detection.
Correction after inspecting actual Lev witnesses: absence of saved immutable
inputs is NOT a new HSL-specific blocker. Lev1 reused persisted input
db175c9d-b911-434e-a3ed-de612640f96f. Lev2 already used the existing read-only
tools/probe_v62_lev2_detection.py bridge: persisted object/island membership
and OCR from run_189150ebf62447fc958f7c23cc34e3bb, source PDF hash checked
against OCR, local page rendering, build_estimation_input, no DB writes.
Its selected replay explicitly records persisted_detection_local_fixture_not_persisted_input.
Earlier claim that this transport needed a new architecture decision was
incorrect. Reuse that established approach for HSL without redetection or
invented object/island membership. Multi-object/document-context handling
still requires verification; the rejected older HSL fixture added all-document
context, while the selected Lev2 witness has no document_context field.
The initial lookup made no provider calls. The subsequently owner-approved
replay completed 18 calls, with no DB writes, prompt changes or deployment.
Superseded local fixture experiment used older run_2dce... and whole-document
OCR, hitting the 100k text bound before provider calls. This does NOT verify
a failure of the requested latest saved package. Its agent-created preparation
script was removed; local diagnostic artifacts remain superseded evidence only.
Executed 2026-11-05 using the existing build_estimation_input route, as in
Lev2: saved nine object rows, existing OCR and exact Detection regions,
source SHA256 verified against the persisted OCR, locally rendered page images.
No synthetic grouping, redetection, added whole-document context, retry or
response normalization. All 34 island references retained. Selected Front V2
and Planner V4, claude-haiku-5-5, unchanged prompt/settings. Two concurrent
object chains, 188.55 seconds provider-batch wall time, 483656 input / 67331
output tokens across 18 calls. This is a diagnostic timing, not production SLA.
Front: 0/9 structural passes, eight invalid island-type labels and one
front-count/box-count mismatch. Existing Planner diagnostic consumes complete
raw Front JSON with failed status explicitly attached as a fallible reference;
no Front output was repaired. Planner: 7/9 structural passes; object-001 invalid
references, object-007 max_tokens truncation. Full-chain acceptance: 0/9.
Visual review: all nine source pages inspected; exact Planner overlays for
N57/object-002 and N68/object-005 reviewed. N57 misses separate upper/appliance
scope and joins physically distinct tops; N60/object-003 invents another run
from views and emits unsupported millimetre labels. N68 recognizes L layout
but worktop overlay lies on upper shelving. Counts/schema are not acceptance.
Earliest confirmed transport defect: source_coordinate_frame calculates frame
from unrotated page_size_points * dpi/72. PDF pages 3,5,6,8,9,10 have rotation
270; images and Detection bboxes are in landscape frame. Five objects receive
no detail crops, object-006 receives two mispositioned crops; all full pages
remain present. Unrotated pages are unaffected by this particular mismatch.
P0 pending recommendation, same work number: correct rotation-aware coordinate
transport and add a rotated-page regression, then replay the same evidence and
prompts. No fix yet authorized/implemented in this diagnostic iteration. Enum,
front-count and Planner budget/semantic failures remain separately open;
the transport defect is not asserted to explain all model errors.
Durable raw responses, usage, hashes and audit:
notes/evidence/hsl07-v62-2026-11-05/replay-evidence.json.
Full local requests/inputs/snapshot/overlays:
/private/tmp/hsl07-saved-replay-20261105-01/.
Existing Lev1/Lev2 accepted abstraction and protected r03 checkpoint unchanged.

N68 targeted Planner update, USER REQUEST, 2026-11-05, same 3.17.4.5,
P0, completed experiment / acceptance FAILED: owner confirms eight hinged
doors and four drawers. Five lift-up fronts are NOT accepted; Front located
F01-F03 and F16-F17 on triangular marks in the upper shelf bands.
CB Planner V5 adds worktop localization on top/axonometric views; an edge-only
fallback explicitly states missing footprint when no surface view exists.
CB Planner V6 also limits tall cabinets to at most TWO tall leaves across,
preserving the one-section-wide rule and the ordinary three-position allowance
for non-tall blocks. V5 single N68 call: 22.921 s. V6 single N68 call: 22.311 s.
Both pass structural validation. Exact same input, images, saved failed Front,
model and settings as V4; only system prompt differs. No Front replay or retry.
V6 shows S01 on p7-view-001 and tall storage split F07/F08 + F09 (2+1).
Regression: previously represented wall-1 appliance column is now absent.
Overlay reviewed without corrections; worktop footprint and drawer box remain
approximate/incomplete. V4 default restored, V5/V6 prompts retained as candidates.
V4 is a comparison baseline, not an accepted full HSL solution. No deployment.
166 focused tests passed with V6 selected; restored-default Planner tests pass
(25 tests); git diff --check passes.
Evidence: notes/evidence/hsl07-v62-2026-11-05/n68-planner-v5-v6-evidence.json.
Next proposed work: diagnose physical scope omission before accepting V6;
do not attribute all omissions to a prompt rule from a single sample.

Historical CB Front V2 support experiment, 2026-11-05, same 3.17.4.5:
Add physical legs and tabletop support interpretation to the existing Front
consumer, not a third stage. Consider four legs, two plus attachment, a central
pedestal or a narrow top with central leg/attachment as contextual possibilities,
not mandatory counts. No hard width cutoff: a broad pedestal can support a wider
top. Distinguish observed connection from assumed attachment. Compare all views
before interpreting one visible leg as a single-leg design; no forced Lev1 count.
Implementation candidate CB Front V2 / estimation_front_count_v6_2_r05;
original r03 file/hash and archived r04 remain immutable. No production route
change. English prompt agents/prompts/cb_front_v2.md. Add tabletop_supports,
separate from unchanged front totals: physical leg count/basis, scheme, ambiguity,
owned views and individual L-ID boxes. No boxes for hidden inferred legs.
Legacy validators remain explicit; no silent output repair. Shared overlay
renders leg boxes and separate display totals; Planner palette stays unchanged.
Bounded verification: one Lev1 Front call, then unchanged Planner V4 consuming
that saved result. Pass requires source-supported two distinct legs, preserved
three drawer fronts, correct references and downstream retention. Same images,
Haiku settings and call count per stage; do not inject the sample benchmark.
159 focused tests pass before live probe. Source images/Front checkpoint protected.
First probe: Front V2 16.227 s, 14777 input / 2774 output tokens; three drawers,
two distinct leg boxes on island 003, explicitly assumed attachment. Original
validation FAILS on snake_case island enums. Diagnostic overlay only expands
spelling on a copy with FORMAT WARNING; raw witness and counts stay unchanged.
Unchanged Planner V4, 11.991 s, 14163 / 2060 tokens: two legs retained, but base
and screen merged into one block, giving TWO rather than prior THREE assemblies.
Only system differs in the Front request; only saved Front context differs in
the Planner request (images/OCR/settings/system unchanged). This does not prove
the added support field caused regrouping: other Front text changed as well.
No promotion: default Front restored to exact V1/r03; V2 available only through
--count-fronts --front-supports, with explicit version/hash recording. Planner
V4 unchanged. Evidence: notes/evidence/cb-front-v2-2026-11-05/.
USER REQUEST repeat comparison: run old Front V1 then same Planner V4; if three
blocks recur, run Front V2 then same Planner. Record every failure, not selected
successes. Repeated 3-versus-2 would support, not establish, a causal dependency.
Repeat completed: V1 Front 9.456 s + Planner 14.087 s gives THREE blocks / one
described leg. V2 Front 15.097 s + Planner 10.993 s gives THREE blocks / two legs.
Both repeated Front requests exactly match their earlier same-variant requests;
Planner system/settings/images unchanged. Only new saved Front responses vary.
Sequence is V1 3, V2 2, V1 3, V2 3 blocks. Simple deterministic 3-to-2 dependency
is not reproduced. A probability effect remains unknown at this sample size.
V2 identifies two legs twice and Planner retains them twice. Both repeated
Front outputs still fail enum validation; both Planner contracts pass.
No repairs or additional retries. Durable comparison:
notes/evidence/cb-front-v2-2026-11-05/lev1-repeat-comparison.json.
Recommendation: retain support candidate; next resolve exact island enum output
contract before promotion. Do not remove the support rule based on this
non-reproduced grouping hypothesis. No Lev2 V2/production acceptance.
Final verification: 163 focused tests pass, including original Front rejections,
support/reference validation, unchanged default r03, exact-box overlay and both
repeat outcomes. git diff --check passes. No full production-cycle verification.

PENDING owner review, P0, CB Planner V4, 2026-11-05, same 3.17.4.5:
Prefer full-height narrow cabinet assemblies exactly one section wide (one
door compartment or drawer stack), keeping vertically stacked doors, drawers,
shelves and appliance openings together before horizontal grouping. Preserve
source boundaries and separate wall units; alignment alone does not prove a
continuous carcass. No new schema/call stage, no sample-specific IDs or counts.
Bounded experiment: one Lev2 Planner call with unchanged saved Front/evidence
and settings. Success requires a coherent single-section tall assembly without
neighbouring sections or bridging separate units, plus valid front ownership.
Compare with V3, preserve its original failure and the accepted Front checkpoint.
Completed one probe: 27.294 s, 15257 input / 5519 output tokens. Only system
differs from V3 request. Original validation passes without repair. Ten blocks
plus one shared worktop. B06 now combines F09/F06/F07/F08 into a single-width
full-height column; former V3 B02/B03 no longer divide its lower/upper parts
between adjacent cabinets. This targeted grouping improvement is confirmed.
Semantic acceptance remains partial: B01/F24 still wrongly describes a tower;
summary regresses L to U-shaped, B06 is misnamed corner and the appliance
opening is not recognized (called panel). Upper open shelves remain unlisted.
Cross-view physical duplication remains unresolved; worktop ownership includes
tall B06 without establishing support. Original boxes visually reviewed,
unchanged. No retry, promotion, main merge or deployment.
Evidence: notes/evidence/cb-planner-v4-2026-11-05/lev2-evidence.json;
raw witness /private/tmp/cb-planner-v4-lev2-01.json.
Next: owner review of B06; proposed next diagnosis is cross-view physical
identity/duplicate assemblies, not another cosmetic grouping-rule revision.
Front r03 accepted checkpoint and historical V2/V3 remain unchanged.
Verification: 130 focused tests pass, including saved V4 column ownership and
retention of its semantic limitations; git diff --check passes.
Owner-requested Lev1 V4 follow-up completed with the unchanged prompt, one
Haiku call, 13.370 s, 13888 input / 2233 output tokens. Only system differs
from the previous Lev1 V3 request. Original Planner validation passes.
Three groups preserved: B01 low carcass with F01/F02/F03 drawers, B02 fixed
decorative slatted upright, B03 tabletop with support. No invented tall cabinet
column. The single-leg error persists although source island 003 shows two.
Additional semantic failure: output invents mm for 158/265/75 and calls the
overall 265 height above-seat height, despite the no-dimensions prompt boundary.
Saved Front enum failure is retained without normalization or a new Front call.
Source and raw-box overlay visually inspected. Grouping preserved, not full
content acceptance. Evidence: notes/evidence/cb-planner-v4-2026-11-05/lev1-evidence.json;
raw witness /private/tmp/cb-planner-v4-lev1-01.json. No runtime/prompt changes.
Pending before material quantities: multi-view completeness and unit grounding;
these findings do not authorize an architecture or schema change.
Follow-up verification: 25 Planner tests pass including the unmodified Lev1
response and its known errors; git diff --check passes. No full-cycle acceptance.

OWNER-APPROVED CB Planner V3, 2026-11-05, same 3.17.4.5:
Owner confirms the countertop is a standalone physical element. Keep it once,
with references to supported carcasses when shared; it is not merely a label
inside a base block. Its review rectangle is not a cutting contour.
Owner approved implementation and testing of the grouping proposal: aim
for at most three fronts across the width of one cabinet block; four only as
an explicitly justified rare exception. Full-height narrow cabinets remain
possible. Owner considered 500-600mm minimum / 1400-1500mm maximum horizontally,
then proposed front-count grouping instead. Do not implement those dimensions
as simultaneous hard bounds or apply a horizontal maximum to height.
Approved refinement: count horizontal front positions, not the sum of
vertically stacked drawers/doors; for a corner block consider both wings to
avoid doubling the allowance. Two door leaves do not prove two compartments.
Do not impose a hard minimum that would erase a necessary narrow cabinet.
This is an estimating grouping policy, not proof of transportability or a
universal furniture-manufacturing rule. Source construction still takes priority.
Countertops/non-cabinet panels are not subject to the facade-count limit.
CB Planner V3 implemented as a versioned prompt, V2 retained unchanged.
No schema, provider settings, images, saved Front or production-route changes.
V3 SHA256 28ddc60a1e8b5c6385cb13f738cc98b40d7a9414e86b6aa43e53b685f0e6dac5.
128 focused tests pass, including current/previous prompt fingerprints and
Front r03 identity. Two bounded live probes use the same Lev1/Lev2 inputs as V2.
Status: completed experiment, partial semantic improvement, not accepted.
Live probes: Lev1 11.057 s (13592 input / 2053 output tokens), Lev2 18.306 s
(14961 / 4081). One Haiku 5.5 call each; comparison against each V2 request
confirms ONLY system changed, including byte-identical evidence/Front context.
Lev1 now returns the three owner-proposed groups: lower drawer carcass,
decorative vertical panel and separate tabletop/support assembly. Contract
passes; model still describes only one support leg instead of two, so this is
grouping improvement, not full physical-content acceptance.
Lev2 returns nine blocks + one separate shared worktop, corrects U to L in
summary and splits rows into groups with at most three stated width positions.
Original validation FAILS: F24 belongs to B09 and front_conflicts simultaneously.
No silent deletion/repair. B09 remains a proposed tall cabinet on the known
ambiguous/fixed structure. Upper open shelving is not explicitly covered;
cross-corner and full-height assembly interpretation remains unproven.
Both full-page overlays visually reviewed. Lev2's diagnostic diagram displays
the original regions under an INVALID banner after separate box/reference
checks, without treating the rejected plan as valid. Source witness unchanged.
Artifacts: /private/tmp/cb-planner-v3-lev1-01.json and
/private/tmp/cb-planner-v3-lev2-01.json, with raw output and overlay suffixes.
Durable final outputs, comparison and review:
notes/evidence/cb-planner-v3-2026-11-05/.
No additional model retries, schema relaxation, main merge or deployment.
Next: owner review of actual boundaries, especially B09/F24 and the tall-unit
split. Front V1/r03 checkpoint and historical V2 prompt remain unchanged.
Final verification: 129 focused tests pass, including replay of both original
V3 outputs: Lev1 validates and Lev2 still rejects the duplicated F24 ownership.
No full-cycle or production acceptance inferred from these tests.
Owner authorized all necessary bounded paid replays and Anthropic evidence
transmission until readiness for production and personal acceptance.
[verified] Capsules 02-06 retain raw responses/usage before validation. No
accepted LF1 result yet. Witness 04 computed in 134.47 s, but had incorrect
materials, duplicate enclosure, missing group geometry and 500-mm slides.
Witnesses 07/08 (adaptive high) exceeded 180 s; 08 received its first provider
event in 2.299 s but no text before timeout. No thinking route is accepted yet.
09/10 strict-schema requests failed with HTTP 400; the experiment was removed.
11 adaptive-medium exhausted 12,000 output tokens before JSON (227.85 s).
12 tests a separate bounded thinking allocation, with unchanged Analyze evidence.
Corrected source/display coordinate presentation, compacted repeated material
descriptions, and added explicit front-schema/build-up validation. These are
experimental until functional acceptance passes. Do not weaken source or
hardware guards to manufacture acceptance. No production write or deployment.
Retain the V5.8.2 production checkpoint. V6.1 evidence-map suite: 1697 passed,
10 unchanged baseline failures. Latest focused map/2VN/semantic/replay/construction
checks: 62 passed. Separate-page context survives legacy per-object composition;
Calculation has a V6-only geometry contract. Live acceptance remains open.
USER REQUIREMENT, P0: functionally correct complete materials cycle first.
Owner explicitly removed the proposed hard latency budget, retaining efficiency
as a quality goal. First pass must explain construction/material assumptions;
Calculation and purchasing must preserve them and count all material demand.
ACTIVE FOCUS, P0, owner clarification 2026-11-05: focus next on Analyze's
whole-object understanding across ALL owned islands and applicable document
context, not a chain of model reviewers. Make its object/construction/material
interpretation readable in one or two sentences. Acceptance is useful estimating
accuracy, not zero error: preserve physical function, major assemblies and
plausible dimensions; assess smaller errors by material/purchasing impact,
without treating the owner's 1800-vs-2000 example as a universal tolerance.
Owner endorsed whole-object-first interpretation and requires an accessible
short explanation of observations, cross-view correspondences and assumptions.
Stop at first-cycle understanding for now; do not advance Calculation or add
reviewer stages. Inspect Detection handoff before attributing perception errors
to the model. Working UI explanation is an owner idea, pending scenario/location
agreement, not authorization for an unverified UI change.
Owner supplied /Users/qb/Desktop/SAMPLES/JOLD/Lev 2.pdf as a possible first
independent understanding case alongside LF1. Read-only source review shows
one kitchen assembly through a plan, axonometric and two elevations; no material
specification text. This is the reviewing agent's interpretation, not a Haiku
result or verification of this file's persisted Detection package. Prefer a
paired evaluation: Lev 2 for conventional composition, LF1 for less conventional
geometry. V6.2 first-cycle experiments are now approved; no production contract
replacement or Calculation integration until first-cycle acceptance.
Owner clarified Lev 2 acceptance: identify the separately hanging cabinet as
a distinct physical assembly within the same kitchen, the sliding drawers,
and horizontal lift-up fronts. Gas-lift provision follows the existing owner
construction policy for lift-up fronts; this is not an explicit hardware
specification printed in the PDF. Analyze must expose these functional
distinctions and their observation/assumption basis. Hardware quantities and
selection stay downstream; no new Calculation work is authorized here.
V6.2, 2026-11-05: owner confirmed this number after reviewing V6.1 history.
V5.9 was a withdrawn discussion label, never a code version or release. Keep
3.17.4.5; do not erase V6.1 experiments or renumber the production V5.8.2.
[verified] Implemented local --understanding-only mode: one shared Haiku request,
whole pages before owned details, short whole-object/construction descriptions,
components/operation, per-view observations, explicit cross-view matches and
uncertainties. No Calculation, hardware counts, automatic reviewer or DB writes.
Readable escaped HTML reports persist even for invalid answers; working UI
placement is still pending scenario agreement. Raw responses/usage retained.
[verified] LF1-01 with Detection name Cabinet misread the screen as hinged doors.
LF1-02 removes that naming hint from request context only: fixed slat panel,
three drawers and two supports recovered. LF1-03 repeats the byte-identical
request independently and returns the same interpretation. 27.75 / 29.80 /
29.62 s total respectively. This supports naming-anchor sensitivity; it does
not establish universal causality or correct geometry/materials. Numerical
claims in the explanation and some cross-view matches remain wrong.
Lev2-01 source-only: no matching immutable input found in company 610 by file
name or exact PDF hash. Full-page probe took 28.95 s, confused multiple facade
functions and returned source_ref as input_id (rejected). NOT a Detection test
or accepted kitchen result. Capsules/reports: /private/tmp/estimation-v6-2-*.json
and corresponding .html. Functional first-cycle acceptance remains OPEN.
Full suite: 1759 passed, same 10 baseline failures, 29 warnings, 16.68 s.
Next: review the accessible first-cycle explanations with owner; establish a
real Lev 2 Detection input before treating results as handoff acceptance.
No further prompt-only retries or progression to Calculation in this iteration.
Lev 2 successful Detection evidence audit, 2026-11-05 (read-only):
[verified] Latest two successful company 610 runs are
run_189150ebf62447fc958f7c23cc34e3bb (event 8fd1c7f0-2f36-42bd-b7ae-537460324445,
10:56:37Z) and run_c63dd16473e645fbb887c55e364af9ca (event
549568f9-8d0d-4109-b8b3-bba5727625ca, 10:55:47Z). Distinct provider request IDs;
identical Discovery/review audit hashes, one object-001, quantity 1 inferred,
four identical owned boxes (plan, render, two technical views). Original PDF
SHA b69e132814531862c1abbf2ea3910e0221ab013dd2d0fb184400149d6ec02b1d
matches the supplied sample and has a persisted original artifact in both runs.
OCR events 29b1d88e-3848-4046-b4b5-662a03fc6869 and
54c2283f-5ef5-4050-b84d-12e924318c92 contain 18 text blocks: 16 numeric/angle
labels and two source readings of the SOLIDWORKS footer. Evidence differs only
in four native-inspection timing values. Coordinate frame 3308x2339 at 200 dpi;
no vector line segments, literal_items or material specification text.
Membership audit records L-shape/corner/tower correspondences and render
attachment, with source refs. These are model interpretations, not verified
part geometry or material facts; current handoff does not transport them.
Both runs currently have ZERO rfq_estimation_object_inputs rows and no
Estimation usage events. Existing runtime persists inputs at estimation-job
start, not Detection completion. Do not call these completed immutable
handoffs. Next proposed step is a local read-only diagnostic fixture from
the latest run's real Detection/OCR/original, without launching production
Calculation; preserve this distinction from a persisted input_id.
Successful exception rows reference valid CR IDs but describe accepted islands,
not actual exclusions. Success therefore does not prove the earlier exception
contract weakness has been repaired. No Detection fix or deployment in this audit.
Detection contract audit, 2026-11-05, same work 3.17.4.5 (USER REQUEST):
CURRENT OWNER POLICY / CABINET DIAGNOSIS, 2026-11-05, 3.17.4.5:
Owner changed hinge height bands: <=1000 mm:2, >1000 mm:3, >2000 mm:4.
Implemented in the shared _hinges_per_facade helper, including hardware audit
and priced-demand paths. Seven boundary cases cover 600,601,1000,1001,1500,
2000,2001 mm end-to-end through structural BOM; slides/lift sets unchanged.
Historic 600-mm records below describe superseded policy, not current intent.
User deferred further response-shortening work: understanding takes priority.
[verified] Cabinet Block's visual classification is a prompt instruction, not
a deterministic detector. Structural composer consumes front_kind/quantity/
arrangement already chosen upstream. Scope gate enforces consistency with the
upstream operation, not with pixels. Tests supply front topology explicitly;
passing composition tests do not prove visual recognition. V6.2 components
reference whole views but lack structured front-level position/orientation/
bay-closing observations, so a wrong front reading can pass schema validation.
Bounded diagnostic 03 changes ONLY removal of upstream Membership context
from probe 02's actual request (exact request comparison confirmed); same
prompt/images/OCR, one Haiku call, 27.6 s, 9787 input / 3095 output tokens.
Capsule /private/tmp/estimation-v6-2-lev2-detection-03-no-grounding.json;
raw /private/tmp/estimation-v6-2-lev2-detection-03-raw.txt.
It now labels vertical fronts hinged and recognizes a separate hanging module,
but calls drawers fixed dividers, worktop an upper shelf, plan a side view,
and still assigns bare numbers millimetres. All output operations are fixed
or hinged. Structural validation passes, semantic acceptance still fails.
Thus prior interpretation is not the sole cause; source reading/local physical
ownership remains unsupported. One paired run is not a general causal proof.
DEFERRED AGENT PROPOSAL, not approved: test compact structured observations of
front groups (owned location, upper/lower, orientation, arrangement, bay closure)
within the SAME first call before deriving operation via existing policies.
No new template library/reviewer, no invented geometry; do not implement this
contract change merely because the proposal is recorded. No further prompt
piling. Full suite 1768 passed / same 10 baseline failures / 29 warnings,
16.04 s; focused 40 passed. No production deployment or new acceptance claim.
OWNER ARCHITECTURE CLARIFICATION, 2026-11-05, same work 3.17.4.5:
Understand whole object from evidence, recognize an applicable construction
class (e.g. kitchen/cabinet/shelving as cabinet furniture), explicitly select
Cabinet Block, then apply its interpretation/hardware policy. This must be
an identifiable module application, not only background prompt wording.
Before the approved experiment below, understanding had no tool/module-selection
invocation; the composer acts after model classification. Module applicability
may be per assembly in mixed objects;
the kitchen label must not classify every component as a cabinet.
Owner subsequently authorized applying this idea and running a diagnostic.
The local route uses explicit tool selection and a second Haiku provider request
to consume returned instructions within one logical Analyze stage.
Do not silently introduce a third review stage, manual template-library project,
or transfer catalog/price authority to the model. Hardware quantities remain
the existing deterministic policy once physical front topology is established.

ACTIVE, P0, explicit Cabinet Block diagnostic, 2026-11-05, same 3.17.4.5:
[verified] Local run_understanding_with_modules exposes apply_cabinet_block
with automatic (not forced) tool choice. First request sees all source evidence
but not detailed policy. The tool result loads the existing Cabinet policy;
the continuation retains the original evidence and forbids further tools.
The old single-call route and production remain unchanged. Non-applicable or
invalid selection stops; mixed/multi-object routing is not production-ready.
CLI tools/probe_v62_module_call.py retains both actual requests, provider raw
responses, usages and module scope without DB writes or Calculation.
Probe /private/tmp/estimation-v6-2-lev2-module-01.json reuses probe 03's real
Detection-backed local fixture, omitting Naming and Membership narrative.
[verified] Both calls contain identical source content, 1 full page + 4 crops.
Haiku selected Cabinet Block at 10.929 s; completed at 37.336 s total.
Tokens: selection 9479 input / 880 output, continuation 12941 / 2922.
No cache hits. Structural validation passes; SEMANTIC ACCEPTANCE FAILS.
Before tool retrieval the model describes a shelving/storage system, misreads
the top-left plan as side section and assigns unsupported millimetres. After
policy retrieval it retains these mistakes, labels the three-drawer stack open
shelves and emits no drawer/lift_up operations. The worktop is not identified.
Confirmed: explicit invocation works but did not fix this run's understanding.
Not established: universal impossibility on Haiku, or a single causal explanation.
This experiment changes both orchestration and first-stage prompt relative to
03, so it is not a one-factor causal comparison of tool use alone.
Raw outputs: /private/tmp/estimation-v6-2-lev2-module-01-module_selection-raw.txt
and /private/tmp/estimation-v6-2-lev2-module-01-understanding-raw.txt.
55 focused tests pass; git diff --check passes. Tests verify routing/contracts,
not visual accuracy. No new accepted checkpoint, commit or deployment.
Earlier proposed diagnostic was isolated whole-object recognition; the owner
subsequently chose the Island Map experiment below instead.
Do not silently retry or pass this output into Calculation.

ACTIVE, P0, USER APPROVED, same 3.17.4.5: Island Map / Карта островов, define view/island
classification vocabulary and decide Detection versus Estimation ownership.
Outcome: distinguish plan/elevation/section/3D/detail and relate them across
the whole object's evidence before interpreting construction. Owner approved
prompt implementation and a live comparative run. Estimation Analyze owns joint view interpretation;
Detection preserves source regions, printed view labels and their references,
not authoritative inferred projections. Separate representation/direction from
coverage/section/exploded modifiers; permit mixed/unknown rather than forcing
one island into one view. Classify jointly with whole-object understanding in
the existing first cycle, not a new per-island call or reviewer chain. Expose
observable grounds and cross-view matches; a label alone is not verification.
OWNER DIRECTION: keep view interpretation at the start of Estimation, before
Cabinet Block application. Approved mechanism:
jointly inspect the entire evidence set, use informative overall views and source
labels to orient the object, then map each view using visible correspondences.
Include view class/direction/coverage, cited grounds and uncertainty in the first
request's module selection payload; continuation receives this map plus original
images and module policy. No extra per-island call. Unknown/mixed cases remain
explicit; map entries are revisable hypotheses, never proof or immutable geometry.
Require concrete correspondence instead of merely repeating a type label. Check
reference coverage/enum validity deterministically, but assess actual classification
against source images. First experiment would retain Lev2 evidence, model and
Cabinet policy, changing only the first-stage mapping contract and its handoff.
Acceptance: identify the top-left plan, volumetric view and two elevations without
inventing units; separately evaluate drawers/lift fronts/worktop, since correct
view classification alone does not establish correct furniture understanding.
Local implementation: agents/prompts/estimation_island_map_v6_2.md and the
existing module route require one map record per Detection-owned island,
representation/direction/depiction/coverage, observable grounds, owned cross-
island correspondences and uncertainty. Validate map before returning Cabinet
policy. Tool continuation retains original images and may explicitly correct a
map interpretation. No source-only region invention, Detection mutation or new
provider stage. Local HTML displays the initial map with escaped provider text.
The policy itself is unchanged; final contract now consumes the map instead of
forbidding formal classification. Stage-one output cap scales with island count
(4000 on Lev2 versus 1600 before); latency comparisons must disclose this change.
67 focused tests passed (1.83 s); no semantic acceptance inferred from tests.
[verified] Live Island Map results, 2026-11-05, same 3.17.4.5:
- island-map-01: stopped after selection at 26.418 s because direction=mixed
  was absent from the schema, despite the intended mixed-island support. This
  is a contract mismatch, not proof that the image has mixed projections.
  Added mixed direction to both schema and prompt, with regression coverage.
- island-map-02: selection completed at 24.553 s; schema passes, Cabinet Block
  receives the exact map. Final response hit max_tokens=3500 at total 46.059 s.
- Only that saved continuation was replayed with max_tokens=6000, not another
  classification request. Exact request diff confirms max_tokens is the sole
  change and original selection is identical. Full continuation completed in
  23.235 s, 29069 input / 3919 output tokens; structure/references pass.
  Default final cap in this diagnostic route is now 6000/object, capped 12000;
  single-call understanding and production routes remain unchanged. 15 module
  tests pass after final adjustments; earlier 67 focused tests passed; diff check passes.
Artifacts: /private/tmp/estimation-v6-2-lev2-island-map-01.json,
/private/tmp/estimation-v6-2-lev2-island-map-02.json and
/private/tmp/estimation-v6-2-lev2-island-map-02-continuation.json (.html report,
-raw.txt untouched full final text). Map raw is ...-island-map-02-module_selection-raw.txt.
Replay script /private/tmp/continue_lev2_island_map_probe.py preserves the truncated
attempt and appends the continuation; it does not silently overwrite a success.
Against module-01, inputs, full-page bytes, actual first-user content and Cabinet
policy are all exactly equal. Both calls keep 1 full page + 4 crops. Image sizes:
1985x1404, 947x746, 552x479, 865x716, 750x592; no missing image inferred from labels.
[verified] SEMANTIC ACCEPTANCE FAILS. Island 001 plan is classified side profile;
002 correctly axonometric; 003/004 elevations are split conceptually into upper
facade + lower plan (mixed). Source numbers are still assigned unsupported mm.
Map correspondences contain invented matches, not merely missing descriptions.
Partial positive change versus module-01: whole object is now a corner kitchen,
worktop appears, two drawer-bearing assemblies appear. But quantity=1 counts
each cabinet, not its actual fronts; no lift_up, drawer-front total unestablished,
separate hanging cabinet identity not clearly retained. Generic parts and wrong
cross-view ownership remain. Do not treat occurrence of word 'drawer' as topology
acceptance or use these groups for deterministic hardware quantities.
Measured effort: 4 provider calls including schema failure and truncated attempt,
95.712 s summed invocation elapsed; successful selection + final continuation
sum to 47.788 s, NOT an independently measured clean end-to-end run. No speed or
cost improvement claim; successful pair consumed 40346 input / 7435 output tokens
versus module-01 22420 / 3802. Cache hits zero. One comparison does not establish
causality or stable recognition improvement. No new accepted checkpoint/deploy.
OWNER FOLLOW-UP, 2026-11-05: fix view classification first and explain missing
drawer count in parallel. Owner confirms island 001 top view, 003/004 frontal
views, five drawers total. These are benchmark annotations, NOT model-input
hints. Drawer faces are landscape rectangles in vertically stacked banks;
do not encode 'vertical narrow rectangle = drawer' from the wording slip.
Implemented --map-only diagnostic, one provider request INSTEAD OF the module
workflow, not a third production stage. It reuses evidence, taxonomy, coverage
validation and local report. Production/Calculation are still untouched.
[verified] ...-island-map-only-01.json: same classification core without module
selection/decomposition, 19.100 s, 10085 input / 1918 output. Plan misread front,
lower elevations mixed; sole module-coupling cause not supported. Inspected
exact decoded sent images: intact readable plan and elevations. Payload text
has no upstream projection labels, only P1/IDs/regions/OCR numbers and footer.
[verified] Replaced generic classification paragraph with surface-based criteria:
start map with informative overall volumetric island; match top/front/side
surfaces; a gap between wall/base units does not establish independent views.
Same schema/images/model/output budget. Saved request comparison of map-only
01/02 differs ONLY in system prompt. ...-island-map-only-02.json completed in
20.435 s: 002 axonometric, 003 and 004 front, but 001 still side; 004 coverage
detail wrongly suggests a magnification of 003. Correspondences still invent
dimensions/parts and quantitative interpretation. Classification PARTIAL,
not accepted; no full module replay or deployment after this prompt change.
All paths share /private/tmp/estimation-v6-2-lev2 prefix; raw files have
-island_map-raw.txt suffix, reports .html. 35 understanding/module tests passed;
17 module tests passed after prompt replacement, git diff --check clean.

Drawer diagnosis, same owner request/outcome:
[verified] Final prior response c2 and c4 name a 'cabinet with drawers', each
quantity=1/operation=drawer. It counts cabinets, not drawer fronts. The V6.2
generic component schema cannot distinguish these quantity meanings and lacks
a structured parent/child or front_groups requirement. The prompt ALREADY says
split fixed parents from moving front groups and count physical fronts, but the
model violates this and validator only checks positive integer/enums/references.
Wrong island interpretation adds incorrect cross-view ownership; do not claim
quantity ambiguity alone explains the visual miscount. No hardware calculation
was run. Existing assembly/BOM contract already has front_groups with front_kind,
quantity, arrangement plus counts.drawers; reuse that separation, do not invent
a competing counting engine. Source/owner benchmark: bank of 3 + bank of 2,
count once from the two elevations and corroborate (not add) axonometric repeats.
PROPOSED, needs contract decision: bridge that existing front-group structure
into understanding so one cabinet cannot pass as one drawer. Current turn changes
classification diagnostics only; quantity schema/hardware composition unchanged.
Next unresolved classification diagnostic should address plan-to-volumetric
surface correspondence, not another broad Cabinet rule or reviewer stage.

OWNER-APPROVED EXPERIMENT, natural visual explanation, same 3.17.4.5:
Test whether removing the classification schema and detailed instructions fixes
cross-island recognition. One Haiku request, no Cabinet Block, tools, materials
or counts. /private/tmp/probe_lev2_natural_visual.py replays map-only-02's exact
request, changing ONLY system. Same full page + four crops, same OCR/context,
model, temperature=0 and max_tokens=4000. Prompt asks to describe the volumetric
whole and explain viewing directions of other islands with visible matches;
no benchmark answers, kitchen label or preset projection assignments supplied.
[verified] /private/tmp/estimation-v6-2-lev2-natural-visual-01.json completed in
7.663 s, claude-haiku-4-5-20251001, 8618 input / 627 output, end_turn, one call,
zero retries. Matching -raw.txt preserves provider text; .html includes exact
prompt plus untouched answer. 002 recognized as volumetric/angular form, but
001 called front, 003 top, 004 side against owner reference top/front/front.
It again invents mm and cross-view correspondences. No semantic acceptance.
Question outcome: rejected as a sufficient fix on this case. Natural wording
is faster/shorter on this run, but not more accurate. This single comparison
does not prove Haiku categorically cannot solve the task. Production and shared
classifier prompt/code unchanged; no failed free-form replacement to roll back.
NEXT AGENT PROPOSAL, not authorized/run: same natural question and images,
remove OCR/numeric textual context while retaining image-to-island locators,
to distinguish textual anchoring from visual projection-reading failure.
This would be a diagnostic input comparison, not permanent context deletion.
OWNER STRATEGY DISCUSSION, same 3.17.4.5: owner challenges further text-cleaning
experiments and asks why view classification fails, plus three independent
strategies. The tentative Sonnet request was interrupted; do NOT run or switch
models from that phrasing. No new live probe authorized in this discussion.
Confirmed failure is source-image cross-view interpretation, not missing images
or a demonstrated OCR cause; general model incapability is still unproven.
AGENT PROPOSALS, pending choice, specific to island recognition (not replacements
for earlier whole-Estimation strategies):
1. Visual few-shot calibration of Haiku: a small fixed set of correctly labelled
   multi-view examples, not more verbal rules. Evaluate on held-out files;
   never train/prompt on Lev2 answers then claim independent Lev2 acceptance.
   Trade-off: curation and additional image-context/token cost; benefit unverified.
2. Geometry-assisted interpretation: use available PDF vectors, contours and
   dimension correspondences to check candidate projections. Keep uncertainty
   for ambiguous/raster sources; no guarantee that geometry uniquely determines
   view class. Trade-off: substantial implementation and source-format coverage.
3. Change only the first visual interpreter to a more capable model, if allowed;
   keep Haiku downstream and deterministic composition. This replaces a request,
   not adds a reviewer stage. First test identical evidence blindly, do not assume
   Sonnet succeeds. Production model change requires explicit owner approval.
Recommended next diagnostic decision: a bounded same-input control with another
model can test whether a different interpreter can read the packet before major
geometry investment. One correct answer establishes neither reliability nor
Haiku impossibility; retain a small held-out acceptance set for any adopted path.

OWNER APPROVAL / SONNET CONTROL, same 3.17.4.5, 2026-11-05:
Owner now explicitly authorizes Sonnet test (supersedes prior interrupted request).
Primary outcome is island CLASSIFICATION; cross-island correspondence is only
supporting evidence, not a mandatory lengthy product output. Geometry-heavy
implementation is disfavoured as disproportionate. Owner can supply around ten
examples of each type. Proposed use: labelled full-sheet/object packs, a small
few-shot subset and separate held-out evaluation files; do not inject all examples
into every request or mistake prompt examples for weight training. No example
collection or data-contract rewrite performed in this turn.
[verified] /private/tmp/probe_lev2_sonnet_visual.py replays natural-visual-01,
changing ONLY model from claude-haiku-4-5-20251001 to claude-sonnet-4-6 (the
Sonnet version in repository rate config). Exact prompt, full page + four crops,
OCR/context, temperature=0 and max_tokens=4000 retained. One call, no retries.
/private/tmp/estimation-v6-2-lev2-natural-visual-sonnet-01.json completed in
23.499 s, 8619 input / 1096 output tokens, end_turn, no cache hits. Matching
-raw.txt and .html retain untouched answer/prompt. Response model confirms 4.6.
Plan 001 identified correctly; 003 front elevation; 004 called 'side (facade
from the short perpendicular wall)', which serves the correct second-elevation
role, not another plan. 002 understood as volumetric corner kitchen. Do not
score literal front-vs-side terminology without considering elevation of each
wing. Basic view classification improved on this controlled case, but full
object understanding NOT accepted: 45-degree end moved to corner junction,
incorrect tall/standing-cabinet claims and view correspondences remain. No
Cabinet Block continuation, drawer counting, schema acceptance or production
integration tested with Sonnet.
Approximate standard API list-price cost: $0.042297, versus Haiku $0.011753;
rates verified https://platform.claude.com/docs/en/about-claude/pricing
Sonnet 4.6 $3 input/$15 output per million, Haiku 4.5 $1/$5. This is calculated
from usage, not invoice readback. Input images/context make short output nonzero
cost; no multi-object timing extrapolation accepted.
Call-budget clarification: current local module diagnostic is TWO Analyze
provider calls, Calculation excluded. Prepending Sonnet classification makes
THREE; replacing the existing first interpreter keeps TWO. Neither production
choice approved by this diagnostic. Do not conflate original logical Analyze/
per-object Calculation stages with the current local module call count.
Important new discovery while checking official rates: the tested Haiku is
4.5, not the entire current Haiku family. Official overview lists Haiku 5.5,
released 2026-10-07, claude-haiku-5-5, at $0.10/$0.50 per million for prompts
up to 100k tokens; account availability and performance on our data UNVERIFIED.
Source: https://platform.claude.com/docs/en/models/haiku-5-5/overview
API guide says omit temperature/top_p/top_k; default adaptive thinking means a
future probe must disclose API differences, not claim a model-only request diff.
OWNER-APPROVED FOLLOW-UP / FIXED ENGLISH TYPES, 2026-11-05, same 3.17.4.5:
Status: active, P1. Outcome: reliable island classification with only ID:type
output, using Haiku; geometry matching remains auxiliary. Owner approved an
English fixed taxonomy and a Haiku 5.5 probe, not a production route change.
[verified] /private/tmp/probe_lev2_haiku55_types.py retains exact previous
messages/images/OCR. Changes: system prompt, model=claude-haiku-5-5,
temperature removed per migration guide, output_config.effort=low.
max_tokens=4000 retained. No tools, retries, Cabinet or Calculation.
Probe -01 failed to connect inside sandbox before response. Network-enabled
probe /private/tmp/estimation-v6-2-lev2-haiku55-types-02.json completed:
1.916 s, 11629 input / 66 output, zero thinking tokens, end_turn, actual model
claude-haiku-5-5. Raw answer, literally:
  island ID: p1-view-001: Top view
  island ID: p1-view-002: Axonometric view
  island ID: p1-view-003: Front elevation
  island ID: p1-view-004: Side view
Strict format FAIL due literal 'island ID:' prefix. Script's strict parser
correct_count=0 is NOT semantic accuracy: after ignoring that prefix the
owner-agreed labels match 3/4; 004 is side instead of second-wing front.
No plan/elevation confusion in this answer. -review.json records the distinction;
-raw.txt and -prompt.txt preserve exact response and English prompt.
Estimated standard list-price cost $0.0011959, not invoice readback.
Model and prompt changed together, so separate causal contributions unproven.
No production/shared-code changes; no new accepted checkpoint. Accessible 5.5
route confirmed for this account, general quality not established by one case.
OWNER CLARIFICATION / LANGUAGE AUDIT / NEXT BOUNDARY, 2026-11-05:
Owner accepts Side view for 004. Accepted semantic classification for this case
is therefore 4/4, not 3/4; the literal prefix format defect remains. Preserve
original artifact and strict-parser result as historical evidence. No new
request was run and prompt-versus-model causal attribution remains unisolated.
Owner confirms the old detailed Island Map is superseded by simple view-type
classification. Do NOT translate or polish the old map/correspondence contract.
Next requested discussion is returning to Cabinet Block using classifications
AND original complete evidence, not labels alone. Full integration has not yet
been implemented; successful classifier is currently a local probe only.
User requirement: all agent instructions and generated workflow text in English;
retain original source evidence, multilingual aliases and quoted examples.
[verified] Audit: Estimation checkout f20e343 + current local changes, and
Detection checkout /private/tmp/costerly-detection-v846 at 8eb87f1. Checked 34
Estimation prompt files, agent Python/inlined request construction, provider
entrypoints, and Detection prompt/inlined sources. Russian instructions found
only in the superseded V6.2 Island Map file and two inline blocks in
estimation_understanding_agent.py (isolated-map and module-selection paths).
The otherwise English estimation_understanding_v6_2.md explicitly requests
Russian human-readable output. Other Cyrillic prompt occurrences are source
examples (legacy Detection, Naming, material facts, Price Source); Python
occurrences elsewhere are regexes, transliteration or UI/report text, not
Russian instructions. No remote production runtime verification in this audit.
No translation/model/source-code edits made in this turn. Existing local dirty
work preserved. Remaining P1 requirement: integrate simple classification with
Cabinet Block and English instructions/output without reintroducing old map.
Owner-requested global Haiku 5.5 migration, including Detection: DEFERRED, P2,
explicitly 'later'; no model settings changed. Separate migration verification
must cover sampling compatibility, token budgets, tools and regressions.
Earlier agent suggestion to run 4.5 control is not the next active task; owner
redirected discussion to Cabinet Block. Held-out classification tests remain
pending, not evidence against acceptance of this single corrected case.

OWNER-APPROVED HAIKU 5.5 CABINET REPLAY, 2026-11-05, same 3.17.4.5:
Status: active, P1. Owner asks to move onward with 5.5 and retry the existing
whole-object/Cabinet task. Current execution scope stated before work:
experimental Estimation first cycle only, no Detection/production migration.
[verified] Local agent now uses claude-haiku-5-5 for direct understanding,
isolated classification and both tool-selected Analyze requests; low effort,
no temperature/top_p/top_k, max_tokens caps retained. Full source evidence
and any adaptive-thinking signatures remain in the tool continuation.
Replaced old detailed Island Map with island_types [{view_id,type}] and the
approved nine-type English instructions in estimation_island_types_v6_2.md.
Removed superseded local map prompt, whose prior contents remain in saved
request artifacts. Two provider calls remain: classify/select module, then
apply returned Cabinet policy and produce the existing understanding contract.
No separate classifier/reviewer call. Prompt, output and local report text are
English. Source-language data and aliases remain untouched. All classification
coverage/ID/enum checks remain; no mandatory invented correspondences.
Standalone classification produces only ID:type lines; legacy --map-only CLI
flag is an alias of --classify-only, not a second implementation.
[verified] /private/tmp/estimation-v6-2-lev2-haiku55-cabinet-01.json:
15.046 s, TWO calls, both actual response model claude-haiku-5-5. Call 1
4.585 s cumulative; whole evidence byte-equivalent in initial messages to
natural-visual-01, no accepted labels/counts injected. Input/output total
28689/3208, approximate standard list-price $0.0044729, not billing readback.
Raw stage TXT, HTML report and -review.json retained beside witness.
Reference/schema checks PASS. Four view types correct; Cabinet selected;
drawer function, two lift-up fronts, detached wall unit and countertop found.
Semantic acceptance PARTIAL, not ready for Calculation: drawers quantity=null
instead of five; grouped parent/front semantics persist; chamfered free end
misplaced at the junction; tall open frame simplified into hinged storage;
unsupported appliance housing appears in exclusions. No automatic retries,
no hardware totals or material Calculation, no DB writes, no deploy/checkpoint.
Next proposed diagnostic: preserve successful classification and make the
Cabinet output distinguish physical parent assemblies from counted moving
fronts using the existing front-group contract. This is not implemented by
this replay and must not be disguised as a classifier fix or a third reviewer.
Global 5.5 migration remains pending outside this first-cycle experiment;
Detection and other model callers have NOT been migrated. Existing production
checkpoint and unrelated dirty changes preserved. No claim of general model
superiority or prompt-only causality from this combined change.
Verification: 75 focused tests passed (understanding, module/classification,
V6 replay, structural BOM, visual evidence); git diff --check passed. Tests
cover two-call sequencing, unchanged evidence, exact ID/type schema, rejection
of prefixed/duplicate/foreign IDs, English instructions, unsupported sampling
parameter omission and thinking-signature preservation. One added empty-answer
test initially expected ValueError, corrected to the existing adapter's
RuntimeError; provider behavior was not changed to satisfy the test. Unit tests
do not establish semantic acceptance. Language scan found no Cyrillic in the
new instruction sources or local report generator.

OWNER-APPROVED CLASSIFICATION + FRONT COUNTS, 2026-11-05, 3.17.4.5:
Status: active, P1. Applied the exact approved English prompt to
agents/prompts/estimation_front_count_v6_2.md and the existing local probe CLI
as --count-fronts, mutually exclusive with --classify-only. One combined
request for one object; not a third request or a production architecture
replacement. The two-call Cabinet route remains available and unchanged.
Existing evidence preparation and island validation reused. Added bounded
front-group/reference/count/total validation; unknown counts propagate null,
absent types total zero, no silent count repair. No hardware/Calculation.
[verified] /private/tmp/estimation-v6-2-lev2-haiku55-front-count-01.json:
same initial messages as cabinet-01, actual Haiku 5.5/low, 20.122 seconds,
one call, 12371 input / 4056 output tokens (2744 thinking), estimated standard
list cost $0.0032651. No ground-truth labels/counts injected or automatic retry.
Raw result: drawer groups 2 + 3 = FIVE, lift-up fronts TWO, hinged doors 18,
total fronts 25. Four semantic view directions correct. Drawer/lift counts
match owner-described case. Door total is model output, NOT accepted truth:
right-hand tall side/frame counted as a door and other groups need review.
Strict contract FAIL: model emits top_view/axonometric_view/front_elevation
instead of the declared labels, plus Markdown fences. Shared JSON extractor
strips fences; enum validator rejects. Read-only diagnostic translation of
enum spelling on an in-memory copy confirms remaining schema/references and
all arithmetic pass. Original failed artifact and raw text remain unchanged.
Unsupported mm values also appear in location strings; dimensions were not
requested. Prompt/report/raw/review artifacts retained, none auto-opened.
92 focused tests passed, git diff --check passed. This establishes requested
drawer/lift count improvement, NOT full front inventory or production success.
Next proposed check: resolve questionable door groups and exact output enums
without disturbing successful counts; no extra reviewer/model call authorized
or executed in this experiment. Classification/counting-only performance must
not be presented as equivalent scope to prior full object understanding.
Owner preference: do not automatically open code, reports or results; user
opens them when wanted. No tab was opened during this experiment.

OWNER BENCHMARK / DOORS VERSUS SIDES, 2026-11-05, 3.17.4.5:
Status: active, P1. Lev 2 owner-counted benchmark: 15 hinged doors, with 16
acceptable only for the specifically ambiguous narrow end door; never more.
Five physical drawers imply five slide sets; two lift-up fronts imply two
gas-lift sets under existing hardware policy. Front-count stage emits fronts,
not counts of individual struts or hardware totals. Nominal total fronts 22,
accepted upper total 23 for the stated end-door ambiguity. These numbers are
review criteria only and MUST NOT be injected into the model's prompt/evidence.
Owner refinement: distinguish DOOR ROLE from CARCASS SIDE ROLE before using
rectangle proportions. A door closes an access opening; a side bounds the
carcass. Very narrow/tall strips default to fixed sides/fillers/posts unless
explicitly identified or depicted as operable. Do not mistake foreshortening
or an edge-on normal door for a physically narrow front. No hard numerical
aspect-ratio cutoff, source cleanup, new geometry engine or extra model call.
Applied identical policy intent to current count prompt and existing Cabinet
Block understanding policy so later reuse retains the instruction. Only the
count prompt changes in the controlled front-count-02 request. Existing exact
enum/Markdown issue deliberately not patched in this visual-policy experiment.

[verified] Repeat front-count-02, prompt r02: 20.205 s, one Haiku 5.5 call,
12573 input / 4331 output tokens (2882 thinking), estimated cost $0.0034228.
Exact request comparison with 01 shows ONLY system changed. Types now use
declared enum labels; existing JSON parser strips Markdown fences. Schema,
references and arithmetic pass, but actual counts remain 18 doors, 5 drawers,
2 lift-up fronts, 25 total. Door benchmark FAIL (15 preferred, 16 maximum).
Tall return-end element still counted as an inferred door. Drawer uncertainty
claims possible overlap while count_basis says clear; do not claim robust
cross-view association just because total five matches. No semantic gain in
door count from this added policy in this run. No automatic retry or deploy.
Saved front-count-02 raw/witness/review; nothing auto-opened.

PROMPT REVISION TRACKING, owner requirement, same 3.17.4.5:
Keep product version V6.2 and work number unchanged. Prompt revisions are
explicit identities, not new product iterations:
- estimation_front_count_v6_2_r01: approved classification + count task;
  experiment front-count-01. System SHA256
  427c7f0ecf49e2596f62c0eb7a22d9275ab8c87e79c9ef874ae8dd09e63de918.
- estimation_front_count_v6_2_r02: same task plus doors versus fixed sides and
  narrow-strip policy; experiment front-count-02. System SHA256
  c9dbf340d347c48710cd770b4113208c887294b106492ba5c0bba27c0a13b9a7.
Current prompt content exactly matches the r02 provider request. Historic raw
request artifacts remain untouched; review sidecars and this ledger identify
their revisions. Future --count-fronts witnesses persist prompt_version and
actual-system prompt_sha256 alongside full request hash. Successful agent
results also expose both. A revision/fingerprint regression test prevents
unrecorded current prompt edits. Revision numbers are never reused.
Verification: 93 focused tests passed; prompt numbering changes require no
paid model retry because the actual system content did not change.
Next recommendation: inspect the reported door groups against owner markup
to locate all extra doors before another broad prompt variation. Classification
and drawer/lift counts remain the preserved partial result, not a full checkpoint.

OWNER-REQUESTED FRONT OVERLAY, 2026-11-05, 3.17.4.5:
Status: completed deliverable, P1. r02 has no per-front coordinates, so an exact overlay of
that old answer cannot be reconstructed honestly. Owner authorizes a visual
overlay; r03 obtains new model-authored individual front boxes and useful
excluded-side boxes. Do not describe r03 boxes as r02's hidden detections.
Prompt revision estimation_front_count_v6_2_r03, system SHA256
81b49dc8d2dd4c33a7459d824178ea8601ba241370a401e530bed2748dab0bb0.
Same counting rules; added per-front id/view_id/bbox_1000 and excluded_surfaces.
Each physical front gets one canonical view box. Coordinates normalized to
0..1000 on EXACT supplied labelled detail image, INCLUDING generated header.
Known group counts must equal number of front boxes. No count hints injected.
max_tokens raised 6000 -> 10000 for annotation output, same Haiku 5.5/low and
60 s timeout/no retries. This is a diagnostic schema revision, not production.
tools/render_estimation_front_overlay.py renders exact model coordinates with
Pillow onto saved request images, not generative image editing or manual box
placement. Full-page inverse transform accounts for existing .015 crop margin
and 32 px generated header. Separate full-page/detail PNGs and coordinate JSON
retain source mapping. Invalid coordinates stop rendering; header overlap is
reported rather than silently shifted. Overlay is model output, not ground truth.
104 focused tests passed, including annotation counts/IDs/bounds, coordinate
transform, original-artifact preservation and no output overwrite. Requested
image may be shown inline; do not automatically open report/code tabs.
[verified] front-count-03 completed in 29.021 s, one actual Haiku 5.5 call,
13228 input / 6324 output tokens (3507 thinking), estimated cost $0.0044848.
Changed request fields versus r02: system and max_tokens only; images/context
unchanged. Schema/references/arithmetic/annotation coverage pass. Result:
17 doors, 5 drawers, 2 lift-up fronts, 24 individual front boxes + 3 exclusions.
Door semantic benchmark still FAIL (15 preferred, 16 maximum). No production
or inventory checkpoint. Overlay deliverable completed and visually inspected.
Saved /private/tmp/estimation-v6-2-lev2-haiku55-front-count-03-overlay-page.png,
-overlay-details.png, -overlay-coordinates.json, -review.json plus raw witness.
No coordinate warnings; full-page and detail images inspected. Approximate
boxes follow individual source panels without manual correction. F24 explicitly
counts tall return-end rectangle as hinged; X03 excludes adjacent side strip.
F06 above the two drawers also counted as a door, requiring owner/source
confirmation of physical role. These are r03 annotations, not r02's hidden
boxes. Show requested image inline only, no automatic file/report navigation.

OWNER-APPROVED FRONT COUNT r04, 2026-11-05, same 3.17.4.5:
Status: completed experiment, not selected. Owner returned to r03 as sufficient
for now; further front refinement deferred. Owner identifies r03 F01 and F24 as side/longitudinal
carcass depictions, not operating doors. These IDs are feedback about r03 only,
not stable cross-run IDs and MUST NOT be embedded into the next prompt.
Applied exactly the proposed generic instruction: count using clearest
elevation, use an available axonometric/perspective view to establish whether
the candidate closes an opening or forms a fixed side/partition/support.
Do not drop fronts merely because hidden in axonometry; retain uncertainty.
No change to model/images/settings/schema in the inference. One call only.
Prompt identity estimation_front_count_v6_2_r04, system SHA256
52d6f563f94add159d2b9c457eedc4dd31bbe47011e293c8bf0b68e266b95a99.
104 focused tests passed before the live run. Preserve r03 artifacts; current
experiment is not an accepted inventory checkpoint until its actual front
selection is reviewed, even if totals happen to match.
Completed r04: one Haiku 5.5 call, 26.487 s, 13424 input / 5805 output tokens
(3166 thinking), estimated standard-list cost $0.0042449, not billed-cost
readback. Saved request differs from r03 only in system prompt. Returned
15 hinged doors, 5 drawers, 2 lift-up fronts, 1 unresolved, total 23.
Original contract validation FAILED: snake_case island type labels instead
of the exact allowed enum strings. Raw response also contains Markdown fences.
For diagnostic display ONLY, renderer now has explicit opt-in label alias
normalization with FORMAT WARNING. Original failed witness remains unchanged;
counts and boxes are untouched. Default strict behavior remains unchanged.
104 focused tests pass after this change. Full-page and detail overlays
visually inspected; no coordinate warnings or manual corrections.
Semantic result is partial, NOT accepted: r03 F24 is now excluded as X04,
but owner-rejected r03 F01 remains counted as r04 F07. Former r03 F06 is
now unresolved F12, not excluded. Thus 15 doors is not benchmark acceptance.
Witness: /private/tmp/estimation-v6-2-lev2-haiku55-front-count-04.json
Review: /private/tmp/estimation-v6-2-lev2-haiku55-front-count-04-review.json
Overlays: same prefix with -overlay-page.png and -overlay-details.png.
Earlier proposed next step was review of F07/F12. Superseded by owner's
decision to keep r03 and move to major assemblies; do not auto-restart this loop.
No production deployment or accepted-checkpoint change.

Cabinet Block restoration and raw-output request, 2026-11-05, 3.17.4.5:
[verified] Full operability rules were in the V5.2 assembly/BOM prompt, not
the V6.2 first-cycle request. Probe 01 did not invoke that agent or the existing
hardware composer. Owner authorized restoring those rules to understanding.
Local V6.2 prompt now includes lower shallow/stacked drawer fronts, upper/middle
landscape lift-up flaps, portrait bay-closing hinged fronts and fixed-screen
exclusion. Owner's typical 300 mm / occasional 400 mm drawer height is a soft
context heuristic only. No new template library, hardware engine or threshold
change: current hinges remain <=600:2, >600:3, >2000:4; slides/lifts remain sets.
Short Russian prose requested, redundant numerical dimensions excluded from
first-cycle narrative, enum example now uses valid single values. Prompt-only
experimental restoration is NOT a new accepted checkpoint.
[verified] Probe 02 uses byte-identical inputs/images/grouping context to 01;
actual saved request includes Cabinet Block rules. One Haiku call, 29.044 s,
11435 input / 2870 output tokens (01: 10867 / 2887). Structural validation passes,
but semantic acceptance FAILS: vertical lower facades called six drawers,
lift-up group remains unknown, separate hanging module misread as tall tower,
unsupported veneer and millimetre assignments persist. Still English and verbose
(11306 raw chars versus 10983); brevity/language requirement not achieved.
Do not treat validator success as product acceptance; no further prompt piling,
Calculation integration or deployment. Missing rules were one real omission,
not a sufficient explanation of all failures.
Raw unedited responses exported as
/private/tmp/estimation-v6-2-lev2-detection-01-raw.txt and
/private/tmp/estimation-v6-2-lev2-detection-02-raw.txt; report body is model fields
with HTML headings/escaping, not assistant narrative. Prior chat paraphrase
was the assistant's translation, not raw model output. User wants direct data.
45 focused understanding/structural/replay tests passed; git diff --check clean.
Baseline f20e343 remains the local code checkpoint, V5.8.2 production unchanged.

V6.2 real Detection-backed local probe, 2026-11-05, owner-authorized:
tools/probe_v62_lev2_detection.py reconstructs a LOCAL fixture from latest run
run_189150ebf62447fc958f7c23cc34e3bb, exact OCR/event/original hash above.
No persisted input_id fabricated: local-detection locator and local-render page
are explicitly labelled, no DB writes. Existing V6.2 request receives 1 full
page + 4 crops, 18 cited OCR blocks and existing Membership observations with
exact bbox-derived VG-to-view mapping and SF-to-OCR mapping. No Naming, no
island-description addition, no Calculation. Optional context appended only
inside this diagnostic process; production agent/prompt/runtime unchanged.
[verified] One Haiku call, 10867 input / 2887 output tokens, 29.297 provider /
29.571 total seconds, end_turn. Capsule/report:
/private/tmp/estimation-v6-2-lev2-detection-01.json and .html.
Raw output identifies L-shaped kitchen and countertop but fails acceptance:
labels 416/300/265 as mm without unit evidence, misplaces 45-degree end detail
at the L junction, conflates hanging cabinet with tower section, does not
resolve drawers or lift-up fronts, suggests unsupported veneer/wood-grain.
It answers in English despite Russian instruction and emits combined literal
enum strings drawer|hinged and visual_interpretation|construction_assumption.
Validator rejects unknown operation; raw HTML retained without remapping.
Several geometric descriptions repeat prior Detection Membership claims;
context-induced anchoring is a hypothesis until paired same-input comparison,
not a causal conclusion from this one run. No retry or compensating patch.
Preflight verified five images/four owned views/18 blocks/no Naming manifest;
16 understanding tests passed; git diff --check passed. Owner review pending.

[verified by code inspection] V6.2 consumes full pages, owned region boxes,
raw cited OCR/literals and available document_context. The local V6.1 handoff
adds all document pages/text as shared context; old immutable inputs do not
gain that context retroactively. Registry-to-public conversion retains view
boxes but drops original group IDs, visual descriptions, representation kinds
and membership grounds. Naming stores name_basis/category_evidence in usage
audit, not estimation_input_v4; V6.2 also deliberately omits object_name from
its model request. This is a boundary decision, not proof those observations
are useless or that every historic run retained a recoverable audit.
OWNER DECISION, 2026-11-05, P0, pending implementation within 3.17.4.5:
Do not use Naming labels, name_basis or category_evidence in Analyze. Narrow
the proposed upstream context extension to existing source-linked grounds
for grouping views into one physical object. Do not add island-description
generation or require it from Detection. Earlier broader observation-layer
proposal is superseded by this scope; grouping grounds remain fallible
upstream interpretations, not source facts or authority to alter membership.
Next bounded verification: retrieve actual grouping grounds and exact view
mapping for the same Detection run; if unavailable, report missing evidence,
never reconstruct it as Detection output. Compare identical Haiku inputs
with/without those grounds, keeping Naming absent and all images unchanged.
Assess whole-object function, major assemblies, operability, material basis,
cross-view agreement and latency. LF1 and real Detection-backed Lev 2 are
the intended cases; source-only Lev 2 is not handoff acceptance. Review the
short reports with owner before promoting the first cycle to a diagnostic
UI release. No Calculation or automatic estimate publication in this step.
No runtime, Detection, UI or deployment change made by this audit.
Audit verification: 29 passed, 3 existing shadow-handoff failures (OCR filtering
and legacy preview-artifact expectations), 1.96 s. No implementation edits;
these failures were already listed in the V6.2 full-suite baseline.
LATEST OWNER CONSTRAINT: production Analyze and Calculation must remain Haiku,
fast and inexpensive. Stronger models may be diagnostic comparisons only;
their passing results do not establish V6.1 acceptance. Improve prompts,
bounded contracts and deterministic tools, not the production model tier.
Haiku witness 15 still failed semantic acceptance (drawers omitted / screen
treated as carcass). Diagnostic 16 isolates visual understanding from the
large response contract. Stronger comparisons 13/14 also remain unaccepted.
16/17 observations did not establish correct visual semantics; generated view
headers improved id association only. Full Haiku witness 18 again failed the
fixed-panel guard (24.62 s). Stop this prompt/presentation approach after two
unsuccessful full Haiku runs (15/18).
APPROVED, ACTIVE within 3.17.4.5: owner approved simplifying only the
model-facing Analyze contract; deterministic compiler owns dependent layer,
edge-width and role expansion fields. Preserve one Analyze + per-object
Calculation, Haiku, existing persisted contracts and source authority.
Compact witnesses 19/20 remain unaccepted. Witness 20 completed in 48.93 s
without DB writes, but selected solid wood, wrong member/support counts and
incorrect geometry. Deterministic 40-mm finished / 2 x 20-mm purchased build-up
is supported; it is not proof that Haiku selects it reliably. Owner clarified
this is a possible construction, not mandatory stock thickness. Preserve
explicit 40-mm stock as one layer and count its edge only once. Evidence-first
implementation/diagnostics below continue the visual/axis investigation.
UNVERIFIED ACCEPTANCE: owner-visible inspection of construction/material
rationale. Facts retain it, but the new fields have no verified Object Detail
display path. No UI change without scenario agreement/live verification.
ARCHITECTURE STRATEGIES, USER REQUEST, within 3.17.4.5 (same outcome, no new block):
- ACTIVE, P0, strategy 2, evidence-first map, approved by owner: extend existing
  Dimension Graph/2VN with source-local dimension lines/endpoints, view candidates,
  indexed text/legend context and explicit interpretation provenance before
  construction. Preserve Haiku and immutable Detection membership. First gate:
  source-frame-correct LF1 line witnesses and a read-only full-cycle replay;
  later gates include legends and multiple objects. No manual template library.
  [verified] First local slice: raster/native candidate lines in source coordinates,
  explicit view/boundary readings, cross-page index links, scoped measurement
  references and conflict downgrade through 2VN. CPU-only LF1 preparation ~0.45 s.
  Full Haiku witnesses 25/26 completed in 79.33/80.86 s but remain NOT accepted:
  top-plan classification, material/thickness choices and geometry still wrong.
  Isolated projection probe 27 also called the plan a front elevation (1.98 s
  provider, 2,941 input / 90 output tokens). Prompt load alone is not established
  as the cause. Exact cached replay 28 verifies final guards without paid calls.
  Stop this combined-map prompt approach after 25/26, retain experimental code
  for comparison, no deploy. Cross-view dimensional diagnostics 29-37 completed
  locally; no accepted estimate. Code reconciles plan/side projections under
  recorded assumptions; correcting projections and withdrawing prior ownership
  still leaves wrong component dimensions. Compact geometry 36/37 took 5.02 /
  6.489 s provider time, but wrong top width / screen height / support section
  remain. Thinking-budget probe 31 did not fix perception. Trial 33 was an invalid
  intervention (solver abstained), not evidence against correction. New preflight
  stops no-op reconciliation before paid Calculation. Details/capsules in the
  existing V6.1 construction decision record. No production route added.
  Owner authorized continued bounded experiments without per-attempt approval.
  Preserve Haiku/materials-only and production boundaries. Diagnostic relation
  graph checks printed equalities/sums against line spans across existing views;
  no projection/physical ownership is promoted from numeric coincidence alone.
  Short outside-label dimensions/chain endpoints remain candidates, not arrowhead
  proofs. Ten-object latency/output capacity and live legend/UI acceptance are
  unverified; no automatic source-based claim from aggregate candidate counts.
- DEFERRED, P2, strategy 1, construction templates: retain as an alternative,
  not the current implementation. Owner rejects the manual preparation burden.
  Revisit only if evidence-first fails and owner chooses this trade-off.
- BLOCKED, P0, strategy 3, bounded targeted verification/repair: owner approved
  conditional third Haiku request after discussion of 29-37. Same work 3.17.4.5.
  One shared Analyze, per-object Calculation, then at most one targeted review
  for detected contradictions. No request when no contradiction is detected.
  Preserve source/assumption authority; revalidate patches deterministically.
  [verified] Implemented and tested in LF1 trials 38-40, NOT accepted: the
  verifier can choose an axis-compatible number for the wrong physical part.
  Fresh full cycle 39 took 74.26 s; verification took 3.878-6.043 s across trials.
  Trial 39's forbidden-axis patch was rejected atomically. Trial 40 corrected
  projection context and removed inherited narrative, but still selected a
  190 mm countertop width. Stop prompt-only retries of this candidate selector.
  Production integration/cache-version changes withdrawn; retain only explicit
  CLI --geometry-verification diagnostics. No deployment or DB writes.
  Cached 41/42 verify default two-stage behavior and opt-in review separately,
  zero paid calls. Full suite 1740 passed, same 10 baseline failures.
  Blocker: physical dimension-to-component ownership, not request scheduling.
  PENDING, AGENT PROPOSAL within this objective: test explicit spatial boundary
  attachment before choosing a numeric candidate; revise the interpretation
  contract only after owner discussion. Do not add a fourth request by default.
  Whole-cycle materials/counts/geometry acceptance remains open.
DEFERRED, AGENT PROPOSAL: <=60 s single object / 2-3 min ten objects, bounded
parallel Calculation and incremental ready-object visibility. These were not
approved SLAs; routing/concurrency optimization follows functional acceptance.
No new orchestration worker or UI behavior is authorized by this deferral.

CHECKPOINT, deployed, pending authenticated interaction witness, 3.17.4.4
Estimation V5.8.2 handoff recovery, 2026-11-04: [verified] V5.8
(`512bf6e`) prepared navigation targets and V5.8.1 (`7405e67`) preserved an
active or pending estimate during File Review and Objects navigation. The
owner's V5.8.1 live test confirmed that Back and Continue no longer reset the
calculation, but surfaced a distinct terminal failure:
`Expecting value: line 1 column 1 (char 0)` left an object visually at 45%.
V5.8.2 (`710165d`) retries only the safe content-addressed immutable Storage
upload when its response body is blank, then ends a final handoff failure as
`Failed / 100%` rather than a live `Estimating` row. Production marker:
`estimation-v5.8.2-handoff-recovery`. Local verification: 403 focused tests;
full suite `1639 passed, 10 failed` with the established unrelated baseline.
Pending acceptance: a fresh authenticated LF1 run must retain its estimate
through Back/Continue, complete after one transient Storage response, or show
terminal `Failed` after three failures. This does not accept Cabinet Block,
2VN, Analyze/Calculation, materials, pricing or visual transition quality.
Record: `notes/ESTIMATION_V5_8_2_PRODUCTION_CHECKPOINT_2026_11_04.md`.

ACTIVE, V6.59, P0, New Estimate to Upload client-transition observability:
The evidence rejects server-side auth, Supabase, and Upload rendering as the
source of the reported 3-4 second warm navigation: prior successful
`New Estimate → Upload` runs reached Python app-ready in 8-18 ms and browser
styled in 0.5-2.0 seconds. The latest affected transition produced a browser
timeout after 15 seconds with `python_runs=0`, so its callback never reached
the app. Preserve the existing native callback and diagnose the client
transition path, rather than adding a cache around unrelated server work.
Acceptance: a live authenticated File Review → New Estimate transition records
one `browser.transition_ready` or `browser.transition_styled`, one Python run,
and no client timeout.

IMPLEMENTED locally, not deployed, V6.59 New Estimate warm-transition repair,
2026-11-03:
[verified] The V4.29 recovery treated a missing Upload app-ready after 900 ms
as a dead callback. That threshold overlaps the already measured 0.5-2.0
second normal styled-transition range, so it could destroy a live warm
Streamlit session and force a fresh iframe load. The repair waits 2.5 seconds
only for an explicit callback acknowledgement written by `_open_new_estimate`
and consumed by the next app run. A real callback cancels recovery even while
Upload is still rendering; a truly absent callback alone receives the existing
clean-iframe fallback. Runtime events now separate callback reset time,
callback-to-run time, browser acknowledgement, and fallback activation.
Pending acceptance: an authenticated File Review → New Estimate click must
reach Upload without `browser.new_estimate_iframe_recovery`; the trace must
contain `server.new_estimate_callback_consumed` and
`browser.new_estimate_callback_received`. No deployment was made.

IMPLEMENTED, pending production interaction witness, Estimation V4.28, Object Detail screen-read repair, 2026-11-03:
[verified] A completed Object Review had no detail cache and loaded object,
lines, material plan, facts, and company settings in a serial request chain.
The bounded repair clears the stale outer Object route as soon as New Estimate
is clicked, preserves the native server callback, reads the independent first
Review projections concurrently, and prefetches ready Object Details through a
two-worker read-only queue after Objects is already visible. Snapshots are
discarded after any detail edit, approval, estimation completion, recalculation,
or New Estimate. The prefetch result is advisory: a failed or missing snapshot
falls back to the normal authorized read. Local targeted checks: 20 passed;
the wider route and detail group: 71 passed, with two pre-existing unrelated
static-observability failures. Pending acceptance: live authenticated timing for
both New Estimate → Upload and Objects → Review, with no stale route, no empty
File Review terminal state, and no stale detail after an edit.

IMPLEMENTED, pending production interaction witness, Estimation V4.29, New Estimate dead-callback recovery, 2026-11-03:
[verified] The V4.28 production trace `f232f994-ca20-4283-87f0-8c5aac30b892`
recorded a New Estimate click with `python_runs=0`; two later clicks emitted a
visual `transition_styled` event but no server rerun. A visible Upload marker
therefore cannot be accepted as a state reset. V4.29 replaces the outer URL
with `/` at click time and keeps the transition pending until a real Upload
app-ready. If no matching server run arrives within 900 ms, the wrapper reloads
only its iframe after removing all workflow parameters and setting
`screen=upload`, which creates a clean Streamlit session. Acceptance: the next
production New Estimate both shows `/` immediately and reaches Upload without a
timeout, then Last Estimate restores the latest completed File Review.
Full implementation checkpoint and cross-chat handoff:
`notes/ESTIMATION_V4_29_NAVIGATION_AND_OBJECT_DETAIL_IMPLEMENTATION_CHECKPOINT_2026_11_03.md`
and `notes/ESTIMATION_V4_29_FULL_CHAT_HANDOFF_2026_11_03.md`. They do not
close this active item: the next required evidence remains one authenticated
V4.29 interaction witness with runtime trace readback.

CHECKPOINT, owner-accepted, V6.38-V6.40 quantity and Document Identity:
`notes/DETECTION_V6_40_DOCUMENT_IDENTITY_QUANTITY_CHECKPOINT_2026_10_27.md`.
The ordinary `300119_f2.pdf` witness published `ПОДДОН=5` and `СТЕЙШН=1` from
bounded native caption facts, and semantic title-block fallback published its
Project, Client, and Partner without a new model call. Red `QTY` now means only
conflicting explicit quantities for one locked Object. Default one for a unique
built-in kitchen, cabinet system, counter, or other integral object is not a
warning. V6.37 Ada, Page23, Assembly Set, router, object boundaries, Evidence,
Naming, Preview, and Estimation are protected and unchanged. Commits `06e54ee`,
`9686459`, and `f4312d9` are pushed to `main`; Railway health remains pending
independent observation.

ACTIVE EXPERIMENT, V6.41, P0, large-document token preflight and full-page
Discovery batches:
`Morbergs.pdf` failed before any Claude response because its ordinary Discovery
payload was 271,060 input tokens, above the active 200,000-token maximum. The
document is only 22 pages, but every 200-DPI rendered page and its Fusion
context are currently sent in one request. Owner approved an isolated V6.41
experiment: ordinary non-anchor files whose conservative local estimate exceeds
150k tokens retain their complete pages, but Discovery runs in measured batches
targeted to 105k estimated / 160k exact input tokens. Each batch preserves
absolute page numbers and page coverage, and Membership Review still receives
the complete global post-Discovery set. V6.41 must not change Ada, Page23,
Assembly Set, quantity, or Evidence ownership. Pending: deploy and Morbergs
acceptance test, including the recorded batch token audit and final Review size.

ACTIVE EXPERIMENT, V6.42, P0, bounded multilingual Fusion fallback:
Use a content-only gate, not `unknown` metadata, when Fusion contains a material
amount of text outside the primary English/Hebrew/Russian workflows. The gate
may schedule one bounded, text-only Haiku read of facts already owned by locked
Objects and the existing title-block crops for Document Identity. It may fill
an absent Project, Partner, Client, source code or explicit quantity only with
a cited local literal. It cannot change router choice, Island geometry, Object
membership, Naming, or Evidence ownership. No static Latvian aliases are being
added. Protected: V6.41 batching and all accepted routes. Pending: deploy and
Morbergs validation of identity, CF codes, explicit quantities, timing and cost.

ACTIVE, V6.43, P0, Processing forecast to first File Review:
Replace the decorative OCR/Detection/Saving easing curve with one elapsed-time
forecast to File Review. The bar uses the median of at least three successful
same-company cycles in the matching page-count bucket, otherwise a conservative
cold-start estimate. It must update without new model-provider calls, route changes,
or blocking Naming, Preview and Document Identity. Persist a compact stage
ledger inside the existing orchestration event so later forecasts can separate
page preparation, OCR, Fusion/route, Discovery batches, Review, Registry and
publication. Protected: Detection behaviour and the accepted Processing to File
Review handoff. Pending: deploy and a live ordinary-file interaction check.

ACTIVE, V6.44, P0, retry isolated invalid Discovery-batch core geometry:
For V6.41 budgeted ordinary Discovery only, validate each batch's semantic
`core_bbox` containment before it joins the global Registry. If one batch has
an invalid physical core, repeat only that batch once with explicit geometric
correction feedback and preserve every accepted batch unchanged. Record the
failing Island and rule, retry input size, provider attempt and final outcome in
the existing batch audit. Never clamp the core to its envelope or weaken the
fail-closed final validator: core geometry controls deterministic evidence
ownership. Protected: valid ordinary, Assembly Set, Ada and Page 23 detection;
no new provider call or altered output on valid runs. Pending: deploy and
Morbergs retry validation.

CHECKPOINT, V6.23 bounded Naming and Quantity review presentation:
`c990495`, deployed and audited as
`notes/DETECTION_V6_23_NAMING_AUDIT_CHECKPOINT_2026_10_26.md`. HSL returns to
11 OCR pages, $0.044 OCR cost and a 72.243-second initial cycle. V6.23 retains
the V6.22 Kitchen-oriented Naming pass, but its final names are not accepted:
the model correctly proposes `Kitchen` from sink/cooktop evidence, then the
contradictory `category_evidence.cue` validator rejects those rows and leaves
source codes in the UI. Do not change Naming, routing, identity, quantity,
order, bbox, evidence-page membership or View ownership at this checkpoint.

SUPERSEDED, V6.24 compact Kitchen Naming repair: the model complied with its
compact Kitchen cue tokens, but the runtime then rejected visual evidence whose
`visual_group_id` was blank. The object crop had a valid locked group id, but
the model never received it. Preserve the compact cue and 12-word basis rules.

CHECKPOINT, V6.25 bound visual Naming evidence: `a34497b`, deployed and
accepted at `notes/DETECTION_V6_25_HSL_CHECKPOINT_2026_10_26.md`. HSL run
`run_2dceafe62d3440668ca56b6b74101cc8` produced 9 objects, 11 OCR pages at
$0.044, a 69.777-second initial cycle, accepted Naming validation and 9/9
created previews. P11's three evidence regions are one locked object, with
`view-033` selected as its presentation source. The names are operationally
accepted but not a semantic-quality benchmark. Do not reopen Naming, router,
object identity, quantity, order, bbox, evidence-page membership or View
ownership without separate explicit approval.

CHECKPOINT, preliminary, V6.26 assembly-set compiler: retain the V6.12
pre-Sonnet category and V6.11 validated scope observation, but make a
confirmed `assembly_set_candidate` publish one locked commercial Object only
after Registry validation. The compiled Object has quantity one, uses cited
root pages as identity anchors, retains every Registry-owned Island, and
includes every uploaded physical page in its Estimation evidence so authored
notes, material schedules and detail sheets remain available. Shared order,
title-block, date, material, page count or numbering alone still cannot
trigger this compiler. If scope is ordinary, missing, or its roots are not
Registry-owned, preserve the original Registry packages unchanged.
The first V_Cabineter production run correctly selected `assembly_set` and
confirmed scope, but safely retained 14 Registry packages because Discovery's
provider Island IDs had not yet been normalized to Registry `view-NNN` IDs.
V6.26.1 maps those cited scope references before compilation. The same patch
also promotes a repeated explicit `Order`/`Заказ` code to a project identifier
only when no explicit Project field exists and it occurs on a strict document
majority. It must not infer client or partner facts.
V6.26.2 treats a rejected one-object Naming project fallback as a successful
Naming completion when Document Identity has concurrently published a stronger
project value. The fallback remains non-authoritative and its refusal is kept
in the Naming audit rather than surfaced as a false failure.
Owner accepted the preliminary checkpoint at
`notes/DETECTION_V6_26_ASSEMBLY_SET_CHECKPOINT_2026_10_26.md`: production run
`run_41fdb9846abb4c2b9e5cfc0d194b6fe6` on `V_Cabineter.pdf` selected
`assembly_set`, compiled one quantity-one Object, retained all six pages and
17 Views, and persisted `Order 1208`. V6.26.2 `c9cb521` is deployed to remove
the false red Naming failure caused by the concurrent Identity update, but
that narrow presentation repair has not yet had a production re-run. The
separate `V_Stair.pdf` run is a negative guard only, not a second assembly-set
benchmark: it correctly retained the ordinary route and one independent stair
railing Object.

DEFERRED, P1, assembly-set breadth validation: test a second genuinely
multi-sheet built-in/cabinet dossier after the V6.26.2 deploy, plus protected
Adda, HSL, and Page23 regressions. Do not expand the compiler rule from one
accepted V_Cabineter dossier or use object count alone as quality evidence.
`V_Stair.pdf` cost is not comparable to Cabineter: the former selected
`ada_sparse_multi_object` and Sonnet Detection, while Cabineter selected
`assembly_set` and Haiku. The latter's pre-V6.26.2 failed Naming event did not
record model tokens/cost, so `TC1 $0.105` is incomplete rather than a final
ten-cent total. ACTIVE, P0, V6.27 scope-scout experiment: retain the Ada guard
until a separate short Haiku observation classifies only its current candidates
as `single_assembly_candidate`, `multi_object_risk`, or `uncertain`. Only the
first result may use the existing Haiku Assembly Set Registry and compiler;
the other two retain Sonnet Ada. The scope scout cannot create Islands, merge
objects, or use shared title/order metadata as sufficient proof. Its cost must
be stored as a separate Detection usage event. V_Stair passed the local shadow
gate as `single_assembly_candidate` ($0.013431, 28.873 s). Adda's local scout
result was unavailable after two environment-level attempts, so production
Adda is the unresolved gate. The experiment's production acceptance requires
Stair to compile one all-page Assembly Set and Adda to stay on Sonnet with its
accepted two-object boundary.

CHECKPOINT, V6.27 optional-scope validation: a live RFQ failed with
`V6.11 document scope witness references an unknown group`. The V6.11 scope
sidecar may authorize assembly compilation, but it does not own Discovery
Islands or ordinary Registry packages. Reject an invalid scope sidecar,
record the exact validation error, and continue with the unchanged Registry
result. Do not delete the unknown reference, rewrite its evidence, or compile
an assembly without a fully valid scope. Local regression must prove the
unknown-group case returns no validated scope and retains an auditable error;
production run `run_62392d84938242cfa7d83b6060e7ce0e` proved that the invalid
sidecar is rejected while the ordinary Registry retains one quantity-one Object
with all five pages and seven Views. Protected at `e9e8548` and tag
`detection-v6.27-invalid-scope-recovery-production-2026-10-26`.

ACTIVE CANDIDATE, P0, V6.28 bounded witness and Identity ownership: retain up
to eight existing group IDs in one scope witness rather than randomly dropping
valid evidence. Keep four roots, four witnesses, and the 180-character bound.
Split group-limit diagnostics from unknown IDs. Promote an explicit identical
`Title` to Project only when it repeats on a strict majority of OCR pages, with
explicit `Project` still taking precedence. Naming publishes Object names only
and must never write Project, Partner, Client, Author, or Date. Protect V6.27
failure recovery, Registry boundaries, quantity, View ownership, Evidence, and
all accepted Naming behavior.
Local verification: 129 relevant Detection, Identity, Naming, and evidence tests
pass. A read-only replay of production run
`run_62392d84938242cfa7d83b6060e7ce0e` returns grounded Project `Офис` from
page 1 and validates the original witness counts `4, 3, 5, 3` with no scope
error. Fresh production acceptance remains pending.
The full repository suite reports 1445 passed and 20 unrelated existing
Estimation, material-policy, and UI-contract failures; none touches the V6.28
files or protected Detection/Identity/Naming paths. Those failures are not part
of this candidate and were not modified.

CHECKPOINT, V6.29 Ada sparse-native-graphics route guard: the V6.27
scope-scout production gate accepted Stair correctly but falsely classified
Adda as one Assembly Set, collapsing its accepted two-object boundary. Preserve
the existing Ada Sonnet route before the scout when a document has at least 24
native graphic anchors and more than four times as many anchors as recoverable
source facts. This is a boundary-protective source-capability condition, not an
object-count claim or a filename rule. It skips the $0.010497 scout call on the
observed Adda signature, retains Sonnet, and leaves Stair and direct V6.26
Cabinet Assembly Set selection unchanged. Production acceptance: Adda must
remain on Sonnet and retain its two-object boundary; Stair must still compile
one all-page Assembly Set. The threshold is an experiment, not calibrated
universal policy.

REJECTED EXPERIMENT, P0, V6.31 ordinary Sonnet Membership Review: Lev_1
proved that Sonnet can semantically join its six Views into one correct Object,
but ordinary must remain the inexpensive, stable Haiku scenario. V6.31 is
reverted before the next test. Its result is evidence about the required
reasoning capability, not approval to make ordinary a mixed-model contract.

CHECKPOINT, V6.32 direct Ada classification from Mistral graphic
regions: retain exactly three scenarios, Page 23, ordinary, and Ada. Before
Claude, route an unlabelled one-page mixed/vector technical sheet to existing
Ada only when Mistral already exposes four through ten bounded graphic regions
on that page. This repairs the Lev_1 blind spot where the legacy image
inventory says one drawing but Fusion has six graphic candidates. Preserve Ada
directly and skip the scope scout for this evidenced boundary risk. The rule
does not identify commercial Objects, create a scenario, or alter Ada's
existing Sonnet/Mistral-anchor/V6.10 contract. Gates: Lev_1 must route directly
to Ada and assemble correctly; HSL stays ordinary; Adda stays direct Ada; Page
23 keeps its source-degraded route.

CHECKPOINT, V6.34 Ada V6.31 model split: retain the three
established routes and V6.32 router unchanged. Within the already selected Ada
contract only, execute the exact V6.31 two-call pattern: Haiku Discovery, then
one Sonnet Membership Review. Mistral graphic anchors remain the bbox boundary
authority, but V6.10 pairwise Review and Reconciliation are explicitly off for
this experiment. Persist the actual model and stage cost for each provider call,
then sum the mixed-model costs rather than billing all calls at Sonnet rates.
Gates: canonical Adda retains the accepted two-object membership, anchors,
bboxes, and Evidence package; Lev_1 retains its one-object result; ordinary HSL
and Page 23 are unchanged; measured cost and elapsed time are compared with the
V6.31 benchmark before any broader decision.

CHECKPOINT, V6.37 Ada covered-membership: the protected Ada route now retains
the V6.34 Haiku Discovery plus one Sonnet Membership Review shape, but treats a
multi-View hypothesis as a semantic group only after accepted pair-local facts
cover every declared View. It does not fabricate root-to-member edges or demand
a connected pair tree from complementary projections. `Adda.pdf` passed twice
with the benchmark Counter `{V2,V3,V5,V7}` and L-shaped `{V1,V4,V6,V8}`
groups. `Lev_1.pdf` passed twice with all six Views in one object. Four runs,
109 focused tests, exact run IDs, costs, limits, and protected behavior are in
`notes/DETECTION_V6_37_ADA_COVERED_MEMBERSHIP_CHECKPOINT_2026_10_27.md`.
Do not modify the Ada route, its model split, grouping rule, candidate queue,
object quantity, Evidence ownership, Naming, Preview, Document Identity, or
Estimation handoff without a separately approved benchmark.

RESOLVED, V6.22 grounded title facts and Kitchen Naming: retain the V6.21
deferred Naming lifecycle and locked Detection object contract. Build optional
`page_title_fields` during OCR/Fusion from explicit title-field label-to-value
evidence, including full-page Mistral Markdown only as explicitly marked
single-source fallback. Preserve `representation_kind` in the private
Registry-owned sidecar so deterministic preview and Naming crop selection can
prefer elevation over section. Extend the Naming response with object-local
`category_evidence`; Kitchen can cite a sink, faucet/mixer/tap, or kitchen
appliance, while strong categories such as Kitchen and Stair railing must not
publish without an object-local literal or visual cue. Do not change router,
object identity, quantity, order, bbox, evidence-page membership or View
ownership. First gate: HSL audit of title facts, selected source crops and
grounded category evidence. Then run Page23 and Ada regressions.

RESOLVED, V6.21 object-bound Naming evidence and presentation preview: retain
the V6.20 deferred Naming lifecycle and neutral File Review publication, but
make one deterministic Registry-owned front/elevation View available in two
strictly separate roles. It becomes `presentation_preview_bbox` for File
Review only, and its source crop becomes bounded visual context for Naming.
Full annotated pages and local OCR snippets remain in Naming. Do not pass the
UI preview field to Naming or Estimation, and do not change object identity,
quantity, order, evidence-page membership, or View ownership. When a repeated
title-block identifier family is a strict document majority, omit isolated
minority-family codes from the private Naming transport, so a project/file
code cannot be published as an object index. Acceptance: HSL produces stored
front/elevation previews, no `FTC201.06` prefix, and a terminal Naming audit
whose category decisions can cite object-bound visual/OCR evidence. Reassess
the P11 object split separately from Naming: it is a locked Detection-boundary
question, not a name rewrite.

RESOLVED, V6.20 Naming publication and cost lifecycle: preserve the V6.14
Detection checkpoint while repairing the V6.19 deferred Naming worker call,
show `TC1` for completed OCR plus Detection and `TC2` only after terminal
Naming, and keep File Review labels as neutral `Object NN` until one Naming
publication atomically applies the source index with the category name.
Acceptance: HSL performs one terminal Naming call, Naming cost/time appear in
the ledger and File Review, and the locked Detection object identity, count,
order, and evidence remain unchanged. File Review polling must not remount
visible metadata or object cards while no deferred work changes state.

CHECKPOINT, experimental, Detection V5.7.1 is recorded in
`notes/DETECTION_V5_7_1_EXPERIMENTAL_CHECKPOINT_2026_10_23.md`. It is not
accepted or deployed. The measured membership-edge path passes Page23 and
Adda in one run, but HSL regresses to 29 Object Islands and 10 packages.

SUPERSEDED EXPERIMENT, V5.7.1 MVP boundary experiment: start from protected
V5.6.1 checkpoint `5de4cf4`. Registry owns one full-page, non-overlapping
membership proposal for multi-View physical items. Runtime validates typed
facts, exclusive ownership and exact proof trees, but Dimension Similarity and
OCR-locality cannot overturn a valid visual membership proposal. First gate is
Page23 membership, then Adda, HSL and Metal. No extra model call, router,
Sonnet path or file-specific rule.

SUPERSEDED EXPERIMENT, V5.7.1 preserved both Registry evidence paths: direct
`semantic_facts` and membership-edge facts. V5.6 silently ignored direct
facts, so a valid typed criterion could not reach the supporting graph. Keep
the same validators and audit both paths separately.

RESOLVED, V5.7.1 local benchmark invocation: long runner commands return a
PTY session after 30 seconds and must be drained until completion. The prior
missing HSL/Metal reports were orchestration timeouts, not Detection failures.

SUPERSEDED EXPERIMENT, HSL V5.7.1 regression: a full run now completes, but produces 29
object-evidence Islands and 10 packages versus the protected 32/9 benchmark.
The visible losses are page 3 (2 rather than 3 raw Islands) and page 11 (four
raw Islands but only one object-evidence Island). Keep the V5.6.1 Island and
classification contract while isolating the membership-output change. Diagnose
Island recall and classification before considering V5.7.1 for acceptance.

SUPERSEDED EXPERIMENT, V5.7.2 isolates the V5.6.1 Registry prompt and JSON contract,
then deterministically adapts each accepted `object_hypothesis` into N-1
membership edges. HSL `v572-hsl-03` restored 32 Object Islands, but returned
10 packages. P04 was split into two complete hypotheses, while V5.6 merged
their components later through the same-page, 100-score Dimension
batch-confirmation edge `view-004` to `view-005`. The owner later clarified
that P04 may legitimately contain one to three products, so this historical
count is not evidence for either joining or splitting it. Do not use P04's
package count to justify a deterministic bridge or any other membership rule.

SUPERSEDED EXPERIMENT, V5.7.2 three-file regression evidence: Adda `v572-adda-01` passes
at 9 Object Islands and 2 packages. Page23 `v572-page23-01` returns 4/4: the
Registry emitted four forbidden singleton hypotheses, all correctly rejected,
so it created no membership edges. Metal `v572-metal-01` returns 51/11, not a
quality pass: it combines distinct marks OM-2 and OM-3 on P03, OM-1 and MP-1
on P06, and OG-1, OG-2 and OG-3 on P11 into individual hypotheses. Do not run
more regression documents or promote V5.7.2. Decide a membership contract that
can retain complete grouping without admitting singletons or merging explicitly
distinct author marks.

SUPERSEDED EXPERIMENT, V5.7.3 one-call visual-inventory and typed-pair experiment:
preserve V5.6.1 Island/classification rules, eliminate Registry package and
membership-tree output, and compile packages only from validated positive
pair facts plus Dimension Fingerprint/Weighted Similarity. Q is bounded by
concentric proximity: scored same-page pairs, one same-page fallback for an
unanchored proto-region, and only >=85 cross-page anchors. Registry output
must record full-page/crop image counts and bytes, every Registry text block's
character count, Q before/after counts, input/output tokens and their separate
costs. Do not change crop selection in this experiment, so a quality change
has one attributable cause. First benchmark Page23, then HSL, Adda, and a
membership-level Metal review. Target is a quality gate before a separate
crop/input-context cost experiment.

BLOCKED EXPERIMENT, V5.7.3 Page23 quality gate failed twice. `v573-page23-01`
returned 4 Object Islands but 2 packages because a single false
`direct_shared_structure` joined the independent shelving and door systems.
After a narrowly worded shared-member guard, `v573-page23-02` regressed to 5
Object Islands and 2 packages, with three unsupported single semantic merges.
The prompt-only route is rejected after two attempts. Do not benchmark HSL,
Adda or Metal on this state. Next diagnostic is deterministic semantic-proof
strictness: distinguish a real structural/topological identity proof from a
shared material, frame type, hardware or page-wide dimension before allowing
one typed fact to create a merge.

SUPERSEDED EXPERIMENT, V5.7.4 MVP recovery restored the exact V5.6.1 membership-first
Registry output contract, complete non-overlapping `object_hypotheses`, and
V5.6 deterministic package assembly. Retain Dimension Fingerprint and
Weighted Similarity as supporting/bridging evidence, not a replacement for
the Registry's full-page visual grouping. Retain V5.7.3 diagnostic telemetry
only: full-page and crop counts/bytes, each prompt-context character count,
Q counts, Anthropic input/output tokens, separate calculated costs and
duration. Do not add another model call, a router, Sonnet, crop changes, or
unproven semantic wording. First run Page23, then HSL, Adda and membership
review of Metal. Do not accept a single successful Page23 run as stability.

BLOCKED QUALITY GATE, V5.7.4 Page23 `v574-page23-02` and `-03` produced the
same invalid raw Registry response: five Object Islands and five forbidden
singleton hypotheses, all correctly rejected by runtime into five standalone
packages. Claude cost was `$0.018720` per completed run: 8,925 input and
1,959 output tokens; one full page plus three static crops carried 402,136
JPEG bytes, and text context was 10,821 characters. Historical successful
V5.6 traces returned hypothesis sizes `[1, 1, 2]`; current runs return
`[1, 1, 1, 1, 1]`. Do not spend on the remaining pack until the Registry
prompt explicitly reconciles a physically continuous drawing and alternate
projections of one fixture before outputting its Island inventory.

BLOCKED EXPERIMENT, V5.7.5 one-call visual-reconciliation experiment preserved the
V5.6.1 membership-first contract and V5.7.4 telemetry exactly. Before JSON,
Registry must reconcile a physically continuous depiction as one Island,
compare alternate projections, and remove singleton `object_hypotheses`.
No schema, Dimension, crop, package-runtime, router, Sonnet, or extra-call
change. Page23 `v575-page23-01` passes the narrow gate at four Object Islands
and three packages. The pack rejects it: HSL `v575-hsl-01` retains only 30
Object Islands and 10 packages, with P11 classified down to one Object Island;
Adda `v575-adda-01` retains nine Islands but merges all four sheets into one
package instead of the protected two; Metal `v575-metal-01` returns 48 Object
Islands and 10 packages, which is observational only because aggregate Metal
package count is not an acceptance signal. Do not promote or extend this
prompt direction. The reconciliation wording is too broad across sheets and
must not be tuned again without a new causal diagnostic.

BLOCKED EXPERIMENT, P0, V5.8.0 two-pass Registry: retain Fusion, candidate
Regions, View Evidence Packages, Dimension Fingerprints, Weighted Similarity,
the V5.6 deterministic graph and standalone fallback. Haiku call one is
Discovery only: full pages plus fixed enlarged regions, Islands, bboxes,
classification and Candidate Region recall, with no OCR inventory, Q,
object hypotheses or semantic facts. Call two is Membership only: fixed
Object View crops, concise View-local facts and document-context descriptions;
it cannot create, remove or classify Islands and returns only multi-View
hypotheses. Page-wide OCR spans are excluded from a View-local membership
handoff. Persist each call's token, cost, duration, prompt/context characters,
image count and image bytes, as well as aggregate cost. `v580-page23-03` is
the first valid end-to-end trace after the Registry crop sources were wired
through final validation: `$0.016990`, Registry `21.768s`, total `28.719s`.
It rejects the quality gate despite returning three packages. Discovery emitted
five Object Islands. Membership incorrectly merged the door elevations with an
unrelated angled panel, while leaving the physically continuous shelf-and-panel
depiction separate. Do not spend on Adda or HSL, tune generic semantic wording,
or promote V5.8 from this trace. The next decision is whether Membership gets
a bounded full-page visual context in addition to crops, or whether Discovery
must return explicit continuous-drawing component ownership. No Router or
Sonnet.

BLOCKED EXPERIMENT, P0, V5.8.1 Membership page-context experiment: retain the V5.8
two-call responsibilities and every fixed Island/classification boundary. Add
one JPEG page context, longest side `1024`, only for pages containing fixed
Object Views, before the existing View crops in the Membership call. It may
identify continuity and alternate View arrangement, but cannot create, remove,
merge or reclassify Islands. First gate is Page23 exact grouping: shelf with
its continuous panel, doors alone, console projections together. Record the
incremental Membership image bytes, tokens, time and cost before any wider
benchmark. `v581-page23-01` rejects the exact grouping gate: it repeated the
false doors-plus-angled-panel merge and split the two console projections after
the generic direct-shared-structure guard rejected one of their two facts.
Compared with `v580-page23-03`, page context added 81,365 image bytes, 1,047
Membership input tokens and `$0.001082`, but did not correct the false link.
The crop-only-context hypothesis is rejected. Do not run Adda or HSL, tune
semantic wording, or promote this direction. No Router, Sonnet or extra call.

CHECKPOINT, experimental, V5.10.3 two-call Registry: retain Fusion and the
deterministic graph, but separate visual discovery from commercial membership.
Haiku call one receives the rendered pages, Fusion and Candidate Regions, and
returns only immutable Islands, classifications and candidate exceptions.
Haiku call two receives the fixed inventory, page overlays, View crops and
local evidence, then returns only non-singleton multi-View hypotheses. Runtime
alone validates citation IDs and typed positive facts, computes Dimension
Similarity, compiles the graph and creates packages. Both calls use Haiku at
temperature zero. Exact display wrappers such as `[SF00123]` are canonicalised
only when `SF00123` is a known source ID, with an audit row. This checkpoint is
not accepted or deployed. Protected evidence and limits are recorded in
`notes/DETECTION_V5_10_3_TWO_CALL_EXPERIMENTAL_CHECKPOINT_2026_10_23.md`.

VERIFIED LOCALLY, pending checkpoint, P1, V5.10.6 P02 generic floor-plan classification.
The V5.10.3 HSL run retained all protected P03-P11 Island inventory but emitted
P02 as `object_evidence` because it mislabeled `representation_kind` as
`object_evidence`, bypassing the generic-plan safeguard. Repair this upstream
classification-contract breach without changing Island membership, graph,
dimension scoring or P04 package policy. Re-run HSL first, then Page23 before
any broader regression pack.

CHECKPOINT, experimental, V5.10.12 evidence, context and same-page Dimension
repair. This is a protected local evaluation baseline, not accepted or deployed.
V5.10.5 preserved P09.V3 outer dimensions but the final Dimension Graph passed
`allowed_pairs=Q`, which disabled same-page all-to-all after Registry.
Candidate Regions omitted the lower P03 and P09 sections, so their final
Islands received no Dimension pair, semantic fact or graph edge. V5.10.6
scores every final same-page object-Island pair and uses Candidate Q only for
bounded cross-page revalidation. Keep the 25 threshold and cross-page >=85
early stop unchanged. It also demotes a whole architectural floor plan to
`document_context` from its concrete description when Registry incorrectly
emits `representation_kind=object_evidence`. V5.10.7 required verbose per-page
reasoning, which pushed one HSL proposal to its 8,192-token cap. V5.10.8 keeps
the same validated all-pages/all-Islands invariant in a compact page-to-Island
ID map. It fixes the silent P09 omission without raising a token budget or
adding a call. V5.10.8 then restored all P09 Islands, but P09.V3 had no
Dimension edge because its Registry envelope ended 66 pixels above the printed
total `407`; the matching `406` was retained by P09.V2. V5.10.9 tried a Review
completeness instruction and explicitly still classified P09.V3 standalone, so
that prompt-only change was discarded. V5.10.10 attaches an otherwise-unowned
numeric fact of at least 20 in a bounded 80-180 px evidence halo only when
exactly one final Island contains it. This excludes title-block revision rows
such as 1..10 and cannot duplicate or steal a fact across overlapping halos.
V5.10.12 fixes the remaining earlier recall failure: where Mistral exposes no
graphic region on a page, Fusion derives broad, disconnected text/dimension
clusters as Candidate Regions. They only require Registry to inspect those
areas, retain the full-page rule, and never decide Islands or object identity.
Graphic-region pages retain their existing Candidate Region behavior. The
candidate log records the recall basis, including `fusion_text_cluster`.
Local HSL `v51012-hsl-01` passed the primary gate: P02 is Document Context,
P03.V1-V3 are one package, P09.V1-V3 are one package, and P09 has five
accounted recall regions, including a non-Island revision table. It produced
32 Islands and 10 packages in 124.481 seconds at $0.208045. This is an
uncheckpointed local result. Page 23 `v51012-page23-01` confirms this fallback
did not run on ordinary Mistral graphic-region pages, but exposed an independent
semantic-validation defect: generic material/frame language incorrectly merged
door and console Views. It produced five object Islands but the false packages
`P01.V1+V2` and `P01.V3+V4+V5`. Do not checkpoint or deploy. Next isolated
audit corrected the causal label for the zero Dimension pairs. This is not a
Fusion-to-final-Island ownership loss. `page-23.pdf` has only nine native text
spans, all headers, footer, page number, or two notes, and no authored drawing
dimensions. The current one-page Mistral response returns one `image` block
covering the drawing, no interior text blocks, no image annotation, and only
image Markdown. Fusion therefore never receives dimension literals such as
4130, 2345, 2695, 1760 or 3610 with usable coordinates. Treat OCR recall and
locality as a separate early evidence repair. Independently, Registry sees the
full page in both calls but split the physically continuous left shelving and
its diagonal extension into P01.V1 and P01.V2. Repair that Island-segmentation
breach before using semantic facts to mask it. Only then tighten
`matching_topology` and `direct_shared_structure` around pair-specific topology
or an actual shared physical structure. Rerun Page 23 before the remaining
benchmark pack.
Mistral native coordinate blocks remain the confirmed stable OCR path; do not
restore the rejected per-item bbox response schema.

REJECTED LOCAL EXPERIMENT, V5.10.13 Page23 OCR crop and Island-water prompt:
the isolated 200-dpi crop of the complete left shelving unit, including visible
dimensions 2695, 1760, 1660, 630 and 510, still returned one Mistral image
block, image Markdown and zero text or dimension facts. Enlarging the image is
therefore not an OCR recovery path for this provider response. The Proposal
prompt then required a 10-Fusion-pixel water gap and a continuity recheck before
creating Islands. Page23 `v51013-water-01` still returned five Object Islands:
it called the shelf `VG-P1-001` and its visibly attached diagonal extension
`VG-P1-002` independent components, then Review re-merged them into one object.
It retained the correct three final packages but did not repair the Island
boundary. Revert this prompt-only variation. Do not try another wording-only
variant. Any next repair must give an existing stage an explicit, bounded
authority to invalidate a false split, or add a deterministic image-continuity
signal that distinguishes physical body strokes from annotations.

REJECTED LOCAL EXPERIMENT, V5.11 visual-only alternatives: direct Haiku
object discovery, high-resolution retry, isolated visual membership review and
bounded nearest-neighbour visual pairs all failed the Page23 exact grouping
gate. The pair route was invalidated earlier by incorrect View envelopes, which
omitted the required console pair and introduced false neighbours. V5.11 was
never wired into the active Detection path. Do not create a page router, use
Sonnet, or tune this prompt family further.

RESEARCH RESULT, legacy V3/V4 Page23: the historical stable 3-object outcome
does not prove a universal mechanism. Both active legacy prompts contain a
literal example of the Page23 composition, demanding three objects and the
two-view console merge. The reusable observation is narrower: temperature-zero
Haiku made one full-page visual inventory before any bbox candidate constrained
it. It correctly represented the shelf as one complete assembly view, doors as
one track system and the console as two views. It then applied exclusive
ownership. Do not restore the old direct Registry, its Page23-shaped example,
or unvalidated free-text boundary reasoning. Any successor needs a separately
approved full-page-first Island authority while keeping Fusion, Dimensions and
runtime validation.

PENDING, P0, USER DIRECTION, degraded-source visual route: build a separate
Haiku-only Detection path for drawing packages whose Fusion contains no usable
spatial source evidence on every substantive page. This is an input-capability
decision, never a filename, object-count, Page23, document-type or Sonnet
route. The deterministic gate must distinguish authored, page-local MyPDF or
OCR text/dimension/graphic facts from page headers, footers and a provider's
whole-page image placeholder. On a routed file, bypass Candidate Q but retain
visual-source Dimension Fingerprints, typed semantic facts, full rendered
pages, source-quality audit, role classification, exclusive ownership,
Detection Validation, File Review and later Naming. The alternative Haiku
route first builds a full-page visual inventory before any rectangular candidate
boundary, then resolves commercial membership from that inventory. Mixed-evidence
files remain on the ordinary V5 route until a separate mixed-page contract is
approved. Acceptance must cover varied zero-source files, not a Page23 rule.

PENDING, P1, USER DIRECTION, mixed-evidence documents: define a separate
per-page capability and cross-page ownership contract. A single source-degraded
page must not discard good Fusion facts from other pages, and a visual-only
page must still be eligible to join an object evidenced on a structured page.
Do not begin this work during the V5.12 document-level visual-only experiment.

FAILED QUALITY GATE, V5.12 source-degraded visual route, Page23
`v512-page23-02`: the document-level capability gate correctly excluded a
footer address (`100`, `472`) and two adjacent OCR rows of one cable-hole note;
the document has zero usable coordinate evidence and entered the visual-only
route. Two Haiku calls returned five Object Islands and five singleton packages
instead of the required four Islands and three objects. Discovery split the
physically continuous shelving assembly from its diagonal extension, then
Membership did not create any false merge. This isolates the current failure to
full-page visual continuity in Discovery, not Fusion, Dimension Fingerprint,
or Membership validation. The experiment cost `$0.019223` and took 36.470s
wall time, including 7.035s Mistral OCR. Do not wire or deploy V5.12 from this
run. The separate mixed-evidence P1 contract remains deferred.

PENDING EXPERIMENT, P1, USER DIRECTION, ordinary V5 static-crop ablation:
Proposal currently receives every full page plus three fixed static crops
(`upper_left`, `upper_right`, `lower`). The static three-zone topology has no
established advantage and can present one continuous physical depiction as
separate partial images. Remove only these pre-Discovery crops. Retain Review
View crops, because they are produced only after the Island inventory is fixed
and therefore cannot create an Island split. Keep full pages, Fusion, Candidate
Regions, Dimensions, semantic facts and deterministic graph policy. Compare
HSL Island inventory and Page23 commercial boundaries, as well as input bytes,
tokens, cost and duration, before changing the ordinary default.

PENDING DIAGNOSTIC, P0, V5.12.1 source-degraded semantic proof: Page23
`v5121-page23-02` recovered the required four Islands without any crop, but
incorrectly merged the shelving assembly with the TV console. The only causal
semantic fact was `direct_shared_structure` based on a generic claim of the
same metal-frame "principle" or "construction methodology". Define and test a
physical-continuity witness for this fact before widening any validator: either
one View visibly contains both otherwise separate parts as one attached
assembly, or a partial View is visibly continuous with a complete View of that
same assembly. Shared material, profile, frame type, construction method or
similar dimensions are never a witness. Page23 is the first discriminator.

FAILED QUALITY GATE, V5.12.2 source-degraded semantic proof, Page23
`v5122-page23-01`: the new `direct_shared_structure` witness correctly
rejected the original generic metal-frame claim, but Review re-labelled the
same generic resemblance as `matching_topology` and `unique_geometry`. Runtime
therefore accepted six non-specific facts and merged all four Views into one
object, rather than the required three. This rules out a type-specific wording
or blacklist repair. The next approved repair must require a criterion-specific
structured witness for every semantic fact: literal author relation, paired
axis/value transform, recurring ordered topology, named distinctive geometry,
or a physical-structure witness. It must reject generic rectangles, frames,
materials, construction principles and broad visual resemblance regardless of
which evidence type the provider selects. Do not repeat Page23 until that
contract is implemented and unit-tested.

ACTIVE EXPERIMENT, P0, V5.12.5 source-degraded nested-Island resolution:
the visual-only route no longer fabricates a deterministic Dimension Fingerprint
from incomplete model transcription. Discovery locks Islands only. Membership
gets full-page overlays plus post-Island View crops and returns the sixth typed
criterion `visual_dimension_similarity`, citing both Views and concrete visible
readings. It also emits only explicit, grounded dimension conflicts, never an
absent or unknown state. V5.12.4 requires numeric readings separately from both
endpoints of a conflict and directs Membership to inspect every allowed pair for
positive proof before returning any conflicts. V5.12.5 additionally permits a
grounded `nested_duplicate_island` decision: a visually contained fragment with
no independent drawing boundary is removed before graph construction, while
ordinary overlapping boxes remain distinct. A conflict blocks that pair; a
similarity alone remains supporting and must combine with another concrete
criterion. The special route does not use batch confirmation. First gate is
Page23: four Islands and exactly three objects, with the two console projections
merged and no shelf/console merge. This is uncheckpointed and must not affect
ordinary V5.

RESULT, V5.12.4 Page23 `v5124-page23-04`: the conflict repair worked narrowly.
Five conflicts with concrete numeric readings from both endpoint Views were
accepted; two legacy-like conflicts whose second View had only material labels
were rejected. Discovery still returned five rather than four Islands, and
Membership returned no positive fact or merge edge, so all five Views remained
singletons. It also omitted the three potentially relevant console pairs from
the returned facts and conflicts. The next isolated diagnostic is an exhaustive
pair-review receipt, separate from the graph, to prove that every allowed pair
was inspected before changing any merge threshold or Island rule. The run cost
`$0.022056` and took `41.454s` wall time (`15.213s` Mistral, `25.768s` model).

REJECTED, V5.12.5 nested-Island rule, Page23 `v5125-page23-01`: Discovery
still returned five groups and Membership returned neither a nested-duplicate
decision nor semantic facts. The apparent duplicate was not actually contained
by the immutable core boxes in this run: its overlap with the larger candidate
was about `68%`, and it extended materially above it. Do not lower the `85%`
containment guard. The supported diagnosis is a fragmented continuous drawing,
not a nested duplicate. The next distinct proposal, if approved, is an Island
reconciliation relation for same-page fragments whose visual contours visibly
continue into one another. It is a segmentation repair before the object graph,
not a semantic object merge. V5.12.5 cost `$0.016119` and took `29.157s` wall
time (`3.867s` Mistral, `24.728s` model).

REJECTED EXPERIMENT, P0, V5.13.2 source-degraded representation-map roles:
Discovery emitted six representations on Page23 and Review assigned every one
an explicit role, but still created a false shelving-to-door relation and split
the two console projections. The isolated route preserved full pages and
disabled Discovery-coordinate crops because its rendered-frame boxes are not
authoritative. The failure proves that a role taxonomy followed by pairwise
semantic facts cannot replace global object partitioning. Do not tune its pair
prompt further.

REJECTED EXPERIMENT, P0, V5.14 source-degraded full-page Registry partition:
Discovery remained advisory and a second full-page Haiku call owned all roles
and one exclusive partition. Its first response correctly labelled a component
but illegally included it in a partition, which runtime rejected. Its second
response technically passed but falsely merged shelving with doors and left the
two console projections separate. The V4-style partition validator, role
coverage, exclusive ownership and graph materialization worked as intended;
the visual conclusion did not. Cost was `$0.015468`, total wall time `24.807s`.
Do not promote or continue prompt-wording variants of this two-call route.

REJECTED EXPERIMENT, P0, V5.15 source-degraded one-shot full-page Registry:
To remove the two-call map handoff, one Haiku full-page decision produced the
representation map, roles and exclusive partition together. Page23
`v515-page23-01` correctly made the continuous shelf-and-panel one assembly,
kept doors separate, and classified a detail and footer out of ownership, but
still separated the two alternate console projections. It returned four
objects, not the required three, at `$0.013936` and `32.676s` wall time. This
rules out the intermediate map handoff as the sole cause. The historical V4
Page23 result is not an acceptance target because its prompt contained a
literal Page23-shaped example. Do not copy that example or promote V5.15.
Any next source-degraded mechanism needs a document-independent way to ground
alternate-projection identity beyond free visual prose.

REJECTED EXPERIMENT, P0, V5.16 source-degraded V5.6.1 proposal consensus:
two independent 200-dpi full-page Haiku calls, with no pre-Discovery crops,
each returned the same six Object Islands and only forbidden singleton
hypotheses on Page23. The deterministic consensus correctly retained no merge
edge, leaving six standalone packages rather than four Islands and three
objects. Both calls had equal 4,678 input and 2,045 output tokens, and their
normalized maps and decisions were identical, so an identical second proposal
does not create independent evidence. The route gate, no-crop input, Island
matching and consensus materialization behaved as specified, but the quality
gate failed. The retained report cost was `$0.029806`, with latest recorded
wall time `50.068s`. An earlier command reused the same label and may have
overwritten its report, so session-level spend must not be inferred from that
single artifact. Do not tune this prompt or repeat the same consensus mechanism. The remaining diagnostic is to
compare the exact historical V5.6 rendered image transport and present visual
input with no model-contract changes, since V5.6 results cannot be replayed by
its text contract alone.

ACTIVE EXPERIMENT, P0, V5.17 source-degraded post-Discovery view crops:
retain V5.14's two distinct roles and its global exclusive partition contract.
The only changed provider input is that the second call receives the same
authoritative full rendered pages plus one padded crop for every first-call
candidate view. No static grid crop, prompt criterion, role rule, graph rule,
ordinary V5 path, or source-degraded router gate changes. Crops are created
only after Discovery and are supplemental detail, never a boundary authority.
Local structural verification created five valid crops from the historical
Page23 Discovery map, alongside the original 200-dpi full page; 45 focused
tests and `git diff --check` pass. The live provider gate was not executed:
this execution environment exposes project keys without DNS and exposes DNS
without local secrets, so neither Mistral nor Haiku was called. V5.18
supersedes this experiment's crop input.

ACTIVE EXPERIMENT, P0, V5.18 source-degraded full-page partition repair:
remove V5.17's post-Discovery crops entirely. In the final full-page Registry
response, discard only a partition whose members are all known Views already
classified as `component_detail`; persist that deterministic repair in the
decision audit. Unknown IDs, mixed detail and assembly partitions, duplicate
or missing assembly ownership, and invalid visual bases remain hard validation
errors. Ordinary V5 is unchanged. Local structural verification: 57 focused
tests and `git diff --check` pass. Provider-quality outcome remains pending,
and this repair must not be represented as a Page23 object-boundary fix.

ACTIVE RELEASE, P0, V5.19 Detection decision ledger: V5.18's source-degraded
route returned an internal usage dictionary rather than a database event. Its
missing required ledger fields caused the asynchronous batch write to lose
route choice, Islands, roles, partitions and Registry reasoning, while File
Review still showed final objects. Build a DB-ready, timestamped Detection
event for both success and validation failure. Persist it synchronously before
File Review, one event at a time; abort rather than expose an unauditable
Detection decision if that write fails. Continue storing OCR and timing
diagnostics asynchronously. Ordinary V5 decision logic is unchanged.

REJECTED EXPERIMENT, P0, V5.20 source-degraded continuity consolidation:
retain V5.19's two full-page Haiku calls and add an explicit same-page
`continuity_groups` response before roles. A deterministic core-bbox overlap
cue correctly surfaced the Page23 shelving and angled-panel pair as the only
candidate. The full-page Registry nevertheless returned an empty continuity
list, retained the panel as `component_detail`, falsely merged shelving with
doors, and left the console projections separate. The runtime consolidation
and audit behaved as specified, but the provider did not supply the required
physical-contour observation. Live visual-only Registry cost `$0.015511` for
6,881 input and 1,726 output tokens in 21.694 seconds. Reverted to V5.19.
Do not retry this prompt/schema mechanism. The next diagnostic must change the
visual evidence presented for connected-contour recognition, without restoring
static crops or treating bbox overlap as a merge decision.

PROTECTED EXPERIMENTAL CHECKPOINT, P0, V5.21 source-degraded mandatory
boundary ledger: user explicitly approved a narrower replacement after V5.20's
audit showed that the model could leave a continuity candidate unanswered. The
route keeps two full-page Haiku calls and no crops. For every same-page
core-bbox-overlap pair, Registry must return one physical-boundary decision:
`physically_continuous` plus concrete joined geometry, or
`physically_separate` plus `visible_background_gap`,
`separate_closed_contour`, or `independent_projection`. The code accepts no
silent split, unions only attested continuous pairs before roles, and writes
both the full boundary ledger and resulting consolidation audit. This does not
make bbox overlap a merge decision and does not alter ordinary V5.

Production Page23 run `run_caed454c5f6b49479d300f0b532c85c4` executed the
V5.21 prompt and supplied the required V1/V3 answer. It incorrectly asserted
`physically_separate / independent_projection` from different dimensions and
an alleged lack of common geometry, without identifying a visible separator.
The run nevertheless produced packages V1, V2 and V4+V5. This is an accepted
continuation checkpoint, not segmentation-quality acceptance. Preserve the
boundary ledger and do not add more prompt/schema variations automatically;
the next approved diagnostic requires independent visual evidence of physical
continuity. Details: `notes/DETECTION_V5_21_SOURCE_DEGRADED_BOUNDARY_LEDGER_CHECKPOINT_2026_10_24.md`.

SUPERSEDED EXPERIMENT, P0, V5.22 source-degraded local contour witness: retain
V5.21's two full-page Haiku calls and no pre-Discovery crop. Replace its
overlap-only boundary queue with a bounded local same-page core-neighbour
queue. For every selected pair, Registry must supply a coordinate-bearing
physical witness inside a deterministic local inspection corridor. A continuous
claim names and locates the visible construction joint. A separate claim names
and locates a visible background gap or separate closed contour.
`independent_projection`, dimensions, material, annotations and differing
perspective are prohibited as local-boundary evidence. Deterministic code
records whether the witness agrees with the rendered pixels and unions only
pixel-consistent continuous claims before roles. This is a source-degraded
segmentation experiment only, not an ordinary V5/Fusion/Dimension change.
First gate: Page23 must account for every local contour pair and either join
the shelving frame to its attached angled panel with a witness or expose a
failed witness in the audit. Record candidate count, witness coordinates,
pixel audit, roles, partitions, time and cost before broader testing.

SUPERSEDED EXPERIMENT, P0, V5.23 source-degraded role evidence: retain V5.22's
two full-page calls, no pre-Discovery crop and local contour audit. Change
only the final role contract. Every `assembly_view` must assert a complete
fabricated system, which can be a complete 2D elevation rather than a 3D
carcass. Every `component_detail` must either cite a same-page assembly parent
or state an explicit isolated-fragment basis. A full track/frame plus its
complete leaf, panel, bay or door sequence and system dimensions cannot be
discarded as a detail solely because it is technical or 2D. First gate:
Page23 must preserve a single shelving island, retain the door elevation as
an assembly, retain panel-only detail as supporting evidence, and merge the
two console projections only through a valid object basis. This is not a
Dimension Engine, ordinary V5, segmentation, crop or naming change.

SUPERSEDED EXPERIMENT, P0, V5.24 source-degraded overlap guard: retain V5.23's
role-evidence contract and V5.22's local contour witness. Make every
same-page overlapping core pair mandatory for contour review before applying
the bounded nearest-neighbour queue. This records the proven Page23 shelf
failure where an attached angled panel overlapped the shelving core and V5.21
accepted `independent_projection` without a physical separator. The overlap
guard never merges views itself. Registry must still return a local physical
witness and deterministic code must still accept only pixel-consistent
continuity. Regression fixture: the historical V5.21 Page23 V1/V3 boxes must
always enter the contour queue. This changes neither role semantics, object
merge, crops, Dimension Engine nor ordinary V5.

SUPERSEDED EXPERIMENT, P0, V5.25 V5.21 plus physical overlap witness: revert the
source-degraded route's role contract and non-overlap neighbour queue to the
V5.21 baseline. Retain only the mechanism that addresses the historical
Page23 shelf split: every overlapping same-page core pair must provide a
coordinate-bearing physical witness; `independent_projection` cannot explain
separation; deterministic code accepts continuity only after its local pixel
check. V5.21 already queued the historical V1/V3 overlap, so this experiment
tests the witness contract, not the V5.24 queue extension. First gate: Page23
must not silently preserve an overlapping shelf/panel split. All role,
partition, Dimension Engine, crop and ordinary V5 behaviour is V5.21.

SUPERSEDED EXPERIMENT, P0, V5.26 local-overlap witness projection: preserve V5.25's
V5.21 roles, partition and overlap-only queue. A model witness may be broader
than the compact corridor, but must overlap it by at least 4x4 px. Deterministic
code clips it to that local intersection before pixel audit and records both
raw and effective bboxes. This fixes the proven V5.25 false terminal failure
without accepting a remote witness or changing roles, partitions, crops,
Dimension Engine or ordinary V5. First gate: the V5.25 Page23 `view-003` /
`view-005` witness (850,380)-(920,450) against corridor (897,407)-(913,423)
must validate using effective witness (897,407)-(913,423).

REJECTED EXPERIMENT, P0, V5.27 source-degraded post-Discovery visual context:
the second call received padded candidate and nearby-pair crops beside the
complete 200 dpi page. Five Page23 runs produced the exact required grouping
only once. The crop queue used model-produced transport bboxes, so its claimed
adjacencies were false, including shelf plus lower console at zero pixels.
Review then used that context to falsely merge independent systems. Reject
static, candidate or pair crops before final inventory. Do not reuse V5.27's
crop-selection logic, but retain its telemetry as historical evidence.

FAILED QUALITY GATE, P0, V5.28 source-degraded direct inventory and
independent audit: four audited Page23 runs completed without crops or
validation errors, but all returned four final packages instead of shelf,
doors and the two console views as exactly three. Three runs were effectively
identical, with four assembly views and no positive relation edge at all. The
fourth made the angled shelving panel a same-page component of the shelf, but
still left both console views as separate objects. In every run the second
full-page call copied the first call's groups, roles and singleton partitions
rather than independently rebuilding the map. Its claimed console distinction
was vague "different component configuration and detailed labeling", not
concrete separation evidence. The owner constraint prevented an unowned
detail but did not establish physical continuity. Reject V5.28 as a quality
route. Do not tune its wording or re-run it. Its measured average is $0.02341
and 28.34 provider seconds per Page23 call pair. Ordinary V5, Fusion,
deterministic Dimensions and the source-degraded gate remain unchanged.

FAILED QUALITY GATE, P0, V5.29 source-degraded fixed-Island pairwise audit:
four Page23 runs were fully stable at five Islands, four technical plus title
context. The map correctly kept the continuous shelf intact and correctly
joined the two console projections through a concrete `alternate_projection`
edge. However, second-pass role assignment called the doors a
`component_detail` owned by the console without a `same_object` edge, direct
continuity, author label, matching dimensions or other owner proof. Because
the ledger compared only `assembly_view` pairs, the role removed doors before
the graph. All runs therefore returned two packages, shelf and console,
instead of three. The failure is a structural role-to-ledger bypass, not an
Island-map failure. Measured average: `$0.014472`, `19.25s`. Do not tune the
V5.29 wording or rerun it as an acceptance candidate.

FAILED VALIDATION, P0, V5.30 source-degraded pairwise preservation audit:
the first production run reached the second Haiku response, but a provider
returned a non-empty `owner_group_id` for an `assembly_view`. The schema
requires that field for every role, while the former direct-role validator
treated the irrelevant value as terminal. No Island, graph or package result
was produced. This is a role-field normalisation defect, not evidence against
the preservation contract.

FAILED QUALITY GATE, P0, V5.30.1 source-degraded pairwise preservation audit:
five Page23 production runs were stable at five Islands, four technical plus a
title context. The normalisation repair succeeded, but each graph linked shelf
to doors from a false `same_object` relation and left the two alternate console
views separate. The second call called the consoles merely similar and did not
record the full-object structural correspondence that V4.2 had used. The
route is not accepted. Preserve its neutral full-page map, no-loss role repair,
two Haiku calls and audit shape as V5.31's base.

FAILED QUALITY GATE, P0, V5.31 source-degraded pairwise structural audit:
four Page23 runs were identical at five Islands and exactly three published
objects, but the count concealed a wrong partition: shelf, console view one
and console view two. The model called doors a `component_detail` owned by one
console through a false `direct_continuity` claim, then called the two console
views distinct. The structural edge validator correctly rejected the
detail-console relation for graph insertion, but the older role resolver did
not consume that rejection and still removed the door Island before the graph.
The run therefore proves an ordering defect between role resolution and edge
admission, not a volatile visual-model result. V5.31 is not accepted.

ACTIVE EXPERIMENT, P0, V5.32 source-degraded structural admission for roles:
retain V5.31's fixed five-Island map, two complete-page Haiku calls, typed
structural witnesses and graph admission unchanged. A `component_detail` may
now suppress a technical Island only if its exact owner relation has passed the
same deterministic structural admission used for a graph edge. A rejected or
unadmitted direct-continuity claim promotes the Island to `assembly_view` and
records a role repair. No crops, Sonnet, ordinary V5, Fusion,
source-capability routing or deterministic Dimensions change. First gate:
Page23 retains doors as an independent technical object rather than silently
removing them. This is intentionally a one-factor recall repair; it does not
claim to solve the still-separate console views. Record role repairs, witness
ledger, rejected and admitted graph edges, Islands, packages, tokens, cost and
time before any next boundary experiment.

COMPLETE EXPERIMENT, NOT A RELEASE CHECKPOINT, P0, V5.32.1 source-degraded role wording and ledger completion:
preserve V5.32's Island map, two complete-page Haiku calls and structural graph
admission. Clarify that a finished separable fabrication, including a door or
door system, cannot become `component_detail` from plausible proximity,
material or installation alone. If the provider omits a required technical-pair
row, runtime appends only an audited `inconclusive` row with no visual evidence
and no graph edge. This prevents a formatting omission from failing a run, but
does not claim a missing relationship was resolved. First gate: Page23
completes with a visible runtime completion audit and preserves every technical
Island for review. Record original provider rows separately from runtime rows.

[verified, 2026-10-24] Five Page23 production runs were identical: five
Islands, four technical packages and one title context. Every provider response
contained all six technical-pair rows, so runtime completion was unused. The
model still called the door elevation a detail of one console; V5.32.1 promoted
it to an independent assembly because its claimed relation failed structural
admission. The two complete console projections remained `inconclusive`, so
the graph had no positive edge and published four objects instead of the
expected three. V5.32.1 fixes terminal pair-row loss and silent detail loss;
it does not solve complete-assembly pair interpretation and is not accepted as
a source-degraded Detection checkpoint.

REJECTED PRE-DEPLOY EXPERIMENT, P0, V5.33 visual embedding candidate prior:
before changing Detection or Railway, frozen `facebook/dinov2-small` was run
against the actual V5.32.1 Page23 Island bboxes at 96 dpi. Its intended
positive pair, the two alternate TV-console projections V3/V4, scored `0.4642`
and ranked last for both Views. False pairs V1/V4 and V2/V3 scored `0.8180`
and `0.8296` respectively and were mutual nearest neighbours. The model was
therefore trained and executable but unsuitable as an attention prior for this
technical-drawing identity problem. No V5.33 code, dependency, lockfile or
Railway deployment was retained. Do not retry DINOv2 embedding, tune a score,
or add it to ordinary V5. Any future visual encoder must first pass this exact
V3/V4 ranking gate without elevating a false pair. A core-bbox-only rerun
excluded annotation field and transport padding as the cause: V3/V4 fell to
`0.2987`, while false V1/V4 remained `0.8196`.

ACTIVE EXPERIMENT, P0, V5.34 unified rendered-page frame and bbox audit:
the ordinary V5 renderer now requests 200 DPI, matching the existing
source-degraded request. Rendering remains capped at 2,000 px on the longest
side. Diagnostics record requested DPI and each actual rendered page frame;
route labels no longer claim 96 DPI. No Island, crop, Fusion, semantic,
Dimension or graph rule changes. First evidence gate is a fresh Page23
source-degraded raw Island map overlaid on the exact 200-DPI JPEG frame. Then
audit the ordinary V5 proposal, static pre-Discovery regions, Fusion-to-JPEG
coordinate conversion and Review crops separately. Do not infer an Island
repair merely from the resolution change.

[verified, 2026-10-24] Fresh production Page23 run
`run_583c26209c264ac08040afad3b5dd66f` confirms the source-degraded page frame
is `1985x1404` at requested 200 DPI. Its five raw boxes still split the one
continuous shelf between `VG_P1_001` and `VG_P1_004`, and misplace
`VG_P1_003` over the lower left door rather than a TV-console projection. The
renderer is therefore now auditable but does not repair the primary map.

SUPERSEDED EXPERIMENT, P0, V5.35 native graphic-anchor Registry: retain the
source-degraded route only for a PDF where every rendered page contains 2-12
independent native image XObject placements, each covering 5-70% of the page.
Extract each source-authored placement into OCR/Fusion evidence with its PDF
point rectangle and map it deterministically into the actual capped rendered
frame. These are immutable candidate envelopes, not object claims: Registry
may assign their role and pairwise identity only, never draw, move, split or
replace their boundaries. The free Haiku Island-discovery call is skipped for
this source class. The remaining Haiku audit receives the whole page plus an
immutable labelled overlay, then returns the existing roles and same-page pair
ledger. Other PDFs, scans and ordinary V5 remain on their current routes.
First gate: Page23 must expose exactly the four authored drawing envelopes,
then yield shelf plus continuous panel, door system and two console views as
three object packages. Do not treat a correct envelope map alone as a package
quality pass. Record the route, source-anchor count, rejected placements,
overlay audit, cost and timing. If it passes, verify that a non-eligible
source-degraded file still takes V5.32.1 before considering a broader pack.

[verified, 2026-10-24] V5.35 re-ran the previously rejected frozen
`facebook/dinov2-small` diagnostic against the four source-authored Page23
XObject envelopes, not the former V5.32.1 model-produced boxes. The intended
two TV-console projections V3/V4 were mutual top-1 at cosine `0.8278` from
the native XObjects and `0.8316` from their rendered 200-DPI envelopes.
The false shelf-to-door pair V1/V2 was `0.4189` and `0.4440` respectively,
the weakest non-self pair. This reverses the V5.33 ranking failure because
the earlier input boxes were wrong, not because a score was tuned. The test is
diagnostic only: no production merge rule, threshold, dependency or deployment
was added. Before any integration, repeat its exact rank gate on a second
eligible native-XObject drawing and define an explicit negative rule so an
embedding can prioritize a pair for review but cannot independently merge it.

SUPERSEDED EXPERIMENT, P0, V5.36 native-XObject embedding pair priority: retain
V5.35's immutable source-authored XObject boundaries and all existing role,
ledger, witness and graph validators. For the narrow native-XObject route only,
extract the original embedded image bytes, run pinned offline
`facebook/dinov2-small@ed25f3a31f01632728cabb09d1542f84ab7b0056`, and append
only the same-page top-two cosine ranking to the existing Haiku pairwise audit.
The score cannot create a positive or negative relation, enter a witness, or
merge a package. It is recorded with all pair scores, rankings, model revision,
load status and elapsed time. Railway fetches its 88 MB DINOv2 assets at build
time and runtime loads local assets only. Warm model loading starts in the
native-graphic OCR worker, in parallel with Mistral, so an RFQ does not wait
for the first CPU initialization after OCR. Local build, offline load and 144
targeted tests pass. First production gate: Page23 must record an available
prior with V3/V4 mutual top-1, retain four immutable XObject Islands and never
publish an embedding-only merge. Do not extend this model to ordinary V5 or use
it as a numeric threshold until a second eligible native-XObject document
passes the same rank test.

CHECKPOINT, protected production, P0, V5.37 native-XObject embedding witness:
full record is `notes/DETECTION_V5_37_NATIVE_XOBJECT_EMBEDDING_WITNESS_CHECKPOINT_2026_10_24.md`.
V5.37 retains V5.36
native-XObject extraction, immutable Island map, role ledger and graph
validators. A conservative same-page mutual-top-1 pair with cosine at least
`0.80` and margin at least `0.10` over each member's next candidate becomes
typed evidence. The Registry must return its exact `embedding_reference` and
an assessment for every ledger row. For a strong pair, `different_object`
requires an explicit author distinction, incompatible visible dimensions or
physical separation of completed products. `same_object` may count the
embedding as one evidence item, but still needs a concrete independent visual
witness and two original assembly views. Embedding never creates a graph edge
alone. First gate: Page23 V3/V4 must cite `native_mutual_top1:0.8278`, produce
an admitted alternate-projection edge with a visible witness, retain four
immutable XObject Islands, and avoid a false V1/V2 or V1/V3 edge. This is
native-XObject-route-only, not an ordinary V5 rule.

[verified, 2026-10-24] Six independent production Page23 V5.37 runs were
identical: four native-XObject Islands, one admitted V3/V4
`alternate_projection` edge with exact `native_mutual_top1:0.8278`, and three
packages. V2's claimed V2/V4 ownership was rejected and V2 safely promoted to
standalone in every run. The package boundaries are accepted for Page23;
provider reasoning and naming for V2 are not. This checkpoint does not extend
the rule beyond the native-XObject route or establish cross-document validity.

ACTIVE IMPLEMENTATION, P0, V5.38 Railway DINO artifact caching: retain the
exact V5.37 Detection contract and model revision. Build the pinned DINO
artifact after the locked runtime layer and before application-source copy. A
normal code commit must not redownload the approximately 84 MB DINO weights
when Railway's standard layer cache is available. Verify the build image
contains the three required files, local-only runtime loading still works, the
V5.37 test suite passes, and a source-only deployment reuses the model layer.
Railway can evict build caches, so only a separately published image could
guarantee zero refetches after cache loss. This is a deployment-efficiency
change, not a Detection-rule change.

RESOLVED, USER-REPORTED 2026-10-25, V5.38 Railway Docker start-command override:
the Docker build, model-prefetch layer and Deploy stage succeeded, but Network
Healthcheck failed after 60 seconds. Railway Diagnosis attributes this to a
service-level Start Command overriding the Dockerfile `CMD` and passing the
literal `$PORT` to Streamlit without a shell. The owner then corrected the
Railway command configuration and confirmed the V5.38 deployment succeeded.
Do not alter the Dockerfile or Detection contract for this configuration-only
issue. The next deployment must still verify its own healthcheck and DINO
availability during a Detection run.

CHECKPOINT, V6.1, Detection document pre-analysis: the passive, page-level
technical profile is implemented and deployed. It records what each rendered
PDF page can provide deterministically, but does not change active Detection.
The profile is persisted in OCR evidence and Fusion diagnostics only. Page23
retained the protected three objects; HSL retained 10 final objects.

SUPERSEDED EXPERIMENT, P1, V6.2, expanded Fusion handoff: every bounded
page capability profile was sent to the ordinary Fusion Proposal and fixed-
Island Membership Review. The experiment did not demonstrate a quality gain
and added prompt volume. The active contract returns to V6.1: profiles remain
in the immutable OCR evidence and returned Fusion audit, but are not supplied
to either model call. The source-degraded route, router, models, candidate
regions, Candidate Q, embedding rules, deterministic graph and packages stay
unchanged.

REJECTED EXPERIMENT, P0, V6.3, no fixed pre-discovery page crops: ordinary
Registry Discovery briefly received only complete 200-DPI pages plus existing
Fusion text. The change removed the fixed `upper_left`, `upper_right`, and
`lower` crop set. It was not sourced from an Island, View or author-issued PDF
boundary, could show a physically continuous depiction in fragments, and
duplicated one full page-equivalent of pixels per page. The protected crop
contract is restored after the Adda regression below. Preserve 200-DPI
rendering, Mistral, Fusion, router choice, Candidate Regions, Candidate Q, the
source-degraded Page23 route and post-discovery View crops. A post-discovery
crop may remain a second-pass magnifier only, never create, split or move an
Island boundary.

Current 200-DPI local input measurement: HSL has 11 full pages and
added 33 fixed crops, 29,680,851 duplicated pixels and 2,854,649 JPEG bytes;
Adda has four pages and formerly added 12 crops, 11,312,000 duplicated pixels
and 830,268 JPEG bytes. These byte and pixel figures are not provider-token
estimates. Fresh production V6.3 runs confirmed `pre_discovery_region_count=0`.
HSL retained its active Island inventory, 10 packages and the same ten
review-required File Review rows. Versus the directly comparable fixed-crop
run, it saved 34,526 input tokens (142,539 to 108,013) and $0.036291
($0.187694 to $0.151403). Adda saved 12,120 input tokens (33,865 to 21,745)
and $0.041010 ($0.160950 to $0.119940), but regressed from two cross-page
commercial objects to eight page-local, review-required objects. Do not accept
token savings alone if the protected page-local inventory or commercial
boundaries regress. This experiment is rejected and the fixed Discovery crops
are restored. A later replacement must prove that post-discovery object/View
crops preserve Adda's cross-page grouping before it can eliminate them.

SUPERSEDED EXPERIMENT, P0, V6.4, route-scoped fixed pre-discovery crops: preserve
the V6.3 baseline for the deterministic `sonnet_boundary_risk` route only,
which is the unlabelled repeated-multiple-drawing-region condition that Adda
meets. Ordinary `haiku_default` Registry runs must pass `regions=[]` and no
longer construct JPEG crops. The router itself, model choice, Fusion, Page23
source-degraded route, 200-DPI rendered page input, Candidate Q, graph and
post-discovery Review crops are out of scope. Acceptance requires Adda retain
its protected two cross-page commercial objects, HSL retain the active Island
inventory, Page23 retain its protected source-degraded three-object result,
and usage confirm zero `pre_discovery_region_count` for HSL but retained
regions for Adda. Railway deployment titles for this and every later Detection
version must include the version identifier, using the versioned commit
subject as the deployment title.

REJECTED EXPERIMENT, P0, V6.6, single canonical View bbox on the Sonnet
boundary-risk route: retain V6.5 complete-page Discovery and post-Discovery
Review crops, but ask Discovery for only one `bbox` per Island. It is the
smallest View boundary containing the continuous drawing and directly attached
dimensions, labels and leader lines. The runtime mirrors it to the legacy
`core_bbox` only at the compatibility boundary, so Review crops and evidence
ownership use the same canonical geometry. Candidate Regions remain recall
aids, never bbox authority. This is router-scoped, not a filename rule: first
gate is Adda's exact two-object View membership, geometry and non-overlap.
The code is reverted to V6.5 after its first Adda gate. Do not extend this
contract to Haiku.

V6.6 Adda `run_e00376bd61e14f07a5e76d21a7d1bc49` fails that first gate: it
retains eight Object-Evidence Islands but produces four components, not the
protected two. Review correctly joins P2.V1/P4.V1 and P2.V2/P3.V2/P4.V2, but
leaves P1.V1 standalone and falsely joins P1.V2/P3.V1. Discovery also emits
overlapping canonical bboxes for the two P1 Islands and for the two P4 Islands,
despite the single-boundary contract. This rejects the one-bbox contract as
currently specified. Next diagnostic is a deterministic non-overlap/foreign-
Island admission audit before another prompt or routing change.

ACTIVE EXPERIMENT, P0, V6.7, Mistral graphic-anchor admission on the existing
`sonnet_boundary_risk` route: preserve the complete-page 200-DPI input, Mistral
OCR, Fusion, router, Candidate Q and Review, but elevate only Mistral `image`
blocks to initial page-local boundary anchors. Proposal returns one explicit
decision per anchor: `accept`, `tighten`, `expand`, or `reject`. `accept`
forces both effective Core and Envelope to the immutable Mistral bbox. A
`tighten` or `expand` needs cited page-local source facts and is rejected back
to the Mistral bbox if it captures another anchor centre or lacks the required
local evidence. `reject` requires the existing Candidate Region exception.
The raw Sonnet proposal and the deterministic admission audit are both retained.
This is a boundary contract only, not an object-identity, split or merge rule.
It must not activate for text-cluster candidates, ordinary Haiku or the
source-degraded/Page23 route. First live gate: repeat Adda and inspect all eight
anchor decisions, Island geometry, exact Counter/L-shaped View membership, and
two non-overlapping components before testing HSL or V-cabinet.

ACTIVE DIAGNOSIS, V6.7 first Adda gate: the successful live run
`run_632a5422f8264797901a286953aceb85` accepts all eight Mistral graphic
anchors and restores the intended applied P1/P4 boundaries. It still returns
three components: P2.V1/P3.V1/P4.V1 and P2.V2/P3.V2/P4.V2 are each correct,
while Review falsely merges P1.V1 and P1.V2 as one general-view installation.
This is not a V6.7 regression: pre-V6.7 run
`run_a51ffdbabcc64e79851ea8890e3a7bf5` made the same merge, while the earlier
correct run `run_d76e1c6d03374581aa84936676a5d8ad` produced the intended two
four-View components. Candidate Q contains all 28 final pairs, including every
P1-to-P2/P3/P4 pairing, but is supplied only to Discovery. Membership Review
receives no pair queue or draft hypotheses and records no negative decision for
the omitted P1 cross-page links. It instead gives the local P1 relationship a
direct, 100-point merge through an invalid "General View" explicit-document
relation. The review prompt is also internally contradictory: it asks to merge
continuous drawing extensions, then says continuity within one depiction is an
Island-boundary defect rather than pair evidence. Do not add an Adda-specific
ban. Before any identity repair, choose and test a general commercial-object
membership contract that reconciles P1-like perspective Views against existing
cross-page components, and rejects shared-sheet/composition continuity as an
author relation.

SUPERSEDED EXPERIMENT, P0, V6.8, bounded complete pair membership for the V6.7
Mistral-anchor route only: if the admitted object-evidence inventory has 2-10
Views, Membership Review receives the complete unordered matrix and must return
exactly one disposition for every pair: `same_object`, `different_objects`, or
`insufficient_evidence`. Only `same_object` may carry evidence. It needs a
direct cited document relationship or at least two independent typed facts, and
the existing deterministic semantic-ledger and merge policy validate those
facts before package membership changes. Dimensions may reinforce only a pair
that Review marked `same_object`; Candidate Q remains collected and audited but
is no longer the membership authority for this bounded gate. The pair matrix,
all dispositions, evidence counts, and timing remain in the run audit. This is
not a filename rule and does not activate for ordinary Haiku, Page23 or other
non-V6.7 routes. First and only live gate: run Adda, compare the two expected
four-View components with V6.7, then measure additional Review duration,
tokens, and cost before considering any broader route.

SUPERSEDED EXPERIMENT, P0, V6.9, criteria-then-reconciliation for the V6.7
Mistral-anchor route only: preserve Discovery and page-local Mistral boundary
authority. Membership now has three bounded stages. First, Review emits sparse
`preliminary_links`, each naming the exact pair and the first criterion that
made the pair worth testing. Second, Review must audit every preliminary pair
against all five criteria: identifier, topology, geometry, dimensions and
construction. Each criterion is explicitly `supports_same_object`,
`contradicts_same_object` or `not_visible`. Runtime, not model confidence,
computes a strong link: no contradiction plus either a direct supported author
relation or two supported discriminative criteria with two independent typed
evidence facts. Only strong links form transient reference components. Third,
every Island outside those components is compared to every reference component;
Review chooses a concrete member View for each candidate/component comparison
and again audits all five criteria. A final merge remains valid only through
accepted, cited pair evidence. General View titles, shared page, adjacency,
composition continuity, shared material, lighting and strokes cannot support a
criterion. This is not all-to-all and not a page-number rule. First gate is
Adda: retain all eight Mistral boxes, record the sparse preliminary links and
their five-criterion cards, create exactly four P1-to-component reconciliation
rows for a 3+3+2 preliminary result, and return the exact Counter and L-shaped
four-View memberships. Compare Review duration, tokens and cost with V6.7 and
V6.8 before extending any route.

PROTECTED EXPERIMENTAL CHECKPOINT, P0, V6.10, combined evidence review for the
V6.7 Mistral-anchor route only. Implementation is `1bd3c6e`, `c447b5c`,
`27e7e22`; full record is
`notes/DETECTION_V6_10_COMBINED_EVIDENCE_REVIEW_EXPERIMENTAL_CHECKPOINT_2026_10_25.md`.
Adda `run_c2ddd6be0c5b4add910d317382691d54` retained all eight Mistral boxes
and the exact two four-View memberships. It used two provider calls, 98.857
Detection seconds, 23,557 input tokens, 6,436 output tokens and `$0.167211`.
This is 31.1 percent faster and 29.5 percent cheaper than V6.9's true
three-call sum, while retaining the correct result. The aggregate event now
includes Proposal plus Combined Evidence Review. Conditional reconciliation did
not execute because every selected link was already strong. Do not generalize
this result, prune candidates, tune the prompt, or alter boundaries from this
one successful Adda run.

PENDING LIVE GATE, P0, V6.10 conditional reconciliation: before changing the
combined Evidence Review contract or expanding its route, run a document whose
sparse strong graph leaves an Island or component for reconciliation. Verify
the chosen reference member, all five criterion cards, exact final membership,
provider-call count, latency, tokens and cost. This is the first safe next
experiment after the protected Adda checkpoint.

OPEN DIAGNOSTIC, P1, V6.10 Adda local View-label ordering: page 1 assigns
`P01.V1` to the right/upper L-shaped view and `P01.V2` to the left/lower
counter, while pages 2 through 4 use the opposite positional order. Current
object membership is correct. Diagnose the source of local display ordering
without changing Mistral boxes, pair evidence, graph membership or package
boundaries merely to make labels look uniform.

PENDING DESIGN GATE, P1, document-scoped assembly classification: establish a
generic pre-membership category for drawings that describe one commissioned
assembly through an overview plus sections, component details, installation
context and hardware rather than multiple independently quotable products. The
first witness is `V_Cabiner.pdf`, a six-page vector-rich Order 1208 drawing
set. Do not route from filename, project/order number, repeated material or
page count. Existing `component_detail` is deliberately same-page-only and
must not be widened. Introduce a separate cross-page `part_of` relation within
an `assembly_set` scope, whose root may be one overview or a connected root
set. Dimension mismatch between an overall envelope and a carcass, module or
hardware detail is `non_comparable`, never negative evidence. A dimension may
contradict `part_of` only when both cited views explicitly claim incompatible
finished overall envelopes. Require a cited relationship graph from each
proposed member to the scope, using authored cross-references, visual
structural correspondence, component role, or other pair-specific evidence.
A page or Island without such a relationship remains a separate candidate,
never forcibly merged into the document scope. Detection must
preserve the component graph, source facts, quantities and confidence for
Estimation, while publishing one commercial assembly only when all included
members are evidenced. Decide the contract and benchmark before assigning an
implementation version or changing any current HSL, Page23 or Adda route.

ACTIVE EXPERIMENT, P0, V6.11 document-scope observation before Membership
Review: extend the existing full-page Discovery response with one validated,
compact `document_scope` decision. It is a semantic scope observation between
Discovery and Membership Review, not a pre-OCR router and not a fourth final route.
Allowed decisions are `assembly_set_candidate` and `ordinary_object_set`; an
assembly candidate needs a root/root-set and a cited hierarchy,
cross-reference or visual-component witness. Shared client/order metadata,
date, material, title block, page numbering and page count remain insufficient.
The decision is audit-only in V6.11: it must not affect Island boundaries,
Candidate Q, Dimensions, merge graph, commercial Objects or Estimation output.
Dimension mismatch is `non_comparable` unless two cited views explicitly claim
incompatible finished outer envelopes. First live gate: V_Cabiner returns an
auditable `assembly_set_candidate` with valid root and View witnesses;
inspect the resulting Island inventory and Objects explicitly, while no runtime
downstream decision may consume this field. Only after this shadow gate and
negative controls may a specialised `part_of` Membership Review be proposed.

ACTIVE EXPERIMENT, P0, V6.12 pre-Sonnet document categorization: replace the
former V4.2 binary model router with a deterministic scenario classifier that
consumes completed MyPDF/Mistral/Fusion evidence before any Detection-model
call. Categories are `source_degraded_visual`, `page23_native_graphic_pack`,
`assembly_set`, `ada_sparse_multi_object`, and `ordinary_object_set`; there is
no unresolved route, so all non-evidenced special cases default to ordinary.
`source_degraded_visual` remains a capability override for pages with no usable
coordinate evidence, while a source-degraded PDF with multiple native graphic
anchors retains the Page23 category. `assembly_set` is a routing class, not
proof of one final commercial object: its V1 gate is a continuous document
identifier across a majority of three or more structured technical pages, and
it must use Haiku. Only the remaining Ada-shaped boundary-risk category may
select Sonnet. V6.12 must not change Island boundaries, Candidate Q, graph
membership, scope observation, quantities or Estimation output. First live
route gates are V_Cabiner -> assembly_set/Haiku, Page23 -> native graphic pack,
Adda -> Ada/Sonnet, and HSL -> ordinary/Haiku. Audit each gate for category,
model, timing, cost, Island inventory and final Objects before considering any
membership work.

IMPLEMENTED, pending live HSL confirmation, V6.13 ordinary-proposal truncation
recovery: preserve the V6.12 category and model route. Retry Discovery exactly
once only when the initial proposal both consumes its 8,192-token budget and
ends inside a JSON string. The retry reuses the identical prompt, evidence and
images with a 12,288-token ceiling. All other invalid JSON fails immediately.
Persist both provider attempts and aggregate their measured time, tokens and
cost, so a recovered run cannot conceal the retry. First live gate: ordinary
Hasolelim HSL completes with the usual Haiku route, 35 Candidate Regions and a
valid proposal JSON. Do not treat this transport recovery as a change to
Fusion, Candidate Q, Island boundaries, routing, or membership.

VERIFIED, protected ordinary HSL checkpoint, V6.14 route-scoped scope
observation: V6.12 categorization has already selected the document scenario
before any Detection-model request, so ordinary, Page23, Ada and degraded
routes must not ask Discovery to re-classify document scope. Remove
`document_scope` from their prompt, strict output schema, audit payload and
provider response. Preserve it only for `assembly_set`, where V6.11 continues
as an audit-only observation and runtime now enforces its four roots, four
witnesses, four IDs per witness and 180-character observation bounds. Keep
V6.13's one-time truncation recovery as a rare transport safeguard, not a
normal ordinary-path cost. HSL `run_e8006a40e1fe4c68846b59b44dacaf4c` stayed
`ordinary_object_set`/Haiku, completed without retry at `$0.151403` Detection
cost, and retained 32 object-evidence Islands in ten components. Its page-2
floor plan was discarded document context. This protects the ordinary route
only. Deferred Naming and Preview defects remain separate, and future HSL
audits must preserve the full inventory, membership and cost evidence.

FAILED LIVE REGRESSION, V6.15 document metadata and
object-bound Naming evidence: retain the existing Naming prompt, locked object
identity, quantities, route selection, Discovery/Review sequence and
Estimation package. The existing Discovery response now carries one compact,
source-fact-cited sidecar for `project_name`, `design_partner`, `client`,
`author` and `document_date`; unknown is valid only without a citation. The
run record materializes those values while the citation audit stays in the
Detection usage event. After Registry locks its Islands, each object's final
Island bbox is added to its evidence refs and produces ephemeral Naming crops
in the same coordinate frame. Deferred Naming receives those object-bound
crops and only spatial OCR whose centre falls inside a locked Island. It no
longer receives full document pages on the V6.15 path. Explicit administrative
labels such as `Revision log` and `Surface schedule` are rejected as object
names. This must not change Island boundaries, object membership, quantities,
the Naming prompt, or the ordinary HSL route. Live gates: HSL must retain
ordinary/Haiku, 32 object-evidence Islands and ten components while filling
source-supported document fields and avoiding sheet-administration names;
then Page23 and Adda must retain their protected object boundaries. The first
ordinary HSL live gate failed: `run_07934b6dcbbc48bda1da8ea96e4d7d93` remained
on the ordinary Haiku route but produced 33 object-evidence Islands and 14
components, versus V6.14's 32 Islands and ten components in
`run_e8006a40e1fe4c68846b59b44dacaf4c`. The added metadata was requested from
the same mandatory Discovery response that owns Island discovery, so it is not
operationally isolated despite being described as audit-only. Its observed
values also did not meet semantic-role acceptance. Separately, the intended
object-bound Naming path did not run: the audit recorded `crop_count: 0` and
`objects_with_crop_count: 0`, so Naming fell back to whole pages. The cause is
that final normalized visual groups do not retain `evidence_class`, while the
crop helper filters strictly for `object_evidence`. Do not promote or extend
V6.15. Return to the V6.14 protected contract before a replacement experiment;
the replacement must obtain metadata outside the Discovery response, use real
Registry-owned crops, and pass HSL's 32-Island/ten-component gate before
Page23 or Adda regression.

FAILED RUNTIME OBSERVATION, V6.16 isolated document identity and locked Naming
evidence: the code passed focused local tests and preserved the V6.14 Detection
path by construction, but the first production attempt appeared to stall before
it produced a run ledger entry. It was reverted immediately to keep the V6.14
checkpoint live. A subsequent browser attempt reportedly completed, but no
corresponding run appeared in the queried production ledger, so the alleged
stall is inconclusive and must not be attributed to the document-identity code
without a correlated run ID.

ACTIVE, approved V6.17 isolated document identity, source-index Naming and
File Review metadata: preserve V6.14 Discovery, Review, routing, Islands,
proof graph, package membership and Evidence boundaries byte-for-byte. After
Registry has locked objects and File Review has been saved, derive a private
sidecar containing only each Registry-owned View ID, page and existing bbox.
Use that sidecar to make Naming-only crops and local OCR retrieval. Assign
only empty, `Unknown`, `Unlabelled`, `Untitled`, or generic `Object N` labels a
visible deterministic provisional name `Object 01`, `Object 02`, and so on.
Keep every recognized source code, including letter-suffixed `N76B` and
numeric-leading `7-6B`, as the final-name prefix followed by the semantic
description. Move File quality into Technical metadata only. The title-block
result must update the editable Project, Partner and Client fields in the
existing File Review without a full app rerun. The following V6.16 scope is
retained as V6.17 implementation detail:
preserve V6.14 Discovery, Review, routing, Islands, proof graph, package
membership and Evidence boundaries byte-for-byte. After Registry has locked
objects and File Review has been saved, derive a private sidecar containing
only each Registry-owned View ID, page and existing bbox. Use that sidecar to
make Naming-only crops and local OCR retrieval. Do not use full-page Naming
input when every locked object has a crop; retain the existing full-page path
only when a complete crop set is unavailable. In a separate deferred call,
read bounded title-block corner crops and update only still-`unknown` run
fields. `Project` maps only to project_name; `FILE NAME`, drawing identifiers,
logos and addresses cannot establish project, client or partner. Client and
Partner remain `unknown` unless their roles are explicitly visible. Neither
branch can add, remove, merge, split, reorder or rename Detection packages.
Gates: ordinary HSL remains 32 object-evidence Islands and ten components;
Naming receives nonzero Registry-owned crop evidence and returns category plus
source index where supported; HSL title block yields Project `ROOMS`, author
`Ayelet Levit`, document date `09.09.2025`, and no false Partner from
`Hasolelim_Carpentry`; Page23 and Adda then retain protected boundaries.

ACTIVE, approved V6.18 OCR-grounded document metadata and drawing indexes:
replace the unbounded deferred image-model identity call, which scheduled but
never emitted a terminal event in HSL `run_ff729e5345604d70a9f757fc4695bb76`,
with deterministic extraction from the already persisted Mistral OCR evidence.
The OCR fact `PROJECT -> ROOMS` is sufficient only for `project_name`; it does
not establish Client or Partner. Before locked Naming input is made, use only a
literal `DRAWING NAME -> code` title-block fact on an object's already locked
evidence page to replace an `Object NN` placeholder. Thus `N57`, `N60`, `N68`,
`N70`, `N76`, `N76B`, or other literal author codes can prefix the subsequent
semantic name, while an absent or conflicting code remains `Object NN`. Remove
Project name, Partner and Client from Technical metadata because they already
have editable fields above it. This must not change Detection's object count,
package membership, quantities, Island inventory, route, or Estimation package.

ACTIVE, approved V6.19 annotated source-page Naming experiment: supersede only
the V6.17 object-crop input contract. Preserve V6.14 Detection, Registry
membership, OCR, router, object order, quantities, source codes and Estimation
evidence. After Registry locks its View ownership, render each physical source
page containing at least one Registry-owned View once at the existing rendered
page resolution. Overlay every locked View bbox without fill. Each overlay must show
the immutable `object_id`, and every View belonging to one object must use the
same label and colour across pages. Naming receives those annotated full pages,
the existing locked object mapping and bounded OCR facts. It may return only a
semantic name suffix. It cannot alter object count, ownership, source index,
quantity, bbox or package membership. Record page count, source page numbers,
encoded image bytes, overlay View count and overlay-render audit in the
Detection usage event. First live gate is HSL: ordinary Haiku Detection remains
32 Islands and ten objects, Naming emits a terminal event, and the request
contains one annotated page per Registry-Island page rather than one crop per
View. Compare Naming duration, tokens and cost with V6.14 before extending the
experiment to Page23 or Adda.

LIVE AUDIT, V6.19 HSL `run_a209ce477a914e63a277ade7a6577e2e`: Detection
preserved the protected ordinary Haiku result, 32 Registry-owned Views and ten
objects. The overlay contract also materialized correctly: nine annotated
source pages (P3-P11), 32 overlays, ten object labels and 2,139,216 encoded
image bytes. However, no `locked_object_naming_deferred` terminal event exists,
neither success nor failure. The current File Review therefore shows only
deterministic source indices, not a semantic Naming result. Do not evaluate
V6.19 naming quality or cost from this run. The immediate diagnostic must add
nonblocking durable lifecycle evidence that distinguishes submitted, worker
started, provider returned and terminally persisted Naming. Separately, File
Review has two unconditional `run_every=2.0` fragments. The dynamic fragment
refreshes even without deferred work, and the metadata branch never marks its
document-identity flag complete. This is the supported cause of its perpetual
two-second refresh cycle; repair that UI lifecycle independently from Naming.

SUPERSEDED INPUT CONTRACT, V6.5, no static pre-Discovery crops: remove the three
fixed `upper_left`, `upper_right`, and `lower` images from the Adda
`sonnet_boundary_risk` route as well as the ordinary Haiku route. Retain the
same 200-DPI complete rendered pages, Fusion, Candidate Regions, router,
model route, Candidate Q, Review page contexts and post-Discovery View crops.
This isolates whether a page grid which cuts an authored drawing before its
Island is known causes the unstable Adda proposal/review result. First gate is
Adda: exactly two non-overlapping commercial components with counter Views
`P1.V2,P2.V1,P3.V1,P4.V1` and L-shaped cabinet Views
`P1.V1,P2.V2,P3.V2,P4.V2`. The next gates are unchanged Page23 and HSL
protected inventories. A no-crop result with two objects alone is insufficient:
the exact View membership and per-page Island geometry must also pass.

OPEN DIAGNOSTIC, P0, V6.4 Adda Registry instability: compare completed Adda
runs `run_d76e1c6d03374581aa84936676a5d8ad`,
`run_6776dd3ea03040c9b38f8d060863001a`, and
`run_f35b802961ce49d094759890fd42e7cc` before changing the active contract.
Mistral Candidate Regions are byte-for-byte stable at the correct page-local
boxes for pages 2 and 3, but Discovery redraws its own `visual_groups` boxes
from the full page plus static crops. The second proposal's page-2 L-shaped
envelope begins at x=490 instead of the candidate x=913, while the latest
proposal returns a corrected core. Review receives only those model-drawn
groups and their derived crops, so it cannot recover a discarded candidate
boundary. The latest Review also emits an overlapping counter hypothesis;
runtime rejects that duplicate, retains its earlier incomplete three-view
hypothesis, and consequently packages the missing page-1 counter view as a
third standalone object. Establish, by a narrow A/B, whether the fixed
upper-left/upper-right crop boundary, which cuts the page-2 L-shaped drawing,
is causal, and then propose a candidate-region-to-Island admission contract.
Do not treat image XObjects as object boxes: Adda has zero Form XObjects and
only small raster placements; its object-level candidate boxes come from
Mistral graphic regions.

DEFERRED, P2, USER DIRECTION, Detection input and cost optimisation: begin
only after the owner concludes the current correctness experiment. Assess the
full-page Evidence Inventory, Candidate Pair Q prompt rendering, static crops,
review images, output budgets and any other input/output reduction by isolated
benchmark, while retaining the underlying evidence, Q calculation and
deterministic graph unless separately approved. Do not treat HSL's currently
unreferenced facts as globally removable.

DEFERRED WORKING BLOCK, P1, USER DIRECTION, visual matching, geometry evidence
and Estimation preparation: begin only after the owner accepts the current
Detection correctness experiment. This is research and a benchmark plan, not an
approved replacement of Detection, Fusion, routing, DINO, Candidate Q or the
Estimation contract.

Current verified system map:
- Candidate Regions are recall bounding boxes, not a similarity engine. They
  originate from Mistral `image` blocks, or broad spatial clusters of evidence
  facts if no graphic block exists. They never identify objects or compare
  views.
- Candidate Pair Q / Dimension Fingerprint / Weighted Similarity is the
  deterministic mathematical comparison channel. It evaluates normalized
  dimension-chain values, occurrence, page context and normalized Island
  placement. It supplies supporting evidence only and cannot merge a commercial
  object by itself.
- The current DINO channel is `facebook/dinov2-small`, 384-dimensional global
  CLS embeddings of source-authored PDF image XObjects. It is limited to the
  narrow source-degraded native-anchor route, compares same-page placements,
  and requires mutual top-1, cosine >= 0.80 and margin >= 0.10. It remains
  visual supporting evidence and never creates an edge alone.
- Current Mistral is `mistral-ocr-4-1`, with `include_blocks=true` and block
  confidence requested. Its raw blocks, page confidence and provider response
  are retained. Normalized Fusion text facts currently retain block type, text
  and bbox, but do not copy each block's confidence values into the derived
  facts. This is a possible later quality signal only, never geometry proof.
- V6.1 PyMuPDF inspection already inventories text, image XObjects, Form
  XObjects and bounded vector summaries. `get_cdrawings()` / `cluster_drawings()`
  are not semantic dimension-line extraction and must not be sent as raw vector
  dumps to a model.

Research evaluated:
- DINOv2 can also yield patch features. Test only as a bounded local-
  correspondence supplement for already eligible, visually similar 2D views;
  it must not become an embedding-only merge rule.
- DINOv3 may be benchmarked against DINOv2 only after a license/product review
  and a measured CPU/Railway artifact experiment. It is not a current upgrade.
- LightGlue is a local-feature matcher, not a semantic or 3D-view matcher. It
  may help only with near-duplicate, scaled or rotated 2D depictions after a
  licensed detector and geometric inlier validation are chosen. It is not a
  general solution for front/side/top orthographic views.
- SigLIP 2 is potentially useful later for broad semantic retrieval or
  classification, not commercial-object identity, dimensions, materials or
  quantity.
- SAM 3 could create optional candidate masks in raster-heavy pages, but there
  is no evidence it is a strong vector technical-drawing solution. Its model
  license and resource requirements require separate review.
- MASt3R is excluded from product implementation: its published license is
  CC BY-NC-SA 4.0 and its evidence concerns photographic multi-view matching,
  not engineering projections.

Highest-value proposed research direction: an object-bound, line-aware
geometry-evidence extractor inspired by Martin Riegelnegg's 2024 TU Wien
diploma thesis, "Automated extraction of complexity measures from engineering
drawings." The thesis uses entity segmentation, arrowhead / dimension-line
processing, object-view segmentation, orthographic view-grid reconstruction,
axis assignment and OCR-to-pixel consistency. Its reported 0.731% mean
absolute external-dimension percentage error applies to 81 of 84 selected
detail drawings after excluding three OCR-failed cases. It is not evidence of
accuracy for Costerly's multi-object carpentry sheets, plans, schedules,
perspectives or incomplete drawings.

Target boundary, not current behavior:
Detection locks commercial-object identity, quantity and cited evidence pages;
then an eligible object-specific geometry stage emits auditable candidates;
then Estimation interprets construction / Material Demand; Resolver, Material
Engine and Labor Engine remain deterministic. Geometry output must preserve
page reference, object/view bbox, dimension-line bbox, linked OCR literal,
arrow/line orientation, scale-ratio consistency, axis hypothesis and conflicts.
It returns `not_applicable` or `review_required` rather than invented W/H/D,
materials, BOM or labor facts. Presentation Preview remains UI-only.

Eligibility and verification before any integration:
- operate only on object-bound technical detail/elevation/section evidence with
  readable dimensions and adequate raster or vector geometry; exclude schedules,
  title blocks, whole floor plans and unsupported perspectives by default;
- create a manually labelled geometry benchmark of object-bound furniture
  detail views, not Page23 alone; record source line to dimension literal,
  external axis/value, unavailable cases and false associations;
- compare current literal-only evidence against the line-aware candidate output;
  define precision, recall, conflict and `not_applicable` acceptance criteria
  before coding; do not promote a value to Estimation merely because it is
  numerically plausible;
- independently measure CPU, memory, latency, model artifact size, provider
  tokens/cost, license fit, HSL / Adda / Page23 regressions, and evidence-package
  compatibility before any product decision.

SUPERSEDED IMPLEMENTATION, P1, V6.1, USER DIRECTION, Detection document pre-analysis:
define a non-decisive,
page-level technical profile that records what each rendered PDF page can
provide deterministically. It must report native text availability and quality,
image XObject/Form XObject/vector-drawing inventory, rendered-page properties,
visual density and structural complexity, coordinate-bearing evidence
capability, and the cost/timing of every local inspection. The document result
is a list of immutable page profiles plus a derived summary, never one global
document type. Run it asynchronously or in parallel with the existing
PyMuPDF/Mistral work, persist an audit even if it finishes after Registry, and
do not let failure, output, model choice, Island
inventory, Dimensions, graph, packages, or File Review change during this
observation phase. V6.1 explicitly passes the compact profile audit through
Fusion diagnostics but does not add it to the Registry prompt. Acceptance
requires no-behavior-change evidence plus measured incremental critical-path
latency for Page23, HSL and Adda.

Native PDF image XObject placements are already extracted for every PDF in the
OCR worker and retained as `evidence.graphic_regions`; however, the ordinary
Fusion candidate builder currently consumes Mistral graphic regions or text
clusters, not those native placements. Treat every XObject bbox as a
source-authored graphic envelope and recall/diagnostic input only, never as an
object boundary or merge proof. The existing V5.37 immutable-anchor gate stays
separate and narrow: all rendered pages must have 2-12 independent eligible
image placements, each covering 5-70% of its page. Do not broaden that gate or
add embedding to ordinary PDFs without a separate approved experiment.

Later decision: replace layered router mutation with one auditable
`DetectionExecutionPlan` composed from independent axes, including evidence
path, boundary-risk model, Island-anchor authority and optional embedding
availability. Do not merge their criteria into one "complex document" score.
First verification artifact: profiles and no-behavior-change traces for HSL,
Page23, Adda, and a mixed-evidence PDF, including identical current routing and
Detection outputs plus measured incremental CPU, memory and critical-path
latency. Only then decide the mixed-evidence contract and whether native
XObject recall is admissible in ordinary Fusion.

ACTIVE DIAGNOSIS, P0, Processing to File Review client transition defect:
the same run completed Registry in 23.28 seconds and server-side File Review
in 26.67 seconds, while the browser recorded a 15.001-second
`processing_to_file_review` timeout. The current browser readiness predicate
requires `.file-review-card`, but the renderer produces
`.file-review-summary-card-marker` instead. This prevents the browser from
acknowledging the already-rendered File Review and leaves the Processing shell
visible. Do not alter Detection, OCR, or provider timeouts. The repair must
align the browser predicate with the actual File Review marker, retain the
existing 120 ms handoff, and be verified in an authenticated production cycle
by a terminal `browser.transition_ready` rather than only a server render.
The marker-contract repair and regression test are implemented locally. Production
verification remains required before this item can be closed.

DEFERRED, P1, USER REQUEST, Detection Processing provider-outage handling:
when Mistral OCR is unavailable, exhausted, rate-limited, or times out, the
Processing screen must never remain at its initial elapsed value. Persist a
safe early lifecycle marker before OCR, record a terminal OCR failure/timeout
with its stage and duration, and show truthful pending/fallback state while
the bounded no-OCR route runs. If the run cannot continue, expose a retryable
terminal state rather than an infinite Processing screen. Preserve the normal
parallel OCR path and do not add a second Detection call. Acceptance requires
a forced Mistral 402 and a forced timeout to reach an observable terminal or
explicit fallback state without leaking credentials or file content.

BLOCKED QUALITY GATE, V5.9 HSL `v590-hsl-04`: the cross-document run rejects
the experiment in its current form. It returned 31 raw Visual Groups, 28
Object-Evidence Islands and 12 packages, rather than the protected HSL 32/9
orientation. P03 has two rather than three Object Islands; P07 remains four
single packages; P09 splits into two; P11 has three groups but classifies every
one as Document Context, leaving no package. The Proposal cost `$0.158686`
and took `61.559s`; Review cost `$0.027967` and took `22.358s`; combined
provider time was `84.788s` (`110.223s` end-to-end). Do not tune package merge
or Semantic facts from this result. The next causal repair, if approved, is
Island segmentation: one physically continuous visual depiction is exactly one
Island even if its silhouette bends, branches or is highly non-rectangular.
Its bbox is only a padded rectangular transport envelope around that complete
connected depiction. A split continuous shelf and panel is an Island defect,
not two Views to repair downstream.

CONFIRMED ROOT CAUSE, before any later Island-reconciliation experiment: V5.9
has no explicit coordinate-frame transform between Fusion and Review. Native
MyPDF spans and Mistral OCR/graphic Regions are produced at 200 dpi; Registry
Proposal/Review pages are rendered at 96 dpi. Page23 measures 3308x2339 in
the Fusion frame and 1588x1123 in the Review frame. Proposal emitted a
Fusion-frame bbox through x=3265, but Review cropped and overlaid it directly
on the 1588-pixel image. The second call therefore receives displaced or
clipped View crops and misplaced Island labels. This invalidates V5.9 Review
quality conclusions, including its HSL segmentation result. The isolated
Page23 geometry gate now passes locally: all 200-dpi Fusion bboxes transform
to their 96-dpi Review locations, including VG-005 x=1600..3265 becoming
x=768..1567. External run `v590-coordinate-page23-02` independently confirms
the recorded Mistral 3308x2339 to Review 1588x1123 frame, 4 object Islands and
3 packages: shelf, doors, and the linked two-view TV console. It costs
`$0.022186` and takes 32.375 seconds wall time. Coordinate correctness is now
verified for Page23, but this does not validate HSL segmentation or justify
continuity unions or semantic tuning.

V5.10 benchmark state, 2026-10-23: Page23 `v590-coordinate-page23-02`
passes its discriminating boundary at 4 Object Islands and 3 packages. Adda
`v510-adda-01` produces 8 Object Islands and 2 packages, so its package count
is compatible with the known two-object case but Island membership still needs
inspection. Metal `v510-metal-01` fails the universal merge gate: 30 Object
Islands become 28 packages, including five separate packages each on P04 and
P05, versus the roughly 13-15 expected commercial objects. HSL `v510-hsl-01`
did not produce a result, because Proposal JSON truncated in an unterminated
string after 25,358 characters. This is an output-contract failure, not an
Island-quality result. V5.10 is not a checkpoint. First recover a complete HSL
Proposal response without weakening Island or membership evidence, then inspect
Adda membership and Metal page-level boundaries.

P1, pending, V5.10 benchmark failure-cost observability: the local runner
currently records only `repr(exc)` after a failed provider call and drops the
exception's available usage event, so the HSL failed-call cost is unknown in
its local report. Persist safe usage totals and diagnostics on failure, without
logging secrets or retrying automatically.

V5.10.1 HSL `v5101-hsl-01` proves that Proposal output compression is safe for
Island recall: it completes JSON and returns the required page-level Island
inventory, but all Review facts were rejected because the handoff represented
an ID and its text as `SF00123:text`. V5.10.2 `v5102-hsl-01` uses bracketed
source IDs and returns 33 Object Islands, 12 packages, 27 accepted semantic
facts and 21 merge edges. Page-level HSL Island counts meet the active
benchmark: P03=3, P04=6, P05=3, P06=3, P07=4, P08=4, P09=3, P10=3, P11=3.

V5.10.3, verified locally without a provider call: canonicalise only a source
ID in the exact display form `[SF00123]` when the interior `SF00123` is already
known in that run's evidence. Keep the raw Review response unchanged and write
every conversion to `source_id_normalizations`; unknown wrappers remain
rejected. Reprocessing saved HSL Review `v5102-hsl-01` accepts all 65 of its
semantic rows, records 65 such canonicalisations and leaves zero unknown-source
rejections. This validates citation transport only, not the commercial merge
outcome. In particular, P04 may legitimately contain one to three products, so
its package count is not a quality gate. The next provider run must compare the
same page-level Island inventory and View membership, not force P04 into one
package or toward a global count of nine.

V5.10.3 HSL provider run `v5103-hsl-01`, 2026-10-23: the source-ID repair
holds in the complete cycle. It returns 63 accepted semantic facts, no accepted
bracketed source IDs and no `unknown_source_fact` rejection. HSL keeps the
required Object-Island counts on P03-P10, P04=6 and P11=2 Object plus 2 Context
Islands, which are both within the permitted inventory range. P04 produces one
package, an allowed outcome. The run is not a checkpoint because P02's generic
floor plan is again classified as `object_evidence` and published as a singleton
package. The existing generic-plan safeguard did not apply because Registry
mislabelled its `representation_kind` as `object_evidence` instead of
`floor_plan`. Diagnose and repair that classification-contract breach in
isolation before any package or graph tuning. Timing: 165.346 seconds total,
Registry cost $0.206013.

P1, pending, V5.6.10 semantic criteria: stricter `matching_topology` and
`direct_shared_structure` wording was not regression-proven. Re-evaluate it
only after the V5.7.1 boundary strategy is measured across the MVP pack.

Historical V4 notes follow. They are retained for rationale, not the active
implementation plan.

HISTORICAL, Detection V4 commercial-boundary stability: protected checkpoint
`52c314d` retains accepted Naming, File Review, temperature-zero, complete
Evidence, and Page 23/Adda boundary behavior. Hassola LIM is the active
boundary benchmark. The MVP floor is now 9 commercial packages: N56, N57,
N60, N62, N68, N70, N74, N76, and N76B. N57 may remain one review-required
source-root package with all its Evidence, while Estimation later decides
whether to split kitchen, island and tall cabinet. The active V4 candidate
requires every retained object-evidence island to have exactly one package.
Shared physical-page Evidence remains freely reusable.
This adds no model call, router, Sonnet route, or file-specific override.
Preserve object-ID locking, full object evidence, UI-only previews, deferred
Naming, File Review timing, and TC. Next gate: fresh HSL run must produce the
9 packages with complete page-4 Evidence, then regress Page 23 and Adda.
Current model build: `Detection V4.43`, experimental, built on the protected
V4.23 passive OCR cross-check and checkpoint `52c314d`. Comment: V4.12 still
treated every N76B page-11
depiction as a partial component, then attempted to attach all three to N76B.
The failure proved that assembly/component was an invalid eligibility gate, not
that their source Evidence was wrong. V4.13 allowed any full view or detail to
support an object, but still let the model declare membership twice: a group
could be object evidence yet be omitted from the object's group list. V4.14
removes that duplicate ownership declaration. Every visual group is
object-specific Estimation Evidence and names one or more owners locally; code
derives each object's group package from that ledger. Cover/title pages,
generic floor plans, room layouts, electrical, plumbing, lighting, legends and
other non-object-specific pages make no visual group and have empty Evidence
coverage. Detection may still use them for metadata, sheet codes or navigation.
V4.15 preserves that ledger and replaces loose merge-proof type labels with
typed, page-attributed visual facts. The evidence order is explicit document
relation, dimension transform, matching topology, unique geometry, then direct
shared structure. At that stage, a non-explicit merge needed two independent
facts and at least one identity-level fact; direct shared structure alone
cannot merge.
V4.16 discards generic floor plans, title pages and title blocks from the
effective visual-group payload before ownership, proof construction, identity
pages and Estimation Evidence. An object-specific plan remains eligible only
as `object_plan`. This adds no model call, router, Sonnet path, Naming or UI
timing. V4.17 replaces the V4.14 owner ledger as the source of object
membership. The model now returns only object-specific visual groups, typed
pairwise merge facts, one component descriptor per proof-graph component, and
page coverage keyed by that component descriptor. Runtime derives every
commercial object and its `visual_group_ids` solely from the connected proof
forest, assigns ordered runtime object IDs, then resolves Evidence coverage.
An unlinked group is a singleton object, a multi-group object cannot exist
without its minimal proof tree. A physical page remains reusable Evidence for
several components, but one visual group cannot be an owner declaration for
several objects. No model call, router, Sonnet path, Naming or UI timing is
added. The HSL V4.17 failure showed that an optional top-level proof array can
still be omitted while the model returns a smaller set of object descriptors.
V4.18 replaces that optional array in the model contract with one required
`proof_parent` decision on every visual group: either `new_object_root` with a
factual reason, or `attach_to_group` pointing only to an earlier group with
typed evidence facts and a factual reason. Runtime derives the same proof
forest and object packages exclusively from these group-level decisions, and
persists every decision and its answer to "why" in the Registry audit. This
adds no model call, router, Sonnet path, Naming or UI timing. It is not a
checkpoint until HSL produces the canonical 11 packages with complete
object-specific evidence, followed by Page 23 and Adda regression gates.
V4.19 permits one exact `dimension_transform` as a sufficient attachment fact:
it must name measurements on both views and their axis or unit transformation.
"Compatible" dimensions, similar scale or one repeated number are not enough.
All other non-explicit attachments still require two independent typed facts.
V4.20 requires a persisted `dimension_assessment` for every root-or-parent
decision. Before an attachment, Detection compares readable dimensions after
document-wide unit normalization and projection/axis transformation. A
confirmed match can support the existing `dimension_transform` fact. A
confirmed conflict in the same physical axis and scope is a structural no-merge
condition, including when a shared code or sheet might otherwise suggest a
relation. It must become a root with the rejected group's ID and conflicting
measurements in the persisted factual reasoning. Different axes, whole-object
versus local-detail measurements, quantities, scale or missing readable values
are explicitly recorded as not comparable or insufficient, never treated as a
conflict. No model call, router, Sonnet path, Naming or UI timing is added.
V4.21 retains the same dimension-conflict guard but replaces the verbose nested
assessment with a compact required `dimension_status`; the existing mandatory
`decision_reason` remains the factual explanation, including rejected group and
measurements for a conflict root. This avoids exhausting the Registry output
budget on repeated explanation. JSON parse failures now persist a failed
Registry usage event with response length, SHA-256, provider stop reason and
token budget, so truncation versus malformed provider JSON is observable.
V4.22 makes the compact `dimension_status` bidirectional with typed evidence:
`confirmed_match` is valid only with an exact `dimension_transform` fact naming
measurements on both groups and their transformation, and that fact requires
`confirmed_match`. A bare status is never merge evidence. This prevents a
model's generic claim that dimensions agree from bypassing the independent-fact
threshold for a section or alternate view.
V4.23 removes that duplicated positive representation: an exact
`dimension_transform` is now the sole source of a positive dimension match.
When a same-scope dimension conflict rejects one plausible earlier group,
Detection must search every other earlier object-specific group before it
creates a root. It may attach only to an evidence-backed non-conflicting group;
otherwise the root persists a typed `blocked_merge` naming the rejected group
and both incompatible measurements. This preserves the critical no-merge rule
without forcing the model to serialize the same conclusion twice. It adds no
model call, router, Sonnet path, Naming or UI timing.
V4.24 and V4.25 were rejected experiments: making OCR `image` regions a
Registry coverage contract, then requiring a new all-island output, caused
Haiku to classify the entire HSL package as administrative. The active V4.23
cross-check instead appends the same OCR graphic-region coordinates as a
passive visual re-inspection aid. The model first identifies Visual Groups from
rendered pages using the protected V4.23 contract, then may revisit an OCR
coordinate. OCR can neither create, split, merge nor invalidate an object, and
no response field or validation requires equal counts. Runtime persists raw
OCR-region and Visual-Group counts by page on successful and failed Registry
events. No model call, router, Sonnet path, Naming or UI timing is added.
Visual Group discovery gate is provisionally met: the HSL audit found all
three N56 depictions despite only two OCR regions, and four different
subsequent files preserved or exceeded their OCR depiction count. Checkpoint:
`notes/DETECTION_V4_23_PASSIVE_OCR_VISUAL_DISCOVERY_CHECKPOINT_2026_10_19.md`.
Next gate: diagnose and repair HSL pairwise merge proof failures without
changing this protected visual-discovery contract.
V4.26 is the approved one-call structural experiment. It preserves the complete
visual-island search, passive OCR audit and temperature 0, but replaces the
incremental `proof_parent` decision with explicit staged output: complete island
inventory, mandatory `object_evidence` or `document_context` classification
with a factual reason, full typed proof graph between any object-evidence
groups, and finally packages derived by code from graph components. A document
context may not enter the proof graph. The audit persists classification reasons,
every graph observation and each package's boundary/Evidence reasons on success
and validation failure. Acceptance requires successful V4.26 runs with this
audit, then Page 23 and Adda regressions before HSL package quality is judged.
V4.27 keeps the one Haiku call, temperature 0, passive OCR recall aid and the
same proof/package rules, but serializes the response into five non-overlapping
phases: visual-island inventory, exact-once classification, global proof graph,
component packages, then page coverage. Inventory cannot carry a class; each
group receives exactly one later factual classification without changing the
inventory. The prompt also prohibits coalescing separate side-by-side views,
facades or dimension depictions into one island. Classification, graph and
package reasoning remain persisted on both success and validation failure.
Acceptance: recover V4.23-level island recall on HSL, then evaluate HSL
packages, Page 23 and Adda against the protected checkpoint.
V4.28 is approved after intermediate checkpoint `99a9fa1`. It adds the sixth
typed graph relation, `context_reference_link`: a composite view may reference
multiple independently quoted products, but this relation is excluded from
proof components and can never merge them. For an authored sheet-level root
code such as N57, Detection may split products only with separate product
evidence; Naming retains N57 and adds deterministic A/B/C suffixes in product
order. The target is N57A kitchen, N57B island and N57C cabinet, not one
commercial N57 package.
V4.29 is the approved follow-up experiment. It preserves V4.28's proof rules,
context links, one Haiku call, temperature 0 and passive OCR recall aid, but
adds an exact-once package-decision ledger after the graph. Every commercial
visual group must resolve explicitly as `part_of_proven_component` or
`standalone_package`; a context-link source is shared Evidence rather than a
commercial group. A claimed but insufficient relation cannot silently suppress
a package. Runtime verifies every decision against the accepted proof
components and persists it with the Registry audit. Acceptance: HSL succeeds
without an unproved merge, every eligible group is accounted for, and the
result is then regressed against Page 23 and Adda before any checkpoint.
V4.29 is rejected by its first HSL run, not for an inference defect: the
full 31-row ledger exhausted Anthropic's 8,192 output-token limit and truncated
JSON (`stop_reason=max_tokens`). V4.30 retains the binary outcome but transmits
only the sorted `standalone_package_group_ids`; graph connectivity deterministically
establishes the complementary proven-component outcome and runtime persists the
complete per-group ledger. This removes duplicate output without raising the
model budget, adding a call, or relaxing proof validation. The same HSL, Page
23 and Adda acceptance gates apply.
V4.31 object-plan/context-link expansion is rejected as inconclusive. Its first
HSL run reached the Registry provider but exhausted the fixed 8,192 output-token
budget and returned truncated JSON before any semantic Registry validation. The
active behaviour is restored exactly to V4.30. A privacy-safe failed-JSON
observer now persists no raw response, only the reached top-level section,
terminal property key and depth, per-section observed character counts, JSON
error position, open-string state and output-budget utilisation. Its next run
must identify which contract section exhausted the budget before a new boundary
or output change is considered.
V4.32 is the approved one-call repair for the observed HSL self-edge failure,
where the model attempted `G4 -> G4` instead of relating the N56 plan to a
different N56 view or declaring it standalone. A proof edge now explicitly
requires two different group IDs. Before the existing compact singleton-ID
declaration, the same Registry response performs one final audit of every
unconnected object-evidence group against all other object-evidence groups:
add an accepted edge to a different group, otherwise declare the group
standalone. It adds no provider call, response field, token budget, router,
Sonnet path, or validation relaxation. The self-edge remains a hard runtime
rejection. Acceptance: valid HSL graph without a self-edge, then Page 23 and
Adda regressions before any checkpoint.
V4.33 adds the sixth typed graph fact, `dimension_equality`. It is distinct
from `dimension_transform`: it records the same readable physical dimension,
unit and scope on both groups without conversion or axis remapping. One equality
is strong support but cannot merge alone; two independent equalities are
sufficient dimension proof and further equalities reinforce that proof. Before
deciding every candidate relationship, the single Registry call now assesses all
six typed facts. It serializes every positive fact on accepted merge edges but
not a quadratic ledger of negative comparisons. This adds no provider call,
router, Sonnet path, output field, token budget or validation relaxation.
Acceptance: HSL must retain its visual-group inventory, emit the common N56
dimensions as typed facts, form only valid proof edges, then regress Page 23
and Adda before any checkpoint.
V4.34 replaces directional `context_reference_link` with an undirected
`reference_link` using lexically ordered `group_id_a` and `group_id_b`.
`shared_reference_group_ids` records a general view that relates two or more
independently quoted packages. It is shared Estimation Evidence, not a package
or a commercial owner. Reference links never merge components, and every other
object-evidence group remains either a proven merge component or an explicit
standalone package. This removes the artificial context-chain rejection without
relaxing merge proof or ownership validation. It adds no provider call, router
or Sonnet path. Acceptance: valid HSL graph with N76B, then regress Page 23
and Adda.
V4.35 keeps that undirected graph but validates `shared_reference_group_ids`
only after merge components and declared standalone packages are proven. A
shared composite view must directly reference at least two distinct commercial
package anchors, not merely two visual groups or two views of one package. A
generic floor plan or room layout remains `document_context`, even if it shows
placements, and can never become shared Evidence. This adds no model call,
router or Sonnet path. Acceptance: HSL must not classify G002 as commercial or
use G031-G033 as shared Evidence; N76B must instead be proven as its own
package, followed by Page 23 and Adda regression.
V4.37 removes the final duplicate package declaration from the one-call
Registry contract. Runtime derives singleton packages from the accepted proof
graph, so a model cannot fail the RFQ merely by omitting or miscopying the
same result into `standalone_package_group_ids`. Model `objects` rows become
optional descriptive metadata only. A graph component that lacks one valid row
is preserved as a deterministic quantity-one package, receives every physical
page containing its proven visual group as Estimation Evidence, and is marked
`review_required` in File Review. The Registry audit records accepted metadata,
discarded metadata rows, fallback object IDs and deterministic page supplements.
This adds no model call, router, Sonnet path or relaxation of proof, ownership,
classification or page-coverage validation. Acceptance: HSL must complete
without a descriptor/standalone-list validation failure, then regress Page 23
and Adda before checkpointing.
V4.38 replaces the sparse provider proof-edge response with a compact,
exact-once relation ledger. Every `object_evidence` pair has six persisted
criterion states: positive, checked-negative, conflict or unreadable. Every
visual group also returns its readable dimensions once. Positive graph facts
remain concrete and page-cited; two independently recorded dimension equalities
are sufficient merge evidence and three or more are very strong. Runtime builds
provisional components and packages only after the complete ledger, then applies
the semantic proof threshold. This keeps one Haiku call and temperature zero,
but raises the Registry output ceiling from 8,192 to 12,288 tokens to preserve
the complete compact ledger. Acceptance: HSL must return a complete pair ledger
without truncation, preserve every positive dimension fact in its merge graph,
and then pass Page 23 and Adda regressions. V4.39 retains every six-criterion
pair state and positive, page-cited dimension fact, but removes the duplicated
per-group `dimension_inventory` transcript from the model response. Full OCR
and rendered pages remain the literal source record for Estimation and graph
inspection. This corrects the contradictory instruction to both return and not
extract dimensions, while preserving the rule that Detection never infers or
publishes final external object dimensions. It keeps the 12,288-token ceiling
and one Haiku call. Acceptance: HSL returns valid JSON and its full graph,
then Page 23 and Adda retain their protected outcomes.
V4.40 is approved after the V4.38-V4.39 dense pair-ledger experiments proved
that a complete negative matrix cannot fit HSL within the established response
ceiling. It restores a sparse positive graph while retaining V4.33's six typed
facts, especially `dimension_equality`, and requires the model to inspect every
pair but serialize every positive equality, transform and other typed fact only.
`dimension_equality` records direct same-axis literal matches;
`dimension_transform` records a separately named unit or axis remapping. Both
may be present on one pair. Runtime derives components from accepted merge edges
only. A weak, cyclic, duplicate or otherwise unusable individual relation is
persisted as a rejected candidate and cannot fail the RFQ or erase unrelated
packages. Every unmerged object-evidence group becomes a quantity-one,
review-required standalone with its physical page Evidence. `reference_link`
is undirected, non-merging Evidence annotation: it adds linked pages to each
related package but cannot hide a standalone or block validation. Generic floor
plans remain `document_context`. This keeps one Haiku call, temperature zero,
full OCR and page Evidence, without Sonnet or retry calls. Acceptance: HSL
completes with every retained group assigned exactly once to a package, accepted
and rejected relations visible in the audit, and all positive equality and
transform facts persisted; then regress Page 23 and Adda before checkpointing.
V4.42 replaces the invalid V4.41 full pair ledger with the accepted V4.40
positive-fact graph. It keeps one Haiku call, temperature zero, full island
discovery, graph-derived packages, page Evidence and quantity-one standalone
fallbacks. Before the graph, the model records each retained group's literal
dimensions once in a linear source index. It then emits only positive typed
edges: `same_object_view`, `object_detail`, `reference_link`, or
`supporting_relation`. A supporting relation preserves one positive fact without
silently merging or sharing Evidence. Packages derive only from accepted merge
edges; every unmerged object-evidence group becomes review-required standalone.
An invalid dimension index is observable but cannot abort otherwise proven
packages. The HSL acceptance target is a completed File Review, every retained
group assigned once, N57 permitted as one source-root package for MVP, N76B
retained as its own dimensioned standalone when unconnected, and no quadratic
negative-pair output. Then regress Page 23 and Adda before checkpointing.
V4.43 retains one temperature-zero Haiku call and the V4.42 island and
classification stages, but removes model-owned graph, package, coverage and
metadata declarations. The model returns only complete visual islands,
per-island classification, and literal typed source dimensions without unit
conversion. Runtime checks every retained pair, records one exact equality as
support, accepts two independent matching overall dimensions or an independently
proven two-reading axis transform as a merge, and persists all resulting facts,
conflicts and graph audit. A single literal
`DRAWING NAME` code in an OCR title-block table may build a review-required
source-root tree for its sheet. It cannot override a direct same-kind overall
dimension conflict. Invalid model dimension inventory yields auditable,
quantity-one standalone packages rather than an RFQ failure. Generic plans,
title pages and title blocks remain out of Estimation Evidence. Acceptance:
HSL completes with N57 as an allowed whole source-root package and N76B
separate, then Page 23 and Adda retain their protected outcomes.

V4.44 is an approved isolated dimensions-only graph experiment. It preserves
the V4.43 visual-island and classification stages, one temperature-zero Haiku
call and full OCR Evidence, but replaces the provider's unbounded local-
dimension transcript with at most one maximal outer-envelope chain on each
readable horizontal and vertical axis. A direct outer total wins unless a
continuous outer segment chain sums to a greater span. Runtime alone sums
literal segments, compares all retained pairs, and writes only
`dimension_equality` facts. Equality permits up to one-percent drawing drift,
including 406 versus 407. The global document unit is read deterministically
from explicit OCR markers before Registry; bare values inherit it only when all
visible unit markers agree. No author-code root, transform, topology, conflict
or other relation type participates in this graph experiment. Acceptance:
inspect the HSL graph for maximal chains, computed sums and equality edges
before evaluating object packages, then decide whether this becomes the new
graph foundation or is reverted to V4.43.

V4.45 follows the failed HSL V4.44 run. It keeps the same one-call,
dimensions-only graph scope but makes the island to chain binding explicit:
one separately framed, dimensioned or positioned drawing is one immutable
visual group, even when it depicts the same product as its neighbour. The
model may return no chain for an unreadable axis. Runtime canonicalizes only a
completely empty synthetic chain to that existing no-chain state, preserving
all literal measurements. The graph remains only deterministic
`dimension_equality`; no packages, ownership, codes, transforms, topology or
other proof types are part of this experiment. HSL acceptance: the graph must
retain valid chains when another group has no readable outer size, and expose
the obvious external-width comparisons before any later object-assembly work.

V4.46 keeps V4.45's one OCR pass, one temperature-zero Registry call and
dimensions-only graph scope, but replaces each OCR image annotation's flat text
with structured literal geometry. Every image bbox now returns: the complete
verbatim text, `declared_dimensions` such as `H=60`, and one
`page_horizontal` plus one `page_vertical` outer-dimension observation. Each
axis explicitly states `readable` or `not_shown_or_unreadable`; no synthetic
blank chain is used. `H`, `W`, `D`, `L`, `Ø`, `R`, `T` and `THK` are literal
source symbols, not inferred object boundaries or chain segments. Detection
receives those facts separately, so `H=60` cannot be substituted for a nearby
literal chain segment. Acceptance: on HSL, page 4's `H=60` remains a declared
height fact while its horizontal `331 = 64 + 203 + 64` chain is independently
reported; measure the unchanged one-pass OCR timing before any Vision Object
Detection experiment.

V4.47 rejects V4.46's request that OCR infer horizontal or vertical geometry.
It restores the prior text-only bbox annotation and deterministically extracts
only exact symbolic literals from that transcription: `H=`, `W=`, `D=`, `L=`,
`T=`, `THK=`, `Ø` and `R`. The parser preserves page and source bbox, but does
not derive a chain, sum values, select an axis or attach a commercial object.
The Registry still owns all envelope-chain interpretation. Its diagnostics now
store a page-and-island comparison: model-attributed OCR literal IDs, literal
candidates on that page not attributed to the island, and the model's own
horizontal/vertical chains. Acceptance: HSL returns to the V4.45 OCR timing
range and island recall, while the audit exposes OCR and Registry dimensions
side by side before any graph or package change.

V4.48 is the approved native-PDF-text evidence experiment. It preserves the
single Mistral OCR pass, the V4.47 text-only annotation, temperature-zero
Registry, Visual Group discovery and dimensions-only graph scope. While Mistral
OCR reads rendered pages, runtime extracts authored PDF text spans with their
rendered-page coordinates. Deterministic code merges both literal sources into
one ordered OCR evidence package without resolving conflicts, inferring
geometry, creating object boundaries or changing the graph. Every text span
retains `native_pdf_text` or `mistral_ocr` provenance. Detection receives both
conflicting values and must visually resolve them. Scanned or raster-only PDFs
remain supported because an absent native layer is non-fatal. Acceptance: HSL
page 3 exposes the second elevation's `63, 61, 46, 47, 77, 64, 358` native
spans with page-pixel coordinates alongside the existing Mistral output, then
run the existing HSL Detection benchmark before changing any graph rule.

PENDING, P1, USER REQUEST, Detection island-view typology: after the current
outer-dimension extraction experiment is verified, add a separate, evidence-only
classification for common fabrication depictions. An elevation, front, end or
section view should expose width plus height; a plan/top view should expose
width plus depth. This is not permission to infer a missing measurement or a
commercial-object boundary. Define the types and their observable criteria,
then validate them independently against HSL, Page 23 and Adda before allowing
them to affect equality or later object assembly.

PENDING, P1, USER REQUEST, Detection Registry output and latency optimisation:
after the commercial-boundary experiment reaches a valid HSL graph, remove only
proven duplicated model output while preserving all inspectable typed facts and
the complete Estimation Evidence handoff. Prioritise code-derived explanations
from proof facts, deterministic page coverage from accepted groups and context
links, and compact typed classification bases. Do not shorten visual-island
descriptions or proof observations merely to reduce tokens. Measure input and
output tokens, first-token and total generation time, price and HSL/Page 23/Adda
regression behaviour before accepting it. Output reduction is a latency goal as
well as a cost goal; it must not add a model call or weaken validation.


PENDING, P1, USER OBSERVATION, stale Processing cycle after New Estimate:
investigate the authenticated-browser sequence in which a prior saved estimate
is still visible, the user starts New Estimate, and Processing remains on an
old cycle until refresh. Do not attribute this to OCR or Detection without
evidence. Reproduce against the deployed version and distinguish a stale
browser/session or route state from a genuinely active processing run. The
acceptance condition is that an old estimate cannot be presented as the active
new cycle, and a failed or abandoned cycle gives an explicit recoverable state.

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
and Supplier Operations: establish one bilingual, structured normalisation contract
for Price Source, company catalog, Israel Price List, Detection and Supplier
Operations. Canonical display order is entity, primary attribute, brand, then ordered
secondary attributes. Supplier SKU remains supplier-scoped evidence only. The
work includes Hebrew/English aliases, OCR-tolerant variants, department-scoped
brand aliases and a Supplier Operation route to reference operation plus supplier
operation offer, never a material offer. It must preserve the frozen 3.16.7
supplier, VAT, source lifecycle and UI paths. Contract:
`notes/MATERIAL_TAXONOMY_3_17_1.md`.
Owner accepted the five production departments (Wood, Metal, Glass & Plastics,
Stone, Coating), distinct entity roles, and multi-department affinity for
Hardware and Consumables. 3.17.1.3 is active: complete the Material Family
Matrix, including primary and secondary attributes, family-scoped brands, and
eligible operations. Thickness and other identity attributes do not alter
operation eligibility; no operation is mandatory. Contract:
`notes/MATERIAL_FAMILY_MATRIX_3_17_1.md`.
Owner accepted the Company Price Catalog structure on 2026-10-11: its six
top-level sections are Wood, Metal, Glass & Plastics, Stone, Coating and
Hardware. Hardware is a catalog section, not a production department, and no
longer maps to Wood. Keep Consumables excluded from company-catalog persistence
and preliminary-estimate selection. Rename the existing Material Jobs UI to
Supplier Operations.
Material Family Matrix and staged Operation Dictionary accepted by owner on
2026-10-10. The next gate is source-backed time priors and formula parameters
by recipe, beginning with panel-saw and CNC-router sessions. Shared setup and
cleanup apply only within one compatible route and machine session, never
across different machines. Contract:
`notes/OPERATION_DICTIONARY_3_17_1.md`.
Existing Labor evidence has been recovered for this gate: source audit,
baseline, Furniture Core recipes/formulas and route catalog. It must be
reclassified before use because the current engine has 53 flat v0 baselines,
while the broader library mixes source-backed, equipment-bound and derived
priors.
Owner accepted the deliberately incomplete Operation Dictionary v1 on
2026-10-10. Missing operations remain a controlled gap list for a later
versioned expansion. They must not be folded into a similar operation or given
an invented time value.
Owner confirmed the approved new semantics for Hardware, Consumables and
Packaging on 2026-10-10. They will be rebuilt as entity roles in the new
canonical catalog model: Hardware and Consumables have one or more
production-department affinities for retrieval/context only; Packaging has no
production department. The owner also authorised a direct rebuild rather than
legacy product compatibility because the current catalog is transitional and
unused. Internal readers still require complete replacement and verification.
Architecture checkpoint:
`notes/CATALOG_ARCHITECTURE_MIGRATION_3_17_1.md`.
Terminology accepted on 2026-10-10: `Material Resolver` resolves canonical
material identity, `Material Engine` calculates purchasable quantities, `Labor
Resolver` resolves selected operations to route/recipe/machinery session, and
`Labor Engine` calculates staged labor. Sheet-material quantity is nesting and
whole-purchase-unit rounding at project scope, not a generic waste percentage;
V1 does not credit offcuts across projects. Material identity, material supply,
Price Source and labor review states remain separate.
P0, USER REQUEST, 3.17.1 catalog-gap provisional estimate and Staff review
inbox: every review state must still produce an explicitly provisional estimate
rather than block calculation. A bounded research pass may propose a material,
source price, operation or route with provenance, confidence and assumptions.
It is stored only inside that estimate, never as a candidate or provisional
catalog row. Each gap creates a deduplicated internal review job carrying the
source evidence, case-local assumption, calculation trace, gap type and
reoccurrence count. A staff reviewer later creates the authoritative catalog
record separately, if justified. Build the data contract, job lifecycle and
Staff Admin review interface after owner approval of the fallback policy.
Implementation started on 2026-10-11 from checkpoint
`notes/CATALOG_REBUILD_CHECKPOINT_3_17_1_2026_10_11.md`. Increment 1 adds
only the catalog-V2, case-local-assumption and Catalog-Gap-Job contracts in
`db/sql/2026_10_11_catalog_v2_contract_foundation.sql`; it does not apply the
migration, switch readers, write research into canonical catalog rows or expose
the Staff Admin Inbox. Contract: `notes/PROVISIONAL_ESTIMATE_CONTRACT_3_17_1.md`.

Decision correction, 2026-10-13, Material defaults versus assumptions: a
Family Default is not an assumption and never alters OCR evidence. It may fill
only a missing Pricing Key fact after the material family itself is proven,
then continues through the normal Company-first, Israel-second Resolver path.
Its trace records each policy-applied value. A missing family is not eligible
for a Family Default. A deterministic construction rule may make a
case-local `material_family_assumption` from object type and part role, for
example a kitchen-cabinet carcass to melamine-faced particleboard; it remains
review-visible because the input did not prove that family, but it is not a
Catalog Gap. A complete uncommon specification with no Company or Israel
candidate is the separate `catalog_gap_assumption` path and creates the
deduplicated Catalog Gap Ticket. Initial Family Default values require an
owner-approved, versioned baseline matrix rather than implicit selection from
whatever prices happen to exist.

Implementation increment, 2026-10-13, 3.17.4.1: `reference_material_family_default_variants`
stores ordered default variants anchored to an active Israel pricing identity.
The V3 Material Engine applies a variant only to a proven family with missing
facts, verifies that anchor still has an active material-only Israel price,
and persists the applied values in the Material Plan trace. The initial matrix
contains raw MDF 17 mm and raw plywood 17 mm because each has a live Israel
candidate. LDSP 15/17 cannot be activated yet: the active Israel Reference has
no corresponding price identity, which is a catalog-enrichment task rather
than a reason to invent an anchor. Missing-family construction assumptions are
not part of this increment.

Reader/UI scope is mandatory, not a later cosmetic pass: migrate Price Source
ingestion and review/list behaviour, Company Catalog, Estimation/Object Detail
and Staff Admin to the same V2 taxonomy contract. Preserve the accepted Price
Source rule that departments/families without an eligible material row are not
rendered. A Stone row appears after it is standardised into an active Company
Price Catalog offer; a future Israel Catalog link or curation signal never
blocks that publication.
The approved Price Source migration sequence and protected behaviour are in
`notes/PRICE_SOURCE_V2_UPDATE_PLAN_3_17_1.md`.
P0, COMPLETED, 3.17.2.1 Global-Market catalog contract and deterministic
migration plan: owner approved the full
international architecture on 2026-10-11. The canonical chain is Global
Catalog -> Market Catalog (Israel first) -> Company Price Catalog. Checkpoint,
production evidence inventory, mapping rules and cutover gates are in
`notes/GLOBAL_MARKET_CATALOG_CHECKPOINT_3_17_2_2026_10_11.md`. This task
reconciled the unapplied V2 contract with that chain and created an executable
deterministic migration plan before any production SQL application, reader
cutover or legacy-data deletion.
P0, COMPLETED, 3.17.2.2 Global family registry seed: created the approved Global
family vocabulary, primary and secondary attribute contracts and possible
operation eligibility only. The seed must not import legacy rows, construct an
Israel listing, write a Company offer or change a reader. `stone_edge_profiling`
remains excluded until its separate operation and Labor baseline are approved.
P0, COMPLETED, 3.17.2.3 Israel-market projection and strict backfill:
only a row with a proven approved family and that family's required primary
attribute may create a Global model and Israel variant. The 2026-10-11
production dry-run permitted and production backfill created 3,793 active
Global-model and Israel-listing records, excluded 247 consumables by policy,
and retained 408 review rows. No missing thickness, diameter or other primary
attribute was invented to improve this coverage.
P0, COMPLETED, 3.17.2.4 Material Resolver V2 identity bridge: the Estimation
publisher now reads active V2 Global models, Israel market listings and their
approved legacy mappings. It enriches only the 3,793 mapped legacy rows with
their V2 identity, while retaining all 4,448 legacy rows in the resolver
index. The 247 policy-excluded and 408 review-required rows therefore remain
available as fallback evidence and cannot make an estimate disappear. Legacy
material IDs remain the temporary price-identity bridge until the pricing
catalog and Company Price Catalog are migrated to V2 links.
P0, COMPLETED, 3.17.2.5 Company Price Catalog V2 forward bridge: a
Price Source row that has already proved its legacy reference-material identity
now projects deterministically to its Israel Market Listing. The projection
preserves staff-reviewed mappings, records bridge evidence, and cannot fail or
invalidate the frozen Price Source identity flow. The current catalog has 29
items but no proven reference-material links, so no historical item was
guessed or backfilled from its name, price or supplier SKU.
P0, COMPLETED, 3.17.2.6 Source Agent taxonomy adapter and Price Source sections:
Source intake now recognises Stone families and emits V2 family/role/production
department evidence for every deterministic taxonomy match. Hardware is a
standalone Company Price Catalog section, never a Wood row. Price Source now
renders the approved six sections, Wood, Metal, Glass & Plastics, Stone,
Coating and Hardware, and Material Jobs is named Supplier Operations. The
adapter is evidence-only: it must not auto-create a Global model, Israel
listing or Company offer when no proven catalog link exists.
Stone design coverage is complete for current kitchen and furniture scope:
natural, engineered, sintered, porcelain/ceramic, solid-surface and terrazzo
families, countertop-like uses, brands, attributes and possible operations are
defined. The subsequent implementation must create the approved
`stone_edge_profiling` operation only together with its route, driver schema
and Labor baseline. It must not be added as an unpriced catalog label.

ACTIVE, P0, USER REQUEST, 3.17.2.7 Hardware brand and Product System registry:
move the 15 curated Hardware manufacturers from the Source Agent-only vocabulary
into the V2 Global registry, with family-scoped brand aliases and a catalogued
Product System layer. Source evidence may recognise an exact system such as
Blum MOVENTO only after the Hardware family is independently established. A
recognised system may supply the known manufacturer; neither it nor any raw
supplier SKU may invent a nominal length, load class or Global model variant.
Seed only manufacturer-published systems, not every SKU or price offer. The
first scope covers drawer slides and systems, lift/flap mechanisms, door
systems, storage systems, connector systems and hinge systems where the brand
publishes a distinct named line. Product variants and supplier-SKU-to-variant
crosswalks remain staff-authoritative later work. In the same pass, audit
Source Agent static registries against V2 and record unmigrated vocabulary;
do not silently treat it as V2 data.

ACTIVE, P0, USER REQUEST, 3.17.2.10 Estimate Ready Material Resolver:
the Material Pricing Key registry is applied for all 54 active Material Family.
Blue and Green are Estimate Ready: both have a complete Pricing Key, required
purchase format, valid active price and estimation unit; Green also has an
Israel canonical link. Yellow lacks a Pricing Key or required purchase format,
and Red lacks family identity. Complete offer-level purchase format, Source
normalisation and Price Source display, then make Blue and Green eligible for
deterministic selection. The future Material Engine selects minimum total
purchasable cost at document scope, not merely the cheapest unit price.
Contract: `notes/MATERIAL_RESOLVER_SELECTION_POLICY_3_17_2_9.md`.
Current stage: broaden the Global family supply-format registry from verified
Israeli and manufacturer catalogues, normalise ft/cm/mm source notation, and
complete a one-sided format only where exactly one active candidate matches.
The owner must apply `2026_10_12_correct_company_offer_formats.sql` before
this stage can be deployed or tested in Price Source.
Implementation state, 2026-10-12: Resolver and the Price Source indicator
now derive Estimate Ready from the active Global Pricing Key policy and the
specific supplier offer's purchase format. Blue and Green are eligible;
Yellow and Red remain excluded. Pending production verification with a fresh
source cycle. Multi-candidate total-purchasable-cost selection remains the
subsequent Material Engine scope.

Implementation update, 2026-10-13: every source route now converges through
the same Family-first deterministic normalization contract after extraction.
Structured XLS/XLSX columns enrich literal source evidence without replacing
the raw supplier description. The contract extracts only the proven Pricing
Key facts for its Family, including profile section/wall, stone type,
coating system and sheet dimensions. The Global pricing-identity generator
now projects only policy-complete existing materials into V2 classes and does
not invent a missing key or price. Its read-only production dry-run found 364
policy-complete classes from 4,515 Global materials, with active source model
prices for 300. The next fresh-source verification intentionally ignores
legacy Company Catalog rows that the owner will delete before re-import.

Production benchmark, 2026-10-13: a clean import of the controlled legacy XLS
now has 37 active material offers: 18 Green, 19 Blue, 0 Yellow and 0 Red.
The immutable input hash, import result, scope boundary and comparison rule
are recorded in
`notes/PRICE_SOURCE_RESOLVER_BENCHMARK_3_17_2_10_2026_10_13.md`. Do not
compare it to the older 43-offer snapshot, which included six pre-existing
catalog offers.

ACTIVE, P0, USER REQUEST, 3.17.3.1 Material Engine deterministic core:
introduce the calculation-local Material Demand and Material Supply Candidate
contracts, then build and test estimate-wide purchase planning. The Engine must
consolidate only Resolver-compatible demands and select the least-cost complete
basket, not a per-unit-price winner. Scope covers rectangular sheet nesting
with explicit kerf, linear-stock packing, piece-package rounding, direct-unit
purchase and demand-to-purchase traceability. It must not alter the Estimation
Agent, live Estimate publisher, Labor Resolver or catalog data in this task.
The subsequent integration task must extend the agent contract with
calculation-local part geometry and connect Engine candidates directly to the
project-level material-plan path.

ACTIVE, P0, USER-APPROVED, 3.17.3.6 Drawer-slide 400 mm last-resort default:
the prior derived-length rule is cancelled. Estimation V3 retains only
evidenced facts. When an otherwise unresolved `hardware_drawer_slide` lacks
an explicit depth, Material Engine deterministically supplies `400 mm`, then
uses the ordinary Company-first, Israel-Reference-second resolver path. The
400-mm value is a runtime last-resort policy, not a source fact or catalog
default variant, and must be persisted in the plan trace. Explicit source
depth always wins.

ACTIVE, P0, USER-APPROVED, 3.17.3.7 Catalog-driven Material pipeline audit:
verify the one shared Family, Pricing Key, alias and purchase-format contract
for every active Family, rather than a hand-picked material fixture. The
read-only audit must expose unsupported V3 Pricing-Key fields, Price Source or
Estimation alias gaps, and Israel Reference positions that cannot become
Resolver candidates. It must not create a new material model, write Catalog
data, select a price, or treat catalog gaps as assumptions.

ACTIVE, P0, USER-APPROVED, 3.17.3.8 Resolver eligibility closure: close the
catalog-driven audit gaps Family by Family. Owner-approved first rule: every
active `acrylic_pmma` Israel listing receives the `2400 x 1220 mm` catalog
default purchase format. `packaging_material`, `paint_lacquer_stain`,
`powder_coating`, `primer`, and `filler_hardener_thinner` are deterministic
formula-overhead scope, not Resolver Material Demands. Do not silently remove
their cost from runtime before formula rows are connected.

ACTIVE, P0, USER REQUEST, 3.17.3.2 Calculation-local part geometry and
shadow planning: extend the compact Estimation facts transport with rectangular
parts linked to material requirements, full geometry, quantity and rotation
permission. These parts remain inside one estimate and never become Global
catalog entities. Version the page Facts Agent to invalidate its own stale
cache. Feed the new Material Engine as a document-wide read-only plan until
project-level material-plan persistence and rendering are connected.

Implementation stage, 2026-10-13, 3.17.3.3: Resolver-cleared Company offers
now bridge to physical Material Engine candidates in a non-blocking
document-wide shadow plan. The bridge preserves offer-level purchase format,
converts source prices to ex-VAT physical purchase-unit price, and groups only
the active family Pricing Key. The runtime returns only shadow diagnostics;
the live publisher still owns displayed per-object material lines. Israel
Reference candidate conversion remains before direct project-level material
plan output. Accepted fallback chain: complete Company
basket, otherwise complete Israel Reference basket, otherwise an
estimate-local, review-required assumption. The assumption records why it was
needed and never writes back to either catalog. Catalog V2 already has the
target persistence contract: case-local assumption, deduplicated staff-only
Catalog Gap Ticket and occurrence. Runtime creation, Staff Admin review UI and
authoritative catalog-resolution workflow remain unimplemented follow-up work.
Name accepted: `Assumption Fallback`. It is a separate Estimate-orchestration
service after Material Engine, not an Estimation Agent or Engine subsystem.
Build it after Company and Israel candidate planning is accepted and the
Material Engine produces the project-level material plan; it must consume an
Engine-produced `assumption_required` outcome rather than re-run material
selection itself.

Implementation stage, 2026-10-13, 3.17.3.4: Israel Reference is now in the
same Material Engine candidate bridge. An active IL pricing identity must match
the exact completed Family Pricing Key, have an active material-only ILS price,
and have a compatible physical supply format. Square-metre prices become real
sheet candidates through documented family formats, linear prices become stock
candidates, and discrete prices become package candidates. A price per sheet
is intentionally not copied onto every generic family format. The Engine uses
a complete Company basket first, then a complete Israel basket, otherwise
returns `assumption_required`. This stage does not compare against, or depend
on, any former estimator. Project-level plan persistence, rendering and the
separate Assumption Fallback service remain the next work.

Implementation stage, 2026-10-13, 3.17.3.5: an estimate now persists one
derived, estimate-wide Material Plan and a user may override only the net
material norm for one finished item. The Engine recomputes Company-first and
then Israel-Reference purchase candidates after every norm or object-quantity
change. It performs sheet nesting, stock and package rounding at estimate
scope, persists the complete purchase trace, and allocates the resulting
purchase cost back to Object Detail material rows by physical demand. The
allocated Object Detail material costs sum exactly to the rounded plan cost.
Manual area norms never claim fragmented offcuts as usable geometry. Any
material-input change marks the plan stale, clears all object approvals and
coalesces a full recalculation, including a guaranteed follow-up run when an
edit lands during an active rebuild. Final Approval remains blocked until the
plan is `planned`. Schema was applied through
`2026_10_13_estimate_material_plan_v1.sql`; automated verification covers
sheet, stock, package, manual-norm, allocation and approval-gate paths.
Production acceptance still requires a multi-object estimate to verify that
the visible object costs sum to the read-only estimate-wide purchase plan.
The next Material Engine task is read-only Purchase Plan presentation,
including stock format, purchased quantity, remaining material and allocation
trace. Assumption Fallback remains a separate orchestration task.

ACTIVE, P0, USER REQUEST, 3.17.4.1 Estimation Agent V4.1 material-only cutover:
replace the active Estimation path with bounded, page-accountable V4.1 material
facts over the immutable `estimation_input_v4` dossier,
Material Resolver and estimate-wide Material Engine integration. V3 must not
import, invoke or publish V2. Labor, manufacturing and overhead remain
disabled until their own engines are accepted. Company-first and Israel
Reference candidate selection remain deterministic. When neither supplies a
complete candidate set, V3 records `assumption_required` without inventing a
price. V2 is retained only as isolated legacy history pending an explicit
destructive removal task. Acceptance: active runtime and UI read V3 facts,
publish only material norms, persist the project-level Material Plan, and do
not contain an active V2 dependency.

Checkpoint, 2026-10-15: the active end-to-end path now persists and renders a
partial V3 Material Plan. Resolved allocations publish the exact selected
canonical Company Catalog or Israel Reference name and allocated cost while
the overall plan remains `needs_review`; unresolved lines remain unpriced.
The first live run is not accepted as a correct estimate. It exposed
unsupported inferred MDF parts, a 14.25 m envelope proxy in place of the
explicit 4.130 m track, unsupported Oak/30-mm timber selection, and a
sliding-door requirement incorrectly selecting `Folding door system`.
Continue this same task with evidence-bound facts: prohibit invented part
rectangles, prefer exact measurements, make any proxy explicit and
review-visible, and guard physical subtype compatibility before selection.
The complete evidence and commit checkpoint is
`notes/ESTIMATION_V3_MATERIAL_PIPELINE_CHECKPOINT_2026_10_15.md`.

V4.1 experiment, 2026-11-01: the active runtime now uses the new
`estimation_material_facts_v4_1` extractor. It indexes the persisted V4
evidence locally and forms disjoint Cloud batches of at most six page images;
every page must be declared by its batch response and every claim must cite a
local page or OCR block. Unsupported cut rectangles, envelope proxies and
construction-inferred quantities are removed. Ambiguous repeated material
scope becomes blocking review, not a summed quantity. Focused checks passed
70 pre-replay checks and 18 replay-repair checks passed. The saved 39-page
kitchen input was approved for a controlled Cloud replay but did not persist
facts: a 4,000-token response cap truncated dense specification JSON, and
telemetry initially lost received-response usage on parse failure. V4.1 now
records received usage before parsing, permits a complete fenced JSON object,
uses 8,000 output tokens and separates dense pages at 240 OCR blocks. The
safe replay plan is now 20 calls, with every page still covered once. This is
not live-material acceptance: the owner must choose whether to spend the
20-call budget before another replay. The replay tool reads the immutable
package without OCR or re-upload; its paid persistent mode is explicit. Record:
`notes/ESTIMATION_V4_1_BATCHED_EVIDENCE_EXPERIMENT_2026_11_01.md`.

PENDING OWNER REVIEW, P0, 3.17.4.2 Estimation Agent V4.2 persistence repair:
the first small-file V4.1 live witness reached the provider in one bounded
batch and produced a valid material-facts response, but its immutable result
could not be inserted because the production fact-results constraint still
allowed only V1, V2 and V3 contracts. V4.2 retains V4.1's page-accountable
extractor and Material Engine boundary, uses its own immutable result version,
and extends that constraint additively without modifying prior rows. Acceptance:
deploy V4.2, apply and inspect the production constraint, then replay the
already saved small immutable input and confirm one persisted V4.2 result with
the original one-batch coverage and no labor, manufacturing, overhead or price
fields. Commit `497bcbc` was published to `origin/main` and the production
constraint was applied and read back on 2026-11-01. A renewed owner approval is
required before the separate paid replay. That approval was given and the
small immutable input `ec399eb5-9bc7-4960-b7ec-c2ba72d41c2c` persisted result
`bce97bf4-aa95-431f-b3f2-70758b33889f`: three pages were covered exactly once
in two bounded batches, with three material demands, zero parts and no
pricing, labor, manufacturing or overhead fields. The result remains
`review_required` because two sheet/surface demands have no explicit net
consumption. Await owner quality review of the cited material identities
before marking this release accepted.

PENDING USER DECISION, USER REQUEST, next Estimation task after 3.17.4.2:
complete every material demand to a material cost rather than leaving an
unpriced `needs_review` line. Keep evidence extraction separate from this
deterministic downstream step. The requested authority order is Company Catalog,
then Israel Reference, then a visible Assumption Fallback that also creates a
team review job to add or correct the material source. The design must separately
preserve catalog/price authority from consumption basis, so an Israel-selected
material with an assumed net norm is not falsely shown as fully sourced.
The V4.2 small-file witness establishes the immediate prerequisite: its page 2
contains visual geometry, but the V4.2 facts contract persists no structured
dimensions and deliberately emits zero parts. The next task must therefore add
bounded BOM geometry extraction or deterministic construction recipes before
attempting any material-quantity or cost completion.

ACTIVE, P0, USER APPROVED, 3.17.4.3 Object-to-Estimate and approximate BOM
foundation: build the material-only Estimation cycle for sketches, architect
drawings and production documents without restoring external dimensions to the
Detection public contract. Object-to-Estimate reads immutable evidence and may
produce cited geometry or explicitly declared construction assumptions. A
deterministic BOM Composer converts that brief into visible facade, internal
carcass, backing, finish and hardware demands for the whole project; the
existing estimate-wide Material Engine then nests and rounds common materials
across all objects. It must estimate rather than fabricate a precision shop
cut-list: standard thicknesses and construction recipes are permitted, hidden
micron-level gaps are not required. Automatic QA precedes the result; manual
edits are a feedback loop that invalidates only the dependent BOM, purchasing
and QA stages. C/I/A is the sole material price authority. Every demand must
carry a cost: `A` is an immediate estimate-local Assumption Price, not an
unpriced error, and may range from cited Israel price through Global projection
to a documented estimator allowance. It must persist amount, currency, unit,
confidence and reasoning, and keep low-confidence results visible as
assumptions, never review-required.
The future Price Research tool improves an A record and captures sources,
units, purchase formats and a versioned Israel projection. Confidence and
assumption rationale are explanatory only, never a result gate, user approval
request or correction requirement. Every A also silently opens or updates the
existing deduplicated Catalog Gap Job. Acceptance for this increment: no
Detection regression, cited versus assumed geometry is explicit, no model
price/catalog choice, no invented precision parts, every material demand has
C, I or priced A, and a real wardrobe/cabinet package reaches an automatic
approximate BOM and material-cost result.

Implementation update, 2026-11-02: local code now writes separate immutable
`estimation_object_to_estimate_v1` and `estimation_approximate_bom_v1`
results, then uses the existing project-wide Material Engine. The initial
wardrobe/cabinet recipe covers visible facade, internal carcass, backing and
shelves, preserves named finish/hardware demands, and carries shown hardware
piece counts into the estimate-wide plan. The new runtime is not accepted yet:
deploy the additive fact-result constraint, read it back with the pre-existing
Catalog-Gap tables, then run one controlled saved wardrobe/cabinet witness and
inspect all three immutable results, final C/I/A lines, price totals and any
created assumption/job records.

Release numbering correction, 2026-11-02: the published Estimation runtime
increments are retrospectively numbered V4.1 through V4.7 in
`notes/ESTIMATION_V4_RELEASE_SEQUENCE_2026_11_02.md`. The next correction is
V4.8 and every following Estimation deployment must use the next sequential
V4 number in its commit, release note and checkpoint.

V4.8 production repair, 2026-11-02: commit `b9e35c9` makes the completed
Material Engine purchase plan advance the object from 70% to terminal
`materials_costed`, and requirement-scopes every A fallback so incompatible
sheet and direct demands cannot share one candidate. Focused regression checks
passed. The saved wardrobe plan was recalculated without a Cloud call and SQL
readback confirmed a planned five-line C/I/A plan, empty unresolved list,
terminal 100% object state and two synced assumption records. This verifies
completion mechanics, not material-quality acceptance.

ACTIVE, P0, USER APPROVED, 3.17.4.3 V4.9 simplified material recipe: Formica
is ordinary LDSP, paint is only a finish with one standard paint set per
finished object when its consumption is unstated, and every separately shown
handle, hinge, drawer slide or leg remains an independent purchase demand.
Do not create individual rails, connectors, hangers or generic fastening
demands. Acceptance: a new run records these named assumptions, price plan
contains no paint-as-board or compact-laminate Formica line, each shown fitting
is separately costed, and the final project material result is C/I/A priced.

V4.10 production repair, 2026-11-02: commit `d0f1ac2` separates actual
geometry, project-material-plan and terminal states. A technical plan failure
now ends the object with `material_plan_technical_failure` rather than
publishing a permanently running intermediate BOM state. The UI can no longer
animate an initial geometry checkpoint to 70% as if BOM were confirmed.
This does not alter C/I/A: absent catalog coverage remains an immediate priced
Assumption Fallback, while a database or storage outage remains visible as a
technical failure. Focused runtime, Material Engine and progress tests passed.

V4.11 production repair, 2026-11-02: `Lev_1.pdf` exposed a geometry-agent
unit error, `160/72/265` was emitted as `160000/72000/265000 mm`, which made
the sheet splitter enumerate a building-sized panel. Commit `5874031` records
an explicit `unitless_technical_drawing_centimetre_interpretation` assumption
when two or more cited cabinet axes are implausibly 50,000-500,000 mm, then
normalises those values by 100. Separately, Material Engine bounds one finished
panel to 256 split pieces and returns a diagnosable unresolved plan instead of
unbounded nesting. This is not a general unit detector. It is a bounded guard
for unitless cabinet/wardrobe drawings, pending scenario-resolver work.

Next approved analysis within 3.17.4.3: define the bounded BOM scenario
resolver from immutable evidence. It must select a simple construction recipe
only when its defining source facts are present, otherwise emit cited geometry
plus explicit assumptions. Do not introduce a generic shop-drawing engine or
change Detection object identity/boundaries.

V4.12 implementation, 2026-11-02: the owner approved replacement
of the V4.11 `object_kind -> wardrobe/cabinet recipe` path. The new active
pipeline is fixed Detection object identity -> immutable source pages/OCR ->
TU Wien-inspired Geometry and Dimension Graph -> assembly-first construction
interpretation -> structural BOM -> project-wide Material Engine -> C/I/A
material cost. The graph stores source numeric OCR nodes, bounded native PDF
straight-line candidates, Detection-owned view regions and only candidate
relations. It does not infer an axis, a completed drawing or construction.
Large inputs use bounded visual page batches followed by a text-only cited
reconciliation pass, so all pages are observed without one giant vision call.
The assembly contract prohibits object renaming, product-type classification,
generic wardrobe defaults, price/labor/manufacturing/overhead output and fake
cut-parts. Material Engine now rejects an oversized finished panel instead of
splitting it; where no C/I sheet is physically compatible it creates a
dimension-compatible, immediately priced A fallback with an explicit reason.
This is an approximate universal construction interpreter, not a precision
shop-drawing engine. Pending acceptance: apply the additive V4.12 fact-result
constraint, deploy, inspect SQL, then run an owner-approved controlled object
and audit graph, assembly BOM, C/I/A plan and terminal progress. No paid cloud
replay is authorised by this implementation approval alone.

V4.13 pending deployment, 2026-11-02: the first controlled assembly response
preserved source values such as `160`, `265` and `115` but did not name their
unit, and omitted board thicknesses. The V4.13 contract now requires each
part's cited `length_value`/`width_value`, `dimension_unit` and basis; it
deterministically converts explicit `mm`/`cm`/`m` to internal millimetres and
records a named document-convention assumption when a drawing is unitless.
Board parts also require an explicit or construction-assumed `thickness_mm`.
This is a contract correction, not a product classifier or a new fact-result
version. Pending acceptance remains the V4.12 additive SQL constraint, V4.13
deploy, SQL readback, and an owner-approved controlled run that reaches a
terminal C/I/A-priced material result.

V4.14 implementation, 2026-11-02, commit `b5bdf53`: the previous visual
stage was responsible for every finished panel, dimension axis, material
thickness and fitting geometry. A single omitted thickness rejected the whole
BOM. The new active structural contract keeps fixed Detection identity and
immutable evidence, but asks the visual stage only for a document-unit context,
large physical assembly topology, source dimensions, shown counts and material
roles. The deterministic Structural BOM Composer then creates conventional
carcass panels, backs, shelves, drawer faces and boxes, table/countertop layers
and separately counted slides or legs. It carries source dimensions into mm,
records defaults such as board thickness as construction assumptions, never
splits a finished part to fit a purchasable sheet, and leaves whole-project
nesting to Material Engine. A failed structural result now terminates at 100%
without persisting an empty `needs_review` material plan. Assumption text was
removed from the material row: allocation stores `C`, `I` or `A` provenance and
Object Detail renders only that compact marker beside unit price. Focused
structural, Material Engine, runtime and Object Detail tests: 75 passed.
The broader Estimation test selection had 68 passed and three pre-existing
Evidence Handoff failures about preview/OCR fixture expectations, outside this
runtime path. Pending: deploy V4.14, perform SQL read-only audit after a real
LF1 run, and inspect source dimensions, derived part list, sheet allocations,
C/I/A markers and terminal estimate state. No paid replay has been authorised
by this implementation step.

V4.14 live witness rejected, 2026-11-02: run
`run_02f896ef8e8c4c03bfc6b52bba7b09e7`, input
`a8c957e2-d3d8-40c6-b777-749f3dcabd3d`, reached terminal `materials_costed`
but is not an acceptable BOM result. Its immutable OCR contains only unitless
dimensions `20, 43, 75, 72, 19, 90, 145, 4, 158, 160, 265, 187, 160, 115`.
The V4.14 visual response assumed millimetres solely from a `SOLIDWORKS`
watermark, producing a `160 x 265 x 158 mm` box, `115 x 160 mm` facade,
`20 x 72 mm` table and `19 x 90 x 145 mm` shelf stack. This is false for the
known centimetre drawing and proves that a watermark is not a unit authority.
The resulting `0.0198 m²` visible MDF allocation converts the one-sheet
`₪200` A fallback into a misleading `₪10,080.65/m²` Object Detail unit cost.
Separately, the `fibreboard_hardboard|thickness=3` resolver selection rendered
as `Hardboard, 3 mm, Softboard insulation fibreboard`, a physically
incompatible backing choice. Do not accept V4.14 or reuse this result.
Within approved task 3.17.4.3, the next repair must add a bounded unit-scenario
resolver and reject an unsupported global unit before composition; it must
also make Object Detail distinguish purchase price from allocated effective
area price, and disallow insulation-board candidates for structural hardboard
backing. Re-run only after those three failures have focused tests and owner
approval for the next V4 release.

V4.15 document-unit interpretation, 2026-11-02, commits `3e5eb94` and
`cb81dfa`: repair in progress from the rejected V4.14 witness. Unit inference
belongs to the visual stage, which can read the actual dimension lines and the
physical scale of the object as a whole. It declares exactly one document unit:
a cited source unit when printed, otherwise a named convention assumption. The
deterministic composer then only applies that one conversion consistently. It
does not derive units from OCR token frequency, titles, labels or other
non-dimensional document metadata. This fixes scale only, not V4.14's false
assignment of `20 x 72` as a table. Keep the live witness rejected until the
assembly-semantic and material-compatibility repairs are implemented and
verified.

V4.15 live witness rejected, 2026-11-02: `Lev_1.pdf` run
`run_8b0edca5395747cabcd469a06b1eee88`, input
`ed468ad2-28ea-4b81-b640-9f07979b0a43`, completed terminally but remains
unacceptable. The V4.15 Haiku response again selected `mm`, with the recorded
assumption that the drawing's scale indicated millimetres. It then reduced the
shown 158 cm width, 265 cm height and 160 cm depth to a `158 x 265 x 160 mm`
box. The deterministic composer produced only two 18 mm LDSP sides, two top/
bottom panels and one 3 mm backing; it explicitly omitted the seat/bench,
legs, dividers, drawer fronts and drawer components. Material Engine correctly
priced that false demand as one Israel-reference LDSP sheet (₪211.99) and one
Israel-reference softboard insulation fibreboard sheet (₪50.90), total
₪262.89 ex VAT. No raw visual-model response or chain-of-thought is persisted,
only its typed BOM, assumptions, usage and the immutable evidence input. Do
not treat terminal state, price or C/I marker as Estimation acceptance.

V4.16 Objects terminal-navigation repair, 2026-11-02, commit `1cee460`:
when the background Estimation future becomes terminal, the timed Objects
fragment now clears its poll marker and renders the persisted terminal rows in
place. It does not call app-wide `st.rerun()`, which could re-enter the durable
File Review route while the browser reconciles the Objects screen. Focused
Objects navigation checks passed. The File Review deferred-work route retains
its separate timed fragment and its test now checks that actual route rather
than an obsolete source ordering. Pending production verification: a terminal
estimation must remain on Objects and expose its terminal rows without a File
Review return.

V4.17 implementation, 2026-11-02, commit `72c946f`, within approved task
`3.17.4.3`: (1) `Dimension Scale Gate` reads only immutable OCR dimension
literals in the existing Dimension Graph. An explicit source unit always wins.
For a unitless furniture object with at least three 40-400 readings, it records
an auditable centimetre safety constraint and overrides only a model convention
that would reduce the object to a sub-400 mm micro-object. It uses no embedding
and no additional cloud call. (2) The assembly response now carries a compact
coverage ledger. Every Detection-provided visual region maps to an assembly,
countable secondary item or one bounded non-material exclusion; the structural
composer rejects an unassigned material region rather than silently dropping
it. (3) Material Engine purchase rounding stays estimate-wide, but Object
Detail now displays the actual Project Material Plan in purchasable units and
an object's allocated cost separately. It no longer writes or renders an
effective m²/length unit price derived from a whole-sheet or stock purchase.
`C/I/A` remains the compact source marker. Focused dimension, structural BOM,
Material Engine, runtime, Object Detail and Objects navigation checks passed:
`104 passed`; UI/navigation subset `53 passed`. This code is not production
accepted yet. Required witness: a fresh owner-authorized unitless furniture
run must retain cm scale, cover the visible large assemblies, purchase integer
sheet units and remain on Objects at terminal completion. Do not replay LF1
without explicit owner authorization.

V4.18 implementation, 2026-11-02, commit `eba4fae`, within approved task `3.17.4.3`: coverage
is optional audit metadata, never an eligibility gate for geometry, BOM,
material demand, price or terminal status. The visual request may omit region,
page or batch acknowledgements. The deterministic composer preserves valid
coverage rows and records `coverage_audit` as `complete`, `partial`,
`not_provided` or `not_applicable`; it still composes supported assemblies and
Material Engine prices their demand. A new additive
`rfq_estimation_failure_traces` table records a bounded stage, exception type
and safe message for actual technical failures: dimension graph, evidence
artifact, assembly provider, structural composition, persistence, project
material plan, publisher or allocation. It never stores raw provider response
or chain-of-thought. `failed` therefore means a hard technical failure, not a
missing coverage declaration. Pending: apply the additive SQL migration,
deploy, then obtain one owner-run production witness with a terminal priced
result and query its fact/trace rows. Focused tests pass 12/12. The broader
Estimation selection currently has 123 passes and three pre-existing failing
handoff expectations about evidence artifact/OCR retention, outside V4.18.

V4.19 implementation, 2026-11-02, commit `7bfe531`, within approved task `3.17.4.3`: the new
V4.18 trace from `run_9d213e4cb78c4f2d9d7a9bb9e8aa6954`, input
`e2fc6d97-ebf8-43a1-874b-a363ca598644`, isolated a false hard failure in
structural composition: `document_convention_assumption` redundantly carried
source refs. A source claim and assumption cannot coexist, but refs do not
make a unitless-document assumption unusable. V4.19 discards them only for
that assumption basis, records
`document_unit_assumption_refs_discarded` in immutable BOM `normalizations`,
and continues the calculation. Explicit-source units still require valid
immutable refs. The same input's deterministic Scale Gate requires `cm` from
the unitless furniture readings 265, 187, 160, 158, 145, 115 and 90, so this
normalization cannot reintroduce the rejected mm micro-object path. Focused
structural, trace, runtime, Scale Gate, Material Engine and Object Detail
tests pass 68/68. Pending: deploy and obtain one owner-run V4.19 witness.

V4.20 implementation, 2026-11-02, commit `156f9a1`, within approved task `3.17.4.3`: the
accepted V4.19 witness `run_af762e31361047e4a151415c3e2b7285` exposed a
product-layer regression, not a Material Engine purchase error. Object Detail
rendered its internal allocation representation twice, as `Project Material
Plan` and `Material Cost`, and leaked assembly labels such as `Cabinet
Carcass` and `Cabinet Facade` as material names. V4.20 renders one Materials
table only: material name with leading C/I/A marker, strict net required
material volume, purchasable unit/format, whole project purchase quantity and
total. Whole-stock nesting remains estimate-wide internally. Per-object
structural panels become a closed Elements list rather than a second cost
table. Snapshot data now persists supplier/assumption purchase dimensions for
the displayed format. Assumption names suppress assembly-role words, while the
visual prompt directs the model to select a material description from surface
appearance, including Veneered MDF, Painted MDF, LDSP, solid wood or furniture
legs. Current immutable V4.19 output is not rewritten; its UI becomes
non-generic where the stored family permits. Focused structural, runtime,
Material Engine, Object Detail and Objects checks pass 65/65. Pending: deploy
and obtain a fresh V4.20 witness for the visual material-selection change.

V4.21 implementation, 2026-11-02, commit `0b030ea`, within approved task `3.17.4.3`: an
incomplete or malformed secondary assembly no longer discards usable BOM
demand from other assemblies. The structural composer records a compact
`structural_omissions` item with an identifier and reason code, then proceeds
with valid assemblies and valid discrete fittings. It still fails if no
material demand can be assembled at all. Failure traces preserve a bounded
structural validation code such as `assembly_missing_required_dimensions`,
not a raw model response or exception fragment. Pending: focused tests,
deployment, and one fresh production witness that reaches priced terminal
completion.

V4.22 implementation, 2026-11-02, commit `88cacbe`, within approved task `3.17.4.3`: optional
model count fields no longer reject an otherwise usable assembly merely because
they contain zero. `facades` and `shelves` retain zero as an intentional
absence; `drawers`, `top_layers`, and `legs` revert to their conventional
structural defaults when zero or malformed. Structural traces classify
remaining local dimension, count, unit, material-role and evidence validators
with bounded codes. Pending: focused tests, deployment, and one fresh witness.

V4.23 implementation, 2026-11-02, within approved task `3.17.4.3`: a model
reference outside the immutable evidence package no longer fails the complete
BOM. Invalid source or derived dimension refs downgrade the value to a named
construction assumption; invalid source-material refs downgrade the material
to `construction_assumption`; missing assembly refs use the supplied full-page
artifact. Each transformation is retained in BOM `normalizations`. No invalid
ref is ever persisted as source evidence. Every completed or failed cycle
stage now writes a bounded `agent_usage_events` marker: Dimension Graph,
evidence-artifact load, Assembly Agent, structural composition, BOM
persistence, Material Plan, publisher and allocation. A marker contains only
stage, immutable input ID, outcome, safe reason code and aggregate counts; it
never retains the prompt, raw provider output, chain-of-thought or credentials.
Pending: focused tests, deployment, and one fresh production witness.

V4.24 implementation, 2026-11-02, commit `797dc33`, within approved task `3.17.4.3`: Material
Plan reached persisted V4.23 BOM facts, then failed while serializing a catalog
format because the data correctly carried both physical dimensions and
`format_source` metadata. The purchase-format snapshot now exports only known
numeric physical dimensions (`length_mm`, `width_mm`, `height_mm`,
`thickness_mm`, `diameter_mm`) and retains metadata outside the UI-format
contract. A Material Plan `ValueError` is now recorded as the bounded
`material_plan_validation_failed` code, never its raw exception content.
The fresh production witness is now `run_d82f58af38f84a4eb6fc3a2dbb8faeab`:
`Cabinet` reached `completed / materials_costed / 100%` and persisted the
Material Plan, publisher and allocation stages. It is a technical terminal
cycle checkpoint, not quote acceptance. All three displayed material lines
are `A`, including Veneered MDF 18 mm, LDSP 18 mm and Hardboard 3 mm. The
persisted reasons are `material_pricing_key_incomplete` for Veneered MDF and
`no_physically_compatible_company_or_israel_candidate` for the other two.
Next active repair within `3.17.4.3`: a read-only company-610 Resolver audit,
then an approved correction to the earliest missing Family/Pricing-Key/
physical-compatibility constraint. Full evidence:
`notes/ESTIMATION_V4_24_TERMINAL_CYCLE_CHECKPOINT_2026_11_02.md`.

ACTIVE, P0, USER APPROVED, 3.17.4.4 Estimation V5.1 Cabinet Block and
Hardware Composer, 2026-11-03: move the active approximate-construction
contract from V4.24's incomplete-assembly omission rule to non-blocking Cabinet
Blocks. The immutable Estimation input remains the start of the cycle and
Detection/V4.29 navigation remain protected. A missing envelope axis must
resolve as explicit source, auditable peer-derived value, or named construction
default, never silently disappear or stop cost composition. Default hidden and
visible board thickness is 18 mm where source does not state it. One block has
front topology, exposure and nested hardware: every drawer front creates one
drawer-slide purchase set with `floor((depth_mm - 100) / 100) * 100`; each
hinged facade creates individual hinges using `<=600:2, >600:3, >2000:4`; each
lift-up facade creates one gas-lift purchase set. Visible fronts/exposed ends,
hidden carcass, backing, finish and worktop remain distinct material demands.
The model recognises topology only. Composer derives conventional parts and
hardware. Resolver/Engine alone choose catalog and price. Acceptance: Lev_1
and Lev_2 rule tests pass, a fresh V5.1 BOM is persisted with explicit units
and assumptions, and a controlled cabinet/kitchen witness reaches terminal
C/I/A cost without a Detection or V4.29 navigation regression. Contract:
`notes/ESTIMATION_V5_1_CABINET_BLOCK_CONTRACT_2026_11_03.md`.

IMPLEMENTED, pending fresh production witness, V4.27, P0, Profile material allowances: restore three locked formula rows after
the Material Plan allocation. Consumables and Packaging must use the saved Pricing Cost
percentages against primary material cost. Paint consumables must use the saved percentage
against coating material cost only. They are formula allowances, not catalog products, so
they must not be editable, resolved through C/I/A, or become purchase units. Acceptance:
a new production Estimation run persists all three rows, updates the object self cost, and
shows the exact saved Profile percentages. The separate assembly-loss instability remains
the next task after this witness.

Detection readiness update, 2026-11-01: V8.4.5 has an owner-verified positive
large multi-page assembly witness, `24-215. Кухня. СБ.pdf`, now compiled to one
commercial object. The existing immutable `estimation_input_v4` carries its
locked identity and quantity, physical evidence-page references and regions,
cited OCR, private full-page artifacts, original-file reference and OCR-event
identity. This is sufficient to begin the next Estimation-agent contract, not
to declare a correct full estimate. First inspect the successful kitchen
handoff read-only, then keep evidence-bound extraction, deterministic Material
Engine selection, labor routes and pricing as separate authorities.

Israel Reference rebuild, points 1-2, 2026-10-14: the earlier Coverage Audit
incorrectly treated the legacy `reference_material_pricing_identities` bridge
as the Israel catalog. It is superseded. `tools/audit_israel_reference_catalog.py`
now reads the actual canonical chain: Family -> Global Model -> Israel Listing
-> Israel Price and Purchase Format. A Company row maps many-to-one to an
Israel Listing by Family and Pricing Key. Secondary fields never create a new
price class. The corrected snapshot has 54 active families: 18 lack a
canonical model, 19 have a canonical priced position but no purchase format,
six hardware families have no active package price, and five contain models
without their required Pricing Key. It also exposed incorrect backfill data,
including Plywood-named rows assigned to the MDF family. Do not seed further
defaults or prices until the owner and team have reviewed the catalog-layer
contract and the bad family assignments. Hardware package selection remains a
separate deterministic Company-first, Israel-second branch.

ACTIVE, owner-approved, 2026-10-14, Israel Reference normalization: convert
the actual Israel catalog chain into usable resolver data. Every active
listing must have one Family, a complete Pricing Key, an active Israel price
row and, where its Family requires it, an approved purchase format. Every
Family must have one active default listing only when that listing already
has an active Israel price. Do not fabricate a source price. The first
migration is `db/sql/2026_10_14_normalize_israel_reference_foundation.sql`:
it removes wall thickness from furniture-profile Pricing Keys, corrects the
three Plywood rows wrongly placed in MDF, and separates explicit hardware
names from the generic furniture-system Family while preserving their legacy
source and price anchors. The next migration must cover remaining broad
Family splits, default listings and supply formats, followed by the existing
read-only catalog audit.

Material-fact boundary correction, 2026-10-13: V3 must establish only
material family, proven Pricing Key facts and evidenced part geometry. It must
not guess a unit or a purchasable format. A directly evidenced discrete count
may remain in facts, but is not a purchase quantity. The Resolver
selects a compatible Company or Israel candidate first. The Material Engine
then derives the Object Detail net norm from candidate form plus allocations:
sheet allocations render as square metres, linear stock as metres and discrete
stock as pieces. A material with no evidenced usable geometry may remain
identified, but remains review-required and unpriced instead of receiving a
fictional `1 piece` demand. The V3 facts-agent cache version is bumped so the
old guessed-unit facts cannot enter a new plan. Pending production acceptance:
rerun the same three-object document and verify that a resolved part-backed
material receives a deterministic unit and norm, while an unresolved profile
does not receive a cost or unlock approval.

Pricing Key extraction correction, 2026-10-13: V3 now receives the required
evidence-field names from the active Pricing Key registry for every allowed
Resolver family. It searches source evidence for those facts, but Resolver
remains the only authority that decides whether they form a completed key.
This allows the prompt to actively seek, for example, MDF thickness and tube
metal, section and wall thickness without turning absent evidence into a
model-generated specification. Cache version `estimation_material_facts_v3_2`
separates these facts from prior runs.

Multilingual intake grammar correction, 2026-10-14: each active Global
Catalog family has an explicit English, Russian and Hebrew alias set, and each
Pricing Key fact has the corresponding field labels. V3 receives only the
aliases and fact labels relevant to its currently allowed Resolver families.
They guide family and attribute recognition, but cannot prove a missing number,
select a purchasable offer or create a catalog link. Exact aliases are unique
across families. The standalone source-taxonomy product-system lookup is also
kept on the same canonical Global-family projection, so Hardware rows cannot
fail before taxonomy is established.

COMPLETED, P0, USER ACCEPTED, 3.17.1.4 Shared aliases for incoming material text:
move every Family alias, Pricing Key label/value alias, brand alias and unit
alias out of runtime dictionaries into the catalog. Both Estimation and Price
Source must read the same active rows. An alias may establish only a Family,
Pricing Key fact, brand or unit. It never selects a price, purchase format,
Company Catalog offer or Israel Reference Position. Exact aliases for a known
Israel Reference Position remain a separate later mapping, after Family and
Pricing Key are proven. Initial implementation adds the protected tables and
the seed from the former Estimation registry in
`db/sql/2026_10_14_shared_material_aliases.sql` and
`db/sql/2026_10_14_shared_material_aliases_seed.sql`, plus the existing
non-Hardware Price Source brand inventory in
`db/sql/2026_10_14_shared_brand_aliases_seed.sql`. Estimation V3 now reads
only the new persistent rows. Price Source reads the same persistent rows for
Family, Pricing Key, brand and unit interpretation. No local synonym fallback
is permitted after cutover.

Accepted 2026-10-14: live catalog audit confirms 54 multilingual Families,
845 Family aliases, 411 Pricing Key labels, 268 Pricing Key value aliases,
162 unit aliases, 264 brand aliases and 379 product-system aliases. Every
live Family has EN/HE/RU coverage; every multi-Family spelling is explicitly
ambiguous, with no unapproved collision. Estimation V3 and Price Source both
read this shared catalog. Deployment and a production end-to-end check remain
a separate release checkpoint, not unfinished alias-catalog work.

Furniture metal-profile policy correction, 2026-10-13: wall thickness is not
a Pricing Key fact for `metal_tube` or `metal_profile_angle_channel`. An
unstated furniture-profile wall uses the manufacturing default of 1.5 mm;
an explicit wall remains secondary source provenance. `metal_flat_bar` is
deliberately excluded because its thickness is a physical cross-section fact
and can affect price. The corrective SQL is
`2026_10_13_furniture_profile_wall_thickness_default.sql`. MDF 20 mm and
perforated steel sheet 5 mm are confirmed catalog gaps, not extraction gaps:
each still needs an authoritative active price and supply format before the
Resolver can yield a candidate.

Resolver correction, 2026-10-13: the first live multi-object Material Plan
proved that Object Facts had been given legacy Israel price classes rather
than the Resolver's purchasable-family vocabulary. That allowed an unsupported
fact such as `stainless_steel` to replace the proven form `metal tube`, so no
Pricing Key was built and neither Company nor Israel candidates were queried.
Facts now receive only active Family Pricing Policy vocabulary, accept
`metal_type` only as an explicit specification, and forbid invented alloy,
wall or grade facts. Global family codes without a source alias are valid
Resolver families. A 20 mm MDF requirement correctly remains a Catalog Gap
until an authoritative Company or Israel offer is added: current Company data
contains 18/19 mm only and current Israel Reference has no 20 mm MDF price.

V2 Family bridge removal, 2026-10-14: active taxonomy, Resolver, Material
Engine, V3 facts and Israel identity seeding use only current `family_code`
values. The former source-label projection, including mappings such as
`drawer slide` to `hardware_drawer_slide`, is removed rather than renamed.
The remaining test migration must replace old source-label expectations with
current Family codes; no product fallback may be restored to satisfy them.
Historical records with an old stored Family spelling require a one-time data
audit before their next Resolver run. Faced MDF 20 mm remains an explicit Catalog Gap and

Release audit update, 2026-10-14: the live catalog has 54 active Families,
845 Family aliases, 411 Pricing Key labels, 268 Pricing Key value aliases,
162 unit aliases, 264 brand aliases and 379 product-system aliases. Every
active Family has English, Hebrew and Russian coverage. The audit found 16
additional multi-Family spellings; the follow-up seed records each as
ambiguous with explicit candidate Families, so none is resolved by ordering.
incomplete facts remain review-required. A plan with any earlier Resolver gap
is always `needs_review`, even when other requirements already have concrete
purchase lines. Those partial lines remain traceable diagnostics but can never
unlock Final Approval.

Lighting-material request, 2026-10-14: lighting is not one generic Hardware
line. The catalog and Resolver need distinct purchasable families for LED
strip, aluminium LED profile with diffuser, LED power supply and lighting
connector/cable. Candidate Default Matrix baseline: an 8 W/m strip sold in
5 m coils and a 2 m profile with diffuser. Material Engine must group matching
lighting runs across the entire Estimate, round strip to 5 m coils and profile
to 2 m lengths, then derive compatible power-supply capacity from total
installed strip length and strip W/m. The configured power headroom, default
colour temperature and default profile form remain pending owner approval. A
user-specified voltage, colour temperature, strip power, profile form or
power-supply capacity always overrides the default and is retained as source
evidence.

DEFERRED, P1, USER REQUEST, Aluminium/PVC glazing and enclosure pilot:
prepare a separate catalog and Resolver program for the prospective aluminium
and glazing company pilot. Scope: aluminium square, rectangular and glazing
system profiles; thermal-break variants; glazing beads and gaskets; glass-unit
types; aluminium/PVC hybrid profiles; fasteners and accessories; supplier
lengths and compatible cut/waste rules. These are not generic furniture-metal
families. Their family taxonomy, Pricing Keys, aliases, default variants and
Material Engine purchase rules must be designed from the pilot supplier
catalogue and real glazing estimates. Do not make square or rectangular
aluminium glazing profiles a substitute for the existing carbon-steel square
and rectangular furniture profiles.

ACTIVE, P0, USER REQUEST, 3.17.2.11 Universal canonical material-name
contract: at source-row processing time, build every company-catalog display
name solely as `Entity -> one or two proven key attributes -> confirmed brand
when present -> ordered secondary attributes`. Raw supplier prose, SKU,
quantity, packaging wording and a candidate or uncertain brand must never
enter the canonical name. A physical offer format is a key attribute when
proven, rendered as a full `length x width mm` format or as its one proven
side only when completion is ambiguous. The same renderer must project
existing catalog offers without mutating immutable source evidence. Every
processed-material projection, including Catalog, Needs Review, Source Detail,
and later Object Detail material lines, must call this same renderer. The
second display line is literal `raw_description` evidence in the source script,
never a translation or model-normalized phrase. Acceptance:
the two latest plywood sources display their `3100 mm` distinction at once,
the fallback sheet format is visible where resolved, and unconfirmed brands do
not appear in any new canonical name. Add a deterministic multilingual
measurement-alias grammar before name rendering: thickness, length, width,
depth and diameter labels; metric, imperial and Hebrew units; sheet-format
labels; and source-safe separators. A bare number is accepted only in a
proven entity-adjacent or explicitly labelled measurement position, never as
SKU, quantity or packaging notation.

PENDING, P1, USER REQUEST, 3.17.2.12 Price Source upload resilience:
accept legacy XLS through a production-supported parser, while preserving XLSX,
CSV, PDF and image handling. Before that format support is released, an invalid
extension must be rejected at selection time and must keep Extract disabled;
server validation remains the backstop. Add a genuine Cancel extraction action:
it must signal the active worker, close the live provider stream, prevent any
post-cancel persistence and show a terminal Cancelled state. Do not implement a
cosmetic button that merely detaches the browser while work continues. Large
structured spreadsheets must be partitioned into bounded deterministic row
groups or otherwise avoid a single unbounded Claude response, rather than
raising the 60-second stream cap and making the owner wait longer. Acceptance:
the supplied legacy XLS and its XLSX equivalent both parse, a 44-row workbook
is split before model extraction, invalid files cannot start a cycle, and
Cancel reaches a terminal state without catalog/source persistence. Automated
verification passed in commit 40f4739; the 44-row XLSX production import and
resolver-status checkpoint are recorded in
`notes/PRICE_SOURCE_XLS_RESILIENCE_CHECKPOINT_3_17_2_12_2026_10_12.md`.
Production acceptance still requires one XLS import and one Cancel during
extraction.

Production correction, 2026-10-13: the XLS parser and uploader were already
released, but the existing private `company-price-sources` Storage bucket
still allowed XLSX only. Apply
`db/sql/2026_10_13_company_price_sources_legacy_xls.sql` before the legacy
XLS acceptance run. It preserves every enabled MIME type and adds only
`application/vnd.ms-excel`.

DEFERRED, P1, USER REQUEST, 3.17.2.8 Construction Scenario Library and Staff
Admin: define a controlled, versioned library of full estimating archetypes,
starting with kitchen modules and furniture. A scenario describes the complete
base composition, evidence-triggered branches such as doors, drawers, shelves,
lighting and significant hardware, material and labor requirements, plus a
low-impact allowance for cheap construction sundries. It is not a universal
furniture ontology and must never silently invent a supplier SKU, a price, a
labor route or a catalog record. The earlier narrow draft focused on legs and
wall suspension, and is explicitly superseded, see
`notes/CONSTRUCTION_PATTERN_LIBRARY_3_17_2_8.md`.

Create a staff-only Admin interface to list active and inactive patterns, read
their human-readable contract and machine rules, edit a draft, activate a
version, deactivate a version, and view where a version was used in estimates.
Every edit and activation requires an immutable version and audit history. The
interface must not expose source evidence to non-staff users and must not allow
an edited rule to rewrite a completed estimate. Dependency: approve the V2
data contract and deterministic Estimation use path before UI implementation.

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

COMPLETED, P0, 3.19.1 Contacts validation and normalization, owner accepted
10.10, commits `221d448`, `4709579`:
keep Street, House Number and City unchanged. Empty Contact fields remain
permitted. A non-empty Official email must match the existing shared email
syntax rule. Phone accepts an Israeli local number beginning with `0`, or an
international `+972` form, stores canonical E.164, and displays conventional
Israeli spacing. Website, Facebook, LinkedIn and Instagram silently remove an
entered `http://` or `https://`; Website must be a syntactically valid hostname,
while each social field must use its matching service hostname and a non-empty
profile path. A pasted `www.` is removed too, while placeholders retain their
example URLs. Postal code accepts exactly seven digits and strips non-digits at
input time. Email and every URL field strip non-ASCII characters at input time;
the server rejects any bypassed non-Latin value. There are no external network
lookups. Invalid fields receive only the existing Auth-red border and
the save is blocked, with no validation-copy block or extra Streamlit rerun per
edit. The implementation must retain values, clear a red state immediately
after correction, validate all submitted fields together, and reject a bypassed
client request on the server. Acceptance requires the authenticated production
matrix for empty fields, malformed and corrected values, pasted protocol URLs,
local and `+972` phone input, successful persistence/reload, and no regression
to Contacts Logo Save, the Profile rail, protected Price Lists or cold-load
behavior.

COMPLETED, P0, 3.20.1 Bank Details validation and normalization, owner accepted
10.10, commit `fcf0c78`:
Company registration number is exactly nine digits, retaining leading zeros.
Bank, branch and account numbers accept digits only, retaining leading zeros
without invented length limits. Bank and legal names remain free text. BIC is
uppercase Latin letters/digits in its standard eight- or eleven-character
format. IBAN removes spaces, converts letters to uppercase during typing and
paste, and must pass the international IBAN structure and MOD-97 checksum.
Invalid values use the existing Auth-red field border only and block Save,
without validation copy, external bank requests or per-edit Streamlit reruns.
Owner verified authenticated production coverage of paste, correction,
normalization, blocked invalid Save, saved reload and retained Profile behavior.

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

PARTIALLY ACCEPTED, P0, 3.18.4 Profile Overhead and Pricing Cost editable-policy inputs:
make Monthly Cost and Total reciprocal whole-shekel inputs, with Arnona VAT exempt,
and add a visible Total monthly overhead expenses sum. The owner rejected the
last compact-Pricing spacing revision, but selected the preceding compact Pricing
surface: grouped Delivery / Installation, Consumables / Paint consumables,
Packaging, then policy fields with explanatory `?`. Numeric and percentage
inputs now follow the product-wide end-caret design-system contract. Preserve
canonical net-overhead persistence, owner-only
authorization, a single save boundary, and the accepted Price Lists, its fragments,
polling, upload, Source, Review and catalog loading behavior. Acceptance requires
authenticated production edits in both directions, Arnona invariance, correct total
sum, Pricing zero-clear/percent format behavior, aligned compact input columns,
hard-reload restoration of the selected Profile tab, save/reload persistence, and
no Price Lists regression. A cold restored session must render its complete
authorized header controls, including Admin when platform access exists. Owner
accepted the cold-reload speed checkpoint on 10.10: post-candidate visible
completion median was approximately 0.86 s versus approximately 1.08 s in the
preceding comparable sample. The Profile-tab durable-route defect is explicitly
deferred: Pricing Cost can still reload as Overhead Expenses. Do not add another
route experiment without a fresh authenticated reproduction and DOM/message-path
evidence.

ACTIVE, P0, 3.18.5 authenticated-session legal gate boundary, owner approved
10.10: Terms, Privacy, releases, documents and acceptance history are checked
only by the fresh successful password Sign in flow. Any already-authenticated
session resume, hard refresh, Fast Resume, browser-storage restoration, tab
selection, tool action or internal rerun must not read any legal source. A
failed fresh Sign in legal read remains a visible fail-safe error, never a
resume bypass. Membership and authentication checks remain mandatory. Verify in
authenticated production trace that resume contains `server.legal_terms_gate_resume_skip`
and no `server.legal_terms_gate_lookup`, then compare the cold timing with the
11:51 UTC baseline that spent 1.88 s in the legal lookup.

COMPLETED AND OWNER-ACCEPTED, P0, 3.18.6 shared authenticated header controls
in document flow, 10.10: Profile, File Review, Objects and Object Detail now
render the one existing authenticated action component beside their own title,
not as a root-level fixed rail. The controls leave the viewport together with
the screen title during document scrolling. Production implementation:
`b5bce72`; checkpoint: `notes/SHARED_HEADER_CONTROLS_CHECKPOINT_3_18_6_2026_10_10.md`.
The owner confirmed the previously persistent scrolling defect is resolved.
Preserved: action callbacks, authorized visibility, Upload placement,
transition readiness, scroll-to-top behavior, and the Price Lists contract.
No DOM mutation, client polling, uploader, callback or Price Lists behavior was
added. The rejected fixed, top-offset and absolute experiments remain reverted.
Visual refinement is not included in this accepted functional checkpoint and
requires a separately approved UI task.

COMPLETED AND OWNER-ACCEPTED, P0, 3.18.7 unified authenticated header geometry,
10.10: production implementation `b8bd3b0`, Object Detail completion
`9bd7339`; checkpoint:
`notes/UNIFIED_HEADER_GEOMETRY_CHECKPOINT_3_18_7_2026_10_10.md`. One shared
document-flow header component anchors the action rail to the title's local
header container rather than Streamlit-generated grid columns. The owner
accepted the resulting geometry across Company Profile, File Review, Objects,
Partners, Admin and Object Detail. Document-flow scrolling, callbacks, Upload
placement, transition readiness and the accepted Price Lists contract remain
protected.

COMPLETED AND OWNER-ACCEPTED, P0, 3.18.8 Object Detail hero-card vertical
spacing, 10.10: production implementation `8c0eb53`; checkpoint:
`notes/OBJECT_DETAIL_HERO_LAYOUT_CHECKPOINT_3_18_8_2026_10_10.md`. The Object
Detail second row now consumes the one native 16px Streamlit gap beneath the
accepted `Object:` header, without adding a duplicate top margin. Preview keeps
a matching 16px bottom clearance before the Cost/VAT/Total row. The owner
accepted the live authenticated result. Preserved: the accepted `Object:` /
navigation-controls axis, shared header component, callbacks, preview source,
totals, table calculations and responsive behavior.

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
  1. Make benchmark run IDs unique so repeated runs cannot overwrite prior object results. RFQ OCR uses the V2 rendered-pages route. Naming is text-only and receives locked Detection facts plus OCR snippets, never the PDF again.
  2. Validate the V2 rendered-pages OCR route on `mistral-ocr-4-1`. Mistral retired `mistral-ocr-4-0` on 2026-09-30, which produced `400 Invalid model` in production. Structured vision annotation remains part of the V2 evidence contract. Record OCR completeness, p50/p95, dimensions, tokens, and total time.
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
