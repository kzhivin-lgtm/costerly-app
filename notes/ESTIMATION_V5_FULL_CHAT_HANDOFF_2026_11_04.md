# Estimation V5 full-chat handoff

Date: 2026-11-04
Purpose: continue Estimation work in a new chat without rediscovering the
product decisions, runtime boundaries, production incidents, or release state.

## 1. Read this first

2026-11-05 continuation: this document remains the historical V5 handoff, not
the current V6 acceptance statement. Continue from
`notes/ESTIMATION_V6_2_HSL_N68_CHECKPOINT_2026_11_05.md` (3.17.4.5).
Current diagnostics select CB Front V2 and Planner V4; r03 remains protected
history. Later Planner V5/V6 candidates are preserved but not promoted after
N68 physical-scope loss. Nine-object HSL results, rotation transport defect,
owner-accepted counts and next proposals are recorded in the new checkpoint.
No production deployment, Detection change or full material-cycle acceptance.

This is an Estimation-only handoff. Detection, Naming, Document Identity and
object boundary quality are inputs and protected dependencies, not work to
change while repairing Estimation unless a read-only audit proves their
contract is wrong.

The owner wants a fast **approximate cost estimate**, not a manufacturing CAD
system or precision production cut list. Missing dimensions and thicknesses
must therefore resolve to an explicit, auditable approximation. They must not
stop the cycle, silently disappear, or be presented as source facts.

Current implementation worktree:

```text
/private/tmp/costerly-estimation-v425
branch: codex/estimation-v425
```

Current published checkpoint:

```text
d86f42f docs(estimation-v5.8.2): record recovery checkpoint
710165d fix(estimation-v5.8.2): recover handoff failures
7405e67 fix(estimation-v5.8.1): resume active estimate
512bf6e release(estimation-v5.8): prepare navigation targets
```

`origin/main` matched `d86f42f` when this handoff was written. The current
worktree still has pre-existing unstaged additions in `notes/TODO.md`. They
describe earlier V4.28/V5.6.6 UI experiments and an Ada Detection regression.
Do not stage, edit, or reinterpret them incidentally while working on
Estimation.

## 2. Product goal and non-negotiable principles

### 2.1 What Costerly is estimating

The input can be a sketch, architect drawing, client layout, SolidWorks export
or a sparse technical PDF. The human estimator can often see a kitchen,
cabinet, partition/bench, tall screen, tabletop, drawer bank or hanging unit
before knowing every panel. The system needs the same ordering:

1. Understand what physical systems are depicted.
2. Lock that understanding as a constrained composition scope.
3. Resolve dimensions against actual drawing evidence.
4. Expand conventional construction and hardware deterministically.
5. Resolve materials and prices outside the visual model.

The desired customer result is an approximate, economically useful cost. It
is not a CNC nesting plan, assembly drawing, production specification or a
claim that every inferred panel is exactly correct.

### 2.2 Approximate construction is mandatory

The owner explicitly rejected a failure mode where incomplete data blocks the
estimate. For every required cabinet axis, resolve in this order:

1. Explicit, cited source dimension.
2. A compatible peer/linked-zone dimension supported by the same immutable
   object evidence.
3. A named construction default.

The result must state whether the value is `source`, `derived`, or an
`assumption`. Peer-derived values retain source references. Defaults have no
false source reference.

Current V5.1 estimating defaults:

| Missing value | Current default | Meaning |
| --- | ---: | --- |
| Cabinet width | 600 mm | Estimation fallback only |
| Cabinet height | 720 mm | Estimation fallback only |
| Cabinet depth | 600 mm | Estimation fallback only |
| Visible MDF/HDF or hidden LDSP thickness | 18 mm | Use explicit source thickness instead when present |
| Backing thickness | 3 mm | Use explicit source thickness instead when present |

The user repeatedly stressed that a human will estimate an unlabelled depth
from the neighbouring labelled depth. For example, if a kitchen has one shown
depth of 650 mm and its adjacent cabinet side has no label but the geometry is
clearly equivalent, use about 650 mm, then apply the deterministic hardware
rounding rule. This is an intentional estimate, not a production promise.

### 2.3 Clear authority boundaries

