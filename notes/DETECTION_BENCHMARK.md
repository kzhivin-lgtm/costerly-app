# Detection Agent benchmark

## Current no-cache baseline

- Date: 2026-07-22
- Environment: local Streamlit, port 8501
- Detection prompt: `detection_v3_2_6_ocr_identity_reconciliation`
- OCR contract: `ocr_v2`
- Architecture: PDF visual analysis plus OCR evidence
- Anthropic prompt/document cache: disabled
- Backup: `v3.0.27_detection_v3_2_6_object_boundaries`

Application-level file and OCR result caching is disabled for benchmark runs.
Anthropic input prompt/document caching is also disabled by default. Enable it
later for production with `DETECTION_INPUT_CACHE_ENABLED=true`.

## page-23.pdf

Expected commercial objects: 3.

| Run | OCR | Detection | Total | Objects |
|---|---:|---:|---:|---:|
| 1 | 6.236 s | 12.476 s | 20.273 s | 3 |
| 2 | 5.658 s | 14.890 s | 23.799 s | 3 |
| 3 | 5.851 s | 12.465 s | 19.652 s | 3 |
| Median | 5.851 s | 12.476 s | 20.273 s | 3 |

Object boundaries and metadata are stable. All three runs return one shelving
unit, one sliding-door system, and one console; component leaves are not split.
External dimensions remain a separate known issue.

## Металл (1).pdf

Expected commercial objects: 15, including distinct ЛП-1, ЛС-1, ЛС-2, and МП-1 positions.

| Run | OCR | Detection | Total |
|---|---:|---:|---:|
| 1 | 19.040 s | 30.094 s | 51.800 s |
| 2 | 9.512 s | 30.285 s | 41.998 s |
| 3 | 22.486 s | 31.878 s | 57.715 s |
| Median | 19.040 s | 30.285 s | 51.800 s |

All three runs returned the expected 15 objects and stable quantities. OCR
returned byte-identical evidence in 9.512–22.486 seconds; the wide total range
comes from provider OCR latency, while Detection remained at 30.094–31.878
seconds. External dimension axes remain a separate known issue.

## 20.10.2023_Furniture.pdf

Expected commercial objects: **27**, corrected after the product owner inspected
the object sheets on 2026-09-14. The earlier 23-object target was wrong. The
table of contents is useful package evidence, not the final authority: the
object sheets contain reused and conflicting codes.

Canonical physical membership:

- `CM-1.1`, `CM-1.2`, not the parent heading `CM-1`;
- `CM-2`, `CM-3`, `CM-4`, `CM-4.1`, `CM-5`;
- two independent `CM-6` products: bathroom vanity and door/panel assembly;
- separate `CM-7.1` and `CM-7.2`, not an extra parent `CM-7`;
- `CM-8`, `CM-8.1`, `CM-9`, `CM-10`, `CM-11`, `CM-12`, `CM-13`,
  `CM-14`, `CM-15`, `CM-16`, `CM-16.1`, `CM-17`, `CM-18`, `CM-19`;
- two independent `CM-20` products: bench pillows and wooden shelf/ledge.

The `CM-11/CM-12` sheet internally mislabels its two chair bodies as `CM-10`.
The `CM-17/CM-18` sheet labels the second, quantity-four product as `CM-17`.
Resolve these against sheet titles, product bodies, dimensions, and quantities;
do not create `CM-17.1` or a dimensionless extra `CM-18`. A benchmark match
requires the correct physical products, not merely the total count or a flat
set of code strings.

The source is a 27,904,163-byte, 39-page A3 production drawing package. The
original monolithic PDF fails Anthropic document processing even through the
Files API. A 96-DPI page-image experiment produced:

| Variant | Render | OCR | Detection | Effective total | Objects |
|---|---:|---:|---:|---:|---:|
| JPEG pages + OCR | 3.872 s | 36.397 s | 42.151 s | 78.548 s | 17 |
| JPEG pages, no OCR | 3.872 s | 0 s | 75.038 s | 78.910 s | 23 |
| Integrated JPEG, no OCR, run 1 | 3.892 s | 0 s | 68.683 s | 74.170 s | 26 |
| Integrated JPEG, no OCR, run 2 | 3.722 s | 0 s | 80.991 s | 85.513 s | 26 |

`Effective total` assumes JPEG rendering runs concurrently with OCR. The
sequential sum for the OCR variant is 82.420 seconds. These are historical
experiments measured against the superseded 23-object target. Under the
corrected 27-object target, count alone cannot establish their quality.

## Historical cached-input reference

