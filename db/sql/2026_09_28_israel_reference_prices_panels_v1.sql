-- 3.15.1 Israel Reference Catalog v1, panel-material evidence batch 1.
-- Retrieved 2026-09-28. All offers remain candidate until VAT, availability,
-- and comparable-source review support an approved market baseline.

insert into public.reference_sources (
    source_id, market_code, source_type, source_name, source_url, source_date,
    language_code, region, evidence
) values
    (
        'a47ab759-c07e-5e62-bb7b-50bb0eb152b0', 'IL', 'retailer',
        'Camisa MDF product page',
        'https://www.camisa.co.il/product/%D7%9E%D7%93%D7%A4-mdf-%D7%9C%D7%95%D7%97-%D7%9E%D7%AA%D7%95%D7%A2%D7%A9/',
        '2026-09-28', 'he-IL', null,
        '{"date_basis":"retrieved","dimensions_mm":[2440,1220],"delivery":"extra","vat":"not stated on product page"}'::jsonb
    ),
    (
        'a838e5b8-618c-50a9-b4e7-71221d71ebe4', 'IL', 'retailer',
        'Camisa birch plywood product page',
        'https://www.camisa.co.il/product/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A1%D7%A0%D7%93%D7%95%D7%95%D7%99%D7%A5-%D7%9C%D7%91%D7%A0%D7%94-%D7%90%D7%99%D7%9B%D7%95%D7%AA%D7%99%D7%95%D7%AA/',
        '2026-09-28', 'he-IL', null,
        '{"date_basis":"retrieved","dimensions_mm":[2440,1220],"delivery":"extra","vat":"not stated on product page"}'::jsonb
    ),
    (
        '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'IL', 'retailer',
        'Camisa plywood product page',
        'https://www.camisa.co.il/product/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%91%D7%95%D7%93-%D7%A1%D7%A0%D7%93%D7%95%D7%95%D7%99%D7%A5/',
        '2026-09-28', 'he-IL', null,
        '{"date_basis":"retrieved","dimensions_mm":[2440,1220],"delivery":"extra","thickness_tolerance_mm":1,"vat":"not stated on product page"}'::jsonb
    ),
    (
        '9a20d587-e080-5f28-8717-310805fbbf1b', 'IL', 'retailer',
        'Camisa coloured melamine particleboard product page',
        'https://www.camisa.co.il/product/%D7%A4%D7%9C%D7%98%D7%94-%D7%A1%D7%99%D7%91%D7%99%D7%AA-%D7%9E%D7%9C%D7%9E%D7%99%D7%9F-%D7%A6%D7%91%D7%A2%D7%95%D7%A0%D7%99-%D7%91%D7%A2%D7%95%D7%91%D7%99-17-%D7%9E%D7%9E-%D7%91%D7%9E%D7%91%D7%97/',
        '2026-09-28', 'he-IL', null,
        '{"date_basis":"retrieved","dimensions_mm":[2440,1220],"delivery":"extra","vat":"not stated on product page"}'::jsonb
    ),
    (
        '0e91a395-ac15-5d4f-bf66-c86e3b1743e2', 'IL', 'retailer',
        'Camisa coloured laminate-faced plywood product page',
        'https://www.camisa.co.il/product/%D7%A1%D7%A0%D7%93%D7%95%D7%95%D7%99%D7%A5-17-%D7%9E%D7%9E-%D7%A9%D7%A0%D7%99-%D7%A6%D7%93%D7%93%D7%99%D7%9D-%D7%A4%D7%95%D7%A8%D7%9E%D7%99%D7%99%D7%A7%D7%94-%D7%A6%D7%91%D7%A2%D7%95%D7%A0%D7%99/',
        '2026-09-28', 'he-IL', null,
        '{"date_basis":"retrieved","dimensions_mm":[2440,1220],"faces":2,"delivery":"extra","vat":"not stated on product page"}'::jsonb
    ),
    (
        'bfd58ed8-5301-5f2b-b0a6-6b96f679a2db', 'IL', 'supplier',
        'Algolan Express cut-to-size panel list',
        'https://algolan-express.co.il/',
        '2026-09-28', 'he-IL', 'Jerusalem',
        '{"date_basis":"retrieved","vat":"excluded","cutting":"included","sheet_dimensions":"not stated"}'::jsonb
    ),
    (
        '4a672a25-9f87-51bf-bfd1-a86f2cd8795c', 'IL', 'retailer',
        'Hayozrim brown MDF 17 mm cut-to-size page',
        'https://hayozrim.com/products/mdf-brown-17mm',
        '2026-09-28', 'he-IL', 'Beit Shean',
        '{"date_basis":"retrieved","price_unit":"sqm","cutting":"included","supported_dimensions_cm":{"min":[10,10],"max":[240,120]},"vat":"not stated on this product page"}'::jsonb
    )
