# Estimation v2 material-resolution checkpoint, 2026-09-30

Task: 3.15.8 Estimation v2 replacement

Status: checkpoint, ready to begin the Detection handoff contract. No runtime,
database, UI, production, commit or push action was performed for this slice.

## Verified scope

`use_cases/estimate_material_resolution.py` now provides a pure coordinator
for one extracted material requirement. It receives already extracted facts and
preloaded catalog rows. It never reads an original file, calls OCR, calls an
LLM, writes the database, or sends a supplier SKU into an identity resolver.

The resolution order is bounded:

1. one exact normalized compatible Company Material with at least one usable
   active offer resolves through the company route;
2. no company material match uses the existing pure Israel
   `resolve_material_pricing_identity` resolver and exactly one active model;
3. an ambiguous company material, ambiguous Israel model, missing usable price,
   or incompatible facts returns review rather than guessing or silently
   falling back.

`company_material_items.category` is deliberately not used as a material-family
filter. It is company taxonomy, while extracted material family has different
semantics. Exact normalized company name plus explicit structured hard-fact
compatibility is the current MVP rule.

The coordinator returns links and Israel model price range. Company offers are
linked but their price aggregation remains part of the next deterministic
composition slice, where VAT and price selection policy can be applied once.

## Protected decisions

- Israel is the only Estimation v2 market runtime. The global physical catalog
  is not traversed by this coordinator.
- Company material is considered before Israel fallback.
- SKU, supplier index, decor and marketing labels are provenance only. They do
  not select, rank or disambiguate a material or price.
- An ambiguous Company Material never bypasses Company pricing to select an
  Israel price silently.
- Existing Price Source persistence orchestration remains separate. The shared
  pure price-identity resolver is reused below both workflows.

## Evidence

New fixtures in `tests/test_estimate_material_resolution.py` cover:

- E13, unique compatible Company Material with a usable active offer wins;
- E14, absent Company Material uses one active Israel price model;
- E15, ambiguous Company Material returns review without fallback;
- E16, a supplier SKU alone cannot match a Company Material.

The relevant test command completed successfully on 2026-09-30:

```text
.venv/bin/python -m pytest -p no:cacheprovider \
  tests/test_estimate_material_resolution.py \
  tests/test_material_identity_resolution.py \
  tests/test_material_pricing_identity_resolution.py \
  tests/test_price_source_material_resolution.py -q

38 passed in 0.10s
```

`git diff --check` also passed.

## Preserved dirty state

This checkpoint does not absorb or remove the existing unrelated work,
including `.streamlit/`, `tmp/`,
`db/sql/3_15_4_israel_global_catalog_v1_parts/`, Labor work, Price Source work,
and their documentation. All remain uncommitted.

## Next task

Define the smallest additive Detection vNext persistence and handoff contract
for `estimation_input_v2`: one prior OCR result reference, approved object and
quantity, object evidence page or block references, source-region preview
reference, and immutable version snapshot. The owner selected evidence-only
retention: use private Storage for bounded source-derived evidence artifacts,
not the original source file. Do not implement a second OCR pass or replace
Detection's object taxonomy.
