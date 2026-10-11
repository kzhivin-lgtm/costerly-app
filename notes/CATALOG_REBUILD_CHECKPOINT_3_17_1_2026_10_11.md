# Catalog Rebuild Architecture Checkpoint, 3.17.1, 2026-10-11

This is a decision checkpoint immediately before the first catalog-V2
implementation increment. It is not a clean Git snapshot or a commit: the
worktree already contained owner-directed documentation changes and protected
local-only paths. It records the last accepted architecture, not a rollback
target for unrelated work.

## Accepted target

The owner accepted the object-costing cycle: Detection creates one bounded
evidence package per commercial object; Estimation builds an evidence-backed
manufacturing graph; deterministic Material and Labor engines calculate it.
Any catalog gap must still yield a case-local provisional estimate and one
deduplicated Catalog Gap Job. Research results never create, amend or seed a
canonical catalog record automatically.

## Starting state

- The current catalog, resolver and Labor V0 are transitional foundations.
- No production user compatibility is required, but all internal reader paths
  and database constraints must be replaced and verified before activation.
- Existing material rows, aliases, operations, price sources and machinery
  vocabulary are retained as evidence to classify, not deleted.
- Protected untracked paths remain `.streamlit/`, `tmp/` and
  `db/sql/3_15_4_israel_global_catalog_v1_parts/`.

## First implementation increment

1. Add schema for the canonical catalog V2, case-local assumptions and Catalog
   Gap Jobs.
2. Seed only stable department and role vocabularies.
3. Add a contract test that prevents an assumption or gap job from becoming a
   catalog write.

No database migration has been applied at this checkpoint. No runtime reader,
Agent prompt, Price Source result or Staff Admin surface has changed yet.

## Verification gate for the increment

- Migration has RLS and service-only catalog/gap access.
- Company users can read only their own case-local assumptions.
- Five production departments and six entity roles are seeded exactly once.
- The schema cannot contain automatic canonical-material inserts or updates.