on conflict (source_id) do update set
    source_name = excluded.source_name,
    source_url = excluded.source_url,
    source_date = excluded.source_date,
    language_code = excluded.language_code,
    region = excluded.region,
    evidence = excluded.evidence,
    retrieved_at = now();

insert into public.reference_materials (
    material_id, material_code, department, category_code, canonical_name,
    base_unit, specifications
) values
    ('875b0bf6-172b-5579-a0a3-4c3a10fb371b', 'mdf_standard_4mm', 'wood', 'mdf', 'Standard raw MDF 4 mm', 'sqm', '{"thickness_mm":4,"surface":"raw","moisture_resistant":false}'::jsonb),
    ('ae8361c6-6d66-5e7c-8531-c6e764c79f53', 'mdf_standard_6mm', 'wood', 'mdf', 'Standard raw MDF 6 mm', 'sqm', '{"thickness_mm":6,"surface":"raw","moisture_resistant":false}'::jsonb),
    ('e0a6fdaa-7864-5b04-8590-66b4e1c7f548', 'mdf_standard_10mm', 'wood', 'mdf', 'Standard raw MDF 10 mm', 'sqm', '{"thickness_mm":10,"surface":"raw","moisture_resistant":false}'::jsonb),
    ('0082f4d7-5954-578d-a853-a60b43b8c207', 'mdf_standard_12mm', 'wood', 'mdf', 'Standard raw MDF 12 mm', 'sqm', '{"thickness_mm":12,"surface":"raw","moisture_resistant":false}'::jsonb),
    ('5f0709f7-a802-5d9c-a928-4eb72852d652', 'mdf_standard_17mm', 'wood', 'mdf', 'Standard raw MDF 17 mm', 'sqm', '{"thickness_mm":17,"surface":"raw","moisture_resistant":false}'::jsonb),
    ('76f2e435-baeb-52ff-873b-8f0b9076b46a', 'mdf_standard_27mm', 'wood', 'mdf', 'Standard raw MDF 27 mm', 'sqm', '{"thickness_mm":27,"surface":"raw","moisture_resistant":false}'::jsonb),
    ('b06210b3-bebf-58a1-9524-0e35583f0b52', 'mdf_mr_green_17mm', 'wood', 'mdf', 'Moisture-resistant green MDF 17 mm', 'sqm', '{"thickness_mm":17,"surface":"raw","moisture_resistant":true,"colour":"green"}'::jsonb),
    ('08254ef5-3c1f-5cbf-96bb-7317b25eaa70', 'mdf_mr_green_19mm', 'wood', 'mdf', 'Moisture-resistant green MDF 19 mm', 'sqm', '{"thickness_mm":19,"surface":"raw","moisture_resistant":true,"colour":"green"}'::jsonb),
    ('5a818eae-0d4e-5a1f-92a7-8c295ba0853e', 'mdf_mr_green_22mm', 'wood', 'mdf', 'Moisture-resistant green MDF 22 mm', 'sqm', '{"thickness_mm":22,"surface":"raw","moisture_resistant":true,"colour":"green"}'::jsonb),
    ('6483cfba-56ab-52b2-b173-13ae5ddf401e', 'birch_plywood_9mm', 'wood', 'plywood', 'Birch plywood 9 mm', 'sqm', '{"thickness_mm":9,"species":"birch","surface":"raw"}'::jsonb),
    ('c41c1b20-3a63-52de-9a27-8e0976211e7d', 'birch_plywood_12mm', 'wood', 'plywood', 'Birch plywood 12 mm', 'sqm', '{"thickness_mm":12,"species":"birch","surface":"raw"}'::jsonb),
    ('ae666430-92e3-5942-8b74-486e23d364d2', 'birch_plywood_16mm', 'wood', 'plywood', 'Birch plywood 16 mm', 'sqm', '{"thickness_mm":16,"species":"birch","surface":"raw"}'::jsonb),
    ('d6dd463a-110b-52da-8dad-954be85c15df', 'birch_plywood_18mm', 'wood', 'plywood', 'Birch plywood 18 mm', 'sqm', '{"thickness_mm":18,"species":"birch","surface":"raw"}'::jsonb),
    ('50d80607-a1cb-5f2d-9571-f04f1c5869be', 'commercial_plywood_4mm', 'wood', 'plywood', 'Commercial plywood 4 mm', 'sqm', '{"thickness_mm":4,"surface":"raw"}'::jsonb),
    ('6ba4c54c-9d93-5354-b93d-0637767db886', 'commercial_plywood_6mm', 'wood', 'plywood', 'Commercial plywood 6 mm', 'sqm', '{"thickness_mm":6,"surface":"raw"}'::jsonb),
    ('56ad33c8-84e8-5895-a22a-98a3020c7960', 'commercial_plywood_8mm', 'wood', 'plywood', 'Commercial plywood 8 mm', 'sqm', '{"thickness_mm":8,"surface":"raw"}'::jsonb),
    ('1ff1edba-91db-5494-87e8-515fb9ec2a88', 'commercial_plywood_10mm', 'wood', 'plywood', 'Commercial plywood 10 mm', 'sqm', '{"thickness_mm":10,"surface":"raw"}'::jsonb),
    ('42cede69-ad33-51e9-aef0-de6ab03f5fe5', 'commercial_plywood_12mm', 'wood', 'plywood', 'Commercial plywood 12 mm', 'sqm', '{"thickness_mm":12,"surface":"raw"}'::jsonb),
    ('4438014d-8957-5d3d-b9cd-3c8aff05402e', 'commercial_plywood_17mm', 'wood', 'plywood', 'Commercial plywood 17 mm', 'sqm', '{"thickness_mm":17,"surface":"raw"}'::jsonb),
    ('3d4a16fd-7420-592e-b8d7-d52971f6b44f', 'commercial_plywood_20mm', 'wood', 'plywood', 'Commercial plywood 20 mm', 'sqm', '{"thickness_mm":20,"surface":"raw"}'::jsonb),
    ('516bdae5-3a2e-59b9-9b47-4552e0af8b0e', 'commercial_plywood_24mm', 'wood', 'plywood', 'Commercial plywood 24 mm', 'sqm', '{"thickness_mm":24,"surface":"raw"}'::jsonb),
    ('2c5b446a-d2bf-5f08-9f53-1a5d52f8f0b2', 'melamine_particleboard_coloured_17mm', 'wood', 'particleboard', 'Coloured melamine-faced particleboard 17 mm', 'sqm', '{"thickness_mm":17,"surface":"melamine","colour":"assorted"}'::jsonb),
    ('d7aad163-f991-5cd0-8d4c-4bf31f218495', 'laminate_faced_plywood_coloured_17mm', 'wood', 'plywood', 'Two-sided coloured laminate-faced plywood 17 mm', 'sqm', '{"thickness_mm":17,"surface":"decorative_laminate","faces":2,"colour":"assorted"}'::jsonb)
