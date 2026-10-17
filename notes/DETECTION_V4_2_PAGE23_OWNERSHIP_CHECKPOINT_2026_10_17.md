# Detection V4.2 Page 23 ownership checkpoint, 2026-10-17

## Status

Protected owner-authorized checkpoint before the next Registry-contract repair.
It preserves `e56f347`; it is not an acceptance of Page 23 boundary stability.

## Protected behaviour

- V4 remains the Detection version. V4.2 is the deterministic model router,
  not a second boundary agent.
- Haiku H1 cross-view correspondence remains active only for the Haiku Visual
  Registry prompt. It has no effect on the Sonnet Adda route.
- A physical page can be evidence for multiple objects. `page_coverage` is
  the sole source of Estimation evidence-page membership.
- A one-page coverage omission is reconciled only for an already-declared
  Registry object and is recorded in usage diagnostics.
- Every successful or structured-validation-failed Visual Registry usage event
  preserves the model's `registry_decision_audit`, including visual groups,
  boundary basis, quantity decision and page coverage. This is an inspectable
  decision record, not private chain-of-thought.

## Production evidence after H1

All times are Israel time on 2026-10-17. The H1 prompt version is
`detection_v4_2_visual_registry_haiku_correspondence_experiment_v1`.

| Runs | Expected 3-object count | Result | Observed boundary behaviour |
|---|---:|---|---|
| 12:17-12:19, 4 runs | 4/4 | passed count | TV-console alternate views were always one object |
| 12:29-12:34, 5 runs | 4/5 | one failed count | the failed run produced four objects by duplicating a door-leaf group |
| Total, 9 runs | 8/9 | insufficient for acceptance | TV-console merge held 9/9, but Registry ownership was internally inconsistent in two audits |

The four-object audit used `group-003` both for the complete shared-track door
system and for a separate two-leaf quote line. The 12:29 coverage already
included page 1 for every declared object. Therefore neither the one-page
coverage reconciliation nor failed-audit persistence caused or repaired this
boundary error.

## Diagnosed contract gap

`page_coverage` legitimately allows a physical page to support several
objects. The pre-change Registry contract also permits the same
`visual_group_id` to support several commercial objects. That conflates shared
source context with ownership of an object-specific visual representation.
It lets a component group become both evidence for a complete assembly and a
separate quote line.

## Approved next repair

Make `visual_group_ids` exclusive boundary support: one group has at most one
commercial-object owner. A schedule, title block, shared page, layout or other
contextual source remains shareable through `page_coverage`; it need not and
must not be repeated as boundary support for several objects. Unassigned
navigation-only groups remain valid.

The validator will reject duplicate group ownership before persistence and the
existing failure audit will retain the full model decision plus deterministic
conflict details. No additional Anthropic call is added.

## Acceptance gate after the repair

1. Page 23: ten fresh runs, exactly three objects, no duplicate group ownership,
   one TV console composed of both alternate views, and door-system quantity 1.
2. Adda: Sonnet still identifies two objects.
3. Metall: object separation and source codes remain intact, while its known
   LS1/LS2 ambiguity remains an observation rather than a forced count rule.
4. A page remains allowed as Estimation evidence for multiple objects.
