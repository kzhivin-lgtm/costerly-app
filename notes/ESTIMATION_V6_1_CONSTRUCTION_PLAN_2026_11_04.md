# Estimation V6: V6.1 experiments and V6.2 whole-object understanding

Work: 3.17.4.5. Status: local implementation, live acceptance pending.
Current approved iteration: V6.2, 2026-11-05. The historical filename and V6.1
decisions below are retained for continuity. V5.9 was proposed in discussion
and withdrawn before any implementation/version change. Published production
remains V5.8.2; development numbering is not the deployment marker.
Owner authorized V6.1 on 2026-11-04. Base: e608f37, matching remote main.
Latest owner clarification: Haiku is the required production route for both
passes. Stronger models are permitted only for diagnosis, not acceptance or
promotion. Functional quality must come from bounded contracts, prompts and
deterministic tools while retaining a fast, inexpensive result.
V5.8.2 navigation/recovery, Detection identity and material-only scope remain
protected. Pre-existing TODO changes belong to the owner.

## Decision

### Current V6.2 boundary and results, 2026-11-05

Owner approved a whole-to-part first cycle and explicitly stopped downstream
work for now. Explanations must expose observable features, view correspondences
and assumptions, not private chain-of-thought. Small estimating errors are not
automatic failure; wrong physical function, major omitted/duplicated assemblies
and gross geometry remain unacceptable. No universal percentage tolerance is
inferred from the owner's 1800-versus-2000 example. A separately hanging cabinet,
drawers, hinged fronts and horizontal lift-up fronts must remain distinguishable.
Gas-lift provision follows the existing owner policy, not printed evidence.

`agents/estimation_understanding_agent.py` with the V6.2 prompt runs one shared
Haiku 4.5 request on immutable object membership. All unique full pages precede
their labelled detail crops; raw cited OCR/legend context remains available.
It asks for two overview sentences, major components with function/quantity/
operation/material hypotheses, each view's contribution, concrete cross-view
matches and uncertainties. It does not request a BOM, numerical dimension
assignment, prices, hardware counts or formal projection classification.
An explanation can still be false. Reference/coverage checks do not certify
semantic correctness. There is no automatic repair/retry or second model vote.

This is exposed through the existing replay tool's `--understanding-only`, not
the production Calculation path. It rejects other model/observation/repair
overrides. Application bounds: 64 images, 100000 context characters, 60 s,
3500 output tokens per object capped at 12000, no SDK retries. Larger cases
remain unbenchmarked; bounded output is not evidence of ten-object capacity.
Source-only PDF probes are explicit synthetic local inputs (`--source-pdf`),
with no Detection/OCR claim, no catalog reads and no writes to production.
HTML reports escape model content and retain raw malformed/invalid responses
with their failure status. Working product UI remains unchanged pending agreed
scenarios. Reports are local review artifacts, not approved estimates.

Detection handoff audit was bounded to LF1's immutable input
`db175c9d-b911-434e-a3ed-de612640f96f`, not a claim of global Detection correctness.
It retains all six owned islands and one full 1985x1404 page, 16 OCR blocks,
coordinate metadata but no native vector segments. Details are crops from
the same raster, not independent high-resolution rerenders. The code-level
handoff retains raw pages and OCR with shared document context; LF1's older
snapshot has no separate document_context. No loss of LF1 islands was found.

Lev 2 source SHA256:
`b69e132814531862c1abbf2ea3910e0221ab013dd2d0fb184400149d6ec02b1d`.
Read-only company-610 lookups by name and exact SHA returned no matching
immutable Estimation input. Its probe used the original one-page PDF through
the existing bounded renderer, without fabricated Detection regions or OCR.
Do not compare its single-page presentation with LF1's seven images as though
this were a controlled file-difficulty experiment.

All capsules/reports are `/private/tmp/estimation-v6-2-<name>.json` / `.html`:

| Name | Result |
| --- | --- |
| lev2-prepared | Preparation only; synthetic fixture lacked contract_version. No provider call. Superseded by prepared-02, which passes offline request preparation. |
| lev2-01 | 28.823 s provider / 28.95 s total, 2593 input + 3165 output tokens. Recognizes a kitchen overall but invents ribbed fronts and misreads several modules; fails the owner operability gate. Returns source_ref instead of input_id, rejected without remapping. Raw answer/report retained. |
| lf1-01 | 27.503 s provider / 27.75 s total, 9557 input + 2898 output. Name hint Cabinet is present. Invents a closed cabinet with seven hinged doors and one leg. Semantic failure despite valid JSON/references. |
| lf1-02 | 29.525 s provider / 29.80 s total, 9534 input + 3226 output. Removes object_name and its retrieval-hint descriptor only from the outgoing manifest; immutable input unchanged. Same images/prompt. Now identifies fixed slatted panel, three drawers and two supports. Still wrong number/units/measurement assertions and some false view matches. |
| lf1-03 | 29.342 s provider / 29.62 s total, 9534 input + 3226 output. Fresh provider call, request hash identical to 02, same returned interpretation. Confirms repeatability of this one case, not general reliability. |

