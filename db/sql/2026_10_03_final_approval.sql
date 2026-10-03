-- 3.16.2 Final Approval.
-- One idempotent transaction creates or links organizations and project,
-- then freezes the approved estimate as the next immutable project version.

alter table public.project_versions
    add column if not exists snapshot jsonb not null default '{}'::jsonb;

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

    if coalesce(lower(v_project_name), '') in ('', 'unknown') then
        raise exception 'Project name is required before Final Approval';
    end if;
    if coalesce(lower(v_partner_name), '') in ('', 'unknown') then
        raise exception 'Partner is required before Final Approval';
    end if;
    if p_snapshot is null or jsonb_typeof(p_snapshot) <> 'object' then
        raise exception 'Final Approval snapshot is required';
    end if;

    v_project_normalized := lower(regexp_replace(v_project_name, '\s+', ' ', 'g'));
    v_partner_normalized := lower(regexp_replace(v_partner_name, '\s+', ' ', 'g'));

    insert into public.organizations(company_id, name, normalized_name, is_partner, is_client)
    values (p_company_id, v_partner_name, v_partner_normalized, true, false)
    on conflict (company_id, normalized_name) do update
    set is_partner = true, name = excluded.name, updated_at = now()
    returning organization_id into v_partner_id;

    if coalesce(lower(v_client_name), '') not in ('', 'unknown') then
        v_client_normalized := lower(regexp_replace(v_client_name, '\s+', ' ', 'g'));
        insert into public.organizations(company_id, name, normalized_name, is_partner, is_client)
        values (p_company_id, v_client_name, v_client_normalized, false, true)
        on conflict (company_id, normalized_name) do update
        set is_client = true, name = excluded.name, updated_at = now()
        returning organization_id into v_client_id;
    end if;

    insert into public.projects(
        company_id, partner_organization_id, client_organization_id,
        name, normalized_name
    ) values (
        p_company_id, v_partner_id, v_client_id, v_project_name, v_project_normalized
    )
    on conflict (company_id, partner_organization_id, normalized_name) do update
    set client_organization_id = coalesce(excluded.client_organization_id, projects.client_organization_id),
        name = excluded.name,
        updated_at = now()
    returning project_id into v_project_id;

    select pv.version_id, pv.version_number
    into v_version_id, v_version_number
    from public.project_versions pv
    where pv.company_id = p_company_id and pv.estimate_id = p_estimate_id;
    if v_version_id is not null then
        return jsonb_build_object(
            'organization_id', v_partner_id,
            'project_id', v_project_id,
            'version_id', v_version_id,
            'version_number', v_version_number,
            'created', false
        );
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
