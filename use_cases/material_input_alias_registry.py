"""Multilingual input grammar for Resolver material families and Pricing Keys.

This is deliberately an *intake* registry, not ``reference_material_aliases``.
The latter names one exact purchasable Israel identity.  A phrase such as
``MDF`` or ``стальной профиль`` only proves a material family and must never
select a particular offer by itself.
"""

from __future__ import annotations

from typing import Mapping, Sequence


# Every active Catalog V2 family has input terminology in English, Russian and
# Hebrew.  The canonical family code remains the only resolver output.
FAMILY_ALIASES: Mapping[str, tuple[str, ...]] = {
    "mdf_hdf": ("mdf", "hdf", "мдф", "хдф", "плита мдф", "панель мдф", "מדפ", "מדי אף"),
    "faced_mdf": ("faced mdf", "laminated mdf", "melamine mdf", "мдф ламинированный", "мдф с покрытием", "מ.ד.פ מצופה", "מדפ מצופה"),
    "particleboard": ("particleboard", "chipboard", "дсп", "древесностружечная плита", "сיבית", "לוח שבבית"),
    "melamine_faced_particleboard": ("ldsp", "melamine faced particleboard", "melamine board", "ламинированное дсп", "лдсп", "меламиновая плита", "סיבית מלמין", "לוח מלמין"),
    "plywood": ("plywood", "ply", "фанера", "фанерный лист", "לביד", "דיקט", "סנדוויץ", "twin", "combi", "okoume", "okume", "אוקומה", "טווין", "קומבי"),
    "plywood_special": ("marine plywood", "film faced plywood", "fire retardant plywood", "special plywood", "бакелизированная фанера", "морская фанера", "фанера специальная", "לביד ימי", "לביד מיוחד"),
    "osb": ("osb", "oriented strand board", "осб", "ориентированно стружечная плита", "או אס בי"),
    "fibreboard_hardboard": ("hardboard", "fibreboard", "fiberboard", "оргалит", "двп", "мезонит", "מזונית", "הארדבורד"),
    "lightweight_sandwich_panel": ("lightweight panel", "sandwich panel", "honeycomb panel", "лёгкая панель", "сэндвич панель", "сотовая панель", "לוח סנדוויץ", "לוח כוורת"),
    "hpl_cpl": ("hpl", "cpl", "high pressure laminate", "ламинат hpl", "пластик hpl", "פורמייקה", "hpl"),
    "compact_laminate": ("compact laminate", "compact hpl", "компакт ламинат", "компакт плита", "קומפקט", "לוח קומפקט"),
    "wood_veneer": ("wood veneer", "veneer", "шпон", "натуральный шпон", "פורניר", "ציפוי עץ"),
    "edge_banding": ("edge banding", "edge band", "edgeband", "кромка", "кромочная лента", "пвх кромка", "abs кромка", "קנט", "פס קנט"),
    "decorative_film_foil": ("decorative film", "decorative foil", "плёнка декоративная", "пвх плёнка", "фольга декоративная", "יריעת דקור", "נייר דקורטיבי"),
    "timber_solid_wood_panel": ("solid wood", "solid timber", "furniture panel", "butcher block", "массив дерева", "мебельный щит", "дубовый щит", "доска массив", "עץ מלא", "לוח עץ מלא", "בוצ'ר"),
    "sheet_metal": ("sheet metal", "metal sheet", "steel sheet", "plate", "листовой металл", "лист стали", "листовой прокат", "профлист", "פח", "לוח מתכת"),
    "metal_tube": ("round tube", "round pipe", "circular tube", "круглая труба", "труба круглая", "צינור עגול", "צינור"),
    "metal_profile_angle_channel": ("metal profile", "angle iron", "metal angle", "metal channel", "профиль металлический", "уголок металлический", "швеллер", "п образный профиль", "профиль уголок", "פרופיל מתכת", "זווית", "תעלה", "פרופיל u", "פרופיל c"),
    "metal_flat_bar": ("flat bar", "steel strip", "flat steel", "полоса стальная", "полоса металлическая", "плоская полоса", "פס שטוח", "פס מתכת"),
    "metal_round_bar_rod_wire": ("round bar", "rod", "wire", "metal rod", "круглый пруток", "стержень", "проволока", "мוט עגול", "מוט", "חוט"),
    "glass": ("glass", "sheet glass", "стекло", "листовое стекло", "זכוכית"),
    "mirror": ("mirror", "mirror glass", "зеркало", "зеркальное стекло", "מראה", "זכוכית מראה"),
    "acrylic_pmma": ("acrylic", "pmma", "plexiglas", "perspex", "акрил", "оргстекло", "плексиглас", "אקריל", "פרספקס"),
    "polycarbonate_petg_pvc_abs": ("polycarbonate", "petg", "pvc sheet", "abs sheet", "поликарбонат", "пэтг", "пвх лист", "абс лист", "פוליקרבונט", "פי וי סי", "איי בי אס"),
    "sheet_plastic": ("plastic sheet", "hdpe", "polypropylene sheet", "листовой пластик", "пластиковый лист", "полипропилен", "לוח פלסטיק", "פוליפרופילן"),
    "vinyl_film": ("vinyl film", "vinyl wrap", "самоклеящаяся виниловая плёнка", "виниловая плёнка", "יריעת ויניל", "מדבקת ויניל"),
    "aluminium_composite_panel": ("aluminium composite panel", "aluminum composite", "acp", "acm", "dibond", "алюкобонд", "алюминиевый композит", "אלוקובונד", "לוח קומפוזיט אלומיניום"),
    "composite_sandwich_panel": ("composite panel", "sandwich composite", "композитная панель", "сэндвич композит", "לוח מרוכב", "פנל סנדוויץ"),
    "natural_stone_slab": ("natural stone", "marble", "granite", "quartzite", "натуральный камень", "мрамор", "гранит", "кварцит", "אבן טבעית", "שיש", "גרניט", "קוורציט"),
    "engineered_quartz_mineral_hybrid": ("engineered quartz", "quartz slab", "caesarstone", "искусственный кварц", "кварцевый агломерат", "кварц", "אבן קיסר", "קוורץ"),
    "sintered_ultra_compact_surface": ("sintered stone", "ultra compact", "dekton", "спечённый камень", "ультракомпакт", "дектон", "אבן סינטרית", "דקטון"),
    "porcelain_ceramic_slab": ("porcelain slab", "ceramic slab", "керамогранит", "керамическая плита", "גרניט פורצלן", "לוח קרמיקה"),
    "solid_surface": ("solid surface", "corian", "акриловый камень", "кориан", "אבן אקרילית", "קוריאן"),
    "terrazzo_engineered_agglomerate": ("terrazzo", "agglomerate", "терраццо", "агломерат", "טרצו", "אגלומרט"),
    "paint_lacquer_stain": ("paint", "lacquer", "varnish", "stain", "краска", "лак", "морилка", "צבע", "לכה", "בייץ"),
    "primer": ("primer", "undercoat", "грунт", "грунтовка", "פריימר", "צבע יסוד"),
    "powder_coating": ("powder coating", "powder coat", "порошковая окраска", "порошковая краска", "צביעה באבקה", "אבקת צבע"),
    "filler_hardener_thinner": ("filler", "hardener", "thinner", "putty", "шпатлёвка", "отвердитель", "разбавитель", "מדלל", "מקשה", "שפכטל"),
    "hardware_hinge": ("hinge", "concealed hinge", "cup hinge", "петля", "мебельная петля", "ציר", "ציר נסתר"),
    "hardware_drawer_slide": ("drawer slide", "drawer runner", "drawer rail", "направляющая ящика", "направляющая для ящика", "рельса ящика", "מסילת מגירה", "מסילה למגירה"),
    "hardware_connector": ("furniture connector", "cam lock", "minifix", "дюбель", "конфирмат", "мебельный крепёж", "מחבר", "מיני פיקס", "אקסצנטרי"),
    "hardware_fastener": ("screw", "bolt", "nut", "fastener", "винт", "саморез", "болт", "гайка", "בורג", "אום"),
    "hardware_mounting_part": ("mounting plate", "bracket", "mounting part", "кронштейн", "монтажная пластина", "крепёжная пластина", "תושבת", "פלטת הרכבה"),
    "hardware_handle": ("handle", "knob", "pull", "ручка", "мебельная ручка", "кнопка", "ידית", "כפתור"),
    "hardware_leg_caster": ("furniture leg", "adjustable leg", "caster", "wheel", "ножка мебельная", "регулируемая ножка", "колесо", "рגלית", "גלגל"),
    "hardware_lift_system": ("gas lift", "gas strut", "flap lift", "lift mechanism", "газлифт", "подъёмник", "механизм подъёма", "בוכנת גז", "מנגנון קלפה"),
    "hardware_lock_latch": ("lock", "latch", "door catch", "замок", "защёлка", "магнитная защёлка", "מנעול", "תופסן"),
    "hardware_drawer_system": ("drawer system", "drawer box", "metal drawer", "система ящиков", "метабокс", "тандембокс", "מגירת מתכת", "מריבובוקס"),
    "hardware_storage_system": ("storage system", "pull out system", "система хранения", "выдвижная система", "מערכת אחסון", "מערכת נשלפת"),
    "hardware_door_system": ("door system", "sliding door system", "система дверей", "система раздвижных дверей", "מערכת דלתות", "מערכת דלת הזזה"),
    "hardware_furniture_system": ("furniture system", "cabinet system", "мебельная система", "система мебели", "מערכת ריהוט", "מערכת ארון"),
    "hardware_electrical_component": ("led strip", "led driver", "power supply", "lighting profile", "светодиодная лента", "блок питания", "профиль для ленты", "פס לד", "ספק כח", "פרופיל תאורה"),
    "purchased_fabricated_component": ("fabricated component", "custom component", "изготовленная деталь", "покупной узел", "רכיב מיוצר", "מכלול"),
    "packaging_material": ("packaging", "cardboard", "foam packaging", "упаковка", "картон", "упаковочная плёнка", "אריזה", "קרטון"),
}


