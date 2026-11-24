# Labor: four production stages and Prices responsiveness

Planning requested by the owner23November2026. Baseline: accepted Estimation9.47,
runtime6764b9a7, records90478cee. Existing reference3.17.4.6 is retained; no new
hierarchical number or runtime version is assigned by this plan. The authoritative
queue is notes/TODO.md. This file specifies the proposed scope, not a second backlog.
Original planning record. Owner subsequently approved steps1/2 and explicitly
requires all four Labor stages plus empty Additional Assembly to remain visible
with0 for unimplemented work. Estimation9.48 implements that scope; numerical
coating/special-assembly/packing norms remain deferred. Company settings and
source Parts/Material Plan are preserved.

## Target structure

| Labor stage | Existing implementation | Additions / boundary |
| --- | --- | --- |
| Part Production | Sheet Processing, CNC/panel-saw routes, drilling, edging and supplier comparison | Select the applicable route using company Machinery and actual operation eligibility. Retain stock, setup, operator work and source lineage. |
| Part Coating | No integrated complete runtime | Finish selected physical parts where their effective material and required finish demand it; start with Front panels MDF/veneer. |
| Assembly | Block Assembly by saved block/part roles | Retain carcass assembly and add a separate Additional Assembly subsection for LED, profiles, wiring, glass/mirror assemblies and similar sourced tasks. |
| Preparation and Packing | Not integrated as a complete labor stage | Whole-item trial fit, checks, necessary disassembly and packing of transport units. |

Materials, Labor and Overhead remain the accepted top-level cost sections.
The four stages sit inside Labor. Existing default collapsed presentation,
editing, Save/Saved, navigation locks, commercial inputs and final totals remain
protected except the explicitly proposed change from two Labor children to four.

## CNC: clarify the dependency

[verified] Current calculate_sheet_processing reads company availability and
selects CNC when in_house; it can still build the alternate panel-saw calculation.
calculate_block_assembly is a separate role/count-based manual assembly engine.
CNC does not replace assembling the machined parts into a block.

The intended interpretation is to bind Part Production to Machinery. For the
owner's stated CNC-equipped company, use the CNC route for eligible work and
remove the unrelated manual/panel-saw alternative from the active calculation
and presentation. Keep setup, loading, edging and other real operator work.
For other companies, choose the route supported by their own saved capabilities;
never apply the current owner's machine availability globally. Check operation
eligibility and subcontractor scope separately from a machine's mere existence.
This clarification is part of the proposal, not a silent change to Assembly norms.

Unfinished thick/laminated panel fabrication belongs to Part Production:
layup, gluing and pressing make a physical part. Glass-box bonding makes an
assembly and belongs to Additional Assembly. Preserve both existing open
objectives rather than counting every gluing operation under one generic norm.

Supplier-produced parts still pass through Part Production in the process.
Their purchased services remain priced once in the existing Material Plan.
Do not count an included supplier operation again as in-house labor or company
production hours. Existing payroll/VAT and cost-allocation rules stay unchanged.

## Recommended execution sequence

1. Prices responsiveness, as a separate small change before the larger Labor
   work. The owner identifies this as a near-term usability issue.
2. Introduce the four-stage structure around the existing engines and connect
   the active production route to Machinery. Preserve current hours/costs and
   saved manual overrides before introducing any additional norms.
3. Implement Part Coating first. It uses the already selected Front panels
   material and its physical part areas, finish and sides. Confirm the operation
   sequences and rates before calculating new time or consumables.
4. Extend Assembly with Additional Assembly. Use measured quantities from saved
   source evidence, not object names or an arbitrary overall surcharge.
5. Implement Preparation and Packing after identifying the actual transport
   units and distinguishing trial fitting from already charged assembly work.
6. Check full operation coverage and the final aggregate across saved Lev1,
   both distinct Lev2 controls and both Ada objects. This is deterministic
   verification first, with separate owner production acceptance after each
   meaningful release.

## Coating scope and dependencies

