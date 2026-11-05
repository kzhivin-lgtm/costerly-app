import base64
from io import BytesIO
import json

from PIL import Image
import pytest

from tests.test_estimation_front_count import annotated
from tools.render_estimation_front_overlay import box_to_pixels, box_to_page_pixels, render_overlays


def test_coordinate_transform_accounts_for_margin_header_and_image_sizes():
    meta = {'detail_of_existing_view': {'bbox_normalized': [.2, .1, .4, .3]},
        'generated_header_height_px': 32}
    box = [100, 250, 500, 750]
    assert box_to_pixels(box, (200, 132)) == (20, 33, 100, 99)
    assert box_to_page_pixels(box, (200, 132), meta, (1000, 800)) == (205, 69, 285, 135)


@pytest.mark.parametrize('with_supports', [False, True])
def test_renderer_uses_saved_coordinates_and_never_overwrites(tmp_path, with_supports):
    def image_block(size):
        data = BytesIO()
        Image.new('RGB', size, 'white').save(data, format='PNG')
        return {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png',
            'data': base64.b64encode(data.getvalue()).decode()}}
    region = {'view_id': 'p1-view-001', 'bbox_normalized': [.2, .1, .4, .3]}
    detail = {'detail_of_existing_view': region, 'source_evidence_ref': 'page', 'generated_header_height_px': 32}
    parsed = annotated()
    if with_supports:
        from tests.test_cb_front_supports import supported
        parsed = supported()
    revision = 'estimation_front_count_v6_2_r05' if with_supports else 'test-r03'
    request = {'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': json.dumps({'source_evidence_ref': 'page',
            'view_regions': [region], 'displayed_image_pixels': [1000, 800]})},
        image_block((1000, 800)), {'type': 'text', 'text': json.dumps(detail)}, image_block((200, 132))]}]}
    witness = tmp_path / 'witness.json'
    witness.write_text(json.dumps({'provider_responses': [{'stage': 'front_count',
        'prompt_version': revision, 'request': request, 'response_text': json.dumps(parsed)}]}))
    before = witness.read_bytes()
    result = render_overlays(witness, tmp_path / 'result')
    assert witness.read_bytes() == before
    with Image.open(result['page']) as image:
        assert image.size == (1000, 908)
    data = json.loads((tmp_path / 'result-overlay-coordinates.json').read_text())
    assert data['annotations'][0]['bbox_1000'] == parsed['front_groups'][0]['fronts'][0]['bbox_1000']
    assert data['prompt_version'] == revision
    if with_supports:
        legs = [r for r in data['annotations'] if r['type'] == 'leg']
        assert [r['bbox_1000'] for r in legs] == [r['bbox_1000'] for r in parsed['tabletop_supports'][0]['legs']]
        assert data['model_totals']['legs'] == 2
    assert data['warnings']  # Header overlap is reported, never silently repaired.
    with pytest.raises(ValueError, match='overwrite'):
        render_overlays(witness, tmp_path / 'result')

    parsed['island_types'][0]['type'] = 'front_elevation'
    bad = json.loads(witness.read_text())
    bad['status'] = 'failed'
    bad['provider_responses'][0]['response_text'] = json.dumps(parsed)
    witness.write_text(json.dumps(bad))
    before = witness.read_bytes()
    with pytest.raises(ValueError, match='classification'):
        render_overlays(witness, tmp_path / 'bad')
    diagnostic = render_overlays(witness, tmp_path / 'diagnostic', allow_label_aliases=True)
    assert witness.read_bytes() == before
    assert diagnostic['display_only_label_normalizations'] == [
        {'view_id': 'p1-view-001', 'from': 'front_elevation', 'to': 'Front elevation'}]
    data = json.loads((tmp_path / 'diagnostic-overlay-coordinates.json').read_text())
    assert data['annotations'][0]['bbox_1000'] == parsed['front_groups'][0]['fronts'][0]['bbox_1000']
    assert data['model_totals'] == {**parsed['totals'], **({'legs': 2} if with_supports else {})}
