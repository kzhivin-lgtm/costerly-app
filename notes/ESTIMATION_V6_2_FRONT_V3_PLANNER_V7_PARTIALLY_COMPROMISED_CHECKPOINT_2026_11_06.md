# Estimation V6.2: Front V3 + Planner V7 checkpoint, 2026-11-06

Status: PARTIALLY COMPROMISED RESEARCH CHECKPOINT.
Owner wording: "частично скомпрометирован".
Work number: 3.17.4.5. Product iteration: V6.2.

The owner requested preservation of this exact experimental pair after reviewing
the nine-block / one-worktop overlay. This is acceptance of preservation with
known defects, NOT acceptance of model reliability, material estimation or
production readiness. No repair or new model run is part of this checkpoint.

## Identity and selection

Repository: /private/tmp/costerly-estimation-v425
Branch: codex/estimation-v425
Source/evidence parent: 194b244d91ca39abd22118a1f20bcf39e2184945
Checkpoint tag: estimation-v6.2-front-v3-planner-v7-partially-compromised-2026-11-06
Resolve the tag to its commit for the exact snapshot. Do not move or replace it.

Checkpoint experimental pair:
- Front: agents/prompts/cb_front_v3.md, CB Front V3.
  System SHA256: 2530993b653575e5445eced53b34ed6b9393eb73c30428c2bac28d641d49429b.
- Planner: agents/prompts/cb_planner_v7.md, CB Planner V7.
  System SHA256: d3271d697f5398e699511d8a261f3f8734bf744835b52b894188d37d819cd848.
Hashes above are stripped UTF-8 system text, exactly as sent to the provider.

IMPORTANT: this tag preserves V3/V7 as an explicitly selected research pair.
The ordinary runtime selectors remain Front V2 / Planner V4. Merely checking
out this tag does not select V3/V7. Use the process-local overrides below.
Other historical prompt files in the tree are not part of the selected pair.
No main merge, deploy, model change, Detection change, DB write or default
promotion is authorized by this checkpoint.

Protected older checkpoints remain intact:
- estimation-v6.2-hsl-n68-research-checkpoint-2026-11-05
  -> 6952b4eb9744508c718c427c084a40f96d90df13.
- estimation-v6.2-front-count-r03-checkpoint-2026-11-05
  -> 6b686d970703b78fed638c1ced2f4403479e09eb.

## Exact input and experiment

File: /Users/qb/Desktop/SAMPLES/JOLD/Lev 2.pdf
Archived source PDF SHA256: b69e132814531862c1abbf2ea3910e0221ab013dd2d0fb184400149d6ec02b1d
Detection source: run_189150ebf62447fc958f7c23cc34e3bb.
Evidence origin: persisted_detection_local_fixture_not_persisted_input.
The established read-only Lev2 bridge reused saved Detection membership and OCR,
rendered the source page and built the local Estimation input. These are not
claimed to be immutable DB Estimation inputs. No new Detection was run.

All three pairs reuse the exact inputs and page bytes in:
  /private/tmp/cb-front-v2-lev2-01.json
Three independent pairs were launched concurrently, six calls total.
Within each pair, Planner consumes only that pair's fresh Front.
Front request objects match across all three runs; versus baseline V2 only
system changed. Planner receives the same images/input plus its own original
parsed Front and its original success/failure status. No enum or count repair.

Model: claude-haiku-5-5, low effort, no retries, 60-second timeout.
Front max_tokens: 10000. Planner max_tokens: 6000.
This is an isolated diagnostic route, not a deployed project Analyze cycle.

| Pair | Front raw counts: doors / drawers / lift-up | Front format | Planner | Sum of stage time |
| --- | --- | --- | --- | --- |
| 1 | 17 / 5 / 2 | Failed, island enum spelling | Truncated at 6000 | 61.529 s |
| 2 | 17 / 5 / 2 | Passed | Truncated at 6000 | 66.051 s |
| 3 | 17 / 5 / 2 | Failed, island enum spelling | Passed format, 9 blocks + 1 shared worktop | 61.744 s |

All Fronts have zero unresolved fronts and zero legs. Both wings and both
drawer banks are retained in all three responses. Owner benchmark is five
drawers, two lift-up fronts, 15 preferred / at most 16 hinged doors.
Equal totals in this small series do not establish general stability.

Zero pairs pass BOTH stage formats. A failed but parseable Front was deliberately
passed to Planner through the existing diagnostic interface with its failed
status. Planner 3 completion must not be described as a successful full chain.
The two truncated Planner texts remain unparseable and were not salvaged.

## Why partially compromised

1. Front recognition: known lower side and appliance-opening regions are still
   counted as hinged fronts. Seventeen doors exceed the owner benchmark.
2. Front output format: two of three use snake_case island types, rejected by
   the unchanged enum validator. Display-only aliases were used for those
   overlays, never to change the saved response or Planner input.
