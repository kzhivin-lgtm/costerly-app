# TODO

This is the authoritative actionable backlog. Completed implementation history
lives in `notes/DONE_LOG.md`; detailed contracts and checkpoints remain in their
linked notes.

## Next product sequence

### 3.15.19 Editable File Review project metadata

- Status: implementation candidate, production UI acceptance pending.
- Priority: P0.
- Outcome: Detection continues to prefill Project name, Partner and Client.
  All three become editable on File Review with
  the same immediate persistence guarantees as edited object names. User edits
  survive refresh, navigation, Last Estimation and the move into Objects.
- Verified current state: `rfq_runs` already stores `project_name`,
  `design_partner` and `client` text. File Review renders them read-only. There
  are no normalized Partner, Project or Version tables yet.
- Confirmed entity boundary: Project, Partner and Client are distinct product
  concepts. Partner is the direct commercial or design intermediary working
  with the Costerly company. Client is the end customer for whom the Project is
  delivered. A direct customer may fill both roles across different Projects.
- Data model: external Partner and Client organizations use one company-scoped
  counterparty directory and acquire their role through Project relationships.
  They must not be inserted into `companies`, which is reserved for Costerly
  tenant accounts. This avoids duplicate organizations when one counterparty is
  a Partner in one Project and a Client in another.
- File Review interaction: each Partner and Client input can select an existing
  company-scoped counterparty or enter a new organization name. Project name can
  select an existing compatible Project or define a new Project. Detection text
  remains the initial editable suggestion, never an immutable identity.
- Project Address is not part of the current MVP. It may be added later as an
  optional Project attribute, never as the Project identity or Project name.
- Confirmed lifecycle: File Review edits persist immediately in the RFQ draft.
  Continue to Objects freezes the selected Project, Partner and Client draft
  metadata for the estimate cycle but does not create new catalog records. An
  existing selected record may retain its stable ID; a newly typed name remains
  draft text. Final Approval transactionally resolves or creates the new
  counterparties and Project, links their separate roles, and creates the
  immutable Estimate Version. An abandoned RFQ therefore leaves no unused
  Partner, Client or Project in the permanent catalog.
- Preserve `Object` exclusively for individual items inside an estimate.
- Acceptance: Detection values render as initial inputs; edit, Enter or blur
  persists each field; empty destructive saves are rejected; refresh and route
  recovery retain committed values; Continue freezes draft metadata without
  creating catalog rows; one company's metadata is inaccessible to another
  company.
- Implemented candidate: the three native File Review inputs persist through an
  allowlisted, company-owned RFQ update; cache and widget state are scoped by
  run; Continue repeats one atomic draft save before starting Estimation; no
  Partner, Client or Project catalog table is created. Full suite: 862 passed.
- Remaining verification: authenticated production render, one edit by Enter,
  one edit by blur, refresh, Last Estimation recovery and Continue to Objects.
- Production regression repair in progress: the 2026-10-02 metadata deployment
  also activated the previously rejected service-header scroll guard. Production
  telemetry then recorded repeated 15-second transition timeouts even after the
  destination emitted `app-ready`. The isolated candidate removes only that
  guard and must pass the protected authenticated production transition matrix
  before 3.15.19 can be accepted.

### 3.15.20 Final Approval and Client Proposal PDF

- Status: pending after 3.15.19.
- Priority: P0.
- Outcome: after all Objects are calculated and individually approved, the user
  reviews the final project calculation and explicitly completes Final Approval.
  That action closes the mutable RFQ cycle, creates an immutable calculation
  version and produces the client-facing proposal artifact.
- Confirmed boundary: Final Approval generates and stores the PDF server-side.
  Download is a separate optional action and does not determine whether the
  estimate is finalized.
- Proposal content must be derived from the approved deterministic totals and
  current company Pricing Policy. It must never recalculate prices independently
  inside the PDF renderer.
- Acceptance: Final Approval is unavailable while an Object is unfinished or
  unapproved; repeated submission is idempotent; the stored version and PDF
  share one immutable calculation snapshot; download can happen immediately or
  later; new Partner, Client and Project records are created only here;
  generation failure is recoverable without duplicating the version or catalog
  records.

