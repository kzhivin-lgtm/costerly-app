# Detection V4 Page 23 temperature-zero checkpoint, 2026-10-18

## Status

Owner-authorized checkpoint at `2593c23`. It accepts the Page 23
object-boundary release gate under the current Haiku Visual Registry settings.
It is not a general acceptance for Adda, Kitchen, Metal, or arbitrary future
documents.

Detection remains V4. V4.2 names the existing routing and Registry behaviour,
not a new Detection agent version.

## Change protected by this checkpoint

The single integrated Haiku Visual Registry request now explicitly sends
`temperature=0.0`.

- It still receives the same full-document images, OCR package and Registry
  prompt.
- It still makes one model request. No retry, verifier, second boundary agent,
  Sonnet escalation, or object-count override was added.
- The temperature is persisted in the Registry usage event for accepted and
  rejected responses. The experiment can therefore be queried without
  inferring request configuration from a commit date.
- The measured prompt version is
  `detection_v4_visual_registry_group_roles_experiment_v2_temperature_0`.

## Protected V4 contract

- Visual Registry first maps visual depictions and locks the commercial object
  registry. Naming cannot add, remove, split, merge or recount objects.
- Only `assembly_view` depictions may support an object boundary. A
  `component_detail` and `document_context` remain evidence, never commercial
  objects.
- A visual group has one object owner. A physical page may be Evidence for any
  number of relevant objects.
- Evidence remains complete source context for Estimation. Presentation Preview
  remains UI-only and is not Estimation evidence.
- Quantity means complete physical units and defaults to `1` when no explicit
  quantity is established.

## Page 23 acceptance evidence

Source: private `page-23.pdf`, one physical page. Expected result: three
commercial objects, each quantity `1` and each with page `1` as Evidence:

1. Separate vertical shelving assembly.
2. One shared-track sliding door system.
3. One horizontal TV-console assembly represented by two isometric views.

All timestamps below are Asia/Jerusalem on 2026-10-18. Each run used Haiku,
`temperature=0.0`, the same `7,897` Registry input tokens and `1,089` output
tokens.

| Time | Run | Registry s | Locked Detection objects | Registry membership |
|---|---|---:|---:|---|
| 00:03:53 | `run_b56feee691d04b8096162d12709e7b7c` | 12.649 | 3 | shelf, door, both console views |
| 00:04:35 | `run_12942b6c8efb494bb9eae8f98d1f3353` | 12.261 | 3 | shelf, door, both console views |
| 00:05:10 | `run_69a88d76228f4f06a07f49a1bab3dbe0` | 12.231 | 3 | shelf, door, both console views |
| 00:05:41 | `run_8801d8b0667d48b7a396e7f53454b510` | 12.315 | 3 | shelf, door, both console views |
| 00:06:25 | `run_b5382229f8a44e1d822efa4a29e16550` | 12.279 | 3 | shelf, door, both console views |
| 00:06:58 | `run_a6653387bb844ca9bf6d241b83a56e79` | 12.968 | 3 | shelf, door, both console views |
| 00:07:34 | `run_5ca87c56112e419b836f818eac63d6ba` | 14.470 | 3 | shelf, door, both console views |
| 00:08:06 | `run_442882d1d1bd4cc58df7699bbc74c081` | 12.298 | 3 | shelf, door, both console views |
| 00:08:43 | `run_dcc4da27b10b4bb89d47f2aee4954ceb` | 12.476 | 3 | shelf, door, both console views |
| 00:09:23 | `run_7436b010b61e4b419805b51bdac60a16` | 12.438 | 3 | shelf, door, both console views |

Result: 10/10 valid Registries, 10/10 valid locked Detection records, 10/10
with quantities `1, 1, 1`, and 0 validation failures. The Registry averaged
12.639 seconds. The end-to-end RFQ processing-cycle event averaged 23.705
seconds.

Each decision audit classified the shelf and door construction callouts as
`component_detail`, the title block as `document_context`, and the two complete
console depictions as `assembly_view` members of one object. The single source
page was shared Evidence for all three objects.

## Verification

- Commit `2593c23` changes only the integrated Visual Registry temperature,
  telemetry, prompt-version label and their assertions.
- Focused test suite: `57 passed` in
  `tests/test_agent_timing.py`, `tests/test_detection_prompt.py`, and
  `tests/test_detection_vnext_schema.py`.
- The request was submitted through the current Haiku route. It did not use
  Sonnet.

## Limits and next acceptance scope

This result establishes that uncontrolled generation variability was a material
cause of the Page 23 failure under the prior V4 Registry configuration. It
does not prove that temperature zero yields correct semantic grouping for every
document. Before treating it as a cross-document V4 boundary improvement,
evaluate one fresh run each for Adda, Kitchen and Metal, then inspect object
membership and Evidence rather than count alone.
