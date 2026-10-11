# Global-Market Catalog Rebuild Checkpoint, 3.17.2, 2026-10-11

## Purpose and rollback point

This is the complete pre-rebuild checkpoint for the approved direct catalog
replacement. The protected Git baseline is `f019876`; this checkpoint is
committed separately immediately before any Global-to-Market schema or reader
change. The validated source backup is
`backups/v3.17.2_before_global_market_catalog_rebuild/costerly-app_v3.17.2_before_global_market_catalog_rebuild_2026-10-11.zip`.

The existing V2 contract file,
`db/sql/2026_10_11_catalog_v2_contract_foundation.sql`, is an unapplied
transition artifact. It establishes the approved roles, five production
departments and case-local gap contracts, but it does not yet fully separate
Global identity from a market-purchasable material. It must be revised as part
of this rebuild, not applied as the final target unchanged.

## Protected current production state

The production database was inspected read-only on 2026-10-11. It contains
the following catalog evidence, all of which is retained for classification:

| Evidence | Rows |
| --- | ---: |
| Reference materials | 4,728 |
| Active reference materials | 4,448 |
| Reference aliases | 9,723 |
| Reference operations | 78 |
| Material categories | 158 |
| Israel market material profiles | 280 |
| Israel market offers | 320 |
| Israel modeled material prices | 4,448 |
| Israel price identities | 2,832 |
| Price-identity memberships | 4,565 |
| Company material items / offers | 29 / 13 |
| Company source documents / rows | 4 / 23 |

Active reference materials still use the obsolete mixed `department` column:
Wood 2,657; Metal 672; Glass-Stone-Plastic 415; Hardware 400; Consumable 247;
Coating 41; Packaging 16. There are no market operation models or company
supplier-operation offers yet. The V2 family tables do not exist in production.

Existing untracked owner material remains untouched: `.streamlit/`, `tmp/`,
and `db/sql/3_15_4_israel_global_catalog_v1_parts/`.

## Accepted canonical boundary

The new model has three non-interchangeable layers:

```text
Global Catalog
  universal family, attribute contract, brand, material model, operation
       ↓ market availability and local rules
Market Catalog, first market: Israel (IL)
  listing/variant, local names/aliases, supply format, recipe, price model
       ↓ supplier evidence for one company
Company Price Catalog
  supplier item or operation offer, source provenance, current price and unit
```

`reference_markets` already represents the market layer and remains the market
registry. No Israel-specific table name is introduced. New markets use the same
relations and `market_code`.

A Global material family or material model never carries country availability,
currency, supplier price, VAT, source language, local purchasable format or
labor minutes. A market listing never overwrites Global identity. A company
offer never becomes a Global or Israel catalog record automatically.

The retained rules are:

- exactly five production departments: Wood, Metal, Glass & Plastics, Stone,
  Coating;
- Hardware is a catalog section and entity role, not a production department;
  affinities are retrieval-only;
- Consumables do not persist in Company Price Catalog or preliminary estimate
  selection;
- Packaging is an entity role with no production department;
- operation eligibility belongs to Global material family only, while routes,
  recipes, machinery and time priors are market-specific;
- a catalog gap creates a case-local provisional assumption and a Catalog Gap
  Job, never an automatic Global, Israel or Company catalog write.

## Migration contract

Each old reference material is classified into one of three explicit outcomes:

1. **Mapped**: attach its retained identifier to a Global family, Global
   material model and an Israel market listing, or an appropriate
   non-purchasable role.
2. **Excluded by policy**: retain source evidence but do not create a Company
   catalog candidate, for example ordinary consumables.
3. **Review required**: preserve the old row and evidence, publish no invented
   family, variant, operation or price identity.

Existing aliases, price identities, reference price models, source provenance,
company offers and operation records remain linked through migration mapping.
No destructive deletion or silent defaulting is permitted before reader cutover
and integrity checks pass.

## Implementation sequence after this checkpoint

1. Replace the unapplied V2 transition schema with the Global-Market contract,
   including migration-map and review-state relations.
2. Seed Global vocabulary and the Israel market projection from the approved
   V1 family and operation dictionaries.
3. Backfill all current catalog evidence deterministically and produce a
   review-required report for every unresolved row.
4. Change Material Resolver, Labor Resolver, Estimation publisher, Company
   Price Catalog and Supplier Operations to the new contract in one cutover.
5. Run schema, mapping, resolver, estimate and authenticated browser checks.
   Only then remove obsolete reader paths and legacy constraints.

## First active implementation task

Task 3.17.2.1 is the Global-Market schema reconciliation and migration map. It
does not apply SQL to production, change Price Source behaviour, or delete
legacy data. Its acceptance gate is an executable schema contract proving that
Global identity, Israel market variant and Company offer cannot be confused or
written through one another.
