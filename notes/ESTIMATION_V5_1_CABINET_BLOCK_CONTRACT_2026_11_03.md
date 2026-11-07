# Estimation V5.1 Cabinet Block and Hardware Contract

Status: implemented locally, pending production witness

Work number: `3.17.4.4`

## Current owner clarifications, 2026-11-07, Estimation V7.2 review

Continuation work is 3.17.4.6. These decisions update the contract; runtime
changes and a new model trial have not been made in this review iteration.

- Kitchen base cabinets at the lower working level are covered by a worktop
  over the complete base footprint. High cabinets and wall-hung cabinets are
  excluded from that footprint; the worktop stops before a full-height unit.
  A sink opening does not remove coverage of the rest of its cabinet.
  This refines the existing CB Planner V7 worktop-extent rule, not a new tool.
- For an unspecified KITCHEN worktop, choose artificial stone as the material
  estimating default and 30 mm as finished thickness. This supersedes laminate
  chipboard as that kitchen fallback. Source-specified material takes priority.
  Artificial stone does not assert quartz, brand or a particular catalog item.
  Ordinary unspecified panel material remains LDSP 17 mm. This does not force
  artificial stone for every table or every non-kitchen top.
- A 40-mm finished veneered element may be estimated as two 20-mm stock layers
  when explicitly chosen as a construction assumption. Finished thickness and
  purchased stock/layers remain separate. The bare source mark 20 (normalized
  by Detection to 200 mm in Lev1) is not evidence of 20-mm stock thickness.
- Show measurement normalization in the Islands display from saved Detection
  data: original notation/unit, target mm, whether conversion was required,
  and declared/inferred unit basis. Example 265 cm -> 2650 mm; a source mm
  value is retained unchanged. Image-only islands may have no dimensions.
  Do this deterministically; do not ask the model to infer/convert units again.
- Location names must be anchored to island and physical location (for example
  base cabinets on V3, left section), not unexplained long arm / return wing.
  Corresponding appearances remain one physical part/front across islands.

Current owner Lev2 benchmark, replacing the older optional-16-door ambiguity
for the reviewed interpretation: FIVE drawers (3 + 2), FIFTEEN hinged leaves,
TWO lift-up fronts. Hinged breakdown: 4 base before the turn + 4 base after it
+ 2 separate hanging cabinet + 1 upper corner cabinet + 2 tall-column leaves
+ 2 rightmost leaves = 15. Lift-up fronts are separate from gas-strut quantities.
This is evaluation data only; do not put example counts/IDs into generic prompts.

Preferred Lev2 assembly decomposition (owner reference, not a universal block
count): (1-2) two blocks in the first lower run, (3) turn/sink base block,
(4) tall vertical cabinet, (5) right-hand refrigerator-opening structure,
(6) horizontal lift-up wall cabinet, (7) corner wall cabinet with shelves and
one door, (8) separately hanging cabinet. The shared worktop is represented
once in addition to these cabinet blocks, not forced into an eighth/ninth
cabinet or duplicated over every supporting block.

Lev1: owner accepts one combined veneered-panel/base assembly plus a separate
tabletop/support assembly. Two support legs remain required by visual evidence.
17-mm light top was called tolerable in the owner review despite appearing
thicker; this does not change the general 30-mm finished-worktop default.
The returned one-block + single-owner shared element still needs representation
repair: single-owner top belongs in blocks, not multi-block shared_parts.

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

## V3.3 preservation decision after four trials

Owner explicitly requested two additional unchanged trials and immediate full
checkpoint. These yielded B08 bays 350/270 mm and 500/500 mm. Code computes
620/1000 mm and one partition respectively. Across four identical requests,
B08 arithmetic and divider are coherent 4/4; model-estimated widths vary and
full-object validation passes 0/4. Third trial omits B09 and has a drawer-body
height conflict in B02; fourth repeats B02 stacked-height conflict. These facts
do not revoke the accepted equal-subdivision approximation, but prevent a claim
of verified complete geometry or production readiness. No repair/promotion.

