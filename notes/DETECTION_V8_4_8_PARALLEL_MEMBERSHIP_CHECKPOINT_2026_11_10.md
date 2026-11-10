# Detection V8.4.8 parallel Sonnet Membership

Implementation checkpoint on GitHub main base `8eb87f1` (Detection V8.4.7).
This is a local implementation and validation record. Only Ada Membership
changes. Routing, ordinary and Page 23 Haiku paths, and the application and
Cloudflare build markers remain at the base behaviour.

## Contract

On the existing Ada route with Sonnet Membership and a nonempty exhaustive
same-sheet pair queue, send two independent requests in parallel. One must
return one decision per required pair, including pairs without OCR evidence.
The other proposes document-wide Membership without the pair queue or its
responses. Both use the same locked View images. An incomplete pair response
fails validation. The pair ledger is persisted for audit and cannot create
merge edges. Registry continues to admit Membership through the existing
pair-local proof and shared-plan star rules. With zero same-sheet pairs,
the global request suffices.

Multi-sheet technical-only requests use the validated compact Membership
wording and consistent short labels in the provider input. The modern
Discovery descriptions, kinds, bboxes, source facts and classifications
remain in use. Short labels are restored to the fixed Discovery identifiers
before validation. No render field is exposed if there are no render Views
and this compact technical contract applies. A fresh trial with that field
available fabricated render decisions for technical Views and was rejected.
For other split-route documents, the existing render contract applies and
technical evidence must explicitly cite both View endpoints. This retains
the separate render attachment and the V8.4.7 star compiler.

## Verification

All benchmark runs used fresh standard OCR and live Detection. Each of the
two Adda and two Lev 2 runs emitted one Haiku Discovery call followed by two
overlapping Sonnet calls. Provider usage is persisted per call and included
in the existing Registry totals. The failed Adda trials before the schema
restriction were excluded from acceptance.

| File and run | Whole Detection | Sonnet wall | Verified outcome |
| --- | ---: | ---: | --- |
| Adda `run_d7c3f2b173e54b5a9123d7b43d8ff529` | 47.117 s | 23.30 s | `01/04/06/08` and `02/03/05/07` |
| Adda `run_05b06fdcd8b3473c9140ad10b73acdcc` | 49.820 s | 26.52 s | Same exact groups |
| Lev 2 `run_54fd48c9d5c94527b01422b4dc56747e` | 34.811 s | 19.17 s | One kitchen with `01/02/03/04`, render attached |
| Lev 2 `run_284ccfe1556c4b35b30f0d2ecda422e7` | 34.982 s | 19.34 s | Same exact group and render |
| Lev 1 `run_37bc1b7643e545f6af363d9d1fdfbaca` | 54.750 s | | One object with all six Views |

All Adda and Lev 2 View boxes matched the saved reference exactly. Their
queues contained four and six pairs, respectively. Sonnet stage cost was
$0.083091–$0.085266 on Adda and $0.050691–$0.051906 on Lev 2, from provider
tokens at the configured rates. The revised live path used no third Sonnet
request, historical runtime, or manual View descriptions.

Page 23 took its existing native-graphic Haiku route. It produced four
objects with the same quantities and evidence regions as V8.4.7 with the
same OCR package (`run_64515429882040d6bf49fddc9de85a4c` and
`run_69761ea41d014b09bc256a7aebdb90ea`). The older three-object quality
benchmark remains open independently of the Membership change.

HSL Floor 07 stopped before Membership. Its Haiku Discovery response defined
`VG-P001-001` but omitted it from page 1 coverage. The exact saved response
was rejected by both the V8.4.7 and V8.4.8 Discovery validators. No Sonnet
request ran. This leaves the full HSL quality check open without implicating
the new Ada Membership branch.

Broad Detection/OCR and timing suite: 357 passed. The static browser
completion-marker test failed identically on the unchanged V8.4.7 base.
The overlap regression exercises actual concurrent scheduling, complete
pair coverage, rejection of an omitted pair and preservation of the
shared-plan star. Production publication requires the protected-main
release step.

## Owner acceptance

On 2026-11-10 the owner accepted the Adda repair and requested a local
checkpoint. Annotated tag
`detection-v8.4.8-ada-parallel-membership-checkpoint-2026-11-10` resolves to
`6c552b35dd8c58b15307635f7efbf2dd7c9f29a9`. The application was not deployed.