on conflict (material_code) do update set
    department = excluded.department,
    category_code = excluded.category_code,
    canonical_name = excluded.canonical_name,
    base_unit = excluded.base_unit,
    specifications = excluded.specifications,
    active = true,
    updated_at = now();

insert into public.market_material_profiles (
    material_id, market_code, market_name, language_code,
    local_specifications, availability_status
)
select
    m.material_id,
    'IL',
    case m.material_code
        when 'mdf_standard_4mm' then 'MDF גלוי 4 מ"מ'
        when 'mdf_standard_6mm' then 'MDF גלוי 6 מ"מ'
        when 'mdf_standard_10mm' then 'MDF גלוי 10 מ"מ'
        when 'mdf_standard_12mm' then 'MDF גלוי 12 מ"מ'
        when 'mdf_standard_17mm' then 'MDF גלוי 17 מ"מ'
        when 'mdf_standard_27mm' then 'MDF גלוי 27 מ"מ'
        when 'mdf_mr_green_17mm' then 'MDF ירוק 17 מ"מ'
        when 'mdf_mr_green_19mm' then 'MDF ירוק 19 מ"מ'
        when 'mdf_mr_green_22mm' then 'MDF ירוק 22 מ"מ'
        when 'birch_plywood_9mm' then 'סנדוויץ לבנה 9 מ"מ'
        when 'birch_plywood_12mm' then 'סנדוויץ לבנה 12 מ"מ'
        when 'birch_plywood_16mm' then 'סנדוויץ לבנה 16 מ"מ'
        when 'birch_plywood_18mm' then 'סנדוויץ לבנה 18 מ"מ'
        when 'commercial_plywood_4mm' then 'דיקט סנדוויץ 4 מ"מ'
        when 'commercial_plywood_6mm' then 'דיקט סנדוויץ 6 מ"מ'
        when 'commercial_plywood_8mm' then 'דיקט סנדוויץ 8 מ"מ'
        when 'commercial_plywood_10mm' then 'דיקט סנדוויץ 10 מ"מ'
        when 'commercial_plywood_12mm' then 'דיקט סנדוויץ 12 מ"מ'
        when 'commercial_plywood_17mm' then 'דיקט סנדוויץ 17 מ"מ'
        when 'commercial_plywood_20mm' then 'דיקט סנדוויץ 20 מ"מ'
        when 'commercial_plywood_24mm' then 'דיקט סנדוויץ 24 מ"מ'
        when 'melamine_particleboard_coloured_17mm' then 'סיבית מלמין צבעוני 17 מ"מ'
        when 'laminate_faced_plywood_coloured_17mm' then 'סנדוויץ פורמייקה צבעונית דו צדדי 17 מ"מ'
    end,
    'he-IL',
    '{"market":"Israel"}'::jsonb,
    'common'
