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

-- Owner-approved estimating benchmark. The source's published 510 ILS
-- line is subject to a 20% project discount, equivalent to 408 ILS per
-- piece when prorated. The approved reference rate rounds that to 400 ILS.
do $$
declare
    cutout_operation_id uuid;
    benchmark_source_id constant uuid := 'f0ef9f95-77fb-42e3-bb05-84b5663bd6ee';
    benchmark_price_id constant uuid := 'e650115d-93cd-4ed6-bca4-c65c16e0f488';
begin
    select operation_id into strict cutout_operation_id
    from public.reference_operations
    where operation_code = 'stone_cutout' and active;

    if exists (
        select 1 from public.market_operation_service_prices
        where market_code = 'IL' and operation_id = cutout_operation_id
          and material_family_code = 'engineered_quartz_mineral_hybrid'
          and status = 'active' and operation_service_price_id <> benchmark_price_id
    ) then
        raise exception 'An active Israel Reference price already exists for quartz stone_cutout';
    end if;

    insert into public.reference_sources (
        source_id, market_code, source_type, source_channel, source_name, source_url,
        source_date, language_code, region, evidence
    ) values (
        benchmark_source_id, 'IL', 'official', 'public_procurement',
        'Jerusalem bill of quantities, committee 49, appendix 170049',
        'https://jerintsvcblob.blob.core.windows.net/committees/%D7%9E%D7%A1%D7%99%D7%A8%D7%AA%20%D7%A2%D7%91%D7%95%D7%93%D7%95%D7%AA%20%D7%94%D7%A4%D7%98%D7%95%D7%A8%D7%95%D7%AA%20%D7%9E%D7%9E%D7%9B%D7%A8%D7%96/49/%D7%A0%D7%A1%D7%A4%D7%97%20%D7%96%27%20170049.pdf',
        date '2026-07-15', 'he', 'Jerusalem',
        '{"source_item":"00.07.046.0170","scope":"One flush-mount sink opening in a new quartz worktop","published_ils_ex_vat":510,"project_discount_percent":20,"prorated_ils_ex_vat":408,"approved_reference_ils_ex_vat":400,"owner_approved_on":"2026-11-12"}'::jsonb
    ) on conflict (source_id) do nothing;

    insert into public.market_operation_service_prices (
        operation_service_price_id, market_code, operation_id, material_family_code,
        source_id, source_item_code, unit, currency, price_ex_vat, effective_from, status
    ) values (
        benchmark_price_id, 'IL', cutout_operation_id, 'engineered_quartz_mineral_hybrid',
        benchmark_source_id, '00.07.046.0170', 'piece', 'ILS', 400, date '2026-11-12', 'active'
    ) on conflict (operation_service_price_id) do nothing;

    if not exists (
        select 1 from public.market_operation_service_prices
        where operation_service_price_id = benchmark_price_id and status = 'active'
          and price_ex_vat = 400 and source_id = benchmark_source_id
          and market_code = 'IL' and operation_id = cutout_operation_id
          and material_family_code = 'engineered_quartz_mineral_hybrid' and unit = 'piece' and currency = 'ILS'
    ) then
        raise exception 'Israel Reference quartz stone_cutout verification failed';
    end if;
end;
$$;

commit;
