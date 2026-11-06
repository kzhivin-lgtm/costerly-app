# Estimation V6.2: CB Parts V3.3 research checkpoint, 2026-11-06

Status: OWNER-REQUESTED RESEARCH PRESERVATION WITH KNOWN LIMITATIONS.
Work number: 3.17.4.6. Product iteration V6.2, prompt CB Parts V3.3.
The owner explicitly requested two more runs and immediate checkpoint creation.
This preserves the approved architecture experiment and its actual results,
including failures. It does not certify stable dimensions, full-object success,
integrated Analyze/Calculate, deployed UI or production readiness.

## Exact identity

- Repository: /private/tmp/costerly-estimation-v425
- Branch: codex/estimation-v425
- Source implementation parent: 34f10f67d5a248af79579a4359c6365a5186c824
- Immutable checkpoint tag: estimation-v6.2-cb-parts-v3.3-research-checkpoint-2026-11-06
- Resolve the tag to its commit for the complete code/test/document snapshot.
- Prior protected upstream tag: estimation-v6.2-front-v3-planner-v7-partially-compromised-2026-11-06
  at 7b48d7ffc4ee12c7aa42783745301a7961a3c13e. Do not move either tag.
- Main before checkpoint: 8eb87f1b4edc35b30d3bb0b7bc444aaca1cc6d59.
  No merge, deploy, DB write, Detection rerun or default promotion.

Selected research prompts and SHA256 of stripped UTF-8 system text:

| Section | Explicit version | SHA256 |
| --- | --- | --- |
| Front | CB Front V3 | 2530993b653575e5445eced53b34ed6b9393eb73c30428c2bac28d641d49429b |
| Planner | CB Planner V7 | d3271d697f5398e699511d8a261f3f8734bf744835b52b894188d37d819cd848 |
| Parts | CB Parts V3.3 | 79cd946dc110b0fe61fab4209c9b6e7a17a124a2b492db2537d606d7a9da051e |

IMPORTANT: normal selectors remain Front V2 / Planner V4, Parts opt-in default
V3. This checkpoint selects V3.3 explicitly via `--parts-version V3.3`.
Checking out the tag alone does not change production or promote any selector.
Old Parts V1/V2/V3/V3.1/V3.2 prompts and their raw results remain available.

## Approved scope and implementation

Materials/major parts only, no labor/pricing. Target architecture remains one
document-wide Analyze plus one Calculate per object. These experiments replay
saved separate Front/Planner probes; they are NOT a completed integrated Analyze.
Each Parts trial is exactly one claude-haiku-5-5 request, effort low,
thinking disabled, max_tokens 14000, timeout 120 s, no provider retry.

Model returns ordered bays (side-by-side widths), fronts stacked within each
bay, heights/body heights, shelf counts and short assumptions. Code derives:

- Straight-carcass total width from the sum of bay widths.
- Two sides, full top/bottom/back, front panels and five panels per drawer.
- One shared mounting partition at each boundary adjacent to a drawer bay.
  Stacked drawers do not duplicate width or partitions; two drawer bays share
  one wall, not two. Adjacent doors alone do not force a partition.
- Drawer depth: floor((cabinet depth in mm - 100)/100)*100, minimum 100 mm.
- Ordinary 17 mm and explicit-worktop 30 mm finished-thickness defaults.
- Grouping of identical geometry. Raw model responses remain unchanged.

Equal subdivision is owner-accepted when proportions are unclear, but does not
prove the source size or excuse inconsistent totals. Nonrectangular/stepped/free
parts use explicit model-authored geometry, outside straight-bay guarantees.
Full top/back and per-bay shelves are visible coarse assumptions, not verified
joinery or an inventory of reusable furniture templates. Purchasing/lamination
(including two 20 mm panels for 40 mm finished material) remains outside this
stage. Front types/membership retain upstream fallibility.

Code: agents/prompts/cb_parts_v3_3.md, use_cases/estimation_cb_bays.py,
agents/estimation_assembly_bom_agent.py, tools/probe_cb_parts.py.
Tests: tests/test_cb_parts_v3_3.py plus prior Parts/Front/Planner/BOM regressions.

## Inputs and provenance

Source: /Users/qb/Desktop/SAMPLES/JOLD/Lev 2.pdf
PDF SHA256: b69e132814531862c1abbf2ea3910e0221ab013dd2d0fb184400149d6ec02b1d
Detection source: run_189150ebf62447fc958f7c23cc34e3bb.
Origin: persisted_detection_local_fixture_not_persisted_input, not a claim of
immutable DB Estimation input. Same saved membership/OCR and rendered page.
Five supplied images: full sheet plus four islands, unchanged across trials.

Upstream witnesses:
- /private/tmp/lev2-front-v3-planner-v7-20261106-03-front.json
- /private/tmp/lev2-front-v3-planner-v7-20261106-03-planner.json

