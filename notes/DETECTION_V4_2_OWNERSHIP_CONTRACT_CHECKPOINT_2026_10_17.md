# Detection V4.2 exclusive visual-group ownership checkpoint, 2026-10-17

## Status

Owner-authorized contract checkpoint at `8c2c37c`. It protects a verified
Registry invariant and its timing result. It is not an acceptance of complete
Page 23 boundary-quality stability.

## Change protected by this checkpoint

- A `visual_group_id` assigned as object-specific boundary support has exactly
  one commercial-object owner.
- A physical source page remains freely shareable as evidence. `page_coverage`
  may list every relevant object on that page.
- A shared schedule, title block, layout, or other multi-object context is an
  unassigned navigation group and remains page-level evidence for all relevant
  objects.
- Duplicate visual-group ownership rejects the Registry before any RFQ or
  Estimation handoff is persisted. The failed usage event retains the raw
  Registry decision and deterministic owner-conflict details.
- The repair adds no model request and does not merge, split, rename, recount,
  or limit an object's evidence pages.

## Production result: Page 23

Five runs after deployment, all Haiku default, returned the expected three
commercial objects. Registry duration was 11.424-14.972 seconds, average
13.170 seconds. The preceding H1 sample averaged 13.891 seconds. Full
processing averaged 24.880 seconds after deployment versus 25.566 seconds in
the preceding sample, so the contract does not show a timing regression.

The successful runs consistently separated the shelving unit, the shared-track
door system, and the horizontal TV-console assembly. Four of five assigned both
alternate console views to the console. In one run, the model assigned an
alternate console view to shelving instead. This is semantic mis-ownership, not
duplicate ownership: the new invariant correctly permits neither sharing nor
silent persistence of one group under two objects, but it cannot by itself
prove the selected owner is semantically correct.

## Acceptance boundary

The contract is accepted as a rollback and data-integrity checkpoint. The
remaining Page 23 issue is a boundary-quality gate because it can degrade
object-specific evidence on multi-page files even when object count is correct.
It is not a reason to undo exclusive ownership or to reduce shared page
evidence.