The naming ablation gives concrete evidence of sensitivity to upstream labels;
general causal attribution remains limited by one named baseline. Final V6.2
transport omits Detection's semantic name, while retaining IDs/membership and
the original name in the source audit. The global/major-parts reading improved
on LF1, but neither file passes full first-cycle acceptance. In particular the
model keeps injecting unsupported dimensions despite the non-geometric task.
Do not silently strip those errors and present the remaining prose as verified.
Stop this iteration at owner review of the explanations; no Calculation/deploy.

Verification: 1759 passed, the same 10 previously recorded baseline failures,
29 warnings, 16.68 s. New tests cover one Haiku call, source/legend retention,
per-object view coverage/isolation, quantities/operations, no Calculation/DB
entry from first-cycle replay, name-hint removal, HTML escaping and readable
failed answers. Two-object mocked orchestration is not live multi-object
acceptance. Preserve the unrelated 50 TODO lines outside the commit.

### Historical V6.1 decision (not a production acceptance claim)

Use one shared Analyze over Detection's immutable evidence, followed by
object Calculation. Analyze owns large assemblies, repeated members,
operability, surface/material interpretation, evidence-linked text/legend
definitions and explicit construction assumptions. Calculation measures and
completes the locked construction, without choosing a different material.
Code expands parts, layers, edge material and hardware. The existing Material
Engine compares permitted hidden-material alternatives using project purchase
cost, after C/I/A candidate resolution. No extra model call selects materials.

The supplied full pages and OCR are complementary. Shared document context
may inform material interpretation but does not change object membership.
Source instructions in documents are evidence, never application instructions.
Source assignment, linked legend assignment, visual inference and defaults
retain different provenance and a short decision rationale, not private
chain-of-thought. A source-bound material cannot be economically substituted.

## Construction and uncertainty

A veneered panel is a purchasable board. Finished thickness and purchased
sheet thickness are distinct. A 40-mm member can explicitly assume two
20-mm layers and veneer edge treatment; purchasing counts both layers and
the edge material. It must not silently become one 18-mm sheet or automatically
force every hidden drawer part to 40 mm. Visual similarity is a recorded
derived relationship, never proof of an explicit source thickness.
Owner reiterated that 40 mm MAY be two stacked 20-mm panels. This is a
construction option, not proof of the purchased stock thickness. Preserve an
explicit 40-mm stock choice as one layer; both options keep a 40-mm finished
edge. Layer count multiplies sheet demand, not the finished edge perimeter.

Fixed decorative members, countertops and supports remain accountable.
Analyze describes repeated panel groups; Calculation measures each group;
the composer expands its quantity. Cabinet defaults remain available for
incomplete drawings, with named provenance and preserved front arrangement.

2VN checks declared axis/projection and numeric consistency, using Dimension
Graph relations only as candidates, not proof of dimension-line ownership.
Rejecting a binding removes its source authority. No maximum
number from an unrelated side view may overwrite an axis. Explicitly linked
same-axis peers may supply a missing dimension; otherwise use a labelled
construction default.

## Project purchasing

Alternatives must be explicitly allowed for hidden construction, with matching
stock thickness and equivalent physical demand. Compare whole-project rounded
purchase totals with the existing aggregate sheet policy and 10% allowance.
This estimates shared sheet capacity; it does not establish usable offcut
shapes or perform manufacturing nesting. Respect user overrides. Persist
selected material, considered costs, rejection reasons and policy limits.
Use bounded deterministic comparisons, not an exponential scenario search.

## Verification gates

- Sparse LF1: three side-by-side drawers; 720-mm depth yields three 600-mm
  slide sets; no screen hinges; fixed panel multiplicity, top and two supports.
- Material legend on a separate page: callout and definition survive Analyze,
  Calculation and persisted BOM with source references; appearance cannot
  override the explicit finish. Unknown references never become source facts.
- 40-mm build-up: two purchased layers plus edge demand, with distinct stock
  and finished thickness; hidden construction can use compatible alternatives.
- Project economics: small hidden demand can share a purchased material;
  introducing cheaper board only wins when its rounded project cost is lower.
- One Analyze for the accepted file and one Calculation per ordinary object;
  large evidence still uses bounded existing Calculation batches and records
  actual calls rather than promising exactly N regardless of input size.
- Baseline and regression suites, live model witness, deployment and owner
  acceptance are separate evidence levels.

## Implementation and protected behavior

The active fact version is `estimation_calculation_v6_1`; older V5 facts cannot
masquerade as V6 output. Analyze is `estimation_analyze_v6_1`. Both use the
existing runtime, private evidence storage, deterministic composer and Material
Engine. No database migration, UI callback, timer, worker or Detection change
is introduced. Production remains at the previous checkpoint until acceptance.

Full source pages are uploaded once per file handoff, including image-only
context pages outside object membership. Analyze receives deduplicated images
and cited text. Calculation receives object geometry pages plus its locked
construction and material evidence chains. A partial retry still includes
already calculated objects as read-only context; it recalculates only pending
objects. The normal path is one Analyze plus one Calculation per object.
Large object page sets retain existing batching and reconciliation calls.

