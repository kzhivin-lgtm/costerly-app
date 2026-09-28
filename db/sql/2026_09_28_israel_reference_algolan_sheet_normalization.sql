-- 3.15.2 Algolan sheet-unit normalization.
--
-- These offers were blocked because sheet dimensions were not stated. Their
-- canonical material unit is already `sheet`, the source price is per sheet,
-- package quantity is one, and VAT is explicitly excluded. Sheet dimensions
-- are required for later nesting or area conversion, but not for preserving a
-- directly observed price per sheet.
--
-- This migration corrects 12 candidate prices only. It does not infer a square
-- metre price, review or activate an offer, or create a market baseline.

begin;

do $$
declare
    total_count integer;
    pending_count integer;
    normalized_count integer;
    invalid_count integer;
begin
    select count(*)
      into total_count
    from public.market_material_offers o
    join public.reference_materials m
      on m.material_id = o.material_id
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.supplier_name = 'Algolan'
      and m.base_unit = 'sheet';

    if total_count <> 12 then
        raise exception
            'Algolan normalization expected 12 sheet candidates, found %',
            total_count;
    end if;

    select
        count(*) filter (
            where o.vat_mode = 'excluded'
              and o.normalized_price_ex_vat is null
              and o.source_unit = 'sheet_dimensions_unstated'
              and o.package_quantity = 1
        ),
        count(*) filter (
            where o.vat_mode = 'excluded'
              and o.normalized_price_ex_vat = o.source_price
              and o.normalized_unit = 'sheet'
              and o.conversion_basis ->> 'normalization_basis'
                    = 'direct observed price per canonical sheet unit'
        )
      into pending_count, normalized_count
    from public.market_material_offers o
    join public.reference_materials m
      on m.material_id = o.material_id
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.supplier_name = 'Algolan'
      and m.base_unit = 'sheet';

    if pending_count + normalized_count <> 12 then
        raise exception
            'Algolan normalization found unexpected state: % pending, % normalized',
            pending_count,
            normalized_count;
    end if;

    select count(*)
      into invalid_count
    from public.market_material_offers o
    join public.reference_materials m
      on m.material_id = o.material_id
    where o.market_code = 'IL'
      and o.status = 'candidate'
      and o.supplier_name = 'Algolan'
      and m.base_unit = 'sheet'
      and (
          o.vat_mode <> 'excluded'
          or o.source_price <= 0
          or o.package_quantity <> 1
      );

    if invalid_count <> 0 then
        raise exception
            'Algolan normalization found % candidates outside the safe boundary',
            invalid_count;
    end if;
end $$;

update public.market_material_offers o
set
    normalized_price_ex_vat = o.source_price,
    normalized_unit = 'sheet',
    conversion_basis = (
        o.conversion_basis - 'normalization_blocked_by'
    ) || jsonb_build_object(
        'normalization_basis',
            'direct observed price per canonical sheet unit',
        'sheet_dimensions_required_for_area_conversion', true,
        'normalization_formula', 'source_price / package_quantity'
    )
from public.reference_materials m
where m.material_id = o.material_id
  and m.base_unit = 'sheet'
  and o.market_code = 'IL'
  and o.status = 'candidate'
  and o.supplier_name = 'Algolan'
  and o.vat_mode = 'excluded'
  and o.normalized_price_ex_vat is null
  and o.source_unit = 'sheet_dimensions_unstated'
  and o.package_quantity = 1;

commit;
