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
