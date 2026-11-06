# Estimation V6.2: HSL and N68 research checkpoint

Date: 2026-11-05, Asia/Jerusalem. Work: 3.17.4.5, no new block.
Owner requested full checkpoint preservation after reviewing the N68 V6 overlay.
This is a reproducible research checkpoint, NOT production or semantic acceptance.
The existing authoritative backlog remains notes/TODO.md.

Continuation, 2026-11-06: owner corrected N68 from four to SIX drawers,
then from eight doors to TEN door-like rectangular fronts (5 tall + 2 under
sink + 1 dishwasher + 2 tall-column fronts), with lift-ups still unaccepted.
The downward-opening dishwasher front is not an ordinary cabinet-hinge or
gas-lift demand. The historical
counts below describe the checkpoint, not the new benchmark. Two lower drawers
are absent already in Front; Planner box expansion alone is insufficient.
Later Front V3 + Planner V7 trial finds six drawers and seven of ten door-like
fronts, omitting the dishwasher and two column fronts;
Front still fails enum validation and Planner truncates. Neither is promoted.
See TODO, n68-owner-benchmark-2026-11-06.json and the separate
notes/evidence/hsl07-v62-2026-11-06/n68-front-v3-planner-v7.json witness.
The earlier crossed-region/column omission claim needs identity revalidation.
Subsequent Front V4 experiment on unchanged input regresses to five matched
door-like fronts and four drawers, still failing island enums. Rejected for
promotion; no Planner run or default change. Separate witness:
notes/evidence/hsl07-v62-2026-11-06/n68-front-v4.json.
Owner subsequently requested rollback and Lev2 verification. Front V3/V4
experimentation stopped; selected Front V2 / Planner V4 never changed. A single
Lev2 V2 repeat with the exact earlier request gives five drawers, two lift-ups,
18 hinged doors and invalid enums. Earlier V2 had 15 hinged + two unresolved
and valid enums. Reliability remains unaccepted. Separate raw witness:
notes/evidence/cb-front-v2-2026-11-06/lev2-rollback-repeat.json.

## Identity and protected state

- Worktree: /private/tmp/costerly-estimation-v425
- Branch: codex/estimation-v425
- Parent commit: cc923a9af944214f90b61feed556bda00764a57b
- New tag: estimation-v6.2-hsl-n68-research-checkpoint-2026-11-05
- Resolve its exact commit with `git rev-parse estimation-v6.2-hsl-n68-research-checkpoint-2026-11-05^{commit}`.
- Protected earlier tag: estimation-v6.2-front-count-r03-checkpoint-2026-11-05,
  commit 6b686d970703b78fed638c1ced2f4403479e09eb. Do not move it.
- Publication is branch and new tag only, not main or deployment.
- Remote main observed before publication: 8eb87f1b4edc35b30d3bb0b7bc444aaca1cc6d59.
  This is a Git observation, not a fresh live production verification.
- Fifty pre-existing unrelated added TODO lines remain outside the checkpoint
  commit. They concern V4.28/V5.6.6 UI work and the Ada regression; preserve them.

## Selected code versus experimental prompts

| Role | Selection | System SHA256 (stripped UTF-8 text) |
| --- | --- | --- |
| Current Front | CB Front V2 / technical r05 | a929fe8ce72fd7cf75c9c100f2ce48c1e1ab2a4da8cb9ce44a9ac16545e0affd |
| Current Planner baseline | CB Planner V4 | 3f6ae0ff17c071066ba1ea46bfcf954949c4d1cc370ab6ecad46b8767de4a749 |
| Retained candidate | CB Planner V5 | c8a4c285970704c87c2fdc1f0d81108a4df95143f2449d63e70930aadee72a13 |
| Retained candidate | CB Planner V6 | 3f13cae5fa825322b50725e45eeb6df066a5528c9319b6857a4b5bc974a0427d |

Prompts: agents/prompts/cb_front_v2.md and cb_planner_v4.md through
cb_planner_v6.md. Historical r03 remains unchanged and explicitly replayable
with --front-v1. Runtime selector in agents/estimation_understanding_agent.py
is Front V2 + Planner V4. V6 was selected only for its isolated test and then
restored to V4 after a physical-scope regression. V4 is not a fully accepted
HSL solution. No production routing, Detection model or UI changes were made.

