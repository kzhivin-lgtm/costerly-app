# Labor2.11: aggregate disclosure, hours and numeric axes

23November2026, work3.17.4.6. Base: published2.10/runtime20e34aa1, records
ca113847. Accepted full checkpoint9.48/runtime862e28f0 remains immutable.
Published and build identities verified. Owner production acceptance pending.

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

## Publication evidence

- Runtime `63db313d8dbb1e6b8ecec5a05135fe4f2c6d7afc`, build `labor-v2.11-b20261123213531-disclosure-hours-detection-v8.4.29`.
- Full local 999 Python checks and ten browser suites passed in473.687s.
- CI provisioned Chromium in268s (job step21:37:08-21:41:36UTC); this setup
  delay is separate from the contract runtime below.
- Exact-SHA [GitHub UI release gate](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/45271419885/job/138031904780) passed999/ten in346.847s,
  artifact14865333744. Protected publisher verified active/no-bypass
  main rule27499066 separately before promoting this exact runtime.
- Actual Core, wrapper executable/meta and HTTP200 version.json match. Receipt recorded at
  2026-11-23T21:50:55.013839+00:00. This build probe is not owner-project UI acceptance.
- Nested text geometry: all four desktop/mobile/wrapper/document cases satisfy
  the existing1px numeric axes and2px text-center tolerance. Screenshot reviewed.
- Controlled saved-hour flow checks140.75h displayed140.8h and100.25h displayed
  100.3h, unchanged costs and matching exact Overhead basis, including saved reopen.
- Helper-validated runtime source ZIP retained in runtime-backup.json, all bytes compared; existing
  exclusions and5MiB cap preserved. Receipts/logs/artifacts retained under outputs.
- Initial focused run caught compact-header CSS precedence; corrected. A focused
  calculation loaded earlier uppercase H CSS before the final stylesheet change.
  The next run exposed a test reading a still-collapsed Overhead group, then a
  boundary rounding inconsistency. The group now opens explicitly and one-decimal
  hours use half-up display in Python/JS. Both fresh final local and remote gates passed.
- No paid call, production-project data write or accepted-checkpoint replacement.

## Full preservation checkpoint,24November2026

[verified] Full Labor 2.11 preservation checkpoint requested 24 November 2026,
work 3.17.4.6. Runtime63db313d is pinned independently of records. Preserved835
exact source files (4,771,308-byte helper-validated ZIP), full999/ten local and
exact-SHA GitHub evidence, publication/served-build receipts, screenshot witness,
Git bundle, SHA256 manifest and frozen Parts/material controls. Fresh restore
matched all source bytes; four material controls passed with network blocked.
No redeploy, fresh calculation, paid call or live database snapshot. The owner
requests preservation before2.12, while reporting unequal Labor row heights;
this is a known limitation, not a claim of perfect UI acceptance. Earlier9.48
and all older immutable checkpoints remain.
[Checkpoint and restore](LABOR_V2_11_PRODUCTION_CHECKPOINT_2026_11_24.md).
