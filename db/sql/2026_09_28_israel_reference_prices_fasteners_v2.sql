-- 3.15.1 Israel Reference Catalog v1, fasteners batch 2.
-- Retrieved 2026-09-28. Exact chipboard-screw dimensions are separate material
-- identities; supplier pack quantity remains an offer attribute.

insert into public.reference_sources(source_id,market_code,source_type,source_channel,source_name,source_url,source_date,language_code,region,evidence) values
('7880a08b-75ba-54c9-a793-aae1738e349b','IL','retailer','specialist_retailer','ERCO VEGA chipboard screws','https://www.erco.co.il/b2c/99565247v-main.html','2026-09-28','he-IL',null,'{"date_basis":"retrieved","vat_statement":"prices include VAT","brand":"VEGA","availability":"only displayed in-stock variants retained"}'::jsonb),
('0e012e2b-18cd-585d-90cb-bfb33e7890f5','IL','retailer','trade_supplier','Abo Srya FGV chipboard screws','https://sryawood.co.il/products/%D7%91%D7%95%D7%A8%D7%92-%D7%A1%D7%99%D7%91%D7%99%D7%AA-fgv','2026-09-28','he-IL',null,'{"date_basis":"retrieved","brand":"FGV","package_quantity":1000,"vat_statement":"not stated on captured product evidence"}'::jsonb),
('20528b58-6487-5225-8840-27de4752d881','IL','retailer','trade_supplier','Ariel Pirzul FGV screws','https://apirzul.co.il/%D7%91%D7%A8%D7%92%D7%99%D7%9D/','2026-09-28','he-IL',null,'{"date_basis":"retrieved","brand":"FGV","selected_variant":"4x40 mm","package_quantity":1000,"vat_statement":"not stated on captured listing evidence"}'::jsonb)
on conflict(source_id) do update set source_type=excluded.source_type,source_channel=excluded.source_channel,source_name=excluded.source_name,source_url=excluded.source_url,source_date=excluded.source_date,language_code=excluded.language_code,region=excluded.region,evidence=excluded.evidence,retrieved_at=now();

insert into public.reference_materials(material_id,material_code,department,category_code,canonical_name,base_unit,specifications) values
('7502fcce-ae49-5467-9e34-b98422d385ee','chipboard_screw_3x30mm','hardware','screw_bolt','Chipboard screw 3 x 30 mm','ea','{"diameter_mm":3,"length_mm":30}'::jsonb),
('694d0c04-3988-525a-8d52-f5846fb01b87','chipboard_screw_3_5x35mm','hardware','screw_bolt','Chipboard screw 3.5 x 35 mm','ea','{"diameter_mm":3.5,"length_mm":35}'::jsonb),
('6a75205e-48fa-5c4b-b465-689865f32a94','chipboard_screw_3_5x45mm','hardware','screw_bolt','Chipboard screw 3.5 x 45 mm','ea','{"diameter_mm":3.5,"length_mm":45}'::jsonb),
('f21c8223-3699-5681-8158-8ab458b014d5','chipboard_screw_4x20mm','hardware','screw_bolt','Chipboard screw 4 x 20 mm','ea','{"diameter_mm":4,"length_mm":20}'::jsonb),
('a164e53f-c1d5-54f1-8d66-f17551d63fcb','chipboard_screw_4x30mm','hardware','screw_bolt','Chipboard screw 4 x 30 mm','ea','{"diameter_mm":4,"length_mm":30}'::jsonb),
('b93ba021-82a8-530b-9285-13fda0067c44','chipboard_screw_4x40mm','hardware','screw_bolt','Chipboard screw 4 x 40 mm','ea','{"diameter_mm":4,"length_mm":40}'::jsonb),
('e338b6d3-f8f2-5efc-90f1-d09545c7bf56','chipboard_screw_4x50mm','hardware','screw_bolt','Chipboard screw 4 x 50 mm','ea','{"diameter_mm":4,"length_mm":50}'::jsonb),
('5c2a6e18-45ed-57c8-a3ea-6277e68d8418','chipboard_screw_4x60mm','hardware','screw_bolt','Chipboard screw 4 x 60 mm','ea','{"diameter_mm":4,"length_mm":60}'::jsonb),
('b2a0b0e7-fbb0-5323-9ec1-b0c3465e8ee0','chipboard_screw_4_5x20mm','hardware','screw_bolt','Chipboard screw 4.5 x 20 mm','ea','{"diameter_mm":4.5,"length_mm":20}'::jsonb),
('e2ee8eca-44e6-52c1-97c1-c78499a1cbef','chipboard_screw_4_5x40mm','hardware','screw_bolt','Chipboard screw 4.5 x 40 mm','ea','{"diameter_mm":4.5,"length_mm":40}'::jsonb),
('a8b2332d-1312-508e-97d4-ab33f8508cba','chipboard_screw_4_5x60mm','hardware','screw_bolt','Chipboard screw 4.5 x 60 mm','ea','{"diameter_mm":4.5,"length_mm":60}'::jsonb),
('ffc4bb42-c204-5c24-8ef2-5613ae7e0fb9','chipboard_screw_5x30mm','hardware','screw_bolt','Chipboard screw 5 x 30 mm','ea','{"diameter_mm":5,"length_mm":30}'::jsonb),
('25395575-7cfc-5cb2-8d94-5ce6937915e5','chipboard_screw_5x50mm','hardware','screw_bolt','Chipboard screw 5 x 50 mm','ea','{"diameter_mm":5,"length_mm":50}'::jsonb),
('9800e1d2-951d-501d-9ee4-2f7e27808961','chipboard_screw_5x60mm','hardware','screw_bolt','Chipboard screw 5 x 60 mm','ea','{"diameter_mm":5,"length_mm":60}'::jsonb),
('dce7d847-5a3d-59ba-a95f-f401cb8efb2e','chipboard_screw_5x70mm','hardware','screw_bolt','Chipboard screw 5 x 70 mm','ea','{"diameter_mm":5,"length_mm":70}'::jsonb),
('cf18b61d-6f84-51b1-aa14-27d3186cda2d','chipboard_screw_5x80mm','hardware','screw_bolt','Chipboard screw 5 x 80 mm','ea','{"diameter_mm":5,"length_mm":80}'::jsonb)
on conflict(material_code) do update set department=excluded.department,category_code=excluded.category_code,canonical_name=excluded.canonical_name,base_unit=excluded.base_unit,specifications=excluded.specifications,active=true,updated_at=now();

