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
| V4.18 | `eba4fae` | Coverage is optional audit metadata and can never reject an otherwise usable BOM. Bounded technical traces record rare hard failures by stage without retaining raw provider output or chain-of-thought |
| V4.19 | `7bfe531` | A model's redundant evidence refs on a document-unit assumption are discarded and explicitly audited rather than rejecting an otherwise usable BOM |
| V4.20 | `156f9a1` | Object Detail exposes one physical material table: C/I/A material, required net volume, purchasable format, project-rounded purchase quantity and total. Assembly roles move to collapsed Elements, and visible material names cannot be assembly labels |
| V4.21 | `0b030ea` | Incomplete secondary assemblies and secondary items become bounded `structural_omissions`, while usable material demand continues through pricing. Structural validation traces persist a safe reason code, never provider output |
| V4.22 | `88cacbe` | Optional zero counts are interpreted as absent where meaningful or replaced with the structural default where a physical assembly requires a positive count. Remaining structural validation failures emit a bounded reason code |
| V4.23 | `a7d3a2b` | Unsupported model evidence refs are downgraded to named assumptions or a supplied full-page artifact, so they can never become false source claims or block usable BOM demand. Every V4 stage emits a bounded persisted success/failure marker |
| V4.24 | `797dc33` | Purchase-format metadata is kept out of physical dimensions, so catalog fields such as `format_source` can never break Material Plan serialization |
| V4.25 | `484c531` | Resolver uses Company Catalog first, then Israel Reference, and only then A. Sheet planning is aggregate-area estimation with 10% offcut allowance, not a finished-panel fit gate. Required Material and Purchase Quantity are persisted editable inputs |

Rule from 2026-11-02: every subsequent Estimation deployment receives the next
sequential V4 release number in its commit message, change note, deployment
report and any protected checkpoint. A runtime correction stays in its own
numbered release even when it reuses an existing immutable contract version.
