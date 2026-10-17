# Detection V4.2 router and Registry audit checkpoint, 2026-10-17

## Status

Protected owner-authorized working checkpoint. It is not an acceptance of
stable commercial-object boundaries.

## Checkpoints and scope

- Baseline Registry path: `8ea647c`.
- Preserved V4.2 router and File Review metrics checkpoint: `e115ec4`.
- Current code checkpoint: `1049e85`.

V4 remains the Detection version. The router is V4.2 behaviour, not a V5
agent or a second boundary agent.

## Protected behaviour

- The Visual Registry locks object IDs, quantities and evidence pages before
  Naming or Evidence packaging.
- Evidence remains complete object context, with no arbitrary evidence-page
  cap. One physical page may belong to more than one object.
- Presentation Preview is UI-only and is not supplied to Naming or Estimation.
- Naming is deferred and cannot merge, split, count or reorder objects.
- File Review renders persisted Naming duration and total successful-provider
  token cost as `TC`; the value is not an invoice-level provider debit.
- `registry_decision_audit` preserves the exact structured Visual Registry
  response before runtime group-ID normalization and page-coverage derivation.
  It contains visual groups, proposed objects, `boundary_basis` and coverage.

## Router contract

The router is deterministic and only selects the Registry model. It never
proposes, splits, merges or counts objects.

- Default: Haiku Registry and Haiku Evidence packaging.
- Sonnet Registry only: no strong author code and either two or more large
  drawing regions on one page, or such regions repeated on at least two pages.
- Evidence packaging remains Haiku after either Registry path.

## Observed fresh runs

All times below are Israel time, 2026-10-17.

| Time | File | Registry model | Router | Object count | Result |
|---|---|---|---|---:|---|
| 11:33 | Page 23 | Haiku | pre-router baseline | 3 | correct |
| 11:38 | Page 23 | Haiku | pre-router baseline | 3 | correct |
| 11:50 | Page 23 | Haiku | default | 4 | split TV-console views incorrectly |
| 11:51 | Page 23 | Haiku | default | 3 | correct |
| 11:52 | Adda | Sonnet | boundary risk | 1 | merged two assemblies incorrectly |
| 11:56 | Adda | Sonnet | boundary risk | 2 | correct |
| 11:57 | Adda | Sonnet | boundary risk | 2 | correct |

Page 23 does not route to Sonnet because its one-page OCR package reports one
large drawing region. Adda routes to Sonnet every time: four OCR pages, seven
large regions, three pages with multiple large regions, and no strong author
code.

## Diagnosed limits

The persisted audit establishes two unresolved model-decision errors.

1. In Page 23's four-object run, Haiku assigned the two isometric views of one
   TV console to separate objects without stating positive evidence that they
   were separate products.
2. In Adda's one-object run, Sonnet treated the project title, lack of codes
   and a claimed common L-shaped envelope as proof that two visually separate
   assemblies were one commercial object. Project title and shared sheets are
   not merge evidence.

The router correctly selects the expensive model for the Ada risk signature,
but model selection alone does not make Registry output deterministic. No
Page-23 or Adda count override has been added. Any successor repair must be
evaluated against these audits and preserve the protected behaviour above.

## Active experiment H1, Page 23 Haiku correspondence

Scope: only Haiku's Visual Registry prompt. Sonnet, the router, schema,
request count and Evidence packer are unchanged.

The failing four-object audit gave the two TV-console views empty
`related_group_ids`, then treated each as a separate product without positive
evidence of incompatible envelope, function or structure. H1 makes
`related_group_ids` an explicit cross-view correspondence audit. Before
leaving that array empty, Haiku compares distinctive physical patterns. A
linked pair must be one object unless `boundary_basis` names specific
incompatibility. Shared page, room, project, finish or proximity remain
invalid correspondence evidence.

H1 code checkpoint: `1a62549`. Usage events use prompt version
`detection_v4_2_visual_registry_haiku_correspondence_experiment_v1`.
Pass criterion: five fresh Page 23 runs each return three objects, and the
TV-console object contains both corresponding visual groups. Any four-object
run fails H1.

Four persisted fresh Page 23 runs each returned three objects. The next run
failed before a result was persisted because its one `page_coverage` entry
omitted a Registry object, producing empty derived evidence pages. This is a
coverage-transport failure, not evidence that H1 split or merged an object.
H1 is therefore protected as a promising correspondence checkpoint, but its
five-run boundary-stability criterion is not yet complete. The next two
post-checkpoint reliability repairs are deliberately separate: normalize the
single-page coverage invariant and persist failed-validation audits. This
experiment does not evaluate Adda.

## Post-H1 reliability repair

For a one-page upload, every Registry object necessarily has page `1` as
evidence. If the model omits an already-declared object ID from that only
coverage entry, runtime normalization now restores page `1` and records
`single_page_coverage_reconciled_object_ids` in the successful usage event.
This does not add, remove, merge or split a commercial object.

If a structured Visual Registry response still fails validation, Detection now
persists a failed usage event before returning the original failure. Its raw
usage retains the unmodified `registry_decision_audit`, validation error,
validation stage and V4.2 model route. `run_id` is intentionally null because
no validated RFQ run exists. Multi-page coverage remains strict: this repair
does not infer missing evidence pages outside the one-page invariant.

## Verification

- Focused tests: 89 passed.
- `py_compile` completed code compilation but could not write an existing
  `.pyc` cache due local filesystem permissions. This did not affect tests.
- Production ledger was reviewed for all seven runs listed above.

## Active ownership-contract candidate

Checkpoint `5a1871a` preserves the latest H1 and reliability state before this
candidate. The approved next repair makes `visual_group_ids` exclusive
commercial-boundary support, while preserving shared physical-page evidence in
`page_coverage`.

- A shared schedule, title block, layout or multi-object context is an
  unassigned navigation group. It remains evidence for every relevant object
  through `page_coverage`.
- A visual group assigned in `visual_group_ids` has exactly one
  commercial-object owner. A duplicate assignment rejects the Registry before
  any RFQ or Estimation handoff is persisted.
- The existing `registry_decision_audit` remains stored for both successful and
  rejected Registry calls. Duplicate ownership additionally records the
  deterministic object-ID conflict in `validation_details`; it does not request
  private model chain-of-thought.
- No additional Anthropic call, router condition or Evidence-packer behaviour
  is introduced.

Candidate prompt versions are
`detection_v4_2_visual_registry_haiku_correspondence_ownership_v2` for Haiku
and `detection_v4_visual_registry_integrated_v5` for Sonnet. Focused contract,
prompt and audit tests pass 58/58. Production acceptance remains the four-part
gate recorded in `DETECTION_V4_2_PAGE23_OWNERSHIP_CHECKPOINT_2026_10_17.md`.
