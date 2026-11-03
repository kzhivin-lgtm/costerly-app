# Estimation V4 full-chat handoff

Date: 2026-11-03  
Purpose: seamless continuation in a new chat  
Authoritative task: `3.17.4.3`, Object-to-Estimate and approximate BOM foundation  
Current release: V4.29 published implementation. Next Estimation runtime number: V4.30

## Current position

The project has a substantially improved immutable evidence package and several
published Estimation V4 repairs. It does **not** yet have an owner-accepted,
universal material estimator.

[verified] V4.29 runtime code is published on `origin/main` and public wrapper
code contains its recovery markers.  
[unknown] No authenticated post-V4.29 production interaction witness exists.  
[verified] Trace `f232f994-ca20-4283-87f0-8c5aac30b892` proves the latest New
Estimate failure was browser-to-Streamlit callback loss, not ordinary model or
database latency. It emitted a New Estimate click and a timeout with
`python_runs=0`.

First obtain the live V4.27-V4.29 acceptance witness. Do not begin another BOM
patch before that. The exact protocol is in
`notes/ESTIMATION_V4_29_NAVIGATION_AND_OBJECT_DETAIL_IMPLEMENTATION_CHECKPOINT_2026_11_03.md`.

## Product scope

Costerly accepts unstructured sketches, architectural drawings, client layouts
and production PDFs for a fast approximate top-level estimate. It is not Cabinet
Vision, Autodesk or a CNC/cabinet CAD package, which require structured input.

This Estimation V4 block must:

* use Detection-locked object/evidence;
* infer major assemblies, then conventional structural elements;
* calculate approximate material demand and purchasable quantity;
* preserve separately shown legs, slides, handles and hinges;
* price every material demand;
* expose sourcing uncertainty via C/I/A, never a blocked result.

Labor, manufacturing routing, overhead, markup and selling price are separate
deterministic future layers. Do not put them under materials. The result is an
approximation, not a precision cut-list: normal thickness and construction
assumptions are allowed, invented tiny gaps are not.

## Detection boundary and evidence

Detection owns document identity, object identity, object quantity, source pages,
regions and immutable `estimation_input_v4`. The input includes locked object
ID/quantity, physical pages/regions, OCR blocks, private full-page artifacts,
original-file reference and OCR-event identity.

Estimation consumes this package. It must not rename the object, change
Detection boundaries or mutate evidence. A BOM/material issue does not justify a
Detection change without read-only proof of a handoff defect.

The 39-page kitchen proved bounded evidence assembly, not correct complex-kitchen
estimating. Large documents need bounded visual batches and cited reconciliation,
not one unlimited expensive Cloud request.

## Material contract

| Term | Meaning |
| --- | --- |
| Company Catalog, `C` | Normalized company catalog product |
| Israel Reference, `I` | Normalized Israel reference product |
| Assumption Fallback, `A` | Immediate estimate-local priced fallback |
| Material Demand | Physical requirement before resolver selection |

Resolver order is Company Catalog → Israel Reference → Assumption Fallback.
The model may identify material role/family from evidence and appearance.
Resolver/Material Engine alone selects a catalog product and price.

Every demand receives a price. A is a priced uncertainty with reasoning and
confidence, not an error, approval gate or review-required result. It can rely
on an Israeli source, a global projection or a weak explicit allowance. It
should silently create/update a deduplicated Catalog Gap Job. C/I names must be
strict normalized DB names after marker plus space.

Required demand may be area, length or pieces. Purchase quantity is whole
purchase units. Compatible demand is aggregated estimate-wide before rounding.
One long finished panel cannot disqualify a C/I material: it can be joined and a
drawing span may be composed. Compatibility is family/spec, not one finished
panel fitting one sheet. V4.25 uses aggregate area plus 10% offcut, rounded to
units. It is a practical approximation, not CNC nesting.

## Object Detail UI contract

One Materials table only:

| Column | Required behavior |
| --- | --- |
| Material | C/I/A marker, a space, then exact sourced name |
| Required Material | Editable input with unit inside |
| Purchase Unit | Type/format, can occupy two lines |
| Purchase Quantity | Editable input, no duplicate unit |
| Total | Derived, read-only quantity × price |

`Elements` is a collapsed structural list, never a second cost/allocation
table. User-facing material UI must not expose `Project Material Plan`,
`Project Allocation`, `Cabinet Carcass`, or `Cabinet Facade`.

Shown legs/discrete hardware are purchased as pieces, not implicit sets.
Generic connectors, mounts, hangers and fasteners are out of current scope
unless explicitly shown and a later scope decision changes that.

Profile Pricing Cost creates three locked formula rows after physical materials:

* Consumables, percentage of primary physical material cost;
* Packaging, percentage of primary physical material cost;
* Paint consumables, percentage of coating material cost only.

They are not catalog materials, C/I/A, purchase units or editable demands.
V4.27 restored these rows.

## Intended universal pipeline

