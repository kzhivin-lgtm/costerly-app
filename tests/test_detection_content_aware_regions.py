from io import BytesIO

from PIL import Image, ImageDraw

from agents.detection_page_images import _build_contextual_drawing_regions


def test_contextual_regions_keep_sheet_context_with_three_islands():
    image = Image.new("RGB", (1000, 1400), "white")
    draw = ImageDraw.Draw(image)
    for index, y in enumerate(range(50, 1320, 24)):
        x = 35 + (index * 17) % 145
        draw.rectangle((x, y, x + 24, y + 21), fill="black")
    for box in ((400, 100, 880, 260), (380, 560, 860, 600), (350, 900, 900, 1220)):
        draw.rectangle(box, outline="black", width=4)
    encoded = BytesIO()
    image.save(encoded, format="JPEG", quality=90)

    regions = _build_contextual_drawing_regions(
        encoded.getvalue(), page_number=11, max_regions=5
    )

    assert [region["region"] for region in regions] == [
        "sheet_context", "drawing_field", "drawing_island_1", "drawing_island_2", "drawing_island_3",
    ]
