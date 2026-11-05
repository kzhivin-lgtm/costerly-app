# Estimation V6.2: provisional front-count checkpoint

Date: 2026-11-05. Work: 3.17.4.5 (existing number, no new block).
Owner decision: keep the previous prompt r03 as sufficient for now, preserve
a full checkpoint, then proceed to major physical assemblies.
Acceptance scope: a provisional development baseline WITH known visual errors.
Not a production release, correct BOM, complete material cycle or perfect count.

Later owner decision, 2026-11-05: select CB Front V2/r05 with tabletop supports
and accept abstract segmentation of the examined simple objects (Lev1 may be
two or three complete assemblies). This document/tag preserves historical r03,
not the currently selected prompt. V2 is now the default diagnostic; --front-v1
replays r03. Current limitations and Lev2 truncated Planner result are recorded
in notes/TODO.md and ESTIMATION_V6_1_CONSTRUCTION_PLAN_2026_11_04.md. No production
readiness or new protected technical checkpoint is implied by that selection.

## Identity and recovery

Continuation checkpoint: notes/ESTIMATION_V6_2_HSL_N68_CHECKPOINT_2026_11_05.md.
It preserves the later Front V2 + Planner V4 selection, HSL replay and failed
V5/V6 N68 candidates. This historical r03 document/tag remains unchanged in
identity and acceptance scope; do not treat its historical selection as current.

- Worktree: /private/tmp/costerly-estimation-v425
- Branch: codex/estimation-v425
- Pre-change commit: f20e343
- Checkpoint tag: estimation-v6.2-front-count-r03-checkpoint-2026-11-05
- Resolve the exact commit with `git rev-parse estimation-v6.2-front-count-r03-checkpoint-2026-11-05^{commit}`.
- Prompt at this checkpoint: agents/prompts/estimation_front_count_v6_2.md
- Version: estimation_front_count_v6_2_r03
- System SHA256: 81b49dc8d2dd4c33a7459d824178ea8601ba241370a401e530bed2748dab0bb0
- Archived experiment: agents/prompts/history/estimation_front_count_v6_2_r04.md
- r04 SHA256: 52d6f563f94add159d2b9c457eedc4dd31bbe47011e293c8bf0b68e266b95a99

Do not reset a dirty checkout. Inspect state and use the tagged source in an
isolated checkout when recovery is necessary. Earlier unrelated TODO additions
remain unstaged and must not be discarded or silently included in this release.
Publication targets this branch/tag only, never main or deployment. Remote
main observed during preparation: 8eb87f1b4edc35b30d3bb0b7bc444aaca1cc6d59;
this is not a fresh production-runtime verification. Historical V5.8.2 UI
and handoff behavior remains protected.

## Selected behavior

One diagnostic call to claude-haiku-5-5, low effort, max_tokens 10000,
timeout 60 s, no temperature, tools or retries. This is a single-object probe,
not an extra stage installed in production. Input is one full page and four
labelled island crops plus existing Detection source evidence. Naming is not
an interpretation authority. All model instructions/output prose are English.

Prompt tasks: classify islands using a fixed nine-type vocabulary, count
physical drawer/hinged/lift-up fronts, locate counted and useful excluded
surfaces, return JSON groups and totals. References, enum values, arithmetic
and image-local boxes are checked deterministically. These checks cannot
certify physical interpretation. Box coordinates include the generated 32px
header; overlay maps the existing crop margin back to the source page without
manual correction. Individual front IDs are local to each run, not stable IDs.

The older two-call module-selected understanding diagnostic also remains in
source. Do not confuse its call count or output contract with this one-call
front-count probe. No silent architecture replacement occurred. Haiku 5.5
migration is limited to this experimental understanding agent, not Detection
or every production Estimation caller.

## Actual evidence and acceptance limits

| Revision | Doors | Drawers | Lift-up | Unresolved | Time | Original contract |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| r03, selected | 17 | 5 | 2 | 0 | 29.021 s | Pass |
| r04, archived | 15 | 5 | 2 | 1 | 26.487 s | Fail, island enum spelling |

Owner benchmark: 15 doors (16 only for the identified ambiguous end door),
5 drawers, 2 lift-up fronts. The prompt contains neither these target counts
nor example-specific error IDs. r03 F01 and F24 are owner-identified false
doors (side/structural surfaces). They are accepted as current limitations,
not rewritten as ground truth. r04 removes old F24 as X04, retains old F01
as F07, and moves old F06 to unresolved F12. Thus r04's 15 is not success.
The request comparison r03/r04 changes only the system prompt, but one pair
of samples does not establish robust comparative accuracy.

r04's original failed witness is immutable. Its diagnostic overlay uses an
explicit opt-in spelling-only enum normalization with FORMAT WARNING, not
an agent validator repair. Counts/coordinates are unchanged. Both overlays
were visually inspected. No silent coordinate adjustment or image generation.

