# Price Lists rebuild, 3.16.7

Status: active. Stage 1 is the additive data contract. It does not change the
current Price Lists UI or automatically modify any existing source.

## Decision

`reference_operations` is the single global catalog of normalised work. It is
already used by the manufacturing and labor foundations. Price Lists must not
create a parallel work catalog.

A supplier service is distinct from a material:

```text
source row -> reference operation -> company supplier operation offer
source row -> company material item -> company material offer
```

The first path is for subcontract work. The second is for purchasable material.
No source row may follow both paths unless a future approved split creates
separate source rows with separate evidence.

## Stage-1 storage contract

- `company_price_sources.source_supplier_name` retains the exact spelling found
  in the evidence. `supplier_id` is the selected canonical supplier.
- `company_supplier_aliases` records source-observed and manually confirmed
  company-private supplier aliases. It enables a later reversible supplier
  merge without overwriting source evidence.
- `company_price_source_rows.row_kind` separates `material`,
  `operation_service`, and `non_catalog` rows. Existing rows retain the
  additive default `material`; no historical row is reclassified in this stage.
- `reference_operation_id` connects an operation-service row to the existing
  global catalog.
- `company_supplier_operation_offers` is a versioned, company-private price
  observation for that operation and supplier. It points to the exact source
  and source row, preserves VAT and currency, and cannot be a material offer.

## Bundles and units

`supplier_cut_and_edge_banding` is a normalised supplier bundle. It is not a
claim that a supplier price can be decomposed into independent cutting and edge
banding prices.

`pricing_basis = supplier_defined` is required when an invoice gives a price
and quantity but does not prove a physical billing unit. It must never be
displayed or calculated as `piece`, `m`, `m2`, `sheet`, or `hour`. The
`supplier_service_unit_count` driver records the observed count only.

## Protected behaviour

- Existing material source rows and offers remain untouched.
- Current Estimation object-facts and Labor Engine contracts do not receive the
  new supplier bundle in this stage.
- No operation price is automatically attached to a material price.
- No historic service row is promoted into the new table without a reviewed
  classifier in a later stage.

## Stage-1 acceptance criteria

1. Migration is additive and transaction-wrapped.
2. Service offers reference a shared `reference_operation`, supplier, source,
   and source row, and cannot be stored in material-offer tables.
3. Exact supplier spelling can be retained separately from canonical supplier
   identity.
4. The bundled `supplier_cut_and_edge_banding` operation can preserve a
   supplier-defined billing unit without false conversion.
5. RLS protects the two new company-private tables.

## Next stage

Stage 2 changes the Price Source application layer: classify rows, persist
service offers, exclude consumables completely, resolve VAT and currency under
the accepted policies, and keep ambiguous calculation units in review.
