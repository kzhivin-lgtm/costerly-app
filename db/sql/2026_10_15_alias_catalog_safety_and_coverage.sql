-- Alias safety and coverage audit, English/Russian/Hebrew.
-- Adds only high-confidence equivalent terms. Ambiguous terms must not select
-- a Family or Pricing Key value automatically.

begin;

-- These legacy aliases lead to a value that does not exist in the same
-- Family. Keeping them active produces a deterministic but unresolvable key.
update public.reference_material_pricing_key_value_aliases
set active = false, updated_at = now()
where active and (
    (fact_field = 'metal_type' and canonical_value = 'stainless steel 304')
    or (fact_field = 'section_profile' and canonical_value in (
        'angle', 'rectangular tube', 'round tube', 'square tube'
    ))
    or (fact_field = 'species' and canonical_value in (
        'acacia', 'eucalyptus', 'fir', 'maple', 'okoume', 'olive', 'walnut'
    ))
    or (fact_field = 'coating_system' and canonical_value = 'powder coating')
);

with family_alias_seed (family_code, language_code, alias_text) as ( values
    ('acrylic_pmma', 'en', 'acrylic sheet'),
    ('acrylic_pmma', 'en', 'cast acrylic'),
    ('acrylic_pmma', 'ru', 'листовой акрил'),
    ('acrylic_pmma', 'ru', 'литой акрил'),
    ('acrylic_pmma', 'he', 'לוח אקריל'),
    ('acrylic_pmma', 'he', 'אקריל יצוק'),
    ('aluminium_composite_panel', 'en', 'aluminum composite sheet'),
    ('aluminium_composite_panel', 'ru', 'алюмокомпозит'),
    ('aluminium_composite_panel', 'he', 'פנל אלוקובונד'),
    ('compact_laminate', 'en', 'compact hpl board'),
    ('compact_laminate', 'ru', 'компакт hpl'),
    ('compact_laminate', 'he', 'לוח קומפקט hpl'),
    ('decorative_film_foil', 'en', 'finish foil'),
    ('decorative_film_foil', 'ru', 'отделочная плёнка'),
    ('decorative_film_foil', 'he', 'יריעת גמר דקורטיבית'),
    ('edge_banding', 'en', 'edge tape'),
    ('edge_banding', 'ru', 'лента для кромки'),
    ('edge_banding', 'he', 'סרט קנטים'),
    ('engineered_quartz_mineral_hybrid', 'en', 'quartz agglomerate'),
    ('engineered_quartz_mineral_hybrid', 'ru', 'кварцевый камень'),
    ('engineered_quartz_mineral_hybrid', 'he', 'אבן קוורץ'),
    ('fibreboard_hardboard', 'en', 'masonite'),
    ('fibreboard_hardboard', 'ru', 'твёрдая двп'),
    ('fibreboard_hardboard', 'he', 'לוח הארדבורד'),
    ('glass', 'en', 'float glass'),
    ('glass', 'ru', 'флоат стекло'),
    ('glass', 'he', 'זכוכית פלואט'),
    ('hpl_cpl', 'en', 'laminate sheet'),
    ('hpl_cpl', 'ru', 'листовой пластик hpl'),
    ('hpl_cpl', 'he', 'לוח פורמייקה'),
    ('lightweight_sandwich_panel', 'en', 'honeycomb board'),
    ('lightweight_sandwich_panel', 'ru', 'лёгкая сотовая плита'),
    ('lightweight_sandwich_panel', 'he', 'לוח כוורת קל'),
    ('mdf_hdf', 'en', 'medium density fibreboard'),
    ('mdf_hdf', 'ru', 'мдф лист'),
    ('mdf_hdf', 'he', 'לוח mdf'),
    ('melamine_faced_particleboard', 'en', 'melamine chipboard'),
    ('melamine_faced_particleboard', 'ru', 'лдсп плита'),
    ('melamine_faced_particleboard', 'he', 'לוח סיבית מצופה מלמין'),
    ('mirror', 'en', 'mirror sheet'),
    ('mirror', 'ru', 'листовое зеркало'),
    ('mirror', 'he', 'לוח מראה'),
    ('natural_stone_slab', 'en', 'natural stone tile slab'),
    ('natural_stone_slab', 'ru', 'слэб натурального камня'),
    ('natural_stone_slab', 'he', 'לוח אבן טבעית'),
    ('osb', 'en', 'osb board'),
    ('osb', 'ru', 'плита осб'),
    ('osb', 'he', 'לוח osb'),
    ('particleboard', 'en', 'chipboard panel'),
    ('particleboard', 'ru', 'плита дсп'),
    ('particleboard', 'he', 'לוח סיבית'),
    ('plywood', 'en', 'plywood sheet'),
    ('plywood', 'ru', 'лист фанеры'),
    ('plywood', 'he', 'לוח לביד'),
    ('plywood_special', 'en', 'specialty plywood'),
    ('plywood_special', 'ru', 'специальная фанера'),
    ('plywood_special', 'he', 'לביד ייעודי'),
    ('polycarbonate_petg_pvc_abs', 'en', 'engineering plastic sheet'),
    ('polycarbonate_petg_pvc_abs', 'ru', 'технический пластик лист'),
    ('polycarbonate_petg_pvc_abs', 'he', 'לוח פלסטיק הנדסי'),
    ('porcelain_ceramic_slab', 'en', 'porcelain tile slab'),
    ('porcelain_ceramic_slab', 'ru', 'плита керамогранита'),
    ('porcelain_ceramic_slab', 'he', 'לוח גרניט פורצלן'),
    ('sheet_metal', 'en', 'metal plate'),
    ('sheet_metal', 'ru', 'лист металла'),
    ('sheet_metal', 'he', 'פלטת מתכת'),
    ('sheet_plastic', 'en', 'plastic board'),
    ('sheet_plastic', 'ru', 'плита пластика'),
    ('sheet_plastic', 'he', 'פנל פלסטיק'),
    ('sintered_ultra_compact_surface', 'en', 'sintered slab'),
    ('sintered_ultra_compact_surface', 'ru', 'спечённая плита'),
    ('sintered_ultra_compact_surface', 'he', 'לוח אבן סינטרית'),
    ('solid_surface', 'en', 'acrylic solid surface'),
    ('solid_surface', 'ru', 'лист кориана'),
    ('solid_surface', 'he', 'משטח קוריאן'),
    ('terrazzo_engineered_agglomerate', 'en', 'terrazzo surface'),
    ('terrazzo_engineered_agglomerate', 'ru', 'терраццо плита'),
    ('terrazzo_engineered_agglomerate', 'he', 'לוח טרצו'),
    ('timber_solid_wood_panel', 'en', 'solid wood panel'),
    ('timber_solid_wood_panel', 'ru', 'щит из массива'),
    ('timber_solid_wood_panel', 'he', 'פנל עץ מלא'),
    ('vinyl_film', 'en', 'self adhesive vinyl'),
    ('vinyl_film', 'ru', 'самоклеящийся винил'),
    ('vinyl_film', 'he', 'ויניל דביק')
)
insert into public.reference_material_family_aliases (
    family_id, language_code, alias_text, alias_key, active
)
select family.family_id, seed.language_code, seed.alias_text,
       public.normalize_reference_material_alias(seed.alias_text), true
