# Detection V4.27 Phased Registry Intermediate Checkpoint

Date: 2026-10-19

Commit: `99a9fa1`

Status: protected intermediate checkpoint, not an HSL boundary acceptance

## Objective

Separate the single Haiku Registry response into a causal sequence without
adding another model call: visual-island inventory, classification, proof graph,
packages, then page coverage.

## Protected behavior

- One Haiku Registry call remains at `temperature=0.0`.
- The V4.23 passive OCR recall aid remains non-binding.
- Naming, UI-only preview generation, File Review timing, locked object IDs,
  full Evidence, router behavior and Estimation handoff are unchanged.
- Inventory returns no class. A separate exact-once classification record then
  assigns `object_evidence` or `document_context` with a factual reason.
- Only the proof graph may determine the groups in a commercial package.
- The Registry audit preserves inventory, classification, graph and package
  decisions on both success and validation failure.

## Evidence to retain

HSL event `4205e85a-ec39-4373-91c2-fd380f4f6f62`, 2026-10-19 13:15 UTC,
used prompt `detection_v4_27_inventory_classify_graph_package_temperature_0`.
It found 35 islands and classified 32 as object evidence, three as document
context. Its 20 proof edges formed 12 graph components, but it returned only
nine package descriptors. The validator correctly rejected three unrepresented
singleton components rather than silently losing their Evidence.

The page-4 N57 layout is the next active issue. Its shared plan and separate
kitchen, island and cabinet views require a non-merge contextual relationship:
the root sheet code N57 is preserved, while the three commercial products are
ultimately N57A, N57B and N57C. Ordinary proof edges must not join those three
products into one component.

## Verification

- Registry-contract tests: `74 passed`.
- Detection regression tests: `47 passed`.
- `git diff --check` passed.

## Next experiment

V4.28 adds a sixth graph relation, `context_reference_link`. It may associate
a composite view with multiple product packages, but never contributes to a
proof component or merge. Naming preserves an authored root code and assigns
deterministic A/B/C suffixes when Detection splits that authored sheet-level
code into distinct commercial products.
