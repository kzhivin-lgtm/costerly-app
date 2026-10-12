-- 3.17.2.9: Israel Hardware Reference baseline classes.
--
-- These are canonical estimation endpoints, not supplier SKUs, offers or
-- claims of a verified market price. A company offer can link to one class
-- only after Price Source proves its family and, for drawer slides, nominal
-- length. Brand and Product System stay as separate source facts.
begin;

alter table public.reference_materials enable row level security;

with baseline(
    material_code, category_code, canonical_name, base_unit, material_family,
    depth_mm, global_canonical_id
) as (
    values
        ('gcm_baseline_hw_drawer_slide_250mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 250 mm', 'pair', 'drawer slide', 250, 'GCM-V1-HW-DRAWER-SLIDE-250-MM'),
        ('gcm_baseline_hw_drawer_slide_270mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 270 mm', 'pair', 'drawer slide', 270, 'GCM-V1-HW-DRAWER-SLIDE-270-MM'),
        ('gcm_baseline_hw_drawer_slide_300mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 300 mm', 'pair', 'drawer slide', 300, 'GCM-V1-HW-DRAWER-SLIDE-300-MM'),
        ('gcm_baseline_hw_drawer_slide_350mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 350 mm', 'pair', 'drawer slide', 350, 'GCM-V1-HW-DRAWER-SLIDE-350-MM'),
        ('gcm_baseline_hw_drawer_slide_400mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 400 mm', 'pair', 'drawer slide', 400, 'GCM-V1-HW-DRAWER-SLIDE-400-MM'),
        ('gcm_baseline_hw_drawer_slide_450mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 450 mm', 'pair', 'drawer slide', 450, 'GCM-V1-HW-DRAWER-SLIDE-450-MM'),
        ('gcm_baseline_hw_drawer_slide_500mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 500 mm', 'pair', 'drawer slide', 500, 'GCM-V1-HW-DRAWER-SLIDE-500-MM'),
        ('gcm_baseline_hw_drawer_slide_550mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 550 mm', 'pair', 'drawer slide', 550, 'GCM-V1-HW-DRAWER-SLIDE-550-MM'),
        ('gcm_baseline_hw_drawer_slide_600mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 600 mm', 'pair', 'drawer slide', 600, 'GCM-V1-HW-DRAWER-SLIDE-600-MM'),
        ('gcm_baseline_hw_drawer_slide_650mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 650 mm', 'pair', 'drawer slide', 650, 'GCM-V1-HW-DRAWER-SLIDE-650-MM'),
        ('gcm_baseline_hw_drawer_slide_700mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 700 mm', 'pair', 'drawer slide', 700, 'GCM-V1-HW-DRAWER-SLIDE-700-MM'),
        ('gcm_baseline_hw_drawer_slide_750mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 750 mm', 'pair', 'drawer slide', 750, 'GCM-V1-HW-DRAWER-SLIDE-750-MM'),
        ('gcm_baseline_hw_drawer_slide_800mm', 'gcm_29d089f0bcb453e68679a7c7', 'Drawer slide, 800 mm', 'pair', 'drawer slide', 800, 'GCM-V1-HW-DRAWER-SLIDE-800-MM'),
        ('gcm_baseline_hw_drawer_system', 'gcm_8834c64e562e39b2420425d4', 'Drawer system', 'set', 'drawer system', null, 'GCM-V1-HW-DRAWER-SYSTEM'),
        ('gcm_baseline_hw_hinge', 'gcm_7ef67edb2de1e5ea2aad59bd', 'Furniture hinge', 'piece', 'hinge', null, 'GCM-V1-HW-HINGE'),
        ('gcm_baseline_hw_door_closure', 'gcm_8834c64e562e39b2420425d4', 'Door closure', 'piece', 'door closure', null, 'GCM-V1-HW-DOOR-CLOSURE'),
        ('gcm_baseline_hw_mounting_part', 'gcm_8834c64e562e39b2420425d4', 'Furniture mounting part', 'piece', 'mounting plate', null, 'GCM-V1-HW-MOUNTING-PART'),
        ('gcm_baseline_hw_handle', 'gcm_8834c64e562e39b2420425d4', 'Furniture handle', 'piece', 'handle', null, 'GCM-V1-HW-HANDLE'),
        ('gcm_baseline_hw_furniture_leg', 'gcm_8834c64e562e39b2420425d4', 'Adjustable cabinet leg', 'piece', 'furniture leg', null, 'GCM-V1-HW-ADJUSTABLE-CABINET-LEG-ADJUSTABLE-CABINET-LEG'),
        ('gcm_baseline_hw_caster', 'gcm_8834c64e562e39b2420425d4', 'Furniture caster', 'piece', 'caster', null, 'GCM-V1-HW-CASTER'),
        ('gcm_baseline_hw_plinth_profile', 'gcm_8834c64e562e39b2420425d4', 'Plinth profile', 'm', 'plinth profile', null, 'GCM-V1-HW-PLINTH-PROFILE'),
        ('gcm_baseline_hw_drilling_fixture', 'gcm_8834c64e562e39b2420425d4', 'Drilling fixture', 'piece', 'drilling fixture', null, 'GCM-V1-HW-DRILLING-FIXTURE'),
        ('gcm_baseline_hw_furniture_connector', 'gcm_11e9de611e8312bd79f082cb', 'Furniture connector', 'piece', 'furniture connector', null, 'GCM-V1-HW-FURNITURE-CONNECTOR'),
        ('gcm_baseline_hw_lift_mechanism', 'gcm_8834c64e562e39b2420425d4', 'Lift mechanism', 'piece', 'lift mechanism', null, 'GCM-V1-HW-LIFT-MECHANISM')
)
insert into public.reference_materials (
    material_code, department, category_code, canonical_name, base_unit, specifications, active
)
select
    material_code,
    'hardware',
    category_code,
    canonical_name,
    base_unit,
    jsonb_strip_nulls(jsonb_build_object(
        'catalog_version', 'israel_global_catalog_v1',
        'global_canonical_id', global_canonical_id,
        'material_family', material_family,
        'depth_mm', depth_mm,
        'reference_class', 'hardware_baseline',
        'pricing_method', 'reference_class_pending_price'
    )),
    true
from baseline
on conflict (material_code) do update set
    canonical_name = excluded.canonical_name,
    base_unit = excluded.base_unit,
    specifications = excluded.specifications,
    active = true,
    updated_at = now();

commit;
