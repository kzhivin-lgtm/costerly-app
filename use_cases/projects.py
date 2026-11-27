from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from db.supabase_client import get_supabase_client
from use_cases.proposal_pdf import proposal_download_name, PROPOSAL_BUCKET


def load_projects_workspace(company_id: str) -> dict[str, list[dict[str, Any]]]:
    """Load the company-scoped Partner, Project, and Version hierarchy."""
    client = get_supabase_client()
    def read_all(table, columns, order):
        rows=[];offset=0
        while True:
            response=(client.table(table).select(columns,count='exact').eq('company_id',company_id)
                      .order(order).range(offset,offset+499).execute())
            batch=response.data or [];rows.extend(batch);offset+=len(batch)
            count=getattr(response,'count',None)
            if count is not None and offset>=count:return rows
            if not batch:
                if count is not None and offset<count:raise RuntimeError('Project history response was incomplete')
                return rows
            if count is None and len(batch)<500:return rows

    with ThreadPoolExecutor(max_workers=4) as executor:
        organizations_future=executor.submit(read_all,'organizations','organization_id,name,is_partner,is_client,updated_at','organization_id')
        projects_future=executor.submit(read_all,'projects','project_id,partner_organization_id,client_organization_id,name,status,updated_at','project_id')
        versions_future=executor.submit(read_all,'project_versions',
            'version_id,project_id,source_file_id,version_number,run_id,estimate_id,status,approved_at,summary,proposal_pdf_path,objects:snapshot->rows,project_metadata:snapshot->document->project,timezone:snapshot->document->timezone','version_id')
        files_future=executor.submit(read_all,'project_files','file_id,project_id,file_name,content_sha256,created_at','file_id')
        organizations=organizations_future.result();projects=projects_future.result()
        versions=versions_future.result();files=files_future.result()
    organizations.sort(key=lambda r:str(r.get('name') or '').casefold())
    projects.sort(key=lambda r:str(r.get('updated_at') or ''),reverse=True)
    versions.sort(key=lambda r:int(r.get('version_number') or 0),reverse=True)
    project_by_id={str(p.get('project_id')):p for p in projects}
    organization_by_id={str(o.get('organization_id')):o for o in organizations}
    paths={}
    for version in versions:
        project_id=str(version.get('project_id') or '')
        path=str(version.get('proposal_pdf_path') or '')
        version['proposal_pdf_url']=None
        if project_id in project_by_id and path==f"{company_id}/{project_id}/{version.get('version_id')}.pdf":
            paths[path]=version
    # One batched signing request per500 files, independent of accordion clicks.
    # Reuse the SDK's download-query convention with each frozen version's name.
    for offset in range(0,len(paths),500):
        batch=list(paths)[offset:offset+500]
        try:
            signed=client.storage.from_(PROPOSAL_BUCKET).create_signed_urls(batch,3600)
            for item in signed:
                path=item.get('path');url=item.get('signedURL') or item.get('signedUrl')
                if path not in paths or not url or item.get('error'):continue
                version=paths[path];project=project_by_id[str(version['project_id'])]
                partner=organization_by_id.get(str(project.get('partner_organization_id') or ''),{})
                metadata=version.get('project_metadata') or {}
                name=proposal_download_name(project_name=metadata.get('project_name',project.get('name')),
                    partner_name=metadata.get('design_partner',partner.get('name')),version_number=version['version_number'])
                parts=urlsplit(url);query=dict(parse_qsl(parts.query));query['download']=name
                version['proposal_pdf_url']=urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(query),parts.fragment))
        except Exception:
            # Preserve the established actionable page even if signing fails;
            # the ordinary missing-PDF slot remains, navigation retries reads.
            pass
    return {
        "organizations": [row for row in organizations if row.get("is_partner")],
        "clients": [row for row in organizations if row.get("is_client")],
        "projects": list(projects),
        "versions": list(versions),
        "files": list(files),
    }
