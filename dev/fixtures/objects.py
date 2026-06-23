from __future__ import annotations


OBJECTS_FIXTURE = {
    "rows": [
        {
            "name": "Curtain rod system with hardware",
            "materials": "steel tubing / metal brackets / mounting hardware / fabric curtains",
            "quantity": 1,
            "self_cost_unit": None,
            "sale_price_unit": None,
            "suggestion": "suggested: SC + 30%",
            "reviewed": False,
        },
    ],
    "project_costs": [
        {
            "name": "Delivery",
            "materials": "project-level cost",
            "quantity": 1,
            "self_cost_unit": None,
            "sale_price_unit": None,
            "suggestion": "suggested: 3% of objects subtotal",
        },
        {
            "name": "Installation",
            "materials": "project-level cost",
            "quantity": 1,
            "self_cost_unit": None,
            "sale_price_unit": None,
            "suggestion": "suggested: 10% of objects subtotal",
        },
    ],
    "summary": {
        "project_price": None,
        "vat": None,
        "total": None,
    },
}
