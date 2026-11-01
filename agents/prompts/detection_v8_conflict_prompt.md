# Detection V8: Exceptional Conflict Resolution

Inspect only the supplied neutral crop and its page context. This request is
made because one bounded technical candidate was not explained by Discovery.
It is not a second Discovery pass and it must not review any other page area.

Return exactly one decision for the supplied target:

- `object_evidence` only when the crop contains a distinct fabricated-object
  drawing, render/photo, module or construction that Discovery should have
  retained.
- `exclude` for document material, an incomplete non-object fragment, or when
  the crop does not establish a distinct fabricated object.

For `object_evidence`, returned bbox coordinates are in the supplied crop's
pixel frame. `bbox` may include only attached dimensions, labels and leaders.
`core_bbox` encloses the physical depiction. An `exclude` decision needs only
the target ID, decision and reason. Never use a whole-page floor plan as object
evidence.
Return only schema JSON.
