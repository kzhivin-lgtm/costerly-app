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

Canonical display order is:

```text
Entity → primary attribute → brand → secondary attributes
Plywood 10 mm Egger, double-sided, black
```

Absent source evidence stays absent. Matching uses structured attributes, not
the display string or source word order.

## Material Jobs

The bilingual dictionary identifies supplier work such as cutting plus edge
banding, drilling, routing, welding, bending, coating or assembly. A recognised
work line follows:

```text
source row → reference operation → company supplier operation offer
```

It never creates a company material or material offer. The first production
acceptance case is `פס חיתוך + קנט`.

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
