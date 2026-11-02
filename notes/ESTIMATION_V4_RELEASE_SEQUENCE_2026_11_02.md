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

Rule from 2026-11-02: every subsequent Estimation deployment receives the next
sequential V4 release number in its commit message, change note, deployment
report and any protected checkpoint. A runtime correction stays in its own
numbered release even when it reuses an existing immutable contract version.