| Layer | Owns | Must not own |
| --- | --- | --- |
| Detection | Document identity, object identity and quantity, evidence pages/regions, OCR, immutable `estimation_input_v4` | Cabinet BOM, material pricing, changing object boundaries to repair a BOM |
| Dimension Graph | Source numbers, drawing views, vector/OCR candidates, evidence relations | Catalog selection, price, a completed cabinet design |
| Estimation Analyze | Whole-file physical understanding, object scope, zones, operability, front topology and explicit assumptions | Catalog item, price, labour, manufacturing route, arbitrary detail dimensions |
| Estimation Calculation | Object-specific geometry, exposure, material roles, within locked Scope | Inventing/removing zones, changing front topology, secondary hardware choice |
| 2VN resolver | Validates visual axis binding against immutable graph and applies bounded fallbacks | Replacing source evidence with an untraced guess |
| Structural/Hardware Composer | Conventional parts and exact hardware arithmetic | Visual semantic reclassification or catalog selection |
| Resolver and Material Engine | `Company Catalog → Israel Reference → Assumption Fallback`, purchase formats and pricing | Changing detected object, Scope or BOM topology |
| Object Detail UI | Presenting persisted material facts, Elements and cost | Recomputing or silently substituting material facts |

### 2.4 Material vocabulary and pricing rule

Use these terms consistently:

| Term | Meaning |
| --- | --- |
| Company Catalog, `C` | The company-owned normalized material/catalog product |
| Israel Reference, `I` | The normalized Israel reference product |
| Assumption Fallback, `A` | An immediate, explicitly priced estimation fallback |
| Material Demand | Physical demand before resolver selection |

Resolver order is always `C → I → A`. The visual/model layer may propose a
family or role from source context and appearance, but it may not choose a
catalogue product or price. Every demand receives a price. `A` communicates
uncertainty, it is not an approval gate or error state.

Compatible material demand is aggregated estimate-wide before purchase rounding
and bounded offcut. A long finished span must not reject a sheet material
because real production may join material and because drawing dimensions can be
composed spans. V4.25 switched sheet planning to aggregate area with 10%
offcut. Do not restore a one-finished-panel to one-purchase-sheet fit gate.

## 3. Current calculation cycle, precisely

The user calls the two model phases `Estimation Analyze` and `Calculation`.
That is now the correct mental model. Current runtime is not one opaque prompt.

```text
Detection immutable input
  -> Estimation handoff and immutable evidence artifacts
  -> per-object Dimension Graph and evidence-page preparation
  -> one whole-file Estimation Analyze call
  -> one Scope per object
  -> per-object Calculation call
  -> Scope gate
  -> 2VN geometry validation and fallbacks
  -> deterministic Structural and Hardware Composer
  -> immutable BOM fact persistence
  -> project Material Plan / C-I-A resolution / purchase allocation
  -> formula allowances
  -> Objects and Object Detail presentation
```

### 3.1 Immutable input and handoff

The cycle starts only after Detection has locked the object and its evidence.
`estimation_input_v4` includes the locked object ID and quantity, evidence
pages and regions, OCR blocks, private full-page artifacts, original-file
reference and OCR event identity. Estimation must consume this package. It
must not rename the object or change Detection boundaries.

Handoff persists the original and private immutable evidence artifacts. Every
object-relevant full page is stored in the private
`rfq-estimation-evidence` bucket. Artifact paths are content-addressed with a
SHA-256 digest and upsert semantics.

Relevant code:

| Area | Location |
| --- | --- |
| Estimation job and handoff | `use_cases/estimation_runtime.py::_run_estimation_job` |
| Artifact persistence | `use_cases/estimation_artifacts.py` |
| Object-to-estimate batch | `use_cases/estimation_object_to_estimate_runtime.py::run_assembly_first_bom_batch` |

### 3.2 Dimension Graph

Dimension Graph is deterministic and per object. It is built from the immutable
object evidence and persists separately. It contains normalized dimension
numbers, drawing views and relations. It is not a CAD model and has no material
or pricing authority.

The graph is created before Analyze/Calculation composition. The full-page
evidence bytes are then loaded from private Storage and used for both model
phases. The graph must be treated as the evidence-based checker for visual
interpretation, not as a replacement for vision.

