# Detection V6.14 ordinary HSL checkpoint

Date: 2026-10-25
Status: protected live checkpoint for the ordinary HSL path. It is not a
universal acceptance of Detection, a replacement for the separate Page23 and
Adda checkpoints, or a resolution of deferred Naming and Preview defects.

Implementation commit: `cf0bc41`.
Production deployment title: `fix(detection-v6.14): omit scope from ordinary proposal`.
Live run: `run_e8006a40e1fe4c68846b59b44dacaf4c`.

## What is protected

V6.12 categorizes the completed MyPDF/Mistral/Fusion evidence before any
Detection-model request. V6.14 uses that category as the route decision:
ordinary, Page23, Adda and source-degraded routes do not ask the model to
produce `document_scope`. Only the `assembly_set` route retains the V6.11
scope observation, and that observation remains audit-only. Runtime bounds it
to four roots, four witnesses, four Island IDs per witness and a
180-character observation.

This keeps existing ordinary Island discovery, classification, Candidate Q,
dimension evidence, Review, graph membership, quantity and Estimation handoff
unchanged. V6.13's one-time larger-budget retry remains only for a response
proven to be cut off inside a JSON string. It is not part of the ordinary
success path.

## Verified HSL result

The `Hasolelim_Carpentry_Plan_Floor_07.pdf` run selected
`ordinary_object_set` and Haiku. It completed without a retry.

| Measure | Result |
|---|---:|
| Discovery attempt count | 1 |
| Discovery proposal output | 7,145 tokens, below the 8,192-token ceiling |
| Detection input / output tokens | 108,013 / 8,678 |
| Detection time | 66.514 s |
| Detection cost | $0.151403 |
| Deferred Naming time / cost | 7.497 s / $0.023858 |
| Known Detection plus Naming cost | $0.175261 |
| OCR time | 8.907 s, provider cost not persisted |
| Full RFQ processing time | 84.573 s |

The known cost is about 17.5 cents. It matches the pre-scope HSL Detection
baseline (`run_b36fddb61a154c5da7229d4e0ca610d7`, also $0.151403) and avoids
the V6.13-recovered run's duplicate initial proposal cost ($0.289492 Detection
alone).

## Island and object audit

Discovery found 35 visual groups: 32 `object_evidence` Islands and three
document-context groups. The ten proof-graph components contain every one of
the 32 object-evidence Islands, with no unassigned object-evidence Island.

- Page 2's floor plan is `IG-P2-001`, classified as
  `document_context/floor_plan`, and is present in
  `discarded_non_object_visual_groups`. It is not a graph endpoint and is not
  one of the ten commercial objects.
- Page 1's title block and page 11's schedule are also discarded document
  context.
- Page 11 retains two standalone object-evidence Islands, producing the two
  final standalone components there.
- The resulting proof graph has ten components, which is the accepted HSL
  object-count result for this checkpoint.

The File Review labels `Document table`, `Revision log`, `N60 Room layout`,
`Surface schedule`, `Room schedule` and `Job log` are not Detection identity
evidence. They are deferred Naming output, known to be defective in this
stage, and must not be interpreted as proof that any of those sheets became a
commercial object. Naming and preview remain outside this checkpoint.

## Verification

- `py_compile agents/anthropic_adapter.py agents/detection_agent.py` passed.
- Focused Detection regression suite passed: `85 passed`, covering timing,
  document classification and registry evidence.
- The new ordinary-contract test proves that `document_scope` is absent from
  the provider prompt and strict schema when the pre-model category is
  `ordinary_object_set`.
- `git diff --check` passed before this documentation record.

## Limitations and next safe work

1. One HSL run establishes the V6.14 ordinary cost and membership checkpoint,
   not repeatability across arbitrary ordinary documents.
2. The ten-component count alone is insufficient evidence of universal quality.
   Future audits must separately inspect Island inventory, classification,
   membership and evidence packages.
3. V6.13's retry has not been removed. If it appears on a normal ordinary run,
   record both provider attempts and diagnose the output expansion before any
   cap or prompt change.
4. The next independent work is the deferred Naming and Preview audit. Do not
   change ordinary Detection membership merely to correct presentation labels.
