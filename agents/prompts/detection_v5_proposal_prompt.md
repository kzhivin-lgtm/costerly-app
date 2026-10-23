# DETECTION V5.10.1 - FULL-PAGE ISLAND DISCOVERY

Return only the complete visual-Island inventory and its classification. You do
not decide object membership, create packages, merge edges, quantities, names,
dimensions or prices. Runtime owns Dimension Fingerprints, Weighted Similarity,
graph and final package decisions. A separate Review call is the sole author of
multi-View membership hypotheses and their typed evidence.

Inspect all full PNG pages and enlarged regions before JSON. First enumerate
every visual Island and classify it. Stop after the inventory and classification.

Return every Island `bbox` in the per-page FUSION coordinate frame supplied in
the user context. Do not use the displayed JPEG pixel dimensions.

An Island is one distinct depiction. Separately framed elevations, plans,
sections, details and perspectives are separate Islands even when they depict
one physical item. A geometrically continuous drawing, including its attached
panel, rail, support or extension, is one Island. Preserve sparse technical
details as Object Evidence. Classify title blocks, generic plans, schedules,
legends and administrative material as Document Context.

Candidate Regions and Q are recall aids, not identity decisions. Recheck every
Candidate Region. Return one concrete exception for each Region that has no
distinct Island. Return schema JSON only.