The owner referred to the underlying approach as "VN2" and later settled on
`2VN`: first the visual view/orientation claim, then the deterministic witness
against graph candidates. Do not rename this casually in code or user-facing
discussion.

### 3.3 Estimation Analyze, one file-level call

Analyze receives every pending immutable Estimation input in the accepted file,
deduplicated full evidence pages and the locked Detection registry. It runs
once for the file, not once per object. It returns one
`estimation_composition_scope_v1` per object.

Scope must identify enough physical context for later decomposition:

- physical zones and major assemblies;
- role of each zone, such as carcass, drawer bank, fixed divider/screen,
  worktop, hanging cabinet or facade zone;
- operability, including drawer versus door versus lift-up facade versus fixed
  structure;
- exact shown front topology and count;
- explicit construction assumptions where evidence is incomplete.

Analyze must not select a material product, price, labour, manufacturing route
or thickness when source/default policy owns it. Its job is to prevent the
Calculation call from abstractly splitting numbers into arbitrary panels.

The Scope and the exact Calculation handoff are stored in the final immutable
BOM fact. Analyze usage is a separate usage event. This makes the first call
auditable rather than an ephemeral prompt.

### 3.4 Calculation, one call per object

Calculation receives that object’s normalized Scope, Dimension Graph and
evidence pages. It may fill only geometry, exposure and material roles within
the Scope. It does not get to invent zones, delete zones or change locked
operability/topology.

The Scope gate restores the locked zone role/front groups and removes model
injected slide, hinge and lift secondary items. Hardware is composed by code,
not accepted from a model list.

### 3.5 2VN geometry resolution

2VN exists between visual Calculation extraction and deterministic structural
composition.

| Drawing view | Horizontal axis | Vertical axis |
| --- | --- | --- |
| Front elevation | Width | Height |
| Side elevation | Depth | Height |
| Top plan | Explicitly declares Width or Depth | N/A |
| Isometric/perspective | Can corroborate | Cannot be sole numeric axis source |

A direct axis becomes source geometry only where visual binding, graph witness
and normalized numeric value agree. If a binding is invalid, it is removed
before composition. Composer then uses a compatible peer/linked zone or a
named default. It must never keep a rejected nearby number just because it is
numerically plausible.

### 3.6 Deterministic Cabinet Block, parts and hardware

One Cabinet Block combines envelope, front topology, exposure and material
policy. The visual stage may emit only these front groups:

- `drawer_front`, stacked or side-by-side;
- `hinged_facade`, stacked or side-by-side;
- `lift_up_facade`, stacked or side-by-side.

Only the canonical elevation counts fronts. Perspective may corroborate but
must not duplicate a front count. Composer expands a supported block into
hidden carcass, backing, conventional drawer structure, visible fronts and
exposed side panels. It produces an approximate BOM, not a fabrication cut
list.

Material roles are intentionally distinct:

| Role | Current policy |
| --- | --- |
| Visible fronts / exposed carcass ends | `visible_sheet` |
| Hidden carcass, shelves and drawers | `internal_sheet` |
| Backing | Separate `backing` demand, normally 3 mm if not stated |
| Worktop | Separate demand |
| Finish / paint | Separate finish demand under established one-standard-set policy |

### 3.7 Hardware rules, current approved formulas

Hardware is derived only from accepted front topology and resolved cabinet
depth. Units matter.

| Front | Output | Formula / rule | Unit |
| --- | --- | --- |
| Drawer front | Drawer slide | `floor((cabinet_depth_mm - 100) / 100) * 100` | **set** |
| Hinged facade | Hinge | Historical V5: `<=600 mm: 2`; `>600 mm: 3`; `>2000 mm: 4`. Superseded by owner on 2026-11-05: `<=1000: 2`; `>1000: 3`; `>2000: 4` | **piece** |
| Lift-up facade | Gas lift / lift system | One system per lift-up facade | **set** |

Examples: 720 mm cabinet depth gives 600 mm slides. A 650 mm cabinet depth
gives 500 mm slides. A drawer needs one purchasable slide set, never two
individually named runners in the material demand. Gas lifts are a set. Hinges
are individual pieces.

