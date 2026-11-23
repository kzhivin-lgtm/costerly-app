from decimal import Decimal

from use_cases.overhead_engine import build_overhead_lines, estimate_object_overhead


def settings(**changes):
    return {"production_workers": 12, "workdays_per_month": 21, "hours_per_day": 8,
            "vat_percent": 18, "warranty_reserve_percent": 5,
            "management_buffer_percent": 5, **changes}


def estimate(**changes):
    return estimate_object_overhead(**{
        "estimate_id": "estimate", "object_id": "object", "company_id": "company",
        "settings": settings(), "overhead_monthly": {"rent_facilities_cost": 20160},
        "labor_hours": 10, "labor_cost": 625, "material_cost": 1000, **changes,
    })


def test_restore_uses_existing_profile_capacity_and_fee_base_exactly_once():
    result = estimate()
    assert result["capacity_hours"] == 2016
    assert [row["cost"] for row in result["lines"]] == [100, 86.25, 86.25]
    assert (result["cost"], result["vat"], result["total"]) == (272.5, 49.05, 321.55)
    assert result["lines"] == build_overhead_lines(
        estimate_id="estimate", object_id="object", company_id="company",
        settings=settings(), overhead_monthly={"rent_facilities_cost": 20160},
        labor_hours_total=10, subtotal_before_overhead=1625,
    )


def test_current_labor_overrides_and_quantity_scale_the_existing_allocator():
    base = estimate()
    twice = estimate(labor_hours=Decimal("20"), labor_cost=1250, material_cost=2000)
    assert twice["cost"] == 2 * base["cost"]
    assert twice["lines"][0]["allocation_basis"] == "20h / 2016h"
    changed = estimate(labor_hours=12, labor_cost=750)
    assert [row["cost"] for row in changed["lines"]] == [120, 93.5, 93.5]


def test_waiting_or_invalid_labor_never_fabricates_zero_overhead():
    for changes in ({"labor_hours": None}, {"labor_cost": None},
                    {"labor_hours": float("nan")}, {"labor_hours": -1}):
        result = estimate(**changes)
        assert result["status"] != "ready"
        assert result["cost"] is None and result["total"] is None


def test_saved_zero_hours_is_distinct_from_missing_hours():
    result = estimate(labor_hours=0, labor_cost=0)
    assert result["status"] == "ready" and result["cost"] == 0
    assert len(result["lines"]) == 3 and all(line["cost"] == 0 for line in result["lines"])


def test_missing_profile_capacity_is_actionable_and_partial_basis_is_retained():
    result = estimate(settings=settings(production_workers=0))
    assert result["status"] == "missing_capacity" and result["cost"] is None
    partial = estimate(partial=True)
    assert partial["status"] == "ready" and partial["partial"] is True
    assert partial["cost"] == estimate()["cost"]


def test_all_saved_monthly_categories_including_other_spendings_are_retained():
    from use_cases.overhead_engine import _monthly_overhead_map
    monthly = {field: 2016 for field, _, _ in _monthly_overhead_map()}
    result = estimate(overhead_monthly=monthly,
                      settings=settings(warranty_reserve_percent=0, management_buffer_percent=0))
    assert len(result["lines"]) == len(monthly) == 13
    assert result["cost"] == 130
    assert {line["raw_agent_json"]["source_column"] for line in result["lines"]} == set(monthly)


def labor_state():
    return {"status": "ready", "result": {
        "in_house_route": "cnc", "work": {"blank_count": 1},
        "in_house": {"operator_hours": 2}, "file_preparation": {"minutes": 0},
        "edge_banding": {"minutes": 0, "metres": 0}, "cnc_edging": {"minutes": 0},
        "issues": [], "unplaced_blanks": 0,
    }, "assembly": {"planned_minutes": Decimal("120"), "common_roles_for_review": [],
                    "blocks": [{"issues": []}]},
        "overhead_context": {"status": "ready", "settings": settings(),
                             "monthly": {"rent_facilities_cost": 20160}}}


def test_overhead_uses_the_same_current_labor_metrics_and_saved_hours_overrides():
    from screens.estimation_labor_v1 import _labor_pay_metrics, _overhead_html
    state = labor_state()
    overrides = {"assembly": "7", "sheet-processing": "3"}
    _, _, pay = _labor_pay_metrics(state, overrides=overrides)
    assert pay["hours"] == 10 and pay["total"] == 625
    html = _overhead_html(state, identity=("company", "run", "estimate", "object"),
                          material_cost=1000, overrides=overrides)
    assert "10h / 2016h" in html and "₪273" in html
    assert 'data-overhead-ready="true"' in html
    assert 'contenteditable="true"' not in html
    assert 'data-overhead-object-id="object"' in html
    assert 'data-overhead-percent="5' in html
    assert 'data-overhead-monthly="—"' not in html
    assert 'data-overhead-percent="—"' not in html


