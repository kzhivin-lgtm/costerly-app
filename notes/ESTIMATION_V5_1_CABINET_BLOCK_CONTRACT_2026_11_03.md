# Estimation V5.1 Cabinet Block and Hardware Contract

Status: implemented locally, pending production witness

Work number: `3.17.4.4`

V6 continuation (3.17.4.5), 2026-11-05: see
`notes/ESTIMATION_V6_2_FRONT_COUNT_CHECKPOINT_2026_11_05.md`.
Front-count r03 is an accepted provisional interpretation experiment, not a
replacement for this downstream construction/hardware contract. Its known
false doors are not certified material demand. The 1000/2000-mm owner hinge
revision below is tested locally and is not claimed deployed by this checkpoint.

## Shared Cabinet Block rulebook, V6 experimental consumers

One rulebook with two sections, not two mandatory new provider stages:

- **CB Front V1** (protected checkpoint): front interpretation/counting and hardware mapping. This
  is the short display name for the exact selected technical prompt
  `estimation_front_count_v6_2_r03`, not a new prompt or renumbered experiment.
  Source: agents/prompts/estimation_front_count_v6_2.md. Historical r01/r02/r04
  identities remain unchanged. Runtime registry: CB_RULEBOOK in
  agents/estimation_understanding_agent.py.
- **CB Front V2** (owner-selected diagnostic, technical r05): agents/prompts/cb_front_v2.md.
  Same Front pass/evidence, adds tabletop_supports with distinct physical legs,
  support scheme and observed-versus-assumed attachment. One visible leg is not
  proof of one total leg. Use all views; common schemes are clues, not count
  defaults or width cutoffs. Leg boxes/IDs are separate from operating fronts
  and totals; hidden inferred legs require uncertainty, not invented boxes.
  Old r03 and r04 identities remain unchanged. No extra production stage.
  V2 is now the default for --count-fronts; --front-supports explicitly selects
  the same version. --front-v1 replays unchanged protected r03.
  Lev1 twice identifies two legs, retained by Planner. Planner grouping varies
  two then three blocks; repeated V1 yields three. Simple grouping dependency
  is not reproduced. Owner accepts either grouping when coverage is preserved.
  Lev1 enum reliability remains open. Lev2 exact enums pass, five drawers/two
  lift-ups retained, no invented legs; 15 hinged plus two unresolved is not
  exact semantic acceptance. Subsequent Planner response truncated at 6000 tokens.
- **CB Planner V1**: proposed chat draft, not executed. It included detailed
  internal-compartment/shared-part reasoning. Owner requested simplification.
- **CB Planner V2** (retained experiment): agents/prompts/cb_planner_v2.md. Group into large practical
  preassembled units, balancing assembly effort against manageable transport.
  No invented hidden partitions, detailed panels, materials or labor. Receives
  original images plus fallible saved Front output. Short blocks/shared-parts
  list with referenced fronts and image-local review boxes. Assembly boundaries
  and transport suitability remain assumptions unless explicitly established.
- **CB Planner V3** (retained diagnostic): agents/prompts/cb_planner_v3.md.
  Same contract/model/evidence as V2. Owner-approved grouping guideline: up to
  three horizontal front positions, four only with a specific reason; vertical
  stacks are not summed, and a corner shares the allowance across both wings.
  Full-height narrow cabinets remain possible. No hard minimum width. Explicit
  source construction takes priority. Always list a worktop separately, once,
  either as its own block or as a shared part spanning several carcasses.
  The front-count grouping limit does not apply to worktops/decorative panels.

- **CB Planner V4** (current diagnostic candidate): agents/prompts/cb_planner_v4.md.
  Same contract/evidence/settings as V3. Identify full-height, exactly
  one-section-wide columns first, keeping vertically stacked content together.
  Do not bridge separate wall/base cabinets or infer a column from a fixed side.
  Lev2 B06 grouping improves and original contract passes, but false B01 tower,
  U-shaped summary and incomplete physical content prevent full acceptance.
  Lev1 follow-up preserves three groups but still reports one leg and invents
  mm units for bare drawing dimensions. Planner schema passes, semantics do not.

