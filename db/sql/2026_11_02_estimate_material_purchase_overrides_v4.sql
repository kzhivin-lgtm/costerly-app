-- 3.17.4.3 / Estimation V4.25
begin;
create table if not exists public.rfq_estimate_material_purchase_overrides (
    estimate_id text not null references public.rfq_estimates(estimate_id) on delete cascade,
    selection_key text not null,
    company_id text not null references public.companies(company_id),
    purchase_quantity numeric(14, 4) not null check (purchase_quantity > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (estimate_id, selection_key)
);
create index if not exists rfq_estimate_material_purchase_overrides_company_idx on public.rfq_estimate_material_purchase_overrides (company_id, estimate_id);
alter table public.rfq_estimate_material_purchase_overrides enable row level security;
drop policy if exists rfq_estimate_material_purchase_overrides_company_member_read on public.rfq_estimate_material_purchase_overrides;
create policy rfq_estimate_material_purchase_overrides_company_member_read on public.rfq_estimate_material_purchase_overrides for select to authenticated using (exists (
    select 1 from public.company_members member where member.company_id = rfq_estimate_material_purchase_overrides.company_id and member.user_id = (select auth.uid())
));
revoke all on public.rfq_estimate_material_purchase_overrides from public, anon, authenticated;
grant select on public.rfq_estimate_material_purchase_overrides to authenticated;
grant all on public.rfq_estimate_material_purchase_overrides to service_role;
commit;
