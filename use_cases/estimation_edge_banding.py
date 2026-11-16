"""Shared physical norms for sheet edging in Materials and CNC."""

EDGE_FAMILY = "edge_banding"
EDGE_TAPE_THICKNESS_MM = 0.8
EDGE_TAPE_NAMES = {"melamine": "Melamine edge band", "veneer": "Real wood veneer edge band",
                   "pvc": "PVC edge band"}
_SHEET_FAMILIES = {"melamine_faced_particleboard", "mdf_hdf", "faced_mdf", "plywood", "plywood_special"}
_EXCLUDED_ROLES = {"carcass_back", "frame_backing", "drawer_box_bottom", "tabletop_underlayer"}
# Ends of these horizontal panels are normally fitted between adjacent panels.
_JOINED_ENDS = {"carcass_top", "carcass_bottom", "drawer_box_end", "fixed_open_shelf",
                "plinth_front", "plinth_return", "plinth_visible_run"}


def sheet_edge_run(*, role, family, specifications, length_mm, width_mm, thickness_mm, quantity):
    """Return a provisional tape demand with the finished panel, not its raw layers."""
    if family not in _SHEET_FAMILIES or role in _EXCLUDED_ROLES or not thickness_mm or thickness_mm <= 6:
        return None
    finish = " ".join(str(specifications.get(key) or "") for key in ("surface", "coating")).casefold()
    if "veneer" in finish:
        tape = "veneer"
    elif family == "melamine_faced_particleboard" or "melamine" in finish:
        tape = "melamine"
    elif "hpl" in finish or "formica" in finish:
        tape = "pvc"
    else:
        return None
    tape_width = next((width for width in (24, 45, 65) if width >= thickness_mm + 2), None)
    if tape_width is None:
        return None
    sides = (length_mm, length_mm) if role in _JOINED_ENDS else (length_mm, length_mm, width_mm, width_mm)
    return {
        "panel_thickness_mm": thickness_mm,
        "tape_kind": tape,
        "tape_width_mm": tape_width,
        "metres": round(sum(sides) * quantity / 1000, 6),
        "sides": len(sides) * quantity,
    }