insert into public.market_material_profiles(material_id,market_code,market_name,language_code,local_specifications,availability_status)
select material_id,'IL',case material_code
  when 'chipboard_screw_3x30mm' then 'בורג סיבית 3×30 מ״מ'
  when 'chipboard_screw_3_5x35mm' then 'בורג סיבית 3.5×35 מ״מ'
  when 'chipboard_screw_3_5x45mm' then 'בורג סיבית 3.5×45 מ״מ'
  when 'chipboard_screw_4x20mm' then 'בורג סיבית 4×20 מ״מ'
  when 'chipboard_screw_4x30mm' then 'בורג סיבית 4×30 מ״מ'
  when 'chipboard_screw_4x40mm' then 'בורג סיבית 4×40 מ״מ'
  when 'chipboard_screw_4x50mm' then 'בורג סיבית 4×50 מ״מ'
  when 'chipboard_screw_4x60mm' then 'בורג סיבית 4×60 מ״מ'
  when 'chipboard_screw_4_5x20mm' then 'בורג סיבית 4.5×20 מ״מ'
  when 'chipboard_screw_4_5x40mm' then 'בורג סיבית 4.5×40 מ״מ'
  when 'chipboard_screw_4_5x60mm' then 'בורג סיבית 4.5×60 מ״מ'
  when 'chipboard_screw_5x30mm' then 'בורג סיבית 5×30 מ״מ'
  when 'chipboard_screw_5x50mm' then 'בורג סיבית 5×50 מ״מ'
  when 'chipboard_screw_5x60mm' then 'בורג סיבית 5×60 מ״מ'
  when 'chipboard_screw_5x70mm' then 'בורג סיבית 5×70 מ״מ'
  when 'chipboard_screw_5x80mm' then 'בורג סיבית 5×80 מ״מ'
