alter table public.overhead_settings
    add column if not exists consumables_percent numeric not null default 5
        check (consumables_percent between 0 and 100),
    add column if not exists packaging_percent numeric not null default 1
        check (packaging_percent between 0 and 100),
    add column if not exists paint_consumables_percent numeric not null default 10
        check (paint_consumables_percent between 0 and 100);
