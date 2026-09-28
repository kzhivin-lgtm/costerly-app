-- 3.15.1 Israel Reference Catalog v1, fasteners batch 3.
-- Retrieved 2026-09-28. Pre-cut dowels, dowel rods and handle screws remain
-- separate identities because their purchasing units and required labor differ.

insert into public.reference_sources(source_id,market_code,source_type,source_channel,source_name,source_url,source_date,language_code,region,evidence) values
('b4c553ba-6638-53e8-8b69-900facf312f7','IL','retailer','trade_supplier','Abo Srya fluted beech dowels','https://sryawood.co.il/products/%D7%93%D7%99%D7%91%D7%9C-%D7%A2%D7%A5-%D7%91%D7%95%D7%A7-%D7%9E%D7%97%D7%95%D7%A8%D7%A5-%D7%97%D7%AA%D7%95%D7%9A-%D7%A7%D7%95%D7%98%D7%A8-8-%D7%9E%D7%9E','2026-09-28','he-IL',null,'{"date_basis":"retrieved","species":"beech","form":"pre-cut fluted","price_basis":"displayed price per 1000","vat_statement":"not stated on captured product evidence","package_quantity_warning":"page contains inconsistent box quantities, so 1000 is retained only as the displayed pricing unit"}'::jsonb),
('36c826bf-c617-51a3-ad2c-c6eeac5af0ba','IL','retailer','diy_retail','Home Center dowels and handle screws','https://www.homecenter.co.il/collections/nuts-and-bolts','2026-09-28','he-IL',null,'{"date_basis":"retrieved","selection_rule":"exact dimensions and package quantities only","vat_statement":"not stated on captured product evidence","delivery":"excluded"}'::jsonb),
('70b1636e-f17a-5080-bfec-4e26d2d17bc9','IL','retailer','diy_retail','ACE beech dowel rods','https://www.ace.co.il/tools-paint-affixing/affixing-hanging-diy/screws/screw-anchor','2026-09-28','he-IL',null,'{"date_basis":"retrieved","stock_length_m":1,"vat_statement":"prices exclude VAT","promotion_valid_through":"2026-10-04","delivery":"excluded"}'::jsonb)
on conflict(source_id) do update set source_type=excluded.source_type,source_channel=excluded.source_channel,source_name=excluded.source_name,source_url=excluded.source_url,source_date=excluded.source_date,language_code=excluded.language_code,region=excluded.region,evidence=excluded.evidence,retrieved_at=now();

