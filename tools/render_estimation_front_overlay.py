"""Deterministic visualization of model boxes on exact request images. No API calls."""
import argparse
import base64
from io import BytesIO
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from agents.estimation_understanding_agent import validate_front_count, ISLAND_TYPES
from agents.estimation_v4_1_material_facts_agent import _json_object

COLORS = {'hinged': '#2563eb', 'drawer': '#059669', 'lift_up': '#d97706',
          'unresolved': '#9333ea', 'excluded': '#e11d48'}


def decode_evidence_images(request):
    pages, details, pending = {}, {}, None
    for message in request['messages']:
        for block in message['content']:
            if block['type'] == 'text':
                try:
                    meta = json.loads(block['text'])
                except (ValueError, TypeError):
                    continue
                if isinstance(meta, dict) and 'detail_of_existing_view' in meta:
                    pending = ('detail', meta)
                elif isinstance(meta, dict) and 'view_regions' in meta and 'displayed_image_pixels' in meta:
                    pending = ('page', meta)
            elif block['type'] == 'image' and pending:
                image = Image.open(BytesIO(base64.b64decode(block['source']['data']))).convert('RGB')
                kind, meta = pending
                key = meta['detail_of_existing_view']['view_id'] if kind == 'detail' else meta['source_evidence_ref']
                target = details if kind == 'detail' else pages
                if key in target:
                    raise ValueError('ambiguous duplicate image identity')
                target[key] = (image, meta)
                pending = None
    return pages, details


def box_to_pixels(box, size):
    return tuple(box[i] / 1000 * size[i % 2] for i in range(4))


def box_to_page_pixels(box, detail_size, detail_meta, page_size):
    """Inverse of page_content crop margin and generated header. No box correction."""
    x0, y0, _, _ = detail_meta['detail_of_existing_view']['bbox_normalized']
    crop_x = max(0, int((x0 - .015) * page_size[0]))
    crop_y = max(0, int((y0 - .015) * page_size[1]))
    header = detail_meta['generated_header_height_px']
    pixels = box_to_pixels(box, detail_size)
    return tuple(pixels[i] + (crop_x if i % 2 == 0 else crop_y - header) for i in range(4))


def draw_annotations(source, items):
    image = source.convert('RGBA')
    shade = Image.new('RGBA', image.size, (0, 0, 0, 0))
    fill = ImageDraw.Draw(shade)
    for item in items:
        color = COLORS[item['type']]
        fill.rectangle(item['pixels'], fill=color + '18')
    image = Image.alpha_composite(image, shade).convert('RGB')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=15)
    for item in items:
        box, color = item['pixels'], COLORS[item['type']]
        # Coordinates are never shifted or snapped to drawn panel boundaries.
        draw.rectangle(box, outline=color, width=3)
        label = item['id']
        bounds = draw.textbbox((0, 0), label, font=font)
        width, height = bounds[2] - bounds[0] + 6, bounds[3] - bounds[1] + 6
        x = max(0, min(image.width - width, box[0] + 2))
        y = max(0, min(image.height - height, box[1] + 2))
        draw.rectangle((x, y, x + width, y + height), fill=color)
        draw.text((x + 3, y + 2 - bounds[1]), label, fill='white', font=font)
    return image


def banner(width, revision, totals):
    image = Image.new('RGB', (width, 108), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=18)
    draw.text((16, 10), f'{revision} | MODEL ANNOTATIONS, NOT VERIFIED GROUND TRUTH', fill='#111827', font=font)
    draw.text((16, 39), 'Model totals: ' + ' / '.join(f'{k}: {v}' for k, v in totals.items()), fill='#374151', font=ImageFont.load_default(size=15))
    x = 16
    for kind, color in COLORS.items():
        draw.rectangle((x, 75, x + 18, 93), fill=color)
        draw.text((x + 25, 75), kind, fill='#111827', font=font)
        x += 180
    return image