Full research checkpoint: notes/ESTIMATION_V6_2_HSL_N68_CHECKPOINT_2026_11_05.md.
Additional owner-requested Front V3 + Planner V7 snapshot, PARTIALLY COMPROMISED:
notes/ESTIMATION_V6_2_FRONT_V3_PLANNER_V7_PARTIALLY_COMPROMISED_CHECKPOINT_2026_11_06.md.
Known failures retained, defaults unchanged. B08's drawer/door grouping is
permissible; its localization is wrong. Preservation is not semantic acceptance.

2026-11-06, 3.17.4.6: owner approved CB Parts V1 INSIDE Calculate. Product target
remains one shared Analyze plus one Calculate per object, not three stages of
model calls. Front/Planner are logical Analyze responsibilities; their recent
separate research calls do not establish this integration. The opt-in Parts
route bypasses legacy Calculate batching/reconciliation and makes one request.
Estimate large panels only, no gaps/clearances/joinery. LDSP 17 mm is the fallback
when no contrary material/thickness evidence exists. Specific thickness overrides
locally; 40 mm can be an explicitly assumed two-layer 20 mm construction.
Use compact part groups, front/block IDs, arithmetic face dimensions, explicit
assumptions. Shared partitions/worktops once. Drawer body expansion uses the
slide-depth helper (720 -> 600), five panels per box, facade separate. No arbitrary
backing/drawer sheet family. No labor, catalog selection, prices or stock nesting.
Preserve raw replies before validation; 2VN checks envelope axes, not proof of
individual panel topology. Coarse panel faces retain assumption provenance.
Code: agents/prompts/cb_parts_v1.md, use_cases/estimation_cb_parts.py.
The protected V3/V7 checkpoint, normal V2/V4 defaults and legacy route remain.
CB Parts V1 is NOT ACCEPTED: all three initial Lev2 trials fail. Disabling
thinking changes output completion (16.921 s) but yields invalid JSON and
wrong unit/front-size semantics. Do not describe synthetic contract tests as
visual/material acceptance. Next revision remains a proposal in TODO.

OWNER OVERRIDE, same 3.17.4.6: CB Parts V2 now returns ONLY block/shared ID,
part name and quantity. Dimensions/materials/2VN/expressions/explanatory output
are deferred, not part of this call. It stays inside Calculate, with the same
whole-object visual evidence and fallible saved plan. Count conventional drawer
panels without also charging a drawer-box assembly; shared partitions/tops once.
First Lev2 run: 5.676 s, format PASS, semantics NOT ACCEPTED (no partitions,
unverified shelves and extra B09 door). Raw answer unchanged in
notes/evidence/cb-parts-v2-2026-11-06/lev2-counts.json. V1 retained explicitly.

Owner review after V2, 2026-11-06, same 3.17.4.6:
- The discussed B08 coarse quantities are acceptable with one missing shared
  internal vertical divider added between its drawer bay and adjacent door bay.
  Conventional side-mounted drawer runners need mounting walls on BOTH sides
  of their bay. At an internal bay boundary, use/count one shared wall, not two.
  Existing outer sides and previously counted partitions are not additional
  walls. A vertical drawer stack shares its side supports; no divider per drawer.
  A single drawer bay enclosed by two outer sides needs no extra divider solely
  because it contains drawers. Explicit alternative construction takes priority.
- Future geometry fallback: about 600 mm between the TOP of the worktop and
  UNDERSIDE of wall cabinets, when source dimensions are absent and context
  supports it. This is an owner-approved estimating assumption, not source proof,
  a mandatory installation standard or a rule for every furniture type.
- Lev2 contextual derivation: assuming aligned tops, 2650 - 1150 - 600 = 900 mm
  is the estimated WORKTOP TOP elevation. Do not automatically make carcass
  panels 900 mm high and then add the plinth/worktop on top of that again.
  The clearance/alignment assumptions must remain visible in future calculations.
- Previous B08 1100/800/etc. dimensions were an assistant estimate, NOT a model
  response. V2 remains quantity-only. No dimension-model acceptance is implied.
These decisions are recorded for the next numbered prompt update. V2 raw
output, selectors and protected checkpoints remain unchanged in this iteration.