# The attribute grammar is intentionally generic.  Values and numbers remain
# source evidence, while this gives the agent and deterministic parsers the
# language needed to identify their role.
PRICING_KEY_ALIASES: Mapping[str, tuple[str, ...]] = {
    "thickness_mm": ("thickness", "thk", "th.", "gauge", "t", "толщина", "толщ.", "тлщ", "עובי"),
    "species": ("species", "wood species", "timber", "порода", "вид древесины", "древесина", "סוג עץ", "מין עץ"),
    "width_mm": ("width", "wide", "ширина", "шир.", "רוחב"),
    "length_mm": ("length", "long", "длина", "дл.", "אורך"),
    "depth_mm": ("depth", "drawer length", "глубина", "длина направляющей", "עומק", "אורך מסילה"),
    "diameter_mm": ("diameter", "dia", "ø", "φ", "диаметр", "диам.", "קוטר"),
    "profile_section": ("section", "profile section", "cross section", "сечение", "размер профиля", "профиль", "חתך", "מידת פרופיל"),
    "metal_type": ("steel", "stainless", "aluminium", "carbon steel", "сталь", "нержавейка", "нержавеющая сталь", "алюминий", "פלדה", "נירוסטה", "אלומיניום"),
    "coating_system": ("coating", "finish", "paint system", "покрытие", "тип окраски", "система окраски", "ציפוי", "מערכת צבע"),
    "stone_type": ("stone type", "stone", "тип камня", "камень", "סוג אבן"),
    "chemistry_product_type": ("product type", "тип продукта", "סוג מוצר"),
    "component_type": ("component type", "тип компонента", "סוג רכיב"),
    "packaging_type": ("packaging type", "тип упаковки", "סוג אריזה"),
}


