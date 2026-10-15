# Full handoff: Materials catalog to Material Engine, 2026-10-15

## Purpose of this handoff

This is the authoritative continuation brief for the next chat. It records
what the owner approved, what was actually applied to Supabase, what is only
local implementation work, the problems encountered, and the order of the
remaining work. It supersedes abbreviated status claims in older catalog notes
where they conflict with the decisions below.

Authoritative checkout:

`/Users/qb/Documents/Codex/2026-07-17/detection-gpt-detection-agent-ocr-gpt/work/costerly-progress`

Do not work in `/Users/qb/Documents/ChatGPT/Costerly`.

## Current verified checkpoint

Live Supabase, checked after the owner applied the final SQL on 2026-10-15:

- 53 active material Families;
- 53 active Pricing-Key policies, no active Family lacks one;
- 60 active default variants;
- no static default exists only for:
  - `hardware_drawer_slide`, intentionally, because it has a derived-length
    selection rule instead of a fixed default;
  - `packaging_material`, intentionally, because it is estimate overhead, not
    a material demand;
  - `purchased_fabricated_component`, intentionally, because its component
    type must be specifically identified.

The static default layer is closed. This does **not** mean that every Israel
listing has a supplier-proven physical purchase format. Family-level candidate
formats and default-listing formats are in place. Remaining non-default
listing-format enrichment is catalog-quality work, not permission for Engine
to invent a format.

No commit or deployment has been made for the current local code and note
changes. The worktree is deliberately dirty. Preserve all existing changes,
including `.streamlit/`, `tmp/`, prior SQL migrations and uncommitted runtime
work.

## Domain model and forbidden terminology

Use these exact terms only:

1. **Family**: the material type, for example `plywood`, `sheet_metal` or
   `hardware_hinge`.
2. **Pricing Key**: the one or two primary attributes that distinguish a
   purchasable price class for a Family.
3. **Israel Reference position**: an active, priced Israel-market benchmark
   record. Every Israel Reference position is canonical. A Company Catalog row
   may link many-to-one to it.
4. **Canonical name**: the normalized display name of a position. Its order is
   Family/entity, Pricing-Key attributes, brand only when known, then secondary
   attributes. Department labels, raw underscore codes and irrelevant words
   do not belong in it.
5. **Default**: deterministic completion of omitted Pricing-Key detail only
   after Family is proven. A default is not a source fact and never rewrites
   OCR/source evidence.
6. **Assumption Fallback**: estimate-local handling after Company, Israel and
   approved defaults cannot yield a purchasable candidate. It remains review
   required and creates or updates a Catalog Gap Ticket.

Do not reintroduce `Price Identity`, `Global Model`, a V2 bridge, or another
parallel runtime identity layer. Those concepts caused repeated ambiguity in
the prior architecture and are not part of the approved selection path.

## Canonical catalog structure

For an Israel Reference position:

`Family -> Pricing Key -> canonical name -> active price -> purchase format`

Secondary attributes remain available for evidence, display and compatibility,
but do not create a new Pricing Key unless specifically promoted by policy.

For a Company Catalog item:

`raw supplier evidence -> shared Alias catalog -> normalized Family / key / attributes -> Company offer -> optional Israel Reference link`

The Company item may be Blue when it is complete enough to price but does not
yet link to Israel. Green adds the Israel link. Both may be Estimate Ready if
their pricing, unit and required purchase-format conditions are complete.

## Single Alias catalog

There is one shared Alias catalog for all material interpretation. It contains
Family names, Pricing-Key labels and values, brands and units in English,
Hebrew and Russian. Both incoming flows must use it:

- **Price Source** normalizes supplier invoices, XLS/XLSX and other source
  evidence into Company Catalog offers.
- **Estimation V3** normalizes document and OCR evidence into material
  requirements.

Aliases help recognition only. They do not create a price, prove a missing
attribute, create a catalog position, or make an assumption. Legacy runtime
alias dictionaries must not compete with this shared catalog.

## Approved resolver path

This is the only allowed resolution path:

1. Normalize evidence through the shared Alias catalog.
2. Prove Family, then extract Pricing Key when supported by evidence.
3. Try a complete compatible Company Catalog candidate.
4. If absent, try a complete compatible Israel Reference candidate.
5. If Family is proven but a required key fact is absent, apply the relevant
   approved default, first against Company offers, then Israel Reference.
6. If neither lane can supply the demand, return `assumption_required`.

Assumption Fallback is a separate Estimate orchestration service. It owns the
case-local provisional assumption, its evidence and calculation trace, the
review-required state, and the deduplicated Catalog Gap Ticket. It never
writes a guessed Company or Israel catalog row.

