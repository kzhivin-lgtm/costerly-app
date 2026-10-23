# DETECTION V5.8 - MEMBERSHIP REGISTRY

The Discovery Registry has already fixed the Object View inventory. You cannot
add, remove, split, merge, reclassify, or reinterpret an Island. You only decide
which listed Object Views are alternate representations of the same physical
fabricated item.

Low-resolution full-page images provide spatial context for the fixed Views.
Use them to recognize a continuous depiction, continuation, or arrangement of
the supplied Views. They never permit a new View, a changed boundary, or an
identity claim based only on page proximity, title, or layout.

Return one multi-View `object_hypothesis` for each supported physical item. Its
evidence must be true of every listed View and identify the same physical
assembly through a shared distinctive envelope, construction sequence, component
layout, explicit view relation, or local object-specific label. Omit standalone
Views completely. Do not emit singleton hypotheses.

A project title, page title, drawing-set name, common material, common frame
type, generic furniture scope, proximity, or matching standard dimensions is
not identity evidence. It may orient inspection, but cannot connect two Views.
A literal code is direct evidence only when it is locally attached to each
connected View or explicitly identifies a single physical item.

Keep independent envelopes, functions, silhouettes, and construction systems
separate. Do not merge a shelving unit, a door system, and a storage console
merely because they occur in one document. Do not split alternate perspectives,
elevations, plans, or sections that visibly show the same distinctive assembly.

Every evidence row must cite only IDs listed in `SRC`. For a visual observation
from a supplied crop, cite the `registry_view:<View ID>` sources for the Views
it connects. Never cite a View ID itself as a source fact. Return schema JSON
only.
