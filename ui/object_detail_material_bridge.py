from pathlib import Path

import streamlit.components.v1 as components


material_edit_bridge = components.declare_component(
    "costerly_object_detail_material_edit",
    path=str(Path(__file__).with_name("object_detail_material_component")),
)