Latest owner clarification, same 3.17.4.6: the final CB Parts result must be
the practical part list WITH quantity and dimensions, across all project
objects and their blocks. V2 count-only was a bounded intermediate experiment.
The manual assistant-sized B08 list is a format/abstraction example, not proof
of model geometry capability. Model output must be reviewed independently.
New estimating default: WORKTOP finished thickness 30 mm if no specific value
is supported. Explicit/contextual 40 mm or other thickness overrides that
fallback. Ordinary LDSP panels remain 17 mm by default. This rule chooses
neither the worktop material nor its stock/lamination route. It is an owner
cost-estimating assumption, not a universal material/manufacturing standard.
Maintain one document Analyze and one Calculate per object; combine their
lists in code. Proposed CB Parts V3 adds coarse sizes to the compact list,
including the approved internal divider and the conditional 600 mm clearance
assumption. No new prompt, selection change or paid run is made in this note.

CB Parts V3 implemented/tested with owner approval, same 3.17.4.6:
One opt-in Calculate call per object, full evidence, compact named part rows
with quantity, face size, thickness and approximate flag. Per-block explicit
unit and short assumptions; code converts mm/cm/m, applies null-thickness
fallbacks (17 panel, 30 worktop) and computes drawer_depth using the existing
helper. Raw response is immutable; normalized rows are separate. Model-returned
thickness is unverified, not an automatically proven source fact. No material
selection, stock lamination, hardware or labor in this contract. V1/V2 retained.
Initial Lev2 trial uses exactly the V2 images and upstream plan: 16.529 s,
4498 output tokens, all blocks covered. B08 divider fixed, but geometry NOT
ACCEPTED: whole block 600 mm, equal 300 mm door/drawer bays, three equal 220 mm
fronts; unsupported generic 720 mm carcass height. Do not correct these by hand
or present them as source facts. B09 extra door persists, V2 B08 shelf omitted.
Evidence: notes/evidence/cb-parts-v3-2026-11-06/lev2-sized-parts.json.
This does not establish all-object orchestration, visual accuracy or production
readiness. Protected upstream checkpoint and Front/Planner defaults unchanged.

CB Parts V3.1, same 3.17.4.6, owner-approved one-paragraph experiment:
Use labelled span endpoints and proportional visible intervals, including
neighbouring blocks, to estimate and sum block/bay widths; record a short
allocation in the existing assumptions field. No fixture-specific numbers,
new schema, extra call or correction of the saved Planner box. Explicit replay
only; V3 remains the diagnostic default. First Lev2 trial 13.439 s: format PASS,
geometry FAIL. Door and drawer widths each 500 mm but whole B08 also 500 mm;
divider omitted, equal-height drawer fronts persist, allocation not supplied.
One run does not establish causal attribution or stability. Original raw output
preserved in notes/evidence/cb-parts-v3-1-2026-11-06/lev2-sized-parts.json.
The width problem is unresolved. An explicit bay/sum contract is only a next
proposal requiring approval, not implemented here. Production unchanged.

Owner clarification after this trial: equal subdivision is acceptable for
unclear interval sizes at this coarse-estimation stage. Precise visual ratios
are not an acceptance requirement in that case. Keep the overall dimension
constraint and additive consistency across adjacent bays/blocks. This does not
verify the particular 500 mm values or accept a 500 mm block containing two
side-by-side 500 mm bays. Existing raw evidence remains unmodified. The omitted
mounting partition is a separate unresolved defect, not an approximation choice.

CB Parts V3.2, same 3.17.4.6: approved generic reminder that same-run adjacent
bay widths sum to whole carcass width, stacked drawers count as one bay,
whole-width panels follow that sum, and one shared mounting wall is listed at
the drawer/adjacent-bay boundary. Equal subdivision allowed if ratios unclear.
Existing schema/arithmetic unchanged, no additional model stage. One full Lev2
trial: 15.041 s, format PASS, partition restored once, sum FAIL (500 mm block
with 500 mm door plus 500 mm adjacent drawer bay). Requested sum not explained.
Not accepted or promoted. Two unsuccessful width-comment trials require a new
diagnostic, not further blind prompt variants. The known conflicting B08 box
is a candidate input cause, not a proven explanation. Raw response preserved at
notes/evidence/cb-parts-v3-2-2026-11-06/lev2-sized-parts.json.

