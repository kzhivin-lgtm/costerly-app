from ui.screen_transition import screen_transition_marker_html


def test_screen_transition_marker_is_invisible_and_screen_scoped():
    markup = screen_transition_marker_html("object_detail")

    assert 'id="costerly-screen-object_detail"' in markup
    assert 'data-costerly-screen="object_detail"' in markup
    assert 'style="display:none"' in markup


def test_screen_transition_marker_normalizes_unknown_screen_names():
    markup = screen_transition_marker_html("File Review / retry")

    assert 'data-costerly-screen="filereviewretry"' in markup
