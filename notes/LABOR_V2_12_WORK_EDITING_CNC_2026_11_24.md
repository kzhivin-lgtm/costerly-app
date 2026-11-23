# Labor 2.12: editable terminal work and CNC presentation

Owner authorized24November2026, existing work3.17.4.6. Base is the completed
full Labor2.11 preservation checkpoint: runtime63db313d, records099f9180,
835 byte-matched source files and four network-blocked material controls.
Published and served builds verified. Owner production acceptance pending.

## Approved behavior and decisions

Only terminal work is editable. The owner explicitly confirmed that departments,
any row with children, and total Labor remain computed. Known zero-hour work and unknown terminal hours are editable. Unknown stays
unknown until explicit manual input, including an intentional zero. Keep the existing one-
decimal0-1,000,000-hour validation and the same per-item override storage/writer.
Edit coating, Block/Additional Assembly, checking, packing and CNC Operator,
File Preparation and Edge Banding. Defaults remain the same physical norms.
Taxes & Social +25% names the existing payroll load, not an additional charge.

An explicit CNC route shows Elements and CNC time breakdown under Sheet
Processing. The latter contains the three paid-work rows; Operator can expand
the unchanged machine-minute evidence. Remove duplicate stock/material,
in-house/subcontractor comparison and supplier-rate tables from this route.
Other machinery routes retain the existing calculation and comparison view.
Legacy saved Sheet Processing total overrides remain a proportional total basis
for the CNC split; explicit new operation edits replace only that operation's
share. Original norms and old override rows are retained. No migration or model
request is triggered by opening a saved estimate.

One shared labor_work_metrics tree feeds display, saved Labor/Overhead/Self Cost
and Objects. Existing labor_blocks compatibility metadata remains; additive
labor_work stores the detailed receipt basis. Browser preview walks terminal
rows, rolls them into ancestors once, and preserves the original combined CNC
payroll rounding. No new callback, request, poll, worker or separate Save path.

Work rows are contiguous, with title-only indentation and no aggregate-body
padding gaps. Overhead has one column header above all categories; collapsed
category amounts follow the same Cost column as their child rows. Root amounts,
fixed Privacy, native disclosures and save/navigation behavior stay protected.

## Verification scope and retained failures

Evidence: outputs/labor-v2.12-20261124/.
Python: default payroll/source invariance, old aggregate overrides, every new
leaf's per-item save/quantity roundtrip, unknown/explicit zero, aggregate editing
rejection, actual CNC output, full saved Self Cost and one Overhead header.
Browser at1280/390: all terminal editors, no parent editor, input clicks retain
native disclosure state, failed Save/retry, all new leaf values saved/reopened,
correct Overhead/Self Cost/Objects, equal42px row heights, numeric/text centers,
contiguous Labor boundaries and shared Overhead axes/header. Earlier full gate
scenarios remain required, including Front panels, commercial copies and auth.

The first protected Front panels Save exposed editable packing falling from0.25h
to0.08333h in a legacy receipt without detailed work metadata: fallback hour
scaling divided by commercial quantity3 instead of priced configuration1.
Root Labor now carries its physical cost quantity, and acknowledgement fallback
scales against that same basis. The server total was already correct; the old
expected1118.13 source total is retained. A diagnostic assertion preserves all
original hour values. Another focused run required the Packing disclosure test
to click its title, because the new center input correctly prevents toggling.
No protected expected amount or geometry tolerance was relaxed.

Rollback: exact full2.11 checkpoint through the normal exact-SHA UI gate and
publisher. No paid model call, Detection/Parts/Material Plan algorithm change or
production-project test write is part of this release.

Unknown-hour completion reuses the existing Save receipt and shared Overhead
renderer once when a previously pending host becomes ready. Ready Overhead
hosts keep their nodes/disclosure state, all hour editors remain mounted, and
response scope must match object/run/estimate. Clearing an unsaved unknown-hour
edit restores unknown, not0. No extra read/request/writer/callback is added.
Real partial receipt testing exposed section columns being lost in the detail
cache on Save/reopen. Merge new rows into the existing section metadata instead
of replacing its schema. Preserve geometry, source facts and all previous state.

The general input baseline initializer previously turned an unknown hour field
into an empty-string baseline, which JavaScript treats as0. Skip unknown Labor
baselines in both initial seeding and legacy mark-saved handling. The isolated
unknown-hour scenario now passes untouched focus, explicit0, clearing, first
manual Save/Overhead completion and subsequent Save with retained disclosures.
Measured mobile title widths explained two wrapped49.21875px rows; title-only
spacing changes retain the font/material axes and yield42px for all12 rows.

A legacy manually edited total with an all-zero calculated CNC split is retained
as manual Operator hours, not invented Edge Banding demand. Technical evidence
under a work row is not another paid-work node; only paid child work makes a
summary computed. Each charge is still included once.

Rollback limitation: after users save new2.12-only hour keys,2.11 cannot interpret
those new keys. A later rollback must preserve the2.12 paid-hour overrides and
cost snapshots before repricing, rather than silently discarding their financial
meaning. The full2.11 checkpoint has no live database snapshot; this release
introduces additive metadata, not a destructive migration.

## Publication evidence

- Runtime `46e01b5d90e4343c3724afe682f20a4b72a629a2`, build `labor-v2.12-b20261123225823-leaf-hours-cnc-detection-v8.4.29`.
- Full local 1015 Python checks/ten browser suites passed in 405.642s.
- Exact-SHA [GitHub UI release gate](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/45284915978/job/138078636238) passed 1015/ten in 375.79s,
  artifact 14870953615. The established publisher separately
  verified active/no-bypass main rule27499066 and promoted this exact source.
- Core, executable wrapper, metadata and HTTP200 version.json match; read-only
  DOM receipt recorded at 2026-11-23T23:12:43.481293+00:00. This is separate from owner
  production UI acceptance, which remains pending.
- Actual geometry measures12 work rows at42px on both1280/390, with existing1px
  numeric-axis and2px actual-text tolerances unchanged. Both screenshots reviewed.
- Original monetary assertions remain, including legacy Front panels1118.13 and
  the old paid-hour flow. New six-field batch Save/reopen verifies105.8h,
  Labor6612.50, Overhead1058 and configured-item Self Cost8670.50.
- Real unknown-hour control passes untouched focus, explicit0, undo, first1h Save
  completing Overhead and later2h Save keeping healthy disclosures. Source evidence
  stays unknown where no manual override was entered.
- Full2.11 checkpoint source835 files and separate records/source tags are
  independently restorable. New release source838 files is retained separately
  with helper-validated backup receipt, CI artifact, logs and build proofs.
- No paid request, new Detection/Parts/material algorithm or production-project
  test write. Initial failed tests, geometry probes and their fixes are retained.
