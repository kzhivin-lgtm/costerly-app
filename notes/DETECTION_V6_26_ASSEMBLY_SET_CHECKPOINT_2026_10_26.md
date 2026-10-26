# Detection V6.26 preliminary assembly-set checkpoint, 2026-10-26

## Status

Accepted by the owner as the preliminary operational checkpoint for a document
that represents one commissioned built-in joinery assembly through overview,
detail, component, material, and hardware sheets. It confirms the detection
boundary and evidence handoff for one positive dossier. It does not claim a
universal cabinet classifier, a semantic naming benchmark, or a completed
regression pack.

- Compiler delivery: `d26985e`, `feat(detection-v6.26): compile confirmed assembly sets`.
- Canonical View-ID and repeated-order repair: `821d2b9`,
  `fix(detection-v6.26): normalize assembly scope evidence`.
- Deferred-Naming race repair: `c9cb521`,
  `fix(detection-v6.26): preserve newer project identity`.
- Positive production run: `run_41fdb9846abb4c2b9e5cfc0d194b6fe6`,
  `V_Cabineter.pdf`, six physical pages.

## Accepted positive result

| Measure | Result |
| --- | ---: |
| Pre-category | `assembly_set` |
| Validated scope | `assembly_set_candidate` |
| Published commercial Objects | 1 |
| Quantity | 1 |
| Retained physical evidence pages | 1 through 6 |
| Retained Registry Views | 17 |
| Identity anchors | pages 1 and 5 |
| OCR duration | 5.878 s |
| Detection duration | 38.045 s |
| Initial processing cycle | 51.963 s |
| Preview generation | 3.561 s, succeeded |

The compiler recorded
`confirmed_scope_compiled_to_one_document_assembly`. It retained the original
12 Registry object candidates only as audit provenance, not as separate
commercial objects. The published Object therefore has all six sheets
available to Estimation, including authored schedules, material notes, and
detail views that do not match the overview dimensions.

## Project identity and Naming race

The repeated explicit order code was correctly persisted as project
`Order 1208`. Partner and Client remained `unknown`, which is correct because
the source did not provide attributable facts for those fields.

The displayed red Naming failure was not a failed object-name publication.
Naming persisted `Built-in cabinetry` and its immediate read-back matched.
While Naming was still running, Document Identity replaced the generic project
`unknown` with the stronger `Order 1208`. Naming then attempted its lower-rank
one-object project fallback and its conditional write declined. The old code
reported that expected refusal as a Naming failure.

V6.26.2 changes only this publication handling: it preserves the newer Project
fact, records the declined fallback in the Naming audit, and reports Naming as
successful when object-name persistence and read-back succeeded. The patch is
unit-tested and deployed, but needs one production re-run to verify removal of
the banner.

## Negative guard

Production run `run_0ed1e59ae0ee43f4ade975ebbcef2826` on `V_Stair.pdf`
published one `Stair railing` Object through the ordinary route. Its V6.26
audit explicitly says `document_category_is_not_assembly_set`. This confirms
that the compiler did not absorb a non-assembly document merely because it has
one object. It is not evidence that a second cabinet dossier passes.

## Protected boundaries and next gate

The accepted boundary is narrow:

- A shared order, title block, date, material, page count, or sheet numbering
  cannot alone trigger assembly compilation.
- Compilation requires the pre-category plus validated scope with Registry-owned
  root Views and witnesses.
- Naming and Presentation Preview have no authority to change object identity,
  quantity, page membership, View ownership, or Estimation evidence.
- V6.25 HSL, Page23, and Adda remain protected benchmarks. They were not
  re-run as part of this preliminary checkpoint.

The next safe validation is one genuinely multi-sheet cabinet/built-in dossier
after V6.26.2 is live, followed by the protected regression pack. Do not widen
the category rule from this single positive dossier.
