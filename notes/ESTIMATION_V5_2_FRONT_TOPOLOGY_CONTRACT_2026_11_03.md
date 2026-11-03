# Estimation V5.2 Front Topology Contract

Status: implemented locally, pending production Lev 1 witness

Work number: `3.17.4.4`

## Why this revision exists

The V5.1 Lev 1 production run `run_b1752d1c73cc4f64be117984d98eb74e`
joined a lower three-drawer bank and a tall fixed slat screen into one box
carcass. It then labelled six fixed slats as `hinged_facade`, producing twelve
hinges and no drawer-slide sets. The run also attached the 430 mm base height
to the cabinet depth, so a derived drawer-slide size would have been wrong.

This is a front-topology classification defect before hardware composition. It
is not a Material Engine or price-selection defect.

## V5.2 rule

The visual Cabinet Block must classify operability before it emits a front
group:

1. A lower shallow landscape row is a separate `drawer_bank`; each shown
   drawer creates one `drawer_front` and one drawer-slide purchase set.
2. A portrait leaf can be a `hinged_facade` only when it visibly closes a
   cabinet bay. A repeated tall strip alone is not a door.
3. A landscape flap closing an upper or middle cabinet opening is a
   `lift_up_facade` and creates a gas-lift set, not hinges.
4. Repeated slats, dividers, screens, decorative overlays and fixed carcass
   panels remain structural assemblies. They create no operating hardware.

For incomplete drawings the estimator stays non-blocking, but it chooses a
fixed structural panel over fabricated hinge, gas-lift or drawer-slide demand.

## Lev 1 acceptance

The lower `1580 x 430 x 720 mm` drawer bank has three side-by-side drawer
fronts. It must produce:

- three `hardware_drawer_slide` sets;
- `depth_mm=600`, from `floor((720 - 100) / 100) * 100`;
- zero hinges and zero gas-lift sets from the tall decorative screen.

The V5.2 deterministic test contains this exact topology. Production
acceptance requires a fresh Lev 1 run with a persisted V5.2 BOM and a visual
inspection of its Object Detail and Material Plan.
