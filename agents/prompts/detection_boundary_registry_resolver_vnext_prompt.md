# DETECTION V4 - BOUNDARY-SENSITIVE REGISTRY RESOLVER

The input contains full pages, enlarged regions and a locked visual representation map. Resolve commercial-object boundaries from the `assembly_view` groups in that map, then return the final commercial registry and complete page coverage. Do not redraw the map or invent new visual groups.

This is an identity-resolution task. First group alternate projections that show the same physical assembly. Then create one commercial object per independently fabricable physical assembly. Every `assembly_view` must belong to exactly one returned object. `component_detail` and `document_context` groups never appear in `visual_group_ids`.

Merge views only with positive evidence: an explicit relation or code, matching construction topology, dimensions compatible after an axis change, repeated distinctive geometry, or concrete physical integration such as one continuous carcass, worktop, frame, track or mounting structure. A project name, room name, same sheet, visual proximity, shared material palette, generic furniture scope, absence of codes, or a common document layout is never merge evidence.

Different finished envelopes, functions, construction systems, bay topology, heights, appliance arrangement, mounting conditions or incompatible dimensions are independent-product evidence. Treat them as separate products unless the pages establish actual physical integration. A low console with mirror panel and a separate upper wall cabinet are not one assembly merely because they appear on the same sheets or are part of the same interior project.

For every physical upload page return exactly one `page_coverage` record. Include an object ID whenever that page contains any drawing, text, render, plan, section, detail, schedule or layout content relevant to it. A page may relate to several objects. There is no arbitrary evidence-page limit.

Use ordered object IDs, default quantity 1 where quantity is not explicit, and `Object 1`, `Object 2` as transport labels when no literal object code is available. `boundary_basis` must name the specific positive merge evidence, or the specific independent-envelope evidence for a separate object. Return schema JSON only.
