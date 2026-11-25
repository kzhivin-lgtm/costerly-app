# Labor2.17: Coating on the shared table template

Owner authorized25November2026. Existing work3.17.4.6, exact base Labor2.16
8e7a26b3 and its preserved full checkpoint. Candidate build
labor-v2.17-b20261125215904-coating-table-detection-v8.4.29.
Verification/publication pending. No paid calls or production data mutation.

## Scope and protected behavior

Part Coating retains the existing common Labor disclosure and terminal hour
editor. Its details now use the same table header/row/cell renderer as Materials:
Finish, Coated area, Time norm, Hourly rate. Visible norms are40/45/35min/m²,
without person. Rate remains100ILS/h and payroll remains25%, once.

Initial markup and save/preview receipts use the same server-authored rows.
The existing Materials keyed row reconciler is shared with readonly reference
tables. Stable rows/table/disclosure/hour input nodes are retained. The separate
client-side Coating list builder and replaceChildren path are removed. No new
callback, timer, request, fragment, observer or navigation route is introduced.
Reference table updates occur only on the existing scoped accepted edit receipt.
Coating consumables uses the same51px minimum material-row height as its peers.

Financial formulas, inputs, quantities, saved manual hours, profile capacity,
Overhead, Self Cost, material-scope selection and all prior checkpoints remain
protected. Management & Administration is still queued, not implemented here.
The APPROVE incident remains a separate diagnostic, not claimed fixed by this
presentation change. See[the investigation](APPROVE_LATENCY_2026_11_25.md).

## Required verification

Two initial local gates were blocked by the newly added comparison fixture,
not accepted as passing: the first had only one formula row, so no height peer;
after adding real policy rows, the second exposed a missing policy-write adapter
in the fake client before File Review could enable Continue. The financial
fixture extension was withdrawn. Row geometry now renders the real table/CSS
and actual Coating consumables row separately from the unchanged saved-estimate
financial flow. No production calculation was changed to make it pass.
The original assertions/suites and the new height criterion remain strict.
The corrected isolated Calculation suite reached its final result, including
both Coating widths and both formula-row geometry cases, before the final full
local/remote gates. Its log/screenshots are in/private/tmp/labor217-coating-focused.
These failed receipts remain under/private/tmp/labor217-coating-ui-gate
and/private/tmp/labor217-coating-ui-gate-final, separate from final evidence.

An additional isolated failure (0.0 instead of5.1h on390px) was a wrong new test
click: the center of the wide Coating summary hits its hour editor, preserving
focused input across the preview. Exact2.16 replay confirms center=>hours focused,
disclosure closed; clicking the title=>open, no hour focus. The test now clicks
the disclosure title and explicitly checks open, retaining the5.1h assertion.
This is not evidence of a production calculation change or the APPROVE cause.

- Original unit and ten browser suites, unchanged financial/tenant/auth gates.
- Shared initial/receipt table rows for a mixed MDF-front/plywood-body case,
  both recipes retained, unchanged audit and no editable aggregate added.
- Desktop1280/narrow390: lacquer/oil/enamel rows and norm text update, stable
  table node, uniform material formula rows, manual hours/Overhead parity,
  Save/reopen, expanded Coating then material change/Save/APPROVE, no stale
  screen, exception or stranded cover.
- Exact-commit GitHub UI release gate before the normal verified publisher;
  actual remote enforcement and served Core/wrapper versions after deployment.

Unaccepted APPROVE IO experiments are retained in local2f24c839 and reverted
by678eb4e5. The final runtime difference contains no such optimization or
workflow diagnostic changes. The earlier interrupted gate is not this release's
verification. Existing private output/ and tmp/ are not part of the commit.
