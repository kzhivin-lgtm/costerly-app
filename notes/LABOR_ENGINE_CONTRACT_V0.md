# Labor engine contract v0

Status: interface specification only. This document does not modify the legacy Estimation Agent, its schema, or production behavior.

## Boundary

The extraction layer reports object facts with evidence. The Labor Engine derives routes, operations, and internal labor hours. A later pricing layer consumes those results. No layer may overwrite the responsibility of another.

```text
source documents -> object facts -> Labor Engine -> labor trace and hours -> pricing
```

## Accepted object input

`estimation_object_facts_v1` is converted by the bounded
`object_facts_v1 -> labor_input_v1` adapter. The extraction contract is not
flattened or weakened for Labor.

```json
{
  "object_id": "cabinet-01",
  "quantity": 1,
  "template_code": "base_cabinet_hinged",
  "template_confidence": "medium",
  "dimensions_mm": {"width": 600, "depth": 560, "height": 720},
  "materials": [
    {
      "family": "particleboard",
      "specification": {"thickness_mm": 18},
      "evidence_refs": ["ocr:ocr-1:p1:b0002"]
    }
  ],
  "features": {
    "shelf_count": 1,
    "door_count": 2,
    "drawer_count": 0,
    "finish": "none",
    "installation_scope": "included"
  },
  "construction_profile": "panel_screw_standard",
  "source_facts": [
    {"path": "dimensions_mm.width", "value": 600, "provenance": "explicit"}
  ]
}
```

`provenance` is one of `explicit`, `derived`, or `assumed_template`. The extraction layer must not submit labor minutes, employee counts, machine rates, supplier prices, free-form drilling counts, or an unconstrained operation list.

## Required company context

```json
{
  "company_id": "...",
  "machinery": ["wood_panel_saw", "wood_edge_bander", "wood_cnc_router"],
  "qualified_roles": ["wood_machine_operator", "cabinetmaker"],
  "machine_attendance_fraction": {"wood_cnc_router": 0.25},
  "route_preferences": {"stone": "external", "glass": "external"}
}
```

The Machinery list is limited to the accepted 16 Company Profile capabilities. In-house, manual, and external routes are mutually exclusive for the same work.

## Labor output

```json
{
  "object_id": "cabinet-01",
  "status": "estimated",
  "labor_lines": [
    {
      "operation_code": "panel_saw_cutting",
      "route": "in_house_machine",
      "role_allocations": [{"role": "wood_machine_operator", "hours": 0.42}],
      "baseline_version": "labor_time_v0",
      "baseline_confidence": 40,
      "input_drivers": {"panel_count": 6, "linear_cut_m": 14.4},
      "formula": "max(min_batch, setup + rate * quantity)",
      "provenance": ["template:base_cabinet_hinged", "connection:panel_screw_standard"],
      "explanation": "Panel-saw route selected because a qualified in-house panel saw is available."
    }
  ],
  "purchased_components": [],
  "review_items": []
}
```

`status` is `estimated`, `partial_review`, or `review_required`. Every non-trivial assumption must be exposed through provenance or a review item.

## Non-negotiable invariants

1. Identical inputs, catalog version, and company context produce identical output.
2. Every labor line exposes its route, formula, drivers, baseline version, confidence, and provenance.
3. An external component generates zero internal labor and machine cost for the same work.
4. Labor output contains no money, labor rate, overhead, or margin.
5. Confidence never silently changes calculated time.
6. Missing route-critical facts produce `partial_review` or `review_required`, never fabricated precision.
7. Delivery, vehicle loading and site installation are sales-price additions,
   not Labor Engine self-cost operations. `installation_scope` cannot change
   the Labor Engine trace.