Durable Git evidence: notes/evidence/estimation-v6.2-front-count-2026-11-05/
contains r03-evidence.json and r04-evidence.json, with exact final model text,
parsed data, usage, fingerprints, coordinates and historical review. Historical
review status is preserved; this document records the later owner acceptance.
No API keys, source-image base64 or private model thinking are copied there.
Original source images and complete provider envelopes remain local; Git
evidence alone is sufficient for contract replay, NOT a paid visual replay.

Local originals:
- /private/tmp/estimation-v6-2-lev2-haiku55-front-count-03.json
- /private/tmp/estimation-v6-2-lev2-haiku55-front-count-04.json
- Same prefixes with -front_count-raw.txt, -review.json,
  -overlay-coordinates.json, -overlay-page.png and -overlay-details.png
- Replay input: /private/tmp/estimation-v6-2-lev2-detection-03-no-grounding.json
- PDF: /Users/qb/Desktop/SAMPLES/JOLD/Lev 2.pdf
- PDF SHA256: b69e132814531862c1abbf2ea3910e0221ab013dd2d0fb184400149d6ec02b1d
- Detection run: run_189150ebf62447fc958f7c23cc34e3bb
- Detection event: 8fd1c7f0-2f36-42bd-b7ae-537460324445
- OCR event: 29b1d88e-3848-4046-b4b5-662a03fc6869

Source supplies four islands, plan / axonometry / two elevations. It includes
numeric annotations and footer text, but no material specification. Bare
numbers do not prove millimetres. Source words are evidence, not instructions.
If local temp artifacts disappear, recover evidence through the existing
read-only probe and source PDF; do not claim bit-identical replay without hashes.

## Verification

Runtime: /Users/qb/costerly-app/.venv/bin/python, repository root as cwd.

106 passed in focused tests:
test_estimation_front_count, test_estimation_front_overlay,
test_estimation_understanding, test_estimation_module_understanding,
test_estimation_v6_replay, test_estimation_structural_bom,
test_estimation_visual_evidence (all under tests/, .py).
Includes exact selected/archived prompt hashes, recorded response validation,
one-call scope, unknown/zero semantics, count arithmetic, unique owned boxes,
overlay header/margin mapping, non-overwrite behavior and hardware boundaries.

Additional dependency suite: 54 passed, 3 failed across test_estimation_2vn_resolver,
test_estimation_v6_construction, test_estimation_assembly_bom,
test_estimation_composition_scope, test_estimation_evidence,
test_estimation_handoff, test_estimation_material_plan_norms,
test_estimation_assumption_fallbacks. Three failures reproduced on clean
git archive of f20e343, where handoff tests give 4 passed / 3 failed:
- test_shadow_handoff_uses_source_page_when_image_only_ocr_cannot_resolve_anchor
- test_shadow_handoff_falls_back_to_full_page_for_invalid_preview_bbox
- test_shadow_handoff_reuses_detection_preview_and_persists_full_evidence_page

These existing expectations concern retained OCR blocks and preview artifacts.
No fix is included; no full-suite or live UI acceptance is claimed. No paid
model rerun was needed to restore exact r03. r03 and r04 saved runs above are
the live evidence, not fabricated new test results.

Owner-requested hinge revision is included in local source/tests:
<=1000mm: 2; >1000mm: 3; >2000mm: 4, exact 2000mm: 3. Slides remain
floor((depth-100)/100)*100, purchased as sets; gas lifts as sets, hinges as
pieces. This front-count experiment does not invoke the hardware composer.

## Next boundary, not implemented here

Owner requests major-assembly decomposition, not additional front-count tuning.
Existing whole-object understanding already has components with name, function,
quantity, operation, material hypothesis, basis and view references. Inspect
and reuse it before adding a parallel contract. Distinguish a physical parent
assembly from its fronts, and repeated drawings from repeated components.
Agree the minimal contract and call placement before consequential changes;
do not add a reviewer or extra provider stage implicitly. Preserve the wider
goal: shared Analyze, per-object Calculation, deterministic composition.

Use ALL Detection context, including legends/indexed notes when available;
visual texture alone does not prove a substrate. Ready-made veneered panels
are purchasable materials. A 40mm finished element may be two 20mm panels with
edge veneer, recorded as an assumption when source does not establish it.
Avoid unnecessary new sheet materials, but do not claim geometric offcut reuse
from summed area alone. Labor, prices and production cut lists remain outside
this next interpretation step. No new work number or block is assigned here.

Authoritative queue: notes/TODO.md. Design history:
notes/ESTIMATION_V6_1_CONSTRUCTION_PLAN_2026_11_04.md. Historical V5 handoff,
Cabinet contract and DONE_LOG point here without rewriting prior failures.
