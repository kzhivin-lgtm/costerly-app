# DETECTION V4.1 - CONDITIONAL BOUNDARY REVIEW

This is an independent boundary review, invoked only because deterministic
document geometry found repeated separate graphic blocks while the primary
registry returned one commercial object. The primary object decision is not
provided to you and must not be inferred. Inspect the full pages yourself.

Return the complete V4 commercial-object registry and page coverage. This is
not Estimation, naming, dimension extraction, material extraction or a
product-description task.

## Boundary decision

Decide complete fabricated products that a contractor could quote, fabricate,
supply, install, replace or price independently. Representations of one
connected construction, including its views, elevations, sections, modules,
details and assembly sheets, remain one commercial object.

Split only when the full drawings establish separate complete fabricated
constructions. Separate finished envelopes, independent functions, separate
plans, elevations, silhouettes, construction systems, codes, quote scope,
delivery or installation are positive split evidence. A shared sheet, project,
material palette, spatial proximity, room, title block, absence of codes or
generic furniture scope is never merge evidence.

When two complete physical outlines have no visible connecting construction,
return two objects even without labels or codes. Conversely, return one object
only with a factual `boundary_basis` describing positive integration, such as a
continuous carcass, worktop, frame, track, common mounting structure, explicit
same-object relation or explicit joint quote scope. Never call adjacent
furniture an integrated system without that evidence.

The supplied visual map is navigation-only evidence. It does not decide the
commercial object set. Attach map groups to the objects they actually depict.

## Quantity and transport labels

Use the exact printed object code as `transport_label` when one exists.
Otherwise use `Object 1`, `Object 2`, and so on. Quantity is complete physical
commercial units, defaulting to one unless source evidence proves another
count. Keep `quantity_explicit` false for the default.

## Full Evidence coverage

For every physical upload page, return exactly one `page_coverage` entry. Put
an object ID in `object_ids` whenever any visual, graphic, textual, layout,
title, schedule, detail, plan, section, alternate view or assembly instruction
on that page relates to the object. A page may belong to multiple objects.
Evidence is complete object context, never a material-calculation shortlist.

Use empty `object_ids` only when the page has no content related to any
in-scope object. Give every page a concise factual `evidence_reason`.

Return schema JSON only. Do not extract names, dimensions, materials, pricing,
notes, confidence or external envelopes.
