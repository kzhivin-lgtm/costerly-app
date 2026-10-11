"""Curated Global Hardware brands and manufacturer Product Systems.

This is source-recognition vocabulary only. It never derives a physical variant
from a supplier SKU or a bare number. The SQL seed carries the same approved
Global registry; a later repository may read that registry dynamically, but
the deterministic Price Source normaliser needs an offline-safe vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareBrandSeed:
    code: str
    canonical_name: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class ProductSystemSeed:
    code: str
    brand_code: str
    family_code: str
    system_kind: str
    canonical_name: str
    aliases: tuple[str, ...]


HARDWARE_BRAND_SEEDS: tuple[HardwareBrandSeed, ...] = (
    HardwareBrandSeed("blum", "Blum", ("blum", "בלום")),
    HardwareBrandSeed("hettich", "Hettich", ("hettich", "הטיך", "הטיש")),
    HardwareBrandSeed("hafele", "Häfele", ("hafele", "häfele", "haefele", "הפלה", "האפהלה")),
    HardwareBrandSeed("grass", "Grass", ("grass", "גראס")),
    HardwareBrandSeed("fgv", "FGV", ("fgv",)),
    HardwareBrandSeed("salice", "Salice", ("salice", "סליצה", "סליצ'ה")),
    HardwareBrandSeed("titus", "Titus", ("titus", "טיטוס")),
    HardwareBrandSeed("sugatsune", "Sugatsune", ("sugatsune", "סוגאטסונה", "סוגצונה")),
    HardwareBrandSeed("accuride", "Accuride", ("accuride", "אקורייד", "אקיורייד")),
    HardwareBrandSeed("dtc", "DTC", ("dtc",)),
    HardwareBrandSeed("kessebohmer", "Kesseböhmer", ("kessebohmer", "kesseböhmer", "קסבוהמר")),
    HardwareBrandSeed("vauth_sagel", "Vauth-Sagel", ("vauth sagel", "vauth-sagel", "וואט סאגל")),
    HardwareBrandSeed("vibo", "Vibo", ("vibo", "ויבו")),
    HardwareBrandSeed("emuca", "Emuca", ("emuca", "אמוקה")),
    HardwareBrandSeed("lamello", "Lamello", ("lamello", "למלו")),
)


# A Product System is the manufacturer-named line which can distinguish a
# fitting before a specific variant has been proven. It is intentionally not a
# supplier item code and does not imply a length, capacity, finish or price.
PRODUCT_SYSTEM_SEEDS: tuple[ProductSystemSeed, ...] = (
    # Blum.
    ProductSystemSeed("blum_movento", "blum", "hardware_drawer_slide", "drawer_runner", "MOVENTO", ("movento", "מובנטו")),
    ProductSystemSeed("blum_tandem", "blum", "hardware_drawer_slide", "drawer_runner", "TANDEM", ("tandem", "טנדם")),
    ProductSystemSeed("blum_legrabox", "blum", "hardware_drawer_system", "drawer_system", "LEGRABOX", ("legrabox",)),
    ProductSystemSeed("blum_merivobox", "blum", "hardware_drawer_system", "drawer_system", "MERIVOBOX", ("merivobox",)),
    ProductSystemSeed("blum_tandembox", "blum", "hardware_drawer_system", "drawer_system", "TANDEMBOX", ("tandembox",)),
    ProductSystemSeed("blum_metabox", "blum", "hardware_drawer_system", "drawer_system", "METABOX", ("metabox",)),
    ProductSystemSeed("blum_aventos", "blum", "hardware_lift_system", "lift_system", "AVENTOS", ("aventos",)),
    ProductSystemSeed("blum_clip_top", "blum", "hardware_hinge", "hinge_system", "CLIP top", ("clip top", "cliptop")),
    ProductSystemSeed("blum_compact", "blum", "hardware_hinge", "hinge_system", "COMPACT", ("compact blum", "blum compact")),
    ProductSystemSeed("blum_revego", "blum", "hardware_door_system", "door_system", "REVEGO", ("revego",)),
    # Hettich.
    ProductSystemSeed("hettich_actro", "hettich", "hardware_drawer_slide", "drawer_runner", "Actro", ("actro",)),
    ProductSystemSeed("hettich_quadro", "hettich", "hardware_drawer_slide", "drawer_runner", "Quadro", ("quadro",)),
    ProductSystemSeed("hettich_avantech_you", "hettich", "hardware_drawer_system", "drawer_system", "AvanTech YOU", ("avantech you", "avantech")),
    ProductSystemSeed("hettich_arcitech", "hettich", "hardware_drawer_system", "drawer_system", "ArciTech", ("arcitech",)),
    ProductSystemSeed("hettich_innotech_atira", "hettich", "hardware_drawer_system", "drawer_system", "InnoTech Atira", ("innotech atira", "innotech")),
    ProductSystemSeed("hettich_multitech", "hettich", "hardware_drawer_system", "drawer_system", "MultiTech", ("multitech",)),
    ProductSystemSeed("hettich_sensys", "hettich", "hardware_hinge", "hinge_system", "Sensys", ("sensys",)),
    ProductSystemSeed("hettich_intermat", "hettich", "hardware_hinge", "hinge_system", "Intermat", ("intermat",)),
    ProductSystemSeed("hettich_veosys", "hettich", "hardware_hinge", "hinge_system", "Veosys", ("veosys",)),
    ProductSystemSeed("hettich_novisys", "hettich", "hardware_hinge", "hinge_system", "Novisys", ("novisys",)),
    ProductSystemSeed("hettich_topline", "hettich", "hardware_door_system", "door_system", "TopLine", ("topline",)),
    ProductSystemSeed("hettich_slideline", "hettich", "hardware_door_system", "door_system", "SlideLine", ("slideline",)),
    ProductSystemSeed("hettich_wingline", "hettich", "hardware_door_system", "door_system", "WingLine", ("wingline",)),
    # Häfele.
    ProductSystemSeed("hafele_matrix", "hafele", "hardware_drawer_system", "drawer_system", "Matrix", ("matrix",)),
    ProductSystemSeed("hafele_metalla", "hafele", "hardware_hinge", "hinge_system", "Metalla", ("metalla",)),
    ProductSystemSeed("hafele_free", "hafele", "hardware_lift_system", "lift_system", "Free", ("hafele free", "free flap")),
    ProductSystemSeed("hafele_slido", "hafele", "hardware_door_system", "door_system", "Slido", ("slido",)),
    ProductSystemSeed("hafele_ixconnect", "hafele", "hardware_connector", "connector_system", "Ixconnect", ("ixconnect",)),
    # Grass.
    ProductSystemSeed("grass_dynapro", "grass", "hardware_drawer_slide", "drawer_runner", "Dynapro", ("dynapro",)),
    ProductSystemSeed("grass_dynaneo", "grass", "hardware_drawer_slide", "drawer_runner", "Dynaneo", ("dynaneo",)),
    ProductSystemSeed("grass_vionaro_v8", "grass", "hardware_drawer_system", "drawer_system", "Vionaro V8", ("vionaro v8",)),
    ProductSystemSeed("grass_vionaro_v13", "grass", "hardware_drawer_system", "drawer_system", "Vionaro V13", ("vionaro v13", "vionaro")),
    ProductSystemSeed("grass_nova_pro_scala", "grass", "hardware_drawer_system", "drawer_system", "Nova Pro Scala", ("nova pro scala",)),
    ProductSystemSeed("grass_nova_pro_one", "grass", "hardware_drawer_system", "drawer_system", "Nova Pro One", ("nova pro one",)),
    ProductSystemSeed("grass_tiomos", "grass", "hardware_hinge", "hinge_system", "Tiomos", ("tiomos",)),
    ProductSystemSeed("grass_nexis", "grass", "hardware_hinge", "hinge_system", "Nexis", ("nexis",)),
    ProductSystemSeed("grass_omni", "grass", "hardware_hinge", "hinge_system", "Omni", ("omni grass", "grass omni")),
    # FGV.
    ProductSystemSeed("fgv_aerowing", "fgv", "hardware_lift_system", "lift_system", "AeroWing", ("aerowing",)),
    ProductSystemSeed("fgv_aerolift_up", "fgv", "hardware_lift_system", "lift_system", "AeroLift Up", ("aerolift up",)),
    ProductSystemSeed("fgv_aerolift_down", "fgv", "hardware_lift_system", "lift_system", "AeroLift Down", ("aerolift down",)),
    ProductSystemSeed("fgv_aerolift_slim", "fgv", "hardware_lift_system", "lift_system", "AeroLift Slim", ("aerolift slim",)),
    # Salice.
    ProductSystemSeed("salice_silentia", "salice", "hardware_hinge", "hinge_system", "Silentia+", ("silentia", "silentia+")),
    ProductSystemSeed("salice_conecta", "salice", "hardware_hinge", "hinge_system", "Conecta", ("conecta",)),
    ProductSystemSeed("salice_air", "salice", "hardware_hinge", "hinge_system", "Air", ("salice air",)),
    ProductSystemSeed("salice_lapis", "salice", "hardware_hinge", "hinge_system", "Lapis", ("salice lapis",)),
    ProductSystemSeed("salice_progressa", "salice", "hardware_drawer_slide", "drawer_runner", "Progressa", ("progressa",)),
    ProductSystemSeed("salice_futura", "salice", "hardware_drawer_slide", "drawer_runner", "Futura", ("salice futura",)),
    ProductSystemSeed("salice_unica", "salice", "hardware_drawer_slide", "drawer_runner", "Unica", ("salice unica",)),
    ProductSystemSeed("salice_lineabox_easy", "salice", "hardware_drawer_system", "drawer_system", "Lineabox Easy", ("lineabox easy", "lineabox")),
    ProductSystemSeed("salice_wind", "salice", "hardware_lift_system", "lift_system", "Wind", ("salice wind",)),
    ProductSystemSeed("salice_evolift", "salice", "hardware_lift_system", "lift_system", "Evolift", ("evolift",)),
    ProductSystemSeed("salice_pacta", "salice", "hardware_lift_system", "lift_system", "Pacta", ("pacta",)),
    ProductSystemSeed("salice_exedra", "salice", "hardware_door_system", "door_system", "Exedra", ("exedra",)),
    ProductSystemSeed("salice_slider", "salice", "hardware_door_system", "door_system", "Slider", ("salice slider",)),
    ProductSystemSeed("salice_folder", "salice", "hardware_door_system", "door_system", "Folder", ("salice folder",)),
    # Titus.
    ProductSystemSeed("titus_t_type", "titus", "hardware_hinge", "hinge_system", "T-type", ("t type", "t-type")),
    ProductSystemSeed("titus_b_type", "titus", "hardware_hinge", "hinge_system", "B-type", ("b type", "b-type")),
    ProductSystemSeed("titus_s_type", "titus", "hardware_hinge", "hinge_system", "S-type", ("s type", "s-type")),
    ProductSystemSeed("titus_tekform_slimline", "titus", "hardware_drawer_system", "drawer_system", "Tekform Slimline", ("tekform slimline", "tekform")),
    ProductSystemSeed("titus_tacto", "titus", "hardware_drawer_system", "drawer_system", "Tacto", ("tacto",)),
    ProductSystemSeed("titus_system_5", "titus", "hardware_connector", "connector_system", "System 5", ("system 5",)),
    ProductSystemSeed("titus_system_6", "titus", "hardware_connector", "connector_system", "System 6", ("system 6",)),
    ProductSystemSeed("titus_slidix", "titus", "hardware_door_system", "door_system", "Slidix", ("slidix",)),
    # Sugatsune.
    ProductSystemSeed("sugatsune_hes", "sugatsune", "hardware_hinge", "hinge_system", "HES", ("hes hinge", "hes series")),
    ProductSystemSeed("sugatsune_olympia", "sugatsune", "hardware_hinge", "hinge_system", "OLYMPIA", ("olympia",)),
    ProductSystemSeed("sugatsune_aileron", "sugatsune", "hardware_lift_system", "lift_system", "Aileron", ("aileron",)),
    ProductSystemSeed("sugatsune_lin_x", "sugatsune", "hardware_door_system", "door_system", "Lin-X", ("lin-x", "lin x")),
    ProductSystemSeed("sugatsune_mfu", "sugatsune", "hardware_door_system", "door_system", "MFU", ("mfu",)),
    ProductSystemSeed("sugatsune_fd", "sugatsune", "hardware_door_system", "door_system", "FD", ("fd series",)),
    # Accuride.
    ProductSystemSeed("accuride_1532", "accuride", "hardware_door_system", "door_system", "1532 Pocket Door", ("1532", "1532 pocket door")),
    ProductSystemSeed("accuride_st8200", "accuride", "hardware_drawer_slide", "drawer_runner", "ST8200", ("st8200", "st 8200")),
    ProductSystemSeed("accuride_9308e", "accuride", "hardware_drawer_slide", "drawer_runner", "9308E", ("9308e", "9308 e")),
    ProductSystemSeed("accuride_3932ec", "accuride", "hardware_drawer_slide", "drawer_runner", "3932EC", ("3932ec", "3932 ec")),
    ProductSystemSeed("accuride_c4170", "accuride", "hardware_drawer_slide", "drawer_runner", "C4170", ("c4170", "c 4170")),
    # DTC.
    ProductSystemSeed("dtc_d_motion", "dtc", "hardware_drawer_slide", "drawer_runner", "D-MOTION", ("d-motion", "d motion")),
    ProductSystemSeed("dtc_magic_move", "dtc", "hardware_drawer_slide", "drawer_runner", "MAGIC-MOVE", ("magic-move", "magic move")),
    ProductSystemSeed("dtc_super_rail", "dtc", "hardware_drawer_slide", "drawer_runner", "SUPER-RAIL", ("super-rail", "super rail")),
    ProductSystemSeed("dtc_pure_box", "dtc", "hardware_drawer_system", "drawer_system", "PURE-BOX", ("pure-box", "pure box")),
    ProductSystemSeed("dtc_magic_star_ultra", "dtc", "hardware_drawer_system", "drawer_system", "MAGIC-STAR ULTRA", ("magic-star ultra", "magic star ultra")),
    ProductSystemSeed("dtc_pivot_pro", "dtc", "hardware_hinge", "hinge_system", "PIVOT-PRO", ("pivot-pro", "pivot pro")),
    ProductSystemSeed("dtc_top_stays", "dtc", "hardware_lift_system", "lift_system", "TOP-STAYS", ("top-stays", "top stays")),
    ProductSystemSeed("dtc_track_pro", "dtc", "hardware_door_system", "door_system", "TRACK-PRO", ("track-pro", "track pro")),
    # Kesseböhmer.
    ProductSystemSeed("kessebohmer_lemans", "kessebohmer", "hardware_storage_system", "storage_system", "LeMans", ("lemans", "le mans")),
    ProductSystemSeed("kessebohmer_dispensa", "kessebohmer", "hardware_storage_system", "storage_system", "DISPENSA", ("dispensa",)),
    ProductSystemSeed("kessebohmer_tandem", "kessebohmer", "hardware_storage_system", "storage_system", "TANDEM", ("kessebohmer tandem",)),
    ProductSystemSeed("kessebohmer_conero", "kessebohmer", "hardware_storage_system", "storage_system", "CONERO", ("conero",)),
    ProductSystemSeed("kessebohmer_imove", "kessebohmer", "hardware_storage_system", "storage_system", "iMove", ("imove",)),
    ProductSystemSeed("kessebohmer_freelift", "kessebohmer", "hardware_lift_system", "lift_system", "FREElift", ("freelift",)),
    ProductSystemSeed("kessebohmer_freespace", "kessebohmer", "hardware_lift_system", "lift_system", "FREEspace", ("freespace",)),
    ProductSystemSeed("kessebohmer_freeslim", "kessebohmer", "hardware_lift_system", "lift_system", "FREEslim", ("freeslim",)),
    # Vauth-Sagel.
    ProductSystemSeed("vauth_sagel_vs_envi", "vauth_sagel", "hardware_storage_system", "storage_system", "VS ENVI", ("vs envi",)),
    ProductSystemSeed("vauth_sagel_vs_cor", "vauth_sagel", "hardware_storage_system", "storage_system", "VS COR", ("vs cor",)),
    ProductSystemSeed("vauth_sagel_vs_sub", "vauth_sagel", "hardware_storage_system", "storage_system", "VS SUB", ("vs sub",)),
    ProductSystemSeed("vauth_sagel_vs_tal", "vauth_sagel", "hardware_storage_system", "storage_system", "VS TAL", ("vs tal",)),
    ProductSystemSeed("vauth_sagel_vs_top", "vauth_sagel", "hardware_storage_system", "storage_system", "VS TOP", ("vs top",)),
    ProductSystemSeed("vauth_sagel_vs_wash", "vauth_sagel", "hardware_storage_system", "storage_system", "VS WASH", ("vs wash",)),
    # Vibo.
    ProductSystemSeed("vibo_jino", "vibo", "hardware_storage_system", "storage_system", "Jino", ("jino",)),
    ProductSystemSeed("vibo_fly_moon", "vibo", "hardware_storage_system", "storage_system", "Fly Moon", ("fly moon",)),
    ProductSystemSeed("vibo_fly_box", "vibo", "hardware_storage_system", "storage_system", "Fly Box", ("fly box",)),
    ProductSystemSeed("vibo_spacelock", "vibo", "hardware_storage_system", "storage_system", "SpaceLock", ("spacelock", "space lock")),
    ProductSystemSeed("vibo_cleanspace", "vibo", "hardware_storage_system", "storage_system", "CleanSpace", ("cleanspace", "clean space")),
    ProductSystemSeed("vibo_konmodo", "vibo", "hardware_storage_system", "storage_system", "KonModo", ("konmodo", "kon modo")),
    # Emuca.
    ProductSystemSeed("emuca_silver", "emuca", "hardware_drawer_slide", "drawer_runner", "Silver", ("emuca silver", "silver concealed")),
    ProductSystemSeed("emuca_integrity", "emuca", "hardware_drawer_slide", "drawer_runner", "Integrity", ("emuca integrity",)),
    ProductSystemSeed("emuca_brave", "emuca", "hardware_drawer_slide", "drawer_runner", "Brave", ("emuca brave",)),
    ProductSystemSeed("emuca_t30", "emuca", "hardware_drawer_slide", "drawer_runner", "T30", ("t30", "t 30")),
    ProductSystemSeed("emuca_vertex", "emuca", "hardware_drawer_system", "drawer_system", "Vertex", ("emuca vertex",)),
    ProductSystemSeed("emuca_hack", "emuca", "hardware_drawer_system", "drawer_system", "Hack", ("emuca hack",)),
    ProductSystemSeed("emuca_flow", "emuca", "hardware_door_system", "door_system", "Flow", ("emuca flow",)),
    ProductSystemSeed("emuca_concepta", "emuca", "hardware_door_system", "door_system", "Concepta", ("emuca concepta",)),
    ProductSystemSeed("emuca_placard", "emuca", "hardware_door_system", "door_system", "Placard", ("emuca placard",)),
    ProductSystemSeed("emuca_mechanism_doors", "emuca", "hardware_lift_system", "lift_system", "Mechanism doors", ("emuca mechanism doors",)),
    # Lamello.
    ProductSystemSeed("lamello_p_system", "lamello", "hardware_connector", "connector_system", "P-System", ("p system", "p-system")),
    ProductSystemSeed("lamello_system", "lamello", "hardware_connector", "connector_system", "Lamello System", ("lamello system",)),
    ProductSystemSeed("lamello_cabineo", "lamello", "hardware_connector", "connector_system", "Cabineo", ("cabineo",)),
    ProductSystemSeed("lamello_invis_mx2", "lamello", "hardware_connector", "connector_system", "Invis Mx2", ("invis mx2", "invis m x2")),
)


BRAND_NAME_BY_CODE = {seed.code: seed.canonical_name for seed in HARDWARE_BRAND_SEEDS}
