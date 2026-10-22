# Detection V5.7.1 experimental checkpoint, 2026-10-23

**Status:** preserved experiment, not accepted for product quality, not deployed.

**Base:** protected V5.6.1 checkpoint `5de4cf4`.
**Checkpoint tag:** `detection-v5.7.1-experimental-2026-10-23`.

## Purpose and protected constraints

V5.7.1 tests whether a single Haiku Registry call can declare a compact,
full-page membership forest while deterministic runtime code validates every
typed fact, builds the graph and packages, and retains Dimension Fingerprints
and Weighted Similarity as supporting evidence.

It does not add a second model call, a router, Sonnet, file-specific logic, or
an all-pairs comparison. V5.6.1 standalone attachment remains intact.

## Implemented contract

1. Registry returns `membership_edges`, each one positive pair of Object
   Islands. An N-View item is a tree of N-1 links, never a singleton or dense
   pair matrix.
2. Runtime accepts only object-evidence endpoints, typed valid facts, unique
   pairs and acyclic trees. Accepted membership links alone decide package
   membership. Dimensions and other semantic facts remain auditable supporting
   edges and cannot overturn it.
3. Direct Registry `semantic_facts` now reach the existing typed validators.
   V5.6 silently dropped this input path.
4. `explicit_document_relation` with `strength: standard` is rejected. Only
   direct object-specific author evidence or an explicit single-object sheet
   can carry that relation.

## Reproducible local evidence

Focused suite after implementation: **87 passed in 1.98s**. `git diff --check`
passed. The raw local reports are intentionally retained outside Git under
`/private/tmp`.

| Source | Result | Status | Raw report |
|---|---|---|---|
| Page 23 | 4 Object Islands, 3 packages; the two TV-console views merge | passes its boundary gate in this run | `/private/tmp/detection_v571_page-23_v571-page23-03.json` |
| Adda | 9 Object Islands, 2 packages | passes its boundary gate in this run. A material-list relation was rejected because it was only `standard` strength | `/private/tmp/detection_v571_Adda_v571-adda-02.json` |
| Metal | 42 Object Islands, 14 packages | count is within the historical 13-15 interpretation range, but visual membership has not yet been reviewed | `/private/tmp/detection_v571_Металл (1)_v571-metal-04.json` |
| Hasolelim | 29 Object Islands, 10 packages | **fails** the protected 32 Islands/9 packages benchmark | `/private/tmp/detection_v571_Hasolelim_Carpentry_Plan_Floor_07_v571-hsl-05.json` |

Full-cycle timings and model cost for these runs were: Page 23, 34.053s and
$0.014661; Adda, 33.931s and $0.035010; Metal, 111.158s and $0.146023;
Hasolelim, 115.273s and $0.155330.

## Known failure, evidence and scope

Hasolelim fails before package reasoning can repair it. Page 3 returns two raw
Islands instead of three. Page 11 returns four raw Islands but classifies only
one as `object_evidence`. The V5.7.1 graph therefore receives only 29 object
endpoints and returns ten packages. This is an Island discovery/classification
regression, not evidence that Dimensions or the membership compiler failed.

The earlier apparent missing HSL and Metal reports were a local runner issue:
the command had returned a still-running PTY after 30 seconds. Draining that
PTY produced complete reports. One later HSL invocation failed separately with
an Anthropic billing response; the recorded HSL result above is a complete run
after service was available.

## Decision and next bounded experiment

Do not promote V5.7.1 or replace V5.6.1. Preserve its membership-edge runtime
and strict direct-document-relation validation as measured work. The next
experiment must retain the V5.6.1 Island discovery and classification contract
while isolating only the V5.7 membership-output change. Its first acceptance
gate is HSL 32 Object Islands and 9 packages, then Page 23 and Adda regression
checks. A historical raw model response alone is not a golden benchmark.
