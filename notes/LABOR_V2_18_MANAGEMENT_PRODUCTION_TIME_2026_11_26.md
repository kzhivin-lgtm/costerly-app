# Labor2.18: Management, Production time and terminal work rows

Owner authorized26November2026. Public release number2.18 is explicit.
Base runtime57a88923/Labor2.17; source and accepted full2.16 checkpoint remain
preserved. Existing Labor work3.17.4.6 continues. Implementation/verification
in progress, no publication claimed by this initial record.

## Owner decisions and before/after

- Project heading: show `Project <saved File Review Project name>`, preserving
  the actual value, including A3. Empty/Unknown gives only Project. No ADA/A3
  recognition, Detection, document identity or Naming repair is authorized here.
- Production time: before Delivery, ordinary numeric input matching the
  existing service fields. Positive whole working days after payment, until
  ready for delivery. Owner explicitly reconfirmed delivery/installation are
  excluded. Fifteen days permits delivery from day16, without booking a date.
  Copy: `Working days after payment` / `Delivery & installation excluded`.
  No final sentence period. Fifteen is an illustration, not an assigned default.
- Project Price/VAT figures: same mono family and30px as Project Total,
  weight400, black. Project Total remains purple and weight700. Labels unchanged.
- Coating: replace2.17 reference table with the same compact list treatment as
  Trial Installation/Packing. Finish, m², min/m², hourly rate and inclusion of
  batch preparation remain visible.13.2h versus17.26m² is not an hours conflict.
- Terminal work without actual details has no disclosure or expanded gap.
  Actual details remain expandable, terminal hours editable and all four top
  stages visible. No arbitrary change to the reconsidered2h CNC estimate.
  Inapplicable zero Edge Banding is absent; an applicable operation manually set
  to0 and nonzero saved work remain visible/editable.
- Management & Administration: first Overhead category in Profile and each
  object, read-only. Sum active Management/Office total_monthly_cost values,
  already including employer costs. Allocate by exact object Labor hours /
  existing Production capacity. No second employer load and no salary VAT in
  Profile. Current scoped read of the owner's company gives46250ILS/month.

## Existing paths extended

Production days reuse the current rfq_estimate_pricing_overrides table, authenticated
browser writer, per-estimate/object pending-write queue, retry and Set Prices /
proposal acknowledgement protection. Key __project__, field
production_time_working_days, separated from sale_price_unit and every financial
total. Saved value is reloaded and frozen into the approved proposal snapshot;
the existing PDF builder includes it. No new writer, route, timer or worker.
The field reuses Delivery's contenteditable renderer. An initial native-input
experiment cleared its value before blur during the browser replay and was
discarded. The corrected Project replay passed. Failed saved-override reads now
propagate through existing retry/error handling rather than masquerading as
missing saved prices/terms.
Owner applied [the additive constraint migration](../db/sql/2026_11_26_project_production_time.sql).
A deliberately invalid negative term was rejected by the new constraint23514;
no row was changed. RLS, grants, old values and sale-price support are unchanged.

Management reads only company-scoped monthly totals, not worker names or other
personal fields, and rejects incomplete/truncated aggregates. Profile reuses
its existing metrics cache and invalidates the company entry on employee writes.
Object costing derives the same monthly value through the existing Overhead
context, source audit, basis hash and allocator. No duplicated payroll record.

The shared work-detail list renderer is used by Coating/Trial Installation/
Packing. Existing receipt reconciliation retains row and hour-input nodes;
only a real leaf/disclosure change replaces its structural wrapper. No separate
Coating calculator or new refresh trigger is introduced.

Project header is emitted before starting background estimation, as before.
Its existing native placeholder projects saved metadata once loaded. Financial
and quantity input/preview/Save paths and the APPROVE controller remain intact.
The prior production APPROVE incident is not claimed fixed by this feature.

## Acceptance and rollback

Preserve tenant/auth, atomic approval, source geometry, material scope, all
prior norms/manual overrides, commercial-copy invariance, exact Labor hours in
Overhead, Profile Save/recovery and correlated continuous route coverage.
Owner approved adding one service row before Delivery and increasing Price/VAT
figure typography only. Old geometry checks remain, adjusted only for that row's
measured vertical displacement and the explicit figure typography. Rent-focused
tests still edit Rent after the new read-only Management row is inserted first.

Required: full Python and ten browser suites locally and on the exact GitHub
SHA, active strict main ruleset/no bypass, normal publisher and actual executed
Core/wrapper/meta/version parity. Owner authenticated acceptance remains separate.
Rollback runtime57a88923 through the gated publisher; the additive SQL constraint
can remain because2.17 ignores the new commercial field.

Initial focused gate stopped at10.888s on two old static presentation assumptions:
literal Project and details-only four-stage parsing. Updated to preserve the
same header-before-worker and four-stage criteria with named titles and genuine
leaf rows. It is not a successful gate. Receipt/private evidence under
/private/tmp/labor218-focused-ui; corrected focused run separate.

Focused Python passed1061 checks. Subsequent Calculation replays exposed old
details-only selectors and an all-terminal fixture without edge applicability;
criteria now retain four stages including real leaves, and the explicit edge
fixture leaves all prior exact amounts unchanged. Separate coverage asserts no
edge row without an operation and retained applicable manual0. Project replay
passed; Profile replay stopped on a redundant click of its already selected
Labor Costs tab in the added test, removed without runtime navigation changes.
These focused results do not substitute for the required final complete gates.
