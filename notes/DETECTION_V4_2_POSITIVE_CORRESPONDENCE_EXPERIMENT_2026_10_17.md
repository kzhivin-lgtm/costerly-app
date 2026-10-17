# Detection V4.2 positive correspondence experiment, 2026-10-17

## Status

Owner-authorized experiment from protected checkpoint `495851f`. This record
does not establish a new accepted Detection checkpoint until fresh benchmark
runs pass.

## Diagnosed cause

The failed Page 23 Registry audit described `group-001` as vertical shelving
and `group-002` as a door system, but assigned `group-002` to both objects.
The previous correspondence contract carried only a bare group ID, so a model
could use a false cross-view relation as object-boundary support. Exclusive
group ownership correctly rejected that contradictory handoff, but could not
prevent its generation.

## Change

- Keep one integrated Visual Registry request, exclusive visual-group
  ownership, full shared physical-page evidence and the existing router.
- Each Registry object now declares `primary_visual_group_id`, a representation
  that directly depicts the complete product.
- A non-primary representation is allowed only when `related_groups` connects
  it to that primary representation through a positive `match_basis` and a
  relation type of `same_assembly_view` or `object_detail`.
- The runtime normalizes the primary ID together with model-provided group IDs
  and rejects group sets disconnected from their primary representation.
- This is not an extra call, retry, assembly-island experiment or Graph
  resolver.

## Protected behaviour

- A physical page can remain Estimation evidence for every relevant object.
- A shared context group never becomes a second owner of an object-specific
  visual group.
- Detection V4 remains the agent version. V4.2 remains its routing layer.

## Acceptance gate

1. Ten fresh Page 23 runs: exactly three objects, no validation failure,
   shelving and door system remain separate, and both console views are one
   object.
2. Ada retains two objects through its existing Sonnet route.
3. A multi-page benchmark retains all relevant object evidence pages.
