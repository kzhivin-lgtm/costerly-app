# Labor2.11: aggregate disclosure, hours and numeric axes

23November2026, work3.17.4.6. Base: published2.10/runtime20e34aa1, records
ca113847. Accepted full checkpoint9.48/runtime862e28f0 remains immutable.
Candidate, publication and owner acceptance pending.

Owner corrected the original arithmetic report:6.9+14.9+6.5=28.3h. The preparation
children2.5+4.0 are already included in6.5. No allocation/payroll change is needed.
Root Labor now shows rounded total hours alongside money, including collapsed.
It uses the exact existing total passed to Overhead; browser drafts update both
from the same totalHours. Exact source attributes support drift assertions.

Expanded Part Production, Assembly and Preparation and Packing hide their own
hours/pay/taxes/total, leaving name/toggle. Native collapse restores values.
Hide with visibility, retain DOM values for existing draft aggregation. Leaf
metrics/editors remain visible with breakdown open. Four stages stay present.

Nested aggregate-body horizontal padding previously narrowed child grids.
Only nested titles are now indented. All metric cells use full-height centered
content; the first money-pair child now follows the same vertical rule. Reuse
the existing coalesced alignment guard on native Labor toggle, since the existing
mutation filter watches data-stale, not open. The listener is scoped to Labor,
runs once per native disclosure, is cancelled/replaced by the existing rAF and
removed on guard cleanup. No extra polling, observer, network, writer or rerun.

Verification: screenshot28.3h regression, actual nested text centers and header
axes at desktop/mobile/old wrapper/restored document, aggregate hide/restore,
leaf edits, exact shared hours during edits and saved reopen, failure/retry and
all mandatory UI checks. Evidence: outputs/labor-alignment-20261123/.
No paid model call, Detection/Parts/Materials algorithm or persistence change.

Rollback: published2.10/runtime20e34aa1 via the same protected publication gate.
Do not mistake a published candidate for an owner-accepted checkpoint.

Display boundary check: Python Overhead previously rounded100.25h to100.2h,
while Labor/JS showed100.3h. Use shared half-up one-decimal display for Labor
and Overhead, including saved/reopened rows; allocation retains exact100.25h
and all costs are unchanged. Tests cover100.25,140.75,1.15 and28.3h.