Inputs are saved physical part IDs/areas/quantities, effective material choice,
required finish, treated sides and edges, and in-house/supplier execution.
LDSP requires no new surface coating unless source/owner specifications request
it. Raw MDF and veneered MDF need their agreed preparation/finishing sequences.
Plywood follows its specified finish rather than a universal invented rule.
Potential operations include preparation, sanding, priming and paint/lacquer
application. Number of layers, side treatment, setup and rates are decisions
still to agree. Technological drying/curing is separate from active paid labor.

Coating products/consumables feed Materials; active hours feed Labor; resulting
own production hours feed the existing Overhead allocator. Reuse existing
calculation and purchase integration, with no new recognition for saved parts.
Front material changes preserve current Sheet Processing and Block Assembly
as agreed in9.47. They update only the affected new coating dependencies.
Any later proposal to alter machining/edging hours needs its own explicit scope.

## Assembly and preparation boundaries

Block Assembly retains its saved role counts, norms and source/block ownership.
Additional Assembly can use profile/LED/wire lengths, counts of connections and
components, and glass/mirror bonding work from the source. Rates require agreement.
A purchased preassembled service and own assembly cannot both charge the same work.
Common and standalone parts without block_id retain object-level work ownership;
they are not omitted merely because the packing or assembly unit is a Block.

Trial fit of several blocks, alignment checks, necessary separation for dispatch
and packing belong to the final stage. Existing hinge/drawer adjustments are
already in Block Assembly and must not be charged again as final checking.
Electrical installation work and final whole-item function checks also need a
clear single owner in the operation list.

Packing sizes S/M/L/XL are proposed as a simple norm table. Classify the actual
transport unit, normally a block, using agreed geometric boundaries, then apply
agreed minutes per unit. Loose panels, long profiles, fragile glass and assemblies
dismantled after trial fit need explicit units instead of pretending every parcel
is a complete carcass. Dimensions, size boundaries, minutes, handling/fragility
adjustments and what packing materials the existing Packaging allowance covers
must be agreed before rates are activated. Packing labor and packing consumables
remain separate cost inputs.

## Saved data and verification

Preserve run/estimate/input/source-audit/overlay identities and the existing
Material Plan and Parts. Existing manual hours for sheet-processing and assembly
must retain their meanings when the UI is reorganized. Before new Assembly
children are priced, explicitly define whether an old manual Assembly override
applies to its old Block Assembly scope; do not silently let it mask new work.
Each new operation should retain its part/block/transport-unit source, quantity
basis, norm and performer. Reuse the current Labor pipeline and shared aggregate.

Physical part quantities, production batch, purchase packs and commercial copies
remain separate. Commercial copies do not divide the configured item's Self Cost.
No extra payroll load, duplicated stock/service cost or second VAT.

Coverage check: every part requiring work must have an operation, an included
supplier service, or a justified no-additional-work disposition. This is an
internal calculation/test requirement. It does not authorize new user-facing
warnings, badges or notices prohibited by the accepted interface contract.

Retain the613-check/nine-suite baseline and add focused tests for active Machinery
routes, the four-stage aggregate, preserved manual overrides, coating-only
invalidation, source ownership, supplier inclusion, packing boundaries and no
repeated charging. Update only the owner-approved UI expectations for the new
structure. Exact-SHA GitHub gate, protected publisher and actual Core/wrapper
identity checks remain required for every runtime publication.

## Prices: verified current behavior and proposed change

[verified] screens/company_profile.py starts four asynchronous projections:
sources, catalog, review and material_jobs. _render_price_lists_projections waits
for all four before showing the catalog. _render_price_catalog iterates every
row and creates department expanders with expanded=True. Source-library rows
and other projections also have their own dependencies. Existing bounded Price
Lists/Profile executors and identity/generation-aware refresh state already exist.

[hypothesis] Both the all-projection barrier and full row construction contribute
to the reported delay. Measure click, callback/rerun, read, render and visible
completion separately to identify the dominant cost. No production timing has
been measured by this planning iteration.

Requested before/after: currently the first catalog display waits for all
projections and builds all open groups; proposed display shows closed group
headers promptly, then prepares/shows contents progressively. A collapsed visual
expander alone does not skip the unconditional Python row construction.

Proposed behavior:
- Show the existing page shell and closed group headers without waiting for all
  unrelated data. Counts remain truthful, not invented before their reads finish.