Carcass, fronts, drawer internals, back, countertop and support stock have
separate assignments. Missing hidden roles reuse assigned stock with recorded
single-layer assumptions instead of automatically introducing hardboard or
LDSP. Thickness-source claims require references; an inconsistent stock-layer
build-up is retained as a construction normalization for review. Finish area
is scoped to assigned roles and excludes buried laminate faces. Cut dimensions
remain approximate estimating geometry, not a manufacturing cut list.

Project alternatives are a deterministic greedy comparison, at most three
options per group and 24 trial plans overall. Identical alternative demands
are grouped across objects. Source-bound materials, manually edited norms and
edge-system changes are not automatically substituted. Manual purchase
overrides disable substitution. Both compared choices need usable Company
Catalog or Israel Reference prices; an Assumption Fallback price is not
economic evidence. Decisions and effective material facts are persisted in
the existing purchase-plan snapshot and projected into published line facts.

## Live verification boundary

Local verification on 2026-11-04: 18 new tests added. The final complete suite
returned 1657 passed, 10 failed, 29 warnings in 15.84 seconds. Before edits,
the same suite returned 1639 passed and the same 10 failures. No new failing
test remains. `git diff --check` and compilation of the changed core modules
and replay tool passed. These durations measure tests, not customer latency.

The unchanged baseline failures are:

- `test_processing_uses_only_bounded_browser_handshake_after_complete_marker`
- `test_yellow_company_item_cannot_silently_supply_an_estimate_price`
- `test_shadow_handoff_uses_source_page_when_image_only_ocr_cannot_resolve_anchor`
- `test_shadow_handoff_falls_back_to_full_page_for_invalid_preview_bbox`
- `test_shadow_handoff_reuses_detection_preview_and_persists_full_evidence_page`
- `test_drawer_slide_without_nominal_length_is_yellow_not_review_or_red`
- `test_furniture_profile_identity_does_not_require_wall_thickness`
- `test_identity_normalizer_retains_only_domain_attributes_not_source_prose`
- `test_policy_seed_uses_current_family_code_and_only_approved_price_key_facts`
- `test_mdf_policy_keeps_actual_facing_classes_separate`

New tests cover source/legend provenance, shared page/text deduplication,
image-only context outside object membership, locked material roles and drawer
arrangement, stock layers/edge demand, finish area, fixed rib groups, purchased
supports, numeric 2VN rejection, shared project economics and manual restoration.
Mocked runtime tests verify one shared Analyze, one Calculation per pending
object, one download per shared page and complete context on a partial retry.

Read-only production lookup identified the latest LF1 immutable input as
`db175c9d-b911-434e-a3ed-de612640f96f`, created 2026-11-04 18:49:39 UTC.
No production facts, estimates or catalogs were changed by the lookup.

`tools/replay_estimation_v6.py` can execute the same Analyze, Calculation, 2VN,
composer and purchasing path while saving results only to a fresh local JSON.
Its default mode is read-only; `--execute` enables paid provider calls.
The first execution attempt was rejected by access review before the process
started. The owner subsequently explicitly authorized one paid LF1 replay and
Anthropic evidence transmission. No alternative transport or bypass was used.

The authorized replay ran on `fab06ff` and failed after 28.95 seconds at
`normalize_construction_scope`: `construction panel groups require a fixed
panel assembly`. Analyze returned a parseable response with a usable palette,
but at least one zone supplied nonempty `panel_groups` with an assembly role
other than `vertical_panel`. Calculation was not called. The replay wrote only
`/private/tmp/estimation-v6-lf1-witness-01.json`; no database writes occurred.

This is a failed live acceptance gate, not a completed BOM. The agent currently
builds its usage event and returns its response only after normalization, so
the failed witness has no raw model response or token/cost data. Consequently,
the exact offending zone and whether its groups represent a valid construction
cannot be established from this run. Empty usage does not mean a free call.

The owner subsequently authorized all necessary bounded paid replays until
production readiness and personal acceptance. The replay tool now saves raw
text, usage, request fingerprint and immutable input/catalog/page snapshots
before parsing. Identical provider requests can be reused offline; changed
requests require explicit `--execute`. No production writes are performed.

## Diagnostic witnesses after the initial failure

Local capsules: `/private/tmp/estimation-v6-lf1-witness-NN.json`.

