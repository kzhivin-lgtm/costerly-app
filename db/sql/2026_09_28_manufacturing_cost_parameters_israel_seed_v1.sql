-- 3.14.1 Israel CNC / Laser parameter seed v1.
-- Public provider/manufacturer figures are reviewed. Costerly priors are
-- deliberately candidate-only and must not resolve in production until a
-- Platform Admin explicitly approves them.

with seed (
    parameter_id, calculator, parameter_key, material_family,
    thickness_min_mm, thickness_max_mm, machine_class, qualifiers,
    value_low, value_typical, value_high, unit, currency,
    source_type, source_name, source_url, source_date,
    evidence, confidence, status, notes
) as (values
    -- CNC Router, in-house. Pre-DXF priors, not claimed market facts.
    ('31410000-0000-4000-8000-000000000001'::uuid, 'cnc_router_in_house', 'effective_feed_rate_m_per_min', null, null, null, 'nested_router', '{}'::jsonb, 3, 6, 10, 'm/min', null, 'platform_prior', 'Costerly pre-DXF research synthesis', null, '2026-09-28'::date, '{"basis":"toolmaker guidance requires material, cutter and machine-specific calibration"}'::jsonb, 35, 'candidate', 'Fallback only. Company machine data overrides.'),
    ('31410000-0000-4000-8000-000000000002'::uuid, 'cnc_router_in_house', 'seconds_per_hole', null, null, null, 'nested_router', '{}'::jsonb, 2, 4, 8, 's/hole', null, 'platform_prior', 'Costerly pre-DXF research synthesis', null, '2026-09-28'::date, '{}'::jsonb, 30, 'candidate', 'Fallback only.'),
    ('31410000-0000-4000-8000-000000000003'::uuid, 'cnc_router_in_house', 'tool_change_and_non_cutting_minutes', null, null, null, 'nested_router', '{}'::jsonb, 5, 12, 25, 'min/job', null, 'platform_prior', 'Costerly pre-DXF research synthesis', null, '2026-09-28'::date, '{}'::jsonb, 35, 'candidate', 'Fallback only.'),
    ('31410000-0000-4000-8000-000000000004'::uuid, 'cnc_router_in_house', 'programming_minutes', null, null, null, 'nested_router', '{}'::jsonb, 15, 30, 90, 'min/job', null, 'platform_prior', 'Costerly pre-DXF research synthesis', null, '2026-09-28'::date, '{"complexity":"standard to custom nested job"}'::jsonb, 40, 'candidate', 'Fallback only.'),
    ('31410000-0000-4000-8000-000000000005'::uuid, 'cnc_router_in_house', 'setup_minutes', null, null, null, 'nested_router', '{}'::jsonb, 20, 35, 60, 'min/job', null, 'platform_prior', 'Costerly pre-DXF research synthesis', null, '2026-09-28'::date, '{}'::jsonb, 40, 'candidate', 'Fallback only.'),
    ('31410000-0000-4000-8000-000000000006'::uuid, 'cnc_router_in_house', 'sheet_handling_minutes', null, null, null, 'nested_router', '{}'::jsonb, 4, 7, 12, 'min/sheet', null, 'platform_prior', 'Costerly pre-DXF research synthesis', null, '2026-09-28'::date, '{}'::jsonb, 40, 'candidate', 'Fallback only.'),
    ('31410000-0000-4000-8000-000000000007'::uuid, 'cnc_router_in_house', 'machine_capacity_rate_per_hour', null, null, null, 'nested_router', '{}'::jsonb, 60, 120, 220, 'ILS/hour', 'ILS', 'platform_prior', 'Costerly capacity-cost prior', null, '2026-09-28'::date, '{"includes":"depreciation, maintenance, software and allocated floor cost"}'::jsonb, 25, 'candidate', 'Company machinery economics must override.'),
    ('31410000-0000-4000-8000-000000000008'::uuid, 'cnc_router_in_house', 'operator_attendance_fraction', null, null, null, 'nested_router', '{}'::jsonb, 0.10, 0.25, 0.50, 'ratio', null, 'platform_prior', 'Costerly pre-DXF research synthesis', null, '2026-09-28'::date, '{}'::jsonb, 35, 'candidate', 'Company workflow must override.'),
    ('31410000-0000-4000-8000-000000000009'::uuid, 'cnc_router_in_house', 'tooling_and_consumables_cost_per_machine_hour', null, null, null, 'nested_router', '{}'::jsonb, 10, 25, 50, 'ILS/hour', 'ILS', 'platform_prior', 'Costerly tooling prior', null, '2026-09-28'::date, '{}'::jsonb, 25, 'candidate', 'Company tooling history must override.'),
    ('31410000-0000-4000-8000-000000000010'::uuid, 'cnc_router_in_house', 'expected_rework_percent', null, null, null, 'nested_router', '{}'::jsonb, 2, 5, 10, '%', null, 'platform_prior', 'Costerly rework prior', null, '2026-09-28'::date, '{}'::jsonb, 20, 'candidate', 'Company quality history must override.'),

    -- CNC Router, subcontractor. Published Israeli offers.
    ('31410000-0000-4000-8000-000000000011'::uuid, 'cnc_router_subcontractor', 'dxf_cutting_service', null, null, null, null, '{"provider":"Bemida","price_basis":"file_complexity"}'::jsonb, 110, 330, 550, 'ILS/job', 'ILS', 'provider', 'Bemida CNC DXF service', 'https://mail.bemida.co.il/product/%D7%97%D7%99%D7%AA%D7%95%D7%9A-%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%A7%D7%95%D7%91%D7%A5-dxf-%D7%97%D7%99%D7%AA%D7%95%D7%9A-%D7%9E%D7%93%D7%95%D7%99%D7%A7-cnc/', '2026-09-28'::date, '{"published_range":"110-550","inclusions":"not fully specified"}'::jsonb, 60, 'reviewed', 'Do not combine with per-panel pricing.'),
    ('31410000-0000-4000-8000-000000000012'::uuid, 'cnc_router_subcontractor', 'internal_feature_charge', null, null, null, null, '{"provider":"Algolan","examples":["groove","recess","shelf_holes"]}'::jsonb, 12, 12, 12, 'ILS/part', 'ILS', 'provider', 'Algolan Express', 'https://algolan-express.co.il/', '2026-09-28'::date, '{"vat":"excluded"}'::jsonb, 80, 'reviewed', 'Charge per affected part.'),
    ('31410000-0000-4000-8000-000000000013'::uuid, 'cnc_router_subcontractor', 'edge_banding_charge', null, 17, 17, null, '{"provider":"Algolan"}'::jsonb, 6, 6, 6, 'ILS/m', 'ILS', 'provider', 'Algolan Express', 'https://algolan-express.co.il/', '2026-09-28'::date, '{"vat":"excluded"}'::jsonb, 85, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000014'::uuid, 'cnc_router_subcontractor', 'edge_banding_charge', null, 28, 28, null, '{"provider":"Algolan"}'::jsonb, 11, 11, 11, 'ILS/m', 'ILS', 'provider', 'Algolan Express', 'https://algolan-express.co.il/', '2026-09-28'::date, '{"vat":"excluded"}'::jsonb, 85, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000015'::uuid, 'cnc_router_subcontractor', 'provider_minimum', null, null, null, null, '{}'::jsonb, 110, 200, 400, 'ILS/job', 'ILS', 'platform_prior', 'Costerly subcontract minimum prior', null, '2026-09-28'::date, '{}'::jsonb, 20, 'candidate', 'No published general CNC minimum found.'),
    ('31410000-0000-4000-8000-000000000016'::uuid, 'cnc_router_subcontractor', 'file_preparation', null, null, null, null, '{}'::jsonb, 0, 100, 250, 'ILS/job', 'ILS', 'platform_prior', 'Costerly file-preparation prior', null, '2026-09-28'::date, '{}'::jsonb, 20, 'candidate', 'Use zero only for production-ready files.'),
    ('31410000-0000-4000-8000-000000000017'::uuid, 'cnc_router_subcontractor', 'allocated_delivery', null, null, null, null, '{}'::jsonb, 50, 150, 300, 'ILS/job', 'ILS', 'platform_prior', 'Costerly delivery prior', null, '2026-09-28'::date, '{}'::jsonb, 15, 'candidate', 'Company or quote data must override.'),
    ('31410000-0000-4000-8000-000000000018'::uuid, 'cnc_router_subcontractor', 'rush_surcharge_percent', null, null, null, null, '{}'::jsonb, 10, 20, 35, '%', null, 'platform_prior', 'Costerly rush prior', null, '2026-09-28'::date, '{}'::jsonb, 15, 'candidate', 'Company or quote data must override.'),

    -- Sheet Laser, in-house. Manufacturer facts plus visible priors.
    ('31410000-0000-4000-8000-000000000019'::uuid, 'sheet_laser_in_house', 'effective_cut_speed_m_per_min', null, null, null, 'fiber_laser', '{}'::jsonb, 0.5, 3, 10, 'm/min', null, 'platform_prior', 'Costerly fiber-laser prior', null, '2026-09-28'::date, '{"warning":"must be resolved by material, thickness, gas and power"}'::jsonb, 20, 'candidate', 'Generic visibility row only.'),
    ('31410000-0000-4000-8000-000000000020'::uuid, 'sheet_laser_in_house', 'pierce_seconds', null, null, null, 'fiber_laser', '{}'::jsonb, 0.2, 2, 10, 's/pierce', null, 'platform_prior', 'Costerly piercing prior', null, '2026-09-28'::date, '{}'::jsonb, 20, 'candidate', 'Must be calibrated by material and thickness.'),
    ('31410000-0000-4000-8000-000000000021'::uuid, 'sheet_laser_in_house', 'rapid_moves_and_sheet_exchange_minutes', null, null, null, 'fiber_laser', '{}'::jsonb, 2, 5, 10, 'min/sheet', null, 'platform_prior', 'Costerly handling prior', null, '2026-09-28'::date, '{}'::jsonb, 25, 'candidate', null),
    ('31410000-0000-4000-8000-000000000022'::uuid, 'sheet_laser_in_house', 'programming_and_nesting_minutes', null, null, null, 'fiber_laser', '{}'::jsonb, 20, 45, 90, 'min/job', null, 'platform_prior', 'Costerly programming prior', null, '2026-09-28'::date, '{}'::jsonb, 30, 'candidate', null),
    ('31410000-0000-4000-8000-000000000023'::uuid, 'sheet_laser_in_house', 'setup_minutes', null, null, null, 'fiber_laser', '{}'::jsonb, 20, 40, 75, 'min/job', null, 'platform_prior', 'Costerly setup prior', null, '2026-09-28'::date, '{}'::jsonb, 30, 'candidate', null),
    ('31410000-0000-4000-8000-000000000024'::uuid, 'sheet_laser_in_house', 'machine_capacity_rate_per_hour', null, null, null, 'fiber_laser', '{}'::jsonb, 100, 250, 500, 'ILS/hour', 'ILS', 'platform_prior', 'Costerly capacity-cost prior', null, '2026-09-28'::date, '{}'::jsonb, 20, 'candidate', 'Company machinery economics must override.'),
    ('31410000-0000-4000-8000-000000000025'::uuid, 'sheet_laser_in_house', 'operator_attendance_fraction', null, null, null, 'fiber_laser', '{}'::jsonb, 0.10, 0.25, 0.50, 'ratio', null, 'platform_prior', 'Costerly attendance prior', null, '2026-09-28'::date, '{}'::jsonb, 25, 'candidate', 'Company workflow must override.'),
    ('31410000-0000-4000-8000-000000000026'::uuid, 'sheet_laser_in_house', 'assist_gas_cost_per_machine_hour', null, null, null, 'fiber_laser', '{}'::jsonb, 20, 80, 250, 'ILS/hour', 'ILS', 'platform_prior', 'Costerly assist-gas prior', null, '2026-09-28'::date, '{}'::jsonb, 15, 'candidate', 'Gas contract and process must override.'),
    ('31410000-0000-4000-8000-000000000027'::uuid, 'sheet_laser_in_house', 'average_production_kw', null, null, null, 'fiber_laser', '{"manufacturer_family":"TRUMPF TruLaser 3000"}'::jsonb, 10, 16, 27, 'kW', null, 'manufacturer', 'TRUMPF TruLaser 3000 fiber', 'https://www.trumpf.com/en_GB/products/machines-systems/2d-laser-cutting-machines/trulaser-3030-fiber-3040-fiber-3060-fiber-3080-fiber/', '2026-09-28'::date, '{"published_points":{"4kW":10,"6kW":11,"9kW":14.5,"12kW":16,"24kW":27}}'::jsonb, 80, 'reviewed', 'Range summarizes published machine variants.'),
    ('31410000-0000-4000-8000-000000000028'::uuid, 'sheet_laser_in_house', 'electricity_cost_per_kwh', null, null, null, null, '{"tariff":"uniform general","effective":"2026-01-01"}'::jsonb, 0.5418, 0.5418, 0.5418, 'ILS/kWh', 'ILS', 'official', 'Israel Electricity Authority tariff book', 'https://www.gov.il/BlobFolder/generalpage/tarriffbook/he/Files_netunei_hasmal_sefer_tariff_01_2026.pdf', '2026-01-01'::date, '{"table":"1-5.3","value_agorot":54.18}'::jsonb, 85, 'reviewed', 'Company tariff overrides. Recheck after tariff updates.'),
    ('31410000-0000-4000-8000-000000000029'::uuid, 'sheet_laser_in_house', 'consumables_cost_per_machine_hour', null, null, null, 'fiber_laser', '{}'::jsonb, 15, 40, 100, 'ILS/hour', 'ILS', 'platform_prior', 'Costerly consumables prior', null, '2026-09-28'::date, '{}'::jsonb, 15, 'candidate', 'Company maintenance history must override.'),
    ('31410000-0000-4000-8000-000000000030'::uuid, 'sheet_laser_in_house', 'loading_unloading_minutes', null, null, null, 'fiber_laser', '{}'::jsonb, 4, 8, 15, 'min/sheet', null, 'platform_prior', 'Costerly loading prior', null, '2026-09-28'::date, '{}'::jsonb, 25, 'candidate', null),
    ('31410000-0000-4000-8000-000000000031'::uuid, 'sheet_laser_in_house', 'expected_rework_percent', null, null, null, 'fiber_laser', '{}'::jsonb, 1, 3, 8, '%', null, 'platform_prior', 'Costerly rework prior', null, '2026-09-28'::date, '{}'::jsonb, 15, 'candidate', 'Company quality history must override.'),

    -- Sheet Laser, subcontractor. Two models stay separate: per metre and per minute.
    ('31410000-0000-4000-8000-000000000032'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_machine_minute', 'sheet_metal', null, null, null, '{"provider_model":"Laser Portal","service":"metal cutting"}'::jsonb, 20, 30, 40, 'ILS/min', 'ILS', 'provider', 'Laser Portal', 'https://laser-p.com/%D7%9E%D7%97%D7%99%D7%A8%D7%95%D7%9F-%D7%97%D7%99%D7%AA%D7%95%D7%9A-%D7%91%D7%9C%D7%99%D7%99%D7%96%D7%A8/', '2026-09-28'::date, '{"vat":"excluded","file_preparation":"excluded"}'::jsonb, 65, 'reviewed', 'Do not average with per-metre offers.'),
    ('31410000-0000-4000-8000-000000000033'::uuid, 'sheet_laser_subcontractor', 'provider_minimum', 'sheet_metal', null, null, null, '{"provider_model":"Laser Portal"}'::jsonb, 1500, 1500, 1500, 'ILS/job', 'ILS', 'provider', 'Laser Portal', 'https://laser-p.com/%D7%9E%D7%97%D7%99%D7%A8%D7%95%D7%9F-%D7%97%D7%99%D7%AA%D7%95%D7%9A-%D7%91%D7%9C%D7%99%D7%99%D7%96%D7%A8/', '2026-09-28'::date, '{"vat":"excluded"}'::jsonb, 70, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000034'::uuid, 'sheet_laser_subcontractor', 'provider_minimum', 'sheet_metal', null, null, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 200, 300, 400, 'ILS/job', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{"wording":"typical market minimum"}'::jsonb, 55, 'reviewed', 'Market guide, not a binding provider quote.'),
    ('31410000-0000-4000-8000-000000000035'::uuid, 'sheet_laser_subcontractor', 'provider_base_charge', null, null, null, null, '{}'::jsonb, 0, 0, 0, 'ILS/job', 'ILS', 'platform_prior', 'Costerly composition rule', null, '2026-09-28'::date, '{"rule":"derive from selected provider model; do not add a second base charge"}'::jsonb, 50, 'candidate', 'Zero prevents double counting when metre or minute model is selected.'),
    ('31410000-0000-4000-8000-000000000036'::uuid, 'sheet_laser_subcontractor', 'provider_setup', null, null, null, null, '{}'::jsonb, 0, 100, 300, 'ILS/job', 'ILS', 'platform_prior', 'Costerly setup prior', null, '2026-09-28'::date, '{}'::jsonb, 15, 'candidate', 'Quote data must override.'),
    ('31410000-0000-4000-8000-000000000037'::uuid, 'sheet_laser_subcontractor', 'file_preparation', null, null, null, null, '{}'::jsonb, 0, 150, 450, 'ILS/job', 'ILS', 'platform_prior', 'Costerly file-preparation prior', null, '2026-09-28'::date, '{"market_evidence":"Laser Portal explicitly excludes file preparation"}'::jsonb, 20, 'candidate', 'Use zero only for production-ready files.'),
    ('31410000-0000-4000-8000-000000000038'::uuid, 'sheet_laser_subcontractor', 'secondary_operations', null, null, null, null, '{}'::jsonb, 0, 200, 800, 'ILS/job', 'ILS', 'platform_prior', 'Costerly secondary-operation prior', null, '2026-09-28'::date, '{}'::jsonb, 10, 'candidate', 'Must be replaced by operation-specific data.'),
    ('31410000-0000-4000-8000-000000000039'::uuid, 'sheet_laser_subcontractor', 'allocated_delivery', null, null, null, null, '{}'::jsonb, 80, 200, 450, 'ILS/job', 'ILS', 'platform_prior', 'Costerly delivery prior', null, '2026-09-28'::date, '{}'::jsonb, 10, 'candidate', 'Company or quote data must override.'),
    ('31410000-0000-4000-8000-000000000040'::uuid, 'sheet_laser_subcontractor', 'rush_surcharge_percent', null, null, null, null, '{}'::jsonb, 10, 25, 50, '%', null, 'platform_prior', 'Costerly rush prior', null, '2026-09-28'::date, '{}'::jsonb, 10, 'candidate', 'Company or quote data must override.'),

    -- Iron Laser per-metre curves, material usually included but must be confirmed per quote.
    ('31410000-0000-4000-8000-000000000041'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'carbon_steel', 1, 3, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 8, 10, 12, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{"material_usually_included":true}'::jsonb, 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000042'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'carbon_steel', 4, 6, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 12, 15, 18, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000043'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'carbon_steel', 8, 10, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 18, 21.5, 25, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000044'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'carbon_steel', 12, 20, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 25, 32.5, 40, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000045'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'stainless_steel', 1, 3, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 12, 15, 18, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000046'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'stainless_steel', 4, 6, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 18, 23, 28, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000047'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'stainless_steel', 8, 10, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 28, 34, 40, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000048'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'stainless_steel', 12, 20, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 40, 50, 60, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000049'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'aluminum', 1, 3, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 15, 18.5, 22, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000050'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'aluminum', 4, 6, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 22, 27, 32, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000051'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'aluminum', 8, 10, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 32, 38.5, 45, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null),
    ('31410000-0000-4000-8000-000000000052'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_meter', 'aluminum', 12, 15, null, '{"provider_model":"Iron Laser market guide"}'::jsonb, 45, 55, 65, 'ILS/m', 'ILS', 'provider', 'Iron Laser Israel price guide', 'https://iron-laser.co.il/laser-metal-cutting-price-guide-israel/', '2026-09-28'::date, '{}', 60, 'reviewed', null)
),
panel_prices (parameter_id, material_family, thickness_mm, price_ils, qualifiers) as (values
    ('31410000-0000-4000-8000-000000000053'::uuid, 'drawer_melamine', 15.5, 210, '{"finish":"white grey graphite"}'::jsonb),
    ('31410000-0000-4000-8000-000000000054'::uuid, 'melamine_white', 17, 220, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000055'::uuid, 'melamine_colored', 17, 240, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000056'::uuid, 'melamine_white', 28, 310, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000057'::uuid, 'melamine_colored', 28, 340, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000058'::uuid, 'plywood_exposed', 17, 210, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000059'::uuid, 'plywood_white_formica_two_sided', 17, 270, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000060'::uuid, 'plywood_decorative', 17, 280, '{"finish":"grey graphite linen oak"}'::jsonb),
    ('31410000-0000-4000-8000-000000000061'::uuid, 'birch_plywood', 4, 170, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000062'::uuid, 'birch_plywood', 6, 190, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000063'::uuid, 'birch_plywood', 12, 230, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000064'::uuid, 'birch_plywood', 16, 260, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000065'::uuid, 'birch_plywood', 18, 280, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000066'::uuid, 'birch_plywood', 21, 330, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000067'::uuid, 'birch_plywood', 24, 360, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000068'::uuid, 'birch_plywood', 27, 390, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000069'::uuid, 'birch_plywood', 30, 450, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000070'::uuid, 'backing_plywood_white', 5, 130, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000071'::uuid, 'backing_plywood_decorative', 5, 140, '{"finish":"grey graphite linen oak"}'::jsonb),
    ('31410000-0000-4000-8000-000000000072'::uuid, 'oak_butcher_block', 18, 900, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000073'::uuid, 'oak_butcher_block', 26, 1200, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000074'::uuid, 'oak_laminated_panel', 19, 1800, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000075'::uuid, 'green_mdf', 17, 210, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000076'::uuid, 'green_mdf', 19, 230, '{}'::jsonb),
    ('31410000-0000-4000-8000-000000000077'::uuid, 'green_mdf', 22, 310, '{}'::jsonb)
),
all_seed as (
    select * from seed
    union all
    select
        parameter_id, 'cnc_router_subcontractor', 'bundled_panel_service', material_family,
        thickness_mm, thickness_mm, null::text,
        qualifiers || '{"provider":"Algolan","includes_material":true,"includes_cutting":true}'::jsonb,
        price_ils, price_ils, price_ils, 'ILS/panel', 'ILS',
        'provider', 'Algolan Express', 'https://algolan-express.co.il/', '2026-09-28'::date,
        '{"vat":"excluded"}'::jsonb, 80::numeric, 'reviewed', 'Published per-panel service price.'
    from panel_prices
)
insert into public.manufacturing_cost_parameters (
    parameter_id, calculator, parameter_key, country_code, material_family,
    thickness_min_mm, thickness_max_mm, machine_class, qualifiers,
    value_low, value_typical, value_high, unit, currency,
    source_type, source_name, source_url, source_date,
    evidence, confidence, status, version, effective_from, notes
)
select
    parameter_id, calculator, parameter_key, 'IL', material_family,
    thickness_min_mm, thickness_max_mm, machine_class, qualifiers,
    value_low, value_typical, value_high, unit, currency,
    source_type, source_name, source_url, source_date,
    evidence, confidence, status, 1, '2026-09-28'::date, notes
from all_seed
on conflict (parameter_id) do update set
    material_family = excluded.material_family,
    thickness_min_mm = excluded.thickness_min_mm,
    thickness_max_mm = excluded.thickness_max_mm,
    machine_class = excluded.machine_class,
    qualifiers = excluded.qualifiers,
    value_low = excluded.value_low,
    value_typical = excluded.value_typical,
    value_high = excluded.value_high,
    unit = excluded.unit,
    currency = excluded.currency,
    source_type = excluded.source_type,
    source_name = excluded.source_name,
    source_url = excluded.source_url,
    source_date = excluded.source_date,
    evidence = excluded.evidence,
    confidence = excluded.confidence,
    status = excluded.status,
    notes = excluded.notes
where manufacturing_cost_parameters.status in ('candidate', 'reviewed');
