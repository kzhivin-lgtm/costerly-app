-- 3.17.3.5: one current, estimate-wide Material Engine purchase plan and
-- explicit user overrides of the net material norm for one finished item.
--
-- A user never edits purchasable sheets, stock bars, packs, scraps or the
-- project-wide rounded quantity. They edit the net requirement for one item.
-- That edit makes the current plan stale; the Engine later recomputes the
-- whole estimate and replaces this derived snapshot.

begin;

create table if not exists public.rfq_estimate_material_plans (
    estimate_id text primary key references public.rfq_estimates(estimate_id) on delete cascade,
    company_id text not null references public.companies(company_id),
    plan_status text not null default 'pending' check (
        plan_status in ('pending', 'running', 'planned', 'needs_review', 'stale', 'failed')
    ),
    input_fingerprint text,
    plan_payload jsonb not null check (jsonb_typeof(plan_payload) = 'object'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists rfq_estimate_material_plans_company_idx
    on public.rfq_estimate_material_plans (company_id, updated_at desc);

create table if not exists public.rfq_estimate_material_norm_overrides (
    estimate_id text not null references public.rfq_estimates(estimate_id) on delete cascade,
    object_id text not null,
    material_requirement_id text not null,
    company_id text not null references public.companies(company_id),
    quantity_per_item numeric(14, 4) not null check (quantity_per_item > 0),
    unit text not null check (length(trim(unit)) > 0),
    source_line_id text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (estimate_id, object_id, material_requirement_id)
);

create index if not exists rfq_estimate_material_norm_overrides_company_idx
    on public.rfq_estimate_material_norm_overrides (company_id, estimate_id, object_id);

alter table public.rfq_estimate_material_plans enable row level security;

drop policy if exists rfq_estimate_material_plans_company_member_read
    on public.rfq_estimate_material_plans;
create policy rfq_estimate_material_plans_company_member_read
    on public.rfq_estimate_material_plans for select to authenticated
    using (exists (
        select 1 from public.company_members member
        where member.company_id = rfq_estimate_material_plans.company_id
          and member.user_id = (select auth.uid())
    ));

alter table public.rfq_estimate_material_norm_overrides enable row level security;

drop policy if exists rfq_estimate_material_norm_overrides_company_member_read
    on public.rfq_estimate_material_norm_overrides;
create policy rfq_estimate_material_norm_overrides_company_member_read
    on public.rfq_estimate_material_norm_overrides for select to authenticated
    using (exists (
        select 1 from public.company_members member
        where member.company_id = rfq_estimate_material_norm_overrides.company_id
          and member.user_id = (select auth.uid())
    ));

revoke all on public.rfq_estimate_material_plans from public, anon, authenticated;
grant select on public.rfq_estimate_material_plans to authenticated;
grant all on public.rfq_estimate_material_plans to service_role;

revoke all on public.rfq_estimate_material_norm_overrides from public, anon, authenticated;
grant select on public.rfq_estimate_material_norm_overrides to authenticated;
grant all on public.rfq_estimate_material_norm_overrides to service_role;

commit;