| Witness | Result | Evidence and conclusion |
| --- | --- | --- |
| 02 | Haiku Analyze rejected, 28.95 s | False hinged screen, four legs, conflicting material families. Original fixed-panel guard correctly rejected semantic errors. |
| 03 | Sonnet Analyze timed out at 90 s | No response retained; quality unknown. |
| 04 | Computed, NOT accepted, 134.47 s | Sonnet Analyze 98.69 s, Haiku Calculation 35.39 s. Correct fixed screen/three drawers/two supports, but invented stock variants, duplicate enclosure, wrong thickness, missing group dimensions and 500-mm slides. |
| 05 | Analyze rejected, 68.02 s | Clearer contract removed duplicate enclosure and preserved horizontal drawers. Fixed decorative screen was labelled facade_set, with no operating fronts. Thickness interpretation remained wrong. |
| 06 | Analyze rejected, 72.34 s | Coordinate-aware view details preserved; invalid palette provenance `derived`, continued cm/mm and material mistakes. Crops alone did not establish semantic correctness. |
| 07 | Adaptive-high Sonnet timed out, 180.26 s | Same evidence and prompt, reasoning enabled; no completed answer. |
| 08 | Stream diagnostic timed out, 180.29 s | First provider event at 2.299 s, no text token before timeout. Connection establishment is not the dominant delay. No accepted output or complete usage. |
| 09/10 | Strict schema rejected before inference | Both original and simplified schemas exceeded the provider grammar limit (HTTP 400). Approach abandoned after two failures; experimental schema code/tests removed. |
| 11 | Adaptive-medium exhausted output, 227.85 s | 10,646 input and 12,000 output tokens, stop_reason=max_tokens, zero text blocks. The output budget was consumed before the JSON answer, not a connection timeout. |
| 12 | Computed, NOT accepted, 155.23 s | Bounded thinking returned Analyze in 120.57 s (10,675 input / 6,774 output tokens), but still converted 19 cm into 19-mm stock, treated 4 as a gap and assumed compact laminate. Haiku Calculation misclassified plan/side views, multiplied frame-envelope area and lost 720-mm depth under the unchanged 2VN guard. |
| 13 | Opus diagnostic, NOT accepted, 177.27 s | Analyze correctly selected 40-mm ribs from two 20-mm veneered boards, painted MDF and two purchased legs. Rib count, edge width and thickness inheritance remained unresolved. Haiku geometry still wrong. Not a production route. |
| 14 | Sonnet Calculation diagnostic, NOT accepted, 52.56 s | Reused 13 Analyze without another paid Analyze. Better group face dimensions and 600-mm slides, but wrong worktop footprint, a derived height bound to a different source number, and invalid orientation. Not a production route. |
| 15 | Target Haiku Analyze failed, 23.82 s | 13,415 input / 2,427 output tokens. Explicit unit context did not establish correct semantics: drawers omitted, decorative groups assigned to a closed carcass, 40-mm interpretation contradicted by 20-mm assignments. Guard retained. |
| 16 | Observation-only diagnostic, 15.35 s | Haiku saw three drawer/compartment fronts but confused view ids, units and supports. Simplifying only the output request did not solve visual reasoning. 5,777 input / 1,463 output tokens. |
| 17 | Labelled-view observation, 15.16 s | Generated headers improved image/id association but did not fix projection classification, units or moving-front interpretation. 6,040 input / 1,377 output tokens. Not a BOM. |
| 18 | Target Haiku Analyze failed, 24.62 s | Same full contract as 15, with explicit generated view labels. Fixed-panel guard again rejected groups on a non-panel assembly. This prompt/evidence-presentation approach is stopped after two unsuccessful full Haiku runs. |
| 19 | Compact Haiku Analyze, NOT accepted, 18.62 s | Four physical zones and three drawers identified; six inner uprights but frame members omitted. Source 40-mm member and assumed 18-mm cabinet conflicted in one stock family. Compiler now preserves source thickness and records alignment of assumed minor variations to shared stock. |
| 20 | Compact Haiku full cycle, NOT accepted, 48.93 s | Four assemblies, 12 part rows and five material rows computed. Model selected solid wood, seven inner uprights and one support; Calculation misclassified the top plan, used stock thickness as cut-face size and wrong cabinet/worktop dimensions. Completion and shorter latency do not establish acceptance. Capsule: `/private/tmp/estimation-v6-lf1-witness-20.json`. No database writes. |
| 25 | Evidence-first Haiku full cycle, NOT accepted, 79.33 s | Analyze 38.29 s, 17,404 input / 4,321 output; Calculation 40.062 s, 20,156 input / 4,966 output. Four zones, three drawers, six inner uprights plus frame and two supports, but plan labelled elevation, thickness 18/25 rather than justified 40 and contradictory assembly dimensions. Capsule `/private/tmp/estimation-v6-lf1-witness-25.json`. |
| 26 | Evidence-first with conflicts, NOT accepted, 80.86 s | Analyze 35.512 s, 17,498 input / 4,033 output; Calculation 44.378 s, 19,713 input / 5,757 output. Repeated projection failure, incorrect solid-wood choices and one support. Same approach stopped after two full witnesses. Capsule `/private/tmp/estimation-v6-lf1-witness-26.json`. |
| 27 | Isolated projection diagnostic, failed | Full page plus ONLY the named top-plan detail, no BOM/material/schema task. Haiku still answered front_elevation, width/height. Provider 1.976 s, 2,941 input / 90 output. Heavy prompt load alone does not explain this error; this single witness does not establish general model incapability. `/private/tmp/estimation-v6-lf1-projection-27.json`. |
| 28 | Exact cached replay, NOT accepted, 0.88 s | Both provider responses reused by request hash, no paid calls. Final 2VN guards downgrade conflicting ownership/projection and unbound member cut faces instead of certifying them. `/private/tmp/estimation-v6-lf1-replay-28.json`. |

