# Approved defaults and final implementation rules

This document is the single current decision record for the remaining default
work. It supersedes the former `faced_mdf` section: faced MDF is no longer a
Family. Raw MDF, HDF and faced MDF are subfamilies of `mdf_hdf`.

## What is already applied

- `mdf_hdf` Pricing Key is `board_type`, `surface`, `thickness`.
- Active default positions exist for raw MDF 17 mm, raw HDF 8 mm, generic
  laminated MDF 17 mm and two-sided veneered MDF 18 mm.
- The active Israel catalog contains no 17-mm explicit melamine or explicit
  veneer listing. Defaults therefore must be an explicit fallback policy, not
  a claim that such a market position exists.

## MDF and HDF fallback policy

Input evidence is retained. A user saying `melamine one-sided` is not rewritten
to `laminated` in the evidence. Only the missing thickness is resolved by this
policy:

| Normalized requirement | Missing detail | Default purchase requirement |
| --- | --- | --- |
| MDF, raw | thickness | MDF, raw, 17 mm |
| HDF, raw | thickness | HDF, raw, 8 mm |
| MDF, laminated | thickness | MDF, laminated, 17 mm |
| MDF, melamine one-sided | thickness | MDF, laminated, 17 mm |
| MDF, melamine two-sided | thickness | MDF, laminated, 17 mm |
| MDF, veneer one-sided | thickness | MDF, veneer, two-sided, 18 mm |
| MDF, veneer two-sided | thickness | MDF, veneer, two-sided, 18 mm |

`laminated` is a generic surface description. `melamine one-sided` is a more
specific construction and remains such in the normalized requirement. For an
otherwise underspecified request, both use the approved generic 17-mm laminated
MDF fallback. Veneer keeps its own material path and therefore uses the
approved 18-mm veneered MDF fallback. This is deterministic fallback logic,
not a new Israel Reference position.

Explicit thickness always wins. For example, `MDF, melamine one-sided, 16 mm`
must resolve to a compatible 16-mm entry, never to the 17-mm default.

## Hardware

The candidate choices in `HARDWARE_DEFAULT_CANDIDATES.md` were approved, but
they have **not yet been inserted** as active default positions. The pending
implementation has two parts:

1. Store the approved package-price defaults for each hardware Family.
2. Change default selection so a hardware default is allowed to use an active
   `retail_package` price. Material Families continue to require
   `material_only` prices.

This distinction is required because a hinge or door system is purchased as a
piece or set, rather than as a raw material price.

Drawer slides are the deliberate exception. They do not receive a fixed static
default. Material Engine must select the largest standard runner length not
greater than `drawer_depth_mm - 100`. A 600-mm drawer depth therefore selects
a 500-mm runner.

Implementation is tracked as `3.17.3.6 Drawer-slide derived selection` in
`notes/TODO.md`. It is a Resolver and Material Engine rule, not catalog SQL.

## No default by design

- `packaging_material`: calculated overhead, not a material demand.
- `purchased_fabricated_component`: component type is mandatory.

## Remaining catalog decisions before the default layer is complete

The owner approved both remaining static defaults on 2026-10-15. The approved
SQL is `2026_10_15_close_particleboard_and_hardboard_defaults.sql`:

| Family | Approved default |
| --- | --- |
| `particleboard` | P2 furniture-grade raw particleboard, 16 mm, 2440 x 1220 mm |
| `fibreboard_hardboard` | Standard raw hardboard, 3 mm, 2440 x 1220 mm |