## Family and default decisions

### MDF/HDF is one Family

There is one `mdf_hdf` Family. Raw MDF, HDF, laminated MDF and veneered MDF
are subfamilies expressed by attributes. Its Pricing Key is:

`board_type + surface + thickness`

Approved default variants:

| Proven requirement | Missing key detail | Default purchasing requirement |
| --- | --- | --- |
| MDF, raw | thickness | MDF raw, 17 mm, 2400 x 1220 mm |
| HDF, raw | thickness | HDF raw, 8 mm, 2400 x 1220 mm |
| MDF laminated | thickness | laminated MDF, 17 mm |
| MDF melamine one/two sided | thickness | laminated MDF, 17 mm |
| MDF veneer one/two sided | thickness | veneered MDF, 18 mm |

Explicit source thickness always wins. Surface wording remains in source
evidence, even where the purchasing default maps to a generic available
position.

### Board defaults

- particleboard: P2 furniture-grade raw, 16 mm, `2440 x 1220 mm`;
- standard hardboard: 3 mm, `2440 x 1220 mm`;
- melamine-faced particleboard: 16 mm;
- plywood: 17 mm, `2440 x 1220 mm`;
- special plywood: 15 mm;
- OSB: 12 mm.

The obsolete automatic `2400 x 1220 mm` format on the particleboard and
hardboard default listings was explicitly deactivated. Only `2440 x 1220 mm`
is active for them.

### Metal

- Sheet metal Pricing Key: `metal_type + thickness`.
- Carbon steel, stainless steel and aluminium default: 1.5 mm,
  `3000 x 1500 mm`.
- Copper and brass default: 1.5 mm, `2000 x 1000 mm`.
- `metal_tube` means round tube unless source dimensions prove otherwise. The
  default round tube is 20 mm diameter.
- If source says “tube” but gives `20 x 20`, the dimensions override the loose
  word and it is square profile.
- Square profile default: 20 x 20 mm. Rectangular profile: 40 x 20 mm.
- Angle: 30 x 30 mm. Flat bar: 30 x 1.5 mm. Round bar: 10 mm diameter.
- Wall thickness is secondary. When omitted for ordinary carbon or stainless
  profiles, default it to 1.5 mm. It must never block the Pricing Key.

### Stone, surface and plastics

- acrylic PMMA: 5 mm;
- aluminium composite panel: 4 mm;
- compact laminate: 12 mm;
- composite/lightweight sandwich panel: 10 mm;
- glass and mirror: 4 mm;
- HPL/CPL: 1 mm;
- polycarbonate/PETG/PVC/ABS: 4 mm;
- sheet plastic: 12 mm;
- engineered quartz: 20 mm, `3050 x 1440 mm`;
- natural marble: 20 mm, purchased as calculation unit `1 m²` represented as
  `1000 x 1000 mm`. This does not claim quarry slabs are physically 1 m²;
- porcelain ceramic slab: 12 mm;
- terrazzo / engineered agglomerate: 20 mm;
- Solid Surface is a homogeneous acrylic/mineral surface such as Corian, not
  wood. Default: 12 mm, `3658 x 760 mm`;
- sintered ultra-compact surface currently retains the approved 6 mm default.
  Industry catalogues commonly show 8/12/20 mm ranges, so do not silently
  change this without a separate owner decision.

### Timber, coatings, edge and veneer

- solid timber panel: oak, 20 mm;
- wood veneer: European oak, 0.5 mm;
- edge banding: PVC 24 x 0.8 mm;
- decorative and vinyl film: width 1220 mm, purchased by linear metre;
- paint/lacquer/stain: ordinary matte waterborne clear lacquer;
- powder coating: standard-colour powder coating;
- primer: metal etch primer;
- filler/hardener/thinner: matte solventborne polyurethane clear-lacquer
  system.

### Hardware

Hardware is purchased as a piece/set/package. It uses active
`retail_package` prices, not `material_only` prices. For ordinary unspecified
hardware, resolve the cheapest compatible Company package first, then Israel
Reference. Active default package variants exist for connector, door system,
drawer system, electrical component, fastener, furniture system, handle,
hinge, leg/caster, lift system, lock/latch, mounting part and storage system.

#### Drawer slides are deliberately dynamic

`hardware_drawer_slide` has no static default record. It is governed by the
pending task `3.17.3.6 Drawer-slide derived selection`:

1. Require proven drawer depth.
2. Compute target runner length: `drawer_depth_mm - 100`.
3. Choose the longest compatible Company runner not exceeding the target.
4. If Company has none, choose the longest compatible Israel runner not
   exceeding the target.
