# Material Engine contract, 3.17.3.1

Status: implementation contract, 2026-10-13.

## Purpose

The Material Engine converts already-resolved physical demands into one
estimate-wide purchase plan. It contains no OCR, visual interpretation,
family classification, supplier-SKU matching or labor-route choice.

## Inputs

`MaterialDemand` is calculation-local, not a Global catalog entity. It holds:

- estimate object and optional part identity;
- resolved material family and resolver-produced `selection_key`;
- required quantity and unit;
- compatible candidate IDs;
- for cut materials, part length, width and rotation permission.

The page Facts Agent now emits these rectangles as `parts`: `part_id`, linked
`material_requirement_id`, total part quantity for the target object, cut
length and width in mm, and `rotation_allowed`. Evidence references are added
by the server. A part is omitted when geometry is genuinely uncertain; this is
not permission to invent a dimension. The field is additive, and the
page-agent version invalidates its own old cache.

An exact measurement present in the bounded evidence always wins over an
envelope proxy. A proxy can exist only as an explicit review-visible assumption
when no exact measurement exists. In particular, Estimation must not turn an
object envelope into fabricated cut rectangles, dimensions, quantities or a
physical subtype. The Engine may pack supplied supported parts, but does not
validate or repair document interpretation.

`MaterialSupplyCandidate` is produced only after Material Resolver has checked
family compatibility and Estimate Ready status. It holds the exact purchasable
unit, ex-VAT price per purchasable unit, purchase format or package size, kerf,
and Company or Israel-reference authority.

## Deterministic policy

1. Group all compatible demands in the entire estimate by `selection_key`.
2. Evaluate each common candidate as a complete purchase basket.
3. For sheets, nest rectangular parts across all objects before rounding to
   whole sheets. V1 uses a deterministic largest-first guillotine placement
   with explicit kerf clearance. It never substitutes a percentage waste rate.
4. For linear stock, pack cuts across the estimate into stock lengths before
   rounding to whole bars.
5. For piece packages, aggregate pieces before package rounding. For direct
   area, mass or liquid purchases, preserve a fractional quantity where that
   is the candidate's purchase basis.
6. Prefer a complete Company basket whenever one exists. Only where none can
   physically supply the group may an Israel-reference candidate be considered.
   Within that authority lane, select the lowest complete basket cost. Candidate
   ID is the final stable tie breaker. A candidate that cannot physically supply
   every demand is not eligible.
7. The target Engine boundary is: if neither Company nor Israel Reference can
   provide a complete candidate, return a structured `assumption_required`
   outcome. It must not price an invented material or write a catalog.

`Assumption Fallback` is the following Estimate-orchestration service, not an
Estimation Agent or Material Engine responsibility. It turns that outcome into
an estimate-local assumption with reason, research sources and calculation
impact, keeps the estimate `review required`, and creates or updates its
deduplicated Catalog Gap Ticket. The existing Catalog V2 contract persists
this through `estimate_case_assumptions`, `catalog_gap_jobs` and occurrence
records.
7. Preserve allocations from each purchase unit back to every demand. V1 does
   not assign offcuts to a later estimate.

8. A candidate must also be physically subtype-compatible with the evidence.
   A generic `hardware_door_system` candidate that describes a folding door is
   not eligible for an evidenced sliding-door or track system.

## Explicit boundary

The Estimation V2 facts now carry calculation-local per-part rectangles. The
Engine receives a document-wide read-only plan while project-level purchase
plan persistence and rendering are connected. This stage does not compare its
output to any prior estimator. It establishes the Engine's own deterministic
Company, Israel Reference, then Assumption Fallback boundary.

## Publication while review remains required

A persisted plan may have both resolved and unresolved demands. In that case
the plan remains `needs_review`, Final Approval remains blocked, and Object
Detail publishes only the resolved allocations with their selected canonical
names and allocated cost. Unresolved requirements stay visible without a
price. This is not a fallback price and does not make the partial plan
approved.

## Resolver outcomes and strict defaults, 2026-10-15

After a material requirement is recognised, the persisted plan has exactly
three outcomes: Company Catalog allocation, Israel Reference allocation, or
`Assumption Fallback`. The fallback carries the requirement's source name,
Family, specification, net quantity, unit and reason. It has no invented
price, is visible in Object Detail as `Assumption: <source name>`, and keeps
the estimate review-required.

A Family Default completes only a recognised Family or explicitly declared
subtype when no additional Pricing Key fact is evidenced. It selects one
approved concrete position. It must not change a provided thickness, section,
metal type, species, depth, or other Pricing Key fact. Thus a `metal tube
20x20` is exact Resolver work: resolve that key or produce Assumption Fallback,
never a default round tube.

## Canonical Pricing Key values, 2026-10-15

Pricing Key aliases are deterministic catalog vocabulary. They are not a
default and do not supply a missing fact. Once Estimation V3 has selected a
Family and extracted an evidenced value, the system canonicalizes only an
exact active value alias before Material Resolver builds its selection key.
Price Source and Estimation therefore use the same stored aliases.

For ordinary construction steel, the sole canonical `metal_type` is `steel`.
`carbon steel`, `mild steel`, `regular steel`, `standard steel` and their
approved Russian and Hebrew forms are aliases for `steel`. Stainless steel and
aluminium remain separate canonical values. A supplied `metal_type=steel` and
`section_profile=square_tube_20x20` must resolve by that complete key or
produce Assumption Fallback. It must never activate a Family Default.

## Alias safety audit, 2026-10-15

An active Pricing Key value alias may target only a canonical value that exists
in the same active Family. It must not convert a broad term such as `round
tube`, `oak`, or `powder coating` into a non-existent pseudo-position. Where
the wording lacks a concrete purchasable subtype, Resolver preserves that
incompleteness for a Family Default decision or Assumption Fallback under the
strict-default rule above.

All active Family aliases have English, Russian and Hebrew coverage. A phrase
that can honestly identify more than one Family remains in the explicit
ambiguous-alias registry and cannot select a Family by insertion order.
