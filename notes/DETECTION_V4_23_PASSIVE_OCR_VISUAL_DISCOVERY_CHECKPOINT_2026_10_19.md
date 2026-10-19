# Detection V4.23 Passive OCR Visual Discovery Checkpoint

Date: 2026-10-19

Commit: `5306fff`

Status: protected, provisional for Visual Group discovery only

## Objective

Validate that Detection finds visually distinct source depictions without
treating Mistral OCR `image` blocks as object boundaries.

## Protected contract

- The single Haiku Visual Registry request remains at `temperature=0.0`.
- The Registry first identifies Visual Groups from the rendered source pages.
- OCR `image` block coordinates are appended as a passive post-visual
  cross-check only.
- OCR cannot create, split, merge, delete, reject or otherwise decide a Visual
  Group, commercial object, quantity, proof-parent link or Estimation Evidence.
- If the visual search finds more depictions than OCR, they remain valid.
- If an OCR coordinate appears unmatched, the model re-inspects that location;
  it adds a group only if the rendered page confirms a distinct
  object-specific depiction. Equal counts are never required.
- The audit records raw OCR regions and both OCR and Visual Group counts by
  page for successful and failed Registry calls.

This restores the V4.23 Registry structure. V4.24's mandatory OCR-region
coverage and V4.25's required all-island output are rejected experiments. They
caused Haiku to return an all-administrative HSL response and are not active.

## Verification evidence

### HSL, `Hasolelim_Carpentry_Plan_Floor_07.pdf`

Registry event: 2026-10-19 12:23:19 UTC, prompt
`detection_v4_23_passive_ocr_crosscheck_temperature_0`.

The run later failed at merge proof, not visual discovery. Its preserved audit
shows:

| Page | OCR graphic regions | Visual Groups |
| --- | ---: | ---: |
| 1 | 0 | 0 |
| 2 | 1 | 1, generic floor plan |
| 3, N56 | 2 | 3 |
| 4, N57 | 7 | 7 |
| 5 | 3 | 3 |
| 6 | 3 | 3 |
| 7 | 4 | 4 |
| 8 | 4 | 4 |
| 9 | 3 | 3 |
| 10 | 3 | 3 |
| 11, N76B | 4 | 3 |
| Total | 34 | 34 |

The page-2 floor plan is subsequently discarded from the object proof graph,
leaving 33 object-specific Visual Groups. Crucially, the rendered-page search
identified all three N56 depictions despite OCR providing only two graphical
regions on page 3.

### Additional successful files

| File | OCR graphic regions | Visual Groups |
| --- | ---: | ---: |
| `Adda.pdf` | 8 | 8 |
| `page-23.pdf` | 1 | 6 |
| `56bfa63e0236c85a161a2fa95a8996b03003df8f2f01d54ac4236acb5a7287b8.pdf` | 6 | 7 |
| `b69e132814531862c1abbf2ea3910e0221ab013dd2d0fb184400149d6ec02b1d.pdf` | 4 | 4 |

These results demonstrate the intended asymmetric behavior: one broad OCR
region may contain several visual depictions, while an OCR coordinate can be
non-object context.

## Verification

- Detection-focused suite: `46 passed`.
- The change adds no model call, router, Sonnet path, cache behavior, Naming
  work, preview work, File Review timing change or Estimation contract change.

## Limits and next task

This checkpoint does not accept commercial object boundaries, merge proofs,
quantities or final Estimation Evidence for HSL. The HSL run failed because one
pairwise attachment lacked an explicit document relation, exact dimension
transform, or two independent evidence facts. That proof-graph issue is the
next active Diagnosis, independent of the now-provisionally validated Visual
Group discovery stage.
