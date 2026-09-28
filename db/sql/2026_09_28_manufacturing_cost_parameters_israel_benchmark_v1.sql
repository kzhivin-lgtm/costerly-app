-- 3.14.1 Israel CNC subcontractor benchmark v1.
-- Keeps provider observations separate and adds a normalized Costerly market
-- benchmark only where published material, thickness and inclusion scope match.

with seed (
    parameter_id, material_family, thickness_mm, qualifiers,
    value_low, value_typical, value_high, unit,
    source_type, source_name, source_url, evidence, confidence, notes
) as (values
    -- Alfandari observations, prices exclude VAT and include cutting.
    ('31411000-0000-4000-8000-000000000001'::uuid, 'melamine_white', 17, '{"provider":"Alfandari","sheet_mm":"1220x2440"}'::jsonb, 225, 225, 225, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000002'::uuid, 'melamine_colored', 17, '{"provider":"Alfandari","sheet_mm":"1220x2440"}'::jsonb, 245, 245, 245, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000003'::uuid, 'melamine_white', 28, '{"provider":"Alfandari","sheet_mm":"1220x2440"}'::jsonb, 325, 325, 325, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000004'::uuid, 'melamine_colored', 28, '{"provider":"Alfandari","sheet_mm":"1220x2440"}'::jsonb, 345, 345, 345, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000005'::uuid, 'plywood_exposed', 17, '{"provider":"Alfandari"}'::jsonb, 220, 220, 220, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 80, null),
    ('31411000-0000-4000-8000-000000000006'::uuid, 'plywood_white_formica_two_sided', 17, '{"provider":"Alfandari"}'::jsonb, 325, 325, 325, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 80, null),
    ('31411000-0000-4000-8000-000000000007'::uuid, 'backing_plywood_white', 5, '{"provider":"Alfandari"}'::jsonb, 145, 145, 145, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 80, null),
    ('31411000-0000-4000-8000-000000000008'::uuid, 'pine_panel', 18, '{"provider":"Alfandari","sheet_mm":"1220x2440"}'::jsonb, 475, 475, 475, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 80, null),
    ('31411000-0000-4000-8000-000000000009'::uuid, 'pine_panel', 28, '{"provider":"Alfandari"}'::jsonb, 575, 575, 575, 'ILS/panel', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 75, null),
    ('31411000-0000-4000-8000-000000000010'::uuid, null, 17, '{"provider":"Alfandari","edge":"PVC 1.3 mm"}'::jsonb, 7.5, 7.5, 7.5, 'ILS/m', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded"}'::jsonb, 85, 'Edge-banding observation.'),
    ('31411000-0000-4000-8000-000000000011'::uuid, null, 28, '{"provider":"Alfandari","edge":"PVC 1.3 mm"}'::jsonb, 12.5, 12.5, 12.5, 'ILS/m', 'provider', 'Alfandari', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"vat":"excluded"}'::jsonb, 85, 'Edge-banding observation.'),

    -- Egoz observations, prices exclude VAT. Birch rows are deliberately omitted because cutting is excluded.
    ('31411000-0000-4000-8000-000000000012'::uuid, 'melamine_white', 17, '{"provider":"Egoz","sheet_mm":"1220x2440","maximum_parts":8}'::jsonb, 250, 250, 250, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000013'::uuid, 'melamine_colored', 17, '{"provider":"Egoz","sheet_mm":"1220x2440","maximum_parts":8}'::jsonb, 280, 280, 280, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000014'::uuid, 'melamine_white', 28, '{"provider":"Egoz","sheet_mm":"1220x2440","maximum_parts":8}'::jsonb, 290, 290, 290, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000015'::uuid, 'melamine_colored', 28, '{"provider":"Egoz","sheet_mm":"1220x2440","maximum_parts":8}'::jsonb, 310, 310, 310, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000016'::uuid, 'plywood_exposed', 17, '{"provider":"Egoz","sheet_mm":"1220x2440","maximum_parts":8}'::jsonb, 190, 190, 190, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000017'::uuid, 'plywood_white_formica_two_sided', 17, '{"provider":"Egoz","sheet_mm":"1220x2440","maximum_parts":8}'::jsonb, 290, 290, 290, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 80, null),
    ('31411000-0000-4000-8000-000000000018'::uuid, 'backing_plywood_white', 5, '{"provider":"Egoz","sheet_mm":"1220x2440","maximum_parts":8}'::jsonb, 110, 110, 110, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000019'::uuid, 'pine_panel', 18, '{"provider":"Egoz","sheet_mm":"1220x2440","maximum_parts":8}'::jsonb, 450, 450, 450, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 85, null),
    ('31411000-0000-4000-8000-000000000020'::uuid, 'pine_panel', 28, '{"provider":"Egoz","maximum_parts":8}'::jsonb, 550, 550, 550, 'ILS/panel', 'provider', 'Egoz Wood', 'https://www.egozwood.co.il/%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D/%D7%A4%D7%9C%D7%98%D7%95%D7%AA-%D7%A2%D7%A5-%D7%9C%D7%A4%D7%99-%D7%9E%D7%99%D7%93%D7%94', '{"vat":"excluded","includes_material":true,"includes_cutting":true,"cut_scope":"rectangular parts"}'::jsonb, 80, null),

    -- Normalized Israeli market benchmarks. Typical is the median when three comparable observations exist.
    ('31411000-0000-4000-8000-000000000021'::uuid, 'melamine_white', 17, '{"benchmark":"costerly_israel_v1","observations":3}'::jsonb, 220, 225, 250, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari","Egoz"],"method":"min, median, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 80, 'Three close observations.'),
    ('31411000-0000-4000-8000-000000000022'::uuid, 'melamine_colored', 17, '{"benchmark":"costerly_israel_v1","observations":3}'::jsonb, 240, 245, 280, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari","Egoz"],"method":"min, median, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 80, 'Three close observations.'),
    ('31411000-0000-4000-8000-000000000023'::uuid, 'melamine_white', 28, '{"benchmark":"costerly_israel_v1","observations":3}'::jsonb, 290, 310, 325, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari","Egoz"],"method":"min, median, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 80, 'Three close observations.'),
    ('31411000-0000-4000-8000-000000000024'::uuid, 'melamine_colored', 28, '{"benchmark":"costerly_israel_v1","observations":3}'::jsonb, 310, 340, 345, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari","Egoz"],"method":"min, median, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 80, 'Three close observations.'),
    ('31411000-0000-4000-8000-000000000025'::uuid, 'plywood_exposed', 17, '{"benchmark":"costerly_israel_v1","observations":3}'::jsonb, 190, 210, 220, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari","Egoz"],"method":"min, median, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 75, 'Provider terminology is not fully standardized.'),
    ('31411000-0000-4000-8000-000000000026'::uuid, 'plywood_white_formica_two_sided', 17, '{"benchmark":"costerly_israel_v1","observations":3}'::jsonb, 270, 290, 325, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari","Egoz"],"method":"min, median, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 65, 'Surface descriptions require later invoice calibration.'),
    ('31411000-0000-4000-8000-000000000027'::uuid, 'backing_plywood_white', 5, '{"benchmark":"costerly_israel_v1","observations":3}'::jsonb, 110, 130, 145, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari","Egoz"],"method":"min, median, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 75, null),
    ('31411000-0000-4000-8000-000000000028'::uuid, 'pine_panel', 18, '{"benchmark":"costerly_israel_v1","observations":2}'::jsonb, 450, 462.5, 475, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"sources":["Alfandari","Egoz"],"method":"min, midpoint, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 65, 'Two observations.'),
    ('31411000-0000-4000-8000-000000000029'::uuid, 'pine_panel', 28, '{"benchmark":"costerly_israel_v1","observations":2}'::jsonb, 550, 562.5, 575, 'ILS/panel', 'research', 'Costerly Israel benchmark v1', 'https://alfandari.biz/%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%9D/', '{"sources":["Alfandari","Egoz"],"method":"min, midpoint, max","vat":"excluded","includes_material":true,"includes_cutting":true}'::jsonb, 60, 'Sheet dimensions are not stated by both sources.'),
    ('31411000-0000-4000-8000-000000000030'::uuid, null, 17, '{"benchmark":"costerly_israel_v1","observations":2,"edge":"PVC"}'::jsonb, 6, 6.75, 7.5, 'ILS/m', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari"],"method":"min, midpoint, max","vat":"excluded"}'::jsonb, 70, 'Edge-banding benchmark.'),
    ('31411000-0000-4000-8000-000000000031'::uuid, null, 28, '{"benchmark":"costerly_israel_v1","observations":2,"edge":"PVC"}'::jsonb, 11, 11.75, 12.5, 'ILS/m', 'research', 'Costerly Israel benchmark v1', 'https://algolan-express.co.il/', '{"sources":["Algolan","Alfandari"],"method":"min, midpoint, max","vat":"excluded"}'::jsonb, 70, 'Edge-banding benchmark.')
)
insert into public.manufacturing_cost_parameters (
    parameter_id, calculator, parameter_key, country_code, material_family,
    thickness_min_mm, thickness_max_mm, qualifiers,
    value_low, value_typical, value_high, unit, currency,
    source_type, source_name, source_url, source_date, evidence,
    confidence, status, version, effective_from, notes
)
select
    parameter_id, 'cnc_router_subcontractor',
    case when unit = 'ILS/m' then 'edge_banding_charge' else 'bundled_panel_service' end,
    'IL', material_family, thickness_mm, thickness_mm, qualifiers,
    value_low, value_typical, value_high, unit, 'ILS',
    source_type, source_name, source_url, '2026-09-28'::date, evidence,
    confidence, 'reviewed', 1, '2026-09-28'::date, notes
from seed
on conflict (parameter_id) do update set
    material_family = excluded.material_family,
    thickness_min_mm = excluded.thickness_min_mm,
    thickness_max_mm = excluded.thickness_max_mm,
    qualifiers = excluded.qualifiers,
    value_low = excluded.value_low,
    value_typical = excluded.value_typical,
    value_high = excluded.value_high,
    source_type = excluded.source_type,
    source_name = excluded.source_name,
    source_url = excluded.source_url,
    evidence = excluded.evidence,
    confidence = excluded.confidence,
    notes = excluded.notes
where manufacturing_cost_parameters.status = 'reviewed';
