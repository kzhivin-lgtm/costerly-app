from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import secrets
import uuid
from urllib.parse import urlsplit, urlunsplit

import streamlit as st

from config import get_optional_secret
from use_cases.invite_links import DEFAULT_PUBLIC_APP_URL, invite_token_hash, public_app_url


TERMS_CHECKBOX_TEXT = "I have read and agree to the Terms and Conditions"
TERMS_SUMMARY = (
    "These Terms govern professional use of Coasterly AI, organization access, "
    "Customer Content, AI-assisted output, plans and usage limits, confidentiality, "
    "cancellation, warranties, liability and other service conditions"
)
TERMS_INLINE_TEXT = """
**Professional service.** Coasterly AI is for organizations and professional
use. A person creating an Organization Account represents that they have
authority to act for that organization and accept the Terms for it.

**Account access.** The organization is responsible for the access it grants,
its users' activity and the security of its credentials.

**Customer Content.** Customer Content remains owned by the customer or the
applicable rights holder. The customer confirms it has the rights and
permissions needed to upload and process it. Coasterly AI may process and send
Customer Content to authorized service providers only as needed to provide,
secure and support the service.

**Confidentiality and AI providers.** Customer Content may include confidential
drawings, RFQs, BOMs, prices and specifications. Coasterly AI uses it to provide
the service and may use hosting, database, monitoring and AI providers,
including OpenAI, Anthropic and Google. Customer Content is not used to train
Coasterly AI's own general-purpose models and must not be used for general
model training by configured AI providers where their applicable service terms
provide that protection.

**Output.** AI-assisted output may be incomplete or incorrect. The customer
must review dimensions, quantities, materials, prices and other results before
use. Coasterly AI does not provide regulated professional advice.

**Plans and usage.** Pilots, Trial Periods and paid Plans may have different
features, users, Included Usage, tokens, credits and processing limits. A Plan
is not unlimited unless its offer expressly says so. Operations may consume
different usage based on type, size and complexity.

**Billing.** Cancellation stops the next renewal. Started billing periods,
consumed usage and unused Included Usage are non-refundable except where law
requires otherwise.

**Storage.** Customer Content may remain stored after a project or account is
removed. Customers may request permanent deletion, subject to reasonable
processing time, limited backups and legal obligations.

**Availability and responsibility.** The service may change and may sometimes
be unavailable. It does not promise uninterrupted operation, absolute accuracy
or a particular processing volume. The full Terms contain the applicable use,
suspension, warranty, liability, indemnity and change provisions.
"""
SUPPORT_EMAIL = "hello@costerly.ai"


@dataclass(frozen=True)
class LegalDocument:
    document_type: str
    version: str
    acceptance_version: str
    title: str
    effective_at: str
    content_sha256: str
    public_path: str
    requires_reacceptance: bool


@dataclass(frozen=True)
class LegalDocumentSet:
    terms: LegalDocument
    privacy: LegalDocument


