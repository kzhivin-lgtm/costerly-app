from __future__ import annotations


OBJECT_DETAIL_FIXTURE = {
    "object_key": "curtain_rod",
    "name": "Curtain rod system with hardware",
    "quantity": 1,
    "confidence": "85%",
    "preview_label": "Object preview",
    "sections": [
        {
            "title": "Material cost",
            "metrics": [
                ("Cost", 13253),
                ("VAT 18%", 2386),
                ("Total", 15639),
            ],
            "columns": ["Item", "Unit", "Unit cost", "Qty", "Cost"],
            "rows": [
                {"group": "Sheet materials", "item": "Steel tubing, diameter 20mm", "unit": "m", "unit_cost": 180, "qty": 8, "cost": 1440},
                {"group": "Sheet materials", "item": "Curved metal brackets", "unit": "pc", "unit_cost": 240, "qty": 4, "cost": 960},
                {"group": "Hardware", "item": "Ceiling mounting hardware", "unit": "lot", "unit_cost": 420, "qty": 1, "cost": 420},
                {"group": "Consumables / fixings", "item": "Fabric curtain allowance", "unit": "sqm", "unit_cost": 310, "qty": 8, "cost": 2480},
                {"group": "Packaging", "item": "Foam wrap roll", "unit": "roll", "unit_cost": 180, "qty": 1, "cost": 180},
                {"group": "Packaging", "item": "Packing tape", "unit": "roll", "unit_cost": 8.5, "qty": 3, "cost": 26},
            ],
        },
        {
            "title": "Labor cost",
            "metrics": [
                ("Total hours", "42.5 h"),
                ("Cost", 7685),
                ("Employer 25%", 1921),
                ("Total", 9606),
            ],
            "columns": ["Work", "Role", "Hours", "Rate", "Cost"],
            "rows": [
                {"group": "Technical prep / production files", "work": "Site measurement / field survey", "role": "project manager", "hours": 4, "rate": 100, "cost": 400},
                {"group": "CNC operations", "work": "CNC nesting / sheet optimization", "role": "CNC operator", "hours": 2, "rate": 80, "cost": 160},
                {"group": "CNC operations", "work": "CNC cutting / drilling / boring", "role": "CNC operator", "hours": 4, "rate": 80, "cost": 320},
                {"group": "Carpentry", "work": "Edge prep and dry assembly", "role": "carpenter", "hours": 5, "rate": 80, "cost": 400},
                {"group": "Metalworks", "work": "Tube cutting and bending", "role": "metal worker", "hours": 8, "rate": 80, "cost": 640},
                {"group": "Metalworks", "work": "Bracket welding and cleanup", "role": "metal worker", "hours": 6, "rate": 80, "cost": 480},
                {"group": "Assembly", "work": "Dry fit and hardware prep", "role": "carpenter", "hours": 5, "rate": 80, "cost": 400},
                {"group": "Packaging / dispatch", "work": "Packing and loading prep", "role": "worker", "hours": 3, "rate": 60, "cost": 180},
                {"group": "Production contingency", "work": "Production contingency 10%", "role": "all roles", "hours": 3.9, "rate": 79, "cost": 308},
            ],
        },
        {
            "title": "Overhead",
            "metrics": [
                ("Cost", 6974),
                ("VAT", 777),
                ("Total", 7571),
            ],
            "columns": ["Group", "Monthly cost", "Allocation", "Cost"],
            "rows": [
                {"group": "Back-office payroll", "item": "Project manager salary + 25%", "monthly_cost": 16250, "allocation": "42.5h / 2016h", "cost": 343},
                {"group": "Facility / rent / arnona", "item": "Rent", "monthly_cost": 10000, "allocation": "42.5h / 2016h", "cost": 211},
                {"group": "Utilities / safety", "item": "Electricity", "monthly_cost": 7500, "allocation": "42.5h / 2016h", "cost": 158},
                {"group": "Machinery / equipment", "item": "Machine consumables / wear", "monthly_cost": 4500, "allocation": "42.5h / 2016h", "cost": 95},
                {"group": "Software / shop supplies / waste", "item": "Shop supplies / cleaning", "monthly_cost": 1000, "allocation": "42.5h / 2016h", "cost": 21},
                {"group": "Project reserves", "item": "Warranty reserve", "monthly_cost": "5%", "allocation": "5% of self-cost", "cost": 1348},
                {"group": "Project reserves", "item": "Management buffer", "monthly_cost": "5%", "allocation": "5% of self-cost", "cost": 1348},
            ],
        },
    ],
    "self_cost": {
        "title": "Curtain rod self cost (SC)",
        "excl_vat": 27912,
        "vat": 5084,
        "total": 32996,
    },
}
