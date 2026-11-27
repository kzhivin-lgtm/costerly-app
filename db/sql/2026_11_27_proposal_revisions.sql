-- Labor V3.3: Partner -> Project -> immutable source files -> calculation/proposal
-- revisions. Existing rows/snapshots/PDFs remain unchanged; legacy source is NULL.

begin;
create table if not exists public.project_files (
    file_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id) on delete cascade,
    project_id uuid not null,
    content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
    source_file_path text not null,
    file_name text,
    mime_type text not null,
    size_bytes bigint not null check (size_bytes > 0),
    created_at timestamptz not null default now(),
    foreign key (project_id, company_id) references public.projects(project_id,company_id) on delete cascade,
    unique (project_id,content_sha256),
    unique (file_id,company_id,project_id)
);
alter table public.project_files enable row level security;
drop policy if exists project_files_company_member_read on public.project_files;
create policy project_files_company_member_read on public.project_files for select to authenticated
using (exists (select 1 from public.company_members m
               where m.company_id=project_files.company_id and m.user_id=(select auth.uid())));
revoke all on public.project_files from public, anon, authenticated;
grant select on public.project_files to authenticated;
grant all on public.project_files to service_role;

alter table public.project_versions add column if not exists source_file_id uuid;
do $$ begin
    if not exists (select 1 from pg_constraint where conrelid='public.project_versions'::regclass
                   and conname='project_versions_source_file_company_fk') then
        alter table public.project_versions add constraint project_versions_source_file_company_fk
            foreign key (source_file_id,company_id,project_id)
            references public.project_files(file_id,company_id,project_id);
    end if;
end $$;
-- Keep immutable history, allow multiple confirmed revisions of one estimate.
alter table public.project_versions
    drop constraint if exists project_versions_company_id_estimate_id_key;
create unique index if not exists project_versions_proposal_request_key
    on public.project_versions(company_id, estimate_id, (snapshot->>'proposal_request_id'))
    where snapshot->>'proposal_request_id' is not null;
create index if not exists project_versions_estimate_revision_idx
    on public.project_versions(company_id, estimate_id, version_number desc);

