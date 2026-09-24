-- 3.9.1 Add galvanizing to the additive Machinery catalog.
-- Repeat-safe and intentionally does not modify historical capability rows.

insert into public.machinery_catalog
    (machine_code, industry, category, display_name, description, sort_order)
values
    (
        'finish_galvanizing',
        'finishing',
        'protective_coating',
        'Galvanizing',
        'Zinc coating for corrosion protection',
        380
    )
on conflict (machine_code) do update set
    industry = excluded.industry,
    category = excluded.category,
    display_name = excluded.display_name,
    description = excluded.description,
    sort_order = excluded.sort_order,
    active = true,
    updated_at = now();
