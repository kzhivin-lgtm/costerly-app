"""Bilingual deterministic taxonomy for supplier price-source rows.

This module deliberately knows nothing about supplier identity, H.P. numbers,
issuer OCR or merge candidates. It receives one extracted line and can only
refine its material category, family and literal product attributes.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from use_cases.material_normalization import (
    IDENTITY_ATTRIBUTE_DEFAULTS,
    canonical_display_name,
    normalize_identity_attributes,
)


@dataclass(frozen=True)
class TaxonomyRule:
    category: str
    family: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class BrandRule:
    """A recognised manufacturer, deliberately scoped to proven categories.

    A brand is preservation evidence, never category evidence.  For example,
    the word ``Blum`` cannot turn unrelated source text into Hardware; it can
    only be retained after ordinary wording already proved a Hardware family.
    """

    brand: str
    categories: tuple[str, ...]
    aliases: tuple[str, ...]


# Keep the four product areas represented by the existing catalog categories:
# Wood (sheets, solid timber, supplies and fittings), Metal, Coating and the
# separate Material Jobs lane.  English and Hebrew aliases resolve to exactly
# the same canonical category/family.
MATERIAL_RULES: tuple[TaxonomyRule, ...] = (
    # Wood, furniture fittings first so a metal hinge never becomes Metal.
    # A push-to-open catch is a closure, never a hinge. Keep it before the
    # broad hinge rule because supplier wording can mention a hinge-compatible
    # door or glass door in the same line.
    TaxonomyRule("Hardware", "door closure", (
        "push-to-open", "push to open", "push latch", "push catch", "touch latch",
        "butterfly latch", "butterfly catch", "פתיחה בלחיצה", "תופסן לחיצה",
        "לחיצה פרפר",
    )),
    # Plinth clips are small hardware components, not drawer runners. The
    # distinct family is retained so the universal hardware-unit rule assigns
    # a piece, while actual rails continue to use a left/right set.
    TaxonomyRule("Hardware", "plinth clip", (
        "plinth clip", "plinth socket", "socle clip", "plinth fitting",
        "toe kick clip", "תופסן סוקל", "תופסן לסוקל", "תופסן סוקל",
        "תופחן סוקל",
    )),
    TaxonomyRule("Hardware", "drawer slide", (
        "drawer slide", "drawer runner", "drawer rail", "undermount", "runner",
        "ball bearing slide", "concealed slide", "soft close slide", "telescopic slide",
        "movento", "tandem", "telescopic runner",
        "מסילת מגירה", "מסילה למגירה", "מסילה תחתית", "מסילה כפולה",
        "מסילה טלסקופית", "מסילה נסתרת", "מסילה כדורים", "מסילות מגירה",
        "מסילות", "מובנטו", "טנדם", "טלסקופית",
    )),
    TaxonomyRule("Hardware", "hinge", (
        "hinge", "hinges", "concealed hinge", "cup hinge", "soft close hinge",
        "piano hinge", "pivot hinge", "ציר", "צירים", "צירי", "ציר ספר",
        "ציר נסתר", "ציר קלפה", "ציר טריקה שקטה",
    )),
    TaxonomyRule("Hardware", "door closure", (
        "door closure", "door closer", "glass door closure", "glass door hinge",
        "glass hinge", "סוגר דלת", "ציר לזכוכית", "ציר דלת זכוכית",
    )),
    TaxonomyRule("Hardware", "mounting plate", (
        "mounting plate", "connector plate", "fixing plate", "hinge plate",
        "mounting bracket", "bracket", "clip", "latch", "shelf support", "shelf pin",
        "shelf hanger", "shelf bracket", "corner bracket", "פלטת חיבור", "פלטת הרכבה",
        "פלטה לציר", "תושבת", "קליפ", "סוגר", "תומך מדף", "מתלה מדף",
        "מתלה ת מדף", "פין מדף", "זוויתן לרהיט",
    )),
    TaxonomyRule("Hardware", "handle", (
        "handle", "knob", "pull", "drawer handle", "cabinet handle", "profile handle",
        "ידית", "ידיות", "כפתור", "כפתורים", "ידית פרופיל",
    )),
    TaxonomyRule("Hardware", "furniture leg", (
        "furniture leg", "cabinet leg", "plinth leg", "adjustable leg", "leveling foot",
        "רגלית", "רגל מתכווננת", "רגל לארון", "רגל מטבח",
    )),
    TaxonomyRule("Hardware", "furniture connector", (
        "connector", "cabinet connector", "cam lock", "confirmat", "dowel",
        "bolt", "furniture screw", "minifix", "connector bolt", "cam fitting",
        "מחבר", "מחברי רהיט", "אקסצנטרי", "דיבל", "בורג רהיטים", "מיני פיקס",
    )),
    TaxonomyRule("Hardware", "lift mechanism", (
        "lift mechanism", "flap lift", "stay lift", "gas strut", "gas spring",
        "soft close damper", "magnetic catch", "מנגנון קלפה", "מנגנון הרמה",
        "בוכנת גז", "קפיץ גז", "בולם טריקה", "תופסן מגנטי",
    )),
    # Wood sheets. Twin and Okoume prove plywood, but are attributes, not brands.
    TaxonomyRule("Wood Sheets", "plywood", (
        "plywood", "lumber core", "sanded plywood", "blockboard", "marine plywood",
        "לביד", "לבידים", "דיקט", "סנדוויץ", "סנדויץ", "לביד ימי", "לוח לבוד",
        "okume", "okoume", "אוקומה", "אוקמה", "twin", "טווין", "combi", "קומבי",
    )),
    TaxonomyRule("Wood Sheets", "mdf", (
        "mdf", "m.d.f", "m d f", "moisture resistant mdf", "fire retardant mdf",
        # Hebrew invoices and OCR use both the spoken abbreviation and the
        # compact printed form. Dotted and spaced forms cover OCR separating
        # the letters without turning an unrelated Hebrew word into MDF.
        "מדי אף", "אמ די אף", "מדפ", "מ.ד.פ", "מ ד פ", "mdf ירוק", "מדפ ירוק",
    )),
    TaxonomyRule("Wood Sheets", "particleboard", (
        "particleboard", "chipboard", "melamine board", "laminated board", "ldsp",
        "סיבית", "מלמין", "שבבית", "לוח מלמין",
    )),
    TaxonomyRule("Wood Sheets", "hardboard", ("hardboard", "hdf", "מזונית", "הארדבורד")),
    TaxonomyRule("Wood Sheets", "osb", ("osb", "oriented strand board", "או אס בי", "לוח שבבי עץ")),
    TaxonomyRule("Wood Sheets", "laminated panel", (
        "laminated panel", "laminated mdf", "laminated plywood", "formica panel", "פורמייקה",
        "לוח מצופה", "לוח למינציה", "לוח פורמייקה",
    )),
    TaxonomyRule("Glass", "glass", ("glass", "mirror", "זכוכית", "מראה")),
    TaxonomyRule("Plastics & Composites", "acrylic sheet", (
        "acrylic", "pmma", "plexiglas", "perspex", "acrylite", "optix",
        "פרספקס", "אקריל", "אקריליק", "פלקסיגלס",
    )),
    TaxonomyRule("Plastics & Composites", "abs sheet", (
        "abs", "איי בי אס", "א ב ס",
    )),
    TaxonomyRule("Plastics & Composites", "polycarbonate sheet", (
        "polycarbonate", "palsun", "tuffak", "פוליקרבונט", "פלסן",
    )),
    TaxonomyRule("Plastics & Composites", "petg sheet", (
        "petg", "vivak", "ויוואק",
    )),
    TaxonomyRule("Plastics & Composites", "pvc sheet", (
        "foam pvc", "foamed pvc", "rigid pvc", "palight", "pvc", "פי וי סי", "פלייט",
    )),
    TaxonomyRule("Plastics & Composites", "plastic sheet", (
        "hdpe", "polypropylene", "pp sheet", "ptfe", "hips", "plastic sheet",
        "לוח פלסטיק", "פוליפרופילן", "פוליאתילן",
    )),
    TaxonomyRule("Plastics & Composites", "vinyl film", (
        "vinyl film", "vinyl wrap", "oracal", "orajet", "oraguard",
        "מדבקת ויניל", "יריעת ויניל", "אורקל",
    )),
    TaxonomyRule("Plastics & Composites", "aluminium composite panel", (
        "aluminium composite", "aluminum composite", "acp", "acm", "alucobond",
        "dibond", "alucore", "alucodual", "alubond", "reynobond",
        "אלוקובונד", "דיבונד", "לוח קומפוזיט אלומיניום", "פנל אלומיניום מרוכב",
    )),
    TaxonomyRule("Plastics & Composites", "composite sandwich panel", (
        "sandwich panel", "honeycomb panel", "frp", "carbon fibre laminate",
        "panel sandwich", "פנל סנדוויץ", "לוח סנדוויץ", "לוח מרוכב", "כוורת אלומיניום",
    )),
    TaxonomyRule("Solid Wood", "solid timber", (
        "solid wood", "timber", "lumber", "plank", "board", "beam", "batten", "slat",
        "butcher block", "glulam", "finger joint", "עץ מלא", "קורה", "קורות", "קרש", "קרשים",
        "לוח עץ", "סרגל", "לטה", "לוחות עץ", "בוצ׳ר", "בוצר", "עץ גושני", "קורות מודבקות",
    )),
    TaxonomyRule("Wood Supplies", "veneer", ("veneer", "wood veneer", "פורניר", "שכבת פורניר")),
    TaxonomyRule("Wood Supplies", "edge banding", ("edge band", "edge banding", "edgeband", "abs edge", "קנט", "קנטים", "פס קנט")),
    # Metal.
    TaxonomyRule("Metal Profiles", "metal tube", (
        "square tube", "rectangular tube", "round tube", "steel tube", "metal tube", "pipe",
        "צינור", "צינור מרובע", "צינור מלבני", "צינור עגול", "צינור פלדה",
    )),
    TaxonomyRule("Metal Profiles", "metal angle", (
        "steel angle", "metal angle", "angle iron", "l angle", "זווית", "זוויתן", "פרופיל זווית",
    )),
    TaxonomyRule("Metal Profiles", "metal channel", (
        "metal channel", "steel channel", "u channel", "c channel", "תעלה", "פרופיל u", "פרופיל c",
    )),
    TaxonomyRule("Metal Profiles", "metal profile", (
        "metal profile", "aluminium profile", "aluminum profile", "profile", "extrusion",
        "פרופיל", "פרופילי", "פרופיל אלומיניום", "פרופיל מתכת",
    )),
    TaxonomyRule("Metal Sheets", "metal sheet", (
        "sheet metal", "steel sheet", "aluminium sheet", "aluminum sheet", "stainless sheet",
        "steel plate", "aluminium plate", "aluminum plate", "פח", "פחים", "לוח אלומיניום", "פח נירוסטה",
    )),
    TaxonomyRule("Metal Supplies", "metal bar", (
        "round bar", "flat bar", "solid bar", "rod", "wire", "rebar", "metal strip",
        "מוט", "פס שטוח", "חוט", "מוט עגול", "ברזל בניין", "פס מתכת",
    )),
    # Coating.
    TaxonomyRule("Paints & Coatings", "powder coating", ("powder coat", "powder coating", "אבקת צבע", "צביעה בתנור")),
    TaxonomyRule("Paints & Coatings", "epoxy coating", ("epoxy paint", "epoxy coating", "אפוקסי", "צבע אפוקסי")),
    TaxonomyRule("Paints & Coatings", "polyurethane coating", ("polyurethane", "pu coating", "פוליאוריתן", "צבע פוליאוריתן")),
    TaxonomyRule("Paints & Coatings", "primer", ("primer", "undercoat", "יסוד", "פריימר", "צבע יסוד")),
    TaxonomyRule("Paints & Coatings", "lacquer", ("lacquer", "varnish", "clear coat", "לכה", "לכות", "לכה שקופה")),
    TaxonomyRule("Paints & Coatings", "paint", ("paint", "colour paint", "acrylic paint", "צבע", "צבעים", "צבע אקרילי")),
    TaxonomyRule("Coating Supplies", "coating material", (
        "stain", "wood stain", "wood filler", "putty", "hardener", "thinner", "sealer", "catalyst",
        "wood oil", "wax", "מרק", "שפכטל", "מדלל", "מקשה", "סילר", "זרז", "בייץ", "שמן עץ", "ווקס",
    )),
)


# The curated catalogue is deliberately multilingual. Each entry has one
# English canonical display name and recognises Latin spelling, Israeli Hebrew
# transliteration, and only safe OCR variants. It is still not a fuzzy
# proper-name detector: an unknown name is preserved as candidate evidence,
# rather than being silently lost or permitted to select a material category.
#
# Israeli distributors are not listed merely because they sell a brand. These
# are product manufacturers or product-system brands. A supplier name belongs
# to supplier matching, not material identity.
BRAND_RULES: tuple[BrandRule, ...] = (
    # Hardware and furniture fittings.
    BrandRule("Blum", ("Hardware",), ("blum", "בלום")),
    BrandRule("Hettich", ("Hardware",), ("hettich", "הטיך", "הטיש")),
    BrandRule("Häfele", ("Hardware",), ("hafele", "häfele", "haefele", "הפלה", "האפהלה")),
    BrandRule("Grass", ("Hardware",), ("grass", "גראס")),
    BrandRule("FGV", ("Hardware",), ("fgv",)),
    BrandRule("Salice", ("Hardware",), ("salice", "סליצה", "סליצ'ה")),
    BrandRule("Titus", ("Hardware",), ("titus", "טיטוס")),
    BrandRule("Sugatsune", ("Hardware",), ("sugatsune", "סוגאטסונה", "סוגצונה")),
    BrandRule("Accuride", ("Hardware",), ("accuride", "אקורייד", "אקיורייד")),
    BrandRule("DTC", ("Hardware",), ("dtc",)),
    BrandRule("Kesseböhmer", ("Hardware",), ("kessebohmer", "kesseböhmer", "קסבוהמר")),
    BrandRule("Vauth-Sagel", ("Hardware",), ("vauth sagel", "vauth-sagel", "וואט סאגל")),
    BrandRule("Vibo", ("Hardware",), ("vibo", "ויבו")),
    BrandRule("Emuca", ("Hardware",), ("emuca", "אמוקה")),
    BrandRule("Lamello", ("Hardware",), ("lamello", "למלו")),
    # Wood sheet manufacturers. Hebrew names are input aliases, not display.
    BrandRule("EGGER", ("Wood Sheets",), ("egger", "אגר")),
    BrandRule("Kronospan", ("Wood Sheets",), ("kronospan", "קרונוספן")),
    BrandRule("Finsa", ("Wood Sheets",), ("finsa", "פינסה")),
    BrandRule("SWISS KRONO", ("Wood Sheets",), ("swiss krono", "swisskrono", "סוויס קרונו", "שוויץ קרונו")),
    BrandRule("Pfleiderer", ("Wood Sheets",), ("pfleiderer", "פפליידרר", "פליידרר")),
    BrandRule("Kaindl", ("Wood Sheets",), ("kaindl", "קאינדל")),
    BrandRule("Sonae Arauco", ("Wood Sheets",), ("sonae arauco", "סונאה אראוקו")),
    BrandRule("Arauco", ("Wood Sheets",), ("arauco", "אראוקו")),
    BrandRule("Unilin", ("Wood Sheets",), ("unilin", "יונילין")),
    BrandRule("Kastamonu", ("Wood Sheets",), ("kastamonu", "קסטמונו")),
    # Edge systems are branded wood supplies, rather than sheet manufacturers.
    BrandRule("REHAU", ("Wood Supplies",), ("rehau", "רהאו")),
    BrandRule("Döllken", ("Wood Supplies",), ("dollken", "döllken", "דולקן")),
    BrandRule("Ostermann", ("Wood Supplies",), ("ostermann", "אוסטרמן")),
    # Metals. AISI is deliberately not here: it is a grade, not a brand.
    BrandRule("Outokumpu", ("Metal Sheets", "Metal Profiles"), ("outokumpu", "אאוטוקומפו")),
    BrandRule("SSAB", ("Metal Sheets", "Metal Profiles"), ("ssab",)),
    BrandRule("ArcelorMittal", ("Metal Sheets", "Metal Profiles"), ("arcelormittal", "ארסלור מיטאל")),
    BrandRule("Novelis", ("Metal Sheets", "Metal Profiles"), ("novelis", "נובליס")),
    BrandRule("Hydro", ("Metal Sheets", "Metal Profiles"), ("norsk hydro", "hydro aluminium", "הידרו")),
    BrandRule("Aluprof", ("Metal Profiles",), ("aluprof", "אלופרוף")),
    BrandRule("Schüco", ("Metal Profiles",), ("schuco", "schüco", "שוקו")),
    BrandRule("Klil", ("Metal Profiles",), ("klil", "קליל")),
    # Flat and architectural glass.
    BrandRule("Guardian", ("Glass",), ("guardian", "גרדיאן")),
    BrandRule("Pilkington", ("Glass",), ("pilkington", "פילקינגטון")),
    BrandRule("AGC", ("Glass",), ("agc",)),
    BrandRule("Saint-Gobain", ("Glass",), ("saint gobain", "saint-gobain", "סנט גוביין")),
    BrandRule("Şişecam", ("Glass",), ("sisecam", "şişecam", "שישקאם")),
    # Coating manufacturers, including durable Israeli paint brands.
    BrandRule("Sayerlack", ("Paints & Coatings", "Coating Supplies"), ("sayerlack", "סיירלאק")),
    BrandRule("Milesi", ("Paints & Coatings", "Coating Supplies"), ("milesi", "מילזי", "מילסי")),
    BrandRule("Renner", ("Paints & Coatings", "Coating Supplies"), ("renner", "רנר")),
    BrandRule("Sirca", ("Paints & Coatings", "Coating Supplies"), ("sirca", "סירקה")),
    BrandRule("ICA", ("Paints & Coatings", "Coating Supplies"), ("ica",)),
    BrandRule("Sherwin-Williams", ("Paints & Coatings", "Coating Supplies"), ("sherwin williams", "sherwin-williams", "שרווין וויליאמס")),
    BrandRule("AkzoNobel", ("Paints & Coatings", "Coating Supplies"), ("akzonobel", "akzo nobel", "אקזו נובל")),
    BrandRule("Tambour", ("Paints & Coatings", "Coating Supplies"), ("tambour", "טמבור")),
    BrandRule("Nirlat", ("Paints & Coatings", "Coating Supplies"), ("nirlat", "נירלט")),
    # Plastics, films and composite panels. The first three are particularly
    # relevant in Israel because Palram manufactures these material families
    # locally; each product brand remains distinct when printed on a source.
    BrandRule("Palram", ("Plastics & Composites",), ("palram", "פלרם")),
    BrandRule("PALSUN", ("Plastics & Composites",), ("palsun", "פלסן")),
    BrandRule("PALIGHT", ("Plastics & Composites",), ("palight", "פלייט")),
    BrandRule("PALCLEAR", ("Plastics & Composites",), ("palclear", "פלקר")),
    BrandRule("PALGLAS", ("Plastics & Composites",), ("palglas", "פלגלס")),
    BrandRule("PLEXIGLAS", ("Plastics & Composites",), ("plexiglas", "פרספקס", "פלקסיגלס")),
    BrandRule("Perspex", ("Plastics & Composites",), ("perspex",)),
    BrandRule("ACRYLITE", ("Plastics & Composites",), ("acrylite",)),
    BrandRule("PLASKOLITE", ("Plastics & Composites",), ("plaskolite",)),
    BrandRule("OPTIX", ("Plastics & Composites",), ("optix",)),
    BrandRule("TUFFAK", ("Plastics & Composites",), ("tuffak",)),
    BrandRule("VIVAK", ("Plastics & Composites",), ("vivak", "ויוואק")),
    BrandRule("VYCOM", ("Plastics & Composites",), ("vycom",)),
    BrandRule("ORAFOL", ("Plastics & Composites",), ("orafol", "אורפול")),
    BrandRule("ORACAL", ("Plastics & Composites",), ("oracal", "oracle", "אורקל")),
    BrandRule("ORAJET", ("Plastics & Composites",), ("orajet", "אוראג'ט")),
    BrandRule("ORAGUARD", ("Plastics & Composites",), ("oraguard", "אוראגארד")),
    BrandRule("ALUCOBOND", ("Plastics & Composites",), ("alucobond", "אלוקובונד")),
    BrandRule("DIBOND", ("Plastics & Composites",), ("dibond", "דיבונד")),
    BrandRule("ALUCORE", ("Plastics & Composites",), ("alucore", "אלוקור")),
    BrandRule("ALUCODUAL", ("Plastics & Composites",), ("alucodual", "אלוקודואל")),
    BrandRule("ALUBOND", ("Plastics & Composites",), ("alubond", "אלובונד")),
    BrandRule("Reynobond", ("Plastics & Composites",), ("reynobond", "ריינובונד")),
)


ATTRIBUTE_RULES: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "substrate": (
        ("plywood", ("plywood", "לביד", "דיקט", "סנדוויץ", "סנדויץ")),
        ("mdf", ("mdf", "m.d.f", "m d f", "מדי אף", "אמ די אף", "מדפ", "מ.ד.פ", "מ ד פ")),
        ("particleboard", ("particleboard", "chipboard", "סיבית", "שבבית")),
        ("hdf", ("hdf", "hardboard", "מזונית", "הארדבורד")),
        ("osb", ("osb", "oriented strand board", "או אס בי")),
    ),
    "species": (
        ("okoume", ("okume", "okoume", "אוקומה", "אוקמה")),
        ("birch", ("birch", "בירץ", "ליבנה")),
        ("pine", ("pine", "אורן")),
        ("oak", ("oak", "אלון")),
        ("poplar", ("poplar", "צפצפה")),
        ("beech", ("beech", "בוק", "אשור")),
        ("ash", ("ash", "מילה")),
        ("maple", ("maple", "מייפל")),
        ("walnut", ("walnut", "אגוז")),
        ("spruce", ("spruce", "אשוחית")),
        ("fir", ("fir", "אשוח")),
        ("cedar", ("cedar", "ארז")),
        ("teak", ("teak", "טיק")),
        ("acacia", ("acacia", "שיטה")),
        ("mahogany", ("mahogany", "מהגוני")),
        ("bamboo", ("bamboo", "במבוק")),
        ("cherry", ("cherry", "דובדבן")),
        ("olive", ("olive", "זית")),
        ("eucalyptus", ("eucalyptus", "אקליפטוס")),
    ),
    "construction": (
        ("twin", ("twin", "טווין", "combi", "קומבי")),
        ("perforated", ("perforated", "perforation", "מחורר", "מבוקע", "בקוע", "מנוקב")),
    ),
    "finish": (
        ("glossy", ("high gloss", "glossy", "gloss", "מבריק")),
        ("matte", ("matte", "matt", "מט")),
        ("rough", ("rough", "textured", "texture", "מחוספס", "טקסטור")),
        ("sanded", ("sanded", "sanding", "שיוף", "משויף")),
        ("polished", ("polished", "polish", "מלוטש")),
        ("mirror", ("mirror", "mirrored", "מראה")),
        ("brushed", ("brushed", "brush finish", "מברש", "מוברש")),
        ("natural", ("natural", "טבעי", "טבעית")),
    ),
    "coating": (
        ("melamine", ("melamine", "מלמין")),
        ("laminated", ("laminated", "laminate", "למינציה", "מצופה")),
        ("formica", ("formica", "פורמייקה", "פורמיקה")),
        ("veneer", ("veneer", "פורניר")),
        ("polymer", ("polymer", "פולימר")),
    ),
    "colour": (
        ("white", ("white", "לבן", "לבנה")),
        ("black", ("black", "שחור", "שחורה")),
        ("grey", ("grey", "gray", "אפור", "אפורה")),
        ("green", ("green", "ירוק", "ירוקה")),
        ("red", ("red", "אדום", "אדומה")),
        ("blue", ("blue", "כחול", "כחולה")),
        ("brown", ("brown", "חום", "חומה")),
        ("beige", ("beige", "בז׳", "בז")),
    ),
    "grade": (
        ("stainless", ("stainless", "נירוסטה", "נירוסט")),
        ("galvanized", ("galvanized", "zinc coated", "מגולוון", "מגלוון")),
        ("treated", ("treated", "impregnated", "מטופל", "מחוטא")),
        ("moisture-resistant", ("moisture resistant", "water resistant", "mr mdf", "דוחה לחות", "עמיד לחות")),
        ("fire-retardant", ("fire retardant", "fire resistant", "fr mdf", "מעכב בעירה", "חסין אש")),
        ("marine", ("marine plywood", "marine grade", "לביד ימי")),
        ("kiln-dried", ("kiln dried", "dried", "יבש", "מיובש")),
        ("rough-sawn", ("rough sawn", "unplaned", "לא מוקצע", "מנוסר")),
        ("planed", ("planed", "מוקצע")),
        ("aluminium", ("aluminium", "aluminum", "אלומיניום")),
        ("carbon-steel", ("carbon steel", "mild steel", "פלדה", "ברזל")),
        ("brass", ("brass", "פליז")),
        ("bronze", ("bronze", "ברונזה")),
        ("copper", ("copper", "נחושת")),
    ),
}

_IDENTITY_ATTRIBUTE_DEFAULTS = IDENTITY_ATTRIBUTE_DEFAULTS


def _literal_sheet_dimensions(text: str) -> tuple[int, int]:
    """Return only dimensions actually written in the source line.

    Some Israeli invoices use ``2* 3100`` or ``1* 3100`` beside sheet names.
    The star is a sheet notation, not a second dimension. A second side is
    accepted only from an explicit ``x`` or ``×`` separator. Otherwise retain
    the single proven span and never invent a square 3100×3100 sheet.
    """
    explicit_pair = re.search(
        r"(?<!\d)([1-5]\d{3})\s*(?:x|×)\s*([1-5]\d{3})(?!\d)",
        text,
        flags=re.IGNORECASE,
    )
    if explicit_pair:
        return int(explicit_pair.group(1)), int(explicit_pair.group(2))
    spans = [
        int(value)
        for value in re.findall(r"(?<!\d)([1-5]\d{3})(?!\d)", text)
    ]
    return (0, spans[0]) if spans else (0, 0)


JOB_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("supplier_cut_and_edge_banding", (
        "cut and edge", "cutting and edge", "cut + edge", "cutting + edge",
        "חיתוך וקנט", "חיתוך וקנטים", "חיתוך + קנט", "חיתוך + קנטים",
        "פס חיתוך וקנט", "פס חיתוך + קנט",
    )),
    ("edge_banding", ("edge band", "edge banding", "edgeband", "קנט", "קנטים")),
    ("cnc_vertical_drilling", ("drilling", "drill", "קידוח")),
    ("cnc_grooving", ("groove", "dado", "חריץ")),
    ("cnc_router_profile_cutting", ("router", "כרסום")),
    ("cnc_panel_processing", ("cnc cutting", "cnc routing", "cnc machining", "עיבוד cnc", "כרסום cnc")),
    ("panel_saw_cutting", ("cutting", "panel saw", "חיתוך", "ניסור")),
    ("carcass_assembly", ("assembly", "הרכבה", "הרכבת", "הרכב")),
    ("wood_planing", ("planing service", "wood planing", "הקצעה")),
    ("veneer_pressing", ("veneer pressing", "veneer press", "כבישת פורניר", "הדבקת פורניר")),
    ("metal_profile_cutting", ("metal profile cutting", "tube cutting", "profile cutting", "חיתוך פרופיל", "חיתוך צינור")),
    ("sheet_laser_cutting", ("laser cutting", "laser cut", "חיתוך לייזר")),
    ("sheet_shearing", ("sheet shearing", "guillotine cutting", "חיתוך גיליוטינה")),
    ("metal_drilling", ("metal drilling", "קידוח מתכת")),
    ("metal_milling", ("metal milling", "כרסום מתכת")),
    ("metal_punching", ("metal punching", "ניקוב מתכת")),
    ("sheet_metal_bending", ("sheet bending", "press brake", "כיפוף פח")),
    ("metal_profile_bending", ("profile bending", "tube bending", "כיפוף פרופיל", "כיפוף צינור")),
    ("mig_mag_welding", ("mig welding", "mag welding", "mig mag", "רתכת mig", "ריתוך mig")),
    ("tig_welding", ("tig welding", "רתכת tig", "ריתוך tig")),
    ("metal_grinding", ("metal grinding", "grinding weld", "השחזת מתכת", "ליטוש ריתוך")),
    ("metal_polishing", ("metal polishing", "polishing metal", "ליטוש מתכת")),
    ("metal_assembly", ("metal assembly", "הרכבת מתכת")),
    ("glass_cutting", ("glass cutting", "mirror cutting", "חיתוך זכוכית", "חיתוך מראה")),
    ("glass_edge_processing", ("glass polishing", "glass edge", "ליטוש זכוכית", "עיבוד קצה זכוכית")),
    ("glass_drilling", ("glass drilling", "קידוח זכוכית")),
    ("glass_tempering", ("glass tempering", "חיסום זכוכית")),
    ("finish_surface_preparation", ("surface preparation", "finish preparation", "הכנה לצבע", "הכנת שטח")),
    ("wood_staining", ("wood staining", "staining service", "ביצוע בייץ", "צביעת בייץ")),
    ("wood_priming", ("wood priming", "priming service", "צביעת יסוד")),
    ("wood_lacquering", ("wood lacquering", "lacquering service", "צביעת לכה")),
    ("wet_spray_painting", ("spray painting", "wet painting", "צביעה רטובה", "צביעה בהתזה")),
    ("powder_coating_application", ("powder coating service", "powder painting", "צביעה באבקה", "צביעה בתנור")),
    ("wet_spray_painting", ("spray booth", "spray lacquer", "צביעה בהתזה", "צביעה באקדח")),
)

# These phrases are unambiguously paid work even when the commercial model
# calls the line a material. They are intentionally narrower than JOB_RULES:
# a bare "edge band" can still be an edge-band roll and must remain a material.
FORCED_OPERATION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("supplier_cut_and_edge_banding", JOB_RULES[0][1]),
    ("edge_banding", (
        "edge banding service", "edge-banding service", "edge banding application",
        "הדבקת קנט", "הדבקת קנטים", "עבודת קנט", "עבודת קנטים",
    )),
    ("cnc_vertical_drilling", ("drilling service", "drilling work", "עבודת קידוח", "שירות קידוח")),
    ("cnc_grooving", ("grooving service", "grooving work", "עבודת חריץ", "שירות חריץ")),
    ("cnc_router_profile_cutting", ("router service", "routing service", "עבודת כרסום", "שירות כרסום")),
    ("cnc_panel_processing", ("cnc cutting service", "cnc routing service", "עיבוד cnc", "שירות cnc")),
    ("carcass_assembly", ("assembly service", "assembly work", "עבודת הרכבה", "שירות הרכבה")),
    ("wood_planing", ("planing service", "wood planing service", "עבודת הקצעה", "שירות הקצעה")),
    ("veneer_pressing", ("veneer pressing service", "עבודת הדבקת פורניר", "שירות כבישת פורניר")),
    ("metal_profile_cutting", ("metal profile cutting service", "tube cutting service", "עבודת חיתוך פרופיל", "שירות חיתוך צינור")),
    ("sheet_laser_cutting", ("laser cutting service", "laser cutting work", "עבודת חיתוך לייזר", "שירות חיתוך לייזר")),
    ("sheet_shearing", ("sheet shearing service", "guillotine cutting service", "עבודת חיתוך גיליוטינה")),
    ("metal_drilling", ("metal drilling service", "עבודת קידוח מתכת", "שירות קידוח מתכת")),
    ("metal_milling", ("metal milling service", "עבודת כרסום מתכת", "שירות כרסום מתכת")),
    ("metal_punching", ("metal punching service", "עבודת ניקוב מתכת", "שירות ניקוב מתכת")),
    ("sheet_metal_bending", ("sheet bending service", "press brake service", "עבודת כיפוף פח", "שירות כיפוף פח")),
    ("metal_profile_bending", ("profile bending service", "tube bending service", "עבודת כיפוף פרופיל", "שירות כיפוף צינור")),
    ("mig_mag_welding", ("mig welding service", "mag welding service", "עבודת ריתוך mig", "שירות ריתוך mig")),
    ("tig_welding", ("tig welding service", "עבודת ריתוך tig", "שירות ריתוך tig")),
    ("metal_grinding", ("metal grinding service", "עבודת השחזת מתכת", "שירות ליטוש ריתוך")),
    ("metal_polishing", ("metal polishing service", "עבודת ליטוש מתכת", "שירות ליטוש מתכת")),
    ("metal_assembly", ("metal assembly service", "עבודת הרכבת מתכת", "שירות הרכבת מתכת")),
    ("glass_cutting", ("glass cutting service", "mirror cutting service", "עבודת חיתוך זכוכית", "שירות חיתוך זכוכית")),
    ("glass_edge_processing", ("glass edge processing service", "עבודת ליטוש זכוכית", "שירות עיבוד זכוכית")),
    ("glass_drilling", ("glass drilling service", "עבודת קידוח זכוכית", "שירות קידוח זכוכית")),
    ("glass_tempering", ("glass tempering service", "עבודת חיסום זכוכית", "שירות חיסום זכוכית")),
    ("finish_surface_preparation", ("surface preparation service", "עבודת הכנה לצבע", "שירות הכנת שטח")),
    ("wood_staining", ("wood staining service", "עבודת בייץ", "שירות צביעת בייץ")),
    ("wood_priming", ("wood priming service", "עבודת צביעת יסוד", "שירות צביעת יסוד")),
    ("wood_lacquering", ("wood lacquering service", "עבודת צביעת לכה", "שירות צביעת לכה")),
    ("wet_spray_painting", ("spray painting service", "wet painting service", "עבודת צביעה רטובה", "שירות צביעה בהתזה")),
    ("powder_coating_application", ("powder coating service", "powder painting service", "עבודת צביעה באבקה", "שירות צביעה בתנור")),
)


def source_row_text(row: Mapping[str, Any]) -> str:
    # Taxonomy is grounded in source wording. A model-supplied family from a
    # previous pass must not create a false species/category proof.
    return str(row.get("raw_description") or row.get("normalized_name") or "").casefold()


_HEBREW_FINAL_FORMS = str.maketrans({
    "ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ",
})
_TAXONOMY_NOISE_RE = re.compile(r"[\u0591-\u05c7'\"׳״`.,;:/\\|()[\]{}+=*_\-]+")
_TAXONOMY_CONNECTORS = {"and", "plus", "with", "ו"}
_OCR_NEAR_COLLISIONS = frozenset({frozenset({"glass", "gloss"})})


def _canonical_taxonomy_text(value: object) -> str:
    """Make literal Hebrew and English evidence comparable without translation.

    Invoice OCR varies punctuation, niqqud, Hebrew final forms and the joined
    conjunction ``ו``. Normalising those forms is deterministic evidence
    handling, unlike guessing a category from an unrelated brand name.
    """
    text = str(value or "").casefold().translate(_HEBREW_FINAL_FORMS)
    text = _TAXONOMY_NOISE_RE.sub(" ", text)
    return " ".join(text.split())


def _without_hebrew_conjunction(token: str) -> str:
    return token[1:] if len(token) > 2 and token.startswith("ו") else token


def _edit_distance_at_most_one(left: str, right: str) -> bool:
    """Return whether two short OCR tokens differ by at most one edit."""
    if left == right:
        return True
    if abs(len(left) - len(right)) > 1:
        return False
    if len(left) == len(right):
        mismatches = sum(a != b for a, b in zip(left, right))
        return mismatches <= 1
    shorter, longer = (left, right) if len(left) < len(right) else (right, left)
    index = 0
    while index < len(shorter) and shorter[index] == longer[index]:
        index += 1
    return shorter[index:] == longer[index + 1:]


def _compound_alias_matches(text: str, alias: str) -> bool:
    """Allow one OCR typo only when a phrase has multiple corroborating words."""
    alias_tokens = [
        token for token in _canonical_taxonomy_text(alias).split()
        if token not in _TAXONOMY_CONNECTORS
    ]
    if len(alias_tokens) < 2:
        return False
    text_tokens = [
        _without_hebrew_conjunction(token)
        for token in _canonical_taxonomy_text(text).split()
    ]
    for alias_token in alias_tokens:
        candidate_tokens = [token for token in text_tokens if token == alias_token]
        if candidate_tokens:
            continue
        # A one-character OCR error in a short Hebrew root is acceptable only
        # because another independent word in the same compound phrase must
        # match too. Single-word aliases never use this fallback.
        if not any(
            len(alias_token) >= 3
            and frozenset({token, alias_token}) not in _OCR_NEAR_COLLISIONS
            and _edit_distance_at_most_one(token, alias_token)
            for token in text_tokens
        ):
            return False
    return True


def _has_alias(text: str, aliases: tuple[str, ...]) -> bool:
    canonical_text = _canonical_taxonomy_text(text)
    for alias in aliases:
        canonical_alias = _canonical_taxonomy_text(alias)
        # A taxonomy token must not match inside another word. In particular,
        # ``stain`` in ``stainless`` is not coating evidence.
        if canonical_alias and re.search(
            rf"(?<!\w){re.escape(canonical_alias)}(?!\w)", canonical_text,
            flags=re.UNICODE,
        ):
            return True
        if _compound_alias_matches(canonical_text, canonical_alias):
            return True
    return False


def material_rule_for_text(text: str) -> TaxonomyRule | None:
    return next((rule for rule in MATERIAL_RULES if _has_alias(text, rule.aliases)), None)


def brand_for_text(text: str, *, category: str) -> str:
    """Return a curated brand only after the material category is proven."""
    return next(
        (
            rule.brand for rule in BRAND_RULES
            if category in rule.categories and _has_alias(text, rule.aliases)
        ),
        "",
    )


_BRAND_CANDIDATE_NOISE = frozenset({
    "aluminium", "aluminum", "assembly", "black", "blue", "box", "closure",
    "door", "drawer", "front", "glass", "grey", "high", "hinge", "internal",
    "large", "left", "mdf", "metal", "okoume", "particleboard", "plywood",
    "profile", "pure", "right", "sheet", "small", "stainless", "transparent",
    "twin", "white", "wood",
})


def _brand_candidate_from_text(text: str) -> str:
    """Keep an unlisted Latin proper-name candidate without classifying by it.

    The catalog is deliberately incomplete. A final two-word title-cased or
    uppercase run such as ``Mario Box`` is useful brand evidence, while
    ordinary title-cased product prose such as ``Glass Door`` is not. The
    candidate remains low-confidence metadata and never changes a category.
    """
    tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9-]*\b", str(text or ""))
    runs: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        is_proper = (
            (len(token) > 1 and token.isupper())
            or (len(token) > 1 and token[0].isupper())
        )
        if is_proper:
            current.append(token)
            continue
        if current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    for run in reversed(runs):
        for index, token in enumerate(run):
            # Product codes are SKU evidence, not a candidate manufacturer.
            # Keeping one in the identity would recreate the same material
            # merely because an invoice has an unknown stock code.
            if any(character.isdigit() for character in token):
                continue
            if token.casefold() in _BRAND_CANDIDATE_NOISE:
                continue
            candidate = run[index:index + 2]
            return " ".join(candidate)
    return ""


def _explicit_technical_grade(text: str) -> str:
    """Extract standards and alloy grades, never treating them as brands."""
    match = re.search(
        r"\b(?:aisi\s*[- ]?)?(?:304l?|316l?|201|430|s[0-9]{3}|st\s*[- ]?37|"
        r"al\s*[- ]?(?:6061|6063|5083))\b",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    value = match.group(0).upper().replace("-", " ")
    if value.startswith("AISI"):
        digits = re.sub(r"\D", "", value)
        return f"AISI {digits}" if digits else ""
    return re.sub(r"\s+", "", value)


def _explicit_profile_primary_attribute(text: str) -> str:
    """Use an explicit profile section as the primary display attribute."""
    match = re.search(
        r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*(?:x|×)\s*(\d{1,3}(?:\.\d+)?)\s*(?:mm|מ[\"״']?מ)?",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    return f"{match.group(1)}×{match.group(2)} mm"


def job_operation_for_text(text: str) -> str | None:
    matches = [
        (len(_canonical_taxonomy_text(alias)), code)
        for code, aliases in JOB_RULES
        for alias in aliases
        if _has_alias(text, (alias,))
    ]
    return max(matches, default=(0, ""))[1] or None


def forced_operation_for_text(text: str) -> str | None:
    """Return a service code only for wording that cannot denote stock."""
    matches = [
        (len(_canonical_taxonomy_text(alias)), code)
        for code, aliases in FORCED_OPERATION_RULES
        for alias in aliases
        if _has_alias(text, (alias,))
    ]
    return max(matches, default=(0, ""))[1] or None


def _explicit_thickness_mm(text: str) -> float:
    match = re.search(
        r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*(?:mm|מ[\"״']?מ)(?!\w)",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    return float(match.group(1)) if match else 0


def apply_operation_taxonomy(row: dict[str, Any]) -> str | None:
    """Repair a material-vs-service model error from literal source wording.

    This deterministic pass has no supplier inputs. It promotes only explicit
    service phrases, preserving bare product phrases such as a PVC edge-band
    roll for the material taxonomy.
    """
    operation_code = forced_operation_for_text(source_row_text(row))
    if not operation_code:
        return None
    row["item_kind"] = "operation_service"
    row["material_type"] = "Other"
    row["material_family"] = "supplier processing"
    if operation_code == "supplier_cut_and_edge_banding":
        row["normalized_name"] = "Cutting and edge banding"
    row["reason_codes"] = sorted(
        set(row.get("reason_codes") or []) | {"taxonomy_operation_service"}
    )
    return operation_code


def _taxonomy_material_name(rule: TaxonomyRule, attributes: Mapping[str, Any]) -> str:
    """Build the shared compact display from structured, proven facts only."""
    return canonical_display_name(rule.family, attributes)


def apply_material_taxonomy(row: dict[str, Any]) -> bool:
    """Apply only literal bilingual evidence to one material row.

    Unknown terms are intentionally retained in the raw line. They cannot undo
    a category independently proven by the remaining text.
    """
    if row.get("item_kind") != "material":
        return False
    text = source_row_text(row)
    rule = material_rule_for_text(text)
    if not rule:
        return False

    source_attributes = dict(row.get("identity_attributes") or {})
    # Taxonomy is now deliberately applied before schema validation. Preserve
    # the strict identity contract even when a rule clears an unsupported model
    # guess or only proves one field.
    attributes = normalize_identity_attributes(source_attributes)
    # A structured field must be explicitly source-proved. The normalizer does
    # not keep stale agent guesses merely because they are grammatical words.
    # They remain in raw evidence, but never identity, merge or display.
    for field in (*ATTRIBUTE_RULES, "surface"):
        attributes.pop(field, None)
    # Display identity must be reconstructed from source evidence as well.
    # A previous model phrase can be helpful context in raw evidence, but it
    # must not keep arbitrary prose alive as an identity attribute.
    attributes["primary_attribute"] = ""
    for field, values in ATTRIBUTE_RULES.items():
        for canonical, aliases in values:
            if _has_alias(text, aliases):
                if field == "construction":
                    # Construction facts compose. A Twin sheet may also be
                    # perforated, and both distinctions belong to its merge
                    # identity, rather than whichever alias appears first.
                    attributes[field] = " ".join(sorted({
                        *str(attributes.get(field) or "").split(), canonical,
                    }))
                    continue
                attributes[field] = canonical
                break
    catalog_brand = brand_for_text(text, category=rule.category)
    existing_brand = str(attributes.get("brand") or "").strip()
    if catalog_brand:
        attributes["brand"] = catalog_brand
        attributes["brand_basis"] = "catalog"
    elif existing_brand:
        # The extractor can retain a source-proved brand that has not reached
        # our curated catalogue yet. It is a candidate, never a category cue.
        attributes["brand"] = existing_brand
        attributes["brand_basis"] = "candidate"
    elif candidate_brand := _brand_candidate_from_text(str(row.get("raw_description") or "")):
        attributes["brand"] = candidate_brand
        attributes["brand_basis"] = "candidate"
    literal_thickness = _explicit_thickness_mm(text)
    if literal_thickness:
        attributes["thickness_mm"] = literal_thickness
    sheet_categories = {
        "Wood Sheets", "Metal Sheets", "Glass", "Plastics & Composites",
    }
    if rule.category in sheet_categories:
        try:
            thickness = float(attributes.get("thickness_mm") or 0)
        except (TypeError, ValueError):
            thickness = 0
        if thickness:
            attributes["primary_attribute"] = (
                f"{int(thickness) if thickness.is_integer() else thickness} mm"
            )
    elif rule.category == "Metal Profiles":
        attributes["primary_attribute"] = _explicit_profile_primary_attribute(text)
    elif rule.category == "Hardware" and not str(attributes.get("primary_attribute") or "").strip():
        try:
            first_dimension = _explicit_thickness_mm(text)
        except (TypeError, ValueError):
            first_dimension = 0
        if first_dimension:
            attributes["primary_attribute"] = (
                f"{int(first_dimension) if first_dimension.is_integer() else first_dimension} mm"
            )
    if technical_grade := _explicit_technical_grade(text):
        attributes["grade"] = technical_grade
    attributes = normalize_identity_attributes(attributes)
    if rule.category in sheet_categories:
        # Model-generated dimensions are not source evidence. Rebuild this
        # pair from literal text so a single 3100 span cannot become 3100×3100
        # or acquire an unrelated 2400 side.
        attributes["width_mm"], attributes["length_mm"] = _literal_sheet_dimensions(text)
    row["identity_attributes"] = attributes
    row["material_type"] = rule.category
    row["material_family"] = rule.family
    canonical_name = _taxonomy_material_name(rule, attributes)
    # Every ingestion route converges on this compact canonical form. Raw
    # supplier prose remains intact in ``raw_description`` for evidence, but
    # secondary non-attributes can neither leak into the catalog nor split a
    # material identity downstream.
    row["normalized_name"] = canonical_name
    reasons = set(row.get("reason_codes") or [])
    reasons.discard("unknown_product_term")
    reasons.add(f"taxonomy_{rule.category.casefold().replace(' ', '_')}")
    row["reason_codes"] = sorted(reasons)
    # Do not override a real pricing, VAT, unit, or arithmetic blocker.  A
    # row unresolved solely because the model did not recognise a term that
    # the deterministic taxonomy does recognise is safe to continue.
    if row.get("status") == "unresolved" and not (reasons & {
        "missing_unit", "ambiguous_unit", "package_conversion_unresolved",
        "line_total_inconsistent", "unit_price_mismatch", "vat_basis_unknown",
        "document_total_mismatch", "ambiguous_material",
    }):
        row["status"] = "ready"
    return True


def normalize_sheet_name(name: object) -> str:
    return re.sub(r"\s+", " ", re.sub(
        r"\b(?:sheet|sheets|panel|board|\d+\s*[- ]?sheet)\b", "", str(name or ""), flags=re.I,
    )).strip(" ,-")
