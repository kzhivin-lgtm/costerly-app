-- 3.16.7 Price Lists rebuild, stage 1.
--
-- Additive foundation only. A supplier service is not a material and must not
-- enter company_material_items or company_material_offers. It is an
-- evidence-backed, company-private offer for one shared reference operation.
-- Existing source rows, material offers, and Price Lists behaviour remain
-- untouched until the later application and UI stages are accepted.

begin;

alter table public.company_price_sources
    add column if not exists source_supplier_name text;

alter table public.company_price_sources
    add constraint company_price_sources_source_supplier_name_check
    check (
        source_supplier_name is null
        or length(trim(source_supplier_name)) between 1 and 240
    ) not valid;

alter table public.company_price_source_rows
    add column if not exists row_kind text not null default 'material',
    add column if not exists reference_operation_id uuid
        references public.reference_operations(operation_id);

alter table public.company_price_source_rows
    add constraint company_price_source_rows_row_kind_check
    check (row_kind in ('material', 'operation_service', 'non_catalog')) not valid;

create index if not exists company_price_source_rows_operation_idx
    on public.company_price_source_rows(company_id, reference_operation_id)
    where reference_operation_id is not null;

-- Observed and manually confirmed spellings stay private to a company. The
-- future merge layer may use them, but never changes historical source text.
create table if not exists public.company_supplier_aliases (
    supplier_alias_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    supplier_id uuid not null references public.company_suppliers(supplier_id)
        on delete cascade,
    alias_name text not null check (length(trim(alias_name)) between 1 and 240),
    normalized_name text not null check (length(trim(normalized_name)) between 1 and 240),
    alias_kind text not null check (alias_kind in ('source_observed', 'manual')),
    source_id uuid references public.company_price_sources(source_id),
    created_at timestamptz not null default now(),
    unique (company_id, normalized_name),
    constraint company_supplier_aliases_source_check check (
        alias_kind = 'manual' or source_id is not null
    )
);

create index if not exists company_supplier_aliases_supplier_idx
    on public.company_supplier_aliases(company_id, supplier_id);

-- One supplier may quote the same reference operation in several documents.
-- This table preserves every observed price version. Its pricing basis is
-- deliberately explicit: supplier_defined never pretends to be a piece,
-- metre, square metre, or labor-hour rate.
create table if not exists public.company_supplier_operation_offers (
    operation_offer_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    operation_id uuid not null references public.reference_operations(operation_id),
    supplier_id uuid references public.company_suppliers(supplier_id),
    source_id uuid not null references public.company_price_sources(source_id),
    source_row_id uuid not null references public.company_price_source_rows(row_id),
    raw_service_name text not null check (length(trim(raw_service_name)) between 1 and 500),
    supplier_sku text,
    source_price numeric(16, 4) not null check (source_price > 0),
    pricing_basis text not null check (pricing_basis in (
        'supplier_defined', 'piece', 'linear_meter', 'square_meter', 'sheet', 'job', 'hour'
    )),
    source_unit_label text,
    currency text not null check (length(trim(currency)) = 3),
    vat_included boolean,
    valid_from date,
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    status text not null default 'active' check (
        status in ('active', 'superseded', 'review', 'archived')
    ),
    evidence jsonb not null default '{}'::jsonb check (jsonb_typeof(evidence) = 'object'),
    created_at timestamptz not null default now(),
    unique (source_row_id)
);

create index if not exists company_supplier_operation_offers_active_idx
    on public.company_supplier_operation_offers(
        company_id, operation_id, supplier_id, status, valid_from desc, created_at desc
    );

alter table public.company_supplier_aliases enable row level security;
alter table public.company_supplier_operation_offers enable row level security;

do $policy$
declare
    table_name text;
begin
    foreach table_name in array array[
        'company_supplier_aliases',
        'company_supplier_operation_offers'
    ]
    loop
        if not exists (
            select 1
            from pg_policies
            where schemaname = 'public'
              and tablename = table_name
              and policyname = table_name || '_owner_all'
        ) then
            execute format(
                'create policy %I on public.%I for all to authenticated using '
                || '(exists (select 1 from public.company_members m where m.company_id = %I.company_id '
                || 'and m.user_id = (select auth.uid()) and m.role = ''owner'')) with check '
                || '(exists (select 1 from public.company_members m where m.company_id = %I.company_id '
                || 'and m.user_id = (select auth.uid()) and m.role = ''owner''))',
                table_name || '_owner_all', table_name, table_name, table_name
            );
        end if;
        execute format('revoke all on public.%I from anon', table_name);
        execute format('grant select, insert, update, delete on public.%I to authenticated', table_name);
    end loop;
end
$policy$;

-- The invoice evidence is a supplier bundle, not a material price and not an
-- assertion that its quantity is a part, metre, or edge-length measurement.
insert into public.reference_operation_drivers (
    driver_code, driver_name, unit, quantity_type, description, active, sort_order
) values (
    'supplier_service_unit_count',
    'Supplier-defined service unit count',
    'supplier service unit',
    'count',
    'Count printed by a supplier when the invoice does not prove a physical calculation unit.',
    true,
    900
)
on conflict (driver_code) do update set
    driver_name = excluded.driver_name,
    unit = excluded.unit,
    quantity_type = excluded.quantity_type,
    description = excluded.description,
    active = excluded.active,
    sort_order = excluded.sort_order;

insert into public.reference_operations (
    operation_code, department, operation_name, description
) values (
    'supplier_cut_and_edge_banding',
    'wood',
    'Supplier cut and edge banding',
    'Supplier-priced bundle for cutting panel parts and applying edge banding. It remains a bundle unless a source proves separable prices.'
)
on conflict (operation_code) do update set
    department = excluded.department,
    operation_name = excluded.operation_name,
    description = excluded.description;

insert into public.reference_operation_driver_options (
    operation_id, driver_code, driver_purpose
)
select operation_id, 'supplier_service_unit_count', 'evidence'
from public.reference_operations
where operation_code = 'supplier_cut_and_edge_banding'
on conflict (operation_id, driver_code) do update set
    driver_purpose = excluded.driver_purpose;

commit;
