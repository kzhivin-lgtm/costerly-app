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

    def rpc(self, name, values):
        self.calls.append((name, values))
        return _Rpc()


def _approved_data():
    return {
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
        "use_cases.final_approval.proposal_signed_url",
        lambda *args, **kwargs: "https://signed.example/proposal.pdf",
    )

    result = final_approval(company_id="001", run_id="run-1", estimate_id="estimate-1")

    assert result["version_id"] == "version-1"
    assert client.calls[0][0] == "finalize_project_estimate"
    payload = client.calls[0][1]
    assert payload["p_snapshot"]["rows"][0]["sale_price_total"] == 130.5
    assert payload["p_snapshot"]["summary"]["total"] == 158.62
    assert result["proposal_pdf_path"] == "001/project-1/version-1.pdf"
    assert result["proposal_pdf_url"] == "https://signed.example/proposal.pdf"


def test_final_approval_rejects_unapproved_object(monkeypatch):
    data = _approved_data()
    data["rows"][0]["reviewed"] = False
    monkeypatch.setattr("use_cases.final_approval.load_objects_estimation_data", lambda _: data)

    with pytest.raises(ValueError, match="approve every object"):
        final_approval(company_id="001", run_id="run-1", estimate_id="estimate-1")


def test_objects_uses_final_approval_instead_of_generate_proposal():
    source = Path("screens/objects.py").read_text()

    assert '"FINAL APPROVAL"' in source
    assert '"GENERATE PROPOSAL"' not in source
    assert "final_approval(" in source
    assert 'st.session_state.screen = "projects"' not in source
    assert 'key="final_approval_approved" if proposal_ready else "final_approval"' in source

    css = Path("styles/objects.py").read_text()
    assert ".st-key-final_approval_approved button:disabled" in css
    assert "background: rgba(52, 168, 83, 0.12)" in css
