-- 3.17.1.4 Measurement spelling and conversion coverage.
-- Every row normalizes one source spelling into the canonical calculation unit.

begin;

with unit_alias_seed (unit_code, dimension_code, conversion_factor, language_code, alias_text) as ( values
    -- Length.  cm, inch and foot intentionally convert to millimetres.
    ('mm', 'length', 1, 'en', 'mm'), ('mm', 'length', 1, 'en', 'millimetre'),
    ('mm', 'length', 1, 'en', 'millimetre'), ('mm', 'length', 1, 'en', 'millimeter'),
    ('mm', 'length', 1, 'en', 'millimetres'), ('mm', 'length', 1, 'en', 'millimeters'),
    ('mm', 'length', 1, 'en', 'm.m.'), ('mm', 'length', 1, 'en', 'm/m'),
    ('mm', 'length', 1, 'ru', 'миллиметр'), ('mm', 'length', 1, 'ru', 'миллиметров'),
    ('mm', 'length', 1, 'ru', 'миллиметры'), ('mm', 'length', 1, 'ru', 'мм.'),
    ('mm', 'length', 1, 'he', 'מ"מ'), ('mm', 'length', 1, 'he', 'מ״מ'),
    ('mm', 'length', 1, 'he', 'מ מ'), ('mm', 'length', 1, 'he', 'מילימטר'),
    ('mm', 'length', 1, 'he', 'מילימטרים'),
    ('mm', 'length', 10, 'en', 'cm'), ('mm', 'length', 10, 'en', 'centimetre'),
    ('mm', 'length', 10, 'en', 'centimeter'), ('mm', 'length', 10, 'en', 'centimetres'),
    ('mm', 'length', 10, 'en', 'centimeters'), ('mm', 'length', 10, 'ru', 'см'),
    ('mm', 'length', 10, 'ru', 'сантиметр'), ('mm', 'length', 10, 'ru', 'сантиметров'),
    ('mm', 'length', 10, 'he', 'ס"מ'), ('mm', 'length', 10, 'he', 'ס״מ'),
    ('mm', 'length', 10, 'he', 'סמ'), ('mm', 'length', 10, 'he', 'סנטימטר'),
    ('mm', 'length', 25.4, 'en', 'in'), ('mm', 'length', 25.4, 'en', 'inch'),
    ('mm', 'length', 25.4, 'en', 'inches'), ('mm', 'length', 25.4, 'ru', 'дюйм'),
    ('mm', 'length', 25.4, 'ru', 'дюйма'), ('mm', 'length', 25.4, 'he', 'אינץ'),
    ('m', 'length', 1, 'en', 'm'), ('m', 'length', 1, 'en', 'lm'),
    ('m', 'length', 1, 'en', 'lin m'), ('m', 'length', 1, 'en', 'linear m'),
    ('m', 'length', 1, 'en', 'metre'), ('m', 'length', 1, 'en', 'meter'),
    ('m', 'length', 1, 'en', 'metres'), ('m', 'length', 1, 'en', 'meters'),
    ('m', 'length', 1, 'ru', 'метр'), ('m', 'length', 1, 'ru', 'метров'),
    ('m', 'length', 1, 'ru', 'пог.м'), ('m', 'length', 1, 'ru', 'погонный метр'),
    ('m', 'length', 1, 'he', 'מטרים'), ('m', 'length', 1, 'he', 'מטר רץ'),
    ('m', 'length', 0.3048, 'en', 'ft'), ('m', 'length', 0.3048, 'en', 'foot'),
    ('m', 'length', 0.3048, 'en', 'feet'), ('m', 'length', 0.3048, 'ru', 'фут'),
    ('m', 'length', 0.3048, 'he', 'רגל'),
    -- Area.
    ('sqm', 'area', 1, 'en', 'm2'), ('sqm', 'area', 1, 'en', 'm²'),
    ('sqm', 'area', 1, 'en', 'sqm'), ('sqm', 'area', 1, 'en', 'sq m'),
    ('sqm', 'area', 1, 'en', 'square metre'), ('sqm', 'area', 1, 'en', 'square meter'),
    ('sqm', 'area', 1, 'en', 'square metres'), ('sqm', 'area', 1, 'en', 'square meters'),
    ('sqm', 'area', 1, 'ru', 'кв м'), ('sqm', 'area', 1, 'ru', 'кв.м'),
    ('sqm', 'area', 1, 'ru', 'метр квадратный'), ('sqm', 'area', 1, 'ru', 'квадратный метр'),
    ('sqm', 'area', 1, 'he', 'מ"ר'), ('sqm', 'area', 1, 'he', 'מ״ר'),
    ('sqm', 'area', 1, 'he', 'מר'), ('sqm', 'area', 1, 'he', 'מטר רבוע'),
    ('sqm', 'area', 0.0001, 'en', 'cm2'), ('sqm', 'area', 0.0001, 'en', 'cm²'),
    ('sqm', 'area', 0.0001, 'ru', 'см2'), ('sqm', 'area', 0.0001, 'ru', 'см²'),
    ('sqm', 'area', 0.09290304, 'en', 'sq ft'), ('sqm', 'area', 0.09290304, 'en', 'ft2'),
    ('sqm', 'area', 0.09290304, 'en', 'ft²'), ('sqm', 'area', 0.09290304, 'ru', 'кв фут'),
    -- Mass and volume.
    ('kg', 'mass', 1, 'en', 'kg'), ('kg', 'mass', 1, 'en', 'kilogram'), ('kg', 'mass', 1, 'en', 'kilograms'),
    ('kg', 'mass', 1, 'ru', 'килограмм'), ('kg', 'mass', 1, 'ru', 'килограммов'),
    ('kg', 'mass', 1, 'he', 'ק"ג'), ('kg', 'mass', 1, 'he', 'ק״ג'),
    ('kg', 'mass', 1, 'he', 'קילוגרם'), ('kg', 'mass', 0.001, 'en', 'g'),
    ('kg', 'mass', 0.001, 'ru', 'г'), ('kg', 'mass', 0.001, 'he', 'גרם'),
    ('l', 'volume', 1, 'en', 'l'), ('l', 'volume', 1, 'en', 'litre'), ('l', 'volume', 1, 'en', 'liter'),
    ('l', 'volume', 1, 'en', 'litres'), ('l', 'volume', 1, 'en', 'liters'),
    ('l', 'volume', 1, 'ru', 'литр'), ('l', 'volume', 1, 'ru', 'литров'),
    ('l', 'volume', 1, 'he', 'ל'), ('l', 'volume', 1, 'he', 'ליטרים'),
    ('l', 'volume', 0.001, 'en', 'ml'), ('l', 'volume', 0.001, 'ru', 'мл'),
    ('l', 'volume', 0.001, 'he', 'מ"ל'), ('l', 'volume', 0.001, 'he', 'מ״ל'),
    -- Count and purchase packages.  They do not convert across one another.
    ('piece', 'count', 1, 'en', 'piece'), ('piece', 'count', 1, 'en', 'pieces'),
    ('piece', 'count', 1, 'en', 'pcs'), ('piece', 'count', 1, 'en', 'pc'), ('piece', 'count', 1, 'en', 'unit'),
    ('piece', 'count', 1, 'en', 'each'), ('piece', 'count', 1, 'en', 'ea'),
    ('piece', 'count', 1, 'ru', 'штука'), ('piece', 'count', 1, 'ru', 'штук'),
    ('piece', 'count', 1, 'ru', 'ед'), ('piece', 'count', 1, 'he', 'יח'),
    ('piece', 'count', 1, 'he', 'יחידה'),
    ('piece', 'count', 1, 'he', 'יחידות'), ('piece', 'count', 1, 'he', 'יח׳'),
    ('set', 'package', 1, 'en', 'set'), ('set', 'package', 1, 'en', 'sets'),
    ('set', 'package', 1, 'en', 'kit'), ('set', 'package', 1, 'en', 'assembly'),
    ('set', 'package', 1, 'ru', 'набор'), ('set', 'package', 1, 'ru', 'компл'),
    ('set', 'package', 1, 'he', 'סטים'), ('set', 'package', 1, 'he', 'ערכה'),
    ('sheet', 'package', 1, 'en', 'sheet'), ('sheet', 'package', 1, 'en', 'sheets'),
    ('sheet', 'package', 1, 'en', 'board'), ('sheet', 'package', 1, 'en', 'panel'),
    ('sheet', 'package', 1, 'ru', 'листов'), ('sheet', 'package', 1, 'ru', 'плита'),
    ('sheet', 'package', 1, 'he', 'גיליון'), ('sheet', 'package', 1, 'he', 'פלטה'),
    ('roll', 'package', 1, 'en', 'roll'), ('roll', 'package', 1, 'en', 'coil'), ('roll', 'package', 1, 'ru', 'катушка'),
    ('roll', 'package', 1, 'he', 'סליל'), ('pair', 'count', 1, 'en', 'pair'),
    ('pair', 'count', 1, 'ru', 'пара'), ('pair', 'count', 1, 'he', 'זוג'),
    ('box', 'package', 1, 'en', 'box'), ('box', 'package', 1, 'ru', 'коробка'),
    ('box', 'package', 1, 'he', 'קופסה'), ('pack', 'package', 1, 'en', 'pack'),
    ('pack', 'package', 1, 'en', 'package'), ('pack', 'package', 1, 'ru', 'упаковка'),
    ('pack', 'package', 1, 'he', 'חבילה')
)
insert into public.reference_measurement_unit_aliases (
    unit_code, dimension_code, conversion_factor, language_code, alias_text, alias_key, active
)
select distinct on (seed.unit_code, public.normalize_reference_material_alias(seed.alias_text))
       seed.unit_code, seed.dimension_code, seed.conversion_factor, seed.language_code,
       seed.alias_text, public.normalize_reference_material_alias(seed.alias_text), true
from unit_alias_seed seed
order by seed.unit_code, public.normalize_reference_material_alias(seed.alias_text),
         seed.language_code, seed.alias_text
on conflict (unit_code, alias_key) do update set
    dimension_code = excluded.dimension_code,
    conversion_factor = excluded.conversion_factor,
    language_code = excluded.language_code,
    active = true,
    updated_at = now();

commit;
