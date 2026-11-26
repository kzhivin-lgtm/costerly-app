from decimal import Decimal
import pytest

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
    assert len(result["lines"]) == len(monthly) == 14
    assert result["cost"] == 140
    assert {line["raw_agent_json"]["source_column"] for line in result["lines"]} == set(monthly)


def test_management_employer_cost_uses_same_hours_without_second_payroll_load():
    result = estimate(settings=settings(production_monthly_hours=1200, warranty_reserve_percent=0, management_buffer_percent=0),
                      overhead_monthly={'management_administration_cost':46250,'rent_facilities_cost':10000},
                      labor_hours=100)
    assert result['lines'][0]['group_name'] == 'Management & Administration'
    assert result['lines'][0]['monthly_cost'] == 46250
    assert result['lines'][0]['cost'] == 3854.17
    assert result['lines'][0]['allocation_basis'] == '100h / 1200h'
    assert result['cost'] == 4687.5


def test_profile_management_payroll_is_readonly_vat_exempt_and_not_editable():
    from ui.company_metrics_view import table_html
    field='management_administration_cost'
    html=table_html((('Management & Administration',((field,'Management and office payroll'),)),),
                    {field:46250},18,editable=True,readonly_fields=(field,),vat_exempt_fields=(field,))
    assert 'contenteditable' not in html and 'role="textbox"' not in html
    assert html.count('₪46\u202f250') == 3
    assert '₪8\u202f325' not in html


def test_management_query_reads_only_company_scoped_active_nonproduction_totals():
    from db.repositories import fetch_company_management_payroll
    from types import SimpleNamespace
    class Query:
        def table(self,name):assert name=='company_employees';return self
        def select(self,fields,**kwargs):assert fields=='total_monthly_cost' and kwargs=={'count':'exact'};return self
        def eq(self,k,v):assert (k,v)==('company_id','c');return self
        def in_(self,k,v):assert k=='department' and set(v)=={'management','office'};return self
        def is_(self,k,v):assert (k,v)==('deleted_at','null');return self
        def execute(self):return SimpleNamespace(data=[{'total_monthly_cost':100.1},{'total_monthly_cost':200.2}],count=2)
    assert fetch_company_management_payroll(Query(),'c') == 300.3


def test_empty_work_is_a_terminal_editable_row_without_disclosure():
    from screens.estimation_labor_v1 import _cost_band
    from xml.etree import ElementTree as ET
    root=ET.fromstring(_cost_band('File Preparation','',{'hours':.2,'pay':10,'taxes':2.5,'total':12.5},key='file-preparation'))
    assert root.tag=='div' and root.find('summary') is None
    assert root.find(".//*[@data-field='labor_hours']") is not None
    assert root.find("./div[@class='object-detail-work-body']") is None


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
    from db import repositories
    def read_capacity(client, company_id):
        calls.append((client, company_id, "capacity"))
        return {"reported_hours": 1200, "employee_count": 6, "unreported_hours_count": 0}
    monkeypatch.setattr(repositories, "fetch_company_production_capacity", read_capacity)
    client = object()
    context = screen._load_overhead_context(client, "company")
    assert context["status"] == "ready"
    assert context["settings"]["production_monthly_hours"] == 1200
    assert calls == [(client, "company", "settings"), (client, "company", "monthly"),
                     (client, "company", "capacity")]


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


def test_reported_production_capacity_overrides_legacy_staff_count():
    result = estimate(settings=settings(production_monthly_hours=1200,
                      capacity_source="production_employee_hours"))
    assert result["capacity_hours"] == 1200
    assert result["lines"][0]["allocation_basis"] == "10h / 1200h"
    assert result["lines"][0]["cost"] == 168
    assert result["lines"][0]["raw_agent_json"]["capacity_source"] == "production_employee_hours"


def test_production_capacity_is_scoped_and_does_not_read_wages():
    from types import SimpleNamespace
    from db.repositories import fetch_company_production_capacity
    calls = []
    class Query:
        def select(self, columns, **kwargs):
            calls.append(("select", columns, kwargs));return self
        def eq(self, key, value):calls.append(("eq", key, value));return self
        def is_(self, key, value):calls.append(("is", key, value));return self
        def execute(self):return SimpleNamespace(data=[{"monthly_hours":200}] * 6, count=6)
    client = SimpleNamespace(table=lambda name: calls.append(("table", name)) or Query())
    result = fetch_company_production_capacity(client, "company-a")
    assert result == {"reported_hours":1200, "employee_count":6, "unreported_hours_count":0}
    assert calls == [("table", "company_employees"), ("select", "monthly_hours", {"count":"exact"}),
                     ("eq", "company_id", "company-a"), ("eq", "department", "production"),
                     ("is", "deleted_at", "null")]


