# Israel Reference Price Readiness

Task: 3.15.2
Generated: 2026-09-28
Input: all 3.15.1 Israel reference-price SQL seed batches
Generator: `tools/israel_reference_readiness.py`

## Summary

- Materials: 280
- Candidate offers: 320
- Eligible normalized offers: 112
- Materials with an eligible price: 103
- Materials blocked or missing: 177
- Comparable baseline groups: 111
- Single-source provisional groups: 110
- Multi-source candidate groups: 1

An eligible offer has the correct market and currency, known VAT treatment, a
positive VAT-exclusive normalized price, a normalized unit, and a non-archived
candidate, reviewed, or active status. Eligibility does not approve or activate
a baseline.

## Material readiness by department

| Department | Eligible | Normalization blocked | Missing evidence | Total |
| --- | ---: | ---: | ---: | ---: |
| coating | 1 | 8 | 0 | 9 |
| consumable | 6 | 35 | 0 | 41 |
| glass_stone_plastic | 8 | 3 | 0 | 11 |
| hardware | 59 | 85 | 0 | 144 |
| metal | 1 | 0 | 0 | 1 |
| packaging | 5 | 5 | 0 | 10 |
| wood | 23 | 41 | 0 | 64 |

## Blocked-offer reasons

- Missing normalized price: 208 offers
- Unknown VAT: 192 offers
- Missing normalized unit: 78 offers

One offer may have more than one blocking reason, so these counts must not be
summed as unique offers.

## Consequence

The deployed evidence is broad but not yet production-ready as an automatic
Estimator fallback. The fastest material improvement is to resolve VAT and
unit normalization for the existing 177 blocked materials before collecting
more low-impact SKUs. Independent-source collection remains necessary for the
highest-impact furniture groups because 110 of 111 comparable groups currently
depend on one source.

## Production normalization checkpoint

Home Center VAT normalization was applied to production on 2026-09-28 from
commit `6ef34f5`. Home Center website terms section 65 confirm that displayed
website prices include VAT and exclude delivery and installation.

Post-application production verification:

- Materials: 280
- Candidate offers: 320
- Offer statuses: 320 candidate, 0 reviewed, 0 active, 0 archived
- Eligible normalized offers: 204
- Materials with an eligible price: 190
- Materials blocked: 90
- Comparable baseline groups: 201
- Single-source provisional groups: 199
- Multi-source candidate groups: 2
- Offers missing normalized price: 116
- Offers with unknown VAT: 100
- Offers missing normalized unit: 49
- Active or candidate market baselines: 0
- Remaining Home Center offers with unknown VAT: 0

The normalization changed candidate evidence only. It did not approve an offer,
create a baseline, or connect Estimation fallback.

## Camisa normalization checkpoint

The Camisa normalization batch was applied and verified in production on
2026-09-28 from commit `4fb5f7b`. Camisa terms establish consumer online sales,
application of Israel's Consumer Protection Law, and no wholesale sales. The
statutory total-price requirement supports VAT-included classification, but the
supplier does not state VAT inclusion directly. The 21 offers therefore retain
legal-inference provenance and confidence capped at 68.

Post-application production verification:

- Materials: 280
- Candidate offers: 320
- Offer statuses: 320 candidate, 0 reviewed, 0 active, 0 archived
- Eligible normalized offers: 225
- Materials with an eligible price: 211
- Materials blocked: 69
- Comparable baseline groups: 222
- Single-source provisional groups: 220
- Multi-source candidate groups: 2
- Offers missing normalized price: 95
- Offers with unknown VAT: 79
- Offers missing normalized unit: 28
- Active or candidate market baselines: 0
- Camisa offers normalized to VAT-exclusive ILS per square metre: 21

The Camisa batch changed candidate evidence only. It did not approve an offer,
create a baseline, or connect Estimation fallback.

## IKEA Israel normalization checkpoint

The IKEA Israel normalization batch was applied and verified in production on
2026-09-28 from commit `87c30c9`. IKEA Israel's own terms directly state that
website prices include VAT when applicable. Eight offers with complete pricing
quantities were normalized. Three decorative mirror offers remain blocked
because mirror thickness is not stated.

