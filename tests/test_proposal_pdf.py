import pymupdf

from use_cases.proposal_pdf import _contact_lines, build_proposal_pdf, proposal_signed_url


def _snapshot():
    return {
        "rows": [
            {
                "name": "Display shelf",
                "quantity": 2,
                "self_cost_unit": 800,
                "sale_price_unit": 1200,
                "sale_price_total": 2400,
            }
        ],
        "project_costs": [
            {"object_key": "delivery", "name": "Delivery", "sale_price_unit": 72},
            {"object_key": "installation", "name": "Installation", "sale_price_unit": 240},
        ],
        "summary": {
            "project_price": 2712,
            "vat": 488.16,
            "total": 3200.16,
            "vat_percent": 18,
        },
    }


def test_proposal_omits_empty_contacts_and_self_cost():
    assert _contact_lines({"public_email": "office@example.com"}) == ["office@example.com"]

    payload = build_proposal_pdf(
        profile={"company_name": "Workshop"},
        project_name="Restaurant Deer",
        partner_name="Studio Tree",
        client_name="Restaurant Group",
        snapshot=_snapshot(),
    )

    assert payload.startswith(b"%PDF")
    with pymupdf.open(stream=payload, filetype="pdf") as document:
        text = "\n".join(page.get_text() for page in document)
    assert "Display shelf" in text
    assert "Delivery" in text
    assert "Installation" in text
    assert "PROJECT TOTAL" in text
    assert "800" not in text


def test_proposal_supports_non_latin_project_names():
    payload = build_proposal_pdf(
        profile={"company_name": "Мастерская"},
        project_name="Ресторан Олень",
        partner_name="Бюро Ёлочка",
        client_name="Ресторанная группа",
        snapshot=_snapshot(),
    )
    with pymupdf.open(stream=payload, filetype="pdf") as document:
        text = "\n".join(page.get_text() for page in document)
    assert "Ресторан Олень" in text
    assert "Бюро Ёлочка" in text


def test_signed_proposal_url_accepts_supabase_response_spelling():
    class Bucket:
        def create_signed_url(self, path, expires_in):
            assert path == "company/project/version.pdf"
            assert expires_in == 3600
            return {"signedURL": "https://signed.example/proposal.pdf"}

    class Storage:
        def from_(self, bucket):
            assert bucket == "project-proposals"
            return Bucket()

    class Client:
        storage = Storage()

    assert proposal_signed_url(Client(), "company/project/version.pdf") == (
        "https://signed.example/proposal.pdf"
    )