from public.reference_materials m
where m.material_code in (
    'mdf_standard_4mm', 'mdf_standard_6mm', 'mdf_standard_10mm',
    'mdf_standard_12mm', 'mdf_standard_17mm', 'mdf_standard_27mm',
    'mdf_mr_green_17mm', 'mdf_mr_green_19mm', 'mdf_mr_green_22mm',
    'birch_plywood_9mm', 'birch_plywood_12mm', 'birch_plywood_16mm',
    'birch_plywood_18mm', 'commercial_plywood_4mm', 'commercial_plywood_6mm',
    'commercial_plywood_8mm', 'commercial_plywood_10mm',
    'commercial_plywood_12mm', 'commercial_plywood_17mm',
    'commercial_plywood_20mm', 'commercial_plywood_24mm',
    'melamine_particleboard_coloured_17mm',
    'laminate_faced_plywood_coloured_17mm'
)
on conflict (material_id, market_code, language_code) do update set
    market_name = excluded.market_name,
    local_specifications = excluded.local_specifications,
    availability_status = excluded.availability_status,
    active = true,
    updated_at = now();

insert into public.market_material_offers (
    market_offer_id, material_id, market_code, source_id, supplier_name,
    supplier_sku, source_price, source_currency, source_unit, price_scope,
    included_services, delivery_included, package_quantity,
    minimum_order_quantity, vat_mode, normalized_price_ex_vat,
    normalized_unit, conversion_basis, region, valid_from, confidence, status
) values
    ('0cfc4ea8-7517-5398-9ef0-9a0d1348e5f1', '875b0bf6-172b-5579-a0a3-4c3a10fb371b', 'IL', 'a47ab759-c07e-5e62-bb7b-50bb0eb152b0', 'Camisa', 'MDF-4', 60, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('c2abd4d8-078c-554f-b9be-ba318f247786', 'ae8361c6-6d66-5e7c-8531-c6e764c79f53', 'IL', 'a47ab759-c07e-5e62-bb7b-50bb0eb152b0', 'Camisa', 'MDF-6', 79, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('25917bf0-12c8-5fc9-a5b8-5d35ae91d7f4', 'e0a6fdaa-7864-5b04-8590-66b4e1c7f548', 'IL', 'a47ab759-c07e-5e62-bb7b-50bb0eb152b0', 'Camisa', 'MDF-10', 107, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('16a36964-5cce-5f6a-b00e-1f36bb0cb436', '0082f4d7-5954-578d-a853-a60b43b8c207', 'IL', 'a47ab759-c07e-5e62-bb7b-50bb0eb152b0', 'Camisa', 'MDF-12', 150, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('f9ab8234-2957-520b-8fba-ef622697ff77', '5f0709f7-a802-5d9c-a928-4eb72852d652', 'IL', 'a47ab759-c07e-5e62-bb7b-50bb0eb152b0', 'Camisa', 'MDF-17', 147, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('96bb929e-bc30-56eb-aeb9-69de7b0baada', '76f2e435-baeb-52ff-873b-8f0b9076b46a', 'IL', 'a47ab759-c07e-5e62-bb7b-50bb0eb152b0', 'Camisa', 'MDF-27', 319, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('e583a876-0efc-57ba-a7cb-48b8ddf89b81', '6483cfba-56ab-52b2-b173-13ae5ddf401e', 'IL', 'a838e5b8-618c-50a9-b4e7-71221d71ebe4', 'Camisa', 'BIRCH-PLY-9', 206, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('9aeef1f4-2582-508c-9824-432aac93aafc', 'c41c1b20-3a63-52de-9a27-8e0976211e7d', 'IL', 'a838e5b8-618c-50a9-b4e7-71221d71ebe4', 'Camisa', 'BIRCH-PLY-12', 221, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('5ac1622b-dbc7-53b7-b1f4-098669394fda', 'ae666430-92e3-5942-8b74-486e23d364d2', 'IL', 'a838e5b8-618c-50a9-b4e7-71221d71ebe4', 'Camisa', 'BIRCH-PLY-16', 253, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('5a94e15c-94cc-5407-b50d-a176c93c8a93', 'd6dd463a-110b-52da-8dad-954be85c15df', 'IL', 'a838e5b8-618c-50a9-b4e7-71221d71ebe4', 'Camisa', 'BIRCH-PLY-18', 281, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768}'::jsonb, null, '2026-09-28', 70, 'candidate'),
    ('72b04bae-f08a-584a-880d-3e5f95f37bf9', '50d80607-a1cb-5f2d-9571-f04f1c5869be', 'IL', '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'Camisa', 'PLY-4', 83, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"thickness_tolerance_mm":1}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('3670fcb8-39db-550e-9ed8-340592afc802', '6ba4c54c-9d93-5354-b93d-0637767db886', 'IL', '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'Camisa', 'PLY-6', 92, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"thickness_tolerance_mm":1}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('fb041a22-d2d0-5078-b8c1-80ff3727fd91', '56ad33c8-84e8-5895-a22a-98a3020c7960', 'IL', '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'Camisa', 'PLY-8', 120, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"thickness_tolerance_mm":1}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('b5935e0b-06d4-5f19-aaa6-f0d675d0f582', '1ff1edba-91db-5494-87e8-515fb9ec2a88', 'IL', '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'Camisa', 'PLY-10', 135, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"thickness_tolerance_mm":1}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('e7504240-c0f3-587f-b998-8dad9c15adfb', '42cede69-ad33-51e9-aef0-de6ab03f5fe5', 'IL', '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'Camisa', 'PLY-12', 162, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"thickness_tolerance_mm":1}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('6ad8a8f8-44f3-51bf-8782-838f3ff25831', '4438014d-8957-5d3d-b9cd-3c8aff05402e', 'IL', '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'Camisa', 'PLY-17', 176, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"thickness_tolerance_mm":1}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('327b45a8-d12f-569c-848e-e30c87cdc6f3', '3d4a16fd-7420-592e-b8d7-d52971f6b44f', 'IL', '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'Camisa', 'PLY-20', 307, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"thickness_tolerance_mm":1}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('80911a05-8501-5b3b-ad42-ee722e3cfea0', '516bdae5-3a2e-59b9-9b47-4552e0af8b0e', 'IL', '1b346b9b-59af-5a7e-8baa-3696554b57cc', 'Camisa', 'PLY-24', 330, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"thickness_tolerance_mm":1}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('0ed0a890-cf1f-5547-b153-2deebed5cb13', '2c5b446a-d2bf-5f08-9f53-1a5d52f8f0b2', 'IL', '9a20d587-e080-5f28-8717-310805fbbf1b', 'Camisa', 'MEL-PB-COLOR-17', 223, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"colour":"selected variant"}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('4e25fe4a-5a9f-5534-bdea-c8d62a4aca80', 'd7aad163-f991-5cd0-8d4c-4bf31f218495', 'IL', '0e91a395-ac15-5d4f-bf66-c86e3b1743e2', 'Camisa', 'LAM-PLY-COLOR-17', 280, 'ILS', 'sheet_2440x1220', 'material_only', '{}', false, 1, 1, 'unknown', null, null, '{"sheet_area_sqm":2.9768,"faces":2,"colour":"selected variant"}'::jsonb, null, '2026-09-28', 68, 'candidate'),
    ('a56c3518-3d39-5975-b86e-2955fd1a230f', 'b06210b3-bebf-58a1-9524-0e35583f0b52', 'IL', 'bfd58ed8-5301-5f2b-b0a6-6b96f679a2db', 'Algolan Express', 'MDF-GREEN-17-CUT', 210, 'ILS', 'sheet_dimensions_unstated', 'cut_to_size', '{"cutting"}', null, 1, 1, 'excluded', null, null, '{"normalization_blocked_by":"sheet dimensions not stated"}'::jsonb, 'Jerusalem', '2026-09-28', 65, 'candidate'),
    ('b399433a-c5a8-5ed5-b123-68d8a0c8ffbf', '08254ef5-3c1f-5cbf-96bb-7317b25eaa70', 'IL', 'bfd58ed8-5301-5f2b-b0a6-6b96f679a2db', 'Algolan Express', 'MDF-GREEN-19-CUT', 230, 'ILS', 'sheet_dimensions_unstated', 'cut_to_size', '{"cutting"}', null, 1, 1, 'excluded', null, null, '{"normalization_blocked_by":"sheet dimensions not stated"}'::jsonb, 'Jerusalem', '2026-09-28', 65, 'candidate'),
    ('ed7f9b7a-c49e-5828-a05d-1d8e444b867b', '5a818eae-0d4e-5a1f-92a7-8c295ba0853e', 'IL', 'bfd58ed8-5301-5f2b-b0a6-6b96f679a2db', 'Algolan Express', 'MDF-GREEN-22-CUT', 310, 'ILS', 'sheet_dimensions_unstated', 'cut_to_size', '{"cutting"}', null, 1, 1, 'excluded', null, null, '{"normalization_blocked_by":"sheet dimensions not stated"}'::jsonb, 'Jerusalem', '2026-09-28', 65, 'candidate'),
    ('5c0bff1f-f893-5f3d-b017-ec5520a62946', '5f0709f7-a802-5d9c-a928-4eb72852d652', 'IL', '4a672a25-9f87-51bf-bfd1-a86f2cd8795c', 'Hayozrim', 'MDF-BROWN-17-CUT', 208, 'ILS', 'sqm', 'cut_to_size', '{"precision_cutting"}', null, null, null, 'unknown', null, null, '{"source_unit":"sqm","minimum_checkout_total_ils":50}'::jsonb, 'Beit Shean', '2026-09-28', 75, 'candidate')
on conflict (market_offer_id) do update set
    source_price = excluded.source_price,
    source_currency = excluded.source_currency,
    source_unit = excluded.source_unit,
    price_scope = excluded.price_scope,
    included_services = excluded.included_services,
    delivery_included = excluded.delivery_included,
    package_quantity = excluded.package_quantity,
    minimum_order_quantity = excluded.minimum_order_quantity,
    vat_mode = excluded.vat_mode,
    normalized_price_ex_vat = excluded.normalized_price_ex_vat,
    normalized_unit = excluded.normalized_unit,
    conversion_basis = excluded.conversion_basis,
    region = excluded.region,
    valid_from = excluded.valid_from,
    confidence = excluded.confidence,
    status = excluded.status;