def test_unavailable_overhead_does_not_render_fabricated_zeroes():
    from ui.object_detail_view import overhead_section_html
    for status in ("loading", "pending_labor", "read_failed", "missing_capacity"):
        html = overhead_section_html({"status": status})
        assert '>Overhead<' in html and '₪0' not in html
        assert 'data-overhead-ready="false"' in html


def test_company_overhead_context_reads_are_scoped_to_the_current_company(monkeypatch):
    import pandas as pd
    from screens import estimation_labor_v1 as screen
    calls = []
    def read_settings(client, company_id):
        calls.append((client, company_id, "settings"))
        return pd.DataFrame([settings()])
    def read_monthly(client, company_id):
        calls.append((client, company_id, "monthly"))
        return pd.DataFrame([{"rent_facilities_cost": 20160}])
    monkeypatch.setattr(screen, "fetch_company_overhead_settings", read_settings)
    monkeypatch.setattr(screen, "fetch_company_overhead_monthly", read_monthly)
    client = object()
    assert screen._load_overhead_context(client, "company")["status"] == "ready"
    assert calls == [(client, "company", "settings"), (client, "company", "monthly")]


def test_profile_save_invalidation_preserves_labor_and_other_companies(monkeypatch):
    from types import SimpleNamespace
    from screens import company_profile
    current = labor_state()
    other = labor_state()
    cache = {("company", "run", "estimate", "object"): current,
             ("other", "run", "estimate", "object"): other}
    monkeypatch.setattr(company_profile, "st", SimpleNamespace(session_state={"labor_v1_comparisons": cache}))
    company_profile._invalidate_object_overhead_context("company")
    assert "overhead_context" not in current and "assembly" in current and "result" in current
    assert "overhead_context" in other