The immediate user requirement remains: drawers must be understood as
horizontal shallow rectangular fronts, often in a lower bank. A tall repeated
slat, divider or decorative strip is structural, not a door. A horizontal
upper flap is lift-up, not hinged. If evidence is incomplete, prefer a fixed
structural interpretation instead of inventing hardware.

### 3.8 Material Plan and UI result

After persisted BOM facts, the Material Engine resolves and prices demand, then
allocates purchases. Object Detail has one Materials table with marker/name,
Required Material, Purchase Unit, Purchase Quantity and derived Total.
`Elements` is collapsed structure, not a second allocated-material table.

Formula rows owned by Profile Pricing Cost remain after physical materials:

| Formula row | Basis |
| --- | --- |
| Consumables | Percentage of primary physical material cost |
| Packaging | Percentage of primary physical material cost |
| Paint consumables | Percentage of coating material cost only |

They are neither catalog materials nor C/I/A lines, receive no purchase units,
and are not editable material demands.

## 4. Benchmark files and what was learned

### 4.1 Lev_1 / LF1

Path supplied by owner:

```text
/Users/qb/Desktop/SAMPLES/Adda/Lev_1.pdf
```

It is dimension-rich but text-sparse and has a SolidWorks educational
watermark. The watermark is not evidence for unit, material, identity,
construction or a dimension value.

The decisive production failure was
`run_b1752d1c73cc4f64be117984d98eb74e`: it merged a lower three-drawer bank
and a tall fixed slat screen into one carcass, classified six fixed strips as
hinged facades, created 12 hinges and no drawer-slide sets. It also bound the
430 mm base height as cabinet depth. This was a front-topology and dimensional
binding defect before pricing, not a Resolver/material-price defect.

The protected expected LF1 result is:

- lower `1580 x 430 x 720 mm` bank has three shown side-by-side drawers;
- exactly three drawer-slide sets;
- slide depth 600 mm, from the 720 mm depth rule;
- zero hinges and zero lift systems from the tall decorative screen.

### 4.2 Lev_2 / kitchen-like input

Path supplied by owner:

```text
/Users/qb/Desktop/SAMPLES/Lev 2.pdf
```

It is used for cabinet/kitchen topology and cross-view depth reasoning. The
user described five drawers around 650 mm depth, so expected slides are five
500 mm sets. The example also includes hinged vertical facades and lift-up
horizontal facades. Current deterministic fixture expectation is three
1100-mm hinged facades, nine hinge pieces and two lift-up facades, two lift
system sets. This needs a fresh production witness, not just a unit test.

### 4.3 Ada

Ada is a detailed multi-object file. Its last observed production run
`run_94a071678235419dabf2b773ebc072a3` was a **Detection membership
regression**, not an Analyze/Calculation defect: Detection supplied four
page-local objects instead of the protected two commercial assemblies. Analyze
then correctly ran once across the four pages and Calculation correctly stayed
within each locked one-page object, producing small fixed shelf/carcass BOMs.

Do not repair Ada by making Estimation merge Detection objects. First compare
the run’s Discovery/Membership facts with the protected Detection V6.37
witness and propose a bounded Detection benchmark only if that work is
explicitly authorized.

### 4.4 Large kitchen package

The 39-page kitchen is a useful stress input for evidence batching, not an
ordinary one-call estimating benchmark. Do not replay it without a bounded
hypothesis and owner authorization. It proves neither correct BOM nor correct
purchase planning just because a run completes.

## 5. Historical release lineage that matters now

The authoritative sequential numbering record is
`notes/ESTIMATION_V4_RELEASE_SEQUENCE_2026_11_02.md`. Detection has a separate
release/benchmark history, even where it uses similar V5 numbers.

### 5.1 V4 base which remains protected

| Release range | Important retained outcome |
| --- | --- |
| V4.1-V4.3 | Immutable evidence batches, persisted material facts, Object-to-Estimate/BOM foundation |
| V4.4-V4.6 | Priced non-blocking Assumption Fallback |
| V4.7-V4.10 | Geometry/material engine/progress foundation |
| V4.11, V4.15, V4.17 | Whole-drawing unit interpretation, centimentre guard, Dimension Scale Gate |
| V4.12-V4.14 | Assembly-first graph and deterministic structural composer, rather than object-kind recipe |
| V4.18-V4.23 | Optional coverage, bounded stage traces, safe evidence and incomplete-assembly resilience |
| V4.24 | Purchase-format metadata serialization repair |
| V4.25 | Correct C → I → A order and aggregate sheet purchase policy |
| V4.26 | Single Materials table presentation contract |
| V4.27 | Profile formula allowance restoration |
| V4.28-V4.29 | Initial navigation/read-cache and dead-callback experiments |

