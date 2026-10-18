# Detection V4 pairwise-merge-proof checkpoint, 2026-10-18

## Status

Owner-authorized Detection V4 checkpoint at `2718498`. It accepts the
pairwise merge-proof Registry contract after fresh production runs for both
active boundary benchmarks: Adda and Page 23.

This remains Detection V4. It is not a Naming checkpoint and it does not
change the accepted Evidence handoff, UI-only Presentation Preview, Quantity
policy, or the existing conditional Sonnet router.

## Change protected by this checkpoint

The existing Visual Registry request still maps visual groups and locks the
commercial object registry in one model call. It now also returns
`merge_proofs`.

- An object with one `assembly_view` needs no merge proof.
- An object with `N` assigned `assembly_view` groups needs exactly `N - 1`
  links that form one connected graph.
- Every link names the two groups, source pages, observed fact, commercial
  inseparability rationale, and evidence types.
- An explicit document relation is sufficient. Otherwise a merge needs at
  least two independent evidence types, one of which is matching topology,
  transformed dimensions, or unique geometry.
- A shared counter, L shape, touching panels, proximity, title block, colour,
  material, or page alone is not sufficient proof of commercial inseparability.
- The deterministic validator rejects malformed, duplicate, incomplete,
  disconnected, or cross-object proof graphs before Detection persistence.

This is a proof obligation inside the current Registry response. It does not
add a retry, verifier, correction pass, or a second model request.

## Protected V4 contract

- Visual Registry locks commercial-object identity, boundary, quantity and
  relevant evidence pages before Naming. Naming may change only display text.
- `assembly_view` supports object identity. `component_detail` and
  `document_context` can remain Evidence but cannot create a commercial object.
- A visual group has one commercial owner. A physical page can remain Evidence
  for any number of objects.
- Estimation receives each object's complete persisted Evidence handoff. The
  Presentation Preview is UI-only.
- Quantity means complete physical units and defaults to `1` absent explicit
  quantity evidence.

## Production acceptance evidence

All times are Asia/Jerusalem on 2026-10-18. The live database was queried by
`run_id`, including locked object records, Registry decision audit, evidence
references, model route and timing ledger.

### Adda

Expected: two unlabelled but visually separate commercial assemblies. Every
object must retain pages `1-4` as Evidence. The risk router selected Sonnet
because the document has repeated multiple-large-drawing regions and no strong
source object code.

| Time | Run | Registry s | Cycle s | Objects | Evidence |
|---|---|---:|---:|---:|---|
| 11:47:59 | `run_805e2758b9ca4af28236a5b7c78e14f6` | 58.099 | 81.399 | 2 | pages 1-4 per object |
| 11:49:49 | `run_2e7c2389bf944637b25030e148f0e8d5` | 45.947 | 56.739 | 2 | pages 1-4 per object |
| 11:56:59 | `run_63c608037c3a47f0a7958a7971a0ec7a` | 46.688 | 59.371 | 2 | pages 1-4 per object |
| 11:58:45 | `run_474c92e7698a452d869ed016590876a8` | 49.474 | 60.961 | 2 | pages 1-4 per object |
| 12:00:06 | `run_f27bb792720f4df8a393567f00699157` | 47.112 | 59.125 | 2 | pages 1-4 per object |
| 12:02:16 | `run_3e9ea6ccdd874a72a644c1ee42e62c96` | 47.680 | 60.317 | 2 | pages 1-4 per object |
| 12:07:54 | `run_6077ec94461e43ea87d5287774cbdf1b` | 50.588 | 63.737 | 2 | pages 1-4 per object |

Result: 7/7 valid Registries and persisted two-object records, with no
validation failure. Every merge graph had the required connected set of five
or six links across the two assemblies. The Registry averaged `49.370` seconds
and the full cycle averaged `63.093` seconds. One full-cycle outlier of
`81.399` seconds came from the following Evidence stage taking `20.097`
seconds rather than its normal `8-10` seconds, not from Registry failure.

The Registry varied only in whether the overview page was one shared isometric
view or two partial isometric views. It did not alter object boundaries or
Evidence coverage.

### Page 23

Expected: three commercial objects, quantity `1` each, with page `1` as
Evidence for every object: shelving, one sliding-door system, and one
TV-console represented by two alternate views. The router selected default
Haiku for all three runs.

| Time | Run | Registry s | Cycle s | Objects | Merge proof |
|---|---|---:|---:|---:|---|
| 12:10:04 | `run_96d7fe4fdbb544b29451ddb015090f73` | 13.969 | 25.254 | 3 | only the two console views |
| 12:10:38 | `run_caf48affeb46485894bd4fddecf1018b` | 13.528 | 24.727 | 3 | only the two console views |
| 12:11:16 | `run_04126d34d9874af3a9870b9cd10e08f3` | 13.709 | 25.776 | 3 | only the two console views |

Result: 3/3 valid Registries and persisted three-object records, with no
validation failure. Each response had exactly one proof, connecting only the
two TV-console groups through matching topology and transformed dimensions.
Shelving and sliding-door groups remained single-view objects without merge
proofs. The Registry averaged `13.735` seconds and the full cycle averaged
`25.252` seconds.

## Verification

- `main` and `origin/main` point to `2718498`.
- The targeted Detection regression suite passed: `81 passed`.
- `git diff --check` passed.
- The accepted live sample comprises ten successful post-deploy Registries:
  seven Adda and three Page 23.

## Limits and next scope

This checkpoint establishes the current boundary rule for the two active
benchmarks. It does not claim a general proof for Kitchen, Metal or future
documents. Any new benchmark must be evaluated from persisted visual-group
membership, proof graph, object records and Evidence pages, not object count
alone.

Naming is the next separate scope. Its accepted constraints must be recorded
and then tested without changing Detection boundaries, quantities or Evidence.
