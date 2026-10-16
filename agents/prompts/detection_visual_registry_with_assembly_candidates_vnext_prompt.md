## Locked physical assembly candidates

When the input contains `LOCKED PHYSICAL ASSEMBLY CANDIDATES`, they were made by a preceding title-agnostic correspondence task from isolated visual crops. They are not names, quantities, evidence lists or commercial descriptions. They are a binding physical-assembly partition.

Each supplied `candidate_id` must map to exactly one registry object. Each registry object may contain at most one `assembly_candidate_id`. Do not merge or split candidates. Do not dismiss a candidate because the project, room, material palette or page layout is shared. Use `assembly_candidate_ids: []` only for an independently found in-scope object that has no supplied physical-assembly candidate.

The `assembly_candidate_ids` field is required for every registry object. Across the registry every supplied candidate ID must occur exactly once. Continue to decide the object's quantity and all Evidence coverage from the complete drawing package.
