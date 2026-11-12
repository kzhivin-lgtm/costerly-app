-- Reference prices for purchased fabrication services in the local market.
-- Prices are stored excluding VAT, like estimate-wide purchasing costs.
begin;

create table if not exists public.market_operation_service_prices (
    operation_service_price_id uuid primary key default gen_random_uuid(),
    market_code text not null references public.reference_markets(market_code),
    operation_id uuid not null references public.reference_operations(operation_id),
    material_family_code text not null references public.reference_material_families(family_code),
    source_id uuid not null,
    source_item_code text not null check (length(trim(source_item_code)) between 1 and 140),
    unit text not null check (unit = 'piece'),
    currency text not null check (currency ~ '^[A-Z]{3}$'),
    price_ex_vat numeric(16, 4) not null check (price_ex_vat > 0),
    effective_from date not null,
    effective_to date,
    status text not null default 'candidate' check (status in ('candidate', 'active', 'retired')),
    created_at timestamptz not null default now(),
    foreign key (source_id, market_code) references public.reference_sources(source_id, market_code),
    check (effective_to is null or effective_to >= effective_from),
    unique (market_code, operation_id, material_family_code, source_id, source_item_code, effective_from)
);

create unique index if not exists market_operation_service_prices_one_active_idx
    on public.market_operation_service_prices (market_code, operation_id, material_family_code)
    where status = 'active';

alter table public.market_operation_service_prices enable row level security;
revoke all on public.market_operation_service_prices from public, anon, authenticated;
grant all on public.market_operation_service_prices to service_role;

commit;