Both stages use claude-haiku-5-5, low effort, 60-second timeout, no retries.
Front max_tokens=10000; Planner max_tokens=6000. English prompts and outputs.
These are single-object diagnostic stages, not a verified project-wide shared
Analyze implementation. Materials Calculation, pricing and labor were not run.

## Exact saved Detection source

Run: run_99b433940dcc4fd9abbe0587dc56fb12, company 610.
File: Hasolelim_Carpentry_Plan_Floor_07.pdf.
Run created 2026-10-27T21:14:59.844207+00:00 (23:14 Jerusalem).
Detection event: ba7c98b2-2ad6-44a6-8e8b-cba525d67518.
OCR event: 6ffecd2b-e041-4321-b4ef-3a65c0db59a9.
Original SHA256: 45e51f24b04c75b8b0223ef0e60724faaed65f3c34105b1e32c04b16ec005c69.
Nine objects, 34 saved island packages. No redetection or changed membership.

| Object | Sheet | PDF page | Islands |
| --- | --- | ---: | ---: |
| object-001 | N56 | 3 | 3 |
| object-002 | N57 | 4 | 7 |
| object-003 | N60 | 5 | 3 |
| object-004 | N62 | 6 | 3 |
| object-005 | N68 | 7 | 4 |
| object-006 | N70 | 8 | 4 |
| object-007 | N74 | 9 | 5 |
| object-008 | N76 | 10 | 3 |
| object-009 | N76B | 11 | 2 |

Do not use fallible Detection names as visual interpretation authority.
No saved rfq_estimation_object_inputs existed for this HSL run. That was not
a blocker: the existing Lev2 route already used build_estimation_input with
saved Detection rows/OCR and hash-verified original images. HSL reused it
locally, keeping exact region membership and explicitly local artifact refs.
No DB writes or claims of persisted immutable inputs. Lev1, unlike Lev2,
used saved input db175c9d-b911-434e-a3ed-de612640f96f.
The earlier claim that absence of saved Estimation inputs required a new
architecture was incorrect. An older HSL fixture using all-document OCR hit
100k characters before any provider call; that is superseded evidence, not a
failure of this latest saved package. This replay follows page-local Lev2
context, not a validation of all-document legend transport.

## Results and decisions

HSL baseline: 18 calls across nine objects, two concurrent chains, 188.55 seconds
provider-batch wall time, 483656 input / 67331 output tokens. Not a production SLA.
Front 0/9 structural passes: eight island enum failures, one group/box count
mismatch. Planner 7/9 structural passes: object-001 invalid references,
object-007 max_tokens truncation. Full-chain structural passes: 0/9.
The diagnostic Planner accepts complete raw Front JSON as a fallible reference
with its failed status explicitly supplied. No output was normalized or repaired.
Seven valid Planner schemas do not override nine failed Front validations.

All nine object source pages were visually inspected. Exact Planner overlays
were reviewed for N57 and N68; not every box of every object was certified.
N57 misinterprets plans and merges distinct tops; N60 invents a second run from
multiple views and labels bare dimensions in mm. N68 V4 identifies the L layout
but places the worktop box on the upper shelf band.

Owner confirms N68 eight hinged doors and four drawers. Five lift-up fronts
are NOT accepted. Front calls triangular marks in the upper shelf band gas-strut
triangles: F01-F03 on p7-view-003, F16-F17 on p7-view-004. Those references,
not separately detected mechanisms, generate its five-set interpretation.

V5 adds worktop surface localization on top/axonometric views. A front/side
view can show an edge, not the complete top surface. If no surface view exists,
only the visible edge may be located, with explicit footprint uncertainty.
V5 isolated N68 call: 22.921 s, schema pass, S01 moves to a top view.

