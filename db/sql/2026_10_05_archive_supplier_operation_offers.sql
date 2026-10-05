-- 3.16.7 Keep Price Source removal consistent for material and job offers.

begin;

create or replace function public.archive_company_price_source(
    p_company_id text,
    p_source_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    archived_offer_count integer := 0;
    archived_material_count integer := 0;
    archived_operation_offer_count integer := 0;
begin
    if not exists (
        select 1 from public.company_price_sources source
        where source.company_id = p_company_id
          and source.source_id = p_source_id
          and source.status <> 'archived'
        for update
    ) then
        raise exception 'Active company price source not found';
    end if;

    update public.company_material_offers offer
    set status = 'archived'
    where offer.company_id = p_company_id
      and offer.source_id = p_source_id
      and offer.status <> 'archived';
    get diagnostics archived_offer_count = row_count;

    update public.company_supplier_operation_offers offer
    set status = 'archived'
    where offer.company_id = p_company_id
      and offer.source_id = p_source_id
      and offer.status <> 'archived';
    get diagnostics archived_operation_offer_count = row_count;

    update public.company_price_sources source
    set status = 'archived', updated_at = now()
    where source.company_id = p_company_id and source.source_id = p_source_id;

    update public.company_material_items material
    set status = 'archived', updated_at = now()
    where material.company_id = p_company_id
      and material.created_from_source_id = p_source_id
      and material.status <> 'archived'
      and not exists (
          select 1 from public.company_material_offers active_offer
          where active_offer.company_id = material.company_id
            and active_offer.company_material_id = material.company_material_id
            and active_offer.status = 'active'
      );
    get diagnostics archived_material_count = row_count;

    return jsonb_build_object(
        'archived_offers', archived_offer_count,
        'archived_materials', archived_material_count,
        'archived_operation_offers', archived_operation_offer_count
    );
end;
$$;

commit;
