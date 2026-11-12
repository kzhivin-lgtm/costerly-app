# Detection V8.4.27 production checkpoint

Recorded November 12, 2026, Asia/Jerusalem. The owner accepted the observed
Floor 06 production result as a checkpoint. The Upload completed all 15
sheets and published 13 objects with eight render attachments. P05 and P13
still have unattached renders. Fresh Floor 07 and repeat Uploads remain open.

## Release and rollback

| Item | Reference |
| --- | --- |
| Release | Haiku 5.5 · Detection V8.4.27 · Match renders on their technical sheet |
| Deployed commit | `379f91f5760dbacb1652da2a6d0b379d17745586` |
| Exact restore tag | `detection-v8.4.27-same-sheet-render-matching-production-2026-11-12` |
| Previous release | `fb3e4d8120e4cbe8998832517bfbfe5e1b4a2707` |
| Previous release tag | `detection-v8.4.26-single-dimension-weight-production-2026-11-11` |
| Core and wrapper build | `detection-v8.4.27-haiku-5.5-same-sheet-render-matching` |
| Railway deployment | `b34ec6d3-f692-441a-a97f-852756b71ec9` |

The release receipt confirms the live Core and wrapper build markers and
Railway success. The checkpoint receipt records the verified GitHub branch
and tag targets. The documentation branch is `codex/detection-v8427-checkpoint`.

The ordinary Haiku route validates visually disputed render and drawing
roles before Membership. It compares renders to technical crops on the
same sheet at the first attachment attempt. A second comparison requires
a materially tighter technical crop or a smaller set of renders without
a decision or witness. The document-wide route handles sheets that supply
no comparable technical crop. Recompilation reuses the captured replies.

## Owner production evidence

| Item | Result |
| --- | --- |
| File | `Hasolelim_Carpentry_Plan_Floor_06.pdf` |
| Run | `run_b64e3ac0a9b34215a4658350c500cee9` |
| Completed | November 12, 2026, 10:16:42 UTC |
| Sheet coverage | 15/15 |
| Views | 62 before render exclusion, 60 published |
| Objects | 13, one on each sheet from P03 through P15 |
| Render decisions | Eight same-sheet primary attachments, two exclusions |
| Repeat render requests | Zero |
| Processing cycle | 197.31 s by event timestamps |

| Sheet | Persisted attachments | Shared features |
| --- | --- | --- |
| P03 | V1–V4 to V11 | Three shelving tiers and the repeated arrangement of dark uprights and triangular gussets |
| P04 | V1 to V3 | Wide, narrow, wide glass panels separated by slim mullions |
| P09 | V4 and V5 to V3, V6 to V2 | Stacked symbol bands and a sliding door in V3. Three panes and the cabinet sequence in V2 |

The role review corrected three P03 render crops originally labeled
technical drawings. All eight accepted render boxes were verified against
the published object regions and shared the same persisted owner as their
technical target.

- **P05.V2** remained unresolved. Its table has the inclined panel
  shown in V4 and the strip of glass blocks shown in V6. The retry
  gate found no materially tighter technical crop.
- **P13.V7** received `no_match` and did not enter retry. The source
  photograph and V2 show paired straps beside a cushion seam. A fixed
  experiment recovered V7 to V2 using a tighter crop. The owner
  production run left this attachment open.

The prior V8.4.26 Floor 06 Upload
`run_3ad259c296d74631a2cb7d0db8ad5848` published 17 objects and excluded
all nine identified renders. It ran for 152.26 s, 45.05 s less than the
V8.4.27 Upload. These are separate recognition runs. The V8.4.27
processing interval after render matching began also includes later
technical recovery, so it cannot isolate the cost of render matching.

## Verification and private evidence

The release checks returned 271 passing tests and one dependency-list
assertion that fails on the same dependency files in V8.4.26. The
checkpoint preserves the production witness, both release tags, the
source PDFs, page assignments, visual comparisons, and offline replays.
The Floor 06 fixed-input replay covers the role review, first comparison,
and focused retry using saved replies. The Floor 07 replay uses a
simulated role-review abstention. It covers saved input behavior.

The private archive is
`backups/detection-v8.4.27-production-checkpoint-2026-11-12/` in the
Costerly workspace. Its checksum manifest and README describe how to
restore the bundle and replay the recorded evidence offline. The source
PDFs, raw responses, and production traces stay in the archive.

The [benchmark](DETECTION_BENCHMARK.md) records the observed comparison.
Open render attachment, latency, and fresh Upload checks are in
[TODO](TODO.md).
