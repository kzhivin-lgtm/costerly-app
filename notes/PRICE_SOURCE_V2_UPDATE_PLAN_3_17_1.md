# Price Source V2 update plan, 3.17.1

Status: owner-approved target structure, implementation not started.

## Verified starting point

- The Price Source UI does not ask the user to select a department. Its worker
  passes an empty `department` value, and source-level department guarding is a
  compatibility no-op.
- Stone already exists in the reference-taxonomy and Catalog V2 department
  registry. The executable Price Source classifier does not yet consume that
  registry and has no Stone source-row aliases.
- Hardware is currently inferred from useful source wording but is mapped to
  the Wood catalog section by a static category-to-department map.
- Consumables are deliberately discarded before company catalog persistence.
  That policy is retained.
- The existing Material Jobs projection already stores supplier operation offers
  separately from material offers. Its user-facing name changes to Supplier
  Operations only.

## Protected behaviour

Do not change upload batching, source and supplier identity, issuer/HeadPay
resolution, immutable raw-document evidence, VAT handling, price and unit
Review, supplier-lane merge rules, source deletion or asynchronous refresh.
Consumables remain excluded from both company catalog persistence and estimate
selection. Israel Catalog linkage or curation must never block an otherwise
ready Company Price Catalog offer.

## Target Company Price Catalog

```text
Wood
Metal
Glass & Plastics
Stone
Coating
Hardware
Supplier Operations
```

The first five entries are production departments. Hardware is a separate
catalog section with functional categories, not a production department.
Supplier Operations is the renamed operation-offer projection.

## Delivery sequence

### 1. Taxonomy adapter and source-row contract

Replace the static source-category to catalog-section decisions with a V2
taxonomy adapter. A recognised row yields a role, family, approved attribute
facts and catalog section. The Agent supplies bounded evidence facts, never
catalog IDs. The deterministic adapter resolves those facts against the shared
registry.

Keep legacy `material_type` only as a temporary read/write compatibility field
while old rows and readers migrate. Do not reintroduce a user-selected
department control; remove stale prompt wording that implies one exists.

### 2. Hardware routing

Route durable fittings to the Hardware section, with functional families such
as hinge, drawer slide, handle, foot, lock, lift mechanism and connector.
Remove the static `Hardware -> Wood` mapping. Retain supplier-lane evidence,
SKU safeguards, model/dimension merge boundaries and fractional-piece checks.

Hardware is stored once. Future department affinities support lookup only and
never duplicate the item below Wood, Metal or Glass & Plastics.

### 3. Stone adapter integration

Connect the already-defined Stone families and attributes to Price Source
normalisation. The new adapter must recognise source evidence for natural
stone, engineered quartz, sintered/porcelain slabs, solid surface and terrazzo
without creating a second private Stone dictionary.

An accepted source row creates an active Company Price Catalog offer in Stone.
An absent Israel Catalog link creates no Price Source Review blocker.

### 4. Persistence and merge compatibility

Extend company-material persistence to retain V2 role/family/attribute
resolution alongside the existing source evidence. Preserve existing supplier
lane identity and offer history. Migrate current Wood-mapped Hardware records
to Hardware only through a controlled, idempotent reclassification migration
with fixtures for hinges, drawer slides, handles and exclusions.

No consumable record is introduced. Existing consumable-discard behaviour stays
intact.

### 5. Company Price Catalog and Supplier Operations UI

Replace the four hard-coded catalog sections with the five production sections
plus Hardware. Render a section only when it has active rows. Rename the
Material Jobs expander, loading keys, labels and tests to Supplier Operations.
Keep the existing one-loading-state refresh behaviour and Price/Unit-only
Review boundary.

### 6. Nonblocking Israel Catalog integration

After an offer is active, resolve its V2 family and attributes to the Israel
Catalog when evidence permits. Exact linkage enriches retrieval. Incomplete or
unlinked classification creates a separate Catalog Curation signal for staff;
it neither removes the company offer nor enters the Price Source Review queue.

### 7. Verification and release gate

Unit and migration fixtures must cover:

- automatic classifier routing with no department input;
- Wood, Metal, Glass & Plastics, Stone, Coating and Hardware rendering;
- durable Hardware no longer appearing under Wood;
- consumables remaining absent from persisted company catalog records;
- Supplier Operations preserving external-offer semantics;
- existing supplier, VAT, merge, Review and delete-source regressions.

Acceptance additionally requires an authenticated browser pass: empty catalog,
one active row in each applicable section, Review save and refresh, source
delete, and narrow viewport.
