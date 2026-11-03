# Estimation V5.3, 2VN Geometry Contract

Status: implemented locally, pending production Lev 1 and Lev 2 witnesses

## Purpose

V5.3 inserts 2VN geometry resolution between visual Cabinet Block
interpretation and deterministic Structural BOM composition.  2VN means two
bounded views of a dimension:

1. The visual response identifies the orthographic drawing view and local
   line orientation.
2. The deterministic resolver verifies the declared number against immutable
   Dimension Graph OCR, view and native-vector candidates.

This is not a cabinet CAD engine.  It prevents a nearby numeric label from
silently becoming a global width, depth or height, while preserving the
approximate and non-blocking Estimation contract.

## Rules

- A front elevation maps horizontal dimensions to width and vertical dimensions
  to height.
- A side elevation maps horizontal dimensions to depth and vertical dimensions
  to height.
- A top plan declares whether its horizontal direction is width or depth.
- Isometric views can confirm construction but cannot be the sole numeric axis
  source.
- A direct dimension is promoted to source geometry only when its visual
  binding, immutable graph witness and normalized numeric value agree.
- The fallback order is direct source, cross-view derivation, linked-zone
  derivation, then an explicit construction default. Estimation never stops on
  a missing axis.

## Hardware consequence

Hardware remains composed from the resolved cabinet zone, never from the
largest neighbouring assembly.  Drawer slides use
`floor((depth_mm - 100) / 100) * 100`, as purchase sets. Hinges remain pieces
and lift systems remain sets.

## Production acceptance

1. Lev 1 resolves the lower drawer-bank separately from the tall fixed screen,
   producing three 600-mm drawer-slide sets and no screen hardware.
2. Lev 2 resolves the cabinet zones across corresponding views before its
   drawer depth and facade hardware are composed.
3. The persisted V5.3 facts contain a `two_vn` audit with dimension witnesses,
   rejected bindings and the recorded fallback basis for incomplete axes.
