-- 3.16.1 Projects foundation.
-- Organizations are company-scoped counterparties. Partner is the mandatory
-- top-level project owner; Client is an optional role and project relation.

create table if not exists public.organizations (
    organization_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id) on delete cascade,
    name text not null,
    normalized_name text not null,
    is_partner boolean not null default false,
    is_client boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint organizations_name_not_blank check (length(trim(name)) > 0),
    constraint organizations_role_required check (is_partner or is_client),
    unique (company_id, normalized_name),
    unique (organization_id, company_id)
);

create table if not exists public.projects (
    project_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id) on delete cascade,
    partner_organization_id uuid not null,
    client_organization_id uuid,
    name text not null,
    normalized_name text not null,
    status text not null default 'active',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint projects_name_not_blank check (length(trim(name)) > 0),
    constraint projects_status_check check (status in ('active', 'archived')),
    constraint projects_partner_company_fk
        foreign key (partner_organization_id, company_id)
        references public.organizations(organization_id, company_id),
    constraint projects_client_company_fk
        foreign key (client_organization_id, company_id)
        references public.organizations(organization_id, company_id),
    unique (project_id, company_id),
    unique (company_id, partner_organization_id, normalized_name)
);

create table if not exists public.project_versions (
    version_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id) on delete cascade,
    project_id uuid not null,
    version_number integer not null check (version_number > 0),
    run_id text not null references public.rfq_runs(run_id),
    estimate_id text not null references public.rfq_estimates(estimate_id),
    status text not null default 'final',
    approved_at timestamptz not null default now(),
    source_file_path text,
    proposal_pdf_path text,
    summary jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    constraint project_versions_status_check check (status in ('final', 'superseded')),
    constraint project_versions_project_company_fk
        foreign key (project_id, company_id)
        references public.projects(project_id, company_id) on delete cascade,
    unique (project_id, version_number),
    unique (company_id, estimate_id)
);

create index if not exists organizations_company_partner_idx
    on public.organizations(company_id, is_partner, name);
create index if not exists projects_partner_idx
    on public.projects(company_id, partner_organization_id, updated_at desc);
create index if not exists project_versions_project_idx
    on public.project_versions(company_id, project_id, version_number desc);

alter table public.organizations enable row level security;
alter table public.projects enable row level security;
alter table public.project_versions enable row level security;

do $$
declare
    v_table_name text;
begin
    foreach v_table_name in array array['organizations', 'projects', 'project_versions'] loop
        execute format('drop policy if exists company_member_access on public.%I', v_table_name);
        execute format($policy$
            create policy company_member_access on public.%I
            for all to authenticated
            using (exists (
                select 1 from public.company_members m
                where m.company_id = %I.company_id
                  and m.user_id = (select auth.uid())
            ))
            with check (exists (
                select 1 from public.company_members m
                where m.company_id = %I.company_id
                  and m.user_id = (select auth.uid())
            ))
        $policy$, v_table_name, v_table_name, v_table_name);
    end loop;
end $$;

grant select, insert, update on public.organizations, public.projects,
    public.project_versions to authenticated;
revoke all on public.organizations, public.projects, public.project_versions from anon;
