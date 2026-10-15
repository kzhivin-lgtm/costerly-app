# Materials catalog and Material Engine handoff, 2026-10-15

## Status at handoff

The static catalog-default layer is closed. The remaining drawer-slide rule is
a dynamic Resolver and Material Engine task, not a catalog-default gap.

Live check after the owner applied
`2026_10_15_researched_default_purchase_formats.sql`:

- 53 active Families and 53 active Pricing-Key policies;
- 58 active default variants;
- no active Family is missing a Pricing-Key policy;
- the researched formats below are present on their default Israel positions;
- `particleboard` and `fibreboard_hardboard` have active approved defaults and
  one active purchase format each, `2440 x 1220 mm`;
- `hardware_drawer_slide` deliberately has no static default. It requires the
  tracked dynamic selection rule `3.17.3.6`;
- `packaging_material` and `purchased_fabricated_component` intentionally have
  no default. Packaging is added by estimate policy, while a purchased,
  fabricated component must remain specifically identified.

The prior broad audit also found that many non-default Israel positions have no
listing-level purchase format. The family supply-format registry gives allowed
candidate formats, but it is not a substitute for completing supplier/listing
formats where a specific listing must drive a physical purchase basket.

## Terminology and invariant

Use only the established terms:

- **Family**: material type.
- **Pricing Key**: the one or two primary categorising attributes required to
  price a Family.
- **Israel Reference position**: an active, priced Israel market position. It
  is the common benchmark to which Company Catalog positions can link.
- **Canonical name**: the display name of the position, in this order:
  entity/Family, Pricing Key attributes, brand only when known, then secondary
  attributes. Do not put department names, raw underscore codes or irrelevant
  words into the name.
- **Default**: deterministic completion of omitted Pricing-Key detail after
  Family is known. It is not an assumption.
- **Assumption Fallback**: estimate-local outcome only after Company Catalog,
  Israel Reference and approved defaults cannot provide a purchasable result.
  It must retain evidence, mark review required and create/update a Catalog Gap
  Ticket. It never writes an invented catalog record.

Do not introduce `Global Model`, `Price Identity`, or another parallel
identity naming layer into runtime.

## One catalog interpretation mechanism

The shared Alias catalog is the only interpretation dictionary for incoming
material language. It holds Family names, Pricing-Key values, brands and units
in English, Hebrew and Russian. Both flows must use it:

1. Price Source turns supplier evidence into a normalized Company Catalog row.
2. Estimation turns document/OCR evidence into a normalized Material Demand.

No hidden legacy runtime alias list or V2 bridge may compete with this catalog.
Aliases determine interpretation only. They never create a price, a catalog
position, or an assumed attribute.

## Resolver path, approved as the only path

1. Normalize evidence through the shared Alias catalog.
2. Determine Family and, when evidence supports it, Pricing Key.
3. Seek an exact compatible Company Catalog offer first.
4. If absent, seek an exact compatible Israel Reference position.
5. If the Family is known but required key detail is absent, use that Family or
   approved subfamily default, Company first and then Israel Reference.
6. If no complete purchasable candidate exists, return `assumption_required`.
   The separate Assumption Fallback orchestration owns the temporary estimate
   assumption, review state and Catalog Gap Ticket.

Blue means the Company row is complete enough to price but has no canonical
Israel link. Green means it has that canonical link. Both can be Estimate Ready
when their respective pricing conditions are met.

## Pricing-Key and default decisions

### MDF/HDF

There is one active `mdf_hdf` Family, not separate raw, laminated, veneered or
HDF Families. Its Pricing Key is:

`board_type + surface + thickness`

Approved defaults:

- raw MDF: 17 mm, 2400 x 1220 mm;
- HDF: 8 mm, 2400 x 1220 mm;
- laminated MDF, one or two sided when thickness is absent: 17 mm;
- veneered MDF, one or two sided when thickness is absent: 18 mm.

The source evidence must retain the declared surface. A default fills only
missing thickness, it must not overwrite a source fact.

### Metal stock

- `metal_tube` means a round tube by default: 20 mm diameter.
- A source calling something “tube” but specifying `20 x 20` means square
  profile, because the two dimensions override the loose word “tube”.
- Square profile default: 20 x 20 mm. Rectangular profile default: 40 x 20 mm.
- Angle default: 30 x 30 mm. Round bar default: 10 mm diameter. Flat bar
  default: 30 x 1.5 mm.
- Wall thickness is a secondary attribute, never required for Price Key. For
  ordinary carbon and stainless profiles, when omitted it defaults to 1.5 mm.
- Sheet metal Pricing Key: `metal_type + thickness`.
- Sheet-metal defaults: carbon steel, stainless steel and aluminium use 1.5 mm
  and 3000 x 1500 mm. Copper and brass use 1.5 mm and 2000 x 1000 mm.

### Stone and surface material defaults

- engineered quartz: 20 mm, 3050 x 1440 mm;
- natural marble: 20 mm. It uses a calculation purchase unit of 1 m², stored
  as 1000 x 1000 mm with `approved_calculation_unit`. This is not a claim about
  physical quarry slab size;
- Solid Surface is an acrylic/mineral homogeneous surface such as Corian, not
  wood. Approved default is 12 mm, 3658 x 760 mm. The old 6 mm default was
  corrected because 6 mm is a vertical-application product in Corian’s own
  documentation;
- sintered ultra-compact surface still needs an explicit decision whether the
  approved default is retained at 6 mm or corrected to an industry-standard
  8/12 mm product. Do not silently change it.

### Other settled defaults