Front witness has failed format status, retained as fallible parsed evidence;
Planner finished with nine blocks and shared S01. B08 membership includes
F21 door and F22/F23/F24 drawers, but its locator covers only the door. No
historical response, coordinate or enumeration was repaired.
Four V3.3 trials include the ORIGINAL locator. Their entire provider requests
are identical: SHA256 5a411638bd4d4c34bf502e0412740f97e5a61dc35f8719a17082abd4550c571b.

## Four-run result

The following B08 values are isolated deterministic audits of raw responses,
not successful partial outputs of the failed complete-object Calculate call.

| Trial | Time | Door width | Drawer bay width | Derived B08 width | Divider | Whole-object status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 8.190 s | 450 mm | 450 mm | 900 mm | 1 | FAIL, B02 stack exceeds height |
| 2 | 9.282 s | 400 mm | 400 mm | 800 mm | 1 | FAIL, B02 and B06 height conflicts |
| 3 | 9.473 s | 350 mm | 270 mm | 620 mm | 1 | FAIL, B09 omitted; B02 drawer body exceeds facade |
| 4 | 9.674 s | 500 mm | 500 mm | 1000 mm | 1 | FAIL, B02 stack exceeds height |

All four isolated B08 audits retain one door and three drawers. Given the
returned two-bay topology, sum/common-panel width and divider are consistent
in 4/4. This is deterministic arithmetic, not proof of stable vision. Bay
dimensions vary materially, and complete-object validation passes in 0/4.
First B06 used 720 mm height despite printed 1150; source association can be
wrong even where internal arithmetic passes. Do not silently expand carcasses,
scale fronts, invent omitted blocks or discard failed blocks to claim success.

Preceding V3.2 single-factor locator ablation: ONLY B08 region removed from
outgoing context after original-scope validation. It returned bays 300+300 mm
and omitted S01 (13.744 s). Removal alone did not yield acceptable geometry;
one trial does not establish the locator's causal contribution.

## Evidence, backup and recovery

Git evidence:
- notes/evidence/cb-parts-v3-3-2026-11-06/four-run-checkpoint.json
- notes/evidence/cb-parts-v3-3-2026-11-06/locator-and-bay-trials.json
- Earlier version witnesses remain under notes/evidence/cb-parts-*.

Durable PRIVATE archive outside /tmp:
/Users/qb/Documents/ChatGPT/Costerly/backups/estimation-v6.2-cb-parts-v3.3-research-checkpoint-2026-11-06/private-replay-evidence.tar.gz
SHA256: 10199a8f0690986f0018b1790878fc6ee6cc8fafb608dc562bc92b2a95b73c80
Bytes: 5320768. Regular files: 22. All members byte-compared against originals.
MANIFEST.json alongside/inside lists exact paths, sizes and per-file SHA256.
Includes full Parts V1 through V3.3 request/response witnesses, locator ablation,
Front/Planner pair, baseline evidence, two reviewed overlays, source PDF and
the pre-existing TODO patch. Customer page images stay private, not in Git.

Fifty unrelated pre-existing added lines in notes/TODO.md remain UNCOMMITTED.
They are separately preserved as pre-existing-todo.patch in the private backup.
Do not reset the checkout, stage those records or restore over existing work.

Safe restart:
1. Read this checkpoint, current TODO section 3.17.4.6 and Git status. Verify
   tag/commit and all three prompt hashes, preserving local modifications.
2. Prefer existing recorded evidence, without model calls. If /tmp files are
   absent, verify archive SHA256, inspect member names, then extract into a NEW
   directory and verify each member against MANIFEST.json. Never overwrite.
3. A later authorized replay uses the saved matching Front/Planner witnesses:

```sh
/Users/qb/costerly-app/.venv/bin/python -m tools.probe_cb_parts \
  --front-witness /path/to/restored/lev2-front-v3-planner-v7-20261106-03-front.json \
  --planner-witness /path/to/restored/lev2-front-v3-planner-v7-20261106-03-planner.json \
  --output /path/to/new-unique-witness.json --parts-version V3.3 --execute
```

Do NOT use --omit-block-locator for the checkpoint replay. It was a separate
ablation, not a promoted input transformation. Do not regenerate Detection or
substitute a hand-built B08 crop or corrected Front result.

## Verification and stop boundary

201 relevant tests pass, including retained V1/V2/V3 trials, exact prompt hash,
four failed whole replies, isolated B08 sums/partitions, bay input immutability,
one-call route and locator-only ablation. This is not full-suite, production UI
or visual/material accuracy acceptance. git diff --check and staged-scope
review accompany commit/tag publication. Archive hashes/bytes verified.

Preservation is completed at the owner's request. Full-object sizing remains
pending, especially source-height association, vertical consistency, coverage
and dimension variability. No further prompt experiment, paid repeat or
architecture change is authorized merely by this checkpoint. Stop here.
