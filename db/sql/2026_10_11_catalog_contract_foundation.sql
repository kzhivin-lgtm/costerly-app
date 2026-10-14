-- 3.17.1 catalog rebuild, increment 1.
-- Canonical catalog plus case-local provisional assumptions and the
-- Staff-only Catalog Gap queue. This migration deliberately does not change
-- legacy reader paths or write provisional research into the catalog.

begin;

create table if not exists public.reference_production_departments (
    department_code text primary key check (
        department_code in ('wood', 'metal', 'glass_plastics', 'stone', 'coating')
    ),
    department_name text not null check (length(trim(department_name)) between 1 and 120),
    sort_order integer not null default 0,
    active boolean not null default true
);

create table if not exists public.reference_entity_roles (
    entity_role_code text primary key check (
        entity_role_code in (
            'material', 'hardware', 'consumable', 'packaging',
            'purchased_fabricated_component', 'supplier_service'
        )
    ),
    entity_role_name text not null check (length(trim(entity_role_name)) between 1 and 160),
    active boolean not null default true
);

create table if not exists public.reference_material_family_categories (
    category_id uuid primary key default gen_random_uuid(),
    category_code text not null unique check (
        category_code = lower(category_code) and category_code !~ '[^a-z0-9_]'
    ),
    category_name text not null check (length(trim(category_name)) between 1 and 160),
    production_department_code text references public.reference_production_departments(department_code),
    entity_role_code text not null references public.reference_entity_roles(entity_role_code),
    parent_category_id uuid references public.reference_material_family_categories(category_id),
    sort_order integer not null default 0,
    active boolean not null default true,
    unique (parent_category_id, category_code)
);

