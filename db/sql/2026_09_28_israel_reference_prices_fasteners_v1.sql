-- 3.15.1 Israel Reference Catalog v1, fasteners batch 1.
-- Retrieved 2026-09-28. Amrusi terms state prices include VAT and delivery is extra.

insert into public.reference_sources(source_id,market_code,source_type,source_name,source_url,source_date,language_code,region,evidence) values
('fc899f11-c362-507b-9fc4-4b6d9eff6531','IL','retailer','Amrusi wood screws','https://www.amrusi.co.il/%D7%91%D7%A8%D7%92%D7%99-%D7%A2%D7%A5','2026-09-28','he-IL',null,'{"date_basis":"retrieved","selected_variant":"3x20 mm","package_quantity":100}'::jsonb),
('a4407873-f066-52c0-a6fd-aff6693f97cb','IL','retailer','Amrusi site regulations','https://www.amrusi.co.il/terms','2026-09-28','he-IL',null,'{"date_basis":"retrieved","vat_statement":"prices include VAT","delivery":"extra"}'::jsonb)
on conflict(source_id) do update set source_name=excluded.source_name,source_url=excluded.source_url,source_date=excluded.source_date,language_code=excluded.language_code,region=excluded.region,evidence=excluded.evidence,retrieved_at=now();

insert into public.reference_materials(material_id,material_code,department,category_code,canonical_name,base_unit,specifications) values
('1cc756b6-c58e-590b-97fa-dbac4fe817f9','chipboard_screw_3x20mm','hardware','screw_bolt','Chipboard screw 3 x 20 mm','ea','{"diameter_mm":3,"length_mm":20}'::jsonb)
on conflict(material_code) do update set department=excluded.department,category_code=excluded.category_code,canonical_name=excluded.canonical_name,base_unit=excluded.base_unit,specifications=excluded.specifications,active=true,updated_at=now();

insert into public.market_material_profiles(material_id,market_code,market_name,language_code,local_specifications,availability_status)
select material_id,'IL','בורג סיבית 3×20 מ״מ','he-IL','{"market":"Israel"}'::jsonb,'common' from public.reference_materials where material_code='chipboard_screw_3x20mm'
on conflict(material_id,market_code,language_code) do update set market_name=excluded.market_name,local_specifications=excluded.local_specifications,availability_status=excluded.availability_status,active=true,updated_at=now();

insert into public.market_material_offers(market_offer_id,material_id,market_code,source_id,supplier_name,supplier_sku,source_price,source_currency,source_unit,price_scope,included_services,delivery_included,package_quantity,minimum_order_quantity,vat_mode,normalized_price_ex_vat,normalized_unit,conversion_basis,region,valid_from,confidence,status) values
('432f640d-37d9-549c-bbce-d4592e889a6c','1cc756b6-c58e-590b-97fa-dbac4fe817f9','IL','fc899f11-c362-507b-9fc4-4b6d9eff6531','Amrusi','1011163',13.70,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.116102,'ea','{"calculation":"13.70 / 1.18 / 100","vat_evidence_source_id":"a4407873-f066-52c0-a6fd-aff6693f97cb"}'::jsonb,null,'2026-09-28',88,'candidate')
on conflict(market_offer_id) do update set source_price=excluded.source_price,source_currency=excluded.source_currency,source_unit=excluded.source_unit,price_scope=excluded.price_scope,included_services=excluded.included_services,delivery_included=excluded.delivery_included,package_quantity=excluded.package_quantity,minimum_order_quantity=excluded.minimum_order_quantity,vat_mode=excluded.vat_mode,normalized_price_ex_vat=excluded.normalized_price_ex_vat,normalized_unit=excluded.normalized_unit,conversion_basis=excluded.conversion_basis,region=excluded.region,valid_from=excluded.valid_from,confidence=excluded.confidence,status=excluded.status;
