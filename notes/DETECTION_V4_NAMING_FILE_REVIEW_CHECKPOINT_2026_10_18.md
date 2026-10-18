# Detection V4 Naming and File Review checkpoint, 2026-10-18

## Status

Owner-authorized protected checkpoint at `52c314d`. It retains the accepted
Detection V4 pairwise-merge-proof contract at `2718498`, then adds only the
accepted Naming, File Review, and diagnostic work listed below.

`52c314d` reverts the single rejected Hassola prompt experiment `b86d71c`.
It does not roll back any accepted Detection, Naming, File Review, or
observability behavior.

## Protected behavior

- Detection V4 remains at the accepted Registry, boundary, quantity, Evidence,
  pairwise-proof, temperature-zero, and conditional-router behavior from
  `2718498`.
- Naming rejects transport placeholders and fragments such as `Object 3` and
  `ject 3`, and does not add artificial dashes (`bf1fc6a`).
- Deferred Naming records every compare-and-set attempt and an immediate
  database read-back. Processing to first File Review server render is timed
  without making Naming or Preview block File Review (`48acde4`).
- Any later File Review write of an object name is durably attributed to its
  writer path (`0f0aaa8`).
- A stale browser echo of the pre-Naming text-input value is consumed once and
  cannot overwrite the published name. Subsequent genuine manual edits remain
  normal guarded writes (`ca60ac1`).

## Accepted live evidence

For Page 23 run `run_7940311238ba43759cea43bd0daa8b17`:

- Naming selected and immediately read back `object-003 = TV console`.
- Writer provenance proved that File Review later submitted stale `Object 3`.
- The stale-echo guard was added and regression-tested from that exact event
  sequence.

## Explicitly not accepted

Hassola LIM is an active Detection benchmark, not a solved checkpoint. Its
separate N76B sheet is a ninth commercial object with three complete views.
The rejected `b86d71c` rule incorrectly excluded an object based on page type
and is not part of this baseline. Future Hassola work begins from this commit
and must preserve the protected behavior above.

## Verification

- Reverted exactly `b86d71c` through `52c314d`.
- Focused Detection, Naming, File Review, concurrency, and timing regression
  suite passed after the revert.
- User Material worktree changes were not staged or altered.
