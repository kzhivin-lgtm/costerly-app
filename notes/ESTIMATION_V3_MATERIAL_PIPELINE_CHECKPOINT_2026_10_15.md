# Estimation V3 to Material Engine checkpoint, 2026-10-15

## Status

Checkpoint status: integrated and committed to `main`, not accepted as a
correct estimate. This record is the authoritative result of the first
end-to-end V3 material run after catalog closure. It distinguishes confirmed
transport and pricing behavior from material facts that were not supported by
the source document.

Authoritative checkout:

`/Users/qb/Documents/Codex/2026-07-17/detection-gpt-detection-agent-ocr-gpt/work/costerly-progress`

Protected local-only paths remain untracked and must not be committed:
`.streamlit/` and `tmp/`.

## Confirmed implementation state

The following commits are on `main`:

| Commit | Change |
| --- | --- |
| `80937fb` | Adds the raw MDF 20 mm Israel Reference position and fixes bare-MDF normalization to `board_type=mdf`, `surface=raw`. |
| `8973c01` | Lets the Engine plan interim sheet demands and split oversized evidenced parts across purchasable sheets. |
| `00446db` | Carries the selected canonical position name through the persisted Material Plan to Object Detail. |
| `fff7a67` | Completes material-demand intake from evidence, recognizes the metal aliases, adds explicitly review-visible proxy demand when no quantity is available, and excludes out-of-scope overhead families from V3 facts. |
| `111805f` | Publishes priced, resolved allocations from a partial `needs_review` Material Plan, without pretending that unresolved lines are priced. |

Focused automated verification at this checkpoint passed: 61 tests covering
V3 facts, facts contract, Material Engine, adapter, estimation runtime and
material-plan norms. `git diff --check` also passed before `111805f`.

## Verified pipeline behavior

The active flow is:

1. Detection supplies an object and bounded source evidence.
2. Estimation V3 emits material facts only. It does not select a supplier
   position or calculate a price.
3. Resolver and Material Engine evaluate Company Catalog candidates first,
   then Israel Reference candidates, then return `assumption_required`.
4. The Engine persists one estimate-wide Material Plan and allocation trace.
5. Object Detail publishes every resolved allocation even when the overall
   plan is still `needs_review`; unresolved lines remain visibly unpriced.

This preserves the approved Company-first, Israel-Reference-second route.
There is no active V2 pricing or Material Engine fallback.

Families `packaging_material`, `paint_lacquer_stain`, `powder_coating`,
`primer`, `filler_hardener_thinner` and `hardware_fastener` are excluded from
V3 material facts. They remain separate formula-overhead scope. They are not
silently priced as catalog material demands.

## Production evidence examined

Estimate run:

`run_3c96bbd80b534ef6b4a31ab58a8841d5_estimate_20261015155745`

The incoming Detection result collapsed the intended three subjects into one
object, `Track-mounted shelving unit`. That Detection defect is outside this
checkpoint. It nevertheless supplied enough text to test the downstream
material route.

The persisted plan is `needs_review` and proves the mixed outcome works:

| Requirement in UI | Resolver result | Displayed result | Assessment |
| --- | --- | --- | --- |
| MDF 20 mm, raw | Company Catalog | `MDF 20 mm 1220 × 2440 mm, raw`, 15 sheets, ₪3,660 | Canonical name and allocation are correct for the supplied demand. |
| Solid timber panel | Company Catalog default | `Solid Timber 30 mm 1220 × 2440 mm, Oak`, 5 sheets, ₪7,219 | Name is canonical, but Oak and 30 mm are not source-proven. This is an assumption/default quality problem. |
| Door system | Israel Reference | `Folding door system`, 1 piece, ₪34 | Name and arithmetic are canonical, but the choice is semantically wrong for evidence describing sliding doors and track. |
| Perforated sheet, tube, angle, track | No complete candidate | Generic requirement, quantity shown, no price or cost | Correctly remains unpriced and review-required. |

The visible subtotal, ₪10,912, is internally consistent with persisted
allocations: ₪3,660 + ₪7,218.74 + ₪33.75 = ₪10,912.49 before displayed
rounding. VAT and total shown in the interface are also consistent with that
subtotal. The displayed unit costs are rounded presentation values, while the
line totals retain the unrounded allocation values.

## Rejected interpretation and known defects

The current output is not a valid material estimate. These are confirmed input
or selection defects, not arithmetic defects in the already selected rows:

1. The agent invented MDF cut geometry: `5 × 4130 × 1660 mm` and
   `2 × 1760 × 300 mm` are not supported by the source evidence. The Engine
   correctly nested those supplied parts into 15 sheets, but must never receive
   fabricated parts.
2. The direct evidence says the track span is 4.130 m. The emitted 14.25 m is
   an envelope-perimeter proxy, not an evidenced track length.
3. The solid-timber requirement is an unsupported generic proxy. The document
   proves two door leaves of 950 × 2345 mm, not 12.36935 m² of Oak 30 mm.
4. A sliding-door/track requirement must not resolve to `Folding door system`.
   When physical subtype is incompatible, the line must remain unresolved until
   a matching candidate or explicit assumption exists.
5. The metal sheet, tube, angle and track lines have no complete compatible
   candidate. Their unpriced state is correct. Their Catalog enrichment and
   material-fact precision are separate causes and must not be masked with
   zero price or an unrelated default.

## Binding rules preserved by this checkpoint

- A canonical display name is shown only after Resolver selected that exact
  Company Catalog or Israel Reference position.
- A partial plan may show resolved prices and costs, but its status remains
  `needs_review` until every material demand is resolved or explicitly handled
  by Assumption Fallback.
- Estimation may emit a part rectangle only when dimensions and quantity are
  supported by its bounded evidence. Missing geometry is not permission to
  manufacture cut parts.
- A review-visible proxy demand is allowed only as an explicit assumption
  fallback input. It cannot override an exact evidenced measurement, and its
  selection must not cross physical subtype, such as sliding versus folding.
- Engine packing and cost arithmetic stay deterministic. It consumes facts and
  candidates, it does not repair incorrect document interpretation.

## Current next task

Continue `3.17.4.1`, do not open a new material block. Repair the material
facts boundary before further catalog work:

1. reject unsupported inferred part rectangles;
2. prefer explicit evidence measurements, including the 4.130 m track span,
   over envelope proxies;
3. represent missing geometry as a review-visible assumption demand rather
   than as fabricated cuts;
4. add a compatibility guard so a sliding-door requirement cannot select a
   folding-door position;
5. rerun this exact persisted evidence through V3 and verify that every priced
   line is both canonical and source-compatible, while every other line is
   explicitly unresolved.

The separate unresolved metal candidate coverage is then catalog work. Do not
reopen Packaging, paint consumables or Fasteners as Material Engine demands.