def test_capacity_fallback_is_explicit_and_does_not_hide_failed_reads(monkeypatch):
    import pytest
    from db import repositories
    from use_cases.overhead_engine import with_production_capacity
    monkeypatch.setattr(repositories, "fetch_company_production_capacity",
                        lambda *_: {"reported_hours":0, "employee_count":0, "unreported_hours_count":0})
    context = with_production_capacity(object(), "company", settings())
    result = estimate(settings=context)
    assert result["capacity_hours"] == 2016 and result["capacity_source"] == "legacy_settings_fallback"
    assert result["lines"][0]["raw_agent_json"]["production_capacity_audit"]["reported_hours"] == 0
    def fail(*_):raise RuntimeError("capacity read failed")
    monkeypatch.setattr(repositories, "fetch_company_production_capacity", fail)
    with pytest.raises(RuntimeError, match="capacity read failed"):
        with_production_capacity(object(), "company", settings())


@pytest.mark.parametrize("mutation", ["add", "update", "archive"])
def test_employee_mutations_invalidate_only_their_company_overhead(monkeypatch, mutation):
    from types import SimpleNamespace
    import streamlit as st
    from screens import company_profile as profile
    owner = SimpleNamespace(company_id="company-a", user_id="owner", role="owner")
    class Query:
        def insert(self, *_):return self
        def update(self, *_):return self
        def eq(self, *_):return self
        def is_(self, *_):return self
        def execute(self):return SimpleNamespace(data=[{"company_id":"company-a", "employee_id":"employee"}])
    client = SimpleNamespace(table=lambda _: Query())
    monkeypatch.setattr(profile, "_owner_access", lambda _: (owner, client))
    current={"overhead_context":{"capacity":1200},"labor_preserved":"saved"}
    foreign={"overhead_context":{"capacity":400},"labor_preserved":"other"}
    st.session_state.clear()
    st.session_state["labor_v1_comparisons"]={("company-a","run","estimate-a","object"):current,
                                             ("company-b","run","estimate-b","object"):foreign}
    try:
        values={"worker_name":"Worker", "department":"production", "position_code":"carpenter",
                "pay_type":"hourly_rate", "gross_hourly_rate":50,"monthly_hours":200}
        if mutation=="add":profile.add_company_employee(owner, **values)
        elif mutation=="update":profile.update_company_employee(owner, "employee", **values)
        else:profile.archive_company_employee(owner, "employee")
        assert "overhead_context" not in current and current["labor_preserved"]=="saved"
        assert foreign["overhead_context"]=={"capacity":400}
        assert st.session_state["objects_estimation_cache_dirty"]=={"estimate-a"}
        assert st.session_state["object_detail_data_cache_dirty"]=={"estimate-a"}
    finally:st.session_state.clear()