- Opening a group gives its required read/preparation priority over queued warmup.
  If ready, show it immediately; otherwise use the existing scoped loading style.
- Warm remaining groups through the existing bounded infrastructure, once per
  valid data revision. Do not create an additional global polling/background system.
- Avoid duplicate jobs for repeated clicks and reserve responsiveness for actual
  interaction. Already-running work need not be forcibly interrupted to reorder
  queued work. Reuse completed data when still valid.
- Scope data and caches by company, access identity and revision. Drop stale
  completions after sign-out/company/role change; cancel unnecessary queued jobs.
  Background work and its completion must not cover or block another Profile tab.
- Add/remove/edit/import prices invalidates only affected projections/groups,
  preserving unsaved edits, ongoing uploads, current permissions and acknowledged
  save receipts. Keep Source library, review and Supplier Operations functional.

Choose the narrowest implementation after timing: avoid building closed contents
first; split coarse catalog reads into group-level demand only where necessary
to meet selected-group priority. Existing preloading is extended, not duplicated.

Acceptance: delayed unopened groups do not block initial headers or the selected
group; repeat opens reuse valid data; failed reads remain retryable in the same
scope; stale completions cannot overwrite current edits; background updates leave
focus/scroll and other Profile actions usable. Browser scenarios must cover a
large synthetic catalog, delayed selected/unselected groups, rapid open/close,
row-save failure/retry, upload/delete invalidation, tenant/role change and keyboard.
Actual production timings remain a separate acceptance observation.

## Accepted implementation checkpoint, 23 November 2026

The owner accepted steps 1 and 2, Prices responsiveness and the four-stage Labor
structure, after production use. The full checkpoint pins runtime 862e28f0, build
9.48, exact 829-file source, 964-check/ten-suite evidence and restored-source
material controls. Earlier pending implementation/acceptance descriptions in this
plan are historical. Numeric coating/additional assembly/preparation/packing work
remains deferred until boundaries and rates are agreed. Future Labor 2.x naming
will be reconciled before the next release, without reusing historical tags.
[Accepted checkpoint](ESTIMATION_V9_48_PRODUCTION_CHECKPOINT_2026_11_23.md).

## Current focus: Preparation and Packing, owner request 23 November 2026

The owner now selects this stage before Coating. The earlier recommended order
is historical. The authoritative task state remains in notes/TODO.md. Preserve
the accepted 9.48 runtime/checkpoint and all existing hours, saved overrides,
commercial quantity rules, Parts/Material Plan and protected UI behavior.
The owner wants dimensional S/M/L/XL categories first, followed by agreed time
norms and automatic application to the already calculated blocks.

### Checking and separation

One work unit is one actual checkable mating interface between physical blocks
within the priced item. Trial mating, alignment/fit checking and separation for
dispatch belong to that unit. A reverse reference B-A repeats the same A-B
interface; multiple drawings/evidence refs are retained without charging again.
If one pair has distinct physical interfaces, retain their identities rather
than merging by pair alone. Fastener count is not the checking-unit quantity.
Count actual interfaces; a three-block chain A-B-C has two, and a verified extra
A-C interface would add a third. Block count minus one is not a general rule.

Proposed calculation:
T_check = sum(interface_quantity * (t_mate + t_check + t_separate)).
Time norms will be in man-minutes, so ten elapsed minutes with two workers is
twenty man-minutes. Retain the established wage/payroll aggregation; explicitly
define whether future norms are active or planned time before applying any pace
or working-share factor. Do not duplicate carcass assembly or existing drawer/
hinge adjustments. The proposed audit identifies object, interface, both block
instances, quantity, source evidence and applied norm. Schema changes await scope
confirmation and must reuse the existing persisted source contracts.

[verified] Current calculate_block_assembly() has block-owned Parts operations,
not this interface list. The four frozen Parts reports contain no explicit
physical interface field. Inventory/Analyze preserve some shared-component
attached_block_ids upstream. These can provide attachment evidence, but are not
automatically direct pairwise block mating interfaces. Locate and reuse the
existing source evidence before introducing a new recognition call or assumption.
An unavailable interface list must not be treated as proven zero connections.

### Packing classes

