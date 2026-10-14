-- The catalog category table was introduced during the retired V2 prototype.
-- Keep its data and foreign keys, but remove the obsolete name before V3 uses it.
do $$
begin
    if to_regclass('public.reference_material_categories_v2') is not null
       and to_regclass('public.reference_material_categories') is null then
        alter table public.reference_material_categories_v2
            rename to reference_material_categories;
    end if;
end $$;

alter table public.reference_material_categories enable row level security;