def test_persisted_self_cost_sums_three_components_once_and_reprices_profile_changes(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    monkeypatch.setattr(estimation, "load_object_labor", lambda *a, **k: labor_state())
    diagnostics, totals = [], []
    monkeypatch.setattr(estimation, "upsert_rfq_estimate_lines", lambda _, *, lines: diagnostics.extend(lines))
    monkeypatch.setattr(estimation, "update_rfq_object_estimate_totals", lambda *a, **k: totals.append(k))
    rows = [
        {"section": "material", "source": "parts_check", "line_id": "material", "cost": 1000},
        {"section": "labor", "source": "labor_hours_override", "cost": 0,
         "raw_agent_json": {"block": "assembly", "hours_per_item": "7"}},
        {"section": "labor", "source": "labor_hours_override", "cost": 0,
         "raw_agent_json": {"block": "sheet-processing", "hours_per_item": "3"}},
    ]
    plan = {"parts_check_source": {"run_id": "run"}, "lines": []}
    config = settings(employer_load_percent=99)
    context = {"plan": plan, "settings": config, "monthly": {"rent_facilities_cost": 20160},
               "machinery": {}, "parts": {"status": "ready", "payload": "saved"}}
    obj = {"object_id": "object", "run_id": "run", "company_id": "company", "quantity": 1}
    obj.update(self_cost_ex_vat=1000, vat_amount=180, self_cost_total=1180, approved=True)
    def recalculate(current_rows):
        return estimation._recalculate_object_estimate_totals(
            object(), estimate_id="estimate", object_id="object", object_row=obj,
            settings=config, lines_df=pd.DataFrame(current_rows), plan_snapshot=plan, cost_context=context,
        )
    first = recalculate(rows)
    assert first["self_cost_ex_vat"] == 1897.5  # 1000 + 625 (payroll included) + 272.5
    assert first["vat_amount"] == 341.55 and first["self_cost_total"] == 2239.05
    assert first["labor"]["total"] == "625.00" and first["overhead"]["cost"] == 272.5
    assert len(diagnostics) == len(totals) == 1
    assert diagnostics[0]["cost"] == 0  # Audit row must never become a duplicate charge.
    assert first["previous_totals"] == {"self_cost_ex_vat": 1000, "vat_amount": 180,
                                        "self_cost_total": 1180, "approved": True}
    obj.update({k: first[k] for k in ("self_cost_ex_vat", "vat_amount", "self_cost_total")})
    recalculate(rows + diagnostics)
    assert len(diagnostics) == len(totals) == 1  # Reopening unchanged inputs makes no new write.
    context["monthly"]["rent_facilities_cost"] *= 2
    changed = recalculate(rows + diagnostics)
    assert changed["self_cost_ex_vat"] == 2007.5 and totals[-1]["approved"] is False
    assert changed["previous_totals"] == first["previous_totals"]


def test_full_self_cost_is_per_item_and_unknown_work_remains_an_explicit_subtotal(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    state = labor_state()
    monkeypatch.setattr(estimation, "load_object_labor", lambda *a, **k: state)
    monkeypatch.setattr(estimation, "upsert_rfq_estimate_lines", lambda *a, **k: None)
    plan = {"parts_check_source": {"run_id": "run"}, "lines": []}
    context = {"plan": plan, "settings": settings(), "monthly": {"rent_facilities_cost": 20160},
               "machinery": {}, "parts": {"status": "ready", "payload": "saved"}}
    obj = {"object_id": "object", "run_id": "run", "company_id": "company", "quantity": 2}
    overrides = pd.DataFrame([
        {"source": "labor_hours_override", "raw_agent_json": {"block": "assembly", "hours_per_item": "7"}},
        {"source": "labor_hours_override", "raw_agent_json": {"block": "sheet-processing", "hours_per_item": "3"}},
    ])
    result, _ = estimation._full_cost_summary(
        object(), estimate_id="estimate", obj=obj, lines=overrides, material_batch=2000, context=context,
    )
    assert Decimal(result["labor"]["hours"]) == 20
    assert result["self_cost_ex_vat"] == 3795
    assert result["overhead"]["cost"] == 545
    state = {"status": "unavailable"}
    result, _ = estimation._full_cost_summary(
        object(), estimate_id="estimate", obj=obj, lines=pd.DataFrame(), material_batch=2000, context=context,
    )
    assert result["partial"] is True and result["labor"] is None
    assert result["overhead"]["cost"] is None and result["self_cost_ex_vat"] == 2000


def test_unchanged_cost_basis_can_check_parts_without_downloading_payload(monkeypatch):
    from types import SimpleNamespace
    from use_cases import estimation_parts_check_runtime as runtime
    class Query:
        def table(self, _): return self
        def select(self, _): return self
        def eq(self, *_): return self
        def limit(self, _): return self
        def execute(self): return SimpleNamespace(data=[{"estimate_id": "estimate"}])
    monkeypatch.setattr(runtime, "_reports", lambda *a: [{"status": "succeeded", "raw_usage": {
        "report_sha256": "digest", "part_rows": 2, "input_ids": ["saved-input"]}}])
    monkeypatch.setattr(runtime, "_read_report_payload", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Unnecessary payload read")))
    result = runtime.load_parts_check(client=Query(), company_id="company", run_id="run",
                                     estimate_id="estimate", include_payload=False)
    assert result == {"status": "ready", "report_sha256": "digest", "part_rows": 2, "input_ids": ["saved-input"]}


def test_copy_quantity_never_discounts_the_priced_configuration(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    state = labor_state()
    monkeypatch.setattr(estimation, 'load_object_labor', lambda *a, **k: state)
    plan = {'parts_check_source': {'run_id': 'run'}, 'object_quantities': {'object': 1}, 'lines': []}
    context = {'plan': plan, 'settings': settings(), 'monthly': {'rent_facilities_cost': 20160},
               'machinery': {}, 'parts': {'status': 'ready', 'payload': 'saved'}}
    prices = []
    for copies in (1, 3, 5):
        result, _ = estimation._full_cost_summary(None, estimate_id='estimate',
            obj={'object_id': 'object', 'run_id': 'run', 'company_id': 'company', 'quantity': copies},
            lines=pd.DataFrame([
                {'source': 'labor_hours_override', 'raw_agent_json': {'block': 'assembly', 'hours_per_item': '7'}},
                {'source': 'labor_hours_override', 'raw_agent_json': {'block': 'sheet-processing', 'hours_per_item': '3'}},
            ]), material_batch=1000, context=context, persist=False)
        prices.append(result['self_cost_ex_vat'])
        assert result['quantity_basis'] == 'per_priced_configuration'
    assert prices == [1897.5, 1897.5, 1897.5]
