# Detection Agent benchmark

## Current no-cache baseline

- Date: 2026-07-22
- Environment: local Streamlit, port 8501
- Detection prompt: `detection_v3_2_4_metadata_no_cache_baseline`
- OCR contract: `ocr_v2`
- Architecture: PDF visual analysis plus OCR evidence
- Anthropic prompt/document cache: disabled
- Backup: `v3.0.26_detection_metadata_no_cache_baseline`

Application-level file and OCR result caching is disabled for benchmark runs.
Anthropic input prompt/document caching is also disabled by default. Enable it
later for production with `DETECTION_INPUT_CACHE_ENABLED=true`.

## page-23.pdf

Expected commercial objects: 3.

| Run | OCR | Detection | Total | Objects |
|---|---:|---:|---:|---:|
| 1 | 6.904 s | 15.808 s | 24.018 s | 3 |
| 2 | 6.157 s | 13.891 s | 21.001 s | 3 |
| 3 | 8.891 s | 13.144 s | 23.035 s | 3 |
| Median | 6.904 s | 13.891 s | 23.035 s | 3 |

Known quality findings: object count and metadata are stable. Sliding-system
quantity varies between one complete system and two component leaves. External
dimensions remain unstable; the console incorrectly uses 1850 mm as height.

## Металл (1).pdf

Expected commercial objects: 15. The latest persisted result contains all 15, including distinct ЛП-1, ЛС-1, ЛС-2, and МП-1 positions. Both benchmark runs were accepted by the user; because both generated the same run_id, Supabase retains only the latest object payload.

| Run | OCR | Detection | Total |
|---|---:|---:|---:|
| 1 | 11.599 s | 36.813 s | 51.831 s |
| 2 | 12.954 s | 37.471 s | 53.959 s |
| 3 | 8.219 s | 26.402 s | 37.434 s |
| Median | 11.599 s | 36.813 s | 51.831 s |

All three runs returned 15 objects, including distinct ЛП-1, ЛС-1, ЛС-2, and
МП-1 positions. Quantities were stable. External dimension axes still vary and
must be improved in the dedicated dimensions block.

## Historical cached-input reference

Backup `v3.0.24_detection_v3_2_2_speed_quality_baseline` used Anthropic
prompt/document caching. Its medians were 20.963 s for `page-23.pdf` and
43.976 s for `Металл (1).pdf`; these values are retained only for historical
comparison and are not the active benchmark.

## Acceptance rules

Quality has priority over speed. Compare candidates on the same files with at least three fresh runs and use the median, not one run.

- `page-23.pdf`: retain 3 correct commercial objects; investigate a median total above 25 seconds.
- `Металл (1).pdf`: retain 15 correct commercial objects; investigate a median total above 53 seconds.
- Accept a material slowdown only when it produces a clear, reviewed quality improvement.
- Treat fallback retries and validation failures as separate diagnostics rather than normal benchmark samples.
- Never enable application-level result caching during development benchmarks.
- Keep Anthropic input caching disabled while measuring fresh-file behavior.

For quality review, compare object boundaries, short names, quantities, and every external W/H/D axis. Matching object count alone is not sufficient.
