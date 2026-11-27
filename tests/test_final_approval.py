from decimal import Decimal
from pathlib import Path

import pytest

from use_cases.final_approval import final_approval


class _Response:
    data = {
        "organization_id": "partner-1",
        "project_id": "project-1",
        "version_id": "version-1",
        "version_number": 1,
        "created": True,
    }


class _Rpc:
    def execute(self):
        return _Response()


class _Client:
    def __init__(self):
        self.calls = []
        self.versions = []
        self.filters = {}

    def table(self, name):
        assert name == 'project_versions'
        self.filters = {}
        return self

    def select(self, _): return self
    def eq(self, key, value):
        self.filters[key] = value
        return self
    def limit(self, _): return self
    def execute(self):
        class Response: pass
        result = Response()
        result.data = self.versions
        return result

    def rpc(self, name, values):
        self.calls.append((name, values))
        if not self.versions:
            self.versions = [{**_Response.data, 'snapshot': values['p_snapshot'], 'proposal_pdf_path':None}]
        return _Rpc()


def _approved_data():
    return {
        "advance_payment_percent": 70,
        "rows": [
            {
                "object_key": "object-1",
                "status": "completed",
                "reviewed": True,
                "sale_price_total": Decimal("130.50"),
            }
        ],
        "project_costs": [{"object_key": "delivery", "sale_price_unit": 3.92}],
        "summary": {"project_price": 134.42, "vat": 24.2, "total": 158.62},
    }


def test_final_approval_freezes_fresh_priced_snapshot(monkeypatch):
    client = _Client()
    monkeypatch.setattr("use_cases.final_approval.load_objects_estimation_data", lambda _: _approved_data())
    monkeypatch.setattr("use_cases.final_approval.get_supabase_client", lambda: client)
    monkeypatch.setattr("use_cases.final_approval.assert_run_owned", lambda *args: None)
    monkeypatch.setattr("use_cases.final_approval.assert_estimate_owned", lambda *args: None)
    monkeypatch.setattr(
        "use_cases.final_approval.publish_proposal_pdf",
        lambda **kwargs: "001/project-1/version-1.pdf",
    )
    monkeypatch.setattr(
        "use_cases.final_approval.load_estimate_proposal_url",
        lambda **kwargs: "https://signed.example/proposal.pdf",
    )

    monkeypatch.setattr('use_cases.final_approval.capture_proposal_document', lambda **_: {'template':'labor-v3'})
    result = final_approval(company_id="001", run_id="run-1", estimate_id="estimate-1")

    assert result["version_id"] == "version-1"
    assert client.calls[0][0] == "finalize_project_estimate"
    payload = client.calls[0][1]
    assert payload["p_snapshot"]["rows"][0]["sale_price_total"] == 130.5
    assert payload["p_snapshot"]["summary"]["total"] == 158.62
    assert payload['p_snapshot']['advance_payment_percent']==70
    assert result["proposal_pdf_path"] == "001/project-1/version-1.pdf"
    assert result["proposal_pdf_url"] == "https://signed.example/proposal.pdf"


def test_final_approval_rejects_unapproved_object(monkeypatch):
    data = _approved_data()
    data["rows"][0]["reviewed"] = False
    monkeypatch.setattr("use_cases.final_approval.load_objects_estimation_data", lambda _: data)

    with pytest.raises(ValueError, match="approve every object"):
        final_approval(company_id="001", run_id="run-1", estimate_id="estimate-1")


def test_objects_v2_generates_via_the_existing_final_approval():
    source = Path("screens/objects.py").read_text()

    assert '"GENERATE PROPOSAL"' in source
    assert '"Set Prices"' in source
    assert 'st.columns(3, gap="small")' in source
    assert "final_approval(" in source
    assert 'st.session_state.screen = "projects"' not in source
    assert 'key="final_approval_approved" if proposal_ready else f"objects_generate_proposal_' in source

    css = Path("styles/objects.py").read_text()
    assert ".st-key-final_approval_approved button:disabled" in css
    assert "background: rgba(52, 168, 83, 0.12)" in css


def test_retry_renders_the_first_stored_document_without_recapturing_profile(monkeypatch):
    client=_Client()
    monkeypatch.setattr('use_cases.final_approval.get_supabase_client',lambda:client)
    monkeypatch.setattr('use_cases.final_approval.assert_run_owned',lambda *a:None)
    monkeypatch.setattr('use_cases.final_approval.assert_estimate_owned',lambda *a:None)
    monkeypatch.setattr('use_cases.final_approval.load_objects_estimation_data',lambda _:(_ for _ in ()).throw(AssertionError('unexpected calculation read')))
    captures=[]
    monkeypatch.setattr('use_cases.final_approval.capture_proposal_document',lambda **_:captures.append(1) or {'company':'Original','logo_base64':'original'})
    attempts=[]
    def publish(**kwargs):
        attempts.append(kwargs['snapshot'])
        if len(attempts)==1:raise RuntimeError('storage unavailable')
        return '001/project-1/version-1.pdf'
    monkeypatch.setattr('use_cases.final_approval.publish_proposal_pdf',publish)
    monkeypatch.setattr('use_cases.final_approval.load_estimate_proposal_url',lambda **_:'https://example.test/proposal.pdf')
    data=_approved_data()
    with pytest.raises(RuntimeError,match='storage unavailable'):
        final_approval(company_id='001',run_id='run-1',estimate_id='estimate-1',confirmed_data=data)
    data['summary']['total']=99999
    result=final_approval(company_id='001',run_id='run-1',estimate_id='estimate-1',confirmed_data=data)
    assert captures==[1]
    assert attempts[1]['document']['company']=='Original'
    assert attempts[1]['summary']['total']==158.62
    client.versions[0]['proposal_pdf_path']=result['proposal_pdf_path']
    final_approval(company_id='001',run_id='run-1',estimate_id='estimate-1',confirmed_data=data)
    assert len(attempts)==2
