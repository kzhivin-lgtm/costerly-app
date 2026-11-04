# Estimation V6.1, evidence to construction and project materials

Work: 3.17.4.5. Status: local implementation, live acceptance pending.
Owner authorized V6.1 on 2026-11-04. Base: e608f37, matching remote main.
V5.8.2 navigation/recovery, Detection identity and material-only scope remain
protected. Pre-existing TODO changes belong to the owner.

## Decision

Use one shared Analyze over Detection's immutable evidence, followed by
object Calculation. Analyze owns large assemblies, repeated members,
operability, surface/material interpretation, evidence-linked text/legend
definitions and explicit construction assumptions. Calculation measures and
completes the locked construction, without choosing a different material.
Code expands parts, layers, edge material and hardware. The existing Material
Engine compares permitted hidden-material alternatives using project purchase
cost, after C/I/A candidate resolution. No extra model call selects materials.

The supplied full pages and OCR are complementary. Shared document context
may inform material interpretation but does not change object membership.
Source instructions in documents are evidence, never application instructions.
Source assignment, linked legend assignment, visual inference and defaults
retain different provenance and a short decision rationale, not private
chain-of-thought. A source-bound material cannot be economically substituted.

## Construction and uncertainty

A veneered panel is a purchasable board. Finished thickness and purchased
sheet thickness are distinct. A 40-mm member can explicitly assume two
20-mm layers and veneer edge treatment; purchasing counts both layers and
the edge material. It must not silently become one 18-mm sheet or automatically
force every hidden drawer part to 40 mm. Visual similarity is a recorded
derived relationship, never proof of an explicit source thickness.

Fixed decorative members, countertops and supports remain accountable.
Analyze describes repeated panel groups; Calculation measures each group;
the composer expands its quantity. Cabinet defaults remain available for
incomplete drawings, with named provenance and preserved front arrangement.

2VN checks declared axis/projection and numeric consistency, using Dimension
Graph relations only as candidates, not proof of dimension-line ownership.
Rejecting a binding removes its source authority. No maximum
number from an unrelated side view may overwrite an axis. Explicitly linked
same-axis peers may supply a missing dimension; otherwise use a labelled
construction default.

## Project purchasing

Alternatives must be explicitly allowed for hidden construction, with matching
stock thickness and equivalent physical demand. Compare whole-project rounded
purchase totals with the existing aggregate sheet policy and 10% allowance.
This estimates shared sheet capacity; it does not establish usable offcut
shapes or perform manufacturing nesting. Respect user overrides. Persist
selected material, considered costs, rejection reasons and policy limits.
Use bounded deterministic comparisons, not an exponential scenario search.

## Verification gates

- Sparse LF1: three side-by-side drawers; 720-mm depth yields three 600-mm
  slide sets; no screen hinges; fixed panel multiplicity, top and two supports.
- Material legend on a separate page: callout and definition survive Analyze,
  Calculation and persisted BOM with source references; appearance cannot
  override the explicit finish. Unknown references never become source facts.
- 40-mm build-up: two purchased layers plus edge demand, with distinct stock
  and finished thickness; hidden construction can use compatible alternatives.
- Project economics: small hidden demand can share a purchased material;
  introducing cheaper board only wins when its rounded project cost is lower.
- One Analyze for the accepted file and one Calculation per ordinary object;
  large evidence still uses bounded existing Calculation batches and records
  actual calls rather than promising exactly N regardless of input size.
- Baseline and regression suites, live model witness, deployment and owner
  acceptance are separate evidence levels.

## Implementation and protected behavior

The active fact version is `estimation_calculation_v6_1`; older V5 facts cannot
masquerade as V6 output. Analyze is `estimation_analyze_v6_1`. Both use the
existing runtime, private evidence storage, deterministic composer and Material
Engine. No database migration, UI callback, timer, worker or Detection change
is introduced. Production remains at the previous checkpoint until acceptance.

