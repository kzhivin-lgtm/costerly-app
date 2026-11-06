# Estimation V5.1 Cabinet Block and Hardware Contract

Status: implemented locally, pending production witness

Work number: `3.17.4.4`

V6 continuation (3.17.4.5), 2026-11-05: see
`notes/ESTIMATION_V6_2_FRONT_COUNT_CHECKPOINT_2026_11_05.md`.
Front-count r03 is an accepted provisional interpretation experiment, not a
replacement for this downstream construction/hardware contract. Its known
false doors are not certified material demand. The 1000/2000-mm owner hinge
revision below is tested locally and is not claimed deployed by this checkpoint.

## Shared Cabinet Block rulebook, V6 experimental consumers

One rulebook with two sections, not two mandatory new provider stages:

- **CB Front V1** (protected checkpoint): front interpretation/counting and hardware mapping. This
  is the short display name for the exact selected technical prompt
  `estimation_front_count_v6_2_r03`, not a new prompt or renumbered experiment.
  Source: agents/prompts/estimation_front_count_v6_2.md. Historical r01/r02/r04
  identities remain unchanged. Runtime registry: CB_RULEBOOK in
  agents/estimation_understanding_agent.py.
- **CB Front V2** (owner-selected diagnostic, technical r05): agents/prompts/cb_front_v2.md.
  Same Front pass/evidence, adds tabletop_supports with distinct physical legs,
  support scheme and observed-versus-assumed attachment. One visible leg is not
  proof of one total leg. Use all views; common schemes are clues, not count
  defaults or width cutoffs. Leg boxes/IDs are separate from operating fronts
  and totals; hidden inferred legs require uncertainty, not invented boxes.
  Old r03 and r04 identities remain unchanged. No extra production stage.
  V2 is now the default for --count-fronts; --front-supports explicitly selects
  the same version. --front-v1 replays unchanged protected r03.
  Lev1 twice identifies two legs, retained by Planner. Planner grouping varies
  two then three blocks; repeated V1 yields three. Simple grouping dependency
  is not reproduced. Owner accepts either grouping when coverage is preserved.
  Lev1 enum reliability remains open. Lev2 exact enums pass, five drawers/two
  lift-ups retained, no invented legs; 15 hinged plus two unresolved is not
  exact semantic acceptance. Subsequent Planner response truncated at 6000 tokens.
- **CB Planner V1**: proposed chat draft, not executed. It included detailed
  internal-compartment/shared-part reasoning. Owner requested simplification.
- **CB Planner V2** (retained experiment): agents/prompts/cb_planner_v2.md. Group into large practical
  preassembled units, balancing assembly effort against manageable transport.
  No invented hidden partitions, detailed panels, materials or labor. Receives
  original images plus fallible saved Front output. Short blocks/shared-parts
  list with referenced fronts and image-local review boxes. Assembly boundaries
  and transport suitability remain assumptions unless explicitly established.
- **CB Planner V3** (retained diagnostic): agents/prompts/cb_planner_v3.md.
  Same contract/model/evidence as V2. Owner-approved grouping guideline: up to
  three horizontal front positions, four only with a specific reason; vertical
  stacks are not summed, and a corner shares the allowance across both wings.
  Full-height narrow cabinets remain possible. No hard minimum width. Explicit
  source construction takes priority. Always list a worktop separately, once,
  either as its own block or as a shared part spanning several carcasses.
  The front-count grouping limit does not apply to worktops/decorative panels.

- **CB Planner V4** (current diagnostic candidate): agents/prompts/cb_planner_v4.md.
  Same contract/evidence/settings as V3. Identify full-height, exactly
  one-section-wide columns first, keeping vertically stacked content together.
  Do not bridge separate wall/base cabinets or infer a column from a fixed side.
  Lev2 B06 grouping improves and original contract passes, but false B01 tower,
  U-shaped summary and incomplete physical content prevent full acceptance.
  Lev1 follow-up preserves three groups but still reports one leg and invents
  mm units for bare drawing dimensions. Planner schema passes, semantics do not.

Full research checkpoint: notes/ESTIMATION_V6_2_HSL_N68_CHECKPOINT_2026_11_05.md.
Owner benchmark corrected on 2026-11-06: N68 eight hinged doors and SIX
drawers, superseding the earlier four-drawer confirmation. The five lift-up
fronts inferred from triangular marks are not accepted as gas-lift demand.
2026-11-06: CB Planner V7 is a pending, unrun candidate. Owner specifies full
base-run top coverage, full depth to the wall, not the hanging-shelf depth.
This is an estimating default subject to explicit construction, not a universal
furniture fact. Complete carcass localization must not be reduced to front-box
union. Raw N68 V6 contains four drawer IDs in B06, but the owner confirms six:
two lower drawers are omitted already in Front. Box expansion alone cannot
correct the count. Reconcile repeated sections before declaring an assembly.
Owner's crossed-region clarification requires revisiting the earlier column
omission claim; it is not permission to add a duplicate block or promote V6.