Preservation is accepted as a research checkpoint with known limitations:
estimation-v6.2-cb-parts-v3.3-research-checkpoint-2026-11-06.
Full record: notes/ESTIMATION_V6_2_CB_PARTS_V3_3_CHECKPOINT_2026_11_06.md.
It contains exact prompt/request hashes, four-run evidence, private recovery
archive manifest/hash, current selectors and safe continuation. New evidence:
notes/evidence/cb-parts-v3-3-2026-11-06/four-run-checkpoint.json.
Stop at preservation; further dimension/source association work is pending,
not automatically authorized. No deployment has been made for this iteration.

## CB Parts V3.4 approved span-allocation experiment, same 3.17.4.6

Problem confirmed from V3.3: block-local width sums do not constrain the sum of
intervals inside a source dimension spanning several blocks. The model repeatedly
assigned 151 cm to B07 alone and guessed B08 independently. Owner approved
testing an explicit source-span/interval contract, not another prose-only rule.

Model returns width_spans with source label/value/unit, island ID, normalized
endpoints and ordered weighted members referencing block/bay IDs. Anchored bay
widths must be null. Code allocates the dimension total proportionally, records
every interval (including explicitly labelled non-bay areas), converts units,
then invokes the unchanged V3.3 compiler. One bay may use only one allocation
span; overlapping/nested evidence must not allocate it twice. Numeric widths
without a reliable span remain unanchored model assumptions. Invalid references,
duplicate assignments or simultaneous numeric/anchored widths fail validation.
Raw answers are immutable; resolved widths and their audit are separate.

This guarantees conservation, NOT correct dimension reading or association.
Endpoint coordinates/labels are model-authored and marked unverified. Choosing
the wrong intervals still produces a mathematically consistent wrong estimate.
No extra model call, catalog/template library, Detection edit or numeric repair.

Initial whole-Lev2 trial: 9.270 s, 2415 output tokens, same inputs/settings except
prompt/version. Four span totals conserved. However 151 cm allocated to all B07
doors collapsed into one bay at weight 3 and all B08 fronts collapsed into one
bay at weight 1.3; B08 allocation about 456.5 mm. This regresses side-by-side
topology and remains an unaccepted interpretation. B06 pair also collapsed.
Whole-object validation fails height consistency, no accepted parts emitted.
Raw response and diagnostic allocation in
notes/evidence/cb-parts-v3-4-2026-11-06/lev2-span-trial.json.
Protected checkpoint a9b8df8, prior prompts and defaults unchanged. Further
isolation of span membership on fixed topology is only a proposal, not an
approved architecture change or silently inserted extra production stage.

## CB Parts V3.5 fixed-topology diagnostic, same 3.17.4.6

Owner subsequently approved isolating span association from construction
generation. This supersedes the pending diagnostic proposal above, NOT the
production architecture. Explicit V3.5 opt-in with a saved V3.3 topology witness;
one isolated call, no added automatic Analyze/Calculate stage or default change.

Loader checks exact evidence, original Front/Planner scope and provider reply.
Freeze only block kind/ID and bay/front membership. No widths, heights, depths,
shelf counts, panel sizes or previous dimensional assumptions are transmitted
from that reply. Original images, OCR and Front/Planner context stay intact.
Frozen topology retains source failure/provenance, not certified ground truth.
Model may only return width_spans and positive unanchored_widths with reasons.
It cannot return modified topology or parts. Every carcass bay must be allocated
once. The existing V3.4 allocator conserves totals and rejects overlaps/missing
widths; explicit geometry remains outside this diagnostic. Output status is
cb_width_diagnostic_requires_review, never a complete parts result.

One unchanged-evidence Lev2 trial took 5.256 s (1181 output tokens). The model
assigned 151 cm to all three B07 bays plus both B08 bays, equal weights, giving
302 mm each and B08=604 mm arithmetically. F18/F19 lie entirely left of the
declared span start in the same island; source inspection confirms their
exclusion from that dimension. Door/drawer interval order is also reversed.
Eight unanchored widths are null, so validation rejects the whole answer.
Raw output and unvalidated arithmetic remain separate, no repair or repeat.
Evidence: notes/evidence/cb-parts-v3-5-2026-11-06/lev2-fixed-topology-trial.json.

Conclusion bounded to this trial: topology regeneration is not the sole cause;
span-to-bay association fails even with frozen membership. 248 regression tests
pass, semantic goal unmet. A same-view endpoint/front-interval consistency check
is the next proposal, not implemented or approved. It can detect contradictions,
not prove source dimensions or correct visual geometry. Checkpoint a9b8df8 and
production remain unchanged. Stop prompt variants pending the next decision.

