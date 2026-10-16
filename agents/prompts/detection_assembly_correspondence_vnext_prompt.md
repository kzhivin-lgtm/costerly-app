# DETECTION V4 - PHYSICAL ASSEMBLY CORRESPONDENCE

This is a narrow pre-registry visual task. The input consists only of isolated drawing crops, their stable representation IDs and physical PDF page numbers. It deliberately excludes the file name, OCR, project name, room title and title block. Do not infer identity from information outside the crops.

Each crop may show a complete fabricated assembly, another view of one assembly, a component/detail of an assembly, or non-product drawing content. Build a partition of the representations before any commercial-object registry exists.

## Physical assembly candidates

An `assembly_candidate` groups only representations of one complete physically unified fabricated assembly. A candidate may contain one crop or repeated views from several pages.

Merge crops only with positive cross-view correspondence: a matching distinctive silhouette or envelope, repeated panel sequence, common carcass, continuous worktop, frame, track, mounting structure, or an explicit visible view relation. Internal dimension annotations may help distinguish matching versus different envelopes, but never return their values.

Two separate finished envelopes with different silhouettes, proportions, functions or independent bases are separate candidates, even when they appear next to each other on every page, share a finish, have no codes or quantities, or belong to the same room. Do not merge them into a room-furniture composition.

Do not make a candidate for an isolated panel, handle, hardware detail, dimension fragment, schedule or generic drawing notation unless the crop visibly contains a complete independent assembly. Put those representation IDs in `non_assembly_representation_ids`.

This is not naming, quantity, pricing, evidence selection or commercial-object classification. Do not use generic product names. `visual_identity` and `correspondence_basis` must state only visible correspondence facts.

Account for every supplied representation exactly once: either in exactly one candidate or in `non_assembly_representation_ids`. Return schema JSON only.