### 3.15.21 Projects workspace

- Status: pending after 3.15.20.
- Priority: P0.
- Outcome: provide the durable hierarchy
  `Counterparties as Partner and Client -> Project -> Versions -> Objects /
  Estimate / source files / PDF`. Partner and Client are separate relationships
  on a Project. One counterparty may hold different roles in different Projects.
  Each Project retains an append-only history of calculation versions rather
  than overwriting previous results.
- MVP scope: browse Partners, browse their Projects, open one Project, inspect
  its versions, reopen the approved calculation snapshot and download any
  generated proposal.
- Later scope, not part of this task: upload a revised source into an existing
  Project, compare it with the previous version, classify added, removed and
  changed Objects, and recalculate only affected work.
- Dependency: 3.15.19 defines editable identity metadata; 3.15.20 defines the
  immutable version and finalization boundary.
- Acceptance: company isolation, deterministic version numbering, immutable old
  versions, source-file and PDF retention, and route recovery from Projects into
  the selected approved calculation.

## Estimation and material resolution

### 3.15.8 Estimation v2 production stability

- Status: active, pending verification.
- Priority: P0.
- Outcome: every non-ignored detected object reaches an editable Object Detail
  result without a terminal domain failure. Missing exact dimensions, catalog
  prices, company labor rates, optional features, or bounded model fields must
  produce logged assumptions and a provisional estimate, not abort the batch.
- Verified implementation: validation and publication are isolated per object;
  unresolved prices remain visible for review; source previews, Materials,
  Labor, Overhead and self cost are published through Estimation v2.
- Acceptance: run one new representative production cycle and confirm that
  every object completes, Objects receives totals incrementally, Object Detail
  opens for every object, and every approximation is retained in diagnostics.
- Dependency: resolver price quality is not required for runtime acceptance,
  but a technical provider or persistence failure may still be terminal.

### 3.15.11 Israel Price List and resolver normalization

- Status: pending, next after the 3.15.8 production pass.
- Priority: P0.
- Outcome: one coherent material-resolution system for Estimation and Price
  Source. It must match a model-authored material to a company material first,
  then the Israel Price List, without mixing incompatible categories, forms or
  price-bearing subcategories.
- Merged scope: the remaining resolver-policy audit from 3.15.8 and unresolved
  Price Source resolver work from 3.15.4. Their work-number references remain
  historical and are not reassigned.
- Required work:
  1. Formalize family-specific price attributes and compatibility rules.
  2. Start with MDF/HDF: standard, moisture-resistant, fire-retardant, raw,
     PET-faced, acrylic-faced, lacquered, veneer-faced and HPL-faced boards.
  3. Keep sheet, plate, square tube, rectangular tube, round tube, angle, bar,
     channel and other metal forms separate.
  4. Define supported units, conversions, rounding and nearest-size rules for
     every family before automatic pricing is accepted.
  5. Audit `reference_material_pricing_identity_members` and generated
     `price_attributes` for incompatible identities.
  6. Preserve company-first pricing and Israel-only fallback for the MVP.
  7. Keep SKU as provenance only. SKU cannot resolve, rank, shortlist, trigger
     review, select an identity or select a price.
- Verified partial implementation:
  - arbitrary fixed price fallbacks such as ILS 25 per metre are removed;
  - unresolved materials receive no invented unit price;
  - sheet thickness uses exact, next greater, then nearest lower available
    thickness inside the compatible sheet family;
  - furniture hollow profiles and angles default missing wall thickness to
    1.5 mm;
  - square, rectangular, round and angle profile fallback pricing filters the
    kilogram source by profile form and converts weight to length;
  - routine consumables are excluded from material matching and handled by
    Pricing Policy.
- Known gap: form protection and conversions are not yet formalized and proven
  across all material families. A family-level median remains an evidence-based
  approximation, not an accepted final resolver policy.
- Acceptance: family fixtures prove compatible matches and rejection of every
  adjacent incompatible form or subcategory; one persisted Price Source dataset
  is reprocessed without OCR; one production Estimation cycle demonstrates the
  same rules and preserves diagnostics.

