from __future__ import annotations

from io import BytesIO
import math
import re
from datetime import datetime
from typing import Any

import pymupdf

from use_cases.company_logo import load_company_logo_bytes


PROPOSAL_BUCKET = "project-proposals"
_PURPLE = (0.50, 0.28, 0.82)
_INK = (0.12, 0.09, 0.13)
_MUTED = (0.46, 0.43, 0.47)
_RULE = (0.88, 0.85, 0.89)


def _money(value: object) -> str:
    try:
        return f"ILS {float(value):,.2f}"
    except (TypeError, ValueError):
        return "-"


def _clean(value: object) -> str:
    return str(value or "").strip()


def _address(profile: dict[str, Any]) -> str:
    street = " ".join(
        part for part in (_clean(profile.get("address_street")), _clean(profile.get("address_house_number"))) if part
    )
    locality = " ".join(
        part for part in (_clean(profile.get("address_city")), _clean(profile.get("address_postal_code"))) if part
    )
    return ", ".join(part for part in (street, locality, _clean(profile.get("address_country"))) if part)


def _contact_lines(profile: dict[str, Any]) -> list[str]:
    lines = [
        _clean(profile.get("public_email")),
        _clean(profile.get("public_phone")),
        _clean(profile.get("website_url")),
        _address(profile),
    ]
    social = [
        f"Facebook: {value}" if (value := _clean(profile.get("facebook_url"))) else "",
        f"LinkedIn: {value}" if (value := _clean(profile.get("linkedin_url"))) else "",
        f"Instagram: {value}" if (value := _clean(profile.get("instagram_url"))) else "",
    ]
    return [line for line in (*lines, *social) if line]


class _ProposalCanvas:
    def __init__(self) -> None:
        self.document = pymupdf.open()
        self.font = pymupdf.Font(fontname="cjk")
        self.page: pymupdf.Page
        self.y = 0.0
        self._new_page()

    def _new_page(self) -> None:
        self.page = self.document.new_page(width=595, height=842)
        self.page.insert_font(fontname="Proposal", fontbuffer=self.font.buffer)
        self.y = 54

    def ensure(self, height: float) -> None:
        if self.y + height > 790:
            self._new_page()

    def text(self, value: str, *, x: float = 48, size: float = 10, color=_INK, width: float = 499) -> None:
        characters_per_line = max(8, int(width / max(size * 0.56, 1)))
        lines = max(1, math.ceil(len(value) / characters_per_line))
        height = max(size * 1.45 * lines, 18)
        self.ensure(height)
        self.page.insert_textbox(
            pymupdf.Rect(x, self.y, x + width, self.y + height),
            value,
            fontname="Proposal",
            fontsize=size,
            color=color,
            lineheight=1.15,
        )
        self.y += height

    def rule(self) -> None:
        self.page.draw_line((48, self.y), (547, self.y), color=_RULE, width=0.7)
        self.y += 14

    def row(self, cells: list[tuple[str, float]], *, size: float = 9, color=_INK) -> None:
        lines = max(
            max(1, math.ceil(len(value) / max(8, int((width - 8) / max(size * 0.56, 1)))))
            for value, width in cells
        )
        height = max(31, size * 1.35 * lines + 10)
        self.ensure(height)
        x = 48.0
        for value, width in cells:
            self.page.insert_textbox(
                pymupdf.Rect(x, self.y, x + width - 8, self.y + height - 6),
                value,
                fontname="Proposal",
                fontsize=size,
                color=color,
                lineheight=1.05,
            )
            x += width
        self.y += height - 3

    def add_page_numbers(self) -> None:
        total = self.document.page_count
        for index, page in enumerate(self.document, start=1):
            page.insert_textbox(
                pymupdf.Rect(48, 808, 547, 826),
                f"{index} / {total}",
                fontname="Proposal",
                fontsize=8,
                color=_MUTED,
                align=pymupdf.TEXT_ALIGN_RIGHT,
            )


def build_proposal_pdf(
    *,
    profile: dict[str, Any],
    project_name: str,
    partner_name: str,
    client_name: str,
    snapshot: dict[str, Any],
    logo_bytes: bytes | None = None,
) -> bytes:
    """Render a customer-facing proposal from the immutable approved snapshot."""
    canvas = _ProposalCanvas()
    if logo_bytes:
        try:
            canvas.page.insert_image(pymupdf.Rect(48, 42, 126, 120), stream=logo_bytes, keep_proportion=True)
        except Exception:
            pass

    company_name = _clean(profile.get("company_name")) or _clean(profile.get("legal_name"))
    canvas.text(company_name or "Proposal", x=148 if logo_bytes else 48, size=20, color=_PURPLE, width=399)
    for line in _contact_lines(profile):
        canvas.text(line, x=148 if logo_bytes else 48, size=8.5, color=_MUTED, width=399)
    canvas.y = max(canvas.y + 12, 136 if logo_bytes else canvas.y + 12)
    canvas.rule()

    canvas.text("CLIENT PROPOSAL", size=11, color=_PURPLE)
    canvas.text(project_name or "Untitled project", size=24)
    if partner_name:
        canvas.text(f"Partner: {partner_name}", size=10, color=_MUTED)
    if client_name:
        canvas.text(f"Client: {client_name}", size=10, color=_MUTED)
    canvas.y += 12

    canvas.row(
        [("PROJECT OBJECTS", 255), ("QTY", 55), ("SALE PRICE / UNIT", 105), ("TOTAL", 84)],
        size=8,
        color=_MUTED,
    )
    canvas.rule()
    for row in snapshot.get("rows") or []:
        canvas.row([
            (_clean(row.get("name")) or "Untitled object", 255),
            (_clean(row.get("quantity")) or "-", 55),
            (_money(row.get("sale_price_unit")), 105),
            (_money(row.get("sale_price_total")), 84),
        ])
        canvas.rule()

    for row in snapshot.get("project_costs") or []:
        canvas.row([
            (_clean(row.get("name")) or _clean(row.get("object_key")).title(), 415),
            (_money(row.get("sale_price_unit")), 84),
        ])
        canvas.rule()

    summary = snapshot.get("summary") or {}
    canvas.y += 10
    canvas.row([("Project price", 415), (_money(summary.get("project_price")), 84)], size=10)
    vat_percent = summary.get("vat_percent")
    vat_label = f"VAT {vat_percent:g}%" if isinstance(vat_percent, (int, float)) else "VAT"
    canvas.row([(vat_label, 415), (_money(summary.get("vat")), 84)], size=10)
    canvas.row([("PROJECT TOTAL", 415), (_money(summary.get("total")), 84)], size=13, color=_PURPLE)

    canvas.add_page_numbers()
    output = BytesIO()
    canvas.document.save(output, garbage=4, deflate=True)
    canvas.document.close()
    return output.getvalue()