- acrylic PMMA: 5 mm;
- aluminium composite panel: 4 mm;
- compact laminate: 12 mm;
- composite/lightweight sandwich panel: 10 mm;
- edge banding: PVC 24 x 0.8 mm;
- glass and mirror: 4 mm;
- HPL/CPL: 1 mm;
- melamine-faced particleboard: 16 mm;
- plywood: 17 mm, special plywood: 15 mm;
- OSB: 12 mm;
- sheet plastic: 12 mm;
- polycarbonate/PETG/PVC/ABS: 4 mm;
- porcelain ceramic slab: 12 mm;
- terrazzo/engineered agglomerate: 20 mm;
- wood veneer: European oak, 0.5 mm;
- solid timber panel: oak, 20 mm;
- paint/lacquer/stain: ordinary matte waterborne clear lacquer;
- powder coating: standard-colour powder coating;
- primer: metal etch primer;
- filler/hardener/thinner: matte solventborne polyurethane clear-lacquer
  system.

### Hardware

Hardware is priced as a purchasable package or piece, not as raw material. The
approved policy is the lowest-priced compatible Company offer, then Israel
Reference offer, rather than blocking an estimate for brand/specification.
Hardware defaults exist for the main hinge, handle, leg/caster, connector,
fastener, lock/latch, lift, mounting, storage, electrical, door-system,
drawer-system and furniture-system Families.

`hardware_drawer_slide` deliberately has no fixed default. Drawer-slide length
is derived from drawer/cabinet depth minus 100 mm. Resolver and Material Engine
must select the longest available compatible runner not exceeding that target.

## Purchase-format data model

There are two distinct stores. Do not merge them conceptually:

1. `reference_material_family_supply_formats`: allowed physical formats for a
   Family. Material Engine uses it to interpret or complete a one-sided source
   format, and Price Source uses it to validate source formats.
2. `reference_market_material_supply_formats`: actual/approved purchasable
   format of a specific Israel Reference listing. Material Engine uses it for
   purchasing and packing.

Applied SQL, all run without RLS because they create no permanent
client-accessible tables:

- `2026_10_15_mdf_hdf_subfamily_pricing_key.sql`
- `2026_10_15_unify_faced_mdf_into_mdf_hdf.sql`
- `2026_10_15_remove_retired_default_pricing_identity_anchor.sql`
- `2026_10_15_apply_approved_default_positions_part_1.sql`
- `2026_10_15_complete_mdf_surface_and_hardware_defaults.sql`
- `2026_10_15_researched_default_purchase_formats.sql`

The last migration was verified live. It assigned formats to the default Israel
positions for quartz, Solid Surface, natural stone, and each carbon/stainless/
aluminium/copper/brass sheet-metal default.

## Material Engine contract

Authoritative design: `notes/MATERIAL_ENGINE_CONTRACT_3_17_3_1.md`.

Responsibilities:

- Estimation V3 extracts objects, parts and evidence. It identifies a material
  requirement, Family and supported Pricing Key. It does not calculate prices
  or invent procurement formats.
- Material Resolver selects compatible Company or Israel candidates according
  to the path above.
- Material Engine receives resolved `MaterialDemand` records and candidates.
  It aggregates all objects within the estimate by selection key before any
  rounding. It selects a whole-estimate purchase basket deterministically.
- For sheet stock, it nests rectangles across the full estimate with kerf. For
  linear stock it packs cuts across the estimate. For packages it rounds only
  at the estimate-wide package level. It retains the allocation back to each
  object.
- Labor Engine is separate. It owns manufacturing operation minutes and rates,
  not material defaulting, sheet nesting or purchasing selection.

UI / interaction decisions:

- Object Detail shows material norm per one object, not total rounded purchase
  quantity. The user may edit that norm.
- Any norm edit invalidates and recalculates the estimate-wide purchase plan.
- Procurement cost is allocated proportionally back to objects after global
  rounding.
- Object-level Final Approval remains disabled until material plans for all
  objects in the estimate have completed. A change in any file/object triggers
  estimate-wide material recalculation.

## Estimation V3 boundary

V3 is the only forward path. Do not restore V2 or compare against it.

Current intended V3 scope:

- calculate material plan and material cost;
- apply established overhead rows;
- do not calculate labor until Labor Engine and Labor Resolver are built;
- expose unresolved outcomes rather than silently producing zero prices;
- later, invoke separate Assumption Fallback orchestration when no Company,
  Israel or default candidate can satisfy the demand.

Existing local, uncommitted implementation work includes Material Engine
adapter/default logic. `tests/test_material_engine_adapter.py` last passed with
22 tests. It has not yet been committed, deployed or end-to-end accepted in the
authenticated production flow.

## Immediate next work

1. Close the two static catalog defaults with one focused migration:
   - `particleboard`: approved raw furniture-grade 16 mm, 2440 x 1220 mm;
   - `fibreboard_hardboard`: approved raw hardboard 3 mm, 2440 x 1220 mm;
2. Implement `3.17.3.6 Drawer-slide derived selection` in Resolver and Engine.
3. Run a correct coverage audit:
   - each active operational Family has policy;
   - each such Family has default(s), except explicit `packaging_material` and
     `purchased_fabricated_component` exclusions;
   - each default reference position has an active Israel listing, active
     compatible price and required listing-level purchase format;
   - report, do not mask, remaining non-default listing-format holes.
4. Only after that, connect the now-complete catalog to the Material Engine and
   test end-to-end against fresh Price Source data and Estimate documents.

## Repository discipline

Authoritative checkout:

`/Users/qb/Documents/Codex/2026-07-17/detection-gpt-detection-agent-ocr-gpt/work/costerly-progress`

Do not reset or discard the existing dirty worktree. It contains user and prior
in-progress edits, untracked SQL and `tmp/`. No commit or production deployment
occurred during this catalog-default pass.
