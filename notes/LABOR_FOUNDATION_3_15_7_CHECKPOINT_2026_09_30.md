# Labor Foundation Checkpoint, 2026-09-30

Work: 3.15.7, Labor reference-model foundation

Status: active. This checkpoint freezes the accepted preparation work before
route rules are added. It does not modify Estimation Agent, production data, or
the Company Profile Machinery scope.

## Objective

Prepare deterministic, auditable inputs for a future Estimation Agent. The
future agent extracts structured object facts. It does not invent labor hours,
machine minutes, labor rates, or prices. The labor engine later selects routes,
groups compatible work, derives quantities, and applies formulas.

## Accepted architecture

1. `object facts -> requirements -> route -> work operations -> labor hours by
   role -> company labor cost -> overhead`.
2. A time model is `setup + quantity * variable rate`. Setup applies once per
   compatible batch, not once per part.
3. Company machinery chooses the allowed route. Manual, in-house, and external
   routes are mutually exclusive for the same work.
4. A subcontracted fabrication is a purchased component for the customer. Its
   matching internal machine and labor lines must not also be charged.
5. Global physical work identities and baseline time models are separate from
   market prices and company labor rates.
6. Exact 16-capability Machinery scope remains protected. `metal_milling` is a
   production-operation identity, not a new Company Profile machine capability.

## Catalog state

- The operation catalog now contains 78 identities. `metal_milling` was added
  because milling is neither drilling nor laser cutting.
- Roles and drivers were added for `metal_milling`: primary role
  `metal_machine_operator`, primary `cut_length_lm`, secondary `pocket_count`.
- `notes/LABOR_TIME_BASELINE_V0.md` contains the first time baseline for every
  operation, material-specific metal branches, a provenance registry, source
  URLs, and confidence markers.
- Direct source-backed formulas currently cover laser cutting, press-brake
  bending, carbon-steel MIG welding, and selected process structure. Other
  entries are explicitly labelled `E` or `D`, never represented as measured
  facts.

## Evidence model

- `R`: source-backed formula or observed process, confidence 60 to 70.
- `E`: equipment-bound physical model, confidence 40.
- `D`: Costerly derived prior, confidence 25.

The baseline must be superseded by company observations without changing the
operation formula or object schema.

## Protected prior work

Do not discard or overwrite current dirty Price Source, material-catalog,
CNC/Laser, `.streamlit`, `tmp`, test, or purchased-component work. No commit,
push, production migration, or deployed behavior is part of this checkpoint.

## Verification

- Catalog operation insert, role mapping, and driver mapping name
  `metal_milling` consistently.
- Baseline document has explicit confidence and source registry.
- `git diff --check` passes.

## Next action

Create route rules for every operation: entry conditions, company capability
requirements, manual fallback, external component eligibility, exclusions,
batch key, and review condition. This is the next dependency before expanding
formulas or touching Estimation Agent.