## CB Parts V4: geometry before workshop grouping, same 3.17.4.6

Owner approved direction 1, then direction 2 (measurement preparation), and
rejected worked-example teaching for now. Name is CB Parts V4, not V3.6 and not
an Estimation product-major change. The end deliverable remains a coarse list
of material-bearing sized parts, retained as entities for future labor mapping.

Rationale: workshop/transport boundaries do not necessarily coincide with
drawing dimension spans. V3 local block geometry and V3.5 frozen memberships
did not solve dimension ownership. V4 removes the old Planner scope from the
model context, not the original source evidence or Front identity reference.
One shared Analyze plus Calculate/object remains the target. This opt-in replay
uses saved Front and one Calculate call; no extra Planner/reviewer stage. Saved
Front/Planner probes do not establish integrated Analyze acceptance.

Contract order inside that call:
1. Object material palette with stock thickness, layers, finish/edge intent,
   evidence claim and short reason. Reuse existing family vocabulary. No prices.
2. Independent dimensions with units and explicit source-reading/assumption
   status. Physical straight runs/vertical columns reuse those dimensions.
   Width_ids sum to a complete run extent; bays divide it by relative weights.
   Vertically stacked fronts/openings divide that run's height by weights.
3. Workshop groups select consecutive bays from one run, exactly once. Groups
   cannot assign or recompute bay dimensions. Tall/separate runs stay distinct.
4. Explicit worktops, decorative members and supports reference the same
   dimensions/run axes, not independent repeated numbers. All input fronts
   must remain covered exactly once; their upstream classification is fallible.

Implementation reuses `compose_cb_bay_parts` for conventional carcass panels,
one shared wall beside a drawer bay, and five drawer-body panels. Drawer body
height is an explicit coarse policy: 75% of facade height, capped at 250 mm.
Drawer depth retains existing depth-minus-100 rounded-down rule. These are
assumptions, not newly observed source facts. `build_assembly_bom` retains
part identity, role, quantity, material requirements and existing BOM shape.
V4 adds palette ID, final thickness, name and dependency lineage to each part.
Stock layers derive finished thickness and multiply net sheet area, not finished
part count. Support rows are not sheet area. Net rectangular area is not nesting,
waste or procurement. Edge/finish intent is stored, separate demand not compiled.

This diagnostic does not claim a verified project palette in Analyze. V4 reads
material intent in Calculate because those saved Front inputs do not include
one. Source claims and refs are retained for review but normalized parts remain
assumptions; V4 does not emit verified 2VN dimension ownership. Source readings
cannot be certified by valid IDs or arithmetic alone. Existing 2VN/runtime
behavior and material Engine are unchanged. Production/defaults not promoted.

Verification: 283 relevant tests pass, including regrouping invariance, exact
front/bay coverage, shared dimensions, stacked front/opening height allocation,
material layers and hidden-board separation, explicit supports, no Planner
transport, exact raw capture and no extra call. Three live Haiku 5.5 trials,
identical V4 prompt, source evidence unchanged, no retries or hand repairs:
- Lev2, 12.983 s: 9/24 front IDs missing (including tall column), 151 cm still
  assigned to a whole lower run, unsupported veneered-front source claim.
- Lev1, 8.706 s: 3/3 fronts retained but stacked vertically instead of adjacent;
  cm-scale dimensions treated as mm, decorative enclosure duplicated, foreign
  material refs and zero-thickness/zero-layer support material. Rejected.
- N68, 12.203 s: 5/18 input fronts retained, kitchen dimensions treated as mm,
  source-reading dimension without a printed label and unused material. Rejected.
Full replies and audit:
notes/evidence/cb-parts-v4-2026-11-06/three-object-trials.json.
All ended normally at provider level. None yielded an accepted whole-object
parts list. A schema repair would not resolve the substantive geometry errors.
Stop this variant; no conclusion that the abstract architecture is impossible
or that removing grouping alone caused failure, since the contract also restored
materials and changed representation. Next direction is measured input, with
prior evidence-first failures treated as constraints, not ignored history.

## CB Parts V4.1: measured input, same 3.17.4.6

