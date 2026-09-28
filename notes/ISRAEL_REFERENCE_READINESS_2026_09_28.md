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

## Reproduction

```bash
.venv/bin/python tools/israel_reference_readiness.py --format markdown
```