Diagnostic 16 isolates Haiku visual recognition from the large BOM/material
response contract. It uses the same source pixels with concise observation
instructions, no catalogs or formal BOM schema, and cannot publish an estimate.
This is a discriminating diagnostic, not an added production pass.

## Approved compact Analyze contract

### Approved direction: evidence-first, strategy 2

Owner chose strategy 2 after considering (1) construction templates,
(2) an evidence map before construction, and (3) targeted verification/repair.
Manual template-library preparation is not desired. All three alternatives
are tracked in the authoritative TODO under 3.17.4.5. Initially only strategy 2
was active; the later approved strategy-3 experiment is recorded below.
Owner subsequently authorized autonomous bounded experiments until a genuine
blocker, without approval per attempt. Haiku/materials-only and protected
production boundaries remain. Read-only diagnostics may vary the observation
contract; no additional production model stage is implied.
Extend existing Dimension Graph and 2VN, not a parallel estimation system.
First enrich source numbers with line/end-point candidates in the same known
coordinate frame. Keep candidate topology separate from model-interpreted
physical ownership, and keep raw source context/legends available. A line or
number near a view never by itself proves an assembly dimension.
LF1's immutable input has no vector_line_segments, despite a vector-capable
source profile. The bounded first implementation therefore needs a raster
candidate path on existing full-page evidence; no Detection repair, extra
model stage or private local-PDF dependency in production is authorized.
The previous WIP commit 934cc9e is a reproducible comparison, not an accepted
functional checkpoint. V5.8.2 remains the production checkpoint.

Implemented first slice in `use_cases/estimation_evidence_map.py`:
- Reuses Dimension Graph, source coordinate frame and scale policy. Native
  rendered-pixel lines are preferred; missing lines use bounded raster scan
  candidates. No vector capability is fabricated from page profile counts.
- Returns source numbers, candidate lines/endpoints, crossing candidates and
  known views. Raster stroke endpoints are NOT verified arrowheads. Short
  outside-label dimensions and chained spans remain explicitly uncertain.
- Keeps raw text and same-literal index candidates across document context.
  Candidate VN11 joins do not prove that a legend applies to every object.
- Analyze emits view and physical-boundary readings before construction.
  Known refs/ownership are validated, contradictory axis values are recorded
  as needs_review. Calculation can reference a reading without retyping its
  numeric value/unit/ref/binding. Unknown or foreign ids cannot be substituted.
- Full map survives existing scope/fact persistence; model transport omits
  duplicate raw graph/text. Shared object-local view ids cannot cross owners.
  Conflicting bindings and unbound group faces cannot become source geometry.
- Runtime versions now include `evidence_map_v1`, preventing reuse of older
  Calculation facts as if they were generated with the new contract.

Offline line witnesses: `/private/tmp/lf1-evidence-map-21` through `-24`.
21 exposed OCR character strokes in candidates. 22 rejected the masking
experiment because OCR boxes clipped real lines. 23 removes only strokes
fully contained in OCR boxes and preserves long dimension strokes. 24 tested
crossing-count ranking; it worsened leader/chain choices and was discarded.
The retained ranking is 23, with no forced endpoint ownership. Visual review
of overlays, not candidate count, established these limitations. Preparation
was ~0.45 s on LF1; this is not a multi-object performance benchmark.

Verification: 62 focused checks passed; complete suite 1697 passed, the same
10 baseline failures, 29 warnings, 15.73 s. No DB writes, deployment or accepted
LF1 material estimate. Tests establish reference/coordinate/provenance contracts,
not physical interpretation. The combined map+construction model request is
stopped after witnesses 25/26. Next discriminating diagnostic is cross-view
dimension constraints for projection and physical ownership, investigated below. Do not introduce
an extra production vision stage or claim Haiku success based on this WIP.
Open: true extension/arrow endpoints, reliable projections, member-level
measurements, live indexed-legend case, ten-object output/latency budget and
owner-visible rationale/conflict review. Manual template preparation remains
deferred; the bounded repair alternative remains pending in TODO.

#### 2026-11-05: cross-view constraints, trials 29-37, not accepted

Implemented a CLI-only diagnostic in `use_cases/estimation_dimension_relations.py`.
It joins equal printed values with compatible pixel spans, and printed sums
with aligned interval endpoints on the same page. Pixel spans do not create
new measurements. Relations remain candidates, not proof of physical ownership.
On LF1 it finds 187 = 72 + 115 and the two orthogonal 160 spans without any
file-specific constants. Orthographic axis-domain consistency makes the central
upper view a conditional top-plan hypothesis. Bounded minimum-edit search uses
existing view readings to select width/depth orientation only when unambiguous.
Assumptions explicitly exclude rotated elevations, oblique cuts and coincidental
correspondences. Incomplete search, non-orthographic input or ambiguity never
authorizes an arbitrary assignment. Caps: 256 segments, 80 relations, 4096
assignment search states. No production caller is wired to this experiment.

