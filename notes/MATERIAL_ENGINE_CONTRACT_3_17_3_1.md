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
not permission to invent a dimension. The field is additive while legacy facts
remain readable, and the page-agent version invalidates its own old cache.

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
7. Preserve allocations from each purchase unit back to every demand. V1 does
   not assign offcuts to a later estimate.

## Explicit boundary

The current Estimation V2 facts provide family, quantity and unit, but do not
yet carry per-part rectangles. Therefore this first Engine task is pure and is
not wired into the live publisher. Connecting it requires a later agent-output
contract addition for calculation-local part geometry, followed by a read-only
shadow comparison. The existing Resolver's legacy per-unit winner is not used
by this Engine contract and will be replaced at the integration task.
