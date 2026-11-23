# Labor 2.12: editable terminal work and CNC presentation

Owner authorized24November2026, existing work3.17.4.6. Base is the completed
full Labor2.11 preservation checkpoint: runtime63db313d, records099f9180,
835 byte-matched source files and four network-blocked material controls.
Candidate: publication and owner production acceptance pending.

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
