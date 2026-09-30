# Estimation v2 contract, task 3.15.8

Status: active architecture checkpoint candidate

## Objective

Replace the legacy Estimation Agent with a bounded extraction and deterministic
composition pipeline. Estimation v2 must populate reviewable Object Detail
data without inventing material identity, prices, labor time, machinery cost,
overhead, or totals.

The legacy Estimation implementation is not an architectural input. Preserve
only accepted product behavior at the system boundary:

- File Review starts estimation asynchronously and navigates to Objects;
- each object has independent progress, failure, review, and approval state;
- Object Detail remains editable and recalculates from persisted inputs;
- preview is a source-derived screenshot, never a generated illustration;
- unit selling price defaults to `self_cost * 1.30`;
- project delivery defaults to `objects_selling_subtotal * 0.03`;
- project installation defaults to `objects_selling_subtotal * 0.10`;
- the user can override and approve selling prices.

## Pipeline boundary

```text
one OCR pass per source document
  -> Detection object set and durable evidence
  -> Estimation v2 object fact extraction
  -> deterministic material identity and price resolution
  -> deterministic construction, production route and Labor Engine
  -> deterministic machinery, purchased-component and overhead cost
  -> object self cost
  -> temporary hardcoded sales policy and user confirmation
```

The normal Estimation path must not submit the full source document once per
object. It receives the approved Detection object and only its relevant OCR
blocks and source pages or regions. A bounded source-page fallback is allowed
when evidence is missing or contradictory. That fallback does not rerun OCR.

## Approved evidence retention, MVP

The original source document is retained in private Storage once per uploaded
content hash. Detection also writes an immutable private evidence package for
each approved object revision:

- a source-derived preview crop;
- one to three bounded screenshots of the pages or regions that support its
  facts, when the preview alone is insufficient;
- compact OCR text blocks and page or region references in Postgres.

The original and evidence images live in private Supabase Storage and are
served only through company-authorized reads or short-lived signed URLs. This
allows a later bounded recrop or page read without a new user upload or OCR
call. The content hash is immutable audit identity. Cross-run reuse and download
optimization are later implementation tasks.

`evidence_pages` is retained as human-readable source text only. It may contain
drawing labels such as `A-01`, so it is not a reliable file-page address.
Detection vNext must add `evidence_page_refs`, each containing the physical
`page_number` used for OCR and storage plus the displayed `source_label`.
Estimation uses the physical number for lookup and retains the label for audit.

## Detection handoff required by Estimation v2

The existing Detection object remains authoritative for object identity,
quantity and whole-document deduplication. The handoff adds durable evidence,
not a second object taxonomy.

```json
{
  "contract_version": "estimation_input_v2",
  "run_id": "...",
  "company_id": "...",
  "document": {
    "content_hash": "...",
    "file_name": "...",
    "ocr_contract_version": "...",
    "ocr_result_ref": "..."
  },
  "object": {
    "object_id": "...",
    "object_name": "...",
    "quantity": 1,
    "quantity_explicit": true,
    "dimensions": {},
    "detected_materials": "...",
    "notes": "...",
    "evidence_pages": [2, 4]
  },
  "evidence": {
    "ocr_block_refs": [],
    "source_region_refs": [],
    "primary_preview_ref": "..."
  },
  "versions": {
    "detection": "...",
    "material_catalog": "...",
    "labor_catalog": "...",
    "machinery_snapshot": "..."
  }
}
```

File Review edits must be applied before this input is frozen. Every Estimation
result records the exact input and catalog versions used.

## File Review and object revision rules

The Continue to Objects action freezes an `object_input_revision` for every
non-ignored Detection object. Objects marked Ignore do not enter the estimate.

Returning to File Review creates a new revision only for changed object input:

- a name-only change updates the display name and does not rerun fact
  extraction or deterministic costing;
- a quantity change preserves extracted unit facts, then reruns affected batch
  aggregation and totals;