Owner accepted approximate equal allocation and the interpretation of adjacent
500 mm bays as about 1000 mm total, then requested a checkpoint. Before it was
created, owner requested two more identical V3.2 trials to check stability.
Across three identical requests: B08 bay widths 500/600/760 mm; whole block
incorrectly equals one bay in all three. Shared partition 1/0/1; door count 1
and drawer fronts 3 stable. Trial 3 uses a narrow top stretcher, not full top.
Times: 15.041/14.519/15.339 s. Stability is not established; do not call this
a verified complete geometry checkpoint. No tag/archive/default change created.
Raw repeat evidence: notes/evidence/cb-parts-v3-2-2026-11-06/three-run-repeatability.json.
The owner-approved coarse approximation is preserved, not retroactively revoked;
acceptance of the newly observed variability awaits owner review.

## CB Parts V3.3 approved architecture experiment, 3.17.4.6

Context: V3.1/V3.2 independently generated block and part dimensions, allowing
adjacent 500 mm bays inside a 500 mm carcass and optional mounting partitions.
Two comment revisions did not resolve the repeated width inconsistency. Owner
approved testing the conflicting locator, then moving arithmetic/construction
invariants to code without another model call or a furniture-template library.

Decision: model identifies ordered side-by-side bays, their widths, stacked
front IDs/heights, drawer body heights and shelf counts. For a straight
rectangular carcass, `compose_cb_bay_parts` derives total width, two outer sides,
full top/bottom/back, each front, five body panels per drawer and shared mounting
walls. Each boundary adjacent to a drawer bay gets one wall, not two. Stacked
drawers count once for bay width. Adjacent door bays do not automatically add
walls. Group only identical part geometry. 17 mm ordinary/30 mm explicit-worktop
fallbacks retained; material purchasing and lamination remain outside scope.
Front type/membership remain the saved fallible upstream scope, not reclassified.

This is explicit coarse construction, not source-proven joinery. Straight bay
widths are not summed around corners. Nonrectangular, stepped or free parts use
the `explicit` branch and remain model-authored/unverified. The full top/back
assumption is visible in derivation metadata. One shelf count per bay is a
model assumption, not a guarantee of actual shelf span/support design. Missing,
duplicate or foreign blocks/fronts are rejected. Numeric size repairs are not
performed. Whole-object height inconsistency fails validation; per-block audit
reports do not convert failed objects into accepted incomplete estimates.

Alternatives retained: previous prompt-only sized rows remain replayable;
template libraries and extra vision/reviewer calls are not introduced. The
normal V3 diagnostic default and existing Front/Planner selectors stay unchanged.

Verification: one V3.2 locator-only ablation failed coverage (missing S01) and
returned B08 bays 300+300 mm. This is not proof that the locator has no effect.
Two identical V3.3 requests with the original locators: B08 isolated audits
derive 900 and 800 mm, one mounting divider each, correct common-panel width.
Whole replies fail B02 height (1600 mm stack in 1210 mm carcass; 1940 in 1840),
second also fails B06 (1150 facade in 750 carcass). First B06 uses 720 instead
of printed 1150, showing arithmetic validity is not evidence validity. Times
8.190/9.282 s; 2210/2412 output tokens. Raw evidence:
notes/evidence/cb-parts-v3-3-2026-11-06/locator-and-bay-trials.json.
No production acceptance, automatic correction, new checkpoint or deployment.
Next source-height/vertical-consistency work is a proposal pending direction.

