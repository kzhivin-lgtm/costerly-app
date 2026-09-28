-- 3.14.1 Israel in-house operating benchmarks and laser service benchmark.
-- Labor values are loaded employer-cost fallbacks derived from public gross
-- salary ranges. Company labor and machinery settings always take precedence.

with seed (
    parameter_id, calculator, parameter_key, machine_class, qualifiers,
    value_low, value_typical, value_high, unit, currency,
    source_type, source_name, source_url, evidence, confidence, notes
) as (values
    ('31412000-0000-4000-8000-000000000001'::uuid, 'cnc_router_in_house', 'operator_rate_per_hour', 'nested_router', '{}'::jsonb, 62, 88, 122, 'ILS/hour', 'ILS', 'research', 'Israel CNC operator labor benchmark', 'https://work.co.il/professions/cnc-operator/', '{"gross_monthly_ils":[9400,12500,16400],"monthly_hours":182,"employer_load_factors":[1.20,1.28,1.35],"method":"gross salary converted to loaded hourly employer cost"}'::jsonb, 65, 'Fallback only. Company labor profile overrides.'),
    ('31412000-0000-4000-8000-000000000002'::uuid, 'cnc_router_in_house', 'programmer_rate_per_hour', 'nested_router', '{}'::jsonb, 70, 100, 135, 'ILS/hour', 'ILS', 'research', 'Israel CNC setter and programmer labor benchmark', 'https://work.co.il/professions/cnc-setter/', '{"setter_gross_monthly_ils":[10200,13500,17400],"monthly_hours":182,"employer_load_included":true,"cross_check":"experienced setters advertised at 70 ILS/hour and above"}'::jsonb, 55, 'Fallback only. Company labor profile overrides.'),
    ('31412000-0000-4000-8000-000000000003'::uuid, 'cnc_router_in_house', 'machine_capacity_rate_per_hour', 'nested_router', '{}'::jsonb, 15, 45, 120, 'ILS/hour', 'ILS', 'research', 'Israel professional CNC capacity benchmark', 'https://www.fritech.co.il/cnc-in-israel-how-much-does-it-cost/', '{"new_machine_ils":[80000,200000,350000],"economic_life_years":7,"productive_hours_per_year":[1600,1200,800],"maintenance_and_software_included":true,"method":"annual ownership cost divided by practical productive hours"}'::jsonb, 50, 'Excludes operator labor, energy and tooling. Company machine rate overrides.'),
    ('31412000-0000-4000-8000-000000000004'::uuid, 'sheet_laser_in_house', 'operator_rate_per_hour', 'fiber_laser', '{}'::jsonb, 62, 88, 122, 'ILS/hour', 'ILS', 'research', 'Israel CNC machine-operator labor benchmark', 'https://work.co.il/professions/cnc-operator/', '{"gross_monthly_ils":[9400,12500,16400],"monthly_hours":182,"employer_load_factors":[1.20,1.28,1.35],"method":"gross salary converted to loaded hourly employer cost"}'::jsonb, 55, 'Fallback for laser-machine operator. Company labor profile overrides.'),
    ('31412000-0000-4000-8000-000000000005'::uuid, 'sheet_laser_in_house', 'programmer_rate_per_hour', 'fiber_laser', '{}'::jsonb, 70, 100, 135, 'ILS/hour', 'ILS', 'research', 'Israel CNC setter and programmer labor benchmark', 'https://work.co.il/professions/cnc-setter/', '{"setter_gross_monthly_ils":[10200,13500,17400],"monthly_hours":182,"employer_load_included":true}'::jsonb, 45, 'Fallback for laser programming and nesting. Company labor profile overrides.'),
    ('31412000-0000-4000-8000-000000000006'::uuid, 'sheet_laser_in_house', 'machine_capacity_rate_per_hour', 'fiber_laser', '{}'::jsonb, 40, 180, 500, 'ILS/hour', 'ILS', 'research', 'Israel fiber-laser capacity benchmark', 'https://www.fritech.co.il/product/l1530-fiber/', '{"published_entry_machine_ils":149000,"method":"ownership-cost range across entry and industrial utilization scenarios","warning":"upper industrial equipment cost is not publicly quoted"}'::jsonb, 30, 'Excludes labor, electricity, assist gas and consumables. Company machine rate overrides.'),
    ('31412000-0000-4000-8000-000000000007'::uuid, 'sheet_laser_subcontractor', 'cut_charge_per_machine_minute', null, '{}'::jsonb, 15, 20, 40, 'ILS/min', 'ILS', 'research', 'Costerly Israel laser-minute benchmark v1', 'https://xn--9dbli2cc.com/services/laser-cutting-metal', '{"observations":[15,20,"20-40"],"sources":["Israel Steel Center content benchmark","Laser Portal"],"method":"observed floor, central corroborated value, published upper bound","file_preparation":"excluded or additional"}'::jsonb, 50, 'Directional fallback. Material and thickness-specific per-metre rates take precedence when available.')
)
insert into public.manufacturing_cost_parameters (
    parameter_id, calculator, parameter_key, country_code, machine_class,
    qualifiers, value_low, value_typical, value_high, unit, currency,
    source_type, source_name, source_url, source_date, evidence,
    confidence, status, version, effective_from, notes
)
select
    parameter_id, calculator, parameter_key, 'IL', machine_class,
    qualifiers, value_low, value_typical, value_high, unit, currency,
    source_type, source_name, source_url, '2026-09-28'::date, evidence,
    confidence, 'reviewed', 1, '2026-09-28'::date, notes
from seed
on conflict (parameter_id) do update set
    machine_class = excluded.machine_class,
    qualifiers = excluded.qualifiers,
    value_low = excluded.value_low,
    value_typical = excluded.value_typical,
    value_high = excluded.value_high,
    source_name = excluded.source_name,
    source_url = excluded.source_url,
    evidence = excluded.evidence,
    confidence = excluded.confidence,
    notes = excluded.notes
where manufacturing_cost_parameters.status = 'reviewed';
