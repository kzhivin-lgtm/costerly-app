-- 3.9.1 Machinery and production routing foundation.
-- Additive and repeat-safe. The prototype company_machines table is left
-- untouched until a separately verified migration is approved.

create table if not exists public.machinery_catalog (
    machine_code text primary key,
    industry text not null check (industry in ('woodworking', 'metalworking', 'finishing')),
    category text not null,
    display_name text not null check (length(trim(display_name)) between 1 and 160),
    description text not null default '',
    sort_order integer not null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

insert into public.machinery_catalog
    (machine_code, industry, category, display_name, description, sort_order)
values
    ('wood_cnc_router', 'woodworking', 'cutting', 'CNC router', 'Routing, drilling and profiling sheet goods or solid wood', 10),
    ('wood_panel_saw', 'woodworking', 'cutting', 'Panel cutting saw', 'Straight panel sizing and cutting', 20),
    ('wood_edge_bander', 'woodworking', 'edging', 'Edge bander', 'Application and finishing of panel edge material', 30),
    ('wood_boring_machine', 'woodworking', 'machining', 'Boring machine', 'Repeatable construction and hardware drilling', 40),
    ('wood_veneer_press', 'woodworking', 'pressing', 'Veneer or laminating press', 'Flat pressing of veneer or laminate', 50),
    ('wood_solid_preparation', 'woodworking', 'preparation', 'Solid wood preparation line', 'Planing, thicknessing and dimensioning solid wood', 60),
    ('wood_wide_belt_sander', 'woodworking', 'finishing', 'Wide-belt sander or calibrator', 'Calibrating and sanding panels or solid wood', 70),
    ('wood_case_clamp', 'woodworking', 'assembly', 'Case clamp or assembly press', 'Squaring and pressing assembled cases', 80),
    ('metal_sheet_laser', 'metalworking', 'cutting', 'Sheet laser cutter', 'Profile cutting of sheet metal', 110),
    ('metal_tube_laser', 'metalworking', 'cutting', 'Tube laser cutter', 'Profile cutting of tube and section', 120),
    ('metal_press_brake', 'metalworking', 'forming', 'Press brake', 'Controlled bending of sheet metal', 130),
    ('metal_sheet_shear', 'metalworking', 'cutting', 'Sheet shear or guillotine', 'Straight cutting of sheet metal', 140),
    ('metal_punch_press', 'metalworking', 'forming', 'Punching or hydraulic press', 'Punching, stamping and press operations', 150),
    ('metal_profile_saw', 'metalworking', 'cutting', 'Tube or profile saw', 'Length and mitre cutting of profiles', 160),
    ('metal_profile_bender', 'metalworking', 'forming', 'Tube or profile bender', 'Controlled bending of tube and profiles', 170),
    ('metal_rolling_machine', 'metalworking', 'forming', 'Plate or section rolling machine', 'Rolling plate and sections to a radius', 180),
    ('metal_welding', 'metalworking', 'joining', 'Welding capability', 'MIG, MAG, TIG or other welding processes', 190),
    ('metal_deburring', 'metalworking', 'finishing', 'Deburring or grinding machine', 'Edge cleanup, deburring and grinding', 200),
    ('metal_drill_tap', 'metalworking', 'machining', 'Drill or tapping station', 'Hole drilling, countersinking and tapping', 210),
    ('finish_wet_spray_booth', 'finishing', 'wet_paint', 'Wet-paint spray booth', 'Controlled wet coating application', 310),
    ('finish_drying_chamber', 'finishing', 'wet_paint', 'Drying or curing chamber', 'Controlled drying or curing of wet finishes', 320),
    ('finish_powder_booth', 'finishing', 'powder_coating', 'Powder-coating booth', 'Controlled powder application and recovery', 330),
    ('finish_powder_oven', 'finishing', 'powder_coating', 'Powder-curing oven', 'Thermal curing of powder coating', 340),
    ('finish_sandblast_booth', 'finishing', 'preparation', 'Sandblasting booth', 'Abrasive surface preparation', 350),
    ('finish_wash_line', 'finishing', 'preparation', 'Washing or degreasing line', 'Cleaning and pretreatment before coating', 360),
    ('finish_polishing', 'finishing', 'finishing', 'Polishing or buffing station', 'Mechanical polishing and buffing', 370)
on conflict (machine_code) do update set
    industry = excluded.industry,
    category = excluded.category,
    display_name = excluded.display_name,
    description = excluded.description,
    sort_order = excluded.sort_order,
    active = true,
    updated_at = now();

create table if not exists public.company_machinery (
    company_machine_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    machine_code text not null references public.machinery_catalog(machine_code),
    availability_status text not null check (availability_status in ('in_house', 'not_in_house')),
    display_name text,
    capabilities jsonb not null default '{}'::jsonb,
    pricing_method text not null default 'unknown'
        check (pricing_method in ('unknown', 'hourly', 'per_sheet', 'per_part', 'per_job', 'quote_only')),
    pricing jsonb not null default '{}'::jsonb,
    accepts_external_work boolean,
    source text not null default 'owner_confirmed'
        check (source in ('owner_confirmed', 'imported', 'inferred')),
    verified_at timestamptz,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (company_id, machine_code)
);

create index if not exists company_machinery_company_active_idx
    on public.company_machinery(company_id, active, machine_code);

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'company_suppliers_company_supplier_unique'
          and conrelid = 'public.company_suppliers'::regclass
    ) then
        alter table public.company_suppliers
            add constraint company_suppliers_company_supplier_unique
            unique (company_id, supplier_id);
    end if;
