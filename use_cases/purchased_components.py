from __future__ import annotations

from dataclasses import dataclass


PURCHASED_FABRICATED_COMPONENT = "purchased_fabricated_component"
IN_HOUSE_MANUFACTURING = "in_house_manufacturing"
IN_HOUSE_LABOR = "in_house_labor"


@dataclass(frozen=True)
class ExternalProcessPolicy:
    process_code: str
    machinery_capabilities: tuple[str, ...]
    default_route: str


# Uses only the approved Company Profile Machinery subset. A missing capability
# means the process defaults to a subcontractor, not that Machinery should grow.
EXTERNAL_PROCESS_POLICIES = {
    policy.process_code: policy
    for policy in (
        ExternalProcessPolicy("cnc_router", ("CNC router",), "profile_route"),
        ExternalProcessPolicy(
            "sheet_laser", ("Sheet metal laser cutter",), "profile_route"
        ),
        ExternalProcessPolicy("stone_fabrication", (), "subcontractor"),
        ExternalProcessPolicy("glass_fabrication", (), "subcontractor"),
        ExternalProcessPolicy(
            "powder_coating", ("Powder coating",), "profile_route"
        ),
        ExternalProcessPolicy(
            "spray_finishing", ("Spray painting",), "profile_route"
        ),
        ExternalProcessPolicy(
            "press_brake_bending", ("Sheet metal bending",), "profile_route"
        ),
        ExternalProcessPolicy(
            "sheet_rolling", ("Metal rolling",), "profile_route"
        ),
        ExternalProcessPolicy(
            "tube_bending", ("Tube / profile bending",), "profile_route"
        ),
        ExternalProcessPolicy(
            "metal_machining",
            ("Solid metal machining",),
            "profile_route",
        ),
        ExternalProcessPolicy("welding", (), "subcontractor"),
        ExternalProcessPolicy("deburring_grinding", (), "subcontractor"),
        ExternalProcessPolicy("drilling_tapping", (), "subcontractor"),
        ExternalProcessPolicy("sandblasting", ("Sandblasting",), "profile_route"),
        ExternalProcessPolicy("galvanizing", ("Galvanizing",), "profile_route"),
        ExternalProcessPolicy("upholstery", (), "subcontractor"),
        ExternalProcessPolicy("waterjet", (), "subcontractor"),
        ExternalProcessPolicy("metal_finishing", (), "subcontractor"),
    )
}


def classify_process_cost(*, process_code: str, route: str) -> str:
    """Classify a process cost from the customer company's perspective."""
    if process_code not in EXTERNAL_PROCESS_POLICIES:
        raise ValueError(f"Unsupported external process: {process_code}")
    if route == "subcontractor":
        return PURCHASED_FABRICATED_COMPONENT
    if route == "in_house":
        return IN_HOUSE_MANUFACTURING
    if route == "manual":
        return IN_HOUSE_LABOR
    raise ValueError(f"Unsupported production route: {route}")


def price_scope_for_classification(classification: str) -> str | None:
    if classification == PURCHASED_FABRICATED_COMPONENT:
        return "fabricated_component"
    return None
