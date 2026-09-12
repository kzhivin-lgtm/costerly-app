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
