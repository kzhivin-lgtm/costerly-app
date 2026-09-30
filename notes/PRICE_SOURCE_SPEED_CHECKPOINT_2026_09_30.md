# Price Source Speed Checkpoint, 2026-09-30

Task: 3.15.4
Status: active, resolver and intake UX checkpoint

## Verified production measurements

The same Tsidky URL was imported twice without a Railway restart.

| Stage | First import | Warm import |
| --- | ---: | ---: |
| Global resolver index load | 8.33 s | 0.36 s |
| Deterministic resolver | 11.25 s | 7.74 s |
| Non-model work | 29.0 s | 18.4 s |

The warm import had 28 Material Identity Agent candidates rather than 18, so
its second model call was slower. This is not evidence against the resolver
speed improvements. The Source Agent and Material Identity Agent are unchanged.

## Current implementation

- Price Source result notices distinguish `Agent` from `Full cycle` time.
- Full cycle begins when the user presses Extract and ends when the result is
  ready to render in the browser.
- The immutable Israel catalog is cached by resolver version and catalog
  fingerprint.
- The cached catalog now includes safe lookup buckets for departments, material
  family tokens, exact aliases, and aliases by material.
- Compatibility and candidate ranking are unchanged after retrieval.
- A Price Source accepts exactly one input: selecting files clears a typed URL,
  and typing a URL replaces a prior file selection.

## Last file-path observation

Production photo import `photo-document-4-pages.pdf` produced 12 extracted
rows: two active, seven unresolved, and three excluded. It was classified as a
company-internal cost estimate. OCR uncertainty in the source image is the
direct cause of the unresolved rows. This import validates the file path but is
not a material-catalog or resolver benchmark.

## Next work

1. Accept the deployed mutual-exclusion UI and verify full-cycle telemetry.
2. Design a visible multi-stage Price Source progress view, without changing
   source extraction semantics.
3. Move to the Estimation foundation: operations catalog, labor-time model,
   company data precedence, and deterministic machinery routing.
