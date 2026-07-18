# OCR Lab

OCR Lab compares versioned Mistral OCR configurations before they are enabled in
the production RFQ flow.

## Profiles

- `basic`: fast OCR for text, metadata, tables, and structural blocks.
- `evidence`: OCR plus literal transcription of text inside extracted image
  regions. It returns text occurrences, simple evidence categories, page/image
  references, and approximate regions. It forbids product naming, summary,
  counting, and commercial grouping.

## Run

```bash
.venv/bin/python -m tools.ocr_lab /path/to/file.pdf \
  --profile evidence \
  --expected tests/ocr_cases/page-23.expected.json
```

Results are written to `outputs/ocr_lab/` and intentionally excluded from git.
`<file>_evidence.json` contains the exact normalized OCR package stored in
Supabase. `<file>_evidence.report.json` contains runtime and quality metrics.

## Current page-23 baseline

| Profile | OCR time | Literal evidence recall |
| --- | ---: | ---: |
| `basic` | 0.30 s | 15% |
| removed semantic profile | 5.55 s | 55% |
| `evidence` on original low-resolution PDF | 13.95 s | 65% |
| `evidence` after 200 DPI page rendering | 5.07 s | 95% |

The evidence profile is collected and stored but is not passed to Detection
until it passes the quality and total-latency gate.
