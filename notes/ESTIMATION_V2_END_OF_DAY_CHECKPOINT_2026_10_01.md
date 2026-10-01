# Estimation v2 end-of-day checkpoint, 2026-10-01

Task: 3.15.8 Estimation v2 replacement

Status: verified production proof for one complete Object Detail calculation.
This is a checkpoint, not completion of the full Estimation v2 pipeline.

## Resume instruction

Continue task 3.15.8 from this file. Start by replacing every legacy Labor and
Machinery read in the Estimation pricing path with the current Company Profile
tables. Then automate the already proven one-object path from persisted Object
Facts through material resolution, Labor, Overhead and Object Detail
publication.

Do not restart Estimation v2 from the legacy Estimation Agent.

## Verified outcome at end of day

One real production object is available as a complete, editable Object Detail:

- run: `run_845a3781ee66482cb253a7d87b0d2f8c`;
- estimate:
  `run_845a3781ee66482cb253a7d87b0d2f8c_estimate_20260930215045`;
- company: `610`, Company #1;
- object: `object-001`, Shelving unit;
- status: `completed`;
- material rows: 5;
- labor rows: 12;
- overhead rows: 13;
- total persisted lines: 30;
- source preview: private signed preview derived from the uploaded source page;
- all displayed quantities, material unit prices, labor hours and labor rates
  remain editable through the existing Object Detail UI.

Production route:

`https://app.costerly.ai/?screen=object_detail&run_id=run_845a3781ee66482cb253a7d87b0d2f8c&estimate_id=run_845a3781ee66482cb253a7d87b0d2f8c_estimate_20260930215045&object_id=object-001`

The server-side Object Detail loader was verified against production. It
returned all three populated sections, the private preview URL and the final
self-cost values. Authenticated visual acceptance remains a user-side check
because local browser control failed with the existing macOS `TIOCSTI` sandbox
error.

## Current accepted cost result

The current result uses the correct Company Profile Labor source and the
existing Overhead configuration:

- material cost excluding VAT: ILS 679.00;
- direct labor base cost: ILS 229.36;
- employer load at 25 percent: ILS 57.34;
- labor total including employer load: ILS 286.70;
- allocated overhead: ILS 38.32;
- self cost excluding VAT: ILS 1,004.02;
- VAT at 18 percent: ILS 180.72;
- self cost including VAT: ILS 1,184.74.

The UI may round individual displayed monetary cells to whole shekels. The
persisted totals retain two decimal places.

Delivery and installation are not included in object self cost. The temporary
selling-price suggestion remains self cost plus 30 percent. Delivery at 3
percent and installation at 10 percent apply only to the project objects'
selling-price subtotal after all project objects are complete.

## Material calculation now persisted

1. Carbon steel square tube 20x20x1.5 mm, provisional wall thickness:
   - quantity: 13.89 kg;
   - price: ILS 11.21/kg;
   - cost: ILS 155.71;
   - price basis: active Israel catalog square-tube price;
   - quantity basis: 15.94 m derived length and 0.871 kg/m;
   - review remains required because the drawing does not state wall thickness.
2. MDF 20 mm, using the 19 mm market class as an explicit proxy:
   - quantity: 1.211 m2;
   - price: ILS 209.39/m2;
   - cost: ILS 253.57;
   - quantity basis: five shelves, 1.053 m2 net plus 15 percent;
   - review remains required because the Israel pricing catalog has no 20 mm
     MDF pricing identity.
3. Perforated carbon steel sheet:
   - quantity: 1.334 m2;
   - price: ILS 102.00/m2;
   - cost: ILS 136.07;
   - quantity basis: 450 x 2695 mm net plus 10 percent.
4. Epoxy metal primer:
   - quantity: 0.6 L;
   - price: ILS 74.25/L;
   - cost: ILS 44.55.
5. Polyurethane metal topcoat:
   - quantity: 0.6 L;
   - price: ILS 148.50/L;
   - cost: ILS 89.10.

