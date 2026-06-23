from __future__ import annotations


FILE_REVIEW_FIXTURE = {
    "run": {
        "project_name": "—",
        "partner": "—",
        "file_quality": "detailed_drawings",
        "file_name": "shtora+podves.pdf",
        "pages_detected": "3",
        "source_type": "mixed_package",
        "author": "—",
        "document_date": "—",
        "language": "ru",
        "file_quality_confidence": "82%",
        "run_id": "unknown_project_run_001",
        "status": "intake_parsed",
        "missing_information": [
            "Project name and client information not identified",
            "Author and document date unknown",
            "Material specifications for curtain fabric, rod finish, and mounting hardware not explicitly detailed",
            "Clarify whether rod mounting hardware, brackets, and installation labor are included in scope",
            "Confirm final fabric material and weight specifications for load calculation",
            "Verify attachment method to ceiling structure and any structural coordination requirements",
        ],
    },
    "objects": [
        {
            "name": "Curtain rod system with hardware",
            "quantity": "1",
            "confidence": "85%",
            "dimensions": "W 1600 × D 600 × H 2500 mm",
            "materials": (
                "steel tubing (diameter 20mm); metal brackets; mounting hardware; "
                "fabric curtains"
            ),
            "notes": [
                "Custom curtain rod system with welded steel tubing and curved mounting brackets",
                "Includes two welded tubes (diameter 20mm) with custom-bent configuration",
                "Mounting brackets for ceiling attachment visible",
                "Page 3 shows detail of bracket attachment and tube cross-section",
                "Fabric curtains shown in coordinate detail but treated as separate scope unless custom fabricated by workshop",
                "System includes S-curve profile and appears to be bespoke fabrication with custom bending and welding",
            ],
        }
    ],
}
