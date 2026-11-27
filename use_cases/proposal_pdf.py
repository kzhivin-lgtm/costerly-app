from __future__ import annotations

from contextlib import nullcontext
import base64
from datetime import datetime, UTC
import re
from typing import Any

from use_cases.company_logo import load_company_logo_bytes
from use_cases.detection_previews import saved_presentation_preview_ref
from use_cases.estimation_artifacts import download_evidence_artifact
from use_cases.proposal_document import render_proposal, optional_metadata
from use_cases.proposal_basis import pricing_signature
from use_cases.estimation_originals import stored_original_from_metadata, stored_original_metadata

PROPOSAL_BUCKET = "project-proposals"
PROFILE_COLUMNS = (
    "company_name,legal_name,legal_name_hebrew,company_registration_number,vat_file_number,"
    "public_email,public_phone,website_url,address_street,address_house_number,address_city,"
    "address_postal_code,address_country,bank_name,bank_number,branch_number,account_number,iban,swift,logo_url"
)


def _clean(value):
    return str(value or '').strip()


def _address(profile):
    street=' '.join(_clean(profile.get(k)) for k in ('address_street','address_house_number') if _clean(profile.get(k)))
    city=' '.join(_clean(profile.get(k)) for k in ('address_city','address_postal_code') if _clean(profile.get(k)))
    return ', '.join(v for v in (street,city,_clean(profile.get('address_country'))) if v)


def _contact_lines(profile):
    return [line for line in (_clean(profile.get('public_email')),_clean(profile.get('public_phone')),
                             _clean(profile.get('website_url')),_address(profile)) if line]


def capture_proposal_document(*, client,company_id,run_id,snapshot):
    """Capture metadata once. Logos survive replacement; crops keep immutable refs."""
    profiles=client.table('companies').select(PROFILE_COLUMNS).eq('company_id',company_id).limit(1).execute().data or []
    runs=client.table('rfq_runs').select('project_name,design_partner,client,file_name').eq('company_id',company_id).eq('run_id',run_id).limit(1).execute().data or []
    if not runs:raise RuntimeError('Project metadata is unavailable for the proposal')
    profile=dict(profiles[0]) if profiles else {}
    logo=load_company_logo_bytes(client=client,company_id=company_id,reference=_clean(profile.get('logo_url')) or None)
    wanted={str(row.get('object_key')) for row in snapshot.get('rows') or []}
    objects=client.table('rfq_detected_objects').select('object_id,evidence_page_refs').eq('company_id',company_id).eq('run_id',run_id).execute().data or []
    previews={}
    for obj in objects:
        oid=str(obj.get('object_id'))
        ref=saved_presentation_preview_ref(obj)
        prefix=f'storage://rfq-estimation-evidence/{company_id}/{run_id}/{oid}/'
        if oid in wanted and ref and ref.startswith(prefix) and '..' not in ref.removeprefix(prefix).split('/'):
            previews[oid]=ref
    source = capture_proposal_source(client=client,company_id=company_id,run_id=run_id,file_name=runs[0].get('file_name'))
    return {'template':'labor-v3','issued_at':datetime.now(UTC).isoformat(), 'timezone':'Asia/Jerusalem', 'source':source,
            'company_id':company_id,'run_id':run_id,'profile':profile,'project':dict(runs[0]),
            'logo_base64':base64.b64encode(logo).decode() if logo else None,'previews':previews}


def capture_proposal_source(*, client,company_id,run_id,file_name):
    """Reuse the uploaded private original's immutable content identity, no copy."""
    events = (client.table('agent_usage_events').select('raw_usage')
              .eq('company_id',company_id).eq('run_id',run_id)
              .in_('operation',['rfq_source_original','rfq_processing_cycle'])
              .order('created_at',desc=True).execute().data or [])
    for event in events:
        usage = event.get('raw_usage') or {}
        if isinstance(usage,str):
            import json
            try: usage = json.loads(usage)
            except ValueError: continue
        stored = stored_original_from_metadata(usage.get('estimation_original') if isinstance(usage,dict) else None)
        if not stored:
            continue
        prefix=f'storage://rfq-estimation-originals/{company_id}/'
        if not stored.storage_ref.startswith(prefix) or '..' in stored.storage_ref.removeprefix(prefix).split('/'):
            raise ValueError('Proposal source does not belong to this company')
        return {**stored_original_metadata(stored),'file_name':file_name}
    return None


def build_proposal_pdf(*,profile,project_name,partner_name,client_name,snapshot,logo_bytes=None,preview_bytes=None):
    return render_proposal(profile=profile,project_name=project_name,partner_name=partner_name,
                           client_name=client_name,snapshot=snapshot,logo_bytes=logo_bytes,preview_bytes=preview_bytes)