Changed projections invalidate old ownership. The optional reobserve diagnostic
withdraws ALL dependent ownership, retains immutable source numbers, and saves
the superseded interpretation outside Calculation transport. Existing 2VN guards
still downgrade unsupported model source claims. Geometry scope transports the
assumption audit only when explicitly present; ordinary production behavior is
unchanged. A no-op reconciliation now stops before paid Calculation.

All witnesses are local `/private/tmp/estimation-v6-lf1-<name>-NN.json` capsules,
Haiku `claude-haiku-4-5-20251001`, with requests, text responses, usage and source
snapshots. No private thinking contents, DB writes, push or deployment.

| Witness | Controlled question | Result |
| --- | --- | --- |
| projection-29 | Equalities/aligned sums added to isolated projection probe | Still front elevation, provider 1.848 s |
| axes-30 | Joint physical axes before projection names | Still front; rejected true cross-view match as coincidence, 15.452 s |
| axes-31 | Same task with 2048-token Haiku thinking budget | Still front, 19.731 s; no stronger-model route |
| projection-32 | Add computed conditional projection domains | Model still ignores top-plan candidate, total 2.36 s |
| witness-33 | Reconcile projections before Calculation, cached Analyze 26 | INVALID intervention: section-without-axis made solver abstain; paid Calculation therefore did not test correction, total 51.47 s |
| witness-34 | Respect existing 2VN section vertical=height convention; offline preflight proves changes | Calculation accepts top-plan/side projections, but old ownership still gives base height 1450 and top 200 x 1870; Calculation 41.243 s |
| witness-35 | Same corrected projections, withdraw prior ownership | Base depth 720 recovered, but height 1450, screen 2650 and top 1870 x 1150 remain wrong; Calculation 40.885 s |
| measurements-36 | Minimal geometry-only output, no BOM/ref repetition | 5.02 s provider; base 1580 x 430 x 720 correct, top 1870 x 750 and supports wrong |
| measurements-37 | Same compact task plus code-computed axis candidates | 6.489 s provider; top depth 1150 and support height 750 improve, top width still 1870 despite depth-only candidate; screen still 2650; support cross-section absurd |

Comparison caveat: 33-35 reuse Analyze 26, so wall times exclude its original
35.512 s and these runs cannot validate a fresh end-to-end material selection.
That Analyze also has wrong solid-wood/default thickness, member/support count
and support shape. Neither geometry improvement nor passing tests repairs it.
Trials 36/37 are observations, not estimates, and do not compile a BOM.

Conclusion: source geometry constraints can correct a projection as an audited
assumption; they do not establish component ownership, count, material or a
complete valid estimate. Longer reasoning and shrinking output did not remove
the semantic barrier. Stop cosmetic retries of these contracts. Do not promote
this diagnostic into production or infer impossibility of Haiku in every design.
The next proposed architectural fork is bounded verification of specific
contradictions with an explicit spatial/ownership contract (strategy 3), not an
unlimited loop or a per-object second full Analyze. This changes the model-call
topology and needs an owner decision before production adoption. Strategy 1 stays
deferred, and materials-only / Haiku / immutable Detection boundaries remain.

Full local verification: 1717 passed, the same 10 pre-existing failures,
29 warnings, 16.60 s. A final candidate-ambiguity guard preserves distinct line
interpretations instead of selecting the first; its extra regression test brings
the new relation/constraint/provenance tests to 16, plus 5 CLI mode-validation
tests. Final affected relation/replay files: 26 passed in 1.95 s; offline LF1
reconciliation still applies. This validates diagnostic safety, not model acceptance.
Production checkpoint remains V5.8.2; comparison base is local WIP 4fd40d9.
Existing unrelated 50-line TODO changes are preserved outside this commit.

#### 2026-11-05: approved conditional verification, trials 38-42, not accepted

Owner approved implementing the conditional third Haiku request. Same work
3.17.4.5, materials-only, no Detection mutation, manual template library or
stronger production model. Intended topology: one shared Analyze, Calculation
per object, and at most one short review only when deterministic checks detect
a contradiction. This is not three mandatory calls for every object; the
existing Calculation batching/reconciliation can itself use more than one
provider request for larger evidence packs.

Implemented `use_cases/estimation_geometry_verification.py` and
`agents/estimation_geometry_verification_agent.py`. Triggers: disagreement with
view directions, incompatible dimension axis, or source numeric mismatch.
They do NOT cover all wrong materials, counts, hidden parts, or plausible
same-axis selection of another component's dimension. Reviewer must return
exactly one source-ID patch or explicit unresolved reason per target. Code
copies the candidate numeric value, rejects extra targets/fields and invalid
axis choices atomically, preserves all non-target fields, and reruns conflict
checks. Patches stay estimating assumptions, never independently verified source
dimensions. Raw responses and short decision rationales are recorded, not
private model thinking.

