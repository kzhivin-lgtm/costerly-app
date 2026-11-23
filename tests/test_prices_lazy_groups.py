from contextlib import nullcontext
from types import SimpleNamespace
from concurrent.futures import Future

import pytest
from screens import company_profile as profile


@pytest.fixture
def ui(monkeypatch):
    labels, loading = [], []
    state = {}
    monkeypatch.setattr(profile.st, 'session_state', state)
    monkeypatch.setattr(profile.st, 'columns', lambda count, **kw: [nullcontext() for _ in range(count)])
    monkeypatch.setattr(profile.st, 'selectbox', lambda label, options, **kw: options[0])
    monkeypatch.setattr(profile.st, 'markdown', lambda *a, **kw: None)
    monkeypatch.setattr(profile.st, 'container', lambda **kw: nullcontext())
    monkeypatch.setattr(profile, '_render_price_lists_loading', lambda: loading.append(True))
    class Group:
        def __init__(self, label, **kw):
            self.open = state.get(kw['key'], False); labels.append((label, kw))
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr(profile.st, 'expander', Group)
    return SimpleNamespace(labels=labels, loading=loading, state=state,
                           access=SimpleNamespace(company_id='company', user_id='owner'))


def test_pending_catalog_shows_closed_headers_without_waiting_or_row_work(ui):
    profile._render_pending_price_catalog(ui.access)
    assert [label for label, _ in ui.labels] == list(profile._PRICE_CATALOG_DEPARTMENTS)
    assert not ui.loading
    assert all(kw['expanded'] is False and callable(kw['on_change']) for _, kw in ui.labels)
    ui.state['price_group_company_owner_Metal'] = True
    profile._render_pending_price_catalog(ui.access)
    assert len(ui.loading) == 1


def test_closed_large_catalog_does_not_construct_row_widgets(ui, monkeypatch):
    monkeypatch.setattr(profile, '_price_source_saving_row_targets', lambda: set())
    rows = [{'department': 'Wood', 'material_type': 'Plywood', 'supplier_name': 'Supplier'} for _ in range(3000)]
    def expensive(*args): raise AssertionError('Closed group built price row widgets')
    monkeypatch.setattr(profile, '_render_price_catalog_grid_header', expensive)
    profile._render_price_catalog(ui.access, rows, [])
    assert len(ui.labels) == 1


def test_ready_catalog_does_not_wait_for_other_projection_futures(ui, monkeypatch):
    pending = Future()
    rows = [{'department': 'Metal'}]
    monkeypatch.setattr(profile, '_poll_price_lists_projections', lambda _: ({'catalog': rows}, {}, {'sources': pending}))
    for name in ('_settle_price_source_row_save_reconciliations', '_settle_price_source_purge_reconcile', '_render_price_source_save_progress'):
        monkeypatch.setattr(profile, name, lambda **kw: None)
    monkeypatch.setattr(profile, '_price_source_hidden_ids', lambda: set())
    rendered = []
    monkeypatch.setattr(profile, '_render_price_catalog', lambda *args: rendered.append(args[1]))
    profile._render_price_lists_projections.__wrapped__(ui.access)
    assert rendered == [rows] and not pending.done() and not ui.loading


def test_group_state_is_scoped_and_open_survives_count_label_change(ui):
    with profile._price_group(ui.access, 'Metal', 'Metal', open_once=True) as group:
        assert group.open
    ui.state.pop('price_group_company_owner_Metal')  # native ID changes with count label
    with profile._price_group(ui.access, 'Metal', 'Metal · 10 prices') as group:
        assert group.open
    other = SimpleNamespace(company_id='other-company', user_id='owner')
    with profile._price_group(other, 'Metal', 'Metal') as group:
        assert not group.open