def publish_proposal_pdf(*,client,company_id,project_id,version_id,run_id,snapshot,trace=None):
    document=snapshot.get('document') or capture_proposal_document(client=client,company_id=company_id,run_id=run_id,snapshot=snapshot)
    if str(document.get('company_id'))!=str(company_id) or str(document.get('run_id'))!=str(run_id):
        raise ValueError('Proposal snapshot does not belong to this company and project')
    run=document.get('project') or {}
    with trace.span('server.proposal_assets') if trace else nullcontext():
        previews={}
        for oid,ref in (document.get('previews') or {}).items():
            prefix=f'storage://rfq-estimation-evidence/{company_id}/{run_id}/{oid}/'
            if not isinstance(ref,str) or not ref.startswith(prefix) or '..' in ref.removeprefix(prefix).split('/'):
                raise ValueError('Proposal preview does not belong to this project')
            previews[oid]=download_evidence_artifact(client=client,storage_ref=ref)
    encoded=document.get('logo_base64')
    logo=base64.b64decode(encoded,validate=True) if encoded else None
    with trace.span('server.proposal_render') if trace else nullcontext():
        pdf_bytes=build_proposal_pdf(profile=document.get('profile') or {},project_name=_clean(run.get('project_name')),
                                   partner_name=_clean(run.get('design_partner')),client_name=_clean(run.get('client')),
                                   snapshot={**snapshot,'document':document},logo_bytes=logo,preview_bytes=previews)
    object_path=f'{company_id}/{project_id}/{version_id}.pdf'
    # The version snapshot is immutable; deterministic retry writes the same document.
    with trace.span('server.proposal_upload') if trace else nullcontext():
        client.storage.from_(PROPOSAL_BUCKET).upload(object_path,pdf_bytes,
            file_options={'content-type':'application/pdf','cache-control':'3600','upsert':'true'})
    with trace.span('server.proposal_reference_save') if trace else nullcontext():
        response=client.table('project_versions').update({'proposal_pdf_path':object_path}).eq('company_id',company_id).eq('version_id',version_id).execute()
    if len(response.data or [])!=1:raise RuntimeError('The proposal reference was not saved')
    return object_path


def _filename_part(value: object, fallback: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", _clean(value))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._-")
    return cleaned or fallback


def proposal_download_name(
    *, project_name: object, partner_name: object, version_number: object, approved_at: object = None
) -> str:
    parts = [_filename_part(optional_metadata(value), '') for value in (project_name, partner_name)]
    parts.append(f'V{int(version_number)}')
    return '_'.join(part for part in parts if part) + '.pdf'


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


def load_estimate_proposal_url(*, client, company_id: str, estimate_id: str,
                               current_data: dict | None = None, version_id: str | None = None) -> str | None:
    query = (
        client.table("project_versions")
        .select("proposal_pdf_path,run_id,version_id,version_number,approved_at,"
                "proposal_basis_sha256:snapshot->>proposal_basis_sha256,"
                "profile:snapshot->document->profile,project:snapshot->document->project")
        .eq("company_id", company_id)
        .eq("estimate_id", estimate_id)
    )
    if version_id:
        query = query.eq('version_id', version_id)
    rows = query.order('version_number', desc=True).limit(1).execute().data or []
    if not rows:
        return None
    version = rows[0]
    frozen = version.get('snapshot') or {}
    stored_basis = version.get('proposal_basis_sha256') or frozen.get('proposal_basis_sha256')
    if current_data is not None and not stored_basis and not frozen:
        # Legacy snapshots predate the small basis receipt. Only these need the
        # full snapshot read; never transfer the new complete calculation here.
        legacy = (client.table('project_versions').select('snapshot').eq('company_id',company_id)
                  .eq('estimate_id',estimate_id).eq('version_id',version['version_id']).limit(1).execute().data or [])
        frozen = legacy[0].get('snapshot') or {} if legacy else {}
    document = frozen.get('document') or {
        **({'profile':version['profile']} if version.get('profile') is not None else {}),
        **({'project':version['project']} if version.get('project') is not None else {}),
    }
    run = document.get('project')
    if current_data is not None:
        comparison = current_data
        if not stored_basis and 'proposal_source' not in frozen:
            # Earlier issued files have no input-revision receipt. Compare the
            # complete saved commercial fields they did capture, without migration.
            comparison = {**current_data, 'proposal_source': None,
                          'rows': [{**row, 'proposal_input_basis': None} for row in current_data.get('rows') or []]}
        if pricing_signature(comparison) != (stored_basis or pricing_signature(frozen)):
            return None
        if 'profile' in document:
            profiles = (client.table('companies').select(PROFILE_COLUMNS).eq('company_id',company_id)
                        .limit(1).execute().data or [])
            profile = profiles[0] if profiles else {}
            saved_profile = document['profile']
            if any(_clean(profile.get(k)) != _clean(saved_profile.get(k)) for k in PROFILE_COLUMNS.split(',')):
                return None
    run_rows = (
        client.table("rfq_runs")
        .select("project_name,design_partner")
        .eq("company_id", company_id)
        .eq("run_id", version.get("run_id"))
        .limit(1)
        .execute().data or []
    ) if run is None else []
    run = run if run is not None else run_rows[0] if run_rows else {}
    download_name = proposal_download_name(
        project_name=run.get("project_name"),
        partner_name=run.get("design_partner"),
        version_number=version['version_number'],
        approved_at=version.get('approved_at'),
    )
    return proposal_signed_url(
        client,
        _clean(version.get("proposal_pdf_path")),
        download_name=download_name,
    )
