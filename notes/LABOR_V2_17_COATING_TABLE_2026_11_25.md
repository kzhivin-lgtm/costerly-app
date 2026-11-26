# Labor2.17: Coating on the shared table template

Owner authorized25November2026. Existing work3.17.4.6, exact base Labor2.16
8e7a26b3 and its preserved full checkpoint. Candidate build
labor-v2.17-b20261125215904-coating-table-detection-v8.4.29.
[verified] Published runtime57a88923bdccf55d25753fe5c396b63fdde769cb,
26November2026 local time. Owner visual acceptance pending. No paid calls or
production estimate/profile data mutation.

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

## Published verification

[verified] Full local gate on exact runtime57a88923:1054 Python checks and all
ten browser suites passed in433.777s. Its dirty flag records only pre-existing
untracked private output/ and tmp/; tracked runtime matched the committed source.
GitHub ran the full gate, not documentation-only classification:1054 checks,
six subtests and all ten browser suites passed in376.853s.
[Exact SHA gate](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/45712933595/job/139551653538).
Artifact15068178280,1,268,605 bytes, SHA256
58d20b7a77e2f0e5249c158baa082fe80acb06890022d9eea0281e5a33aa947c.
Downloaded bytes matched the provider digest. Local logs, screenshots, CI ZIP
and gate report are preserved privately in
output/labor-v2.17-coating-release-20261126/.

[verified] Normal tools/promote_ui_release.py checked the exact trusted gate and
actual remote ruleset27499066 before publication. An independent authenticated
read confirmed active/strict main enforcement and an empty bypass actor list.
Remote main is57a88923. Railway deployment75515245-5e7f-49aa-b8bc-ed7ef85cc6d0
and Cloudflare Pages f68798c0-3b9e-4c14-9349-540b7b27f85c succeeded.
At22:33:26.689UTC25November, a fresh anonymous browser observed the exact2.17
build in Core's marker, executable wrapper handshake, wrapper meta and uncached
version.json, with zero Streamlit exceptions. This verifies deployment identity,
not the owner's authenticated visual acceptance or live APPROVE responsiveness.
The separate legacy Workers Builds integration is not the Pages publication gate.

Rollback source remains the preserved Labor2.16 runtime8e7a26b3. No full2.17
archive/checkpoint is claimed. Management & Administration remains queued;
APPROVE3.15.23 remains diagnostic-only under the owner's instruction.

## Owner review26November2026

The owner reports a fresh2.17 run and successful Save. The Coating detail table
presentation is superseded by an explicit request for the compact text style
already used by Trial Installation/Packing. No empty disclosures on terminal
work and no inapplicable Edge Banding for the reported plywood item. Existing
40min/m² lacquer recipe on17.26m² gives13.205333h including small-batch setup,
so area17.26 versus hours13.2 is not an arithmetic discrepancy. Preserve this
formula and saved overrides. All requested card revisions, Management payroll,
Project title and Production time metadata are tracked in the authoritative
TODO. Current step captures requirements and an interactive Project sketch;
these subsequent changes are not part of the published57a88923 runtime.
