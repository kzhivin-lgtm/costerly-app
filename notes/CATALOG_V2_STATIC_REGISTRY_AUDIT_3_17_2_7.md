# V2 Static Registry Audit, 3.17.2.7

Status: active implementation record, 2026-10-11.

## Question

Which curated vocabulary still exists only inside Source Agent code rather than
the V2 Global registry?

## Verified inventory

| Registry | Static Source Agent inventory | V2 state before 3.17.2.7 | Disposition |
| --- | ---: | --- | --- |
| Hardware brands | 15 brands, 51 aliases | zero `reference_brands` rows and zero hardware scopes | Seed now, together with Product Systems. Every brand has at least one Hebrew alias |
| Hardware Product Systems | 116 manufacturer lines, 357 aliases | no table | Create Global system and alias relations. Every system has a Hebrew transliteration alias; short ambiguous names remain brand-qualified |
| All curated brands | 73 brands | zero V2 brand rows | The remaining 58 non-Hardware brands are a separate migration slice. They must not be represented as missing V2 data after this Hardware-only seed |
| Material taxonomy families | 47 source families | 46 V2 projections | `laminated panel` has no safe V2 projection. Do not map it to faced MDF or melamine-faced particleboard, because that would invent a substrate. Add a generic laminated-panel family or send it to review in a later approved family expansion |
| Attribute-value vocabulary | 61 deterministic source values | V2 has family attribute contracts, not every allowed literal value | Keep values as structured source evidence for now. A controlled value registry is a later curation task, not a reason to invent model variants |
| Supplier-operation phrase rules | 34 job rules plus 32 forced-operation rules | V2 operation eligibility is seeded independently | Requires a code-by-code audit before any Source Agent operation phrase becomes a canonical operation link |

## 3.17.2.7 boundary

The new Product System relation sits between a scoped brand and a future
material model:

```text
Global brand + hardware family
  -> Product System, for example Blum + drawer slide -> MOVENTO
  -> future staff-approved physical variant
  -> Israel listing / Company supplier offer
```

Raw supplier SKU remains immutable supplier evidence. It is not an alias,
system, model, variant or a source of inferred length, load capacity, finish
or price. A recognised Product System can identify its manufacturer only after
ordinary source wording has independently established the Hardware family.

The 116 seeded systems cover the 15 existing curated Hardware brands. They are
manufacturer product lines, not a claim that every maker SKU or every product
variant has been curated. The seed creates no Global material model, Israel
market listing, Company Price Catalog item, price, supplier offer or SKU
crosswalk.

## Alias coverage invariant added in 3.17.2.7

The active Source Agent vocabulary now has a regression contract: every
material family and every deterministic attribute value carries a Hebrew
recognition alias. The hardware Global registry has the same contract for all
brands and Product Systems, and the SQL seed is tested against the exact
offline Source Agent vocabulary. English canonical names remain display-only.
Aliases are recognition evidence, never a basis for an inferred physical
variant. For example, `מובנטו`, `Moventa` and the OCR variant `Movers` resolve
to Blum MOVENTO only when the line is already established as a drawer slide;
they cannot derive an unstated length or SKU variant.