Owner approved architecture direction 2 after V4 failed. Opt-in only, same
one Haiku Calculate call with unchanged complete evidence and saved Front.
V4 remains reproducible. No model examples, new Detection work or project-wide
material plan introduced. Defaults remain unchanged.

`use_cases/estimation_measurement_packet.py` reuses `build_evidence_map` and its
Dimension Graph/scale policy. It does not introduce another line extractor.
Source labels are linked only to candidate lines with crossings at both ends,
one nearby numeric label, and endpoints inside the actual enlarged image.
Whole chain lines containing several labels are not promoted. Coordinate
conversion uses original source frame, actual overview/detail pixel sizes,
crop margins and generated header. Horizontal Front-centre membership is a
same-image projection, never proof of ownership across levels or projections.
Missing locators/candidates remain unchecked. Raster truncation stays visible.
Max 200 numeric tokens/120000 packet JSON characters, fail rather than silently
discard source data. N68 has 121 numbers and truncated raster extraction.

The new dimension contract has two exclusive shapes:

- Source: `{id,source_id,candidate_id,view_id,reason}`. Code copies source mm;
  candidate may be null, units must have been resolved by evidence/scale policy.
- Estimate: `{id,value_mm,reason}`, visibly assumed, no fabricated source ref.

The resolver rejects extra numbers in source rows, foreign references/views,
duplicate source allocation within a run, and contradictory same-view complete
horizontal span membership/gaps/overlaps. Partial/different-view anchors are
explicitly unchecked, not repaired or certified. V4 composition then expands
the unchanged geometry/parts contract. Original extraction remains untouched;
measurement audit preserves source refs, unit basis and ownership_verified=false.
Copied centimetre-scale values remain policy assumptions if units were not
printed. All final geometry remains subject to V4's unverified-source limits.
No separate finish/edge consumables, pricing or labor is added.

Verification: 325 relevant tests. Three live trials using one identical V4.1
prompt, unchanged evidence, no retry or manual correction:

- Lev2, 8.445 s: valid source IDs and the independent 840/1510 intervals, but
  only 11/24 fronts retained. R2 includes F18/F19 outside its selected 1510
  interval; R1 includes F11 outside its selected width. First validation failure
  is an extra estimate_placeholder field. Independent audit reports the deeper
  geometry contradictions without deleting that field or repairing the reply.
- Lev1, 10.168 s: correct base 1580 x 430 x 720 and three adjacent drawer bays.
  Still a full back panel instead of actual ribs, 1150 mm reused as leg diameter,
  empty source material refs and zero support stock thickness. Rejected.
- N68, 14.628 s: 13/18 fronts retained, all six drawer IDs included, but five
  other fronts missing. Plan dimension 1820 becomes base height, B4/B5 are not
  grouped. Source numbers are correctly copied even where the model's rationale
  says mm or misquotes the source. Invalid material basis also rejects output.

26/26 emitted source references resolve to supplied labels/values. This is
numeric transport acceptance only, not dimensional ownership or parts acceptance.
Whole-object result 0/3 accepted. Evidence and original replies:
`notes/evidence/cb-parts-v4-1-2026-11-06/three-object-trials.json`.
One call per source cannot establish stability or isolate a causal improvement.
Stop combined-contract retries. Proposed next diagnostic isolates ownership
against fixed sections using the new packet, no material/parts generation. That
proposal is not an approved new production architecture or additional call.

## CB Cycle V5: explicit whole-object understanding, same 3.17.4.6

Latest opt-in diagnostic, Understanding V2, 2026-11-06: V1 plus a focus paragraph
excluding non-thickness sizes and explicitly describing supports/visible legs.
--understanding-v2, same evidence/settings, no inherited Front or continuation.
One Lev1/Lev2 call each, 6.044/6.263 s. Lev1 leg count improves in this sample;
thickness attribution and material/unsupported-feature defects persist.
Neither result accepted. No contract promotion or new production stage.
Raw evidence: notes/evidence/understanding-v2-2026-11-06/simple-object-trials.json.