end $$;

create table if not exists public.company_supplier_services (
    supplier_service_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    supplier_id uuid not null,
    machine_code text not null references public.machinery_catalog(machine_code),
    capabilities jsonb not null default '{}'::jsonb,
    pricing_method text not null default 'quote_only'
        check (pricing_method in ('unknown', 'hourly', 'per_sheet', 'per_part', 'per_job', 'quote_only')),
    pricing jsonb not null default '{}'::jsonb,
    typical_lead_time_days numeric(8, 2) check (typical_lead_time_days is null or typical_lead_time_days >= 0),
    preferred boolean not null default false,
    verified_at timestamptz,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (company_id, supplier_id, machine_code),
    unique (company_id, supplier_service_id),
    constraint company_supplier_services_supplier_company_fk
        foreign key (company_id, supplier_id)
        references public.company_suppliers(company_id, supplier_id)
);

create index if not exists company_supplier_services_lookup_idx
    on public.company_supplier_services(company_id, machine_code, active, preferred desc);

create table if not exists public.company_service_offers (
    service_offer_id uuid primary key default gen_random_uuid(),
    company_id text not null references public.companies(company_id),
    supplier_service_id uuid not null,
    source_id uuid references public.company_price_sources(source_id),
    source_price numeric(16, 4) not null check (source_price >= 0),
    source_unit text not null,
    currency text not null,
    vat_included boolean,
    setup_fee numeric(16, 4) check (setup_fee is null or setup_fee >= 0),
    minimum_charge numeric(16, 4) check (minimum_charge is null or minimum_charge >= 0),
    material_included boolean,
    delivery_included boolean,
    valid_from date,
    evidence jsonb not null default '{}'::jsonb,
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    status text not null default 'active'
        check (status in ('active', 'superseded', 'unresolved', 'archived')),
    created_at timestamptz not null default now(),
    constraint company_service_offers_service_company_fk
        foreign key (company_id, supplier_service_id)
        references public.company_supplier_services(company_id, supplier_service_id)
);

create index if not exists company_service_offers_active_idx
    on public.company_service_offers(company_id, supplier_service_id, status, created_at desc);

create table if not exists public.market_service_benchmarks (
    market_benchmark_id uuid primary key default gen_random_uuid(),
    machine_code text not null references public.machinery_catalog(machine_code),
    country_code text not null,
    region text,
    material_family text,
    thickness_min_mm numeric(10, 3),
    thickness_max_mm numeric(10, 3),
    price_basis text not null,
    price numeric(16, 4) not null check (price >= 0),
    unit text not null,
    currency text not null,
    setup_fee numeric(16, 4) check (setup_fee is null or setup_fee >= 0),
    minimum_charge numeric(16, 4) check (minimum_charge is null or minimum_charge >= 0),
    source_url text,
    source_date date not null,
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create index if not exists market_service_benchmarks_lookup_idx
    on public.market_service_benchmarks(machine_code, country_code, active, source_date desc);

alter table public.machinery_catalog enable row level security;
alter table public.company_machinery enable row level security;
alter table public.company_supplier_services enable row level security;
alter table public.company_service_offers enable row level security;
alter table public.market_service_benchmarks enable row level security;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'company_machinery',
        'company_supplier_services',
        'company_service_offers'
    ]
    loop
        if not exists (
            select 1 from pg_policies
            where schemaname = 'public'
              and tablename = table_name
              and policyname = table_name || '_member_select'
        ) then
            execute format(
                'create policy %I on public.%I for select to authenticated using '
                || '(exists (select 1 from public.company_members m where m.company_id = %I.company_id '
                || 'and m.user_id = (select auth.uid())))',
                table_name || '_member_select', table_name, table_name
            );
        end if;
        if not exists (
            select 1 from pg_policies
            where schemaname = 'public'
              and tablename = table_name
              and policyname = table_name || '_owner_write'
        ) then
            execute format(
                'create policy %I on public.%I for all to authenticated using '
                || '(exists (select 1 from public.company_members m where m.company_id = %I.company_id '
                || 'and m.user_id = (select auth.uid()) and m.role = ''owner'')) with check '
                || '(exists (select 1 from public.company_members m where m.company_id = %I.company_id '
                || 'and m.user_id = (select auth.uid()) and m.role = ''owner''))',
                table_name || '_owner_write', table_name, table_name, table_name
            );
        end if;
        execute format('revoke all on public.%I from anon', table_name);
        execute format('grant select, insert, update, delete on public.%I to authenticated', table_name);
    end loop;
end $$;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'machinery_catalog'
          and policyname = 'machinery_catalog_authenticated_select'
    ) then
        create policy machinery_catalog_authenticated_select
            on public.machinery_catalog for select to authenticated using (active);
    end if;
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'market_service_benchmarks'
          and policyname = 'market_service_benchmarks_authenticated_select'
    ) then
        create policy market_service_benchmarks_authenticated_select
            on public.market_service_benchmarks for select to authenticated using (active);
    end if;
end $$;

revoke all on public.machinery_catalog from anon;
revoke all on public.market_service_benchmarks from anon;
grant select on public.machinery_catalog to authenticated;
grant select on public.market_service_benchmarks to authenticated;
