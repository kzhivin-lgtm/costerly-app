# Material Resolver Selection Policy, 3.17.2.9

Status: owner-approved implementation policy, 2026-10-12.

## Four derived identity and estimation states

The Price Source indicator is derived from structured identity, the Material
Pricing Key registry and canonical-link evidence. It is not a subjective
confidence score.

| Tone | Condition | Estimation authority |
| --- | --- | --- |
| Green | Pricing Key and required purchase format are complete, and the Company item links to an Israel Reference/Listing | Estimate ready, eligible for normal deterministic selection |
| Yellow | Family is known but one or more Pricing Key or required purchase-format facts are missing | Never an ordinary authoritative price |
| Blue | Pricing Key and required purchase format are complete, but there is no Israel Reference/Listing link | Estimate ready, eligible for normal deterministic selection |
| Red | Family is not established | Never an ordinary authoritative price; requires research/classification |

An active Company offer already has a valid price and estimation unit. Therefore
Blue and Green are the two Estimate Ready states. Yellow and Red evidence
remains visible in Price Source and may support a case-local provisional
estimate only through the separately governed fallback and review-job path.

The canonical link remains valuable for reference fallback and catalog curation,
but its absence must not suppress a usable Company price.

## Deterministic selection

For a material requirement, Resolver considers Blue and Green candidates in
the requested family that satisfy all known compatibility facts. If one
candidate remains, it is selected. If several remain, the future Material
Engine compares total purchasable cost for the required quantity and supply
format, with stable identifiers as the final tie breaker. If no Estimate Ready
Company offer remains, it considers compatible approved Israel pricing. It
never uses a supplier SKU as a cross-supplier match key.

## Low-impact completion policy

`estimation_impact` is a Global Family property. Low impact permits a shorter,
named compatibility link only when an explicit policy authorizes it. It does
not mean every item in that family is interchangeable.

Initial policy: a source family `furniture leg` may link to the canonical
Israel `Adjustable cabinet leg` anchor, including when brand or height vary.
It excludes casters and wheels. The resulting link is green. Drawer slides,
lift systems, frames, table supports, stone, sheet materials and other
variant-sensitive families remain strict.

## Initial sheet-family canonicalisation policy

This policy is shared by Source ingestion, Material Resolver and Estimation
material resolution. It changes neither supplier evidence nor the number of
Company Price Catalog offers.

- `Plywood`: ordinary plywood, Twin, Combi and Okoume remain distinct Company
  offers, but resolve to the same `raw plywood` Israel class at the same
  thickness. An explicit perforation, veneer, HPL/Formica or other facing is
  not downgraded to raw plywood.
- `MDF`: raw MDF resolves only to raw MDF at the same thickness. White, decor,
  melamine and ordinary laminated MDF resolve to the standard faced class at
  the same thickness; decor or colour does not create another estimation class.
  HPL/Formica and veneered MDF are separate price-bearing classes.
- A class without an authoritative Israel Reference/Listing remains blue. The
  policy never creates a green link by using a neighbouring thickness or a
  different construction class.

### Baseline-class completeness

The Israel catalog must contain each ordinary class required by this policy.
`db/sql/2026_10_12_sheet_material_baseline_reference_classes.sql` supplies
the missing raw-plywood and standard raw/faced MDF thicknesses. It deliberately
does not create prices or infer a special class. A source row becomes green
only when it has the correctly matched same-thickness reference class.

For display, `Twin`, `Combi` and `Okoume` are one supplier-evidence attribute,
not brands. They must render once, for example `Plywood 17 mm, Twin`, while
remaining distinct supplier offers where their source pricing differs.

## Pricing Key registry

`public.reference_material_family_pricing_policies` is the authoritative
registry. It contains exactly one active policy per active Material Family:

- `pricing_key_attribute_codes`: the minimum price-bearing facts;
- `purchase_format_policy`: `not_required`, `required`, or approved
  `standard_sheet_2400x1220`;
- `default_purchasable_dimensions`: only for the explicit standard-sheet
  policy.

The standard sheet default is currently limited to the approved wood-panel
families. It never applies to stone, glass, metal, HPL or plastics. A future
Company offer retains its source evidence and separately records whether a
format was explicit or derived by this policy.

## Current implementation boundary

The registry migration is applied to production. The Price Source runtime still
uses its prior local endpoint table and still blocks Blue candidates. The next
implementation stage replaces that duplicate completion logic, adds
offer-level supply format and makes the derived Blue/Green Estimate Ready rule
effective in the runtime and UI.