def legal_consent_enabled() -> bool:
    """Keep the cross-system rollout off until DB, Auth email, and Pages agree."""
    return str(get_optional_secret("LEGAL_CONSENT_ENABLED", "false")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def public_legal_url(path: str) -> str:
    base = public_app_url(
        get_optional_secret("COSTERLY_PUBLIC_URL") or DEFAULT_PUBLIC_APP_URL
    )
    parts = urlsplit(base)
    normalized = "/" + str(path or "").lstrip("/")
    return urlunsplit((parts.scheme, parts.netloc, normalized, "", ""))


def email_confirmation_url() -> str:
    return public_legal_url("/confirm")


def _document_from_row(row: dict[str, object]) -> LegalDocument:
    return LegalDocument(
        document_type=str(row["document_type"]),
        version=str(row["version"]),
        acceptance_version=str(row["acceptance_version"]),
        title=str(row["title"]),
        effective_at=str(row["effective_at"]),
        content_sha256=str(row["content_sha256"]),
        public_path=str(row["public_path"]),
        requires_reacceptance=bool(row.get("requires_reacceptance")),
    )


def current_legal_documents(server_client) -> LegalDocumentSet:
    """Resolve immutable documents only through the mutable release pointers."""
    documents: dict[str, LegalDocument] = {}
    for document_type in ("terms", "privacy"):
        release_rows = (
            server_client.table("legal_document_releases")
            .select("version")
            .eq("document_type", document_type)
            .limit(1)
            .execute()
        ).data or []
        if not release_rows:
            raise RuntimeError(f"Current {document_type} document is not published")
        version = str(release_rows[0]["version"])
        rows = (
            server_client.table("legal_documents")
            .select(
                "document_type,version,acceptance_version,title,effective_at,"
                "content_sha256,public_path,requires_reacceptance,published_at"
            )
            .eq("document_type", document_type)
            .eq("version", version)
            .limit(1)
            .execute()
        ).data or []
        if not rows or not rows[0].get("published_at"):
            raise RuntimeError(f"Current {document_type} document is not published")
        documents[document_type] = _document_from_row(rows[0])
    return LegalDocumentSet(terms=documents["terms"], privacy=documents["privacy"])


def _request_evidence() -> tuple[str, str]:
    """Return provider-observed request evidence, never browser-supplied form data."""
    ip_value = str(getattr(st.context, "ip_address", "") or "").strip()
    if ip_value:
        try:
            ip_value = str(ipaddress.ip_address(ip_value))
        except ValueError:
            ip_value = ""
    try:
        user_agent = str(st.context.headers.get("User-Agent", "") or "")[:1024]
    except Exception:
        user_agent = ""
    return ip_value, user_agent


def record_pending_registration(
    server_client,
    *,
    user_id: str,
    email: str,
    invitation_kind: str,
    invitation_token: str,
    organization_name: str | None,
    documents: LegalDocumentSet,
) -> str:
    registration_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    ip_address, user_agent = _request_evidence()
    result = server_client.rpc(
        "begin_verified_legal_registration",
        {
            "p_registration_id": registration_id,
            "p_user_id": user_id,
            "p_email": email.strip(),
            "p_invitation_kind": invitation_kind,
            "p_invitation_token_hash": invite_token_hash(invitation_token),
            "p_organization_name": (organization_name or "").strip() or None,
            "p_terms_version": documents.terms.version,
            "p_terms_acceptance_version": documents.terms.acceptance_version,
            "p_terms_sha256": documents.terms.content_sha256,
            "p_privacy_version": documents.privacy.version,
            "p_privacy_sha256": documents.privacy.content_sha256,
            "p_checkbox_text": TERMS_CHECKBOX_TEXT,
            "p_request_id": request_id,
            "p_ip_address": ip_address or None,
            "p_user_agent": user_agent or None,
        },
    ).execute()
    event_id = str(result.data or "")
    if not event_id:
        raise RuntimeError("Terms acceptance was not recorded")
    return event_id


def pending_registration_for_user(server_client, user_id: str) -> dict[str, object] | None:
    rows = (
        server_client.table("pending_legal_registrations")
        .select(
            "registration_id,user_id,email,invitation_kind,"
            "represented_organization_name,target_company_id,completed_at,"
            "completed_company_id"
        )
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    ).data or []
    return dict(rows[0]) if rows else None


def complete_pending_registration(server_client, user_id: str) -> str:
    """Atomically consume the saved invitation after Supabase verified email."""
    attempted_ids: set[str] = set()
    for _ in range(12):
        company_id = f"{secrets.randbelow(999) + 1:03d}"
        if company_id in attempted_ids:
            continue
        attempted_ids.add(company_id)
        try:
            result = server_client.rpc(
                "complete_verified_legal_registration",
                {"p_user_id": user_id, "p_new_company_id": company_id},
            ).execute()
            completed = str(result.data or "")
            if not completed:
                raise RuntimeError("Verified registration did not return company access")
            return completed
        except Exception as exc:
            if str(getattr(exc, "code", "")) != "23505":
                raise
    raise RuntimeError("No available company ID was allocated. Contact support")


def terms_acceptance_required(server_client, user_id: str) -> bool:
    documents = current_legal_documents(server_client)
    rows = (
        server_client.table("legal_acceptance_events")
        .select("event_id")
        .eq("user_id", user_id)
        .eq("terms_acceptance_version", documents.terms.acceptance_version)
        .limit(1)
        .execute()
    ).data or []
    return not bool(rows)


def record_current_terms_acceptance(
    server_client,
    *,
    user_id: str,
    company_id: str,
    email: str,
) -> str:
    ip_address, user_agent = _request_evidence()
    result = server_client.rpc(
        "record_current_terms_acceptance",
        {
            "p_user_id": user_id,
            "p_company_id": company_id,
            "p_email": email,
            "p_checkbox_text": TERMS_CHECKBOX_TEXT,
            "p_request_id": str(uuid.uuid4()),
            "p_ip_address": ip_address or None,
            "p_user_agent": user_agent or None,
        },
    ).execute()
    event_id = str(result.data or "")
    if not event_id:
        raise RuntimeError("Terms acceptance was not recorded")
    return event_id