Bounds: 8 targets, 3 object-owned pages, 24 candidates per target, 20,000 context
characters, 6 detail crops, 1600 output tokens, 30 s hard timeout, zero SDK
retries. Model is fixed to `claude-haiku-4-5-20251001`. Missing evidence, foreign
input identity or exceeded caps makes no request. An unchanged extraction with
an attempted review cannot request again; changed geometry is marked for review,
not silently retried. Failure retains original geometry. Returned-response
usage is recorded separately even if its patch fails validation; timeout before
a response cannot establish actual billed usage. The existing hard-timeout
helper does not guarantee cancellation of an already-running remote request.

Initial integration was after Calculation and before 2VN, with a changed facts
cache version and separately persisted usage/audit. These runtime changes were
WITHDRAWN after live failure. Final code is CLI-only, opt-in via
`--geometry-verification`. Normal Calculation, production cache version, runtime
and UI are byte-identical to pre-experiment HEAD d6f9b60. No new worker, poller,
timer, interaction or production latency was introduced. The failed automatic
patch approach is not a new verified checkpoint.

Immutable input `db175c9d-b911-434e-a3ed-de612640f96f`, run
`run_1cba0b2491dc413c9a3be2fdd526226b`, company 610/object-001.
Witness paths: `/private/tmp/estimation-v6-lf1-witness-NN.json`.

| Trial | Intervention and actual result |
| --- | --- |
| 38 | Reuse Analyze/Calculation 35; new review 3.878 s, 6988 input / 257 output tokens. Two patches accepted as assumptions, but countertop width 1580 instead of 1600 and false attribution of printed 40 to support. Zero detected conflicts is not semantic acceptance. Total 5.09 s excludes original Analyze/Calculation. |
| 39 | Fresh Analyze 35.471 s + Calculation 31.873 s + review 5.644 s; total 74.26 s. Reviewer selected a height-only source for countertop depth. Entire patch rejected, original geometry retained, needs_review. Analyze also retains wrong material/thickness/support/member interpretation. |
| 40 | Exact cached 39 Analyze/Calculation, only review changes. Offline preflight confirmed two conditional projection corrections and six targets. Source scope preserved; reviewer gets copied reconciled projections with old ownership withdrawn, role/ID rather than first-reader shape/count narrative. New review 6.043 s, 8192 input / 526 output tokens; total 7.23 s. Still chooses 190 countertop width, 720 depth and 2650 screen height with false physical justifications. One unresolved thickness, status needs_review. Failed physical-ownership gate. |
| 41 | After withdrawing production integration: cached default replay, 1.03 s, only Analyze + Calculation, no verification audit or paid call. |
| 42 | Same cached input with explicit --geometry-verification, 1.32 s; all three responses reused, zero paid calls. Same geometry as trial 40, still not accepted. |

The final diagnostic retains trial-40 conditional projection context. It is a
hypothesis, not a source correction, and cannot mutate the authoritative scope.
Missing coordinate-frame metadata conservatively yields no relation candidates.
Reproduction of 42: run `python -m tools.replay_estimation_v6` with this input ID,
`--replay /private/tmp/estimation-v6-lf1-witness-40.json`,
`--geometry-verification`, the established local secrets file, and a new output
path, WITHOUT `--execute`. `--fresh-provider --execute` deliberately bypasses
provider-response reuse while retaining immutable input/catalog/page snapshots;
it is only for explicitly paid full-cycle validation.

Conclusion: bounded review and axis restrictions prevent some contradictions,
but the hypothesis that this short repair selector produces an acceptable LF1
estimate is rejected by these trials. More confident prose or agreeing model
readings do not establish physical ownership. Stop this prompt-only loop.
Next proposal, not an approved contract change: test explicit source-local
component boundaries and dimension-to-boundary attachment before numeric choice,
within the existing evidence-first workflow, not a default fourth request.
Material selection, count/shape errors, full LF1, legends, multi-object scaling
and owner-visible assumption review are still unaccepted/unverified.

Final verification: 1740 passed, same 10 known baseline failures, 29 warnings,
16.26 s. Tests cover atomic allowlists, zero-call paths, caps, timeout/malformed
usage, input isolation, immutable scope, no repeated review, and normal
Calculation's exclusion of the unaccepted verifier. The default/opt-in cached
witnesses additionally verify real local orchestration without new paid calls.
No database writes, push or deploy. Production checkpoint remains V5.8.2.
Preserve the unrelated 50 TODO lines outside the experiment commit.

