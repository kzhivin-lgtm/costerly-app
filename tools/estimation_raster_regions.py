"""Identify and index neutral connected raster regions for Block Locator."""

from collections import deque

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def raster_regions(source):
    clean = source.convert("RGB")
    clean.thumbnail((480, 740), Image.Resampling.LANCZOS)
    width, height = clean.size
    quantized = clean.filter(ImageFilter.MedianFilter(3)).quantize(colors=18)
    palette = quantized.getpalette()
    pixels = quantized.tobytes()
    seen = bytearray(width * height)
    found = []

    for start, color in enumerate(pixels):
        if seen[start] or min(palette[3 * color:3 * color + 3]) > 233:
            continue
        seen[start] = 1
        queue = deque([start])
        region = []
        while queue:
            index = queue.popleft()
            region.append(index)
            x, y = index % width, index // width
            neighbors = (index - 1 if x else -1, index + 1 if x + 1 < width else -1,
                         index - width if y else -1, index + width if y + 1 < height else -1)
            for neighbor in neighbors:
                if neighbor >= 0 and not seen[neighbor] and pixels[neighbor] == color:
                    seen[neighbor] = 1
                    queue.append(neighbor)
        if len(region) >= 120:
            found.append((len(region), color, region))

    mapped = clean.copy()
    draw = ImageDraw.Draw(mapped)
    font = ImageFont.load_default(size=14)
    result = []
    for number, (area, color, region) in enumerate(sorted(found, reverse=True)[:45], 1):
        ident = f"R{number:02}"
        xs = [index % width for index in region]
        ys = [index // width for index in region]
        cx, cy = sum(xs) / area, sum(ys) / area
        label = min(region, key=lambda index: (index % width - cx) ** 2 + (index // width - cy) ** 2)
        result.append({"id": ident, "area": area, "bbox": [min(xs), min(ys), max(xs), max(ys)],
                       "rgb": palette[color * 3:color * 3 + 3], "pixels": region})
        draw.text((label % width, label // width), ident, fill="#004878", font=font,
                  stroke_width=2, stroke_fill="white")

    return clean, mapped, {"size": [width, height], "regions": result}
