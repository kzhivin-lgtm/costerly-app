from __future__ import annotations

SPECIFICATION_KEYS = (
    "thickness_mm", "width_mm", "length_mm", "diameter_mm", "wall_thickness_mm",
    "profile_section", "species", "grade", "alloy", "temper", "finish", "surface",
    "color", "coating", "density_class", "fire_rating", "moisture_resistance",
    "supplier_sku",
)
FEATURE_KEYS = (
    "shelf_count", "door_count", "drawer_count", "toe_kick", "back_panel",
    "plumbing_cutout", "installation_scope", "finish", "visible_finish",
    "profile_section_mm", "coating", "open_face", "bend_count", "anchor_count",
)
MANUFACTURING_MEASUREMENT_KEYS = (
    "thickness_mm", "part_count", "sheet_count", "path_length_m", "pass_count",
    "hole_count", "pocket_count", "edge_banding_length_m",
)
MANUFACTURING_FLAG_KEYS = (
    "production_file_ready", "rectangular_parts_only", "single_face_processing",
    "standard_operations_only", "has_freeform_contours", "has_internal_cutouts",
    "has_pockets", "has_horizontal_or_end_drilling", "has_repeated_hole_patterns",
    "has_tight_positional_relationships", "straight_edge_to_edge_cuts_only",
    "rough_finish_acceptable", "material_and_thickness_supported",
)
PURCHASED_SPECIFICATION_KEYS = (
    "width_mm", "depth_mm", "height_mm", "thickness_mm", "material", "finish",
    "cutout_count", "installation_scope",
)
TRANSPORT_FIELDS = frozenset({
    "status", "dimensions_mm", "materials", "features", "manufacturing_features",
    "purchased_components", "source_facts", "review_items",
    "labor_operations",
})
