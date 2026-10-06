-- 3.16.7 Permanently remove one company Price Source and its private evidence.
-- Shared company materials survive only when another offer still uses them.

begin;

create or replace function public.purge_company_price_source(
    p_company_id text,
    p_source_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    deleted_material_offer_count integer := 0;
    deleted_operation_offer_count integer := 0;
    deleted_service_offer_count integer := 0;
    deleted_row_count integer := 0;
    deleted_material_count integer := 0;
    deleted_alias_count integer := 0;
    source_material_ids uuid[] := '{}'::uuid[];
    source_row_ids uuid[] := '{}'::uuid[];
begin
    if not exists (
        select 1
        from public.company_price_sources source
        where source.company_id = p_company_id
          and source.source_id = p_source_id
        for update
    ) then
        raise exception 'Company price source not found';
    end if;

    perform 1
    from public.company_material_items material
    where material.company_id = p_company_id
      and material.created_from_source_id = p_source_id
    for update;

    select coalesce(array_agg(material.company_material_id), '{}'::uuid[])
    into source_material_ids
    from public.company_material_items material
    where material.company_id = p_company_id
      and material.created_from_source_id = p_source_id;

    select coalesce(array_agg(row.row_id), '{}'::uuid[])
    into source_row_ids
    from public.company_price_source_rows row
    where row.company_id = p_company_id
      and row.source_id = p_source_id;

    delete from public.company_material_offers offer
    where offer.company_id = p_company_id
      and offer.source_id = p_source_id;
    get diagnostics deleted_material_offer_count = row_count;

    delete from public.company_supplier_operation_offers offer
    where offer.company_id = p_company_id
      and offer.source_id = p_source_id;
    get diagnostics deleted_operation_offer_count = row_count;

    delete from public.company_service_offers offer
    where offer.company_id = p_company_id
      and offer.source_id = p_source_id;
    get diagnostics deleted_service_offer_count = row_count;

    delete from public.company_supplier_aliases alias
    where alias.company_id = p_company_id
      and alias.alias_kind = 'source_observed'
      and alias.source_id = p_source_id;
    get diagnostics deleted_alias_count = row_count;

    delete from public.material_identity_resolution_events event
    where event.company_id = p_company_id
      and event.source_row_id = any(source_row_ids);

    delete from public.company_material_aliases alias
    where alias.company_id = p_company_id
      and alias.source_row_id = any(source_row_ids);

    -- The row and candidate tables retain optional references to one another.
    -- Break the row-to-candidate side before deleting candidates, which still
    -- retain a mandatory source-row reference.
    update public.company_price_source_rows row
    set identity_candidate_id = null
    where row.company_id = p_company_id
      and row.row_id = any(source_row_ids)
      and row.identity_candidate_id is not null;

    delete from public.material_identity_candidates candidate
    where candidate.company_id = p_company_id
      and candidate.source_row_id = any(source_row_ids);

    delete from public.company_price_source_rows row
    where row.company_id = p_company_id
      and row.source_id = p_source_id;
    get diagnostics deleted_row_count = row_count;

    delete from public.company_material_items material
    where material.company_id = p_company_id
      and material.company_material_id = any(source_material_ids)
      and not exists (
          select 1
          from public.company_material_offers offer
          where offer.company_id = material.company_id
            and offer.company_material_id = material.company_material_id
      )
      and not exists (
          select 1
          from public.material_identity_candidates candidate
          where candidate.company_material_id = material.company_material_id
      )
      and not exists (
          select 1
          from public.material_identity_resolution_events event
          where event.company_material_id = material.company_material_id
      );
    get diagnostics deleted_material_count = row_count;

    -- A material kept by another source cannot retain a foreign key to the
    -- source being purged. Its other offers remain its active provenance.
    update public.company_material_items material
    set created_from_source_id = null,
        updated_at = now()
    where material.company_id = p_company_id
      and material.company_material_id = any(source_material_ids)
      and material.created_from_source_id = p_source_id;

    delete from public.company_price_sources source
    where source.company_id = p_company_id
      and source.source_id = p_source_id;

    return jsonb_build_object(
        'deleted_material_offers', deleted_material_offer_count,
        'deleted_operation_offers', deleted_operation_offer_count,
        'deleted_service_offers', deleted_service_offer_count,
        'deleted_rows', deleted_row_count,
        'deleted_materials', deleted_material_count,
        'deleted_supplier_aliases', deleted_alias_count
    );
end;
$$;

revoke all on function public.purge_company_price_source(text, uuid)
from public, anon, authenticated;
grant execute on function public.purge_company_price_source(text, uuid)
to service_role;

commit;