Backup `v3.0.24_detection_v3_2_2_speed_quality_baseline` used Anthropic
prompt/document caching. Its medians were 20.963 s for `page-23.pdf` and
43.976 s for `Металл (1).pdf`; these values are retained only for historical
comparison and are not the active benchmark.

The previous no-cache metadata checkpoint
`v3.0.26_detection_metadata_no_cache_baseline` had medians of 23.035 seconds
for `page-23.pdf` and 51.831 seconds for `Металл (1).pdf`, with Detection
medians of 13.891 and 36.813 seconds respectively.

## Acceptance rules

Quality has priority over speed. Compare candidates on the same files with at least three fresh runs and use the median, not one run.

- `page-23.pdf`: retain 3 correct commercial objects; investigate a median total above 25 seconds.
- `Металл (1).pdf`: retain 15 correct commercial objects; investigate a median total above 53 seconds.
- `20.10.2023_Furniture.pdf`: compare all 27 physical products and their boundaries, including the two `CM-6` and two `CM-20` products; the monolithic PDF route is not acceptable because it fails before returning JSON.
- Accept a material slowdown only when it produces a clear, reviewed quality improvement.
- Treat fallback retries and validation failures as separate diagnostics rather than normal benchmark samples.
- Never enable application-level result caching during development benchmarks.
- Keep Anthropic input caching disabled while measuring fresh-file behavior.

For quality review, compare object boundaries, short names, quantities, and every external W/H/D axis. Matching object count alone is not sufficient.

## Rejected naming experiments

V3.2.7 and V3.2.8 attempted to enforce compact bilingual names inside one
free-form `object_name`. V3.2.9 separated index, English name, and original name
in the Detection response and assembled the UI label in Python. These versions
were rejected: naming compliance remained inconsistent, page-23.pdf regressed
to four objects and quantity 2 in one run, and V3.2.9 medians increased to
28.160 s for page-23.pdf and 50.297 s for Металл (1).pdf.

The additive Supabase columns `object_index`, `object_name_en`, and
`object_name_original` may remain in the database. V3.2.6 does not read or write
them, so no destructive rollback SQL is required.

## Direct PDF + Naming Split v3.0.30 baseline

Backup: `v3.0.30_experimental_direct_pdf_naming_split_checkpoint`.
Despite the historical archive slug, this checkpoint is the accepted stable
baseline and its flow is active by default in production.

The active flow sends the original document to Mistral once, removes
user-facing naming from Detection, and applies a separate Naming Agent after
the object list is locked. The former rendered-page OCR route remains only as
an explicit rollback path.

Three accepted repeated runs of `Металл (1).pdf` produced:

| Run | OCR | Detection | Naming | Total | Objects |
|---|---:|---:|---:|---:|---:|
| 1 | 1.061 s | 30.124 s | 4.298 s | 38.216 s | 15 |
| 2 | 0.798 s | 30.913 s | 4.390 s | 38.586 s | 15 |
| 3 | 0.960 s | 29.508 s | 4.461 s | 38.308 s | 15 |
| Median | 0.960 s | 30.124 s | 4.390 s | 38.308 s | 15 |

All three OCR results contained 11 pages and 633 literal evidence items.
Commercial object boundaries stayed correct, including distinct LS-1, LS-2,
and LP-1 positions. External dimensions varied materially between identical
OCR handoffs, so dimension binding remains the next quality task.

The sub-second OCR repeats may include provider-side deduplication of the same
PDF. They must not replace the cold-user benchmark until Direct PDF is tested
on previously unseen or byte-unique documents. `page-23.pdf` also returned two
objects in one of four Direct PDF runs, so that quality variance remains an
open issue even though v3.0.30 is the active baseline.

## Restored API-compatible checkpoint — 2026-09-12

Checkpoint commit: `bb7c712`.

After restoring one-request Direct PDF OCR and the Detection + text-only Naming
split, the user-visible runs returned to approximately 23 seconds for
`page-23.pdf` and 43 seconds for `Металл (1).pdf`. The corresponding persisted
cycle timings were 19.925 seconds (OCR 0.864, Detection 12.801, Naming 4.380)
and 41.551 seconds (OCR 1.271, Detection 26.928, Naming 11.138).

This is a recovered speed checkpoint, not a new quality acceptance baseline;
object-boundary quality remains subject to the existing 3-object and 15-object
acceptance rules.

## Compact Naming input — 2026-09-12

Naming v4 keeps locked identifiers, existing labels, evidence pages, up to 300
characters of Detection context, and capped OCR snippets. It no longer repeats
dimensions, materials, or complete notes. The serialized Naming payload was
reduced by approximately 30% for `page-23.pdf` and 41% for `Металл (1).pdf`
relative to the full text-only input.

