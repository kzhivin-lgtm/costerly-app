# Detection V4.5 conditional orphan-detail resolver checkpoint, 2026-10-18

## Status and authority

Implementation checkpoint: commits `4a0fcef` and `1f53231`, deployed to
`main`. This is a narrowly scoped commercial-boundary checkpoint, not a new
Detection major version and not an acceptance claim for all benchmarks.

The owner verified one fresh production run of
`Hasolelim_Carpentry_Plan_Floor_07.pdf`: Detection returned nine commercial
objects, including the separate N76B object. The conditional resolver ran for
the unresolved N76B page. This closes the observed self-target and false-N76
attachment failure for that run.

## Protected contract

- The primary Visual Registry remains one call and remains responsible for
  normal commercial-object boundaries.
- The orphan-detail resolver is independent of the Ada Sonnet router. It runs
  only after Registry finds an unowned `component_detail` on an unresolved
  physical page, or a provisional zero-view Registry object.
- A normal Registry result without either condition makes no resolver request.
- All previously locked objects remain available to the resolver as
  ID-free comparison cards. It can compare the candidate with their source
  labels, visual identity, quantities, boundary basis and identity pages.
- Only a locked object whose literal source code occurs on the candidate page
  is an attachment target and receives an ID in the resolver input. A similar
  code, drawing order, shared scale or construction style cannot create an
  attachment.
- The resolver renders only its unresolved physical page. It does not receive
  previous objects' rendered pages merely because they exist in the Registry.
- A distinct source code with coherent orthogonal or dimensioned views and no
  direct relation to an attachment target must be promoted to a separate
  commercial object. `component_detail` is a representation role, not proof
  that the physical item is non-commercial.
- Runtime validation repeats the attachment-target restriction, so a model
  cannot bypass it by emitting a hidden or invented object ID.

## Verification

- Focused Detection suite: `89 passed`.
- `git diff --check` passed before commit.
- Production owner observation: HSL returned the expected nine objects. This
  was a successful resolver path, not merely the regular Registry path.

## Remaining verification and separate work

- Production regressions remain required: Page 23 must return three objects
  through the ordinary Haiku path, and Adda must return two through its routed
  Sonnet path. Neither should invoke this resolver when their Registry result
  is already complete.
- HSL naming is not part of this checkpoint. The observed N76B label rendered
  as `Shell Unit` instead of retaining its source code is a separate Naming
  defect.
- The observed File Review continuous grey refresh is a separate UI defect.
  Do not attribute it to Detection without measuring the browser event, server
  rerun, reads, writes and render cycle.