Full source pages are uploaded once per file handoff, including image-only
context pages outside object membership. Analyze receives deduplicated images
and cited text. Calculation receives object geometry pages plus its locked
construction and material evidence chains. A partial retry still includes
already calculated objects as read-only context; it recalculates only pending
objects. The normal path is one Analyze plus one Calculation per object.
Large object page sets retain existing batching and reconciliation calls.

Carcass, fronts, drawer internals, back, countertop and support stock have
separate assignments. Missing hidden roles reuse assigned stock with recorded
single-layer assumptions instead of automatically introducing hardboard or
LDSP. Thickness-source claims require references; an inconsistent stock-layer
build-up is retained as a construction normalization for review. Finish area
is scoped to assigned roles and excludes buried laminate faces. Cut dimensions
remain approximate estimating geometry, not a manufacturing cut list.

Project alternatives are a deterministic greedy comparison, at most three
options per group and 24 trial plans overall. Identical alternative demands
are grouped across objects. Source-bound materials, manually edited norms and
edge-system changes are not automatically substituted. Manual purchase
overrides disable substitution. Both compared choices need usable Company
Catalog or Israel Reference prices; an Assumption Fallback price is not
economic evidence. Decisions and effective material facts are persisted in
the existing purchase-plan snapshot and projected into published line facts.

## Live verification boundary

Local verification on 2026-11-04: 18 new tests added. The final complete suite
returned 1657 passed, 10 failed, 29 warnings in 15.84 seconds. Before edits,
the same suite returned 1639 passed and the same 10 failures. No new failing
test remains. `git diff --check` and compilation of the changed core modules
and replay tool passed. These durations measure tests, not customer latency.

The unchanged baseline failures are:

- `test_processing_uses_only_bounded_browser_handshake_after_complete_marker`
- `test_yellow_company_item_cannot_silently_supply_an_estimate_price`
- `test_shadow_handoff_uses_source_page_when_image_only_ocr_cannot_resolve_anchor`
- `test_shadow_handoff_falls_back_to_full_page_for_invalid_preview_bbox`
- `test_shadow_handoff_reuses_detection_preview_and_persists_full_evidence_page`
- `test_drawer_slide_without_nominal_length_is_yellow_not_review_or_red`
- `test_furniture_profile_identity_does_not_require_wall_thickness`
- `test_identity_normalizer_retains_only_domain_attributes_not_source_prose`
- `test_policy_seed_uses_current_family_code_and_only_approved_price_key_facts`
- `test_mdf_policy_keeps_actual_facing_classes_separate`

New tests cover source/legend provenance, shared page/text deduplication,
image-only context outside object membership, locked material roles and drawer
arrangement, stock layers/edge demand, finish area, fixed rib groups, purchased
supports, numeric 2VN rejection, shared project economics and manual restoration.
Mocked runtime tests verify one shared Analyze, one Calculation per pending
object, one download per shared page and complete context on a partial retry.

Read-only production lookup identified the latest LF1 immutable input as
`db175c9d-b911-434e-a3ed-de612640f96f`, created 2026-11-04 18:49:39 UTC.
No production facts, estimates or catalogs were changed by the lookup.

`tools/replay_estimation_v6.py` can execute the same Analyze, Calculation, 2VN,
composer and purchasing path while saving results only to a fresh local JSON.
Its default mode is read-only; `--execute` enables paid provider calls.
The execution attempt was rejected by access review before the process started:
explicit owner approval is required to send LF1 evidence to Anthropic and incur
the calls. This is not a successful model witness or a model-quality failure.
Approval was requested; no alternative transport or bypass was attempted.

Pending acceptance: a real LF1 model witness, then a multi-object / separate
legend witness, followed by authenticated production behavior and owner review.
Large-file latency and actual model interpretation are not established by
mocked orchestration tests. No global-optimum or usable-offcut claim is made.