1. Object-to-Estimate receives locked object, quantity and immutable evidence.
2. Unit/dimension context reads the whole drawing. Explicit source unit wins.
   Unitless convention is auditable and cannot come from a watermark.
3. Assembly decomposition finds major physical multi-part blocks first.
4. Deterministic structural composer expands supported assemblies into sides,
   tops/bottoms, backs, dividers, drawers, shelves, layers and shown fittings.
5. Secondary shown details are retained. Unsupported details become bounded
   omissions rather than silent loss of all valid demand.
6. Material demand proposes family/role from source context and visual
   appearance. Formica is currently ordinary LDSP. Paint is finish, not board.
7. Material Engine resolves C → I → A, aggregates project demand, applies
   offcut/purchase rounding and produces material cost.
8. Formula allowances calculate from Profile settings.
9. Result presents the single material table and collapsed Elements.
10. Manual edits invalidate dependent BOM/purchase/QA state, never Detection.

TU Wien/2VN research is decomposition inspiration, not a turnkey generic
algorithm or cabinet-CAD replacement. The product requires controlled visual
interpretation plus deterministic composition and resolver rules.

## Benchmark inputs and learned failures

### Lev_1, Adda, LF1 / Cabinet

User file: `/Users/qb/Desktop/SAMPLES/Adda/Lev_1.pdf`. It is text-sparse but
dimension-rich and includes a SolidWorks educational watermark. The watermark is
not evidence of unit, material, identity or construction.

The user's human decomposition was illustrative: split into lower/drawer,
vertical, table/top and upper blocks, then compose conventional structural
pieces only where context supports them. Retain shown legs/hardware. Do not
invent decorative strips or generic fixings.

Earlier results used values such as `266` and `720` as unrelated panels, lost
legs and misassigned materials/dimensions. The failure is assembly-first semantic
interpretation, not just insufficient OCR extraction.

Historic scale failure treated `160`, `72`, `265` as building-scale mm
values. V4.11 added a bounded centimetre guard. V4.15/V4.17 advanced
whole-drawing unit interpretation and Dimension Scale Gate. Explicit unit wins.

### 39-page kitchen

The kitchen package is useful for evidence stress testing, but expensive and not
an ordinary one-call test. Any replay must have a bounded hypothesis and current
user authorization. Its availability does not prove BOM/purchase correctness.

## Release lineage

Numbering authority: `notes/ESTIMATION_V4_RELEASE_SEQUENCE_2026_11_02.md`.

| Release | Commit | Core change |
| --- | --- | --- |
| V4.1 | `347f61b` through `773937c` | Bounded immutable evidence batches |
| V4.2 | `497bcbc` | Persisted material facts |
| V4.3 | `4246eb2` | Object-to-Estimate/BOM base |
| V4.4-V4.6 | `16c0f1e`, `0c70004`, `9d5266d` | Priced, non-blocking A |
| V4.7-V4.10 | `c7482f8` through `d0f1ac2` | Geometry/material engine/progress foundation |
| V4.11 | `5874031` | Unitless cm safety and bounded splitting |
| V4.12 | `3e7c04c` | Assembly-first graph, no object-kind recipe |
| V4.13 | `76d51fb` | Unit/basis/thickness normalization |
| V4.14 | `b5bdf53` | Structural composer and compact C/I/A |
| V4.15 | `3e5eb94` | Whole-drawing unit convention |
| V4.16 | `1cee460` | Objects terminal navigation repair |
| V4.17 | `72c946f` | Scale Gate, coverage ledger, project units |
| V4.18 | `eba4fae` | Optional coverage and bounded stage traces |
| V4.19 | `7bfe531` | Safe invalid-assumption-ref normalization |
| V4.20 | `156f9a1` | One material table and Elements |
| V4.21-V4.23 | `0b030ea`, `88cacbe`, `a7d3a2b` | Omission/count/evidence resilience |
| V4.24 | `797dc33` | Purchase-format serialization repair |
| V4.25 | `484c531` | C → I → A resolver and editable demand |
| V4.26 | `cbac71f` | Input/table layout contract |
| V4.27 | `80e71f0` | Formula allowance restoration |
| V4.28 | `4e87892` | File Review ordering and detail warm reads |
| V4.29 | `f891e56` | Dead-callback New Estimate recovery |

## Important rejected technical witness

`run_d82f58af38f84a4eb6fc3a2dbb8faeab` reached
completed/materials_costed/100% and persisted BOM, plan, publisher and
allocation for Cabinet, ILS 800 ex VAT, ILS 944 incl VAT. This proves terminal
cycle mechanics only, never output quality.

It emitted A for Veneered MDF, LDSP and Hardboard. Reasons included
`material_pricing_key_incomplete` and
`no_physically_compatible_company_or_israel_candidate`. The user correctly
rejected sheet length as a material compatibility condition. V4.25 corrected
that resolver contract. Do not cite this run as material/source acceptance.

## V4.27-V4.29 implementation facts

### V4.27

Restored Profile formula allowances. Focused tests passed. Production witness
still required.

### V4.28