CB Planner V5/V6 are retained diagnostic candidates, not selected defaults.
V5 localizes worktops on top/axonometric views. V6 also caps tall blocks at
two tall door leaves across without relaxing one-section-wide columns.
N68 V6 follows both rules but omits a previously represented appliance column;
the diagnostic default remains V4. Exact evidence and review are in
notes/evidence/hsl07-v62-2026-11-05/n68-planner-v5-v6-evidence.json.

Planner V2 failed semantic review. Owner has now accepted abstract segmentation
on the examined simple objects, including alternative two/three Lev1 groupings.
V3/V4 are still NOT verified full-cycle/runtime checkpoints; latest Lev2 truncation
and classification limitations remain open.
V3 first probes improve grouping (Lev1 three blocks; Lev2 nine + worktop), but
retain physical interpretation errors; Lev2 additionally fails front ownership
validation. These are recorded failures/limitations, not patched outputs.
One Planner call per probe consumes an existing Front witness without rerunning
Front. Production Analyze/Calculation orchestration is unchanged. Keep per-run
Front IDs local and record conflicts explicitly rather than dropping them.
The full live results and limitations are in the V6 design record and TODO.

## Scope

V5.1 starts at the immutable `estimation_input_v4` package. Detection identity,
evidence and navigation remain outside its scope. The active path is:

`immutable input -> Dimension Evidence Graph -> Cabinet Block interpretation -> Dimension Resolver -> Structural and Hardware Composer -> Material Engine -> C/I/A`

The graph retains its evidence-only boundary. It supplies source numbers,
native-vector candidates, views and candidate relations. It is not a finished
shop drawing and does not choose a catalog or price.

## Approximate, non-blocking construction rule

An approximate estimate must not stop because an input is incomplete. Every
required block axis resolves in this order:

1. Exact explicit source value.
2. The only source-supported shared axis among compatible cabinet blocks in
   the immutable object.
3. A versioned construction default.

The output records the resulting basis and reason. Peer inference remains
`derived` and retains its source refs. A construction default is `assumption`
and has no false source refs. V5.1 defaults a missing cabinet width, height or
depth to `600`, `720` or `600 mm` respectively. These are estimating defaults,
not production measurements.

Where thickness is not explicit, visible MDF/HDF and hidden LDSP carcass sheet
both default to `18 mm`; backing defaults to `3 mm`. Explicit source material
always overrides a default.

## Cabinet Block

One physical cabinet block carries its envelope, front topology, exposure and
material policy. The visual stage may emit `front_groups` only as:

- `drawer_front`, stacked or side-by-side
- `hinged_facade`, stacked or side-by-side
- `lift_up_facade`, stacked or side-by-side

Only the canonical elevation counts fronts. A perspective can corroborate a
front group but cannot duplicate it. The deterministic composer turns the
block into hidden carcass, backing, conventional drawer structure, visible
fronts and exposed side panels. It does not produce a fabrication cut list.

Visible fronts and declared exposed carcass ends use `visible_sheet`, while
hidden carcass, shelves and drawers use `internal_sheet`. Backing and worktops
are separate demand roles. Paint remains a separately named finish demand
under the established one-standard-set policy until a consumption model is
approved.

## Hardware Block

Hardware belongs to its Cabinet Block and is derived only from front topology:

- Each `drawer_front` creates one `hardware_drawer_slide` purchase **set**.
  Its `depth_mm` is `floor((cabinet_depth_mm - 100) / 100) * 100`.
  `720 mm -> 600 mm`; `650 mm -> 500 mm`.
- Each `hinged_facade` creates individual `hardware_hinge` demands. Owner
  revision 2026-11-05 uses `<=1000 mm: 2`, `>1000 mm: 3`, `>2000 mm: 4` hinges.
  This supersedes the original V5.1 600-mm threshold; exact 2000 mm gets 3.
- Each `lift_up_facade` creates one `hardware_lift_system` purchase **set**.

The visual model recognises physical fronts and their arrangement. The
deterministic Composer applies the rules. The Resolver and Material Engine are
still the sole catalog and price authorities.

## Protected behavior and witness

V4.29 New Estimate navigation and all Detection contracts are protected. V5.1
does not require a schema migration because it retains the existing
`estimation_assembly_bom_v1` persisted envelope and publishes a fresh agent
version, `estimation_assembly_bom_v5_1`.

Local acceptance covers Lev rules in deterministic composition:

- Lev_1: three stacked drawers at 720 mm depth create three 600-mm slide sets.
- Lev_2-style cabinet topology: five drawers at 650 mm create five 500-mm slide
  sets; three 1100-mm hinged facades create nine individual hinges; two lift-up
  facades create two gas-lift sets.
- Missing cabinet depth is derived from the sole source-supported peer depth,
  otherwise a named construction default is used without discarding the block.

Production acceptance remains separate. It requires one owner-approved
cabinet/kitchen input to reach a persisted V5.1 BOM and C/I/A-priced Material
Plan, followed by inspection of front counts, hardware units, depth specs,
assumptions and terminal Object Detail. The V4.29 authenticated navigation
witness is still independently pending.
