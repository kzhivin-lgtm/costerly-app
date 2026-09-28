-- 3.15.1 Israel Reference Catalog v1, metal evidence batch 1.
-- Retrieved 2026-09-28. Exact selected variant only.

insert into public.reference_sources (
    source_id, market_code, source_type, source_name, source_url, source_date,
    language_code, region, evidence
) values
    ('de18095f-0427-5d4f-b2d2-65f37b42ead9', 'IL', 'retailer',
     'Amrusi galvanized steel profile',
     'https://www.amrusi.co.il/%D7%A4%D7%A8%D7%95%D7%A4%D7%99%D7%9C-%D7%91%D7%A8%D7%96%D7%9C-%D7%9E%D7%92%D7%95%D7%9C%D7%95%D7%95%D7%9F',
     '2026-09-28', 'he-IL', 'Petah Tikva',
     '{"date_basis":"retrieved","selected_variant":"20x20x1.5 mm","stock_length_m":6,"cutting":"extra charge","delivery":"extra"}'::jsonb),
    ('d4a94319-9f55-51d3-ab02-2a30f1398332', 'IL', 'retailer',
     'Amrusi terms of use',
     'https://www.amrusi.co.il/%D7%AA%D7%A0%D7%90%D7%99_%D7%A9%D7%99%D7%9E%D7%95%D7%A9',
     '2026-09-28', 'he-IL', 'Petah Tikva',
     '{"date_basis":"retrieved","vat_statement":"product prices include VAT unless stated otherwise"}'::jsonb)
on conflict (source_id) do update set
    source_name=excluded.source_name, source_url=excluded.source_url,
    source_date=excluded.source_date, language_code=excluded.language_code,
    region=excluded.region, evidence=excluded.evidence, retrieved_at=now();

insert into public.reference_materials (
    material_id, material_code, department, category_code, canonical_name,
    base_unit, specifications
) values (
    '8a15d219-60d9-5443-b674-7f37f24a91d7',
    'galvanized_square_steel_tube_20x20x1_5mm', 'metal', 'steel_tube',
    'Galvanized square steel tube 20 x 20 x 1.5 mm', 'lm',
    '{"material":"steel","finish":"galvanized","section":"square hollow","width_mm":20,"height_mm":20,"wall_mm":1.5}'::jsonb
)
on conflict (material_code) do update set
    department=excluded.department, category_code=excluded.category_code,
    canonical_name=excluded.canonical_name, base_unit=excluded.base_unit,
    specifications=excluded.specifications, active=true, updated_at=now();

insert into public.market_material_profiles (
    material_id, market_code, market_name, language_code,
    local_specifications, availability_status
) values (
    '8a15d219-60d9-5443-b674-7f37f24a91d7', 'IL',
    'פרופיל ברזל מגולוון 1.5×20×20 מ"מ', 'he-IL',
    '{"market":"Israel","stock_length_m":6}'::jsonb, 'common'
)
on conflict (material_id, market_code, language_code) do update set
    market_name=excluded.market_name,
    local_specifications=excluded.local_specifications,
    availability_status=excluded.availability_status,
    active=true, updated_at=now();

insert into public.market_material_offers (
    market_offer_id, material_id, market_code, source_id, supplier_name,
    supplier_sku, source_price, source_currency, source_unit, price_scope,
    included_services, delivery_included, package_quantity,
    minimum_order_quantity, vat_mode, normalized_price_ex_vat,
    normalized_unit, conversion_basis, region, valid_from, confidence, status
) values (
    '74dfbf7e-2fe7-57c0-be9c-573fcd8cad11',
    '8a15d219-60d9-5443-b674-7f37f24a91d7', 'IL',
    'de18095f-0427-5d4f-b2d2-65f37b42ead9', 'Amrusi', '1127440',
    65.80, 'ILS', 'stock_length_6m', 'material_only', '{}', false, 1, 1,
    'included', 9.293785, 'lm',
    '{"gross_stock_length_ils":65.80,"vat_rate":0.18,"stock_length_m":6,"calculation":"65.80 / 1.18 / 6","cutting":"excluded","delivery":"excluded"}'::jsonb,
    'Petah Tikva', '2026-09-28', 90, 'candidate'
)
on conflict (market_offer_id) do update set
    source_price=excluded.source_price, source_currency=excluded.source_currency,
    source_unit=excluded.source_unit, price_scope=excluded.price_scope,
    included_services=excluded.included_services,
    delivery_included=excluded.delivery_included,
    package_quantity=excluded.package_quantity,
    minimum_order_quantity=excluded.minimum_order_quantity,
    vat_mode=excluded.vat_mode,
    normalized_price_ex_vat=excluded.normalized_price_ex_vat,
    normalized_unit=excluded.normalized_unit,
    conversion_basis=excluded.conversion_basis, region=excluded.region,
    valid_from=excluded.valid_from, confidence=excluded.confidence,
    status=excluded.status;
