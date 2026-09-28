-- 3.14.1 CNC / Laser costing parameter foundation.
-- Additive and repeat-safe. It does not change Company Profile Machinery or
-- feed any parameter into the current Estimation scaffold.

create table if not exists public.manufacturing_cost_parameters (
    parameter_id uuid primary key default gen_random_uuid(),
    calculator text not null check (calculator in (
        'cnc_router_in_house',
        'cnc_router_subcontractor',
        'sheet_laser_in_house',
        'sheet_laser_subcontractor'
    )),
    parameter_key text not null check (
        length(trim(parameter_key)) between 1 and 120
        and parameter_key = lower(parameter_key)
        and parameter_key !~ '[^a-z0-9_]'
    ),
    country_code text not null default 'IL' check (country_code ~ '^[A-Z]{2}$'),
    region text,
    material_family text,
    thickness_min_mm numeric(10, 3) check (
        thickness_min_mm is null or thickness_min_mm >= 0
    ),
    thickness_max_mm numeric(10, 3) check (
        thickness_max_mm is null or thickness_max_mm >= 0
    ),
    machine_class text,
    object_family text,
    qualifiers jsonb not null default '{}'::jsonb check (
        jsonb_typeof(qualifiers) = 'object'
    ),
    value_low numeric(18, 6) not null,
    value_typical numeric(18, 6) not null,
    value_high numeric(18, 6) not null,
    unit text not null check (length(trim(unit)) between 1 and 80),
    currency text check (currency is null or currency ~ '^[A-Z]{3}$'),
    source_type text not null check (source_type in (
        'official',
        'provider',
        'manufacturer',
        'research',
        'platform_prior'
    )),
    source_name text not null check (length(trim(source_name)) between 1 and 240),
    source_url text,
    source_date date not null,
    evidence jsonb not null default '{}'::jsonb check (
        jsonb_typeof(evidence) = 'object'
    ),
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    status text not null default 'candidate' check (
        status in ('candidate', 'reviewed', 'active', 'archived')
    ),
    version integer not null default 1 check (version > 0),
    supersedes_parameter_id uuid references public.manufacturing_cost_parameters(parameter_id),
    effective_from date not null default current_date,
    effective_to date,
    notes text,
    created_by uuid references auth.users(id),
    approved_by uuid references auth.users(id),
    approved_at timestamptz,
    created_at timestamptz not null default now(),
    constraint manufacturing_cost_parameter_range_check check (
        value_low <= value_typical and value_typical <= value_high
    ),
    constraint manufacturing_cost_parameter_thickness_check check (
        thickness_min_mm is null
        or thickness_max_mm is null
        or thickness_min_mm <= thickness_max_mm
    ),
    constraint manufacturing_cost_parameter_effective_check check (
        effective_to is null or effective_from <= effective_to
    ),
    constraint manufacturing_cost_parameter_active_source_check check (
        status <> 'active'
        or (source_url is not null and length(trim(source_url)) > 0)
    ),
    constraint manufacturing_cost_parameter_approval_check check (
        status <> 'active'
        or (approved_by is not null and approved_at is not null)
    )
);

create index if not exists manufacturing_cost_parameters_route_idx
    on public.manufacturing_cost_parameters (
        calculator, country_code, status, parameter_key, source_date desc
    );

create index if not exists manufacturing_cost_parameters_history_idx
    on public.manufacturing_cost_parameters (
        calculator, parameter_key, version desc, created_at desc
    );

create unique index if not exists manufacturing_cost_parameters_active_scope_uidx
    on public.manufacturing_cost_parameters (
        calculator,
        parameter_key,
        country_code,
        coalesce(region, ''),
        coalesce(material_family, ''),
        coalesce(thickness_min_mm, -1),
        coalesce(thickness_max_mm, -1),
        coalesce(machine_class, ''),
        coalesce(object_family, ''),
        md5(qualifiers::text)
    )
    where status = 'active';

alter table public.manufacturing_cost_parameters enable row level security;

revoke all on public.manufacturing_cost_parameters from public, anon, authenticated;
grant all on public.manufacturing_cost_parameters to service_role;

create or replace function public.platform_admin_manufacturing_cost_parameters(
    p_requesting_user_id uuid,
    p_calculator text default null,
    p_include_history boolean default false
) returns setof public.manufacturing_cost_parameters
language plpgsql
security definer
set search_path = public
as $$
begin
    if not exists (
        select 1 from public.platform_staff s
        where s.user_id = p_requesting_user_id
          and s.active
          and s.role in ('platform_admin', 'platform_viewer')
    ) then
        raise exception 'Platform Admin access is required' using errcode = '42501';
    end if;

    if p_calculator is not null and p_calculator not in (
        'cnc_router_in_house',
        'cnc_router_subcontractor',
        'sheet_laser_in_house',
        'sheet_laser_subcontractor'
    ) then
        raise exception 'Unsupported manufacturing calculator' using errcode = '22023';
    end if;

    insert into public.platform_admin_audit_events (
        platform_user_id,
        company_id,
        action,
        metadata
    ) values (
        p_requesting_user_id,
        null,
        'manufacturing_cost_parameters_viewed',
        jsonb_build_object(
            'calculator', p_calculator,
            'include_history', coalesce(p_include_history, false)
        )
    );

    return query
    select p.*
    from public.manufacturing_cost_parameters p
    where (p_calculator is null or p.calculator = p_calculator)
      and (coalesce(p_include_history, false) or p.status <> 'archived')
    order by p.calculator, p.parameter_key, p.source_date desc, p.version desc;
end;
$$;

revoke all on function public.platform_admin_manufacturing_cost_parameters(uuid, text, boolean)
    from public, anon, authenticated;
grant execute on function public.platform_admin_manufacturing_cost_parameters(uuid, text, boolean)
    to service_role;