- changing an object to Ignore excludes it from the active estimate without
  deleting its earlier revision or audit history;
- restoring an ignored object reuses a compatible frozen fact package when one
  exists, otherwise it queues that object for Estimation;
- a future edit to dimensions, material evidence or source scope invalidates
  the affected fact package and queues only that object again.

Unchanged objects must not be re-read or recalculated merely because the user
visited File Review again.

## Material identity and price linkage

The Israel MVP runtime has three material layers:

1. `estimate_material_requirement`: one material occurrence extracted for one
   object, with the source phrase, specification facts, quantity and evidence;
2. `company_material_item`: the company's private catalog identity and display
   name, with private supplier offers;
3. `reference_material_pricing_identity`: the Israel price class and active
   Israel price model used when no compatible company material is available.

The global physical catalog is not part of the Estimation v2 MVP decision path.
Existing global reference links may remain as inactive metadata, but Estimation
must not require, create or traverse them to identify or price a material.

The estimate requirement is not a new catalog material. Estimation produces a
normalized identity request:

```json
{
  "requirement_id": "...",
  "source_name": "white lacquer MDF 18 mm",
  "category_hint": "mdf",
  "specification": {
    "thickness_mm": 18,
    "surface": "laminated_or_faced",
    "color": "white"
  },
  "quantity": 4.2,
  "unit": "m2",
  "evidence_refs": []
}
```

An Estimation material-resolution coordinator applies two bounded stages. It
reuses shared normalization and hard-attribute compatibility rules, but it is
not the Price Source persistence workflow.

Stage A resolves against the current company's private catalog:

1. load active company material items with active compatible offers;
2. check exact normalized company material names and the structured source row
   behind each active offer;
3. check only aliases that are explicitly linked to a `company_material_id`;
4. reject explicit hard-attribute conflicts;
5. select only one unambiguous compatible company material and offer;
6. return review when multiple plausible company materials remain.

Supplier SKU, supplier index, decor and marketing labels are evidence only.
They may be displayed and retained as offer provenance, but never select a
material identity or price by themselves. In particular, the same SKU string
from any supplier, or a unique SKU from one supplier, is not an automatic
match. Identity follows compatible material facts, not supplier indexing.

The current `company_material_aliases` table points to global reference
materials, not to `company_material_items`, so it cannot serve Stage A while
the global catalog is outside the MVP runtime. The first implementation can use
exact company names and source-row specifications. Persisting a
confirmed recurring estimate phrase requires a separate additive alias mapping
to `company_material_id`; do not repurpose or break the existing table silently.

No company match proceeds to Stage B. An ambiguous or conflicting company match
does not silently bypass company pricing through a market fallback.

Stage B calls the existing pure Israel pricing-identity resolver with the
extracted material family and price-bearing specifications:

```text
unique compatible active Israel pricing identity and active price model
  -> review
```

The existing `resolve_material_pricing_identity` behavior is reused: decoration,
colour, marketing name and supplier SKU cannot create a price class; explicit
price-bearing conflicts reject a candidate; a maximum-five shortlist remains
internal review evidence.

The existing `resolve_price_source_material_identities` orchestration is not
called by Estimation. It reads and writes Price Source-specific rows and audit
events. Shared pure resolution functions must sit below both workflows so that
matching rules do not diverge.

The persisted estimate line keeps all applicable identifiers separately:
`requirement_id`, `company_material_id`, `pricing_identity_id`, and `offer_id`.
Exactly one pricing route is active for a resolved line: company offer or
Israel pricing model. It also keeps `source_name` so the user can compare
extracted evidence with the resolved catalog item.

Object Detail displays the company material name when a company item supplied
the price. Otherwise it displays the Israel pricing material name and identifies
the fallback. User correction creates an audited resolution override,
recalculates the affected line and totals, and does not rewrite the original
extracted evidence.

