# Detection V8.4.28 production checkpoint

The owner accepted the production Adda Upload on 2026-11-12. Both
commercial objects have the expected four Views. Two fresh Adda checks
and a fresh Lev 2 control on the release candidate also passed. The next
work is verification of the Estimation parts list against the drawing.

## Release and rollback

| Item | Value |
| --- | --- |
| Release | Haiku 5.5 · Detection V8.4.28 · Sonnet View descriptions and pair evidence |
| Production commit | `114a7b809e168ccaddd14caeb176d43945e0fd9d` |
| Production tag | `detection-v8.4.28-ada-view-descriptions-and-pairs-production-2026-11-12` |
| Combined build | `estimation-v9.2-detection-v8.4.28` |
| Railway deployment | `08f267ce-f2a4-4ed8-98bb-0b49c19ac0d1` |
| Exact rollback commit | `f09b9f62fff7e249f9c74f765f12c59a787741d8` |
| Exact rollback tag | `detection-v8.4.28-rollback-estimation-v9.2-detection-v8.4.27-2026-11-12` |

The rollback retains Estimation 9.2 and restores its immediately preceding
Detection V8.4.27 runtime.

## Accepted behavior

On the Ada route, Haiku 5.5 Discovery returns geometry, View types,
classification and Mistral anchor decisions. Sonnet 4.6 receives the
locked View imagery and writes the descriptions. A positive Membership
observation names two explicit View IDs. The existing pair validation
checks that both are distinct members of that hypothesis. An independent
Sonnet call audits every same-sheet pair when the queue is nonempty.

Owner Upload `run_090b2315dc6a4036a0932bfbaf9ec319` processed the
four-page Adda PDF and published two object records in File Review.
The partition below was matched against the persisted evidence-region
coordinates.

| Published object | Views |
| --- | --- |
| `object-001` | `02/03/05/07` |
| `object-002` | `01/04/06/08` |

All eight Mistral graphic anchors were accepted and carried to the two
objects. Sonnet supplied eight descriptions, the four same-sheet
comparisons kept the neighboring items separate, and all Membership
hypotheses passed local evidence validation. Detection took 61.535 s
and the processing cycle recorded 68.445 s. Deferred Naming completed.
The original PDF was persisted, and its SHA-256 matches the OCR input.

## Verification

| Check | Evidence |
| --- | --- |
| Fresh Adda | `run_e711c352e6f04e03be88060172782b7c` and `run_3be2ece8654f44d39631eeafaec2a788` both returned the exact accepted partition |
| Fresh Lev 2 | `run_b94f440bdba444deba25b92e47c20750` returned one kitchen with all four Views and the render attached |
| Offline replay | Reproduced all four saved partitions, including the two published owner evidence sets and the Lev 2 render attachment |
| Automated tests | 376 passed; the known baseline dependency pin check was deselected |
| Private evidence | The archive includes exact source PDFs, saved responses and audits, published owner evidence, a replay script, and an independently restorable Git bundle |

The separate missing-Bbox-decision failure and robustness of Ada Discovery
under invalid geometry remain open. The accepted Adda partition is the
Detection input for the next Estimation experiments. Verify part identity,
quantity and dimensions against the original drawing before accepting a
Parts Check result.