insert into public.reference_materials(material_id,material_code,department,category_code,canonical_name,base_unit,specifications) values
('5ae0cdba-2bd8-50a7-965a-b19563b556ae','wood_dowel_fluted_8x25mm','hardware','dowel_confirmat','Fluted beech dowel 8 x 25 mm','ea','{"material":"beech","form":"pre-cut fluted","diameter_mm":8,"length_mm":25}'::jsonb),
('aaea126d-d073-545c-86e9-aa7cd5ff98ee','wood_dowel_fluted_8x30mm','hardware','dowel_confirmat','Fluted beech dowel 8 x 30 mm','ea','{"material":"beech","form":"pre-cut fluted","diameter_mm":8,"length_mm":30}'::jsonb),
('0970f87d-57fb-5d93-a7b9-7a033d34c85c','wood_dowel_fluted_8x35mm','hardware','dowel_confirmat','Fluted beech dowel 8 x 35 mm','ea','{"material":"beech","form":"pre-cut fluted","diameter_mm":8,"length_mm":35}'::jsonb),
('0584b614-9421-548c-b036-db3a48ca52fb','wood_dowel_fluted_8x40mm','hardware','dowel_confirmat','Fluted wood dowel 8 x 40 mm','ea','{"form":"pre-cut fluted","diameter_mm":8,"length_mm":40}'::jsonb),
('595e62f4-da1b-5301-83bf-998f150c07d4','wood_dowel_fluted_8x45mm','hardware','dowel_confirmat','Fluted beech dowel 8 x 45 mm','ea','{"material":"beech","form":"pre-cut fluted","diameter_mm":8,"length_mm":45}'::jsonb),
('e7f58909-d074-574d-bc03-697ad65a608e','wood_dowel_fluted_8x50mm','hardware','dowel_confirmat','Fluted beech dowel 8 x 50 mm','ea','{"material":"beech","form":"pre-cut fluted","diameter_mm":8,"length_mm":50}'::jsonb),
('308c8a95-826e-5ffd-8b4f-0937533f3b0b','wood_dowel_fluted_6x40mm','hardware','dowel_confirmat','Fluted wood dowel 6 x 40 mm','ea','{"form":"pre-cut fluted","diameter_mm":6,"length_mm":40}'::jsonb),
('1f3f32d1-f595-5328-8704-9ef97a11e826','beech_dowel_rod_8mm','hardware','dowel_confirmat','Beech dowel rod 8 mm','lm','{"material":"beech","form":"round rod","diameter_mm":8}'::jsonb),
('80929c7b-5f16-5874-bf60-87a795539cf2','beech_dowel_rod_10mm','hardware','dowel_confirmat','Beech dowel rod 10 mm','lm','{"material":"beech","form":"round rod","diameter_mm":10}'::jsonb),
('a950b70f-ac88-54e5-b722-647af84390be','beech_dowel_rod_12mm','hardware','dowel_confirmat','Beech dowel rod 12 mm','lm','{"material":"beech","form":"round rod","diameter_mm":12}'::jsonb),
('e7ce12cd-73a7-5a69-a99b-e982c9e43867','beech_dowel_rod_15mm','hardware','dowel_confirmat','Beech dowel rod 15 mm','lm','{"material":"beech","form":"round rod","diameter_mm":15}'::jsonb),
('8319ef30-c240-555f-bf86-2f18f5de4a2b','beech_dowel_rod_18mm','hardware','dowel_confirmat','Beech dowel rod 18 mm','lm','{"material":"beech","form":"round rod","diameter_mm":18}'::jsonb),
('3512e753-8099-5892-acb9-27578379349c','beech_dowel_rod_22mm','hardware','dowel_confirmat','Beech dowel rod 22 mm','lm','{"material":"beech","form":"round rod","diameter_mm":22}'::jsonb),
('c75aac87-f0b3-574a-8ec7-9211df522478','machine_screw_m4x25mm','hardware','screw_bolt','Furniture handle machine screw M4 x 25 mm','ea','{"thread":"M4","length_mm":25,"application":"furniture handle"}'::jsonb),
('5906e94d-4b8f-528b-8825-860f26ce3d3d','machine_screw_m4x30mm','hardware','screw_bolt','Furniture handle machine screw M4 x 30 mm','ea','{"thread":"M4","length_mm":30,"application":"furniture handle"}'::jsonb),
('86591797-48cf-5205-ae98-bd673d6aef23','machine_screw_m4x40mm','hardware','screw_bolt','Furniture handle machine screw M4 x 40 mm','ea','{"thread":"M4","length_mm":40,"application":"furniture handle"}'::jsonb)
on conflict(material_code) do update set department=excluded.department,category_code=excluded.category_code,canonical_name=excluded.canonical_name,base_unit=excluded.base_unit,specifications=excluded.specifications,active=true,updated_at=now();