5. Missing drawer depth remains review-required. Do not invent a 500 mm slide.

Examples: 600 mm drawer depth selects 500 mm. If depth is 620 mm and standard
lengths are 500 and 550 mm, select 500 mm.

## Purchase-format architecture

There are two different data layers. Do not merge them conceptually:

1. `reference_material_family_supply_formats`: allowed candidate formats for a
   Family. Price Source and Material Engine use it to validate formats and,
   when a source gives only one side, complete the other only if exactly one
   candidate matches.
2. `reference_market_material_supply_formats`: purchasable format attached to
   one Israel Reference listing. Material Engine uses it for real packing and
   whole-unit purchasing.

The Family registry is an open set of allowed formats. It is not a claim that
every supplier offers every format. A missing listing-specific format remains a
known catalog-quality gap and must not be silently fabricated during pricing.

## Material Engine division of responsibility

### Estimation V3

- extracts object, part and evidence facts;
- establishes Family, proven Pricing Key facts and part geometry;
- does not select supplier SKU, calculate prices, invent units or invent a
  purchasable format.

### Material Resolver

- converts normalized requirements into compatible Company and Israel
  candidates under the approved Company-first path;
- applies approved default variants only after Family is proven;
- will own the derived drawer-slide length rule jointly with Engine;
- never calculates sheet nesting or rounds procurement quantities.

### Material Engine

- receives calculation-local demands and resolved supply candidates;
- groups compatible demand across the whole estimate, not per object;
- chooses the least-cost complete Company basket, otherwise Israel basket;
- nests sheet rectangles estimate-wide with kerf, packs linear cuts by stock
  length and rounds packages only at estimate scope;
- allocates final rounded purchase cost back to individual object demands;
- returns `assumption_required`, never an invented price, when no complete
  candidate exists.

### Labor Engine / Resolver

Labor stays separate and is not in current V3 scope. Labor owns operation,
route, machine and minutes. It does not own material defaulting, purchase
format selection, sheet nesting or procurement rounding.

## Estimate/UI decisions

- Object Detail displays the material norm for one object, not the globally
  rounded purchase total.
- The user may edit this one-object norm. The edit is treated as source of
  truth and invalidates the whole-estimate Material Plan.
- Procurement rounding is recalculated globally after every relevant object or
  norm change.
- Rounded purchase cost is allocated proportionally back to objects. Object
  totals must sum exactly to the full purchase-plan cost.
- Object-level Final Approval remains disabled until material planning for all
  estimate objects is complete. Any relevant edit makes all approvals stale.

## Estimation V3 boundary

V3 is the only forward path. Do not restore, compare against, or add a runtime
fallback to V2. The immediate V3 scope is material plan plus approved overhead
only. Labor is disabled until its own Engine/Resolver are accepted.

Local runtime work exists in files including:

- `use_cases/material_engine_adapter.py`
- `use_cases/estimation_runtime.py`
- `use_cases/estimation_material_context.py`
- `use_cases/estimation_v3_material_contract.py`
- `use_cases/material_identity_status.py`

The latest focused `tests/test_material_engine_adapter.py` run passed 22 tests,
but this is not production acceptance. The end-to-end authenticated V3 flow
must be rerun after the catalog closes and the dynamic drawer-slide rule is
implemented.

## Problems encountered and corrections

1. **Alias integration temporarily broke Price Source.** Replacing old
   dictionaries without preserving the existing Price Source normalization
   contract caused all Company offers to become Blue/unlinked and names to
   regress. The corrected direction is additive normalization through the
   shared Alias catalog, not replacing the Price Source resolver path.
2. **The Israel Reference catalog had incorrectly classified and incomplete
   records.** Examples included Plywood names inside MDF/HDF and missing
   Pricing Keys, prices or formats. Catalog migrations normalized canonical
   names, Family, Pricing Key and price linkage.
3. **Defaults were initially confused with assumptions.** This is resolved:
   defaults fill omitted detail of a proven Family; assumptions handle a
   specific unmet requirement after ordinary catalog resolution fails.
4. **The old Solid Surface 6 mm default was not suitable for normal horizontal
   furniture/counter use.** It was corrected to 12 mm, 3658 x 760 mm using
   manufacturer documentation.
5. **The first researched-format SQL had duplicate temporary seed keys.** The
   failed transaction rolled back. Codes were made metal-type-specific before
   the successful run.
6. **The particleboard/hardboard default migration activated an old automatic
   2400 x 1220 format alongside the approved 2440 x 1220 format.** A follow-up
   migration updated the Family policy and deactivated only the obsolete format.
   The final live check confirms only the approved format is active.
