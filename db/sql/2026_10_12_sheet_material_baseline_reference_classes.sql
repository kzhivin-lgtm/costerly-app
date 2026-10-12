-- 3.17.2.9: Complete baseline Israel classes used by the shared sheet resolver.
-- Trade names such as Twin, Combi and Okoume remain supplier evidence. They
-- resolve to the raw-plywood class of the same thickness, never to a special
-- birch/HPL/veneered class.
begin;

with raw_plywood(thickness_mm) as (
    values (3), (4), (5), (6), (8), (9), (10), (12), (15), (18), (21),
           (24), (25), (27), (30), (35), (40), (45), (50)
)
insert into public.reference_materials (
    material_code, department, category_code, canonical_name, base_unit, specifications, active
)
select
    'gcm_baseline_plywood_raw_' || thickness_mm || 'mm',
    'wood',
    'gcm_366f7689193afaf6f0a55a20',
    'Plywood, raw, ' || thickness_mm || ' mm',
    'm2',
    jsonb_build_object(
        'catalog_version', 'israel_global_catalog_v1',
        'global_canonical_id', 'GCM-V1-PLY-RAW-' || thickness_mm || '-MM',
        'category_en', 'Wood panels',
        'subcategory_en', 'Plywood',
        'canonical_name_he', 'לביד גולמי, ' || thickness_mm || ' מ״מ',
        'material_family', 'plywood',
        'construction', 'raw',
        'thickness_mm', thickness_mm,
        'pricing_method', 'reference_class_pending_price'
    ),
    true
from raw_plywood
on conflict (material_code) do update set
    canonical_name = excluded.canonical_name,
    specifications = excluded.specifications,
    active = true,
    updated_at = now();

with raw_mdf(thickness_mm) as (
    values (4), (6), (8), (10), (12), (16), (18), (19), (22), (25), (28), (30)
), faced_mdf(thickness_mm) as (
    values (4), (6), (8), (10), (12), (16), (18), (19), (22), (25), (28), (30)
), baseline_mdf(construction, thickness_mm, category_code, canonical_name) as (
    select
        'raw', thickness_mm, 'gcm_872a62372adec333d2c0a62c',
        'MDF, raw, ' || thickness_mm || ' mm'
    from raw_mdf
    union all
    select
        'plastic_laminate_faced', thickness_mm, 'gcm_40c81f29fd45ae19ca4e5ce9',
        'MDF, plastic laminate faced, ' || thickness_mm || ' mm'
    from faced_mdf
)
insert into public.reference_materials (
    material_code, department, category_code, canonical_name, base_unit, specifications, active
)
select
    'gcm_baseline_mdf_' || construction || '_' || thickness_mm || 'mm',
    'wood',
    category_code,
    canonical_name,
    'm2',
    jsonb_build_object(
        'catalog_version', 'israel_global_catalog_v1',
        'global_canonical_id', 'GCM-V1-MDF-' || upper(construction) || '-' || thickness_mm || '-MM',
        'category_en', 'Wood panels',
        'subcategory_en', case when construction = 'raw' then 'MDF and HDF' else 'Faced MDF' end,
        'material_family', 'mdf',
        'construction', construction,
        'thickness_mm', thickness_mm,
        'pricing_method', 'reference_class_pending_price'
    ),
    true
from baseline_mdf
on conflict (material_code) do update set
    canonical_name = excluded.canonical_name,
    specifications = excluded.specifications,
    active = true,
    updated_at = now();

commit;