insert into public.market_material_profiles(material_id,market_code,market_name,language_code,local_specifications,availability_status)
select material_id,'IL',case material_code
  when 'wood_dowel_fluted_8x25mm' then 'דיבל עץ בוק מחורץ 8×25 מ״מ'
  when 'wood_dowel_fluted_8x30mm' then 'דיבל עץ בוק מחורץ 8×30 מ״מ'
  when 'wood_dowel_fluted_8x35mm' then 'דיבל עץ בוק מחורץ 8×35 מ״מ'
  when 'wood_dowel_fluted_8x40mm' then 'דיבל עץ מחורץ 8×40 מ״מ'
  when 'wood_dowel_fluted_8x45mm' then 'דיבל עץ בוק מחורץ 8×45 מ״מ'
  when 'wood_dowel_fluted_8x50mm' then 'דיבל עץ בוק מחורץ 8×50 מ״מ'
  when 'wood_dowel_fluted_6x40mm' then 'דיבל עץ מחורץ 6×40 מ״מ'
  when 'beech_dowel_rod_8mm' then 'מוט עגול מעץ בוק קוטר 8 מ״מ'
  when 'beech_dowel_rod_10mm' then 'מוט עגול מעץ בוק קוטר 10 מ״מ'
  when 'beech_dowel_rod_12mm' then 'מוט עגול מעץ בוק קוטר 12 מ״מ'
  when 'beech_dowel_rod_15mm' then 'מוט עגול מעץ בוק קוטר 15 מ״מ'
  when 'beech_dowel_rod_18mm' then 'מוט עגול מעץ בוק קוטר 18 מ״מ'
  when 'beech_dowel_rod_22mm' then 'מוט עגול מעץ בוק קוטר 22 מ״מ'
  when 'machine_screw_m4x25mm' then 'בורג לידית M4×25 מ״מ'
  when 'machine_screw_m4x30mm' then 'בורג לידית M4×30 מ״מ'
  when 'machine_screw_m4x40mm' then 'בורג לידית M4×40 מ״מ'
end,'he-IL','{"market":"Israel"}'::jsonb,'common'
from public.reference_materials where material_code in (
  'wood_dowel_fluted_8x25mm','wood_dowel_fluted_8x30mm','wood_dowel_fluted_8x35mm',
  'wood_dowel_fluted_8x40mm','wood_dowel_fluted_8x45mm','wood_dowel_fluted_8x50mm',
  'wood_dowel_fluted_6x40mm','beech_dowel_rod_8mm','beech_dowel_rod_10mm',
  'beech_dowel_rod_12mm','beech_dowel_rod_15mm','beech_dowel_rod_18mm',
  'beech_dowel_rod_22mm','machine_screw_m4x25mm','machine_screw_m4x30mm',
  'machine_screw_m4x40mm'
)
on conflict(material_id,market_code,language_code) do update set market_name=excluded.market_name,local_specifications=excluded.local_specifications,availability_status=excluded.availability_status,active=true,updated_at=now();

