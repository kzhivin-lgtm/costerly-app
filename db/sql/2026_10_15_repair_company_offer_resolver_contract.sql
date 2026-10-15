-- Repair pre-existing Price Source rows created before Company-offer scope
-- and MDF Pricing-Key normalization were connected to Material Resolver.
-- Prices, purchase formats and source evidence remain unchanged. Run WITHOUT RLS.

begin;

update public.company_material_offers offer
set price_scope = 'retail_package'
from public.company_material_items item
where offer.company_material_id = item.company_material_id
  and offer.status = 'active'
  and offer.price_scope = 'material_only'
  and item.specifications ->> 'material_family' like 'hardware_%';

create temporary table _mdf_pricing_key_repair (
    source_description_key text primary key,
    board_type text not null,
    surface text not null
) on commit drop;

insert into _mdf_pricing_key_repair values
    ('mdf 18 mm 2440 x 1220 mm raw', 'mdf', 'raw'),
    ('mdf 19 mm 2440 x 1220 mm white melamine faced', 'mdf', 'melamine_two_sided'),
    ('mdf 19 mm 2800 x 2070 mm oak melamine faced', 'mdf', 'melamine_two_sided');

update public.company_material_items item
set specifications = item.specifications || jsonb_build_object(
        'board_type', repair.board_type,
        'surface', repair.surface
    ),
    updated_at = now()
from _mdf_pricing_key_repair repair
where item.specifications ->> 'source_description_key' = repair.source_description_key
  and item.specifications ->> 'material_family' = 'mdf_hdf';

do $$
declare
    hardware_scope_count integer;
    mdf_key_count integer;
begin
    select count(*) into hardware_scope_count
    from public.company_material_offers offer
    join public.company_material_items item
      on item.company_material_id = offer.company_material_id
    where offer.status = 'active'
      and item.specifications ->> 'material_family' like 'hardware_%'
      and offer.price_scope = 'retail_package';
    if hardware_scope_count < 7 then
        raise exception 'Expected at least 7 active hardware offers in retail_package scope, found %', hardware_scope_count;
    end if;

    select count(*) into mdf_key_count
    from public.company_material_items item
    join _mdf_pricing_key_repair repair
      on item.specifications ->> 'source_description_key' = repair.source_description_key
    where item.specifications ->> 'material_family' = 'mdf_hdf'
      and item.specifications ->> 'board_type' = repair.board_type
      and item.specifications ->> 'surface' = repair.surface;
    if mdf_key_count <> 3 then
        raise exception 'Expected 3 repaired MDF Pricing Keys, found %', mdf_key_count;
    end if;
end $$;

commit;
