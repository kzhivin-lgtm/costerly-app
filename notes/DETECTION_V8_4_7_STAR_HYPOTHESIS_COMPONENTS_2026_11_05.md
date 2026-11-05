# Detection V8.4.7 star-hypothesis components, 2026-11-05

## Status

Deployed from V8.4.6 as `0f0380b`. Both `app.costerly.ai` and
`core.costerly.ai` exposed `detection-v8.4.7-star-hypothesis-components` on
2026-11-05. Product acceptance remains pending a fresh `Lev 2.pdf` run.

## Incident witness

Production run `run_158feb0e2e2c4e3c8701d7444c0ff443` completed after the
V8.4.6 Candidate Region repair, but returned `Kitchen` and `Wall cabinet`.
Membership Review correctly described both relationships below:

1. `view-001` plan with `view-003` left elevation.
2. `view-001` plan with `view-004` right elevation.

The V5.6 object-hypothesis validator accepted the first pair, rejected the
second with `object_hypothesis_overlaps`, and V6.37 consequently compiled two
components. A weak 2600/2650 dimension equality stayed only a supporting
relation. This was a Detection commercial-object boundary defect, not an
Estimation or BOM decision.

## Decision

The owner approved a bounded star rule: a single plan or section may support
multiple complementary projections of one physical product. A shared View is
not sufficient evidence. Every proposed pair must still pass the existing
V6.37 local typed-evidence coverage gate.

## Repair

V8.4.7 is active only for the existing V6.37 Ada Membership route.

1. The object-hypothesis validator retains overlapping proposals only when the
   complete overlap cluster has one or more common anchor Views.
2. V6.37 validates local coverage for every retained hypothesis before any
   union.
3. Only then does it coalesce the star into one immutable proof component.
4. A chain with no common anchor, for example `AB`, `BC`, `CD`, keeps the
   historical first non-overlapping components. It cannot become one object.

The Membership prompt now asks for one complete hypothesis when a plan or
section supports several projections. Runtime coalescence remains necessary as
a safe recovery for a valid but split provider response.

## Protected behaviour

V8.4.7 does not change Discovery, Candidate Regions, Fusion, classifications,
Conflict Resolver, dimension scoring, presentation-render treatment, Naming,
Estimation, material resolution, UI, or provider call count.

## Verification

The following focused regression suite passed before deployment:

```text
242 passed, 5 warnings in 2.69s
```

It proves all of the following:

1. A plan plus two independently evidenced elevations produces one component.
2. The same star is exercised through the real Ada Discovery and Membership
   adapter path, not only through a compiler unit test.
3. A non-star overlap chain remains split.
4. Existing Detection prompt, graph, timing and runtime-observability tests
   remain green.

The remaining production acceptance is a fresh `Lev 2.pdf` run. It must
complete and return one commercial kitchen object rather than a Kitchen plus
spurious Wall cabinet split.
