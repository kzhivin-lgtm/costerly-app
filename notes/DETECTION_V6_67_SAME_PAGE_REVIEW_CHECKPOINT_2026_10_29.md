# Detection V6.67 same-page Review checkpoint, 2026-10-29

## Scope

V6.67 restores the accepted V6.63 baseline and changes one behaviour only:
after Discovery fixes retained `object_evidence` Islands, Membership Review is
given every unordered within-page pair and must inspect identifier, topology,
geometry, dimensions and construction before deciding membership. The queue is
comparison work, never merge evidence, and it creates no cross-page all-to-all
work.

## Verified implementation

- Commit: `47826f7` (`feat(detection-v6.67): require same-page full-criteria review`)
- Protected base: V6.63. V6.64-V6.66 Fusion, bbox, halo, scoring and routing
  experiments are excluded.
- `finalize_detection_same_page_membership_queue()` builds the exact queue only
  after Discovery, from retained same-page `object_evidence` groups.
- The Review contract requires all five criteria for every queue row.
- Candidate Q continues to bound cross-page Dimension revalidation.

## Focused verification

- Focused relevant suite: 164 passed, 1 deselected.
- One unrelated baseline failure was reproduced unchanged on clean V6.63:
  `test_visual_registry_materializes_view_package_from_immutable_source_fact`.
- Live Floor 06 run created 125 required same-page pairs from 54 post-Discovery
  Object Evidence groups. The final run contained 49 retained View packages
  and 15 proof components, compared with 51 components on the direct V6.63
  Floor 06 control.

## Boundary of this checkpoint

The same-page queue is verified. It does not accept Floor 06 end-to-end quality:
P09, P10, P11 and P14 expose a separate classification defect. Technical views
were labelled `floor_plan` and discarded by the legacy representation-kind gate
despite an `object_evidence` classification. V6.68 is the isolated repair.