def test_preparation_packing_is_persisted_and_allocated_once_in_full_self_cost(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    state=labor_state()
    state['preparation']={'version':'preparation_packing_v1','checking_minutes':30,'packing_minutes':30,
        'checking_known':True,'packing_partial':False,'interfaces':[{'unit_ids':['A','B']}],
        'packing_units':[{'id':'A'},{'id':'B'}],'issues':[]}
    monkeypatch.setattr(estimation,'load_object_labor',lambda *a,**k:state)
    summary,_=estimation._full_cost_summary(None,estimate_id='estimate',
        obj={'object_id':'object','run_id':'run','company_id':'company','quantity':1},
        lines=pd.DataFrame([{'section':'material','source':'parts_check','line_id':'m','cost':1000}]),
        material_batch=1000,context={'plan':{'lines':[]},'parts':{'status':'ready','payload':'saved'},
            'machinery':{},'settings':settings(warranty_reserve_percent=0,management_buffer_percent=0),
            'monthly':{'rent_facilities_cost':20160}},persist=False)
    assert Decimal(summary['labor']['hours'])==5
    assert Decimal(summary['labor']['total'])==Decimal('312.50')
    assert Decimal(summary['labor_blocks']['preparation_packing']['total'])==Decimal('62.50')
    assert summary['overhead']['cost']==50
    assert summary['self_cost_ex_vat']==1362.5 and summary['vat_amount']==245.25
    assert summary['preparation_packing']['packing_minutes']==30


def test_new_fractional_labor_costs_update_previously_integral_objects_columns(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    frame=pd.DataFrame([{'object_id':'o','company_id':'c','run_id':'r','status':'completed',
        'self_cost_ex_vat':1000,'vat_amount':180,'self_cost_total':1180,'approved':True}])
    monkeypatch.setattr(estimation,'_full_cost_context',lambda *a,**k:{})
    monkeypatch.setattr(estimation,'fetch_rfq_estimate_lines',lambda *a:pd.DataFrame())
    monkeypatch.setattr(estimation,'_recalculate_object_estimate_totals',lambda *a,**k:{
        'self_cost_ex_vat':1018.13,'vat_amount':183.26,'self_cost_total':1201.39,'approved':False,'partial':False})
    estimation._ensure_full_object_costs(None,estimate_id='e',objects=frame,
        plan={'status':'planned','parts_check_source':{'run_id':'r'}},settings={})
    assert frame.iloc[0]['self_cost_ex_vat']==1018.13
    assert frame.iloc[0]['self_cost_total']==1201.39
    assert not frame.iloc[0]['approved']


def test_screenshot_preparation_children_are_counted_once_in_header_and_overhead():
    from screens.estimation_labor_v1 import _cost_band, _labor_html, _overhead_html, _labor_pay_metrics
    state = labor_state()
    state['preparation'] = {'checking_minutes':150, 'packing_minutes':240,
        'checking_known':True, 'packing_partial':False, 'interfaces':[], 'packing_units':[], 'issues':[]}
    overrides = {'sheet-processing':'6.9', 'assembly':'14.9'}
    _, _, metrics = _labor_pay_metrics(state, overrides=overrides)
    assert metrics['hours'] == Decimal('28.3')
    html = _cost_band('Labor', '', metrics, key='labor')
    assert 'data-labor-total-hours="28.3"' in html
    assert '>28.3 h<' in html
    assert _labor_html({'status':'waiting_for_materials'}).count('data-labor-aggregate="true"') == 3
    overhead = _overhead_html(state, identity=('company','run','estimate','object'),
                              material_cost=1000, overrides=overrides)
    assert 'data-overhead-labor-hours="28.3"' in overhead
    assert '28.3h / 2016h' in overhead


@pytest.mark.parametrize('hours,display', [('100.25','100.3'), ('140.75','140.8'), ('1.15','1.2'), ('28.3','28.3')])
def test_labor_and_overhead_round_only_display_half_up(hours, display):
    from screens.estimation_labor_v1 import _cost_band
    from use_cases.estimation_labor_v1 import labor_pay_metrics
    from use_cases.overhead_engine import format_labor_hours
    exact = Decimal(hours)
    result = estimate(labor_hours=exact)
    assert format_labor_hours(exact) == display
    assert f'>{display} h<' in _cost_band('Labor', '', labor_pay_metrics(exact), key='labor')
    assert f'{display}h / 2016h' in result['lines'][0]['allocation_basis']
    assert result['lines'][0]['raw_agent_json']['labor_hours_total'] == float(exact)
    assert result['lines'][0]['cost'] == round(20160*float(exact)/2016, 2)


def test_closed_overhead_group_sums_monthly_cost_and_uses_one_current_allocation():
    from ui.object_detail_view import _group_summary_value
    rows=[{'monthly_cost':v,'allocation':'28.3h / 1200h','cost':v*28.3/1200,'reserve_percent':''}
          for v in (10000,1000,500)]
    assert _group_summary_value('Monthly cost',rows)=='₪11\u202f500'
    assert _group_summary_value('Allocation',rows)=='28.3h / 1200h'
    assert _group_summary_value('Cost',rows)=='₪271'


def test_reserve_group_is_formula_and_never_adds_percentages_as_monthly_money():
    from ui.object_detail_view import _group_summary_value,overhead_section_html
    rows=[{'monthly_cost':5,'reserve_percent':5,'allocation':'5% of self-cost','cost':50},
          {'monthly_cost':7,'reserve_percent':7,'allocation':'7% of self-cost','cost':70}]
    assert _group_summary_value('Monthly cost',rows)=='—'
    assert _group_summary_value('Allocation',rows)=='Formula'
    assert _group_summary_value('Cost',rows)=='₪120'
    result=estimate()
    html=overhead_section_html(result)
    assert 'data-overhead-group-column="monthly"' in html
    assert 'data-overhead-group-column="allocation">Formula<' in html