end,'he-IL','{"market":"Israel"}'::jsonb,'common'
from public.reference_materials where material_code in (
  'chipboard_screw_3x30mm','chipboard_screw_3_5x35mm','chipboard_screw_3_5x45mm',
  'chipboard_screw_4x20mm','chipboard_screw_4x30mm','chipboard_screw_4x40mm',
  'chipboard_screw_4x50mm','chipboard_screw_4x60mm','chipboard_screw_4_5x20mm',
  'chipboard_screw_4_5x40mm','chipboard_screw_4_5x60mm','chipboard_screw_5x30mm',
  'chipboard_screw_5x50mm','chipboard_screw_5x60mm','chipboard_screw_5x70mm',
  'chipboard_screw_5x80mm'
)
on conflict(material_id,market_code,language_code) do update set market_name=excluded.market_name,local_specifications=excluded.local_specifications,availability_status=excluded.availability_status,active=true,updated_at=now();

insert into public.market_material_offers(market_offer_id,material_id,market_code,source_id,supplier_name,supplier_sku,source_price,source_currency,source_unit,price_scope,included_services,delivery_included,package_quantity,minimum_order_quantity,vat_mode,normalized_price_ex_vat,normalized_unit,conversion_basis,region,valid_from,confidence,status) values
('7fda47e5-6b78-5026-ad8a-77e21f714b1d','1cc756b6-c58e-590b-97fa-dbac4fe817f9','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565247V',4.80,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.040678,'ea','{"calculation":"4.80 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('f533bf6b-e8b7-5a81-b13c-85075b05662c','7502fcce-ae49-5467-9e34-b98422d385ee','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565250V',5.50,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.046610,'ea','{"calculation":"5.50 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('05138fe5-11b5-577b-84e4-d834de24534b','694d0c04-3988-525a-8d52-f5846fb01b87','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','995652502V',6.20,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.052542,'ea','{"calculation":"6.20 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('e1d5a389-c44f-567b-9340-ab3572e81494','6a75205e-48fa-5c4b-b465-689865f32a94','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','995652504V',7.20,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.061017,'ea','{"calculation":"7.20 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('92d2b347-f2a9-5406-9644-6e803073e24a','f21c8223-3699-5681-8158-8ab458b014d5','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565252V',5.70,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.048305,'ea','{"calculation":"5.70 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('838d4869-adee-57b5-a79b-0f3f98da170d','a164e53f-c1d5-54f1-8d66-f17551d63fcb','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565254V',6.20,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.052542,'ea','{"calculation":"6.20 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('7586a9e6-217e-5f21-9f1d-42476bbe1c87','e338b6d3-f8f2-5efc-90f1-d09545c7bf56','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565258V',8.60,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.072881,'ea','{"calculation":"8.60 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('6c5f1573-d517-55be-b22c-735e3301e4fb','5c2a6e18-45ed-57c8-a3ea-6277e68d8418','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565259V',11.40,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.096610,'ea','{"calculation":"11.40 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('4a210aab-ab74-58e5-bb97-eee3599a4284','b2a0b0e7-fbb0-5323-9ec1-b0c3465e8ee0','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565260V',7.10,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.060169,'ea','{"calculation":"7.10 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('1dde2b65-e971-554b-9f07-7fdec73d6b55','e2ee8eca-44e6-52c1-97c1-c78499a1cbef','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565264V',8.40,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.071186,'ea','{"calculation":"8.40 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('ae1e53bf-c75b-5816-90d7-869f8b0cb2e7','a8b2332d-1312-508e-97d4-ab33f8508cba','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565267V',12.40,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.105085,'ea','{"calculation":"12.40 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('afb9d694-ca7c-53d0-bd58-594b16f990b8','ffc4bb42-c204-5c24-8ef2-5613ae7e0fb9','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565272V',9.30,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.078814,'ea','{"calculation":"9.30 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('eb4fbe68-0f8e-518b-8603-d970c756fa57','25395575-7cfc-5cb2-8d94-5ce6937915e5','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565276V',11.90,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.100847,'ea','{"calculation":"11.90 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('6b459da3-fc50-5b8e-9312-fc80f9e55acc','9800e1d2-951d-501d-9ee4-2f7e27808961','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565277V',14.30,'ILS','pack_100','retail_package','{}',false,100,1,'included',0.121186,'ea','{"calculation":"14.30 / 1.18 / 100"}'::jsonb,null,'2026-09-28',90,'candidate'),
('18707727-504f-5f09-81b2-e534f0fe060e','dce7d847-5a3d-59ba-a95f-f401cb8efb2e','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565278V',20.10,'ILS','pack_50','retail_package','{}',false,50,1,'included',0.340678,'ea','{"calculation":"20.10 / 1.18 / 50"}'::jsonb,null,'2026-09-28',90,'candidate'),
('852a9f8e-1f6e-5870-b194-ba1fd12b13f4','cf18b61d-6f84-51b1-aa14-27d3186cda2d','IL','7880a08b-75ba-54c9-a793-aae1738e349b','ERCO','99565279V',21.70,'ILS','pack_50','retail_package','{}',false,50,1,'included',0.367797,'ea','{"calculation":"21.70 / 1.18 / 50"}'::jsonb,null,'2026-09-28',90,'candidate'),
('5128c869-d7b6-5e34-b93c-8a38f9513772','1cc756b6-c58e-590b-97fa-dbac4fe817f9','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3320',64.68,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('8c115aad-9b83-5930-81d6-3655e1e73149','7502fcce-ae49-5467-9e34-b98422d385ee','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3330',77.42,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('21fad6f0-a704-52b5-9667-b59de007258a','694d0c04-3988-525a-8d52-f5846fb01b87','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO33535',98.00,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('4132f844-1df3-5783-835d-1d2ce6fcebca','6a75205e-48fa-5c4b-b465-689865f32a94','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO33545',116.62,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('63cff6d3-43ae-566a-a626-b96e2d3760b2','f21c8223-3699-5681-8158-8ab458b014d5','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3420',78.40,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('381f2c4e-7c88-56fd-8bfc-a58850c1c2c4','a164e53f-c1d5-54f1-8d66-f17551d63fcb','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3430',98.00,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('52956db0-1f6c-5e8e-b07d-ff5ea13edadb','b93ba021-82a8-530b-9285-13fda0067c44','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3440',122.50,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('ac246beb-70f7-5117-ad59-999184831619','e338b6d3-f8f2-5efc-90f1-d09545c7bf56','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3450',146.02,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('c7786a87-965c-5570-beab-859d40dda580','b2a0b0e7-fbb0-5323-9ec1-b0c3465e8ee0','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO34520',98.00,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('c113f58c-4391-50d7-8f20-055e9748634f','e2ee8eca-44e6-52c1-97c1-c78499a1cbef','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO34540',153.86,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('19220696-aee1-57e0-8ed4-eaf26128a1c2','a8b2332d-1312-508e-97d4-ab33f8508cba','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO34560',119.56,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('3d8a1873-f915-5a3e-a494-cb827e792c26','ffc4bb42-c204-5c24-8ef2-5613ae7e0fb9','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3530',155.82,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('a1aff6b4-64e0-5cd5-91b2-517153b8490d','25395575-7cfc-5cb2-8d94-5ce6937915e5','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3550',119.56,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('4ac472f1-a73e-54e3-bc09-76e5a5a35f09','9800e1d2-951d-501d-9ee4-2f7e27808961','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3560',231.28,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('ad874138-bebb-5817-a6b6-dd2a5f581cbf','dce7d847-5a3d-59ba-a95f-f401cb8efb2e','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3570',74.48,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated","price_outlier_review_required":true}'::jsonb,null,'2026-09-28',60,'candidate'),
('b12d5cd3-2b3c-59ad-9019-56d05487647b','cf18b61d-6f84-51b1-aa14-27d3186cda2d','IL','0e012e2b-18cd-585d-90cb-bfb33e7890f5','Abo Srya','DO3580',91.14,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',82,'candidate'),
('c09e140f-4ea3-5604-bc0b-da927d1191f3','b93ba021-82a8-530b-9285-13fda0067c44','IL','20528b58-6487-5225-8840-27de4752d881','Ariel Pirzul',null,118.00,'ILS','pack_1000','trade_package','{}',false,1000,1,'unknown',null,'ea','{"normalization_blocked_by":"VAT status not stated"}'::jsonb,null,'2026-09-28',78,'candidate')
on conflict(market_offer_id) do update set source_price=excluded.source_price,source_currency=excluded.source_currency,source_unit=excluded.source_unit,price_scope=excluded.price_scope,included_services=excluded.included_services,delivery_included=excluded.delivery_included,package_quantity=excluded.package_quantity,minimum_order_quantity=excluded.minimum_order_quantity,vat_mode=excluded.vat_mode,normalized_price_ex_vat=excluded.normalized_price_ex_vat,normalized_unit=excluded.normalized_unit,conversion_basis=excluded.conversion_basis,region=excluded.region,valid_from=excluded.valid_from,confidence=excluded.confidence,status=excluded.status;
