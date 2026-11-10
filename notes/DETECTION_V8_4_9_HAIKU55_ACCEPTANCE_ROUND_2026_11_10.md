# Haiku 5.5 ordinary Detection acceptance round, 2026-11-10

[verified] The pre-experiment V8.4.9 checkpoint is reproducible. This
round improves the saved HSL result in a replay, but the fresh
Detection result still misses the nine-object acceptance criterion.
The product runtime is restored to the tagged checkpoint.

## Checkpoint and controls

- Local rollback tag `detection-v8.4.9-with-research-checkpoint-2026-11-10`
  at `ea9af62604f405a926840ee9202b1b0b8ac0c7ec`, runtime `3f3f157`.
  Restored 41 archive files and 60 nested replay inputs. Five saved
  scenarios, the Page 23 fallback and the 54-region research reference
  reproduced exactly.
- The four protected cases matched checkpoint requests and partitions
  during the local candidate trial. Adda has two exact four-View groups.
  Lev 1 has one six-View object. Lev 2 has one kitchen with four Views
  including its render. Native Page 23 has three packages, and the
  visual fallback has two. These are fixed-response regressions.
- The HSL 07 frozen comparator is nine exact objects on 32 retained
  Views and 49 required same-page pairs. The accepted V6.25 historical
  source is `run_2dceafe62d3440668ca56b6b74101cc8`, with a third View
  on P11. The fixed input already had that View classified as context.
  Two fresh Discovery runs retained the historical P11 View.

## Main experiments

| Controlled experiment | Frozen HSL groups | Main evidence |
| --- | --- | --- |
| V8.4.9 Haiku 5.5 low, same OCR and Discovery | 30 | All seven N57 Views are standalone. |
| Haiku 4.5 comparison from the checkpoint | 9 | Exact co-membership of the 32 frozen Views. |
| Concise prompt, normalize copied display citations offline | 12 | On the same response the malformed citations gave 32. Eight sheets recover, P07 still misses all six expected co-membership pairs. |
| Interleave page images with their crops, give bare citation syntax | 9, 12, 15 | Three requests with identical payload hashes. Misses were P07 and N57. One Membership call, 13.473 to 32.511 seconds. |
| Separate pair observations for topology and geometry | 9, 15 | Identical-input repeat misses N57. With fresh Discovery/OCR this gives 27 objects. |
| Three parallel same-page batches | 10 | Misses the P11 pair. Provider maximum elapsed 15.346 seconds frozen and 19.059 seconds with fresh Discovery/OCR. Fresh input yields 14 objects. |
| Full interleaved Review plus successful batches for pages with no accepted merge | 9, 9, 9 | Offline replay of the same supplementary replies over the three primary responses. No compiler thresholds or Q pairs changed. |
| High effort, 16,384-token output budget | No JSON | Used the entire output budget in 81.881 seconds. |
| Additional review in one request for all missed fresh pages | Incomplete | 13.059 seconds. It omitted both N57 and P05. |

The exact initial fixture, candidate production request, response message
IDs and hash evidence are in the private bundle. A normal Detection
entrypoint on the transient candidate generated the exact tested request.
Its independent live results were `run_5d094a305792422e802f314fc892ec3b`
with saved OCR and fresh Discovery (32 objects, 54.957 seconds), and
`run_a7166b78c69c4679babdab87353bd9b7` with new OCR and fresh Discovery
(26 objects, 77.178 seconds including 23.337 seconds of OCR).

[verified] The supplemental replay on the latter live input restores all
expected membership on P03 through P10, including the seven N57 Views.
It gives 11 objects. P02 is an extra object admitted by Conflict Resolver,
which describes the target as a whole architectural floor plan. P11 has
one pair and one unjoined View. With a separately recorded generic role
response, the same offline replay removes P02 and gives 10 objects on all
33 expected Views. A repeat of the role instruction also withheld a
target another response identified as a technical elevation. This role
candidate has not passed recall controls.

[verified] The small P11 plan has a visible printed item callout. A
targeted reading recovered its code once but did not confirm its leader
against a fabricated part. It also tried to cite a Q comparison row as a
printed relation. The follow-up excluded Q rows as author evidence and
still did not establish the link. The P11 View was left independent in
the experimental replay.

## Disposition

The single-request candidate was removed from runtime. The supplemental
and role results remain experiments. Keep all same-page pairs, protected
Ada and Page 23 routes, and current merge thresholds. Keep Q redesign,
routing, singleton attachment and switching to Haiku 4.5 deferred.

Any successor must be universal. Document names, page numbers, item
codes, source IDs used as examples and expected partitions belong only
in the benchmark. The prompt can specify general evidence rules and read
runtime inputs. The remaining work is to find a document-independent
bounded review that repeats on newly discovered Views, preserve real
fabrication recalls when changing role review, and verify a negative
same-page control before accepting a new runtime. An additional product
review stage changes call count and needs an explicit decision on its
budget and scope.

Private artifact directory
`/Users/qb/Documents/ChatGPT/Costerly/output/detection-haiku55-ordinary-acceptance-2026-11-10`.
All 181 files verified from `SHA256SUMS`, whose SHA-256 is
`735f8828a81fea1410fd15c3902da34b4f496981184ca31a35c4dc11b2256400`.
Focused candidate tests reported 259 passed and the existing Processing
completion-marker failure. The current code is identical to the checkpoint.