Historical terminal run `run_d82f58af38f84a4eb6fc3a2dbb8faeab` reached
`completed / materials_costed / 100%`. It proved cycle mechanics only. It was
not acceptable material output because Veneered MDF, LDSP and Hardboard all
used `A` due to unresolved keys/physical compatibility. Do not cite it as
catalog or quote-quality acceptance.

### 5.2 V5 construction semantic line

| Version | Commit/status | Meaning |
| --- | --- | --- |
| V5.1 | Implemented, needs fresh witness | Cabinet Blocks, approximate axes/default thickness and hardware formulas |
| V5.2 | Implemented, needs fresh LF1 witness | Operability/front-topology correction after 12 false hinges |
| V5.3 | Implemented, needs Lev_1/Lev_2 witness | 2VN visual-to-graph geometry binding |
| V5.6 | Implemented, needs witness | Whole-file Analyze scope followed by per-object Calculation |
| V5.6.1 | Implemented, needs witness | Store Scope/Calculation handoff in existing fact contract |
| V5.6.2 | Implemented, needs witness | Remap Calculation IDs to Scope IDs before 2VN |
| V5.6.3 | Implemented, needs witness | Agent-version transition so old repaired facts cannot be silently reused |

The active code currently routes `_run_estimation_job` into
`_run_estimation_v5_3_for_all_objects`, which calls the V5 assembly batch. The
batch itself includes the V5.6 Analyze/Calculation split. The user-facing
`estimation_version` string still says `v5_3_2vn_geometry_composer`; do not
mistake that label for absence of Analyze. It is a version-label hygiene issue
worth addressing only with a conscious evidence migration decision, because
the fact agent version governs cache reuse.

### 5.3 V5.7-V5.8 navigation/recovery line

This line is separate from construction semantics. It was necessary because
the user could not operate the product due to repeated Streamlit reruns,
stale DOM, mixed screens, duplicate headers and navigation delays.

#### V5.7.0.1, one browser navigation owner

`app.costerly.ai` owns browser history, cold-load masking and telemetry.
`core.costerly.ai` owns Streamlit route state, authorization, calculation and
the final correlated `app-ready`. The public wrapper has one iframe and must
not replace its `src` for normal internal navigation.

Earlier 900 ms New Estimate fallback and build-mismatch reload created a
competing navigation owner. They were removed. A lost callback records a
timeout or mismatch, but must not destroy a live iframe/session.

#### V5.7.0.2 and V5.7.0.3, prepared source and durable restoration

File Review prepares an `ObjectsLaunchPlan` only after editable cards render.
For a new estimate it contains reviewed edits, ignore list, metadata, source
bytes, target ID and seed rows. Preparation is no model call, no estimate
shell, no route write. Continue callback should only consume the prepared plan.

V5.7.0.3 fixed restored historical File Reviews: source bytes may be absent
from the Streamlit session after refresh, even though the original private
file exists. Processing stores immutable storage reference, SHA-256, MIME and
byte length in the existing `rfq_source_original` ledger event. File Review
restores that source in the background. It must not guess a random Storage
file if historical metadata is absent.

#### V5.7.0.4 and V5.7.0.5, root cause of the broken mixed screens

V5.6 display-snapshot transition code left a capture-phase browser handler in
old tabs. It could inject an Objects heading over stale File Review DOM,
creating the screenshots with duplicate logos/buttons or broken mixed screens.
V5.7.0.4 removed the retired snapshot handler, shell, styles, marker/body
classes, obsolete header helper and unused direct-DOM Objects progress runtime.
It did not replace them with another synthetic screen.

V5.7.0.5 then found two synchronous waits inside the live Streamlit route:
App re-read ownership before first target render, and Objects started a worker
before writing its header. The fix records an exact in-session ownership receipt
and paints the native target header before background setup. Direct URLs and
refreshes retain ordinary ownership validation.

#### V5.8, readiness bundles

