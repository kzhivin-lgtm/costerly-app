-- Labor V3, owner clarification27November2026: Project, Partner and Client
-- are optional. Preserve immutable versions, company ownership and approval gates.
-- No placeholders, organization rows or reserved groups for absent metadata.
-- This migration changes constraints/function only; it rewrites no existing data.

begin;
alter table public.projects
    alter column name drop not null,
    alter column normalized_name drop not null,
    alter column partner_organization_id drop not null;

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

    v_project_normalized := lower(regexp_replace(v_project_name, '\s+', ' ', 'g'));
    v_partner_normalized := lower(regexp_replace(v_partner_name, '\s+', ' ', 'g'));

    -- Serialize creation by logical project, or by RFQ for unnamed projects.
    -- NULL values cannot rely on the legacy named-project unique constraint.
    perform pg_advisory_xact_lock(hashtextextended(
        'proposal:' || p_company_id || ':' || coalesce(v_partner_normalized, '') || ':' ||
        case when v_project_normalized is null then 'rfq:' || p_run_id
             else 'name:' || v_project_normalized end, 0));

    -- Retry returns the original association before creating any new entities.
    select pv.project_id, pv.version_id, pv.version_number, p.partner_organization_id
    into v_project_id, v_version_id, v_version_number, v_partner_id
    from public.project_versions pv
    join public.projects p on p.project_id = pv.project_id and p.company_id = pv.company_id
    where pv.company_id = p_company_id and pv.estimate_id = p_estimate_id;
    if v_version_id is not null then
        return jsonb_build_object(
            'organization_id', v_partner_id, 'project_id', v_project_id,
            'version_id', v_version_id, 'version_number', v_version_number, 'created', false);
    end if;

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

    perform pg_advisory_xact_lock(hashtextextended(v_project_id::text, 0));
    select coalesce(max(pv.version_number), 0) + 1
    into v_version_number
    from public.project_versions pv where pv.project_id = v_project_id;

    insert into public.project_versions(
        company_id, project_id, version_number, run_id, estimate_id,
        summary, snapshot
    ) values (
        p_company_id, v_project_id, v_version_number, p_run_id, p_estimate_id,
        coalesce(p_snapshot->'summary', '{}'::jsonb), p_snapshot
    ) returning version_id into v_version_id;

    return jsonb_build_object(
        'organization_id', v_partner_id,
        'project_id', v_project_id,
        'version_id', v_version_id,
        'version_number', v_version_number,
        'created', true
    );
end;
$$;

revoke all on function public.finalize_project_estimate(text, text, text, jsonb)
    from public, anon, authenticated;
grant execute on function public.finalize_project_estimate(text, text, text, jsonb)
    to service_role;

commit;