def render_overlays(witness_path, prefix, *, allow_label_aliases=False):
    witness = json.loads(Path(witness_path).read_text())
    record = next(r for r in reversed(witness['provider_responses']) if r['stage'] == 'front_count')
    request = record['request']
    pages, details = decode_evidence_images(request)
    parsed = _json_object(record['response_text'])
    normalizations = []
    if allow_label_aliases:
        # Display-only spelling normalization; never change counts or coordinates.
        # The source witness and its failed validation status stay untouched.
        aliases = {v.lower().replace(' ', '_'): v for v in ISLAND_TYPES}
        for item in parsed.get('island_types', []):
            original = item.get('type')
            if isinstance(original, str) and original in aliases:
                item['type'] = aliases[original]
                normalizations.append({'view_id': item.get('view_id'),
                    'from': original, 'to': item['type']})
    known = {r['view_id'] for _, meta in pages.values() for r in meta['view_regions']}
    validate_front_count(parsed, known, require_annotations=True)
    revision = record.get('prompt_version', witness.get('prompt_version', 'unknown revision'))
    display_revision = revision + (' | FORMAT WARNING' if normalizations else '')
    rows = [{**front, 'type': group['type'], 'location': group['location']}
            for group in parsed['front_groups'] for front in group['fronts']]
    rows += [{**item, 'type': 'excluded'} for item in parsed['excluded_surfaces']]
    if not rows:
        raise ValueError('no annotations to render')
    by_view, by_page, warnings = {}, {}, []
    for row in rows:
        if row['view_id'] not in details:
            raise ValueError('annotation lacks exact supplied detail image')
        image, meta = details[row['view_id']]
        page_ref = meta['source_evidence_ref']
        page_image, _ = pages[page_ref]
        pixels = box_to_pixels(row['bbox_1000'], image.size)
        page_pixels = box_to_page_pixels(row['bbox_1000'], image.size, meta, page_image.size)
        if pixels[1] < meta['generated_header_height_px']:
            warnings.append(f'{row["id"]} intersects the generated header; not corrected')
        by_view.setdefault(row['view_id'], []).append({**row, 'pixels': pixels})
        by_page.setdefault(page_ref, []).append({**row, 'pixels': page_pixels})
        row['detail_pixels'] = pixels
        row['page_pixels'] = page_pixels
    if len(by_page) != 1:
        raise ValueError('single-page review renderer requires one annotated page')
    paths = {kind: Path(str(prefix) + suffix) for kind, suffix in {
        'page': '-overlay-page.png', 'details': '-overlay-details.png', 'coordinates': '-overlay-coordinates.json'}.items()}
    if any(path.exists() for path in paths.values()):
        raise ValueError('refuse overlay overwrite')
    page_ref, items = next(iter(by_page.items()))
    page = draw_annotations(pages[page_ref][0], items)
    header = banner(page.width, display_revision, parsed['totals'])
    whole = Image.new('RGB', (page.width, page.height + header.height), 'white')
    whole.paste(header, (0, 0)); whole.paste(page, (0, header.height))
    whole.save(paths['page'])
    tiles = []
    for view_id, items in sorted(by_view.items()):
        tile = draw_annotations(details[view_id][0], items)
        tile = tile.resize((880, round(tile.height * 880 / tile.width)), Image.Resampling.LANCZOS)
        tiles.append(tile)
    tile_height = max(t.height for t in tiles)
    cols = min(2, len(tiles)); width = cols * 900 + 20
    header = banner(width, display_revision, parsed['totals'])
    sheet = Image.new('RGB', (width, header.height + math.ceil(len(tiles) / cols) * (tile_height + 20)), '#f3f4f6')
    sheet.paste(header, (0, 0))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, (20 + i % cols * 900, header.height + i // cols * (tile_height + 20)))
    sheet.save(paths['details'])
    paths['coordinates'].write_text(json.dumps({'prompt_version': revision,
        'source_witness': str(witness_path), 'coordinate_convention': 'bbox_1000 on exact labelled detail; page_pixels exclude added output banner',
        'model_totals': parsed['totals'], 'display_only_label_normalizations': normalizations,
        'warnings': warnings, 'annotations': rows}, ensure_ascii=False, indent=2))
    return {**{k: str(v) for k, v in paths.items()}, 'warnings': warnings,
        'display_only_label_normalizations': normalizations}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--witness', required=True)
    parser.add_argument('--output-prefix', required=True)
    parser.add_argument('--diagnostic-label-aliases', action='store_true',
        help='Display-only snake_case label spelling normalization; source failure remains unchanged')
    args = parser.parse_args()
    print(json.dumps(render_overlays(args.witness, args.output_prefix,
        allow_label_aliases=args.diagnostic_label_aliases)))