7. **Drawer slides were mistakenly reported as a missing static default.**
   This was corrected. They are a dynamic derived-length rule and are now a
   separate tracked Material Resolver/Engine task.

## Applied Supabase migrations in this catalog pass

All following SQL files were run **without RLS**. They create no permanent
client-readable table unless explicitly noted otherwise; the current files use
existing tables and temporary tables only.

1. `2026_10_15_mdf_hdf_subfamily_pricing_key.sql`
2. `2026_10_15_unify_faced_mdf_into_mdf_hdf.sql`
3. `2026_10_15_remove_retired_default_pricing_identity_anchor.sql`
4. `2026_10_15_apply_approved_default_positions_part_1.sql`
5. `2026_10_15_complete_mdf_surface_and_hardware_defaults.sql`
6. `2026_10_15_researched_default_purchase_formats.sql`
7. `2026_10_15_close_particleboard_and_hardboard_defaults.sql`
8. `2026_10_15_correct_particleboard_and_hardboard_sheet_format.sql`

If a future SQL creates a permanent public table, state the RLS choice before
asking the owner to run it. Do not silently disable RLS on a new table.

## Immediate next plan

### 1. Implement 3.17.3.6, Drawer-slide derived selection

Implement in Material Resolver and Material Engine, not in default SQL.

Acceptance cases:

- 600 mm depth, 500 and 550 available: select 500;
- 620 mm depth, 500 and 550 available: select 500;
- compatible Company offer beats Israel offer;
- Israel is used only when Company has no compatible runner;
- no depth means review required, no invented runner;
- trace persists input depth, calculated target, candidates considered and
  selected runner.

### 2. Audit the full candidate bridge

Run a read-only audit that distinguishes:

- default positions, which must have active Israel listing, valid price and
  required listing-level format;
- non-default positions, whose missing listing format is a catalog enrichment
  gap, not a reason to fake it;
- Company offers, which require source/registry-supported purchase format;
- hardware, which must use `retail_package`, unlike material-only families.

Do not return to V2 or old Price Identity in this audit.

### 3. Material Engine end-to-end acceptance

Use fresh Company Price Sources and a multi-object estimate. Verify:

- exact Company resolution when available;
- Israel fallback only when Company cannot complete the basket;
- Family default applied only after Family is proven and required detail is
  missing;
- estimate-wide, not per-object, sheet/linear/package rounding;
- allocation back to objects sums exactly to total procurement cost;
- Material Plan controls Final Approval as specified;
- unresolved exact requirements return `assumption_required` with a review
  trace, never zero price or a fabricated material.

### 4. Only then build Assumption Fallback execution and Labor

Assumption Fallback consumes the Engine's structured unresolved result. It is
not part of document interpretation and must not rerun supplier selection.
Labor Resolver and Labor Engine begin only after material flow is accepted.

## Existing repository records

- Material Engine contract: `notes/MATERIAL_ENGINE_CONTRACT_3_17_3_1.md`
- Current default decision record:
  `notes/DEFAULT_POSITIONS_REMAINING_DECISIONS.md`
- Authoritative backlog: `notes/TODO.md`
- Earlier compact handoff:
  `notes/MATERIALS_CATALOG_AND_ENGINE_HANDOFF_2026_10_15.md`

When starting the next chat, read this file first, then inspect the live
catalog before changing code or data. Do not clear the worktree or rerun old
migrations merely to obtain a clean-looking history.

## Superseding integration checkpoint, 2026-10-15

The catalog closure described above has now been connected to active Estimation
V3, Resolver, Material Engine and Object Detail. The earlier statements that
there was no commit for this runtime work are superseded by
`80937fb`, `8973c01`, `00446db`, `fff7a67` and `111805f` on `main`.

The connection is verified as a partial-plan path, not as accepted estimating
quality. Resolved allocations now display their exact selected canonical names
and prices while unresolved requirements remain unpriced and the plan stays
`needs_review`. The first live run exposed evidence-bound facts defects,
including invented MDF cut rectangles, use of a 14.25 m proxy instead of the
evidenced 4.130 m track, unsupported solid-timber detail and a folding-door
selection for sliding-door evidence. Do not treat the displayed total as a
valid estimate.

The authoritative continuation record is
`notes/ESTIMATION_V3_MATERIAL_PIPELINE_CHECKPOINT_2026_10_15.md`. Its next
task remains within `3.17.4.1`: correct fact extraction and compatibility
before enriching unresolved metal candidates or building Assumption Fallback.
