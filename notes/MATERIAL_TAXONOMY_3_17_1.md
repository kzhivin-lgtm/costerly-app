# Unified material taxonomy and identity, 3.17.1

Status: active, P0. Owner-approved 2026-10-08.

## Outcome

Every material-bearing input follows one structured contract before it enters
Price Source, company catalog, Israel Price List, Detection or Estimation.
Material Jobs use the same bilingual evidence layer but follow the separate
operation-offer path.

## Protected boundaries

- Supplier matching, issuer OCR, company-identity blacklist, VAT resolution,
  source deletion and completed-cycle UI remain frozen under 3.16.7.
- Raw source wording, SKU, quantities and prices remain immutable evidence.
- Brand is an attribute, never enough on its own to classify a material.

## Canonical identity and display

Structured identity fields are: `entity`, `primary_attribute`, `brand`, then
ordered secondary attributes: dimensions, technical grade, substrate,
construction, finish, colour and other source-proved qualifiers. SKU is stored
only in the supplier lane. AISI and other steel marks are technical grade, not
brands.

`brand_basis` is explicit: `catalog` for a category-scoped curated match,
`candidate` for a plausible source proper name not yet curated, and `unknown`
when no brand evidence exists. The brand catalogue improves recognition but is
never a whitelist. A candidate is preserved, cannot select a category, and is
reviewable for later catalogue curation.

An entry in the catalogue has one English canonical name. Latin spelling,
Hebrew transliteration and safe OCR variants are input aliases only. Thus
`אגר` and `EGGER` persist and display as `EGGER`; they are not two brands or
two UI localisations. Supplier/distributor names are never added as brand
aliases unless they are a proven product manufacturer or product-system brand.

Canonical display order is:

```text
Entity → primary attribute → brand → secondary attributes
Plywood 10 mm Egger, double-sided, black
```

Absent source evidence stays absent. Matching uses structured attributes, not
the display string or source word order.

## Classification and compact-display matrix

Classification is entity-first. An unknown adjective, trade word or OCR token
never turns a row into `Unclassified` when the entity is otherwise proven.
Conversely, a word such as `glass` is not enough to turn a hinge or hardware
profile into a glass material. Its product role must be determined from the
whole source phrase and the price-table context.

Metal is a stock or structural-metal lane only: sheet, tube, profile, angle,
channel, bar, rod, wire and solid structural section. A fastening, furniture
or mounting part remains Hardware even when it is made from steel or
aluminium. In particular, a mounting, connector or hinge plate is Hardware;
only a source-proven stock plate such as `steel plate` is Metal.

| Department | Entity families | Primary attribute | Bounded secondary attributes |
| --- | --- | --- | --- |
| Wood | plywood, MDF, particleboard, HDF, OSB, laminated panel, solid timber, veneer, edge banding | thickness or timber section | dimensions, species, substrate, construction, finish, colour |
| Hardware | hinge, mounting plate, drawer slide, handle, leg, lift, connector | model or proven series | opening angle, load/length, finish, handedness |
| Metal | sheet, profile, tube, angle, channel, flat/round bar, rod, wire | section or thickness | metal type, technical grade including AISI, wall thickness, finish |
| Glass & Plastics | glass, mirror, acrylic/PMMA, ABS, polycarbonate, PETG, PVC, plastic sheet, vinyl film, aluminium composite panel, sandwich panel | thickness or product form | dimensions, core, fire class, tempering, edge process, finish |
| Coating | paint, lacquer, primer, powder coating, stain, filler, hardener, thinner | system/product type | substrate, sheen, colour, chemistry |
| Material Jobs | cutting and edge banding, machining, metalwork, glasswork, finishing, assembly | reference operation | supplier-proved billing basis and scope only |

The formatter emits at most one entity, one primary attribute, one brand and
up to four identity-bearing secondary attributes. This is an allowlist, not a
word-shortening heuristic: a token enters structured identity only when it is
an attribute of that material or operation. Boilerplate, duplicated
adjectives, seller prose, generic positional words, source SKU, incidental
marketing names and every other non-attribute word are excluded from the
normalised record. They remain only in immutable raw source evidence for audit
or later agent context. They never participate in matching, merge, catalog
storage, Estimation resolution or the canonical display. No formatter may
discard a proven model, dimension, grade, brand or price-class attribute.

For same-supplier material identity, two known but different brands are a
boundary. One missing brand is uncertainty, not a forced split. Supplier SKU
remains a supplier-lane signal and is never a display field or global identity.

## Material Jobs

The bilingual dictionary identifies supplier work such as cutting plus edge
banding, drilling, routing, welding, bending, coating or assembly. A recognised
work line follows:

```text
source row → reference operation → company supplier operation offer
```

It never creates a company material or material offer. The first production
acceptance case is `פס חיתוך + קנט`.

## Pending consumables boundary

The owner requested an explicit small-hardware exclusion boundary. This is a
commercial rule, not a taxonomy rule: a mounting or connector plate remains
Hardware by entity even when it is excluded from the purchasable catalog.
Proposed policy awaiting owner confirmation: after source-price arithmetic is
verified, exclude only a discrete Hardware line whose ex-VAT unit price is at
most ILS 10 and whose source explicitly proves a package or line quantity of
at least 10. The raw source row remains audit evidence with an exclusion
reason. Stock metal, sheets, Material Jobs and a distinct low-cost single
fitting are outside this policy.

## Delivery sequence

1. Audit current taxonomy and define the full department/entity/attribute/job
   matrix, Hebrew and English aliases, likely OCR variants, and exclusions.
2. Research and add department-scoped brand aliases. Brands are preserved but
   cannot select a category alone.
3. Implement the shared structured identity and deterministic formatter.
4. Route Material Jobs through the shared taxonomy and verify the supplier
   operation offer in production.
5. Run representative source, catalog, global-catalog and Detection cases;
   confirm no 3.16.7 regression.

## Acceptance

- One literal source line has one structured identity and the same canonical
  display in every consuming system.
- Hebrew, English and known OCR variants resolve to the same entity where the
  evidence supports it.
- Brand survives display and matching context without becoming the category.
- A true supplier job is never persisted as material, and a material is never
  persisted as a job.