### 3.15.10 Review Required workspace

- Status: pending, not currently actionable.
- Priority: P1.
- Dependency: stable 3.15.11 resolver reason codes and family rules.
- Outcome: an internal workspace for material, labor, machinery, conversion and
  other estimation mismatches. Each case retains the original fact, applied
  fallback, evidence, confidence, cost impact and resolution. Accepted
  resolutions improve the shared deterministic policy without blocking the
  customer estimate.
- Includes the former 3.15.5 Material Identity review-interface outcome. It is
  one internal review system, not two competing tools.

### 3.15.13 Labor Engine review

- Status: pending.
- Priority: P1 after material resolution.
- Outcome: inspect universal operation coverage, physical drivers, routing,
  formulas, company-rate selection, fallback rates, aggregation and displayed
  totals across wood, metal and mixed objects.
- Constraint: no canonical objects and no object-specific labor templates.
- Preserved foundation: 3.15.7 and
  `notes/LABOR_FOUNDATION_3_15_7_CHECKPOINT_2026_09_30.md`.
- Acceptance: representative real-document scenarios, batch aggregation and
  traceable operation-level totals. Do not treat a prior production result or
  an informal hour estimate as a benchmark.

## RFQ lifecycle and navigation

### 3.15.14 RFQ cancellation and Project finalization

- Status: pending.
- Priority: P1.
- Outcome: one upload creates one explicit RFQ cycle. Starting a new upload is
  the cancellation boundary for unfinished queued or running work. It prevents
  later publication for the superseded run and records an auditable cancelled
  outcome. A successfully generated client PDF finalizes the RFQ and creates
  the durable Project record.
- Acceptance: cancellation during queued and running phases, no orphan provider
  work, no Project before PDF, and reopening a finalized Project.

### 3.15.16 Header controls scroll stability

- Status: deferred.
- Priority: P2.
- Trigger: resume only when production DOM geometry can be inspected during
  real scrolling.
- Outcome: accepted resting header controls remain stable while File Review,
  Objects, Object Detail, Company Profile and Platform Admin content scrolls.
  Upload and Auth are out of scope.
- Do not repeat approaches rejected in
  `notes/HEADER_CONTROLS_SCROLL_FAILED_ATTEMPTS_2026_10_02.md`.
- The rejected generic service-header scroll guard was removed again during
  3.15.19 transition regression repair. Do not restore it as a workaround.

## Pricing and Company Profile

### 3.15.17 Pricing Policy production acceptance

- Status: implementation complete, production interaction verification pending.
- Priority: P1, small verification task.
- Verified implementation: Pricing stores VAT, warranty, management,
  consumables, packaging, paint consumables, default markup, delivery and
  installation. Estimation and Objects consume the persisted policy.
- Acceptance: in the authenticated production Profile, change representative
  values, Save, reload, and confirm persistence plus recalculated object and
  project totals.

### 3.15.18 Machinery session-draft production acceptance

- Status: implementation complete, production interaction verification pending.
- Priority: P1, small verification task.
- Verified implementation: selector changes remain in a session draft across
  Profile tabs; Supabase writes occur only through the bottom Save action and
  only for changed routes.
- Acceptance: make unsaved changes, visit another Profile tab, return, confirm
  the draft remains, Save once, reload, and confirm persisted values.

## Price Source and internal observability

### Price Source accuracy and performance

- Status: pending.
- Priority: P1 after 3.15.11 resolver rules.
- Related work numbers: 3.12.1, 3.15.4 and 3.15.6.
- Outcome: improve extraction accuracy, service-row exclusion, unit
  normalization, identity candidate recall, pricing activation decisions,
  latency and recoverable progress while preserving the accepted Price Lists UI.
- Required production evidence: representative URL, PDF, spreadsheet and photo;
  exact, shortlist and unmatched resolver outcomes; timing by fetch, parsing,
  model, persistence and identity stages.
- Constraint: reprocess persisted source rows when possible, without paying for
  OCR or extraction again.