Observed Naming time fell from 4.380 to 2.934 seconds for `page-23.pdf` and
from 11.138 to 2.650 seconds for `Металл (1).pdf`. Product categories recovered
after the context hint was added, while original-language labels remain less
consistent. Detection object-count variance is evaluated separately because
Naming runs only after the object list is locked.

## Asynchronous Supabase diagnostics — 2026-09-12

The authoritative RFQ run and detected objects remain a synchronous File Review
dependency. Full OCR JSON and OCR, Detection, Naming, and cycle usage events now
leave the critical path and are inserted afterward as one background batch.

The verified `page-23.pdf` cycle completed in 18.512 seconds (OCR 0.700,
Detection 13.431, Naming 3.420); its unclassified persistence/orchestration tail
was 0.961 seconds versus 1.940 seconds in the preceding run. The verified
`Металл (1).pdf` cycle completed in 28.664 seconds (OCR 1.192, Detection 24.393,
Naming 2.536); its tail was 0.543 seconds versus 2.850 seconds. All four events
and complete OCR payloads were subsequently present in Supabase; the stored OCR
payloads were approximately 7 KB and 229 KB.

This persistence change cannot alter Detection semantics. The large-file run
returned 13 rather than the 15 acceptance objects, which remains an independent
upstream Detection variance tracked by the existing acceptance benchmark.

## Deferred Naming checkpoint — 2026-09-12

Naming v4 now starts only after the provisional Detection result is stored, so
File Review no longer waits for Naming. The screen opens with locked provisional
labels and replaces only unchanged names when the background result arrives.

The first local user-visible laps were approximately 16 seconds for
`page-23.pdf` and 29 seconds for `Металл (1).pdf`. Persisted critical-path cycles
were 13.177 seconds (OCR 0.967, Detection 11.805) and 26.649 seconds (OCR 1.160,
Detection 24.427). Background Naming took 2.526 and 9.335 seconds respectively
and is excluded from Total lap. The remaining 2–3 user-visible seconds occur in
the final Streamlit transition and File Review load.

This checkpoint improves perceived latency but does not change Detection. The
same runs returned 4 and 13 objects rather than the 3 and 15 acceptance targets,
so object-boundary stabilization remains the next prompt task.

## Semantic-category Naming V5 — 2026-09-12

Naming V5 keeps the compact text-only background route but no longer accepts an
object index or proper/model name as a complete product name. Every English
label must identify the physical product category; an explicit model name may
be retained only alongside that category. The application now joins the index
and semantic label with a space instead of a dash.

The local qualitative check produced useful category-bearing names and about
2.9 seconds of background Naming. The tested large-file Detection result held
13 objects, which is below the 15-object acceptance target and remains an
upstream Detection issue. Some source-language labels present in local OCR,
including an OM15-1 railing label, were not returned consistently; that is the
reason V5.1 adopts a single English-only MVP label instead.

V5.1 returns one 2–3 word English semantic label; explicit proper/model names
may be transliterated when useful. The application renders `index + name` with
a space, without a dash, parentheses, or source-language duplicate. The compact
text-only background route is unchanged.

## Key rollback checkpoint — Detection 3.2.6.1 — 2026-09-13

Detection 3.2.6.1 deliberately keeps the effective Claude prompt byte-identical
to the accepted 3.2.6 no-naming prompt. Its only user-facing change is the File
Review heading `Detected Objects: N`, where Python computes `N` from the object
list already loaded for rendering. This code runs after the measured processing
cycle and makes no OCR, Claude, or Supabase request.

The user-designated verification set produced:

| File | OCR | Detection | Total | Objects |
|---|---:|---:|---:|---:|
| `page-23.pdf` | 0.934 s | 13.698 s | 15.293 s | 4 |
| `Металл (1).pdf` run 1 | 1.386 s | 28.263 s | 30.293 s | 13 |
| `Металл (1).pdf` run 2 | 1.281 s | 27.526 s | 29.381 s | 13 |
| `Металл (1).pdf` run 3 | 1.917 s | 28.156 s | 31.168 s | 15 |

This is the key code and UX rollback point requested by the user. It does not
replace the earlier 3-object and 15-object quality targets: Detection output
still varies on both benchmark documents and remains the next investigation.

### Detection/UI 3.2.6.2 — persisted File Review names