Start from the dimensions of the actual unit being packed, normally the saved
block in its dispatch configuration. A loose shared top/panel or dismantled
subassembly requires its own identified packing unit when applicable. Retain
object/block/part provenance so these elements are not omitted or counted twice.
Commercial selling copies remain distinct from the physical contents of the
configured item. Confirm transport-unit rules before mapping complex logical
Blocks directly to parcel counts.

Owner-approved boundaries, confirmed 23 November 2026. These define our estimation
policy and are not claimed to be industry norms:

| Class | Three sorted side limits, largest to smallest, mm |
| --- | --- |
| S | 600 x 600 x 400 |
| M | 1200 x 800 x 600 |
| L | 2000 x 1200 x 800 |
| XL | Beyond L |

For three known positive dimensions, sort descending and choose the smallest
class whose three limits all contain the unit. Boundary equality belongs to the
smaller class. Rotation does not change the class. Proposed packing time:
T_pack = N_S*t_S + N_M*t_M + N_L*t_L + N_XL*t_XL.
The owner approved the classes and then approved10/15/20/25 planned man-minutes
for S/M/L/XL and30 for one complete mating/checking/separation cycle. Implementation
is active as Labor2.10; earlier pending-rate statements are historical.
Existing Materials' Packaging formula remains a
separate material allowance and is not replaced or charged again as labor.

The saved controls provide 30 block records: 19 complete three-axis envelopes and
11 with missing axes. Some contain an explicitly named depth_proxy. Resolve
missing packing geometry from existing block/part evidence or a separately
audited, approved budget assumption before treating a category as known. An
unresolved case is not silently S, zero work or omitted from the calculation.
Full source audit and draft classifications are private diagnostic artifacts in
outputs/labor-preparation-packing-20261123/source-audit.json. This audit uses only
saved inputs and makes no paid call or production write.

### Verification before activation

Verify unique interfaces and repeated evidence, physical multiplicity, common
parts, separated packing units, all class boundaries/rotations, missing/invalid
dimensions, man-minute conversion, unchanged existing overrides and commercial
quantity invariance. Verify single inclusion of the new stage in Labor, payroll,
Overhead and Self Cost. Preserve all accepted UI checks and add only the agreed
stage behavior to the exact-SHA release gate. No new UI warnings or controls are
authorized by this planning note. No new runtime version is assigned here.

## Published Labor 2.10 implementation

Labor 2.10 published 23 November 2026, work 3.17.4.6, runtime 20e34aa1.
Preparation and Packing now includes trial mating/checking/separation at30 planned
man-minutes per sourced interface and S/M/L/XL packing at10/15/20/25. Owner approved
both sizes and rates and explicitly confirmed the Labor2.10 release name.
Known work enters Labor/payroll/Overhead/Self Cost once; old manual keys, material
replacement preservation and commercial-copy rules stay. New Parts runs retain
native/structural interface evidence without extra model requests. Legacy reports
without a graph keep checking unknown; unresolved packing units remain listed.
Offline Ada replays leave Parts and full Material Plan identical, with no network
or paid call. Full local991/ten436.242s followed by994 full-unit checks; exact-SHA
GitHub994/ten362.833s passed. Protected main rule27499066 active/no bypass.
Core/wrapper/meta/version.json all match Labor2.10 at2026-11-23T19:08:50.531617+00:00.
Owner production acceptance pending. Accepted9.48 full checkpoint is preserved;
this publication is not a new accepted checkpoint. [Release and evidence](LABOR_V2_10_PREPARATION_PACKING_2026_11_23.md).

## Labor2.11 disclosure and hours

[verified] Labor2.11 published23November2026, existing work3.17.4.6,
runtime63db313d. Expanded Part Production, Assembly and Preparation and Packing
hide own hours/pay/taxes/total and restore them on native collapse. Root Labor
shows shared total hours, including collapsed. Nested numeric axes and text
centers are aligned without shrinking their grids. Exact source hours stay equal
to Overhead during edits and after Save/reopen. The screenshot28.3h is correct;
shared half-up display rounding, no allocation/payroll change, paid call or Detection/Parts/Materials algorithm change.
Full local999/ten473.687s and exact-SHA GitHub999/ten
346.847s passed. Protected main rule27499066 active/no bypass. Actual Core,
wrapper executable/meta and version.json match; receipt recorded at2026-11-23T21:50:55.013839+00:00.
Owner production acceptance pending; accepted9.48 checkpoint stays immutable.
[Release and evidence](LABOR_V2_11_DISCLOSURE_HOURS_2026_11_23.md).