V5.8 changed File Review → Objects and unchanged Objects → File Review:

- Continue is enabled only after one complete readiness bundle exists for the
  exact company and run.
- Bundle contains reviewed edits/ignored IDs, source bytes only if a new worker
  is needed, selected estimate ID, and complete initial Objects payload.
- For completed unchanged estimate it has durable/cached data and prepared
  Object Detail route tokens.
- Continue consumes the bundle without reading source, loading objects or
  writing Supabase before changing screen.
- Back retains an exact File Review snapshot for the first return render,
  skipping optional Naming, Document Identity and Preview refreshes. Deferred
  fragment remains responsible for later real updates.

Original V5.8 rule considered a running worker non-reusable. That contradicted
the product requirement for Back → Continue during calculation.

#### V5.8.1, active-estimate resume

Commit `7405e67` fixes that contradiction. An active worker or a pending
callback-to-first-render launch is still the same estimate:

- reuse current estimate ID if it matches the exact RFQ run;
- retain active Future and pending launch request;
- use reviewed seed rows for immediate Objects first paint while shell persists;
- retain `prepared_estimate_access` until worker completion or there is no
  pending worker/request;
- changed File Review edits still create a new estimate.

Owner live evidence: Back to File Review and Continue stopped resetting the
cycle. This is real evidence for resume behavior, not acceptance of the rest
of Estimation.

#### V5.8.2, handoff recovery

After V5.8.1, user saw exactly:

```text
Estimation failed: Estimation V4 handoff failed:
Expecting value: line 1 column 1 (char 0)
```

Objects was left at visual 45%, still `Estimating`. Diagnosis:

- **verified**: Handoff exception did not transition known reviewed objects to
  terminal failure; `_consume_estimation_future` only held a session error.
- **verified**: 45% is the early smooth-progress display cap, not proof that
  calculation reached a genuine 45% stage.
- **likely**: Supabase Storage uploaded/replied with an empty body and its
  Python SDK raised `JSONDecodeError` while parsing the response. Handoff
  itself does not parse model JSON. This remains likely until a provider trace
  confirms the blank response.

Commit `710165d` repairs only that bounded failure:

1. `use_cases/estimation_artifacts.py::_upload_immutable_artifact` retries
   only a blank-response `JSONDecodeError` at most three times with 0.2s then
   0.4s backoff. The artifact path/bytes are content-addressed and upserted,
   so retry is idempotent.
2. Any final handoff exception calls `_mark_handoff_failure`, setting known
   non-ignored rows to `failed / 100%` with
   `estimation_handoff_failed`.
3. `screens/objects.py` overlays that terminal failure in this browser session
   when the durable update is also blocked by the same incident.
4. No broad retry exists for arbitrary model, resolver, BOM or material errors.

Production marker verified after release:

```text
estimation-v5.8.2-handoff-recovery
```

## 6. UI and navigation lessons, do not repeat past failures

The owner had repeatedly asked that an enabled button means destination data is
ready. That is the desired contract, but Streamlit cannot make a full screen
atomically appear by caching data alone. Browser-side DOM overlays/snapshots
were tried and caused serious regressions: duplicate logo, duplicate action
rail, stale File Review under Objects heading, grey screens and a second
Streamlit rerun interrupting an apparent fast route.

Do not reintroduce:

- wrapper-owned synthetic target pages;
- capture-phase DOM snapshots or headers above Streamlit DOM;
- iframe reload/replacement as normal internal navigation;
- timers that declare screen readiness before correlated core `app-ready`;
- a click callback that synchronously waits for unrelated source restore,
  metadata save, shell creation or worker launch;
- a cache that overrides authorization or survives an edit/recalculation.

Keep:

- one live iframe;
- target-first native Streamlit render;
- exact in-session ownership receipt only for ordinary transitions;
- source/background work prepared before button enablement;
- short-lived Session State readiness bundle and seed rows;
- direct URL/refresh normal authorization path;
- UI data caches invalidated after edit, approval, recalculation, completion
  and New Estimate;
- one stable truthful loading state, not stacked spinners/toasts/reloads.

The user considers visible latency and broken transition frames product bugs.
Passing a unit suite or seeing a marker does not prove acceptance. Use the real
authenticated flow in the same browser tab and collect screenshot, timestamp,
route and runtime event evidence.