The 3.2.6.2 checkpoint keeps the same effective Detection prompt and adds one
post-Detection behavior: committing an object-name input with Enter or blur
immediately updates `rfq_detected_objects.object_name`, synchronizes the local
File Review cache, and leaves the active screen unchanged. The persistence path
was verified directly in Supabase on `unknown_project_run_001`, `object-002`,
whose edited value was stored as `Sliding door panelbjhbj`.

### Detection/UI 3.2.6.3 — Page-aware processing progress

The final Detection checkpoint keeps the exact Golden runtime prompt and
provider schema:

- effective prompt SHA-256: `682b91359ae4ac72b6329e1968360a63f37e714fa115725fa151d13a0ef676c5`;
- provider schema SHA-256: `ec673df2276cf316fa059bda8f14b064e463a96a3c6f99fa077a73d68c1ba52c`.

The rejected schema and quantity-prompt experiments are not included. The UI
change is based on 35 Golden orchestration runs, whose median backend stages
were 1.386 seconds for OCR, 25.065 seconds for Detection, and 1.011 seconds for
saving. The visible range is now 8–13% for OCR, 13–96% for Detection, and
96–99% for saving. Detection uses an ease-in curve so progress starts
conservatively and accelerates when the backend phase completes.

After OCR, the authoritative OCR page count selects only the expected Detection
pacing, without changing backend work or completion:

| OCR pages | Expected Detection pacing |
|---:|---:|
| 1–2 | 14 s |
| 3–6 | 18 s |
| 7–12 | 28 s |
| 13–20 | 45 s |
| 21+ | 60 s |
| Unknown | 28 s |

Across 36 matched Golden runs, page count and Detection time had Pearson
correlation `0.853`. Production upload time remains outside orchestration
timing because the browser progress shell starts before Streamlit receives the
file. No unverified production multiplier is applied.

### v3.0.41 - Large PDF Sonnet transport and resilient Naming checkpoint

The accepted experimental route keeps the Golden effective Detection prompt
and provider schema unchanged:

- prompt SHA-256 `682b91359ae4ac72b6329e1968360a63f37e714fa115725fa151d13a0ef676c5`;
- schema SHA-256 `ec673df2276cf316fa059bda8f14b064e463a96a3c6f99fa077a73d68c1ba52c`.

PDFs whose estimated inline Base64 payload reaches 30,000,000 bytes are
rendered into ordered JPEG pages at 96 DPI and sent as one complete package to
Sonnet 4.6. The large route skips Mistral OCR, Identity Lock, and the rejected
flat index anchor. Smaller files retain the Golden Mistral OCR plus inline PDF
route and Haiku Detection. The original PDF still remains available to the
downstream workflow; Detection receives all page images together, not separate
page-wise object decisions. Each benchmark run can append a timestamp to its
run_id so stored outputs do not overwrite earlier trials.

Naming V5.2 accepts a precise one-word physical category. A single invalid
name no longer discards valid names for the entire locked object set: only the
invalid row retains its original placeholder. Naming failures are logged and
persisted as failed usage events. This fixes the observed Naming failure caused
by one one-word category being rejected under the former 2-3-word-only rule.

Three `jpeg_sonnet_clean` runs on the 27,904,163-byte, 39-page furniture PDF
were stored under unique run_ids:

| Run | Render | Detection | Total to File Review | Objects | Naming background |
|---|---:|---:|---:|---:|---:|
| 1 | 6.836 s | 141.315 s | 149.371 s | 25 | 17.011 s, succeeded |
| 2 | 6.743 s | 139.057 s | 146.470 s | 26 | 18.011 s, succeeded |
| 3 | 6.656 s | 114.593 s | 121.846 s | 27 | 5.320 s, succeeded |

All three runs used 67,278 input tokens and generated 5,735-5,991 output
tokens. Detection cost was $0.288-$0.292 per run. The median total to File
Review was 146.470 seconds. JSON generation after the first token was stable
at approximately 80-82 seconds; first-token time ranged 32-61 seconds.

This is a working transport and Naming checkpoint, **not a 27/27 quality
acceptance**. Run 1 missed the second `CM-6` and the pillow `CM-20`. Run 2
found both `CM-6` bodies but joined pillows with the wooden `CM-20`. Run 3
again missed the pillows, created a weak/dimensionless `CM-18`, and labelled
the quantity-four `CM-18` body as a second `CM-17`. The count 27 was therefore
accidental. File Review remains required before estimating this package.

Known limitation: the one-call image route rejects PDFs over 100 pages because
the provider request cannot contain more than 100 images. A universal route for
such packages is still pending. The rejected duplicate-identifier addendum,
OCR-plus-Identity-Lock path, and local index anchor are not part of this
checkpoint.