create or replace function public.finalize_project_estimate(
    p_company_id text,
    p_run_id text,
    p_estimate_id text,
    p_snapshot jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_project_name text;
    v_partner_name text;
    v_client_name text;
    v_project_normalized text;
    v_partner_normalized text;
    v_client_normalized text;
    v_partner_id uuid;
    v_client_id uuid;
    v_project_id uuid;
    v_version_id uuid;
    v_version_number integer;
    v_request_id text;
    v_source_path text;
    v_source_hash text;
    v_source_file_id uuid;
    v_target_project_id uuid;
begin
    if not exists (
        select 1 from public.rfq_runs r
        where r.run_id = p_run_id and r.company_id = p_company_id
    ) or not exists (
        select 1 from public.rfq_estimates e
        where e.estimate_id = p_estimate_id
          and e.run_id = p_run_id
          and e.company_id = p_company_id
    ) then
        raise exception 'RFQ or estimate is not available to this company';
    end if;

    if exists (
        select 1 from public.rfq_object_estimates o
        where o.estimate_id = p_estimate_id
          and (not o.approved or o.status not in ('completed', 'review_required')
               or o.self_cost_ex_vat is null)
    ) or not exists (
        select 1 from public.rfq_object_estimates o where o.estimate_id = p_estimate_id
    ) then
        raise exception 'Every object must be priced and approved before Final Approval';
    end if;

    select trim(r.project_name), trim(r.design_partner), trim(r.client)
    into v_project_name, v_partner_name, v_client_name
    from public.rfq_runs r where r.run_id = p_run_id;

    -- Missing presentation metadata stays NULL, never a fabricated entity.
    if coalesce(lower(v_project_name), '') in ('', 'unknown', 'none', 'null', '-', '—') then
        v_project_name := null;
    end if;
    if coalesce(lower(v_partner_name), '') in ('', 'unknown', 'none', 'null', '-', '—') then
        v_partner_name := null;
    end if;
    if coalesce(lower(v_client_name), '') in ('', 'unknown', 'none', 'null', '-', '—') then
        v_client_name := null;
    end if;
    if p_snapshot is null or jsonb_typeof(p_snapshot) <> 'object' then
        raise exception 'Final Approval snapshot is required';
    end if;
    v_source_path := p_snapshot#>>'{document,source,storage_ref}';
    v_target_project_id := nullif(p_snapshot->>'target_project_id','')::uuid;
    if v_target_project_id is not null and not exists (
        select 1 from public.projects p where p.project_id=v_target_project_id and p.company_id=p_company_id
    ) then
        raise exception 'Project is not available to this company';
    end if;
    v_source_hash := p_snapshot#>>'{document,source,content_sha256}';
    if v_source_path is not null and (
        strpos(v_source_path, 'storage://rfq-estimation-originals/' || p_company_id || '/') <> 1
        or '..' = any(string_to_array(v_source_path, '/'))
    ) then
        raise exception 'Proposal source does not belong to this company';
    end if;
    if v_source_path is not null and (
        coalesce(v_source_hash,'') !~ '^[0-9a-f]{64}$'
        or coalesce((p_snapshot#>>'{document,source,size_bytes}')::bigint,0) <= 0
        or coalesce(p_snapshot#>>'{document,source,mime_type}','') = ''
    ) then
        raise exception 'Invalid proposal source identity';
    end if;

    v_project_normalized := lower(regexp_replace(v_project_name, '\s+', ' ', 'g'));
    v_partner_normalized := lower(regexp_replace(v_partner_name, '\s+', ' ', 'g'));

    v_request_id := nullif(p_snapshot->>'proposal_request_id', '');
    if v_request_id is not null and v_request_id !~ '^[0-9a-f]{32}$' then
        raise exception 'Invalid proposal revision request';
    end if;
    -- Serialize a draft even when its presentation name/partner has changed.
    perform pg_advisory_xact_lock(hashtextextended('proposal-estimate:' || p_company_id || ':' || p_estimate_id, 0));

    -- Serialize creation by logical project, or by RFQ for unnamed projects.
    -- NULL values cannot rely on the legacy named-project unique constraint.
    perform pg_advisory_xact_lock(hashtextextended(
        'proposal:' || p_company_id || ':' || coalesce(v_partner_normalized, '') || ':' ||
        case when v_project_normalized is null then 'rfq:' || p_run_id
             else 'name:' || v_project_normalized end, 0));

    -- Retry returns the original association before creating any new entities.
    select pv.project_id, pv.version_id, pv.version_number, p.partner_organization_id, pv.source_file_id
    into v_project_id, v_version_id, v_version_number, v_partner_id, v_source_file_id
    from public.project_versions pv
    join public.projects p on p.project_id = pv.project_id and p.company_id = pv.company_id
    where pv.company_id = p_company_id and pv.estimate_id = p_estimate_id
      and (v_request_id is null or pv.snapshot->>'proposal_request_id' = v_request_id)
    order by pv.version_number desc limit 1;
    if v_version_id is not null then
        if v_target_project_id is not null and v_target_project_id<>v_project_id then
            raise exception 'An issued estimate cannot be moved to another project';
        end if;
        return jsonb_build_object(
            'organization_id', v_partner_id, 'project_id', v_project_id,
            'version_id', v_version_id, 'version_number', v_version_number,
            'source_file_id', v_source_file_id, 'created', false);
    end if;

    -- New revisions of this estimate retain its stable project association.
    select pv.project_id, p.partner_organization_id into v_project_id, v_partner_id
    from public.project_versions pv
    join public.projects p on p.project_id = pv.project_id and p.company_id = pv.company_id
    where pv.company_id = p_company_id and pv.estimate_id = p_estimate_id
    order by pv.version_number desc limit 1;
    if v_project_id is not null and v_target_project_id is not null and v_target_project_id<>v_project_id then
        raise exception 'An issued estimate cannot be moved to another project';
    end if;
    if v_project_id is null and v_target_project_id is not null then
        v_project_id := v_target_project_id;
        select partner_organization_id into v_partner_id from public.projects where project_id=v_project_id and company_id=p_company_id;
    end if;

    if v_project_id is null then
    if v_partner_name is not null then
        insert into public.organizations(company_id, name, normalized_name, is_partner, is_client)
        values (p_company_id, v_partner_name, v_partner_normalized, true, false)
        on conflict (company_id, normalized_name) do update
        set is_partner = true, name = excluded.name, updated_at = now()
        returning organization_id into v_partner_id;
    end if;
    if v_client_name is not null then
        v_client_normalized := lower(regexp_replace(v_client_name, '\s+', ' ', 'g'));
        insert into public.organizations(company_id, name, normalized_name, is_partner, is_client)
        values (p_company_id, v_client_name, v_client_normalized, false, true)
        on conflict (company_id, normalized_name) do update
        set is_client = true, name = excluded.name, updated_at = now()
        returning organization_id into v_client_id;
    end if;

    select p.project_id into v_project_id
    from public.projects p
    where p.company_id = p_company_id
      and p.partner_organization_id is not distinct from v_partner_id
      and p.normalized_name is not distinct from v_project_normalized
      and (v_project_normalized is not null or exists (
          select 1 from public.project_versions pv
          where pv.project_id = p.project_id and pv.company_id = p_company_id and pv.run_id = p_run_id))
    order by p.created_at limit 1 for update;
    if v_project_id is null then
        insert into public.projects(company_id, partner_organization_id, client_organization_id, name, normalized_name)
        values (p_company_id, v_partner_id, v_client_id, v_project_name, v_project_normalized)
        returning project_id into v_project_id;
    else
        update public.projects
        set client_organization_id = coalesce(v_client_id, client_organization_id),
            name = v_project_name, updated_at = now()
        where project_id = v_project_id and company_id = p_company_id;
    end if;

    end if;

    perform pg_advisory_xact_lock(hashtextextended(v_project_id::text, 0));
    if v_source_path is not null then
        insert into public.project_files(company_id,project_id,content_sha256,source_file_path,file_name,mime_type,size_bytes)
        values (p_company_id,v_project_id,v_source_hash,v_source_path,
                p_snapshot#>>'{document,source,file_name}',p_snapshot#>>'{document,source,mime_type}',
                (p_snapshot#>>'{document,source,size_bytes}')::bigint)
        on conflict (project_id,content_sha256) do nothing;
        select file_id into v_source_file_id from public.project_files
        where project_id=v_project_id and company_id=p_company_id and content_sha256=v_source_hash;
    end if;
    select coalesce(max(pv.version_number), 0) + 1
    into v_version_number
    from public.project_versions pv where pv.project_id = v_project_id;

    insert into public.project_versions(
        company_id, project_id, version_number, run_id, estimate_id,
        summary, snapshot, source_file_path, source_file_id
    ) values (
        p_company_id, v_project_id, v_version_number, p_run_id, p_estimate_id,
        coalesce(p_snapshot->'summary', '{}'::jsonb),
        p_snapshot || jsonb_build_object('calculation',jsonb_build_object(
            'estimate',(select to_jsonb(e) from public.rfq_estimates e where e.estimate_id=p_estimate_id and e.company_id=p_company_id),
            'objects',(select coalesce(jsonb_agg(to_jsonb(o)), '[]'::jsonb) from public.rfq_object_estimates o where o.estimate_id=p_estimate_id),
            'lines',(select coalesce(jsonb_agg(to_jsonb(l) order by l.line_id), '[]'::jsonb) from public.rfq_estimate_lines l where l.estimate_id=p_estimate_id and l.company_id=p_company_id),
            'material_plan',(select to_jsonb(m) from public.rfq_estimate_material_plans m where m.estimate_id=p_estimate_id and m.company_id=p_company_id),
            'pricing_overrides',(select coalesce(jsonb_agg(to_jsonb(p)), '[]'::jsonb) from public.rfq_estimate_pricing_overrides p where p.estimate_id=p_estimate_id),
            'norm_overrides',(select coalesce(jsonb_agg(to_jsonb(n)), '[]'::jsonb) from public.rfq_estimate_material_norm_overrides n where n.estimate_id=p_estimate_id and n.company_id=p_company_id),
            'purchase_overrides',(select coalesce(jsonb_agg(to_jsonb(b)), '[]'::jsonb) from public.rfq_estimate_material_purchase_overrides b where b.estimate_id=p_estimate_id and b.company_id=p_company_id)
        )), v_source_path, v_source_file_id
    ) returning version_id into v_version_id;
    update public.projects set updated_at=now() where project_id=v_project_id and company_id=p_company_id;

    return jsonb_build_object(
        'organization_id', v_partner_id,
        'project_id', v_project_id,
        'version_id', v_version_id,
        'version_number', v_version_number,
        'source_file_id', v_source_file_id,
        'created', true
    );
end;
$$;

-- The application may acknowledge the first PDF upload or change status. Issued
-- source, commercial snapshot and identifiers must never be rewritten in place.
create or replace function public.protect_issued_project_version() returns trigger
language plpgsql set search_path=public as $$
begin
    if (new.version_id,new.company_id,new.project_id,new.version_number,new.run_id,new.estimate_id,
        new.approved_at,new.created_at,new.summary,new.snapshot,new.source_file_path,new.source_file_id)
       is distinct from
       (old.version_id,old.company_id,old.project_id,old.version_number,old.run_id,old.estimate_id,
        old.approved_at,old.created_at,old.summary,old.snapshot,old.source_file_path,old.source_file_id)
       or (old.proposal_pdf_path is not null and new.proposal_pdf_path is distinct from old.proposal_pdf_path) then
        raise exception 'Issued project versions are immutable';
    end if;
    return new;
end;
$$;
drop trigger if exists protect_issued_project_version on public.project_versions;
create trigger protect_issued_project_version before update on public.project_versions
    for each row execute function public.protect_issued_project_version();
revoke all on public.project_versions from public, anon, authenticated;
grant select on public.project_versions to authenticated;
grant all on public.project_versions to service_role;

create or replace function public.protect_project_file_identity() returns trigger
language plpgsql set search_path=public as $$
begin
    if (new.file_id,new.company_id,new.project_id,new.content_sha256,new.source_file_path,
        new.mime_type,new.size_bytes,new.created_at) is distinct from
       (old.file_id,old.company_id,old.project_id,old.content_sha256,old.source_file_path,
        old.mime_type,old.size_bytes,old.created_at) then
        raise exception 'Project source file identity is immutable';
    end if;
    return new;
end;
$$;
drop trigger if exists protect_project_file_identity on public.project_files;
create trigger protect_project_file_identity before update on public.project_files
    for each row execute function public.protect_project_file_identity();

revoke all on function public.finalize_project_estimate(text, text, text, jsonb)
    from public, anon, authenticated;
grant execute on function public.finalize_project_estimate(text, text, text, jsonb)
    to service_role;

create or replace function public.rename_file_review_object(
    p_company_id text,p_run_id text,p_object_id text,p_expected_name text,p_object_name text
) returns boolean language plpgsql security definer set search_path=public as $$
declare v_changed text; v_current text;
begin
    if not exists(select 1 from public.rfq_runs where run_id=p_run_id and company_id=p_company_id) then
        raise exception 'RFQ is not available to this company';
    end if;
    if coalesce(trim(p_object_name),'')='' then raise exception 'Object name cannot be empty'; end if;
    update public.rfq_detected_objects set object_name=trim(p_object_name)
    where run_id=p_run_id and object_id=p_object_id and object_name=p_expected_name
    returning object_id into v_changed;
    select object_name into v_current from public.rfq_detected_objects where run_id=p_run_id and object_id=p_object_id;
    if v_current is not null then
        update public.rfq_object_estimates set object_name=v_current,updated_at=now()
        where run_id=p_run_id and object_id=p_object_id and company_id=p_company_id and object_name is distinct from v_current;
    end if;
    return v_changed is not null;
end;
$$;
revoke all on function public.rename_file_review_object(text,text,text,text,text) from public,anon,authenticated;
grant execute on function public.rename_file_review_object(text,text,text,text,text) to service_role;

-- Late workers must not overwrite an acknowledged manual File Review name.
create or replace function public.project_canonical_object_name() returns trigger
language plpgsql set search_path=public as $$
declare v_name text;
begin
    select object_name into v_name from public.rfq_detected_objects
    where run_id=new.run_id and object_id=new.object_id;
    if v_name is not null then new.object_name:=v_name; end if;
    return new;
end;
$$;
drop trigger if exists project_canonical_object_name on public.rfq_object_estimates;
create trigger project_canonical_object_name before insert or update of object_name on public.rfq_object_estimates
    for each row execute function public.project_canonical_object_name();

notify pgrst, 'reload schema';
commit;
