# SKU Information-Only Checkpoint

Date: 02.10.2026

Task lineage: 3.15.3 Material Resolution Core and 3.15.4 Price Source Material
Resolution.

## Decision

Supplier SKU is an informational source field and provenance only. It is not
evidence of material identity or price identity because different suppliers may
assign unrelated SKUs to equivalent products, and one supplier code cannot be
generalized outside that source.

SKU therefore cannot:

- resolve or disambiguate a reference material;
- rank candidates or create a shortlist;
- trigger or suppress review;
- override names, aliases, categories, or hard technical attributes;
- select a pricing identity or choose a price.

SKU remains stored with the original source row and offer for inspection and
audit. Existing use inside recurring-source revision correlation remains a
transport and provenance concern only. It does not enter the Material Identity
Resolver. Changing revision correlation is outside this checkpoint and requires
a separate product and migration decision.

## Implemented boundary

- Removed supplier name, supplier SKU, and market offers from the shared
  resolver input contract.
- Removed the exact supplier-SKU resolution route.
- Removed the market-offer query previously loaded only for that route.
- Kept confirmed company aliases, exact Israel aliases, compatible hard
  attributes, and a maximum-five compatible shortlist as the identity routes.
- Added regression coverage proving an SKU cannot resolve an identity by itself
  and cannot override material evidence.
- Removed the obsolete supplier-SKU acceptance benchmark.
- Updated the Israel routing, Material Resolution Core, Price Source integration,
  and central architecture records.

## Protected behavior

- Company aliases and Israel aliases continue to resolve compatible identities.
- Hard technical conflicts continue to exclude candidates.
- Price Source still persists the supplier's original SKU as source evidence.
- Existing source revision handling is unchanged.
- No catalog rows, prices, aliases, SQL schema, or production data are modified.
- No Estimation, Labor, UI, CSS, or navigation behavior is part of this change.

## Verification

- Focused Material Resolver, Price Source integration, and Estimation integration
  suite: 40 passed.
- Full repository suite: 837 passed, 25 pre-existing deprecation warnings.
- Static call-site inspection confirms Price Source and Estimation no longer pass
  SKU or market offers into `resolve_material_identity()`.
- `git diff --check` passed for the checkpoint files.
- Production behavior was not exercised in this documentation checkpoint. The
  change requires no database migration and writes no production data.

## Repository isolation

The checkpoint commit includes only the SKU identity-boundary implementation,
its tests, verifier, and documentation. Existing unrelated UI, CSS, transition,
runtime-observability, TODO, SQL catalog, `.streamlit`, and `tmp` work remains
uncommitted and must not be discarded.
