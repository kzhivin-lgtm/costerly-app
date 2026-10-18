# DETECTION V4 - ORPHAN DETAIL RESOLVER

This is a conditional, narrowly scoped repair stage. The normal Visual Registry has already completed. Do not recreate the visual map, reconsider valid object boundaries, rename objects, or alter a valid object's quantity, identity pages, group ownership, or merge proofs.

You receive only `component_detail` groups that have no established commercial owner, any provisional zero-view rows, the locked existing objects, and the relevant source pages. Resolve every candidate group exactly once. Group candidates together only when the source positively establishes that they are views of one physical fabricated product.

For each candidate cluster choose exactly one decision:

1. `attach_to_existing_object`: the candidates are supporting construction evidence for one existing object. Use that exact existing `target_object_id`. This does not add the candidate IDs to that object's `visual_group_ids`.
2. `promote_to_new_object`: the candidates together depict a complete independently fabricable, supplied, installed, replaced, or priced product. Supply its object fields. Every promoted group becomes an `assembly_view`. When it has N groups, provide exactly N-1 compact pairwise proofs connecting them.
3. `non_commercial_support`: the source positively establishes that the candidates are not an independently quoteable product and do not belong to any existing commercial object. Use only for a material/profile/detail/legend or other non-commercial support item. Do not use it merely because the association is difficult.

Use evidence in this order: explicit code/callout/view reference, matching construction topology, dimensions compatible after a change of axes, and unique repeated geometry. Colour, material, sheet proximity, or room name can only support stronger evidence. Different finished envelopes, functions, or incompatible principal dimensions are positive evidence of a separate product.

An own code combined with a coherent set of principal dimensions and no positive relation to an existing object is strong independent-product evidence. A set of details with no owner is not automatically a product, but it must receive a deliberate decision. Never leave a candidate group unresolved.

Return schema JSON only.
