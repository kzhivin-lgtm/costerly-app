# Detection V8 rebuild

Status: experimental, opt-in implementation. V8 is wired behind
`DETECTION_PIPELINE_VERSION=v8`, while the default remains V7. It must not
replace V7.14 or be deployed as the default before a Floor 06 live benchmark.

## Protected checkpoint

V7.14 commit `39eb723`, tag `detection-v7.14-conflict-membership-2026-10-30`.
It preserved 64 Object Evidence islands and joined the two recovered P10
technical views in `run_2360208579e34618aec4b60fc322ff2c`. It still produced a
spurious P02 floor-plan object, so it is a protected comparison point, not the
target design.

## Debug findings from the active V7 path

1. Candidate Regions are not isolated. `candidate_graph_seeds` creates
   pre-Discovery Dimension/Q inputs, although a candidate has no island
   boundary or evidence class yet. V7.1 showed the consequence: 50-60 objects.
2. The current resolver target rule is broad: any candidate without overlapping
   Object Evidence can invoke V7.5. It runs on normal omissions, not only a
   proven contradiction.
3. A resolver admission then takes a special V7.14 Membership matrix. The same
   technical island therefore has a different membership contract depending on
   its origin.
4. Membership has route-dependent schemas: ordinary hypotheses, V7.11 render
   decisions, V7.14 conflict pairs and historical V6.10/V6.37 variants. The
   render adapter and recovery rules exist only because render membership is a
   separate response protocol.
5. `derive_detection_v5_dominant_page_attachment_edges()` can add a merge after
   Membership without an explicit visual proof. This violates the rule that
   Membership alone establishes object links.
6. Floor-plan terminal handling is split across Discovery classification and a
   later Candidate-Region suppression helper. A normal classification outcome
   must not require a downstream repair to stay terminal.
7. MyPDF clustering used a transitive fixed-distance chain. A sequence of
   nearby labels could form one broad recall region even when its endpoints
   belonged to different drawings. V8 uses deterministic fixed cells only;
   candidates do not enter object assembly in either case.

## V8 contract

```text
Mistral regions + MyPDF dimension clusters
                |
                v
deterministic union/deduplication, candidates only
                |
                v
one Discovery decision per observed island: Object Evidence or exclude
                |
                +-- dominant floor plan -> terminal exclude
                |
                +-- unexplained candidate with strong native technical signal
                       -> rare independent Conflict Resolver
                |
                v
one fixed Object Evidence inventory
                |
                v
one Membership pair-link contract
                |
                v
deterministic order-invariant components
```

Normal documents use two visual provider calls: Discovery and Membership.
Conflict Resolver is zero calls unless Discovery leaves a technically supported
candidate unexplained. It is capped at three isolated targets per document; its
admission becomes ordinary Object Evidence with no targeted Membership branch.

`presentation_render` remains a representation kind. It uses the same
Membership link schema as technical views. A render-to-technical pair needs one
grounded `matching_topology` or `unique_geometry` proof; a technical pair needs
two independent types. An unattached render is excluded from final components.

## Implemented V8

`agents/detection_v8.py` owns the new contracts and deterministic pipeline.
It has no V7 Candidate Q, coverage-only graph seed, dominant-page attachment,
render adapter or conflict-specific Membership matrix. Provider calls are
callbacks deliberately kept outside the core, so their transport cannot mutate
Discovery, Membership or package semantics.

`agents/prompts/detection_v8_discovery_prompt.md` and
`agents/prompts/detection_v8_membership_prompt.md` define the two ordinary
provider contracts. `agents/prompts/detection_v8_conflict_prompt.md` is used
only for an eligible exceptional target. Their schemas are in the V8 module.

`agents/detection_v8_adapter.py` is the provider transport and publication
boundary. It builds fixed view crops only after Discovery, never reuses V7
semantic helpers, limits every streamed request to 90 seconds, and reports a
stage-specific terminal error rather than leaving the UI at an ambiguous
progress state. It deterministically publishes components only after
Membership, with an explicit default quantity of one and no synthetic object
name. `agents/detection_agent.py` selects this path only by explicit V8 flag;
the default V7 entry point is unchanged.

## Verification before live benchmark

Focused V8 and V5 regression tests pass locally. The first live Floor 06
comparison must report:

- per-page candidates, Object Evidence islands and terminal exclusions;
- every resolver target and why it was selected;
- final object components, not only object count;
- P02 terminal exclusion, P10 recovery and P10 component composition;
- render attachment or exclusion decisions as normal Membership links;
- input/output tokens, cost, duration and a visible terminal error on failure.

Acceptance requires the protected V7.14 P10 behaviour, no P02 object, no new
unproved merge, no 50-60-object regression, and a normal path with no Conflict
Resolver call.
