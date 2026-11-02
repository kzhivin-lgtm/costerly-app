# Estimation V4 release sequence

This is the authoritative deployment numbering for the material-only
Estimation V4 line. A release number labels a user-facing runtime increment,
not an internal immutable fact-contract suffix.

| Release | Published commit | Runtime change |
| --- | --- | --- |
| V4.1 | `347f61b` through `773937c` | Bounded, page-accountable immutable evidence batches |
| V4.2 | `497bcbc` | Persisted bounded material facts under an additive result contract |
| V4.3 | `4246eb2` | Object-to-Estimate and deterministic BOM foundation |
| V4.4 | `16c0f1e` | Mandatory priced Assumption Price contract |
| V4.5 | `0c70004` | Assumptions made non-blocking for the customer result |
| V4.6 | `9d5266d` | Material Engine prices every unresolved material through A |
| V4.7 | `c7482f8` | Full geometry brief, wardrobe/cabinet BOM runtime and Catalog Gap initiation |
| V4.8 | `b9e35c9` | Correct V4.7 purchase-plan grouping and terminal completion state |
| V4.9 | `9796ba3` | Simplify Formica to LDSP, keep paint only as a finish, and preserve separate visible fittings |
| V4.10 | `d0f1ac2` | Keep geometry and material-plan progress truthful, and end technical material-plan failures instead of displaying an unconfirmed 70% state |
| V4.11 | `5874031` | Interpret an implausible unitless cabinet dimension set as centimetres with an explicit assumption, and bound sheet-fragment expansion before nesting |
| V4.12 | `3e7c04c` | Assembly-first BOM: immutable TU Wien-inspired number, native-vector-line and Detection-view graph; bounded visual batches with reconciliation; no `object_kind` recipe; no fictional splitting of an oversized finished panel, with a dimension-compatible priced A fallback instead |
| V4.13 | `76d51fb` | Assembly BOM dimensions preserve the cited source value and unit, then deterministically normalise `mm`, `cm` or `m` to millimetres. Unitless drawing conventions are explicit named assumptions, and every board part carries an explicit or assumed thickness |
| V4.14 | `b5bdf53` | Structural BOM composer: the visual stage emits document unit, large physical assemblies, source dimensions and shown counts; deterministic code expands them into conventional panels, drawer parts and discrete fittings before estimate-wide C/I/A purchasing. Object Detail shows a minimal `C`, `I` or `A` price-source marker |
| V4.15 | `3e5eb94` | Unit interpretation is model-led: the visual stage reads the dimension lines and object scale as a whole, declares one source-cited or assumed document unit, then the deterministic composer converts it consistently. Non-dimensional document metadata is not input |
| V4.16 | `1cee460` | Objects terminal refresh remains inside its timed fragment. Completion renders persisted terminal rows directly and does not start an app-wide rerun that can replay File Review navigation |
| V4.17 | `72c946f` | OCR Dimension Scale Gate constrains unitless micro-scale furniture to centimetres, coverage ledger prevents silent visible-region omission, and Object Detail shows whole project purchase units separately from allocated object cost |

Rule from 2026-11-02: every subsequent Estimation deployment receives the next
sequential V4 release number in its commit message, change note, deployment
report and any protected checkpoint. A runtime correction stays in its own
numbered release even when it reuses an existing immutable contract version.
