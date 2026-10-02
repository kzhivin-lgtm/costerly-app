# Material Resolution Core

Task: 3.15.3
Status: active
Started: 2026-09-28
Market: Israel (`IL`)

## Objective

Give Price Source, Estimation, company catalogs, and the reference catalog one
deterministic material-identity resolver. Exact evidence must resolve without a
model. Ambiguous or new identities must remain usable privately while entering
an explicit review buffer rather than polluting the global catalog.

## Starting checkpoint

Task 3.15.2 has 280 active Israel material baselines for 280 reference
materials. The company-first price resolver resolves the active catalog but
production currently has no company material items or company offers. Price
Source does not yet populate `reference_material_id`.

## Implemented candidate

The resolver applies this order:

1. confirmed company alias;
2. exact Israel reference alias;
3. unique compatible hard attributes;
4. a compatibility-filtered shortlist of at most five;
5. `new_identity_or_needs_review`.

Supplier SKU is retained as source provenance only. It cannot resolve, rank, or
disambiguate a material identity, even inside one supplier.

Hard specification conflicts cannot be overridden by phrase similarity. Alias
collisions never select an arbitrary identity. English, Hebrew, Russian,
common unit spellings, multiplication signs, decimal commas, punctuation, and
supplier SKU separators are normalized deterministically.

The prepared transactional migration
`db/sql/2026_09_28_material_resolution_core_v1.sql` adds:

- versioned resolver metadata;
- private confirmed company aliases;
- the identity-candidate review buffer;
- immutable resolution events;
- Price Source reference links and independent identity, conversion, and
  eligibility confidence fields;
- explicit company-offer price scope and included services.

It enables RLS, revokes client access, grants service-role access, and does not
reprocess, auto-link, or publish any company row.

## Production read-only benchmark

The candidate was tested against the deployed 280 materials, 851 aliases, and
320 observed offers:

- 797 of 797 unique exact alias routes selected the correct material;
- three alias keys collide;
- collision false resolutions: zero.

The historical supplier-SKU benchmark is superseded. SKU is no longer an
identity route and must not be used as a current acceptance denominator.

## Next action

Apply the prepared schema migration and verify its tables, RLS, resolver
version, and additive company columns. Then task 3.15.4 can route new and
historical Price Source rows through this core without repeating OCR.
