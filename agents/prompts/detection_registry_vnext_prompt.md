# RFQ DETECTION REGISTRY VNEXT 3.15.8

Return only the locked commercial-object registry. The input contains full pages and labelled enlarged page regions. Use enlarged regions to identify separate drawing groups, then use the full pages to link only proven repeated views of the same physical product.

Start each spatially separate product drawing group as a separate candidate. A shared page, room title, material palette or proximity never merges candidates. Link candidates only with a shared distinctive silhouette, integral frame and panel pattern, explicit view relation, common object code, or matching overall dimensions. A front and perspective of the same long cabinet are one object only when their distinctive structure and panel sequence match.

An object is one physical product a custom-fabrication contractor would quote, fabricate, supply, install, replace, or price independently. Split only with strong independent-product evidence: separate envelope, function, code, quantity, responsibility, or independent fabrication and installation. Never create entries for views, components, panels, fronts, tracks, hardware, appliances, loose lighting, MEP, decor, renders or drawing pages.

A kitchen, integrated cabinet wall or shelving wall is one object. Its blocks, modules, panels, fronts, carcasses, profiles, hardware and assembly sheets are construction detail, not objects.

Return schema JSON only. `object_id` is ordered `object-001`, `object-002`, and so on. `transport_label` is the exact object code when printed, otherwise `Object 1`, `Object 2`, and so on. `quantity` is the number of complete physical objects. `identity_pages` uses physical upload page numbers. `visual_identity` describes the complete silhouette and the specific full-page groups or views that prove it. `boundary_basis` records the factual reason it is one quote line. Do not extract dimensions, materials, pricing or names.
