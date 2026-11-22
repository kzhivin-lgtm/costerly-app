# V3.3 Front panels material selection

Status: implementation candidate, publication and owner production acceptance pending.
Work continues under the existing Estimation Parts Check objective 3.17.4.6.
Runtime base is main `071593fcdbff06a804ace403ef8c24d535e43b18`, including the
published Objects V2.7 Profile Loading repair and Estimation V3.2 source bindings.
The current checkout also retains its V2.7 publication records at `f93584b8`.

## Approved outcome

Materials offers Front panels selection for each existing source stock group.
Choices are LDSP, Veneered MDF, MDF and Plywood. Door, drawer and lift-up fronts
belong to this class through existing physical roles. An explicitly different
source, such as metal, remains selected with all four replacement types offered.
The current source remains authoritative until a deliberate user choice.

Selecting a material starts one read-only automatic preview using saved Parts,
inputs and the existing catalogs and engine. The existing footer button shows
Calculating while the request is pending. Save changes or APPROVE publishes the
choice and calculation. A late response cannot overwrite a newer selection.
Unrelated drafts retain their established behavior. No new model/OCR call,
timer, observer, database table or permanent preview write is introduced.

## Calculation and persistence

- `use_cases/estimation_front_panels.py` owns the shared role set, source groups,
  allowed material choices, stable demand partitioning and legacy norm mapping.
  Source geometry and counts remain in the immutable Parts Check.
- The existing material adapter applies a selected material before derived edge
  demands, rebuilds the appropriate stock identity and preserves source-group
  ownership. Fronts and body retain shared purchase rounding when their stock
  identity is the same. Original non-front assignments are preserved.
- Choices and front groups live in the existing Material Plan JSON. They enter
  the calculation fingerprint through effective facts. Legacy source facts
  provide controls for older plans. Mixed-row norms are divided by physical
  front/body area instead of assigning the whole old norm to the body.
- Preview and Save validate ownership, group identity and the fixed options.
  Unsupported catalog/thickness combinations use the existing actionable error
  state. A failed preview or save retains the draft and existing saved plan.
- Preview reuses the full Materials/Labor/Overhead calculation with diagnostic
  persistence disabled. Save uses the existing publication and Self Cost paths.
  Objects outside the material edit keep their approvals when their calculated
  cost is unchanged. A new selection made during Save is previewed after the
  accepted save completes, preserving the newer draft and the Saved state.
  Raw MDF replacements allow rotation independently of the original veneer's
  grain evidence. Plywood and veneer keep their grain constraints.
- Coating preparation, coating materials and coating labor are the next
  workstream, as the owner specified. This release adds no new coating charge.

## Protected behavior and verification

The complete selector matrix is in
[the approved scope and scenarios](CASEWORK_FRONTS_MATERIAL_CLASS_PLAN_2026_11_22.md).
All original UI gate suites remain obligatory, including the seven forced
Objects V2.7 Profile ready cases, auth/tenant protection, numerical editing,
save/retry/approval, navigation and full self-cost aggregation.

Targeted verification covers front-only membership, each material choice,
source restoration, original sheet specifications, geometry/count stability,
legacy mixed norms, explicit outside materials and read-only previews.
The Calculation browser suite additionally exercises automatic price and Self
Cost updates, rapid choice changes, preview failure, explicit Save/reopen and
both 1280 px and 390 px layouts.

Network-blocked controls against the current main reproduce original purchase
signatures for all three saved files. Lev1 retains15 lines, Lev2 retains10 and
the accepted V3.2 Adda control retains15. Adda preserves24/133 Parts. All four
front types receive catalog prices on both Adda objects, and selecting Plywood
restores the original2,720.64/8,586.68 ILS base material amounts. These exclude
formula consumables, Labor, Overhead and VAT. Evidence is saved-controls.json.

Initial candidate149480b1 passed its UI gate but was not promoted: additional
saved-file comparisons exposed duplicate derived material IDs. Empty source
sets must not merge edge-tape variants. Surfaces and cutouts of one physical
part also require their own source reference. The fix retains those identities,
checks uniqueness and has two dedicated regressions. The corrected candidate
requires its own complete exact-SHA gates. The new Approve-during-preview
browser case also needed the existing synthetic approval client wired into the
Calculation fixture. No production approval code changed for that setup repair.
No paid request or production project write is used for these controls.

Private evidence is retained in the handoff workspace under
`outputs/front-panels-v3.3/`. Runtime publication requires an exact-SHA successful
UI gate, active trusted no-bypass remote rule, the existing publisher and matching
served Core/Cloudflare build identities. This candidate is not an accepted
production checkpoint until the owner verifies it.
