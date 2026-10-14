-- The original Israel Reference category table uses category_code as its key.
-- Family categories use their own UUID key, so V3 reads a neutral view over
-- the existing family-category table without touching Israel Reference.
do $$
begin
    if to_regclass('public.reference_material_categories_v2') is not null then
        execute $view$
            create or replace view public.reference_material_family_categories as
            select
                category_id,
                category_code,
                category_name,
                production_department_code,
                entity_role_code,
                parent_category_id,
                active,
                sort_order
            from public.reference_material_categories_v2
        $view$;
    end if;
end $$;
