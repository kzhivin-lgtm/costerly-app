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

## Experimental Direct PDF + Naming Split candidate

Backup: `v3.0.30_experimental_direct_pdf_naming_split_checkpoint`.
This candidate is not yet the production baseline.

The local experiment sends the original document to Mistral once, removes
user-facing naming from Detection, and applies a separate Naming Agent after
the object list is locked. The former rendered-page OCR route remains available
as the disabled control path.

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
objects in one of four Direct PDF runs, so the candidate is not accepted yet.