The persisted material total is ILS 679.00. The Object Detail material total including VAT is
approximately ILS 801.22, which explains the user's observed approximately
ILS 800 material figure.

## Labor calculation now persisted

The previous temporary flat rate of ILS 75/hour was invalidated and removed.
It came from an incorrect diagnostic read of obsolete tables. Current rates
come from `company_employees` gross pay and receive the employer factor once in
the self-cost total.

Persisted operations:

1. Cut square tube profiles, 0.613 h at ILS 50/h.
2. Fixture and frame assembly, 0.300 h at ILS 50/h.
3. MIG/MAG welding, 1.043 h at ILS 50/h.
4. Grind and dress welds, 0.643 h at ILS 50/h.
5. Handle five MDF panels, 0.117 h at ILS 50/h.
6. Cut MDF shelf panels, 0.183 h at ILS 40/h.
7. Edge band shelf panels, 0.217 h at ILS 40/h.
8. Prepare metal surfaces, 0.364 h at ILS 60/h.
9. Apply metal coating, 0.331 h at ILS 60/h.
10. Install perforated back panel, 0.383 h at ILS 50/h.
11. Quality inspection, 0.117 h at ILS 71.4286/h.
12. Protective packaging, 0.167 h at ILS 50/h.

Total estimated labor time is 4.478 hours.

Direct mappings from Labor Engine roles to Company Profile positions are used
where available. The following provisional mappings remain `needs_review`:

- `metal_machine_operator` to `welder`;
- `grinder_polisher` to `welder`;
- `general_worker` to `carpenter`;
- `production_manager` to `general_manager`;
- `packer` to `carpenter`.

The user considers the result plausible enough to continue but specifically
questioned whether one hour of welding is realistic. Labor baseline validation
therefore remains required. The current result is a useful draft, not an
accepted manufacturing standard.

## Correct Company Profile data sources

The current Company Profile does not use legacy `labor` or
`company_machines` tables.

Correct tables:

- Labor Cost: `company_employees`;
- Machinery: `company_machinery`.

Company `610` has 9 active employees:

- owner/director, monthly gross ILS 15,000;
- general manager, monthly gross ILS 12,000;
- office administrator, monthly gross ILS 10,000;
- two carpenters, each ILS 50 gross/hour;
- welder, ILS 50 gross/hour;
- CNC operator, ILS 40 gross/hour;
- painter/finisher, ILS 60 gross/hour;
- installer, ILS 50 gross/hour.

The profile stores an employment factor of 1.25 and already shows total labor
costs. Estimation labor lines currently persist gross rates, then the existing
self-cost calculation adds the company employer-load setting once. Do not use
`total_hourly_cost` and then add 25 percent again.

Company `610` has 16 active Machinery records:

- metal profile saw, in house;
- metal rolling machine, in house;
- metal press brake, in house;
- wet spray booth, in house;
- powder booth, in house;
- sandblast booth, not in house;
- wood CNC router, in house, ILS 100/hour internal cost;
- wood panel saw, in house;
- galvanizing, not in house;
- metal profile bender, in house;
- wood veneer press, in house;
- solid wood preparation, in house;
- wood edge bander, in house;
- sheet metal laser, not in house;
- metal punch press, not in house;
- wide belt sander, in house.

The existing `build_company_production_context()` already reads
`company_machinery`. The legacy `fetch_company_data()` and pricing path still
read `labor` and `company_machines`; this is a verified defect and the first
implementation task for the next work session.

## Overhead calculation

The company monthly overhead total is ILS 17,250. Capacity is calculated from:

- 12 production workers;
- 21 workdays per month;
- 8 hours per day;
- monthly capacity: 2,016 labor hours.

The object receives 4.478 / 2,016 of each monthly overhead category. The 13
persisted overhead lines total ILS 38.32. The allocation is deterministic and
was correctly displayed in Object Detail. No delivery or installation amount
enters these lines.

## Evidence and Detection correction