V6 adds maximum TWO tall door leaves across a tall block, no three/four-leaf
exception. It preserves exactly one-section-wide full-height columns; two
leaves may close one section. Ordinary non-tall blocks retain the three-position
guideline. No invented numerical height cutoff.
V6 isolated N68 call: 22.311 s, schema pass, seven blocks plus shared S01.
S01 moves to p7-view-001 and tall storage becomes F07/F08 plus F09 (2+1).
However, the previously represented wall-1 appliance column disappears.
Worktop and drawer boxes remain approximate/incomplete. V6 is not accepted.
V5/V6 inputs, images, saved Front, model and request settings match V4 exactly;
only system prompts differ. A single comparison does not establish causation
for the omission. No automatic retry, Front recount or new prompt revision.
Default restored to V4; V5 and V6 retained without rewriting historical outputs.

## Confirmed transport defect and next work

source_coordinate_frame in use_cases/estimation_dimension_graph.py calculates
page_size_points * dpi / 72 without accounting for PDF rotation. Pages
3,5,6,8,9,10 have rotation 270; Detection bboxes and rendered images use the
landscape frame. Five objects receive no enlarged crops and object-006 gets
two mispositioned crops. Full-page images remain present. Pages 4,7,11 do not
have this mismatch, so the N68 failure cannot be blamed on this defect.

Pending proposals, not approved implementations:
1. P0: fix rotation-aware coordinate transport, add rotated-page regression,
   then replay affected saved evidence without changing model/prompts.
2. P0: diagnose N68 physical-scope omission before promoting V6. Preserve
   the owner-approved two rules and the eight-door/four-drawer benchmark.
3. P0: resolve Front enum/box-count failures and lift-up/open-shelf ambiguity;
   preserve raw failures, do not mask them with silent coercion.
4. P0: bound Planner output without truncation or loss of physical elements.
5. Deferred: full multi-object/material cycle and latency optimization, no labor.

## Evidence and recovery

Git evidence directory: notes/evidence/hsl07-v62-2026-11-05/.
replay-evidence.json retains all baseline raw final texts, usage, errors,
request/prompt hashes and visual audit. n68-planner-v5-v6-evidence.json retains
both candidates, input identity checks and the default-restoration decision.
No secrets, source-image base64 or private thinking are committed.

Complete local witnesses: /private/tmp/hsl07-saved-replay-20261105-01/.
Full input/image/request/response snapshots and overlays, original PDF and
preparation/audit scripts are also preserved outside /tmp in this PRIVATE archive:
/Users/qb/Documents/ChatGPT/Costerly/backups/estimation-v6.2-hsl-n68-2026-11-05/private-replay-evidence.tar.gz
SHA256: e000063ac406176504537d5fb0ec5bc99a3760aed4aa5020229a1f182648faef.
Keep it private: it includes customer source images and complete provider envelopes.
It is an evidence archive, not a replacement for the Git source checkpoint.

Start a continuation by checking Git status, branch/tag and selected prompt
hashes; never reset this dirty checkout. Read this file and the affected TODO
section. Restore the archive into a NEW directory if /tmp witnesses disappeared,
check its hash and source hash first. Reuse captured input/image bytes, never
redetect or silently switch to a source-only PDF probe. Model calls require
explicit --execute; no calls are needed to inspect existing outputs/overlays.
tools/probe_v62_module_call.py replays saved inputs; tools/render_estimation_front_overlay.py
renders original boxes. Default Planner is V4; V5/V6 replay requires an explicit
process-local prompt/version override before importing the probe, not changing
the selected runtime or pretending an old result came from the current default.

## Verification at checkpoint

166 tests pass on the final restored-default tree (3.08 s):
test_cb_front_supports, test_cb_planner, test_estimation_front_count,
test_estimation_front_overlay, test_estimation_understanding,
test_estimation_module_understanding, test_estimation_v6_replay,
test_estimation_structural_bom, test_estimation_visual_evidence.
Archive content is byte-compared with originals; AppleDouble metadata is not
treated as source content. git diff --check and staged scope inspection required
before publication. Full suite, authenticated UI, new live production estimation,
material quantities and manufacturing acceptance are not claimed.

This checkpoint closes preservation only. It neither certifies V6 readiness nor
authorizes the pending repairs. The next recommended task is the bounded
rotation-aware transport fix; the independent N68 scope loss stays explicit.
