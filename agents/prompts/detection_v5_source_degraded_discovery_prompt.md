# DETECTION V5.13.2 - SOURCE-DEGRADED VISUAL REPRESENTATION MAP

This route is used only when no page has usable coordinate-bearing OCR or
native-PDF evidence for ordinary Detection V5. Work from the attached full
rendered pages only. Do not decide commercial objects, quantities, names,
prices, dimension chains, summed dimensions or graph edges.

Return a complete visual representation map. A representation is an observed
drawing or graphical detail, not a future Object Island, commercial object or
rectangular region. Do not decide whether it is an independent product, part,
detail, document context or alternate view. That decision belongs to Review.

One representation is one coherent graphical depiction. Group all visually
connected geometry, including attached panel, rail, support, diagonal
continuation or extension. A continuous depiction remains one representation
even where its shape is not rectangular. A track with its leaves, or a complete
assembly with its attached geometry, remains one representation even if empty
space lies between subparts. Do not split a depiction because annotations,
leaders, local dimensions or visual density change.

Use the supplied rendered-page pixel frame for both `core_bbox` and `bbox`.
`core_bbox` tightly encloses the physically continuous depiction. `bbox` adds
only the immediately associated dimensions, leaders and labels. It may overlap
another envelope when drawings are spatially interleaved, but must never absorb
a different physical depiction solely for convenience.

Return exactly one compact `page_coverage` record for every page. It must list
every returned representation exactly once. Return schema JSON only.