from family_alias_seed seed
join public.reference_material_families family using (family_code)
on conflict (family_id, alias_key) do update set
    language_code = excluded.language_code, alias_text = excluded.alias_text,
    active = true, updated_at = now();

with value_alias_seed (fact_field, canonical_value, language_code, alias_text) as ( values
    ('metal_type', 'brass', 'en', 'brass'),
    ('metal_type', 'brass', 'ru', 'латунь'),
    ('metal_type', 'brass', 'he', 'פליז'),
    ('metal_type', 'copper', 'en', 'copper'),
    ('metal_type', 'copper', 'ru', 'медь'),
    ('metal_type', 'copper', 'he', 'נחושת'),
    ('metal_type', 'stainless steel', 'en', 'stainless steel 304'),
    ('metal_type', 'stainless steel', 'en', '304 stainless'),
    ('metal_type', 'stainless steel', 'ru', 'нержавейка 304'),
    ('metal_type', 'stainless steel', 'he', 'נירוסטה 304'),
    ('section_profile', 'angle_30x30', 'en', '30x30 angle'),
    ('section_profile', 'angle_30x30', 'ru', 'уголок 30x30'),
    ('section_profile', 'angle_30x30', 'he', 'זווית 30x30'),
    ('section_profile', 'channel', 'en', 'u channel'),
    ('section_profile', 'channel', 'ru', 'профиль канал'),
    ('section_profile', 'channel', 'he', 'פרופיל תעלה'),
    ('section_profile', 'square_tube_20x20', 'en', '20x20 square tube'),
    ('section_profile', 'square_tube_20x20', 'ru', 'труба 20x20 квадратная'),
    ('section_profile', 'square_tube_20x20', 'he', 'צינור מרובע 20x20'),
    ('section_profile', 'rectangular_tube_40x20', 'en', '40x20 rectangular tube'),
    ('section_profile', 'rectangular_tube_40x20', 'ru', 'труба 40x20 прямоугольная'),
    ('section_profile', 'rectangular_tube_40x20', 'he', 'צינור מלבני 40x20'),
    ('section_profile', 'round_tube_d20', 'en', '20mm round tube'),
    ('section_profile', 'round_tube_d20', 'ru', 'круглая труба 20 мм'),
    ('section_profile', 'round_tube_d20', 'he', 'צינור עגול 20 ממ'),
    ('board_type', 'mdf', 'en', 'medium density fibreboard'),
    ('board_type', 'mdf', 'ru', 'мдф'),
    ('board_type', 'mdf', 'he', 'מדפ'),
    ('board_type', 'hdf', 'en', 'high density fibreboard'),
    ('board_type', 'hdf', 'ru', 'хдф'),
    ('board_type', 'hdf', 'he', 'הדפ'),
    ('surface', 'raw', 'en', 'unfinished'),
    ('surface', 'raw', 'ru', 'без покрытия'),
    ('surface', 'raw', 'he', 'ללא ציפוי'),
    ('stone_type', 'marble', 'en', 'marble'),
    ('stone_type', 'marble', 'ru', 'мрамор'),
    ('stone_type', 'marble', 'he', 'שיש'),
    ('stone_type', 'granite', 'en', 'granite'),
    ('stone_type', 'granite', 'ru', 'гранит'),
    ('stone_type', 'granite', 'he', 'גרניט'),
    ('stone_type', 'limestone', 'en', 'limestone'),
    ('stone_type', 'limestone', 'ru', 'известняк'),
    ('stone_type', 'limestone', 'he', 'אבן גיר'),
    ('stone_type', 'quartzite', 'en', 'quartzite'),
    ('stone_type', 'quartzite', 'ru', 'кварцит'),
    ('stone_type', 'quartzite', 'he', 'קוורציט'),
    ('stone_type', 'travertine', 'en', 'travertine'),
    ('stone_type', 'travertine', 'ru', 'травертин'),
    ('stone_type', 'travertine', 'he', 'טרוורטין')
)
insert into public.reference_material_pricing_key_value_aliases (
    family_id, fact_field, canonical_value, language_code, alias_text, alias_key, active
)
select family.family_id, seed.fact_field, seed.canonical_value, seed.language_code,
       seed.alias_text, public.normalize_reference_material_alias(seed.alias_text), true
from value_alias_seed seed
join public.reference_material_families family on family.active
join public.reference_material_family_pricing_policies policy
  on policy.family_id = family.family_id and policy.active
 and (
    (seed.fact_field = 'metal_type' and 'metal_type' = any(policy.pricing_key_attribute_codes))
    or (seed.fact_field = 'section_profile' and 'section_profile' = any(policy.pricing_key_attribute_codes))
    or (seed.fact_field = 'board_type' and 'board_type' = any(policy.pricing_key_attribute_codes))
    or (seed.fact_field = 'surface' and 'surface' = any(policy.pricing_key_attribute_codes))
    or (seed.fact_field = 'stone_type' and 'stone_type' = any(policy.pricing_key_attribute_codes))
 )
where exists (
    select 1
    from public.reference_material_models model
    join public.reference_material_model_attribute_values value
      on value.material_model_id = model.material_model_id
     and value.family_id = family.family_id
     and value.attribute_code = seed.fact_field
     and value.attribute_value #>> '{}' = seed.canonical_value
    where model.family_id = family.family_id and model.active
)
on conflict (family_id, fact_field, canonical_value, alias_key) do update set
    language_code = excluded.language_code, alias_text = excluded.alias_text,
    active = true, updated_at = now();

commit;
