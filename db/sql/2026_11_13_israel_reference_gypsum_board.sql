-- Catalog price for a standard indoor gypsum board, excluding paint and labor.
begin;

do $$
declare
    family_key uuid;
    model_key uuid;
    listing_key uuid;
    legacy_key uuid;
    version_key text;
    source_key constant uuid := '16ef3735-9e48-491a-808d-1954433eae8a';
    price_key constant uuid := 'f5d45b40-cda7-44a2-9ca7-1a8b2e75d213';
    source_url constant text := 'https://www.mgeves.co.il/לוח_גבס_לבן_260';
    unit_price constant numeric := round(52::numeric / 1.18, 6);
    catalog_date constant date := date '2026-11-13';
begin
    select catalog_version into strict version_key
    from public.reference_catalog_versions where market_code = 'IL' and status = 'active';

    insert into public.reference_material_families (family_code, family_name, entity_role_code)
    values ('gypsum_board', 'Gypsum board', 'material') on conflict (family_code) do nothing;
    select family_id into strict family_key from public.reference_material_families
    where family_code = 'gypsum_board' and active;

    insert into public.reference_material_family_attributes
        (family_id, attribute_code, attribute_name, attribute_role, value_type, required)
    values (family_key, 'thickness', 'Thickness in millimetres', 'primary', 'number', true)
    on conflict (family_id, attribute_code) do nothing;

    insert into public.reference_material_family_pricing_policies
        (family_id, pricing_key_attribute_codes, purchase_format_policy)
    values (family_key, array['thickness'], 'required') on conflict (family_id) do nothing;

    insert into public.reference_material_family_aliases (family_id, language_code, alias_text, alias_key)
    select family_key, language_code, label, public.normalize_reference_material_alias(label)
    from (values ('en', 'drywall'), ('en', 'gypsum board'), ('en', 'plasterboard'),
                 ('ru', 'гипсокартон'), ('he', 'לוח גבס')) aliases(language_code, label)
    on conflict (family_id, alias_key) do nothing;

    insert into public.reference_material_models (family_id, material_model_code, canonical_name)
    values (family_key, 'gypsum_board_standard_12_5_mm', 'Gypsum board, 12.5 mm, standard indoor')
    on conflict (material_model_code) do nothing;
    select material_model_id into strict model_key from public.reference_material_models
    where material_model_code = 'gypsum_board_standard_12_5_mm' and family_id = family_key and active;

    insert into public.reference_material_model_attribute_values
        (material_model_id, family_id, attribute_code, attribute_value)
    values (model_key, family_key, 'thickness', '12.5'::jsonb)
    on conflict (material_model_id, attribute_code) do nothing;

    insert into public.reference_market_material_listings
        (market_code, material_model_id, listing_code, canonical_market_name, availability_status)
    values ('IL', model_key, 'gypsum_board_standard_12_5_mm', 'Gypsum board, 12.5 mm, standard indoor', 'common')
    on conflict (market_code, material_model_id) do nothing;
    select market_material_listing_id into strict listing_key from public.reference_market_material_listings
    where market_code = 'IL' and material_model_id = model_key and active;

    insert into public.reference_market_material_supply_formats
        (market_material_listing_id, supply_format_code, purchase_unit, purchasable_dimensions)
    values (listing_key, 'sheet_2600x1200', 'sheet',
            '{"length_mm":2600,"width_mm":1200,"format_source":"supplier_listing"}'::jsonb)
    on conflict (market_material_listing_id, supply_format_code) do nothing;

    insert into public.reference_material_categories (category_code, category_name, department)
    values ('gypsum_board', 'Gypsum board', 'glass_stone_plastic') on conflict (category_code) do nothing;
    insert into public.reference_materials
        (material_code, department, category_code, canonical_name, base_unit, specifications)
    values ('gypsum_board_standard_12_5_mm', 'glass_stone_plastic', 'gypsum_board',
            'Gypsum board, 12.5 mm, standard indoor', 'sheet', '{"thickness_mm":12.5}'::jsonb)
    on conflict (material_code) do nothing;
    select material_id into strict legacy_key from public.reference_materials
    where material_code = 'gypsum_board_standard_12_5_mm' and active;

    insert into public.reference_market_material_legacy_mappings
        (legacy_material_id, market_code, family_id, material_model_id, market_material_listing_id,
         classification_status, classification_basis)
    values (legacy_key, 'IL', family_key, model_key, listing_key, 'mapped', 'catalog_seed')
    on conflict (legacy_material_id) do nothing;

    insert into public.reference_sources
        (source_id, market_code, source_type, source_channel, source_name, source_url, source_date, language_code, evidence)
    values (source_key, 'IL', 'supplier', 'specialist_retailer', 'Merkaz HaGeves, ORBOND Knauf white board',
            source_url, catalog_date, 'he',
            '{"sku":"120260","price_with_vat_ils":52,"vat_rate":0.18,"unit":"sheet","length_mm":2600,"width_mm":1200}'::jsonb)
    on conflict (source_id) do nothing;

    insert into public.market_material_model_prices
        (model_price_id, material_id, market_code, catalog_version, price_low, price_typical, price_high,
         unit, currency, price_scope, pricing_method, confidence, anchor_count, formula_description,
         model_metadata, effective_from, status)
    values (price_key, legacy_key, 'IL', version_key, unit_price, unit_price, unit_price, 'sheet', 'ILS',
            'material_only', 'derived_from_israel_anchor', 80, 1, 'Published ILS 52 per sheet, divided by 1.18.',
            jsonb_build_object('source_id', source_key, 'source_url', source_url, 'supplier_sku', '120260',
                               'published_price_with_vat_ils', 52, 'vat_rate', 0.18), catalog_date, 'active')
    on conflict (model_price_id) do nothing;

    insert into public.reference_material_family_default_variants
        (family_id, reference_position_id, default_specifications, applicability_specifications, priority, active)
    values (family_key, model_key, '{"thickness":12.5}'::jsonb, '{}'::jsonb, 10, true)
    on conflict (family_id, priority) do nothing;
end;
$$;

commit;