Subsequent owner-approved isolation, 2026-11-06: Understanding V1 is a separate
plain-text prompt, agents/prompts/understanding_v1.md, not an overwrite of this
mixed cycle. --understanding-v1 runs only that prompt on unchanged evidence.
Output name/description/materials/assumptions is retained as text for review,
not a valid Front or accepted downstream input. Lev1/Lev2 complete in
5.291/5.164 s, but visual/unit/material errors remain. No downstream call or
production integration. Exact evidence and current next action are in TODO
and notes/evidence/understanding-v1-2026-11-06/simple-object-trials.json.

Owner requested restoring the foundational whole-object interpretation and
called the next cycle V5. This is an experimental contract version inside
Estimation V6.2, not an overwrite of historical CB Front V5/Planner V5 files.

1. Understanding + Front, ONE existing first-stage Haiku call. Reuse the old
   understanding schema (summary, construction_summary, views, components,
   cross_view_links, uncertainties) and Front V3 rules. Physical components are
   not workshop blocks or individual facade rectangles. Link every Front ID
   and tabletop-support group to one component, using object-owned views.
2. Planner, ONE explicit next call. Reuse V7 grouping rules, consume the exact
   saved interpretation and original evidence. Map all components to resulting
   blocks/shared parts, including fixed/open/decorative construction. Validate
   front-to-component-to-block consistency. Preserve interpretation conflicts;
   an unresolved component may have no blocks only with an explicit conflict.
3. Calculate, ONE explicit call per object when structurally valid. Carry the
   same interpretation, mappings, Front and Planner scope. Retain V3.3 parts
   compiler/arithmetic, reject V4/V4.1 regrouping in this route. Any interpretation
   or Front conflict blocks Calculate. Dimensions are still model estimates;
   this version does not claim to fix span ownership or complete material demand.

These are three diagnostic provider calls per object, not the original desired
one Analyze across all document objects plus Calculate per object. No additional
fourth understanding call. Integrating document-wide Analyze and exposing the
description in product UI are pending, not silently replaced or accepted here.
The saved description is available in raw/HTML diagnostic reports. Prompts are
English, model Haiku 5.5, low effort, thinking disabled, no automatic retries.

Implementation: agents/estimation_cb_cycle_v5_agent.py and
use_cases/estimation_cb_cycle_v5.py; existing probe CLIs opt in with --cycle-v5.
Parts also requires --parts-version V3.3. No default route/prompt mutation.
The V5 loader checks exact shared evidence, complete original responses and
the actual Planner input against the saved first-stage response. Original raw
response is captured before validation. Unit tests cover preserved context,
missing/fixed components, ownership references, conflict gating and isolation.
Structural reference checks cannot certify that a component is physically real
or actually belongs to the source object. No private reasoning is requested.

423 relevant tests. First Ada live test uses protected saved two-object run
run_4e47c1226af946698779203ca31ff705, object-001, four pages, four full-page images.
No saved Estimation input existed: use the existing HSL input builder with saved
Detection/OCR, unchanged membership and hash-verified PDF. No DB writes.
One complete Haiku response in 10.415 s, rejected: Front incorrectly flattened
to one group; whole-object summary combines the counter with the other L-shaped
display. Source notes about plywood were read, but veneer was additionally
inferred. Three fronts described as stacked, not adjacent. Planner/Calculate
not called, no raw repair or paid retry. Failed witness and review:
notes/evidence/cb-cycle-v5-2026-11-06/adda-object-001-trial.json.

Owner-requested simple-file transfer, unchanged V5: Lev1 8.760 s and Lev2
8.327 s, one first-stage call each. Both complete replies fail the Front schema.
Lev1 states three drawers but replaces annotated rows with count categories;
F01-F03/T01 mappings have no actual referenced rows. Lev2 leaves groups empty
and counts null. No Planner/Calculate or repaired outputs. Source inputs/pages
and prepared request evidence are unchanged. Raw replies/hashes:
notes/evidence/cb-cycle-v5-2026-11-06/simple-object-trials.json.
Failure is therefore not confined to Ada's multi-object pages. The next proposed
diagnostic is a single explicit merged output schema instead of inherited schema
plus wrapper placeholder. This is a prompt-composition hypothesis, not confirmed
causality. Coarse descriptions and view assignments are not yet visually accepted.
Ada object-scope presentation remains a separate hypothesis: full-page context
shows both objects with no enlarged island crops. Keep original pages/legends
and Detection ownership intact; do not accept merged understanding as correct.

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
