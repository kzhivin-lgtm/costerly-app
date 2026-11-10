# Detection V8.4.9 candidate

Base is the owner-accepted local V8.4.8 tag
`detection-v8.4.8-ada-parallel-membership-checkpoint-2026-11-10` at `6c552b3`.
Haiku migration is local commit `89f87b7`. The owner requested a local
checkpoint and deferred deployment.

## Runtime

The shared Claude transport migrates Haiku defaults and legacy Haiku overrides
to `claude-haiku-5-5`. It preserves response schemas, uses low effort, and
omits the sampling parameters rejected by the model. Sonnet stays on
`claude-sonnet-4-6`. The Haiku accounting includes both prompt-length tiers.
The shaded CAD render clarification applies to the existing Ada Discovery
route only. The ordinary Discovery prompt is byte-identical to V8.4.8.
See [Anthropic migration guide](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide)
and [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).

Detection reads standalone numeric labels using PP-OCRv6 tiny on the same
rendered pages sent to Mistral, concurrently with the provider request.
The reader rotates a page once and maps each tight label box back to OCR
page pixels. It preserves page, original text, bbox, confidence, and source
in `evidence.numeric_labels`. No extra provider OCR request is made.
Two local page workers run alongside Mistral. The original three-second tail
wait was raised to 12 seconds after the owner approved a longer wait for
incomplete pages. Detection continues as soon as the local work finishes.
Partial output explicitly records missing pages and reasons. The image build
verifies two pinned ONNX model hashes. The local reader can be disabled with
`DETECTION_COORDINATE_OCR_ENABLED=0`.

The coordinate labels are attributed to locked Views after Membership.
`coordinate_dimension_audit` contains per-View readings and a separate
Dimensional Fingerprint with source fact IDs and unit basis. The live merge
graph and route selection consume the established evidence. This separation
is required by the benchmark. Counting the extra numbers as text coverage
bypassed the Ada protection and moved Page 23 off its specialized route.
Sending the extra numbers to Membership on the protected Ada route then
returned six groups on Adda. Both experiments were rejected.

## Local benchmark

Fresh Mistral plus coordinate OCR with the original three-second limit,
followed by live Detection on the saved packages. Tests exercised the normal OCR entry. Page 23 and HSL used Haiku.
Each Ada-family test used Haiku Discovery and two Sonnet calls.

| File | OCR total / local wait | Completed pages | Bboxes / assigned to Views | Result and run |
| --- | ---: | ---: | ---: | --- |
| Adda | 6.222 s / 2.965 s | 4/4 | 33 / 33 | Exact two groups `01/04/06/08` and `02/03/05/07`, `run_b9a002a9ef2341208efeb6e1a7837edf` |
| Lev 1 | 1.746 s / 0.000 s | 1/1 | 7 / 7 | One object, six Views, `run_87a093dde8184a3ab4c054f77911c60b` |
| Lev 2 | 1.294 s / 0.055 s | 1/1 | 9 / 9 | One kitchen, four Views, positive render attachment, `run_fbc2e7606823415abfac8be7a2e217dd` |
| Page 23 | 2.821 s / 0.000 s | 1/1 | 26 / 26 | Three objects on the native-graphic route, `run_135f679368c64c3eb970cdd046335dc3` |
| HSL 07 | 19.776 s / 3.001 s | 7/11 | 117 / 92 | Ordinary Haiku completed with 30 objects, `run_49a6d5bd14fa4e0e971a763af919470c`. P04 completed local OCR. P07, P08, P10 and P11 timed out. |

Adda matched 25 of 27 control text labels. Its tight boxes matched 24 of 25
independent same-text witnesses with vector-bound reference positions
(overlap at least 60% of the smaller box). Its eight locked View boxes and
Lev 2's four locked View boxes were identical to V8.4.8. The Adda, Lev 1 and
Lev 2 same-sheet Sonnet audits checked 4, 15 and 6 pairs, respectively. Adda
repeated the exact groups on `run_f015f699c15e4626816d45d0fbdfabc4` with the
same saved OCR package. Before scoping the shaded-render rule to Ada, one HSL
run failed V7.11 on an invalid render decision for a conflict-admitted ID.

The broad Detection/OCR suite returned 410 passes and the pre-existing static
Processing completion-marker failure. The lockfile validated offline.
Production image startup and timing remain unmeasured. HSL coverage and
quantity of final packages are open acceptance criteria. Membership use of
the new fingerprint requires a separate controlled test.

## Twelve-second wait verification

A fresh HSL 07 run completed 11/11 pages with 237 numeric labels. Local
collection took 0.005 s because the reader finished during the provider
pass. The fresh Adda run completed 4/4 pages with 33 labels and waited
0.813 s for the local reader. The Mistral request counts were 11 and 4.

A separate HSL replay reused the saved Mistral responses, set the standard
OCR deadline to the previous fast run's 16.775 s, and measured both wait
thresholds in the same run. Eight of eleven local reads had finished after
three seconds. All eleven completed after 6.240 s of local collection,
including P08. Total replay OCR time was 23.028 s. Artifacts are under
`/private/tmp/detection-coordinate-wait.dcEfpx`. Focused OCR tests passed
27/27. These checks cover OCR and timing on the local host.

The local raw OCR packages are under `/private/tmp/detection-v849-coordinates.NboV4g/single-pass`.

| OCR package | SHA-256 |
| --- | --- |
| `adda-ocr.json` | `febce0ecc07dda9c92693e49f7e95d7f5db31c596a7bfb3049237c783e852cec` |
| `hsl07-ocr.json` | `e4453aad3f4f5211c9218d2fe07729919e0bd73c205e7e600d167d3e7415b591` |
| `lev1-ocr.json` | `e538eee74f1d229ecc1cbaca2a1279794517e301f7062206eca35ef9e2c05a46` |
| `lev2-ocr.json` | `0ac436dad81f7ace91630a02a0bed55d144643014181054218dd7888fdbcc25f` |
| `page23-ocr.json` | `7a0c4a9b6e59f284889d7b85a1a90cc3f4cbc73fa64441730e353e23afc1b543` |

## Local checkpoint after historical adapter cleanup

The runtime anchor is `3f3f15773e040979a407904bfbaceaa50f9fb9fb`. Local annotated tag
`detection-v8.4.9-post-cleanup-checkpoint-2026-11-10` records this runtime and the checkpoint documentation.
Cleanup commits `f875111` and `3f3f157` removed the seven retired
entry points and their exclusive dependencies.

The private replay archive is `/Users/qb/Documents/ChatGPT/Costerly/backups/detection-v8.4.9-post-cleanup-checkpoint-2026-11-10/private-replay-evidence.tar.gz`.
All 60 file hashes verified after extraction.
Restored source replayed the five fixed drawings and the visual fallback.
The results matched the saved verification digests byte for byte with
zero provider calls. The archive contains the original drawings, stored
OCR and model responses, replay code, runtime tree and prior coordinate
experiments. Manifest: `notes/evidence/detection-v8.4.9-post-cleanup-checkpoint.json`.

The broader Detection/OCR suite passed 406 tests. The Processing
completion-marker test failed before and after cleanup. This is a local
checkpoint of the measured behavior. HSL package boundaries remain
outside the acceptance claim.

Next scope is dominant-page attachment safety. The owner identified the
sparse detail in the lower-left of HSL Floor 07 P03 as a positive case
to inspect in whole-sheet context. The target object still needs to be
bound to an exact saved View and source witness. The checkpoint makes
no change to attachment behavior.