## Estimation v2 output

The extraction layer may return only evidence-backed or explicitly derived
facts required by deterministic engines:

- construction-template candidate from the approved template vocabulary;
- component and part primitives with dimensions, count and provenance;
- material requirements with specification facts and evidence, but no price;
- bounded manufacturing features used by the CNC and Laser routers;
- purchased fabricated-component requirements;
- installation and delivery scope facts;
- one source preview reference;
- missing and contradictory facts with explicit review reason codes.

The extraction layer must not return:

- material prices or a chosen fallback price;
- labor operations, minutes, hours, crew sizes or labor rates;
- a chosen manual, machine or subcontractor route;
- machine cost, overhead, margin, sale price, VAT or totals;
- unconstrained material, operation, role or template identifiers.

Candidate identifiers are validated against versioned catalogs. Unsupported
values and route-critical missing facts become review items.

## Deterministic composition

For one frozen object fact package:

1. validate the construction template and primitives;
2. resolve every material identity;
3. resolve company-first material price, then exact Israel fallback;
4. choose exclusive production routes from Company Machinery;
5. classify external fabrication as purchased components;
6. call Labor Engine with validated facts and route context;
7. apply company labor rates and machine-cost parameters;
8. allocate overhead from productive labor hours under a separate contract;
9. persist inspectable Object Detail lines and calculate object self cost;
10. suggest selling price and project delivery or installation charges.

A failed resolver or calculator must not silently substitute a guessed value.
The object can be partially reviewable, but self cost is not complete while a
required cost line remains unresolved.

## Scenario matrix

| ID | Scenario | Required result |
| --- | --- | --- |
| E01 | One supported object with complete evidence | Complete Object Detail, deterministic self cost and source preview |
| E02 | Two supported objects in one document | Independent progress and results, shared OCR, no repeated full-document read |
| E03 | One object spans plan, elevation and detail pages | Only linked pages are read, evidence remains attached to every derived fact |
| E04 | File Review changes name, quantity or ignore state | Frozen Estimation input uses the approved edits exactly once |
| E05 | Required fact is absent or contradictory | Specific review reason, no invented material, route, quantity or time |
| E06 | Material identity or price cannot resolve | Editable material line remains visible and self cost stays incomplete |
| E07 | Fabrication is external | Purchased component is charged, corresponding internal machine and labor cost are zero |
| E08 | Machinery capability changes the route | Exactly one deterministic route and an auditable machinery snapshot |
| E09 | One object fails while another completes | Completed object remains usable, failed object has retryable bounded state |
| E10 | Refresh, retry or duplicate submission | Idempotent persisted result for the same input and version set |
| E11 | Return to File Review and change only the object name | Display name updates without a model call or cost recomputation |
| E12 | Return to File Review and change quantity or Ignore | Only affected aggregation and active object membership change |
| E13 | Extracted material uniquely matches a compatible company item | Company material and offer are recorded, company price wins |
| E14 | No compatible company item matches | Existing Israel pricing resolver supplies the visible fallback |
| E15 | Company or Israel candidates are ambiguous or conflict on a hard attribute | Internal review candidates are bounded, no price is guessed |
| E16 | SKU is present but material facts do not uniquely match | SKU remains provenance only, no automatic material or price selection |

## First implementation checkpoint

The first pure material slice is implemented and covered by E13-E16 fixtures:
exact compatible Company Material with active offer wins, absent company match
uses one active Israel price model, ambiguity returns review, and SKU cannot
match a company material. It is not wired to Detection, persistence or UI.

Before SQL or runtime replacement:

1. approve this input and output boundary;
2. define exact reason-code and status enums;
3. define a minimal durable OCR and object-evidence persistence contract;
4. extend fixtures from E13-E16 to E01-E12;
5. prove that one object can be composed from a frozen fact package without an
   LLM call or database writes.

Production and UI remain unchanged until this checkpoint passes.