Owner benchmark corrected on 2026-11-06: N68 TEN door-like fronts and SIX
drawers, superseding the earlier eight-door/four-drawer confirmation. Ten
comprises five tall, two under sink, one downward-opening dishwasher front,
and two in the tall appliance column. It is not a ten-cabinet-hinge benchmark;
appliance-front hardware is not established by the rectangle count. The five lift-up
fronts inferred from triangular marks are not accepted as gas-lift demand.
2026-11-06: CB Planner V7 is a tested but unaccepted candidate. Owner specifies full
base-run top coverage, full depth to the wall, not the hanging-shelf depth.
This is an estimating default subject to explicit construction, not a universal
furniture fact. Complete carcass localization must not be reduced to front-box
union. Raw N68 V6 contains four drawer IDs in B06, but the owner confirms six:
two lower drawers are omitted already in Front. Box expansion alone cannot
correct the count. Reconcile repeated sections before declaring an assembly.
Owner's crossed-region clarification requires revisiting the earlier column
omission claim; it is not permission to add a duplicate block or promote V6.

CB Front V3 candidate reads drawer stacks through the bottom, allowing taller
lower fronts and requiring visible reasons for plinth exclusions. N68 replay
finds all six drawers with boxes, but only seven of ten door-like fronts and invalid
island enums. Planner V7 consumes that raw response, then truncates at 6000
tokens; worktop coverage has no accepted result. Selected defaults remain
Front V2 + Planner V4. Evidence: notes/evidence/hsl07-v62-2026-11-06/n68-front-v3-planner-v7.json.

CB Front V4 (location before classification, same schema) was tested once on
unchanged N68. Rejected: five of ten target door-like fronts, four of six
drawers, three unsupported lift-ups and invalid island enums. No Planner call
or promotion. Evidence: notes/evidence/hsl07-v62-2026-11-06/n68-front-v4.json.

Owner rollback, 2026-11-06: stop Front V3/V4 experiments, retain unchanged
Front V2 / Planner V4. Exact-request Lev2 V2 repeat gives five drawers, two
lift-ups, 18 hinged doors and invalid island enums, versus previous 15 hinged
and two unresolved with valid enums. Rollback does not establish reliability.
Evidence: notes/evidence/cb-front-v2-2026-11-06/lev2-rollback-repeat.json.
Three later owner-approved identical-request controls return respectively
(drawers/hinged/lift-up/unresolved) 5/17/2/1, 5/16/2/1, 2/11/2/0. The third
omits the entire perpendicular-wing front set due to possible overlap, while
still recognizing that island as a front elevation. Exact-enum validation
passes twice, fails once. No semantic acceptance or changed default.
Evidence: notes/evidence/cb-front-v2-2026-11-06/lev2-three-controls.json.
CB Front V5 adds only an explicit physical-front match requirement before
deduplicating across views, directly on V2. One Lev2 trial retains both wings
and returns 5 drawers, 16 hinged, 2 lift-ups, 1 unresolved, valid format.
Known side/opening false positives remain. V2 had already produced this same
outcome in control 2, so efficacy/reliability is unproven. Candidate only;
defaults unchanged. Evidence: notes/evidence/cb-front-v5-2026-11-06/lev2-identity-trial.json.

Three later owner-approved Lev2 Front V3 + Planner V7 pairs retain 17 hinged,
5 drawers and 2 lift-ups in all Front responses, but only one Front passes
exact enums. Planner truncates twice; the third returns 9 blocks + S01 but
has incorrect block coverage and incomplete worktop bounds. No pair passes
both format stages, no semantic acceptance or promotion. Evidence:
notes/evidence/lev2-v3-v7-2026-11-06/three-paired-runs.json.

CB Planner V5/V6 are retained diagnostic candidates, not selected defaults.
V5 localizes worktops on top/axonometric views. V6 also caps tall blocks at
two tall door leaves across without relaxing one-section-wide columns.
N68 V6 follows both rules but omits a previously represented appliance column;
the diagnostic default remains V4. Exact evidence and review are in
notes/evidence/hsl07-v62-2026-11-05/n68-planner-v5-v6-evidence.json.

Planner V2 failed semantic review. Owner has now accepted abstract segmentation
on the examined simple objects, including alternative two/three Lev1 groupings.
V3/V4 are still NOT verified full-cycle/runtime checkpoints; latest Lev2 truncation
and classification limitations remain open.
V3 first probes improve grouping (Lev1 three blocks; Lev2 nine + worktop), but
retain physical interpretation errors; Lev2 additionally fails front ownership
validation. These are recorded failures/limitations, not patched outputs.
One Planner call per probe consumes an existing Front witness without rerunning
Front. Production Analyze/Calculation orchestration is unchanged. Keep per-run
Front IDs local and record conflicts explicitly rather than dropping them.
The full live results and limitations are in the V6 design record and TODO.