## 7. Current operational state and verification

### 7.1 What is verified

| Item | Evidence |
| --- | --- |
| V5.8.1 no longer resets active worker on Back/Continue | Owner live test before V5.8.2 |
| V5.8.2 code deployed | Wrapper marker `estimation-v5.8.2-handoff-recovery`; core endpoint HTTP 200 |
| V5.8.1 tests | 393 targeted passed; full 1,636 passed with same 10 unrelated baseline failures |
| V5.8.2 tests | 403 focused passed; full `1639 passed, 10 failed, 29 warnings in 15.90s`; `py_compile` and `git diff --check` passed before release |
| V5.8.2 checkpoint published | `d86f42f`, `origin/main` matched at checkpoint time |

The established 10 full-suite failures are unrelated baseline failures:

1. One Detection page-image browser handshake expectation.
2. One Estimate material-resolution expectation.
3. Three historical Estimation handoff preview/OCR fixture expectations.
4. Four material identity, normalization or Profile fixture expectations.
5. One sheet-material family policy fixture expectation.

Do not call these V5.8.2 regressions unless a changed source path or a fresh
diagnostic proves the link.

### 7.2 What remains unknown or not accepted

| Topic | Status |
| --- | --- |
| Fresh V5.8.2 authenticated LF1 run | Required |
| One Storage blank-response recovery | Required, only code/test evidence exists |
| Terminal display after all three Storage retry failures | Required, only code/test evidence exists |
| LF1 hardware output: 3x 600-mm slide sets, no false screen hardware | Required production witness |
| Lev 2 zone/depth/front output | Required production witness |
| Analyze Scope and Calculation handoff inspection | Required production witness |
| C/I/A quality and catalog selection | Not accepted by terminal cycle success |
| Perfectly coherent same-tab File Review/Objects/Review/Back browser paint | Still needs fresh end-to-end observation |

The owner said the recent result was "acceptable" only in the context of
making the checkpoint. Do not inflate that into full Estimation or UI product
acceptance.

### 7.3 Required next live acceptance run

Start a fresh authenticated LF1 estimate, not an already failed or reused one:

1. From File Review, Continue to Objects Estimation.
2. While the worker is active, Back to File Review, then Continue again.
3. Confirm exactly the same estimate ID/worker continues and no duplicate
   calculation begins.
4. Observe final result. If Storage has one transient blank response, it should
   retry and proceed. If the response is blank all three times, every affected
   object must show `Failed`, not `Estimating 45%`.
5. Confirm File Review, Objects, Review and Back never display mixed/duplicated
   screen DOM in the same tab.
6. Preserve run ID, route, timestamp, screenshot and runtime event markers.

After this navigation/recovery witness, the next Estimation-semantic witness
is LF1 Scope/Calculation inspection. It must show the three drawer fronts and
fixed tall screen before looking at materials. If those facts are wrong, stop
before tuning the Material Engine.

## 8. How to inspect a production run without guessing

For an Estimation incident, collect in this order:

1. RFQ run ID and estimate ID.
2. `agent_usage_events` and bounded Estimation stage events.
3. Immutable input records, evidence artifact references and Dimension Graph.
4. Analyze usage event plus persisted `composition_scope` and
   `calculation_handoff` in final BOM fact.
5. Structural BOM: assemblies, parts, materials, normalizations and `two_vn`
   audit.
6. Material Plan, resolver source markers/reasons and Object Detail snapshot.
7. Browser runtime event trace only for a UI/navigation symptom.

The fact that Analyze says a correct thing in raw reasoning is not enough. It
must survive into persisted Scope, handoff, deterministic BOM and material
demand. Conversely, a wrong final cabinet BOM can originate earlier in
Detection identity, evidence completeness, Analyze scope, Calculation output,
2VN binding, composer rules or Material Engine. Isolate the earliest supported
cause.

## 9. Relevant code and tests

