# Estimation V5.1 Cabinet Block and Hardware Contract

Status: implemented locally, pending production witness

Work number: `3.17.4.4`

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
- Each `hinged_facade` creates individual `hardware_hinge` demands. V5.1 uses
  the construction rule `<=600 mm: 2`, `>600 mm: 3`, `>2000 mm: 4` hinges.
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
