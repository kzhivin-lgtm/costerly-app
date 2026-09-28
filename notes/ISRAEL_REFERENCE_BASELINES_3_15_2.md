# Israel Reference Baselines and Furniture-Core Completion

Task: 3.15.2
Status: active
Started: 2026-09-28
Market: Israel (`IL`, `ILS`)

## Objective

Turn the deployed Israel reference evidence into a production-ready material
fallback for deterministic furniture estimation. The task closes the
high-impact furniture-core gaps, expands fast material recognition, derives
auditable low, typical, and high prices, and validates the result on
representative furniture scenarios.

This task does not rebuild the Estimation Agent. It prepares the verified
material identities and prices that Estimation v2 will consume later.

## Starting checkpoint

Task 3.15.1 is complete at commit `1f8d6ab`. Production contains:

- 1 Israel reference market;
- 99 reference sources;
- 113 material categories;
- 280 reference materials and 280 Israel market profiles;
- 320 candidate market offers;
- 851 material aliases;
- 0 active market baselines.

Production alias lookup is verified for an exact technical code and an exact
Hebrew market name. The complete local test suite passed with 599 tests. Failed
SQL attempts were transactional and left no partial production state.

## Protected behavior and data

- Preserve every source, material, market profile, offer, alias, and provenance
  record from 3.15.1.
- Company prices remain the first pricing authority.
- Israel reference prices are fallback data only.
- Never mix incompatible units, dimensions, grades, VAT modes, price scopes,
  included services, or fabricated and raw-material offers.
- Candidate evidence is not an active fallback price.
- Unsupported material identity or price scope returns `needs_review`.
- The five-level reserve setting is applied after base-cost calculation. It is
  not stored as five different market prices.
- Preserve the accepted CNC and Sheet Laser routing and costing checkpoint.
- Preserve untracked `.streamlit/` and `tmp/` and keep them out of commits.

## Current evidence quality

- All 280 reference materials have at least one candidate offer.
- 245 materials have one offer, 31 have two, three have three, and one has four.
- Most identities currently have three fast aliases: canonical English name,
  stable technical code, and Israel market name. Supplier and common-language
  synonym coverage is still narrow.
- The 72-group furniture-core matrix has evidence in 71 groups, but only 12
  groups are representative enough to be marked covered. Evidence breadth is
  not baseline readiness.

## Delivery sequence

1. Generate one reproducible, impact-weighted readiness report from deployed
   seed data.
2. Normalize comparable prices to their canonical unit and VAT-exclusive base.
3. Classify every material as baseline-ready, provisionally usable,
   normalization-blocked, identity-blocked, or evidence-gap.
4. Define and test robust low, typical, and high derivation for single-source
   and multi-source evidence without activating it.
5. Close the highest-impact furniture-core gaps and add independent sources
   where they materially improve estimates.
6. Expand deterministic aliases and parameter parsing for common English,
   Hebrew, Russian, supplier, thickness, dimension, and unit variants.
7. Validate kitchen, wardrobe, cabinet, table, upholstered, glass, metal-frame,
   and mixed-material scenarios.
8. Present the candidate baselines, coverage, uncertainty, and rejection cases
   for explicit approval.
9. After approval, activate versioned baselines and connect the deterministic
   company-first price resolver.

## Baseline rules to implement and verify

- Comparable evidence must share market, exact material identity, compatible
  canonical unit, price scope, VAT basis, and service boundary.
- A multi-source baseline uses robust central tendency and bounded dispersion,
  not unfiltered minimum and maximum values.
- A valid single-source baseline remains provisional, carries lower confidence,
  and uses an explicit uncertainty policy rather than pretending to describe a
  market distribution.
- Retail, trade, quote, invoice, and public catalog observations retain their
  channels and weights.
- Source freshness, package quantity, minimum order, delivery, and included
  processing remain visible.
- No missing VAT or unit conversion is guessed silently.

## Verification

- Schema and seed validation tests.
- Reproducible readiness and coverage report.
- Unit tests for normalization, comparability, aggregation, confidence, and
  rejection paths.
- Idempotent migration test on a clean database before production.
- Scenario fixtures for representative furniture estimates.
- Production count, resolver, permission, and fallback checks after deployment.

## Decision gates

Explicit owner approval is required before:

1. activating the first market baseline;
2. widening automatic identity linking beyond verified exact routes;
3. using anonymized private company observations for global market learning;
4. connecting the catalog as an automatic Estimation fallback.

## Next action

The reproducible readiness report is implemented and recorded in
`notes/ISRAEL_REFERENCE_READINESS_2026_09_28.md`. Next, resolve the existing
VAT and unit-normalization blockers by furniture-estimate impact, then derive
non-active candidate baselines. Do not activate or deploy a market baseline
until the report and methodology are reviewed.

The first evidence-bounded normalization batch is prepared in
`db/sql/2026_09_28_israel_reference_home_center_vat_normalization.sql`. Home
Center website terms section 65 confirms that all displayed website prices
include VAT and exclude delivery and installation. The migration can normalize
92 candidate offers and does not review or activate them.

The Home Center batch was applied and verified in production on 2026-09-28.
Eligible materials increased from 103 to 190, while blocked materials decreased
from 177 to 90. All 320 offers remain candidates and the baseline table remains
empty. Continue with Camisa and Abo Srya VAT and unit evidence, then derive
non-active candidates under the approved calculable-catalog policy.

