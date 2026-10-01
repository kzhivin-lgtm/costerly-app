# Materials and Labor checkpoint, 2026-09-30

Work: 3.15.1 through 3.15.7 accumulated foundation

Status: saved implementation checkpoint before continuation in a new chat.

## Included state

- Israel global catalog v1: 4,436 canonical recognition rows, 45 categories
  and 8,872 English and Hebrew aliases.
- Israel pricing identity layer and company-first material-price routing.
- Purchased fabricated component classification for external CNC, laser,
  stone and related supplier fabrication.
- CNC and Laser costing, routing and Estimation scaffold integration already
  present in the dirty worktree.
- Labor taxonomy: 78 operations with roles and physical drivers.
- Labor time baselines with formula evidence, sources and confidence classes.
- Route rules, operation formulas, crew rules and ten
  golden scenarios.
- Historical object-specific Labor proof, superseded by the universal
  operation-plan engine on 2026-10-01.
- Full continuation handoff in
  `notes/MATERIALS_LABOR_NEXT_CHAT_HANDOFF_2026_09_30.md`.

## Verification

- Full automated suite: 720 passed, 27 deprecation warnings.
- Targeted Labor and manufacturing suite: 40 passed.
- `git diff --check`: passed.
- Duplicate 12-part SQL export was byte-compared. The copy under
  `db/sql/3_15_4_israel_global_catalog_v1_parts/` is identical to the 12 files
  in `db/sql/` and is intentionally excluded from the Git checkpoint.
- Secret-bearing and local runtime data under `tmp/` is intentionally excluded.
- `.streamlit/` is intentionally excluded and preserved locally.

## Checkpoint limitations

- Estimation v2 is not implemented or connected.
- Labor Engine was not production complete at this checkpoint.
- Cross-object batch aggregation is not implemented.
- Internal material identity review UI is not implemented.
- Price Source latency, progress UX and production source matrix remain open.
- No production deployment or database migration is performed by this
  checkpoint.

## Protected next step

This protected next step was superseded on 2026-10-01. Continue with universal
agent-created operations, batch aggregation, route guards and production
scenarios without object-specific routing.
