-- 3.15.1 Israel Reference Catalog v1, furniture-hardware evidence batch 1.
-- Retrieved 2026-09-28. Fixed-price Gerassi product cards only. Listings with
-- "starting from" or an unresolved variant selector are intentionally omitted.

insert into public.reference_sources (
    source_id, market_code, source_type, source_name, source_url, source_date,
    language_code, region, evidence
) values
    (
        '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'IL', 'retailer',
        'Gerassi Blum hardware catalogue', 'https://gerassi.co.il/blum-hinges',
        '2026-09-28', 'he-IL', 'Mishor Adumim',
        '{"date_basis":"retrieved","selection_rule":"fixed displayed price only","unit_basis":"one displayed sellable item"}'::jsonb
    ),
    (
        '04783ea5-a268-5001-9e0e-dbc8ea95eb07', 'IL', 'retailer',
        'Gerassi site regulations', 'https://gerassi.co.il/site-regulations',
        '2026-09-28', 'he-IL', 'Mishor Adumim',
        '{"date_basis":"retrieved","vat_statement":"all site prices include VAT unless stated otherwise"}'::jsonb
    ),
    (
        'e76828b1-c4e3-5e91-9d5e-1c63702f40e5', 'IL', 'official',
        'Israel Central Bureau of Statistics, January 2025 CPI',
        'https://www.cbs.gov.il/he/mediarelease/Madad/DocLib/2025/052/10_25_052e.pdf',
        '2025-02-14', 'en-IL', null,
        '{"vat_rate":0.18,"effective_from":"2025-01-01","statement":"VAT increased from 17% to 18%"}'::jsonb
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
    ('8b1a2747-fe16-57f8-a9c2-46e292224988', 'blum_plate_straight_screws', 'hardware', 'mounting_hardware', 'Blum straight mounting plate, screw fixing', 'ea', '{"brand":"Blum","component":"hinge mounting plate","fixing":"screws"}'::jsonb),
    ('4cbfe733-44c9-55d5-83b6-ac58de00351b', 'blum_plate_expando_super_dowel10', 'hardware', 'mounting_hardware', 'Blum super Expando mounting plate, 10 mm dowel', 'ea', '{"brand":"Blum","component":"hinge mounting plate","fixing":"Expando dowel","dowel_mm":10}'::jsonb),
    ('6262bba7-e269-5904-b290-74e17d10b52b', 'blum_plate_clip_3mm_metal', 'hardware', 'mounting_hardware', 'Blum Clip metal mounting plate 3 mm', 'ea', '{"brand":"Blum","component":"hinge mounting plate","height_mm":3,"material":"metal"}'::jsonb),
    ('efb71f4a-d18b-5202-84ba-c0c9b8c57de0', 'blum_plate_clip_18mm', 'hardware', 'mounting_hardware', 'Blum Clip mounting plate 18 mm', 'ea', '{"brand":"Blum","component":"hinge mounting plate","height_mm":18}'::jsonb),
    ('fdb6d497-3cfe-5159-b0d2-c09e075d52fd', 'blum_plate_clip_9mm', 'hardware', 'mounting_hardware', 'Blum Clip mounting plate 9 mm', 'ea', '{"brand":"Blum","component":"hinge mounting plate","height_mm":9}'::jsonb),
    ('5914e09d-0a9a-527d-9de0-c1ec775f0e17', 'blum_plate_clip_6mm', 'hardware', 'mounting_hardware', 'Blum Clip mounting plate 6 mm', 'ea', '{"brand":"Blum","component":"hinge mounting plate","height_mm":6}'::jsonb),
    ('4ab99a68-64c2-5298-8a75-69c4a7599d78', 'blum_hinge_155_cliptop_blumotion_expando_straight', 'hardware', 'hinge', 'Blum 155 degree Clip Top Blumotion straight Expando hinge', 'ea', '{"brand":"Blum","opening_degrees":155,"overlay":"straight","fixing":"Expando","soft_close":true}'::jsonb),
    ('aed43afe-82b7-593a-9ab5-baf1aeaa9c3b', 'blum_hinge_corner_folding_door', 'hardware', 'hinge', 'Blum hinge for folding corner door', 'ea', '{"brand":"Blum","application":"folding corner door"}'::jsonb),
    ('b47b58cc-c32b-5a57-a156-c97ce40281cf', 'blum_aventos_hl_microwave_lift', 'hardware', 'lift_system', 'Blum Aventos HL microwave-door lift mechanism', 'ea', '{"brand":"Blum","series":"Aventos HL","application":"microwave door"}'::jsonb),
    ('ebb88591-9854-5bef-83a3-d71d14369c58', 'blum_hinge_110_blumotion_expando_bent', 'hardware', 'hinge', 'Blum 110 degree Clip Blumotion bent Expando hinge', 'ea', '{"brand":"Blum","opening_degrees":110,"overlay":"bent","fixing":"Expando","soft_close":true}'::jsonb),
    ('32ca72ec-ea9f-5dd2-bf49-bc4b5cd4ddd6', 'blum_plate_expando_clip', 'hardware', 'mounting_hardware', 'Blum Expando Clip mounting plate', 'ea', '{"brand":"Blum","component":"hinge mounting plate","fixing":"Expando"}'::jsonb),
    ('3cba326b-4522-5793-95d4-94c2e7f70d96', 'blum_plate_super_clip', 'hardware', 'mounting_hardware', 'Blum Super Clip mounting plate', 'ea', '{"brand":"Blum","component":"hinge mounting plate","series":"Super Clip"}'::jsonb),
    ('c74b749c-c4a3-5c16-8529-3dc8d332e693', 'blum_plate_super_expando', 'hardware', 'mounting_hardware', 'Blum Super Expando mounting plate', 'ea', '{"brand":"Blum","component":"hinge mounting plate","series":"Super Expando"}'::jsonb),
    ('0c20a892-a672-55ab-acde-c493f0a9207a', 'blum_plate_super_dowel10_clip', 'hardware', 'mounting_hardware', 'Blum Super Clip mounting plate with 10 mm dowel', 'ea', '{"brand":"Blum","component":"hinge mounting plate","fixing":"dowel","dowel_mm":10}'::jsonb),
    ('e875bd57-4dea-55e7-9585-4bb4ba46b3c6', 'blum_push_to_open_long_grey', 'hardware', 'lock_latch', 'Blum long grey push-to-open mechanism', 'ea', '{"brand":"Blum","mechanism":"push-to-open","length":"long","colour":"grey"}'::jsonb),
    ('94b512aa-71b8-5702-9fd0-8eb72762ef91', 'blum_push_to_open_adapter_long_grey', 'hardware', 'mounting_hardware', 'Blum adapter for long grey push-to-open mechanism', 'ea', '{"brand":"Blum","component":"push-to-open adapter","length":"long","colour":"grey"}'::jsonb)
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
    m.material_id, 'IL',
    case m.material_code
        when 'blum_plate_straight_screws' then 'תושבת אצבע ישרה משוכללת ברגים - Blum'
        when 'blum_plate_expando_super_dowel10' then 'תושבת אצבע אקספנדו סופר משוכלל דיבל 10 - Blum'
        when 'blum_plate_clip_3mm_metal' then 'תושבת 3 מ"מ מתכת קליפ - Blum'
        when 'blum_plate_clip_18mm' then 'תושבת 18 מ"מ משוכלל קליפ - Blum'
        when 'blum_plate_clip_9mm' then 'תושבת 9 מ"מ משוכלל קליפ - Blum'
        when 'blum_plate_clip_6mm' then 'תושבת 6 מ"מ משוכלל קליפ - Blum'
        when 'blum_hinge_155_cliptop_blumotion_expando_straight' then 'ציר ישר 155° קליפ טופ טריקה שקטה - אקספנדו'
        when 'blum_hinge_corner_folding_door' then 'ציר קרוסלה לדלת פינתית - Blum'
        when 'blum_aventos_hl_microwave_lift' then 'מנגנון קלאפה HL לדלת מיקרוגל - Blum'
        when 'blum_hinge_110_blumotion_expando_bent' then 'ציר כפוף 110° קליפ בלומושן אקספנדו - Blum'
        when 'blum_plate_expando_clip' then 'תושבת אקספנדו קליפ - Blum'
        when 'blum_plate_super_clip' then 'תושבת סופר משוכלל קליפ - Blum'
        when 'blum_plate_super_expando' then 'תושבת סופר אקספנדו משוכלל - Blum'
        when 'blum_plate_super_dowel10_clip' then 'תושבת אצבע שתילה סופר משוכלל דיבל 10 קליפ - Blum'
        when 'blum_push_to_open_long_grey' then 'פתיחה בלחיצה אפור ארוך - Blum'
        when 'blum_push_to_open_adapter_long_grey' then 'מתאם לפתיחה בלחיצה אפור ארוך - Blum'
    end,
    'he-IL', '{"market":"Israel","supplier":"Gerassi"}'::jsonb, 'common'
from public.reference_materials m
where m.material_code in (
    'blum_plate_straight_screws',
    'blum_plate_expando_super_dowel10',
    'blum_plate_clip_3mm_metal',
    'blum_plate_clip_18mm',
    'blum_plate_clip_9mm',
    'blum_plate_clip_6mm',
    'blum_hinge_155_cliptop_blumotion_expando_straight',
    'blum_hinge_corner_folding_door',
    'blum_aventos_hl_microwave_lift',
    'blum_hinge_110_blumotion_expando_bent',
    'blum_plate_expando_clip',
    'blum_plate_super_clip',
    'blum_plate_super_expando',
    'blum_plate_super_dowel10_clip',
    'blum_push_to_open_long_grey',
    'blum_push_to_open_adapter_long_grey'
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
    ('704760e0-732e-503a-ab1c-7be615500469', '8b1a2747-fe16-57f8-a9c2-46e292224988', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 5.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 4.237288, 'ea', '{"vat_rate":0.18,"calculation":"5.00 / 1.18","vat_evidence_source_id":"04783ea5-a268-5001-9e0e-dbc8ea95eb07","rate_evidence_source_id":"e76828b1-c4e3-5e91-9d5e-1c63702f40e5"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('443e6143-040c-5f58-9b07-b37681695f68', '4cbfe733-44c9-55d5-83b6-ac58de00351b', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 4.50, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 3.813559, 'ea', '{"vat_rate":0.18,"calculation":"4.50 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('67cb5cab-65b8-5e10-a448-c9b34851dee2', '6262bba7-e269-5904-b290-74e17d10b52b', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 2.50, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 2.118644, 'ea', '{"vat_rate":0.18,"calculation":"2.50 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('30fa9a97-8fa3-59eb-a6c2-7c928eaa8a14', 'efb71f4a-d18b-5202-84ba-c0c9b8c57de0', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 14.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 11.864407, 'ea', '{"vat_rate":0.18,"calculation":"14.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('d3959db8-dbfd-55d6-b95b-0ac775a8d5df', 'fdb6d497-3cfe-5159-b0d2-c09e075d52fd', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 11.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 9.322034, 'ea', '{"vat_rate":0.18,"calculation":"11.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('d44d3bc7-f794-5cb0-b74d-dd99795b2aad', '5914e09d-0a9a-527d-9de0-c1ec775f0e17', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 8.50, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 7.203390, 'ea', '{"vat_rate":0.18,"calculation":"8.50 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('302eb8aa-8989-5d89-bb7d-71bbd86393fe', '4ab99a68-64c2-5298-8a75-69c4a7599d78', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 49.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 41.525424, 'ea', '{"vat_rate":0.18,"calculation":"49.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('24f1bdd1-7996-5a74-8c44-2cdee12275ea', 'aed43afe-82b7-593a-9ab5-baf1aeaa9c3b', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 33.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 27.966102, 'ea', '{"vat_rate":0.18,"calculation":"33.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('1af9a327-2c67-54a6-a35e-c3f7fc4c4a1e', 'b47b58cc-c32b-5a57-a156-c97ce40281cf', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 550.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 466.101695, 'ea', '{"vat_rate":0.18,"calculation":"550.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 80, 'candidate'),
    ('2d59d20d-0447-5119-ab98-73d57ac322e6', 'ebb88591-9854-5bef-83a3-d71d14369c58', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 24.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 20.338983, 'ea', '{"vat_rate":0.18,"calculation":"24.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('a675579d-f3f2-5b8a-9093-175a494918cd', '32ca72ec-ea9f-5dd2-bf49-bc4b5cd4ddd6', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 4.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 3.389831, 'ea', '{"vat_rate":0.18,"calculation":"4.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('3bb9c4b1-d049-5cbe-b645-cd657f118e95', '3cba326b-4522-5793-95d4-94c2e7f70d96', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 4.50, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 3.813559, 'ea', '{"vat_rate":0.18,"calculation":"4.50 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('098a05c6-a794-5402-857f-22b6489057a0', 'c74b749c-c4a3-5c16-8529-3dc8d332e693', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 5.50, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 4.661017, 'ea', '{"vat_rate":0.18,"calculation":"5.50 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('90596341-8062-5797-b433-a2b3b8007b71', '0c20a892-a672-55ab-acde-c493f0a9207a', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 5.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 4.237288, 'ea', '{"vat_rate":0.18,"calculation":"5.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('5f79ecf7-32d8-568d-81ad-43d8a6886ba5', 'e875bd57-4dea-55e7-9585-4bb4ba46b3c6', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 36.70, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 31.101695, 'ea', '{"vat_rate":0.18,"calculation":"36.70 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate'),
    ('492fb0d0-4870-59dd-8a17-9904c62381e1', '94b512aa-71b8-5702-9fd0-8eb72762ef91', 'IL', '3cac47d1-d2a7-5002-abb8-7f7ae2ebcd36', 'Gerassi', null, 7.00, 'ILS', 'displayed_item', 'retail_package', '{}', false, 1, 1, 'included', 5.932203, 'ea', '{"vat_rate":0.18,"calculation":"7.00 / 1.18"}'::jsonb, 'Mishor Adumim', '2026-09-28', 82, 'candidate')
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