def publish_proposal_pdf(
    *,
    client,
    company_id: str,
    project_id: str,
    version_id: str,
    run_id: str,
    snapshot: dict[str, Any],
) -> str:
    profile_rows = (
        client.table("companies")
        .select(
            "company_name,legal_name,public_email,public_phone,website_url,"
            "address_street,address_house_number,address_city,address_postal_code,address_country,"
            "facebook_url,linkedin_url,instagram_url,logo_url"
        )
        .eq("company_id", company_id)
        .limit(1)
        .execute().data or []
    )
    run_rows = (
        client.table("rfq_runs")
        .select("project_name,design_partner,client")
        .eq("run_id", run_id)
        .eq("company_id", company_id)
        .limit(1)
        .execute().data or []
    )
    if not run_rows:
        raise RuntimeError("Project metadata is unavailable for the proposal")
    profile = dict(profile_rows[0]) if profile_rows else {}
    run = dict(run_rows[0])
    try:
        logo_bytes = load_company_logo_bytes(
            client=client,
            company_id=company_id,
            reference=_clean(profile.get("logo_url")) or None,
        )
    except Exception:
        logo_bytes = None
    pdf_bytes = build_proposal_pdf(
        profile=profile,
        project_name=_clean(run.get("project_name")),
        partner_name=_clean(run.get("design_partner")),
        client_name=_clean(run.get("client")),
        snapshot=snapshot,
        logo_bytes=logo_bytes,
    )
    object_path = f"{company_id}/{project_id}/{version_id}.pdf"
    client.storage.from_(PROPOSAL_BUCKET).upload(
        object_path,
        pdf_bytes,
        file_options={
            "content-type": "application/pdf",
            "cache-control": "3600",
            "upsert": "true",
        },
    )
    response = (
        client.table("project_versions")
        .update({"proposal_pdf_path": object_path})
        .eq("company_id", company_id)
        .eq("version_id", version_id)
        .execute()
    )
    if len(response.data or []) != 1:
        raise RuntimeError("The proposal reference was not saved")
    return object_path


def _filename_part(value: object, fallback: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", _clean(value))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._-")
    return cleaned or fallback


def proposal_download_name(
    *, project_name: object, partner_name: object, approved_at: object
) -> str:
    date_value = _clean(approved_at)
    try:
        date_value = datetime.fromisoformat(date_value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        date_value = date_value[:10] or datetime.now().date().isoformat()
    return (
        f"{_filename_part(project_name, 'Project')}_"
        f"{_filename_part(partner_name, 'Partner')}_"
        f"{_filename_part(date_value, 'Date')}.pdf"
    )


def proposal_signed_url(
    client,
    object_path: str,
    *,
    expires_in: int = 3600,
    download_name: str | None = None,
) -> str | None:
    if not object_path:
        return None
    options = {"download": download_name} if download_name else None
    response = client.storage.from_(PROPOSAL_BUCKET).create_signed_url(
        object_path,
        expires_in,
        options=options,
    )
    return response.get("signedURL") or response.get("signedUrl")


def load_estimate_proposal_url(*, client, company_id: str, estimate_id: str) -> str | None:
    rows = (
        client.table("project_versions")
        .select("proposal_pdf_path,run_id,approved_at")
        .eq("company_id", company_id)
        .eq("estimate_id", estimate_id)
        .limit(1)
        .execute().data or []
    )
    if not rows:
        return None
    version = rows[0]
    run_rows = (
        client.table("rfq_runs")
        .select("project_name,design_partner")
        .eq("company_id", company_id)
        .eq("run_id", version.get("run_id"))
        .limit(1)
        .execute().data or []
    )
    run = run_rows[0] if run_rows else {}
    download_name = proposal_download_name(
        project_name=run.get("project_name"),
        partner_name=run.get("design_partner"),
        approved_at=version.get("approved_at"),
    )
    return proposal_signed_url(
        client,
        _clean(version.get("proposal_pdf_path")),
        download_name=download_name,
    )
