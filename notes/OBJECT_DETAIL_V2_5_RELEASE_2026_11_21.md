# Object Details V2.5 release

Status: owner-approved design and publication, candidate under verification.
Accepted rollback: Objects V2.4 runtimea8b08ba5, with its full checkpoint intact.
Build: `object-details-v2.5-b20261121155644-compact-estimation-v3.2-detection-v8.4.29`.
This is the existing Object Details interface continuation; no new work block,
costing/model version or hierarchy number is assigned.

The owner-approved compact design keeps Object title and native menu anchored,
uses a240x164px contained preview and name/quantity row, removes AI Confidence,
starts Materials/Labor/Overhead closed, and exposes useful existing detail only.
Material rows stay flat. Material/Work duplicate column labels are empty.
Overhead groups are white when closed and pale purple when open. Self Cost (SC)
shares the final amounts' axis. Incomplete-calculation captions/Subtotal labels
are removed from this view, without replacement warnings or changed numeric data.

Implementation is confined to view renderers/CSS and synchronized build markers.
No input guard, controller, browser auth, shared header, Object Detail screen
handler, cache, persistence, costing or model code changes. Existing update hooks
and data attributes are retained, including live Labor/Overhead/net/VAT totals.
The existing local native disclosure is reused, without a new observer, timer,
request, writer or rerun. The prior partial audit remains internally available.

The [approved contract](OBJECT_DETAIL_V2_2_1_UI_CONTRACT_2026_11_18.md)
and [protected behavior](UI_GUIDELINES.md) govern acceptance and publication.
Private receipts and full local/CI/live evidence reside in
`.ui-artifacts/object-details-v25-release/`. The first browser probe exposed
an old760px default on the newly separated mobile Labor heading, versus the
609px material grid. Its scoped CSS was corrected; unchanged alignment assertions
then passed. The second probe passed navigation/calculation in97.839s. Final
exact-commit full gates, source isolation and production build checks follow.
Preflight:72 focused tests passed. All443 other protected files match the
V2.4 runtime byte-for-byte;54 non-presentation functions in the touched modules
are AST-identical. Local view corrections also align the three collapsed
amounts and restore the approved8px gaps, without touching the editor/controller.

Synthetic local/CI tests do not establish authenticated owner production
acceptance. No paid model run or production project edit is part of this release.