Post-application production verification:

- Materials: 280
- Candidate offers: 320
- Offer statuses: 320 candidate, 0 reviewed, 0 active, 0 archived
- Eligible normalized offers: 233
- Materials with an eligible price: 219
- Materials blocked: 61
- Comparable baseline groups: 230
- Single-source provisional groups: 228
- Multi-source candidate groups: 2
- Offers missing normalized price: 87
- Offers with unknown VAT: 71
- Offers missing normalized unit: 28
- Active or candidate market baselines: 0
- IKEA Israel offers normalized: 8
- IKEA Israel mirror offers intentionally still blocked: 3

The IKEA batch changed candidate evidence only. It did not approve an offer,
create a baseline, or connect Estimation fallback.

## Algolan sheet-unit normalization checkpoint

The Algolan sheet-unit batch was applied and verified in production on
2026-09-28 from commit `a777b77`. Twelve offers had known VAT-exclusive prices,
one-sheet package quantities, and canonical unit `sheet`. Missing sheet
dimensions blocked square-metre conversion but did not justify blocking the
direct observed price per sheet. The limitation remains in provenance.

Post-application production verification:

- Materials: 280
- Candidate offers: 320
- Offer statuses: 320 candidate, 0 reviewed, 0 active, 0 archived
- Eligible normalized offers: 245
- Materials with an eligible price: 230
- Materials blocked: 50
- Comparable baseline groups: 242
- Single-source provisional groups: 240
- Multi-source candidate groups: 2
- Offers missing normalized price: 75
- Offers with unknown VAT: 71
- Offers missing normalized unit: 16
- Active or candidate market baselines: 0
- Algolan sheet offers normalized: 12

The Algolan batch changed candidate evidence only. It did not infer a price per
square metre, approve an offer, create a baseline, or connect Estimation
fallback.

## A.R. Sharpening normalization checkpoint

The A.R. Sharpening batch was applied and verified in production on 2026-09-28
from commit `9737a52`. Fourteen connector and adhesive offers had complete pack
or weight quantities. The supplier's online-sale and return terms invoke
Israel's Consumer Protection Law but do not directly state VAT inclusion, so
the normalization retains legal-inference provenance and confidence capped at
60.

Post-application production verification:

- Materials: 280
- Candidate offers: 320
- Offer statuses: 320 candidate, 0 reviewed, 0 active, 0 archived
- Eligible normalized offers: 259
- Materials with an eligible price: 244
- Materials blocked: 36
- Comparable baseline groups: 256
- Single-source provisional groups: 254
- Multi-source candidate groups: 2
- Offers missing normalized price: 61
- Offers with unknown VAT: 57
- Offers missing normalized unit: 16
- Active or candidate market baselines: 0
- A.R. Sharpening offers normalized: 14

The A.R. Sharpening batch changed candidate evidence only. It did not approve
an offer, create a baseline, or connect Estimation fallback.

## Complete calculable catalog checkpoint

A read-only production-backed resolver run now produces 280 candidates for 280
reference materials:

- 244 exact candidates from eligible normalized evidence, including two with
  more than one independent source;
- 30 low-confidence candidates modeled from the material's own observed offer;
- 3 low-confidence green-MDF candidates modeled from observed per-sheet prices
  and an explicit standard-sheet area assumption;
- 1 low-confidence configurable veneer range divided by its documented maximum
  panel area;
- 2 low-confidence department medians for configurable hardboard products.

The fallback hierarchy preserves observed price, package, VAT, unit, and
provenance. Unknown VAT remains represented as a wider range. Configurable
minimums are not treated as exact unit prices. The weakest remaining candidates
have confidence 10, and the complete-catalog median confidence is 55.

This establishes calculability, not activation or market-price verification.
There are still zero rows in `market_material_baselines`, every source offer
remains `candidate`, and Estimation is not connected.

## Reproduction

```bash
.venv/bin/python tools/israel_reference_readiness.py --format markdown
```

The local seed report reproduces the pre-normalization checkpoint. Production
post-normalization counts were verified directly through the service-role data
client and are recorded above.