File Review action controls render before deferred poll can rerun. Object Detail
authorizes first, parallelizes independent object/lines/plan reads, and
parallelizes facts/settings. Objects schedules bounded read-only prefetch only
after it is visible. Detail consumes matching cache or normal authorized
fallback. Cache invalidates after edit, approval, recalculation, completion and
New Estimate.

Verification: 20 focused tests passed, 71 wider route/detail tests passed. Two
unrelated stale static expectations failed: obsolete `profile_tab` route text
and obsolete `RFQ_UPLOAD_CYCLE_ID_KEY` text. Python compile and diff checks
passed. Node was unavailable for JS parser validation.

### V4.29

Trace `f232f994-ca20-4283-87f0-8c5aac30b892` showed New Estimate click and
timeout without Python. V4.29 wrapper:

* clears outer URL with `history.replaceState` at click time;
* emits `browser.new_estimate_route_cleared`;
* leaves native callback as preferred reset path;
* keeps transition pending until real matching Upload app-ready;
* after 900 ms without server-ready, replaces only iframe on clean
  `screen=upload` route;
* uses `frame.src` to preserve `obs_trace`, correlating recovered app-ready;
* clears recovery timer after matching server ready.

Focused V4.29 suite: 3 passed. Public wrapper served its markers after deploy.
Authenticated interaction acceptance remains pending.

## Current sources and records

Implementation checkout: `/private/tmp/costerly-estimation-v425`  
Branch: `codex/estimation-v425`

Relevant source: `cloudflare/index.html`, `screens/file_review.py`,
`screens/objects.py`, `screens/object_detail.py`,
`use_cases/estimation.py`, `use_cases/object_detail_runtime.py`,
`state/session.py`, `tests/test_runtime_observability.py`, and
`tests/test_object_detail_cache.py`.

Authoritative records: `notes/TODO.md`, `notes/DONE_LOG.md`,
`notes/ESTIMATION_V4_RELEASE_SEQUENCE_2026_11_02.md`,
`notes/ESTIMATION_3_17_4_3_OBJECT_TO_ESTIMATE_BOM_PLAN_2026_11_02.md`,
`notes/ESTIMATION_V4_24_TERMINAL_CYCLE_CHECKPOINT_2026_11_02.md`, and
`notes/ESTIMATION_V4_29_NAVIGATION_AND_OBJECT_DETAIL_IMPLEMENTATION_CHECKPOINT_2026_11_03.md`.

Do not assume `/Users/qb/Documents/ChatGPT/Costerly` is the implementation
checkout. It is usually a handoff/document workspace. Confirm authority before
editing.

## First action in the next chat

After one ordinary browser refresh, run one authenticated production scenario:

1. Start from completed object/estimate route, click New Estimate once.
2. Confirm outer URL immediately becomes `/` and Upload is actionable.
3. Upload a small file, confirm File Review shows Back to Upload and Continue
   to Objects Estimation.
4. Press Last Estimate, verify it returns latest completed File Review.
5. Continue to Objects, open Review twice, compare visible load time.
6. Edit permitted material input, save/recalculate, reopen and confirm no stale
   detail snapshot.
7. Read runtime events. Require click, route-cleared `/`, real app-ready plus
   Python run or named recovery then app-ready, and no transition timeout.

On failure preserve trace ID, timestamps, route and screenshot. Inspect trace
before a new patch. Do not call it cache without evidence.

## Backlog after the witness

1. **P0**: accept or reject V4.27-V4.29 in actual production flow.
2. **P0**: audit assembly loss on Lev_1/equivalent through immutable evidence →
   dimension graph → assembly output → structural composition → Elements →
   material demand. Repair earliest stage losing a leg, drawer or layer.
3. **P0**: audit hardboard/solid-timber family choice independently from lost
   element diagnosis.
4. **P1**: make A-created Catalog Gap jobs operationally visible.
5. **P1**: validate project-wide aggregation with two objects sharing material.
6. **Future approved block**: labor/manufacturing/overhead/pricing.

## Do not do

* Do not accept terminal cost as correct BOM.
* Do not change Detection without handoff evidence.
* Do not treat SolidWorks watermark as estimation evidence.
* Do not let an invalid model evidence reference fail customer BOM.
* Do not reject C/I because finished part exceeds one sheet.
* Do not omit price. A is mandatory fallback.
* Do not show Project Allocation/Plan or duplicate cost UI.
* Do not add generic hardware/labor to materials.
* Do not use any Detection release number for Estimation. Next runtime number is
  V4.30.
* Do not rewrite origin/main merely to rename neutral V4.28 code commit.
* Do not replay 39-page kitchen without bounded question and authorization.

## Suggested opening prompt

“Continue from the published Estimation V4.29 implementation checkpoint and
full handoff dated 2026-11-03. First obtain and audit one live authenticated
V4.29 New Estimate → Upload → File Review → Objects → Review witness. Do not
start a BOM/material repair until callback recovery and File Review actions are
verified in production. Use recorded trace markers and acceptance protocol.”
