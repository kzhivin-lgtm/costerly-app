# Material Resolver Selection Policy, 3.17.2.9

Status: owner-approved implementation policy, 2026-10-12.

## Four derived identity states

The Price Source indicator is derived from structured identity and canonical
link evidence. It is not a subjective confidence score.

| Tone | Condition | Estimation authority |
| --- | --- | --- |
| Green | Family and all family completion facts are known, and the Company item links to an Israel Reference/Listing | Eligible for normal deterministic selection |
| Yellow | Family is known but one or more family completion facts are missing | Never an ordinary authoritative price |
| Blue | Family and completion facts are known, but there is no Israel Reference/Listing link | Never an ordinary authoritative price; requires staff catalog linking or curation |
| Red | Family is not established | Never an ordinary authoritative price; requires research/classification |

Yellow, blue and red evidence remains visible in Price Source. It may support a
case-local provisional estimate only through the separately governed fallback
and review-job path. It cannot silently win ordinary price resolution.

## Deterministic selection

For a material requirement, Resolver considers only green candidates in the
requested family that satisfy all known compatibility facts. If one candidate
remains, it is selected. If several remain, it selects the lowest normalized
ex-VAT compatible company offer, with stable identifiers as the final tie
breaker. If no green company offer remains, it considers compatible approved
Israel pricing. It never uses a supplier SKU as a cross-supplier match key.

## Low-impact completion policy

`estimation_impact` is a Global Family property. Low impact permits a shorter,
named compatibility link only when an explicit policy authorizes it. It does
not mean every item in that family is interchangeable.

Initial policy: a source family `furniture leg` may link to the canonical
Israel `Adjustable cabinet leg` anchor, including when brand or height vary.
It excludes casters and wheels. The resulting link is green and eligible for
normal selection. Drawer slides, lift systems, frames, table supports, stone,
sheet materials and other variant-sensitive families remain strict.

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

## Current implementation boundary

The first low-impact rule is code-registered and has resolver coverage. It
must move to the future staff-managed compatibility-policy registry before
additional rules are introduced. The `estimation_impact` migration exists but
has not yet been applied to production. A blue catalog state is visible and
blocked from ordinary selection; its future staff Inbox workflow remains under
the approved Catalog Gap and Staff Admin work.