create table if not exists public.reference_material_families (
    family_id uuid primary key default gen_random_uuid(),
    family_code text not null unique check (
        family_code = lower(family_code) and family_code !~ '[^a-z0-9_]'
    ),
    family_name text not null check (length(trim(family_name)) between 1 and 200),
    category_id uuid references public.reference_material_family_categories(category_id),
    production_department_code text references public.reference_production_departments(department_code),
    entity_role_code text not null references public.reference_entity_roles(entity_role_code),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.reference_material_family_attributes (
    family_id uuid not null references public.reference_material_families(family_id) on delete cascade,
    attribute_code text not null check (
        attribute_code = lower(attribute_code) and attribute_code !~ '[^a-z0-9_]'
    ),
    attribute_name text not null check (length(trim(attribute_name)) between 1 and 160),
    attribute_role text not null check (attribute_role in ('primary', 'secondary')),
    value_type text not null check (value_type in ('text', 'number', 'boolean', 'dimension', 'enum', 'json')),
    required boolean not null default false,
    sort_order integer not null default 0,
    primary key (family_id, attribute_code)
);

create unique index if not exists reference_material_family_one_primary_attribute_idx
    on public.reference_material_family_attributes (family_id)
    where attribute_role = 'primary';

create table if not exists public.reference_material_family_department_affinities (
    family_id uuid not null references public.reference_material_families(family_id) on delete cascade,
    department_code text not null references public.reference_production_departments(department_code),
    primary key (family_id, department_code)
);

create table if not exists public.reference_material_family_operation_eligibilities (
    family_id uuid not null references public.reference_material_families(family_id) on delete cascade,
    operation_id uuid not null references public.reference_operations(operation_id),
    active boolean not null default true,
    primary key (family_id, operation_id)
);

create table if not exists public.reference_material_family_memberships (
    membership_id uuid primary key default gen_random_uuid(),
    material_id uuid not null references public.reference_materials(material_id) on delete cascade,
    family_id uuid not null references public.reference_material_families(family_id),
    classification_basis text not null check (
        classification_basis in ('catalog_seed', 'deterministic_rule', 'staff_review')
    ),
    classification_evidence jsonb not null default '{}'::jsonb check (
        jsonb_typeof(classification_evidence) = 'object'
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    unique (material_id, family_id)
);

create unique index if not exists reference_material_one_active_family_idx
    on public.reference_material_family_memberships (material_id)
    where active;

-- Global family, Global material model, market listing and company offer are
-- intentionally separate. A model such as a specific Blum system is global;
-- its Israel listing, supply format and price are not.
-- The existing reference_materials table remains a legacy evidence source until
-- the migration map and every reader have passed cutover checks.
create table if not exists public.reference_brands (
    brand_id uuid primary key default gen_random_uuid(),
    brand_code text not null unique check (
        brand_code = lower(brand_code) and brand_code !~ '[^a-z0-9_]'
    ),
    canonical_name text not null check (length(trim(canonical_name)) between 1 and 240),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.reference_material_family_brand_scopes (
    family_id uuid not null references public.reference_material_families(family_id)
        on delete cascade,
    brand_id uuid not null references public.reference_brands(brand_id),
    active boolean not null default true,
    primary key (family_id, brand_id)
);

create table if not exists public.reference_brand_aliases (
    brand_alias_id uuid primary key default gen_random_uuid(),
    brand_id uuid not null references public.reference_brands(brand_id) on delete cascade,
    market_code text references public.reference_markets(market_code),
    language_code text,
    alias_text text not null check (length(trim(alias_text)) between 1 and 240),
    alias_key text not null check (length(trim(alias_key)) between 1 and 240),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    unique (brand_id, market_code, alias_key)
);

create index if not exists reference_brand_aliases_lookup_idx
    on public.reference_brand_aliases (market_code, alias_key)
    where active;

create table if not exists public.reference_material_models (
    material_model_id uuid primary key default gen_random_uuid(),
    family_id uuid not null references public.reference_material_families(family_id),
    brand_id uuid references public.reference_brands(brand_id),
    material_model_code text not null unique check (
        material_model_code = lower(material_model_code)
        and material_model_code !~ '[^a-z0-9_]'
    ),
    canonical_name text not null check (length(trim(canonical_name)) between 1 and 500),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (material_model_id, family_id),
    foreign key (family_id, brand_id)
        references public.reference_material_family_brand_scopes(family_id, brand_id)
);

create table if not exists public.reference_material_model_attribute_values (
    material_model_id uuid not null,
    family_id uuid not null,
    attribute_code text not null,
    attribute_value jsonb not null check (jsonb_typeof(attribute_value) in ('string', 'number', 'boolean', 'object', 'array')),
    primary key (material_model_id, attribute_code),
    foreign key (material_model_id, family_id)
        references public.reference_material_models(material_model_id, family_id)
        on delete cascade,
    foreign key (family_id, attribute_code)
        references public.reference_material_family_attributes(family_id, attribute_code)
);

create table if not exists public.reference_market_material_listings (
    market_material_listing_id uuid primary key default gen_random_uuid(),
    market_code text not null references public.reference_markets(market_code),
    material_model_id uuid not null references public.reference_material_models(material_model_id),
    listing_code text not null check (
        listing_code = lower(listing_code) and listing_code !~ '[^a-z0-9_]'
    ),
    canonical_market_name text not null check (length(trim(canonical_market_name)) between 1 and 500),
    availability_status text not null default 'unknown' check (
        availability_status in ('unknown', 'common', 'limited', 'special_order', 'unavailable')
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (market_code, listing_code),
    unique (market_code, material_model_id),
    unique (market_material_listing_id, material_model_id)
);

create index if not exists reference_market_material_listings_lookup_idx
    on public.reference_market_material_listings (market_code, material_model_id, active);

create table if not exists public.reference_market_material_supply_formats (
    supply_format_id uuid primary key default gen_random_uuid(),
    market_material_listing_id uuid not null references public.reference_market_material_listings(market_material_listing_id)
        on delete cascade,
    supply_format_code text not null check (
        supply_format_code = lower(supply_format_code) and supply_format_code !~ '[^a-z0-9_]'
    ),
    purchase_unit text not null check (length(trim(purchase_unit)) between 1 and 80),
    purchasable_dimensions jsonb not null default '{}'::jsonb check (
        jsonb_typeof(purchasable_dimensions) = 'object'
    ),
    minimum_purchase_quantity numeric(18, 6) not null default 1 check (
        minimum_purchase_quantity > 0
    ),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (market_material_listing_id, supply_format_code)
);

create table if not exists public.reference_market_material_legacy_mappings (
    legacy_mapping_id uuid primary key default gen_random_uuid(),
    legacy_material_id uuid not null unique references public.reference_materials(material_id),
    market_code text not null references public.reference_markets(market_code),
    family_id uuid references public.reference_material_families(family_id),
    material_model_id uuid,
    market_material_listing_id uuid,
    classification_status text not null check (
        classification_status in ('mapped', 'excluded_by_policy', 'review_required')
    ),
    classification_basis text check (
        classification_basis in ('catalog_seed', 'deterministic_rule', 'staff_review')
    ),
    classification_evidence jsonb not null default '{}'::jsonb check (
        jsonb_typeof(classification_evidence) = 'object'
    ),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (
        (classification_status = 'mapped'
            and family_id is not null
            and material_model_id is not null
            and market_material_listing_id is not null
            and classification_basis is not null)
        or (classification_status <> 'mapped'
            and material_model_id is null
            and market_material_listing_id is null)
    ),
    foreign key (material_model_id, family_id)
        references public.reference_material_models(material_model_id, family_id),
    foreign key (market_material_listing_id, material_model_id)
        references public.reference_market_material_listings(market_material_listing_id, material_model_id)
);

create index if not exists reference_market_material_legacy_mappings_review_idx
    on public.reference_market_material_legacy_mappings (market_code, classification_status)
    where classification_status = 'review_required';

create table if not exists public.company_material_item_market_listing_mappings (
    company_material_id uuid primary key
        references public.company_material_items(company_material_id) on delete cascade,
    market_material_listing_id uuid references public.reference_market_material_listings(market_material_listing_id),
    mapping_status text not null check (
        mapping_status in ('matched', 'no_market_match', 'review_required')
    ),
    mapping_basis text check (
        mapping_basis in ('deterministic_rule', 'staff_review')
    ),
    mapping_evidence jsonb not null default '{}'::jsonb check (
        jsonb_typeof(mapping_evidence) = 'object'
    ),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (
        (mapping_status = 'matched'
            and market_material_listing_id is not null
            and mapping_basis is not null)
        or (mapping_status <> 'matched'
            and market_material_listing_id is null)
    )
);

create table if not exists public.catalog_gap_jobs (
    gap_job_id uuid primary key default gen_random_uuid(),
    gap_fingerprint text not null unique check (gap_fingerprint ~ '^[0-9a-f]{64}$'),
    gap_type text not null check (gap_type in (
        'material_identity', 'material_supply', 'price_source', 'operation',
        'labor_route', 'labor_recipe'
    )),
    market_code text not null references public.reference_markets(market_code),
    normalized_statement text not null check (length(trim(normalized_statement)) between 1 and 2000),
    route_critical_attributes jsonb not null default '{}'::jsonb check (
        jsonb_typeof(route_critical_attributes) = 'object'
    ),
    status text not null default 'open' check (
        status in ('open', 'research_pending', 'staff_review', 'resolved', 'rejected')
    ),
    occurrence_count integer not null default 0 check (occurrence_count >= 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    resolved_by uuid references auth.users(id),
    resolved_at timestamptz
);

create table if not exists public.estimate_case_assumptions (
    assumption_id uuid primary key default gen_random_uuid(),
    estimate_id text not null,
    object_id text not null,
    company_id text not null references public.companies(company_id),
    fact_result_id uuid references public.rfq_estimation_object_fact_results(fact_result_id),
    gap_job_id uuid references public.catalog_gap_jobs(gap_job_id),
    assumption_kind text not null check (assumption_kind in (
        'material_identity', 'material_supply', 'price_source', 'operation',
        'labor_route', 'labor_recipe'
    )),
    status text not null default 'active' check (status in ('active', 'superseded')),
    chosen_assumption jsonb not null check (jsonb_typeof(chosen_assumption) = 'object'),
    research_sources jsonb not null default '[]'::jsonb check (jsonb_typeof(research_sources) = 'array'),
    calculation_impact jsonb not null default '{}'::jsonb check (jsonb_typeof(calculation_impact) = 'object'),
    confidence numeric(5,2) not null check (confidence >= 0 and confidence <= 100),
    created_at timestamptz not null default now(),
    superseded_at timestamptz,
    foreign key (estimate_id, object_id)
        references public.rfq_object_estimates(estimate_id, object_id) on delete cascade
);

create table if not exists public.catalog_gap_job_occurrences (
    occurrence_id uuid primary key default gen_random_uuid(),
    gap_job_id uuid not null references public.catalog_gap_jobs(gap_job_id) on delete cascade,
    assumption_id uuid not null unique references public.estimate_case_assumptions(assumption_id) on delete cascade,
    company_id text not null references public.companies(company_id),
    created_at timestamptz not null default now()
);

create index if not exists estimate_case_assumptions_lookup_idx
    on public.estimate_case_assumptions (company_id, estimate_id, object_id, created_at desc);
create index if not exists catalog_gap_jobs_status_idx
    on public.catalog_gap_jobs (status, created_at);
create index if not exists catalog_gap_job_occurrences_job_idx
    on public.catalog_gap_job_occurrences (gap_job_id, created_at desc);

insert into public.reference_production_departments (
    department_code, department_name, sort_order
) values
    ('wood', 'Wood', 10),
    ('metal', 'Metal', 20),
    ('glass_plastics', 'Glass & Plastics', 30),
    ('stone', 'Stone', 40),
    ('coating', 'Coating', 50)
on conflict (department_code) do update set
    department_name = excluded.department_name,
    sort_order = excluded.sort_order,
    active = true;

insert into public.reference_entity_roles (entity_role_code, entity_role_name) values
    ('material', 'Material'),
    ('hardware', 'Hardware'),
    ('consumable', 'Consumable'),
    ('packaging', 'Packaging'),
    ('purchased_fabricated_component', 'Purchased fabricated component'),
    ('supplier_service', 'Supplier service')
on conflict (entity_role_code) do update set
    entity_role_name = excluded.entity_role_name,
    active = true;

alter table public.reference_production_departments enable row level security;
alter table public.reference_entity_roles enable row level security;
alter table public.reference_material_family_categories enable row level security;
alter table public.reference_material_families enable row level security;
alter table public.reference_material_family_attributes enable row level security;
alter table public.reference_material_family_department_affinities enable row level security;
alter table public.reference_material_family_operation_eligibilities enable row level security;
alter table public.reference_material_family_memberships enable row level security;
alter table public.reference_brands enable row level security;
alter table public.reference_material_family_brand_scopes enable row level security;
alter table public.reference_brand_aliases enable row level security;
alter table public.reference_material_models enable row level security;
alter table public.reference_material_model_attribute_values enable row level security;
alter table public.reference_market_material_listings enable row level security;
alter table public.reference_market_material_supply_formats enable row level security;
alter table public.reference_market_material_legacy_mappings enable row level security;
alter table public.company_material_item_market_listing_mappings enable row level security;
alter table public.catalog_gap_jobs enable row level security;
alter table public.estimate_case_assumptions enable row level security;
alter table public.catalog_gap_job_occurrences enable row level security;

drop policy if exists estimate_case_assumptions_company_member_read
    on public.estimate_case_assumptions;
create policy estimate_case_assumptions_company_member_read
    on public.estimate_case_assumptions for select to authenticated
    using (exists (
        select 1
        from public.company_members member
        where member.company_id = estimate_case_assumptions.company_id
          and member.user_id = (select auth.uid())
    ));

revoke all on public.reference_production_departments,
    public.reference_entity_roles,
    public.reference_material_family_categories,
    public.reference_material_families,
    public.reference_material_family_attributes,
    public.reference_material_family_department_affinities,
    public.reference_material_family_operation_eligibilities,
    public.reference_material_family_memberships,
    public.reference_brands,
    public.reference_material_family_brand_scopes,
    public.reference_brand_aliases,
    public.reference_material_models,
    public.reference_material_model_attribute_values,
    public.reference_market_material_listings,
    public.reference_market_material_supply_formats,
    public.reference_market_material_legacy_mappings,
    public.company_material_item_market_listing_mappings,
    public.catalog_gap_jobs,
    public.estimate_case_assumptions,
    public.catalog_gap_job_occurrences
from public, anon, authenticated;

grant select on public.estimate_case_assumptions to authenticated;
grant all on public.reference_production_departments,
    public.reference_entity_roles,
    public.reference_material_family_categories,
    public.reference_material_families,
    public.reference_material_family_attributes,
    public.reference_material_family_department_affinities,
    public.reference_material_family_operation_eligibilities,
    public.reference_material_family_memberships,
    public.reference_brands,
    public.reference_material_family_brand_scopes,
    public.reference_brand_aliases,
    public.reference_material_models,
    public.reference_material_model_attribute_values,
    public.reference_market_material_listings,
    public.reference_market_material_supply_formats,
    public.reference_market_material_legacy_mappings,
    public.company_material_item_market_listing_mappings,
    public.catalog_gap_jobs,
    public.estimate_case_assumptions,
    public.catalog_gap_job_occurrences
to service_role;

commit;