The uploaded source is `page-23.pdf`, a one-page Russian furniture drawing.
The original remains in the private Supabase originals bucket. Estimation uses
the stored OCR result and source-derived preview. OCR was not rerun.

Detection incorrectly assigned width 4130 mm to the Shelving unit. That
dimension belongs to the neighboring sliding rail. Visual inspection of the
private source preview established the shelving width as 450 mm and the height
as 2695 mm. Shelf depths shown on the drawing include 350, 460 and 510 mm.

The persisted Object Facts result remains `review_required` because several
material quantities and identities were not explicit. It must not be silently
promoted to `ready`. The deterministic draft calculation makes every
assumption editable and retains `needs_review` on provisional rows.

## Object Facts agent measurement

Accepted extractor result:

- input ID: `c7058cd4-a806-448f-9bcc-9d8ebb2970f5`;
- fact result ID: `0cb6a13a-c201-43fc-a2b2-b5d776a345c6`;
- extractor: `estimation_object_facts_agent_v2`;
- model: `claude-haiku-4-5-20251001`;
- model duration: 18.253 seconds;
- input tokens: 2,735;
- output tokens: 2,109;
- source document attached: false;
- OCR rerun: false.

At the official Haiku 4.5 standard price of USD 1 per million input tokens and
USD 5 per million output tokens, the accepted call cost USD 0.01328. At the
Bank of Israel representative rate of 3.063 ILS/USD on 2026-09-30, this was
approximately ILS 0.041, about four agorot.

One discarded v1 attempt used 3,120 input and 1,463 output tokens and cost
approximately USD 0.010435. Total Object Facts model spend for both attempts
was USD 0.023715, approximately ILS 0.073. No extra OCR cost was incurred.

The complete automatic File Review to completed self-cost latency is not yet
measured. The 18.253 second number is only the accepted AI extraction call.
Material quantity completion and final publication were manual in this proof.
Do not present the manual proof duration as production agent latency.

## Production and repository state

Production deployment:

- current committed checkpoint: `12a9e35 feat: open completed estimation v2 details`;
- Railway deployment status: success;
- backend health: HTTP 200;
- `HEAD...origin/main`: 0 0 at checkpoint creation;
- full test suite: 782 passed, 27 warnings;
- `git diff --check`: passed before the deployment commit.

Relevant deployed sequence:

- `7c10728 feat: enable estimation v2 facts shadow`;
- `0df0d92 fix: create estimate shell before objects route`;
- `bca9b87 fix: preserve v2 facts on image-only drawings`;
- `2f85f06 fix: reject unrelated OCR citations`;
- `b58a6d5 fix: normalize square profile sections`;
- `a4f2ead fix: normalize unknown purchased quantities`;
- `12a9e35 feat: open completed estimation v2 details`.

Production schema does not yet expose `economic_classification` and
`price_scope` on `rfq_estimate_lines` through the PostgREST schema cache. The
first write including those fields failed safely, then the draft was written
using the existing compatible schema. Do not assume the purchased-components
migration is active in production until it is verified explicitly.

## What is verified versus still experimental

Verified:

- private original and preview persistence;
- no second OCR call;
- bounded Object Facts extraction;
- private source preview in Object Detail;
- current Company Profile contains Labor and Machinery data;
- deterministic Overhead allocation;
- editable Material, Labor and Overhead rows;
- persisted self-cost totals;
- delivery and installation excluded from self cost;
- one completed production Object Detail;
- low Object Facts model cost and 18.253 second model latency.

Experimental or incomplete:

- automatic material quantity derivation;
- exact 20 mm MDF pricing;
- exact square-tube wall thickness;
- complete role-to-employee mapping policy;
- validated labor baselines for the actual emitted operation mix;
- automatic v2 composition and publication;
- full end-to-end telemetry;
- processing of objects 002 through 004;
- project totals, because three objects remain pending;
- representative real-document end-to-end scenarios;
- remaining operation coverage and batch aggregation.