COMMON_VALUE_ALIASES: Mapping[str, Mapping[str, tuple[str, ...]]] = {
    "metal_type": {
        "carbon steel": ("carbon steel", "mild steel", "steel", "углеродистая сталь", "сталь", "железо", "פלדת פחמן", "פלדה"),
        "stainless steel": ("stainless", "stainless steel", "inox", "нержавейка", "нержавеющая сталь", "нерж", "нержав", "נירוסטה"),
        "aluminium": ("aluminium", "aluminum", "алюминий", "אלומיניום"),
    },
    "species": {
        "oak": ("oak", "дуб", "אלון"),
        "birch": ("birch", "берёза", "береза", "לבנה"),
        "walnut": ("walnut", "орех", "אגוז"),
    },
    "coating_system": {
        "powder coating": ("powder coat", "порошковая окраска", "צביעה באבקה"),
        "semi-matte": ("semi matte", "semi-matt", "полуматовый", "полуматовая", "חצי מט"),
    },
}


def aliases_for_catalog_family(family_code: str) -> tuple[str, ...]:
    return FAMILY_ALIASES.get(str(family_code or ""), ())


def alias_context_for_v3(
    *,
    source_family_to_catalog_family: Mapping[str, str],
    pricing_key_fields_by_family: Mapping[str, Sequence[str]],
) -> dict[str, dict[str, object]]:
    """Return a bounded, family-relevant grammar for one V3 prompt batch."""
    context: dict[str, dict[str, object]] = {}
    for source_family, catalog_family in sorted(source_family_to_catalog_family.items()):
        fields = tuple(pricing_key_fields_by_family.get(source_family) or ())
        context[source_family] = {
            "catalog_family": catalog_family,
            "family_aliases": list(aliases_for_catalog_family(catalog_family)),
            "pricing_key_aliases": {
                field: list(PRICING_KEY_ALIASES.get(field, ()))
                for field in fields
            },
        }
    return context