| Topic | Main files |
| --- | --- |
| Immutable evidence Storage and safe retry | `use_cases/estimation_artifacts.py`, `tests/test_estimation_handoff.py` |
| Job handoff and terminal technical failure | `use_cases/estimation_runtime.py`, `tests/test_estimation_runtime.py` |
| Dimension Graph, Analyze, Calculation, Scope gate, 2VN and BOM persistence | `use_cases/estimation_object_to_estimate_runtime.py`, `use_cases/estimation_composition_scope.py`, `use_cases/estimation_structural_bom.py` |
| 2VN resolver | `use_cases/estimation_2vn_resolver.py` and structural BOM tests |
| Material resolution / drawer-slide fallback | `use_cases/material_engine_adapter.py`, `use_cases/material_identity_status.py` |
| File Review readiness and Continue | `screens/file_review.py`, `tests/test_navigation_routes.py` |
| Objects first paint, worker, failure overlay | `screens/objects.py`, `ui/objects_pricing.py` |
| Session receipts and invalidation | `state/session.py`, `app.py` |
| Wrapper and app/core transition contract | `cloudflare/index.html`, `ui/screen_transition.py`, `tests/test_runtime_observability.py` |

Useful symbols:

```text
use_cases.estimation_runtime._run_estimation_job
use_cases.estimation_runtime._mark_handoff_failure
use_cases.estimation_artifacts._upload_immutable_artifact
use_cases.estimation_object_to_estimate_runtime.run_assembly_first_bom_batch
use_cases.estimation_composition_scope.calculation_handoff
screens.file_review._prepare_objects_launch_plan
screens.file_review._continue_to_objects_estimation
screens.file_review._current_estimate_is_reusable
screens.objects._consume_estimation_future
screens.objects._data_with_progress
```

## 10. Authoritative records

Read these before making a material Estimation change:

1. `notes/ESTIMATION_V5_1_CABINET_BLOCK_CONTRACT_2026_11_03.md`
2. `notes/ESTIMATION_V5_2_FRONT_TOPOLOGY_CONTRACT_2026_11_03.md`
3. `notes/ESTIMATION_V5_3_2VN_GEOMETRY_CONTRACT_2026_11_03.md`
4. `notes/ESTIMATION_V5_6_ANALYZE_CALCULATION_CONTRACT_2026_11_03.md`
5. `notes/ESTIMATION_V5_8_1_ACTIVE_ESTIMATE_RESUME.md`
6. `notes/ESTIMATION_V5_8_2_PRODUCTION_CHECKPOINT_2026_11_04.md`
7. `notes/ESTIMATION_V4_RELEASE_SEQUENCE_2026_11_02.md`
8. `notes/TODO.md` section `3.17.4.4`

For navigation/UI changes also read:

1. `notes/ESTIMATION_V5_7_0_NAVIGATION_READINESS_CHECKPOINT.md`
2. `notes/ESTIMATION_V5_8_NAVIGATION_READINESS.md`
3. `notes/ESTIMATION_V4_29_NAVIGATION_AND_OBJECT_DETAIL_IMPLEMENTATION_CHECKPOINT_2026_11_03.md`

## 11. Safe next-action protocol for the new chat

1. Confirm checkout, branch, `git status`, remote/main and current production
   marker. Preserve the existing dirty TODO lines.
2. Ask the owner for the newest fresh LF1 run or run it only if authorized.
3. Inspect persisted evidence and stage events before writing code.
4. If navigation/recovery fails, distinguish browser click, rerun, source
   restore, durable write, worker handoff, read/render and visible completion.
5. If semantic hardware/BOM fails, inspect Analyze Scope then Calculation
   handoff then 2VN audit before altering composer or Material Engine.
6. Make one bounded change at the earliest supported cause. Preserve
   Detection and existing prepared-navigation contracts.
7. Add focused test coverage, run the appropriate full/regression suite,
   deploy only with a correct sequential Estimation version and record exact
   marker, commit, run ID and acceptance state.

Do not stack another cache, timer or client overlay onto an unverified UI
symptom. After two unsuccessful variants of the same approach, stop and take a
new diagnostic measurement.

## 12. One-line state for the next chat

**Estimation V5 now has the intended two-pass Scope-to-Calculation architecture
and bounded approximate cabinet/hardware rules, while the deployed V5.8.2
checkpoint has fixed active-worker resume and terminal handoff recovery; the
next required evidence is one fresh authenticated LF1 run, first for
navigation/terminal state, then for Scope, 2VN and drawer topology quality.**