3. Planner completion: two outputs exhaust max_tokens=6000. Their reported
   thinking usage is 4151 and 4975 tokens. No budget increase or retry occurred.
4. Planner 3 physical scope/localization:
   - B08 contains door F21 AND drawers F22-F24 in its front_ids.
     THE DRAWER ASSEMBLY IS NOT OMITTED FROM THE PLAN. It is grouped with the
     adjacent door, a permissible grouping. The box is wrong: x=595..735
     locates the door but misses drawers at x=446..597.
     This distinction reflects the owner's overlay discussion.
   - B06's box covers only part of its hanging door pair.
   - B01's box does not include its listed lift-up fronts.
   - B09 interprets the tall right end side as a cabinet column, while its
     uncertainty admits the fixed-panel alternative.
   - S01 is a separate worktop on Top view, a retained positive result.
     Its box misses the terminal chamfered end of one base wing. The empty
     interior of an L-shaped rectangular locator is not itself an error.
All supplied Front IDs are assigned once; syntactic assignment alone does not
establish physical correctness. Boxes are review locators, not material geometry.

## Evidence and durable recovery

Git raw final responses, settings, hashes, errors, usage and review:
  notes/evidence/lev2-v3-v7-2026-11-06/three-paired-runs.json
Regression fixture:
  tests/test_cb_v3_v7_replay.py

Private live witnesses, raw text, HTML and overlays:
  /private/tmp/lev2-front-v3-planner-v7-20261106-0[1-3]-*
The owner-reviewed overlay is:
  /private/tmp/lev2-front-v3-planner-v7-20261106-03-planner-overlay-page.png

Durable PRIVATE archive outside /tmp:
  /Users/qb/Documents/ChatGPT/Costerly/backups/estimation-v6.2-front-v3-planner-v7-partially-compromised-2026-11-06/private-replay-evidence.tar.gz
SHA256: 49bba88ada97be184523b6dff83905d72e60711c3634bb358fd59bbfad38c03a
Bytes: 3119243. Regular files: 32.
Every file was byte-compared against its original. Archive includes all six
full provider/request witnesses, raw responses, generated reports/overlays,
the unchanged baseline input witness and source PDF. MANIFEST.json alongside
the archive has per-file SHA256 and size. Complete provider envelopes and
customer images remain private; they are not added to Git.
The archive is not a replacement for the Git source snapshot.

Fifty pre-existing unrelated added TODO lines remain outside this commit.
They are separately preserved as pre-existing-todo.patch alongside the archive.
Never reset this dirty checkout or overwrite those records.

## Safe continuation

1. Read this record and the affected 3.17.4.5 TODO entry. Check Git status,
   checkpoint tag/commit and both prompt hashes. Preserve existing local work.
2. Inspect existing evidence and overlays without making model calls.
3. If /tmp data is absent, verify the archive hash and restore into a NEW
   directory, never over an existing witness. Reuse captured input/page bytes.
4. To replay V3/V7 only after a new authorized experiment, use
   tools.probe_v62_module_call with unique output paths and these overrides
   BEFORE importing the probe's main:
   Front:
     a.FRONT_SUPPORTS_PROMPT_PATH = a.FRONT_SUPPORTS_PROMPT_PATH.with_name("cb_front_v3.md")
     a.FRONT_SUPPORTS_PROMPT_VERSION = "CB Front V3"
     arguments: --replay <restored-baseline.json> --output <new-front.json> --count-fronts --execute
   Planner:
     a.PLANNER_PROMPT_PATH = a.PLANNER_PROMPT_PATH.with_name("cb_planner_v7.md")
     a.PLANNER_PROMPT_VERSION = "CB Planner V7"
     arguments: --replay <same-baseline.json> --output <new-planner.json> --plan-assemblies --front-witness <that-new-front.json> --execute
   Here a is agents.estimation_understanding_agent. The probe rejects output
   overwrites and mismatched evidence. No global selector edit is needed.
5. Do not call a failed Front / successful Planner pair a successful cycle.
   Do not repair historical responses, infer missing quantities from boxes,
   or promote this pair on the strength of the tag.

## Verification and remaining boundary

183 focused tests pass at preservation, including raw failed responses,
exact prompt identities, default preservation, separate stage statuses and
the B08 assigned-drawer/box mismatch. Archive files byte-verified.
git diff --check and staged scope inspection are required for publication.
No new paid calls are part of this preservation. Full suite, production UI,
BOM/material quantities, hardware quantities, manufacturing and labor are not
accepted by these checks. Authoritative pending work remains in notes/TODO.md.

Owner requested checkpoint preservation now. Stop speculative follow-up.
A later approved task may isolate completion/enum failures and separately
physical-role/box accuracy; neither is authorized merely by creating this tag.