Owner explicitly approved this change on 2026-11-04: simplify the model-facing Analyze
contract to semantic assemblies, material intent and source observations.
Keep one shared Analyze plus per-object Calculation and the existing persisted
construction/BOM/Engine contracts. Extend the deterministic compiler to derive
layer count, required edge width and default role expansion, rather than asking
Haiku to redundantly specify all mutually dependent purchasing/construction
fields. Preserve explicit overrides, source constraints and recorded assumptions.
The model still owns visual interpretation; deterministic code cannot establish
an unseen material or correct a wrong drawer/slat count without evidence.
No guarantee of Haiku acceptance is inferred from the approval.
Implementation in progress: semantic zone/material intent is compiled into the
existing construction scope. Source numeric thickness references are converted
by the existing unit guard; visual same-thickness relationships remain assumptions.
Exact stock/layer multiples and edge widths are calculated, hidden components
reuse single-layer stock, and painted MDF creates a scoped finish demand.
Explicit source stock, linked legends and unknown-material family escape routes
remain available. Cyclic thickness references and incompatible stock fail.
Witness 20 does not establish correct visual semantics. Do not continue cosmetic
prompt retries or override the witness with LF1-specific counts/materials.
The subsequent evidence-first experiment above isolates the remaining
visual-to-geometry interpretation from deterministic stock/layer expansion.
Local compact-contract verification: 36 focused semantic/construction/replay
tests passed; full suite 1683 passed, the same 10 baseline failures and 29
warnings. Explicit 20-mm and 40-mm stock both preserve a 40-mm finished member,
with two and one layers respectively. This verifies compiler arithmetic, not
Haiku visual selection, source ownership or production acceptance.

Source/assumption rationale is retained in facts/capsules. An owner-visible
UI inspection path for the new rationale has not been verified; relevant
Object Detail renderers do not directly reference the new rationale fields.
Any UI change needs the established scenario agreement and live interaction
verification; no UI patch is included in these experiments.

Additional deterministic checks: contradicted numeric thickness citations lose
source authority without silently changing chosen stock; assumed edge width
must cover the finished panel thickness, not just one laminated layer. Explicit
source edge-width contradictions fail. The existing numeric/projection 2VN
guards are not weakened to make a witness pass.

Inspection confirmed source OCR/view coordinates use the 200-DPI frame
(3307 x 2339), while the saved page image is 1985 x 1404. Previously neither
Analyze nor Calculation described this mapping. Evidence presentation now
includes the documented source frame, normalized view boxes and bounded
same-source detail images (12 per request maximum). Unknown frames never
authorize a crop. This changes presentation only, not Detection membership.

The 04 Calculation received 18,231 input tokens; its scope alone was 29,195
JSON characters because material descriptions were repeated per role. The
geometry handoff now supplies one palette plus compact role assignments.
Full provenance, economic alternatives and immutable facts remain in the
authoritative plan. No additional model call or background activity is added.

Two deterministic contract repairs have focused tests: malformed V6 front
groups fail instead of silently becoming stacked; an explicitly fixed,
zero-front decorative facade with panel groups uses the fixed-panel composer.
Hinged or drawer-bearing facade groups still fail. An inconsistent assumed
finished thickness follows selected stock layers with a recorded correction;
source/derived contradictions fail rather than rewriting source authority.

Production defaults and timeout are still unchanged. Neither prompt refinement
nor evidence crops have yet established a passing LF1 gate. Strict-schema
transport was rejected twice and removed, not promoted. Adaptive thinking also
has no accepted witness. Replay 12 isolates a bounded thinking allocation from
the answer allocation, keeping the same source and Analyze prompt. The CLI-only
option does not change the production route. This deprecated but still supported
Sonnet 4.6 option is diagnostic, not a future-proof routing decision:
https://platform.claude.com/docs/en/build-with-claude/extended-thinking.

Calculation now has a V6-only geometry prompt, including dimensions for each
locked panel group; the legacy prompt remains intact. Legacy same-run inputs
share source context at read time so a separate-page legend remains traceable
in each object's composer. Object-owned geometry and immutable records are
unchanged. Focused construction/evidence/replay/scope/BOM/2VN tests: 37 passed,
including V6 versus legacy prompt routing. Before compact/evidence-first changes: 1674 passed,
the same 10 baseline failures, 29 warnings, 10.60 seconds. No new failing test.

Owner emphasized compact latency for ten objects with 3-4 islands each.
Agent-proposed, not approved SLA: <=60 s for a simple single object and 2-3 min
for ten ordinary objects, with a compact shared Analyze and bounded parallel
Calculation (suggested concurrency 3). Current Calculation remains serial.
At the measured 35 s/object, ten serial calculations alone imply about six
minutes; this is an extrapolation, not a ten-object benchmark. Parallel
orchestration and incremental UI publication require agreement on the tradeoff
and preservation of cancellation, write ownership and accepted navigation.

Owner clarification after the latency discussion: remove the hard proposed
time budget and finish the functionally correct cycle first. Routing and
parallelism are deferred, not acceptance prerequisites. Efficiency still means
no redundant paid calls or repeated payloads; all necessary bounded functional
replays remain authorized. No production route is selected solely by latency.

Pending acceptance: a real LF1 model witness, then a multi-object / separate
legend witness, followed by authenticated production behavior and owner review.
Large-file latency and actual model interpretation are not established by
mocked orchestration tests. No global-optimum or usable-offcut claim is made.