insert into public.market_material_offers(market_offer_id,material_id,market_code,source_id,supplier_name,supplier_sku,source_price,source_currency,source_unit,price_scope,included_services,delivery_included,package_quantity,minimum_order_quantity,vat_mode,normalized_price_ex_vat,normalized_unit,conversion_basis,region,valid_from,valid_to,confidence,status) values
('ee88656f-8e1f-57cb-a6d0-f3bbe3aaed9f','5ae0cdba-2bd8-50a7-965a-b19563b556ae','IL','b4c553ba-6638-53e8-8b69-900facf312f7','Abo Srya','VL825',122.50,'ILS','price_per_1000','retail_package','{}',false,1000,null,'unknown',null,'ea','{"pricing_quantity":1000,"normalization_blocked_by":"VAT status not stated","package_quantity_not_confirmed":true}'::jsonb,null,'2026-09-28',null,80,'candidate'),
('12d8bed0-f945-5883-b037-bc83305858ef','aaea126d-d073-545c-86e9-aa7cd5ff98ee','IL','b4c553ba-6638-53e8-8b69-900facf312f7','Abo Srya','VL830',130.34,'ILS','price_per_1000','retail_package','{}',false,1000,null,'unknown',null,'ea','{"pricing_quantity":1000,"normalization_blocked_by":"VAT status not stated","package_quantity_not_confirmed":true}'::jsonb,null,'2026-09-28',null,80,'candidate'),
('795e0d1a-b3d5-5312-bcc8-20c3a2f2d356','0970f87d-57fb-5d93-a7b9-7a033d34c85c','IL','b4c553ba-6638-53e8-8b69-900facf312f7','Abo Srya','VL835',145.04,'ILS','price_per_1000','retail_package','{}',false,1000,null,'unknown',null,'ea','{"pricing_quantity":1000,"normalization_blocked_by":"VAT status not stated","package_quantity_not_confirmed":true}'::jsonb,null,'2026-09-28',null,80,'candidate'),
('632de29f-1e79-5812-9f7a-d35926985a7b','595e62f4-da1b-5301-83bf-998f150c07d4','IL','b4c553ba-6638-53e8-8b69-900facf312f7','Abo Srya','VL845',161.70,'ILS','price_per_1000','retail_package','{}',false,1000,null,'unknown',null,'ea','{"pricing_quantity":1000,"normalization_blocked_by":"VAT status not stated","package_quantity_not_confirmed":true}'::jsonb,null,'2026-09-28',null,80,'candidate'),
('a77cc7fa-1798-511f-9da2-aa098294a660','e7f58909-d074-574d-bc03-697ad65a608e','IL','b4c553ba-6638-53e8-8b69-900facf312f7','Abo Srya','VL850',192.08,'ILS','price_per_1000','retail_package','{}',false,1000,null,'unknown',null,'ea','{"pricing_quantity":1000,"normalization_blocked_by":"VAT status not stated","package_quantity_not_confirmed":true}'::jsonb,null,'2026-09-28',null,80,'candidate'),
('3ee69e83-e32f-5c9c-a191-73091cfa3ec4','308c8a95-826e-5ffd-8b4f-0937533f3b0b','IL','36c826bf-c617-51a3-ad2c-c6eeac5af0ba','Home Center','8081214759',10.00,'ILS','pack_12','retail_package','{}',false,12,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated","delivery":"excluded"}'::jsonb,null,'2026-09-28',null,84,'candidate'),
('f4156516-8340-52a5-8b79-93d555fb4c79','0584b614-9421-548c-b036-db3a48ca52fb','IL','36c826bf-c617-51a3-ad2c-c6eeac5af0ba','Home Center','8081214760',10.00,'ILS','pack_12','retail_package','{}',false,12,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated","delivery":"excluded"}'::jsonb,null,'2026-09-28',null,84,'candidate'),
('9663f204-962d-5dfa-afdd-cfdb93bf3430','0584b614-9421-548c-b036-db3a48ca52fb','IL','36c826bf-c617-51a3-ad2c-c6eeac5af0ba','Home Center','1736756629760',11.90,'ILS','pack_16','retail_package','{}',false,16,1,'unknown',null,'ea','{"brand":"Herman","normalization_blocked_by":"VAT status not stated","delivery":"excluded"}'::jsonb,null,'2026-09-28',null,84,'candidate'),
('4617d09d-99f4-5e72-8f95-b2c25e8734b5','1f3f32d1-f595-5328-8704-9ef97a11e826','IL','70b1636e-f17a-5080-bfec-4e26d2d17bc9','ACE','4805838',9.24,'ILS','rod_1m','retail_package','{}',false,1,1,'excluded',9.24,'lm','{"stock_length_m":1,"calculation":"9.24 / 1","promotion":true,"delivery":"excluded"}'::jsonb,null,'2026-09-28','2026-10-04',90,'candidate'),
('4e853985-ec16-58e6-96ad-58665c51f910','80929c7b-5f16-5874-bf60-87a795539cf2','IL','70b1636e-f17a-5080-bfec-4e26d2d17bc9','ACE','4805845',10.93,'ILS','rod_1m','retail_package','{}',false,1,1,'excluded',10.93,'lm','{"stock_length_m":1,"calculation":"10.93 / 1","promotion":true,"delivery":"excluded"}'::jsonb,null,'2026-09-28','2026-10-04',90,'candidate'),
('790715d1-95eb-5bf1-8f75-32979d368615','a950b70f-ac88-54e5-b722-647af84390be','IL','70b1636e-f17a-5080-bfec-4e26d2d17bc9','ACE','4805852',13.48,'ILS','rod_1m','retail_package','{}',false,1,1,'excluded',13.48,'lm','{"stock_length_m":1,"calculation":"13.48 / 1","promotion":true,"delivery":"excluded"}'::jsonb,null,'2026-09-28','2026-10-04',90,'candidate'),
('6bc5114a-bc76-5459-9986-a0e650ebac26','e7ce12cd-73a7-5a69-a99b-e982c9e43867','IL','70b1636e-f17a-5080-bfec-4e26d2d17bc9','ACE','4805869',19.41,'ILS','rod_1m','retail_package','{}',false,1,1,'excluded',19.41,'lm','{"stock_length_m":1,"calculation":"19.41 / 1","promotion":true,"delivery":"excluded"}'::jsonb,null,'2026-09-28','2026-10-04',90,'candidate'),
('784bfec5-8c98-5bed-91fc-086b81812112','8319ef30-c240-555f-bf86-2f18f5de4a2b','IL','70b1636e-f17a-5080-bfec-4e26d2d17bc9','ACE','4805876',31.27,'ILS','rod_1m','retail_package','{}',false,1,1,'excluded',31.27,'lm','{"stock_length_m":1,"calculation":"31.27 / 1","promotion":true,"delivery":"excluded"}'::jsonb,null,'2026-09-28','2026-10-04',90,'candidate'),
('d0e837d6-3e65-5ff9-8c79-72a252069925','3512e753-8099-5892-acb9-27578379349c','IL','70b1636e-f17a-5080-bfec-4e26d2d17bc9','ACE','4805883',38.05,'ILS','rod_1m','retail_package','{}',false,1,1,'excluded',38.05,'lm','{"stock_length_m":1,"calculation":"38.05 / 1","promotion":true,"delivery":"excluded"}'::jsonb,null,'2026-09-28','2026-10-04',90,'candidate'),
('b56d0cc4-f2cf-5a39-bf9c-5ee3b141e0cc','c75aac87-f0b3-574a-8ec7-9211df522478','IL','36c826bf-c617-51a3-ad2c-c6eeac5af0ba','Home Center','8081214410',10.00,'ILS','pack_20','retail_package','{}',false,20,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated","delivery":"excluded"}'::jsonb,null,'2026-09-28',null,84,'candidate'),
('c9488ccd-ee75-5660-bf7b-88d5e65fa518','5906e94d-4b8f-528b-8825-860f26ce3d3d','IL','36c826bf-c617-51a3-ad2c-c6eeac5af0ba','Home Center','8081214411',10.00,'ILS','pack_20','retail_package','{}',false,20,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated","delivery":"excluded"}'::jsonb,null,'2026-09-28',null,84,'candidate'),
('6ee31479-0b97-5a5c-b128-8255fb6b9ba6','86591797-48cf-5205-ae98-bd673d6aef23','IL','36c826bf-c617-51a3-ad2c-c6eeac5af0ba','Home Center','8081214412',10.00,'ILS','pack_20','retail_package','{}',false,20,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated","delivery":"excluded"}'::jsonb,null,'2026-09-28',null,84,'candidate')
on conflict(market_offer_id) do update set source_price=excluded.source_price,source_currency=excluded.source_currency,source_unit=excluded.source_unit,price_scope=excluded.price_scope,included_services=excluded.included_services,delivery_included=excluded.delivery_included,package_quantity=excluded.package_quantity,minimum_order_quantity=excluded.minimum_order_quantity,vat_mode=excluded.vat_mode,normalized_price_ex_vat=excluded.normalized_price_ex_vat,normalized_unit=excluded.normalized_unit,conversion_basis=excluded.conversion_basis,region=excluded.region,valid_from=excluded.valid_from,valid_to=excluded.valid_to,confidence=excluded.confidence,status=excluded.status;