Camisa is the next isolated normalization batch. Its consumer terms make online
sales subject to Israel's Consumer Protection Law and explicitly prohibit
wholesale sales. The statutory total-price rule requires consumer-facing prices
to include VAT. Because Camisa does not repeat that VAT statement on its product
pages, this is recorded as a legal inference with capped confidence, not as
direct supplier evidence. The prepared migration normalizes 21 sheet offers to
VAT-exclusive ILS per square metre and does not activate any fallback.

The Camisa batch was applied and verified in production on 2026-09-28 from
commit `4fb5f7b`. All 21 Camisa offers are normalized to VAT-exclusive ILS per
square metre with legal-inference provenance and confidence capped at 68.
Production now has 225 eligible offers covering 211 of 280 materials, 69
materials remain blocked, and 222 comparable candidate groups exist. All 320
offers remain candidates and the baseline table remains empty.

Next, audit the 69 blocked materials by source and furniture impact. Normalize
Abo Srya only if its VAT basis can be established or explicitly modeled with a
lower-confidence policy. Then derive non-active low, typical, and high baseline
candidates for owner review.

## Candidate derivation checkpoint

The deterministic review-only derivation is implemented without writing a
baseline to production. It groups evidence only when market, material, unit,
currency, scope, and region match. Duplicate observations from one source are
collapsed to one source median.

For one source, the observed normalized price is `typical`. The candidate range
uses the evidence confidence, bounded between plus or minus 15% and 40%, and
candidate confidence is capped at 55. For multiple sources, `typical` is the
median of one price per source. The observed range is capped at 40% below and
60% above `typical`, and confidence increases with independent-source count but
is capped at 85. These are uncertainty calculations, not a user setting. The
CNC and Sheet Laser reserve slider remains unrelated to material prices.

A read-only production run derives 222 candidates from current evidence: 220
single-source provisional candidates and two multi-source candidates. Candidate
confidence currently ranges from 55 to 65. No candidate has been inserted or
activated, and Estimation fallback remains disconnected.

IKEA Israel is the next evidence-bounded normalization batch. Its own terms
directly state that website prices include VAT when applicable. Eight offers
have a complete price quantity and can be normalized. Three mirror offers stay
blocked because mirror thickness is not stated. The identity blocker is not
overridden by resolving VAT.

The IKEA Israel batch was applied and verified in production on 2026-09-28
from commit `87c30c9`. Eight candidate offers were normalized. The three mirror
offers remain blocked as designed. Production now has 233 eligible offers
covering 219 of 280 materials, 61 materials remain blocked, and 230 review-only
baseline candidates can be derived. All 320 offers remain candidates and the
baseline table remains empty.

The next blocker audit found a normalization defect in 12 Algolan offers. Their
canonical unit is `sheet`, source unit is a single sheet, and VAT is already
excluded. Unknown sheet dimensions prevent conversion to square metres, but do
not prevent preserving an observed price per sheet. A bounded migration is
prepared to normalize only to `sheet`, with the area-conversion limitation kept
in provenance.

The Algolan batch was applied and verified in production on 2026-09-28 from
commit `a777b77`. All 12 observed sheet prices are now normalized to the
canonical `sheet` unit. Production now has 245 eligible offers covering 230 of
280 materials, 50 materials remain blocked, and 242 review-only baseline
candidates can be derived. All 320 offers remain candidates and the baseline
table remains empty.

A.R. Sharpening is the next isolated batch. Fourteen offers have complete pack
or weight quantities. The supplier's online-sale and return terms invoke
Israel's Consumer Protection Law, but do not directly state VAT inclusion.
Normalization therefore uses legal-inference provenance and caps confidence at
60. No identity, quantity, or source-scope assumption is added.

The A.R. Sharpening batch was applied and verified in production on 2026-09-28
from commit `9737a52`. All 14 pack or weight prices are normalized with
legal-inference provenance and confidence capped at 60. Production now has 259
eligible offers covering 244 of 280 materials, 36 materials remain blocked,
and 256 review-only baseline candidates can be derived. All 320 offers remain
candidates and the baseline table remains empty.

## Complete-catalog candidate checkpoint

The review-only resolver now returns one calculable candidate for all 280
reference materials without changing the underlying evidence or writing to the
baseline table. The production-backed distribution is:

- 242 exact single-source candidates;
- 2 exact multi-source candidates;
- 30 candidates modeled from their own observed offer;
- 3 candidates modeled from a per-sheet offer with an explicit sheet-area
  assumption;
- 1 configurable-range candidate;
- 2 department-median candidates.

The three green moisture-resistant MDF candidates retain Algolan's observed
VAT-exclusive per-sheet prices. Algolan's own page states that pricing is by
sheet, cutting is included, and VAT is excluded, but does not state sheet
dimensions. Their square-metre candidates therefore use an explicit 2440 x
1220 mm typical-sheet assumption, preserve a wider 2800 x 2070 mm alternative
in the low bound, and carry confidence 15 rather than pretending that the
dimensions were observed.

Complete-catalog confidence ranges from 10 to 65, with a median of 55. The 36
modeled candidates are deliberately distinguishable from the 244 candidates
backed by normalized evidence. No baseline row has been inserted or activated,
and Estimation remains disconnected. Owner review is the next gate before any
production baseline write.