## Required next implementation order

1. Correct the Estimation data boundary:
   - stop reading legacy `labor` and `company_machines`;
   - read `company_employees` and `company_machinery`;
   - add tests proving the active Company Profile rows are used;
   - prevent double application of the employment factor.
2. Define the bounded Labor role-resolution policy:
   - exact position match first;
   - approved fallback mappings only;
   - unresolved roles remain visible and block or require review;
   - do not invent a universal hourly rate.
3. Implement the deterministic v2 publisher:
   - latest immutable Object Facts input;
   - material requirement resolution with company-first and Israel fallback;
   - deterministic quantity validation from physical operation drivers;
   - Labor Engine using the real production context;
   - company employee rate resolution;
   - deterministic Overhead allocation;
   - atomic material, labor, overhead and total publication;
   - object becomes `completed` only when required lines are publishable.
4. Run the universal planner for the actual production object and validate its
   emitted physical operations. Validate the welding baseline rather than
   accepting it from this proof.
5. Repeat this exact production object from a fresh immutable input with no
   manual calculation. Measure one end-to-end span from File Review action to
   persisted `completed` state.
6. Verify the real authenticated UI:
   - Objects row shows Completed and Review;
   - Object Detail preview loads;
   - all three cost sections are populated;
   - editing one material quantity recalculates totals;
   - editing one labor hour recalculates totals;
   - Approve persists;
   - Back to Objects preserves the updated self cost;
   - refresh preserves every row and total.
7. Only after the single-object automatic cycle is accepted, process the
   remaining objects and implement project-level sales pricing.
8. Continue the deferred 3.15.7 Labor backlog: remaining operation formulas,
   batch aggregation and real-document acceptance scenarios.

## Prohibited shortcuts

- Do not restore or consult the legacy Estimation Agent as architecture.
- Do not read current Labor or Machinery from legacy tables.
- Do not use supplier SKU as a material identity decision signal.
- Do not call OCR again when the persisted OCR package is available.
- Do not send the original document to Object Facts after bounded evidence is
  prepared.
- Do not publish a complete self cost while a required material, labor,
  machinery or overhead line is unresolved.
- Do not hide assumptions behind a numeric value. Persist provenance and
  `needs_review`.
- Do not add delivery or installation to object self cost.
- Do not double-count employer load.
- Do not treat this manual proof as automated end-to-end acceptance.
- Do not change File Review, Objects or Object Detail layout while wiring the
  deterministic backend unless a verified UI defect requires it.

## Dirty worktree preservation

The following pre-existing work remains intentionally dirty and must not be
lost, reverted or folded into an unrelated checkpoint commit:

- `notes/ISRAEL_REFERENCE_MATERIAL_ROUTING.md`;
- `notes/MATERIAL_RESOLUTION_CORE_3_15_3.md`;
- `notes/PRICE_SOURCE_MATERIAL_RESOLUTION_3_15_4.md`;
- `notes/TODO.md`;
- `tests/test_material_identity_resolution.py`;
- `tools/verify_material_identity_resolver.py`;
- `use_cases/material_identity_resolution.py`;
- `use_cases/price_source_material_resolution.py`;
- untracked `.streamlit`;
- untracked `db/sql/3_15_4_israel_global_catalog_v1_parts/`;
- untracked `tmp/`.

The end-of-day checkpoint file must be committed separately from those files.

## Exact restart point

Begin with tests around a new Company Profile labor-context loader. Use company
`610` only as production evidence, not as a hardcoded fixture. The first test
must fail if the implementation queries `labor` or `company_machines`. The
second must prove that an hourly employee rate uses gross pay and receives the
employer factor exactly once. The third must prove that current Machinery codes
reach Labor Engine unchanged.

After those tests pass, implement the smallest automatic publisher that can
reproduce the current `object-001` sections and totals from frozen inputs. Do
not expand to all four objects before this one-object automatic cycle is
measured and accepted.