## Scope

V5.1 starts at the immutable `estimation_input_v4` package. Detection identity,
evidence and navigation remain outside its scope. The active path is:

`immutable input -> Dimension Evidence Graph -> Cabinet Block interpretation -> Dimension Resolver -> Structural and Hardware Composer -> Material Engine -> C/I/A`

The graph retains its evidence-only boundary. It supplies source numbers,
native-vector candidates, views and candidate relations. It is not a finished
shop drawing and does not choose a catalog or price.

## Approximate, non-blocking construction rule

An approximate estimate must not stop because an input is incomplete. Every
required block axis resolves in this order:

1. Exact explicit source value.
2. The only source-supported shared axis among compatible cabinet blocks in
   the immutable object.
3. A versioned construction default.

The output records the resulting basis and reason. Peer inference remains
`derived` and retains its source refs. A construction default is `assumption`
and has no false source refs. V5.1 defaults a missing cabinet width, height or
depth to `600`, `720` or `600 mm` respectively. These are estimating defaults,
not production measurements.

Where thickness is not explicit, visible MDF/HDF and hidden LDSP carcass sheet
both default to `18 mm`; backing defaults to `3 mm`. Explicit source material
always overrides a default.

## Cabinet Block

One physical cabinet block carries its envelope, front topology, exposure and
material policy. The visual stage may emit `front_groups` only as:

- `drawer_front`, stacked or side-by-side
- `hinged_facade`, stacked or side-by-side
- `lift_up_facade`, stacked or side-by-side

Only the canonical elevation counts fronts. A perspective can corroborate a
front group but cannot duplicate it. The deterministic composer turns the
block into hidden carcass, backing, conventional drawer structure, visible
fronts and exposed side panels. It does not produce a fabrication cut list.

Visible fronts and declared exposed carcass ends use `visible_sheet`, while
hidden carcass, shelves and drawers use `internal_sheet`. Backing and worktops
are separate demand roles. Paint remains a separately named finish demand
under the established one-standard-set policy until a consumption model is
approved.

## Hardware Block

Hardware belongs to its Cabinet Block and is derived only from front topology:

- Each `drawer_front` creates one `hardware_drawer_slide` purchase **set**.
  Its `depth_mm` is `floor((cabinet_depth_mm - 100) / 100) * 100`.
  `720 mm -> 600 mm`; `650 mm -> 500 mm`.
- Each `hinged_facade` creates individual `hardware_hinge` demands. Owner
  revision 2026-11-05 uses `<=1000 mm: 2`, `>1000 mm: 3`, `>2000 mm: 4` hinges.
  This supersedes the original V5.1 600-mm threshold; exact 2000 mm gets 3.
- Each `lift_up_facade` creates one `hardware_lift_system` purchase **set**.

The visual model recognises physical fronts and their arrangement. The
deterministic Composer applies the rules. The Resolver and Material Engine are
still the sole catalog and price authorities.

## Protected behavior and witness

V4.29 New Estimate navigation and all Detection contracts are protected. V5.1
does not require a schema migration because it retains the existing
`estimation_assembly_bom_v1` persisted envelope and publishes a fresh agent
version, `estimation_assembly_bom_v5_1`.

Local acceptance covers Lev rules in deterministic composition:

- Lev_1: three stacked drawers at 720 mm depth create three 600-mm slide sets.
- Lev_2-style cabinet topology: five drawers at 650 mm create five 500-mm slide
  sets; three 1100-mm hinged facades create nine individual hinges; two lift-up
  facades create two gas-lift sets.
- Missing cabinet depth is derived from the sole source-supported peer depth,
  otherwise a named construction default is used without discarding the block.

Production acceptance remains separate. It requires one owner-approved
cabinet/kitchen input to reach a persisted V5.1 BOM and C/I/A-priced Material
Plan, followed by inspection of front counts, hardware units, depth specs,
assumptions and terminal Object Detail. The V4.29 authenticated navigation
witness is still independently pending.
