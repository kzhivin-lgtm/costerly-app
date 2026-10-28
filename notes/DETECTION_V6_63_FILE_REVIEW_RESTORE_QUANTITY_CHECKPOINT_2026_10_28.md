# Detection V6.63 File Review restore and quantity checkpoint

Date: 2026-10-28

Status: owner-accepted production checkpoint. V6.62 Progress and File Review
handoff remain protected. V6.63 was deployed from `main` at `e97933f` and
accepted by the owner after a live rerun and repeated navigation check.

## Protected baseline

The V6.62 browser progress controller and File Review handoff remain unchanged.
This checkpoint does not add an AI call, change the selected document route,
alter Island or object membership, or reclassify dimensions as quantities.

## V6.63 changes

### Retained File Review

`New Estimate` retains the last immutable File Review payload so `Last
Estimate` can return immediately. It now clears the retained cards' old
Streamlit name-input values and terminal Naming flags. On restore, File Review
performs its existing narrow durable Naming read before edit state or widgets
are created. A former empty placeholder can no longer write against the
already-persisted name and produce a false conflict.

### Explicit quantity caption

The ordinary one-page witness `Стейшен и поддон.pdf` contains the authored
caption `04 / ПОДДОН 5 ШТ` immediately above the mesh View. Its normal evidence
envelope starts below the caption, so V6.40's otherwise correct bounded parser
never received the literal. V6.63 admits only a text fact containing an
explicit quantity marker from a unique, bounded strip directly above one View.
The fact is then subject to the existing caption-bound quantity parser and
conflict audit. Dimensions, unlabeled numbers, side notes, and ambiguous
captions remain excluded.

## Verification

- Targeted Detection evidence and File Review navigation tests: `78 passed`,
  `1 deselected` pre-existing static source-order test.
- `py_compile` passed for `agents/anthropic_adapter.py`,
  `screens/file_review.py`, and `state/session.py`.
- `git diff --check` passed.
- Direct production audit of `run_d865a6499e2f46d4be2822635da38430` established
  the pre-fix failure: both persisted objects had quantity one and the quantity
  audit had no candidates, while the source PDF contains `04 / ПОДДОН 5 ШТ`
  above the second View.
- Live production witness after `e97933f`: the second object returned quantity
  `5`; repeated `New Estimate -> Last Estimate` navigation did not show a
  name-conflict banner and retained the visible object names.

## Accepted behaviour

The accepted result is deliberately narrow:

1. the second object has quantity `5` and no red quantity warning;
2. `New Estimate -> Last Estimate` can be repeated while Naming completes;
3. no name-conflict banner appears and the same persisted names remain visible.