## Labor 2.12 terminal work and CNC

[verified] Labor 2.12 published 24 November 2026, work 3.17.4.6,
runtime `46e01b5d`. Only terminal paid work is editable, including explicit
unknown-hour overrides; departments and root totals remain computed. CNC now
shows Elements and Operator/File Preparation/Edge Banding in its time breakdown,
without duplicate material/in-house/subcontractor/rate panels. Taxes & Social
states +25%. All 12 work summaries are 42px at desktop/mobile; nested boundaries
have no extra padding gaps. Overhead has one shared header and aligned Cost axis.
Same-source hours feed Labor/Overhead/Self Cost/Objects once; all new edits survive
Save/retry/reopen. Real partial receipts retain section columns. Unknown fields
never become zero unless explicitly entered; first Save can complete Overhead
without replacing healthy groups or any hour input. Full local 1015/ten in
405.642s and exact-SHA GitHub 1015/ten in 375.79s passed.
Main rule27499066 active/no bypass; actual Core/wrapper/meta/version match.
Owner production acceptance pending. Full2.11 checkpoint63db313d/records099f9180
remains immutable. [Release and evidence](LABOR_V2_12_WORK_EDITING_CNC_2026_11_24.md).

## Labor2.13 shared presentation and Project

[verified] Labor2.13 published24November2026, existing work3.17.4.6,
runtime `c5364813`. CNC, Elements and block disclosures share compact42px
rows, fonts, chevrons and expanded backgrounds. Keep Operator/File Preparation/
Edge Banding separate and terminal work editable. Project replaces Objects
Estimation in the summary and Continue/Back copy; internal route identities and
separate Projects navigation remain. Project logo artwork aligns with body.
The owner-approved offline artwork shows the purple mark before Something went
wrong., with Are you connected to the internet? below, without a wordmark.
Existing wrapper cover/offline/online events provide it, with no polling,
auth mutation, iframe unload on loss or separate reconnect path. Processing
survives offline/online without reload; idle reconnect retains existing behavior.
Server-only disconnect while browser stays online retains native Streamlit UI.
Full local 1015/ten in 431.247s and exact-SHA GitHub 1015/ten
in 417.065s passed. Main rule27499066 active/no bypass, actual served
Core/executable wrapper/meta/version agree. Owner accepted sketch; production
acceptance pending. Full2.11 checkpoint remains immutable;2.12 runtime46e01b5d
is the rollback baseline. [Release/evidence](LABOR_V2_13_PROJECT_CNC_OFFLINE_2026_11_24.md).

## Labor2.14 nested rollups and shared hierarchy

[verified] Labor2.14 published24November2026, existing work3.17.4.6,
runtime `fc3e5827`. CNC precedes reference Elements and has its own read-only
closed rollup of Operator/File Preparation/Edge Banding. All nested work sums
are shown closed and hidden when expanded; terminal editors remain. No new
charge/key/source norm. Shared Overhead triangle/mono style and explicit nested
indentation measure13 work rows at42px on1280/390. Elements remains last on all
Sheet Processing routes. Closed Overhead groups show Monthly Cost sum/current
Allocation/Cost; expanded ones hide all summary metrics. Reserves show — and
Formula, not percentages as monthly money. Live edits/save/reopen keep group
allocations and costs current, preserving original amounts and once-only hours.
Owner-confirmed Trial Installation and All Projects change labels only. Current
summary remains Project; stored trial-fit/projects identities stay. Previous
2.13 offline/auth/recovery and all persistence behavior remain protected.
Full local 1018/ten in409.363s and exact-SHA GitHub 1018/ten
in385.316s passed. Main rule27499066 active/no bypass; actual served
Core/executable wrapper/meta/version agree. Owner production acceptance pending.
Full2.11 checkpoint unchanged; rollback baseline2.13c5364813. No paid calls.
[Release/evidence](LABOR_V2_14_NESTED_ROLLUPS_2026_11_24.md).