### Cross-agent failure observability

- Status: pending proposal.
- Priority: P1 internal reliability.
- Outcome: record every attempted Detection, Estimation, Price Source and
  Material Identity run before external work starts. Retain company-safe
  correlation ID, stage, timing, provider metadata and sanitized error, then
  expose retry and grouping by failure signature internally.
- Clarification: this is not Token Cost. Token Cost answers how much successful
  or failed model work cost. Failure observability answers where and why a run
  failed. The systems may share event storage but have different outcomes.

### Batch Price Source ingestion

- Status: deferred after MVP.
- Priority: P2.
- Outcome: allow several independent supplier documents to be dropped in one
  action and process them as separate bounded jobs. Each document keeps its own
  progress, result, retry, duplicate decision, timing and cost. Several image
  pages may still represent one logical document.
- Current behavior: one PDF, spreadsheet or CSV per extraction. This task is
  convenience and throughput work, not required for Price Source correctness.

## Detection, manufacturing and product follow-ups

### Detection quality and large-document routing

- Status: pending.
- Priority: P1 after Estimation and resolver stability.
- Outcome: improve object boundaries and dimension attribution without repeating
  OCR or allowing Naming to change object identity. Benchmark fresh files with
  multiple cold runs and record quality, time, tokens and cost.
- Deferred large-PDF requirement: estimate the complete provider payload and
  use a supported file-upload route before an inline request approaches its
  transport limit. Do not retry a non-retriable 413 through another model.

### CNC and Laser completion

- Status: pending verification and parameter-library work.
- Priority: P1 with Labor review.
- Related work number: 3.14.1.
- Outcome: finish production acceptance of deterministic routing, supplier
  minimums, four calculators, estimate levels and the internal parameter library
  while preserving the approved Company Profile Machinery capability subset.

### UI and export follow-ups

- Status: pending or deferred as listed.
- Priority: P2 unless a production regression is observed.
- Object UI: reduce the Objects pricing header gap, show a running Self Cost
  spinner, format whole object quantities without `.0`, keep Delivery and
  Installation free of object self-cost status, show AI Confidence when
  available, and remove stale fragment flicker after Back or Approve.
- Upload: revisit cold-start skeleton and optional post-deploy prewarm.
- Copy: audit remaining user-facing blocks for the no-final-period rule.
- Company Logo: production-check PNG and PDF inputs. SVG is already accepted.
- Export: add XLS proposal export.
- Detection: add a missing-object second-pass flow only after its object-identity
  contract is defined.
- Profile feedback: standardize success-message placement and dismissal.

## Completed and removed from the actionable queue

- 3.15.9 Active RFQ navigation recovery: completed and owner-accepted at
  `348604a`. `Last Estimation` restores the newest company-owned estimate through
  File Review, `New Estimation` opens Upload without deleting the prior estimate,
  and route lookups are company-scoped. Reverified by the focused 02.10 test run.
- 3.15.12 Paint consumables policy: completed in 3.15.17. The locked Paint
  consumables row is the configured percentage of explicit coating material
  cost and remains zero when no coating exists.
- Arbitrary fixed material-price fallbacks: removed. Tests require unresolved
  material prices to remain unresolved rather than inventing a unit price.
- Missing furniture profile wall thickness: completed at 1.5 mm for square,
  rectangular and round hollow profiles and angles. Explicit thickness wins.
- Sign in password Enter behavior: completed. Enter targets Sign in rather than
  Forgot password, with a dedicated regression test.
- Token Cost Admin observability: completed for the current requested scope.
  Platform Admin shows Detection, Estimation, Price Source and total AI cost.
- Local Price Source green-on-green report: removed from the actionable queue.
  There is no current reproducible evidence. Reopen only with a new production
  observation or screenshot.

## Verification for this reconciliation

- Focused navigation, Estimation publisher, resolver, Pricing Policy, Admin and
  Auth suite: 286 passed, 5 warnings on 02.10.2026.
- Full-suite checkpoint immediately before this reconciliation: 857 passed,
  25 warnings at commit `f58315c`.
