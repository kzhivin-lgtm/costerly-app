-- Add the Israel Reference position anchor for defaults.
-- The FK uses the normalized storage relation, but runtime calls this opaque
-- identifier a reference position rather than exposing a separate Model term.

begin;

alter table public.reference_material_family_default_variants
    add column if not exists reference_position_id uuid
    references public.reference_material_models(material_model_id);

with seed(family_code, material_model_id) as (
    values
        ('mdf_hdf', 'f20cbefa-ea35-4b7d-bfbe-b8e378b32fc6'::uuid),
        ('plywood', 'c61befe4-229e-4a80-a30e-a712da72e6be'::uuid)
)
update public.reference_material_family_default_variants variant
set reference_position_id = seed.material_model_id,
    updated_at = now()
from seed
join public.reference_material_families family on family.family_code = seed.family_code
where variant.family_id = family.family_id;

do $$
declare
    missing_model integer;
    invalid_anchor integer;
begin
    select count(*) into missing_model
    from public.reference_material_family_default_variants
    where active and reference_position_id is null;
    if missing_model <> 0 then
        raise exception 'Cannot migrate % active defaults without an Israel Reference Model', missing_model;
    end if;

    select count(*) into invalid_anchor
    from public.reference_material_family_default_variants variant
    join public.reference_material_models model
      on model.material_model_id = variant.reference_position_id
    left join public.reference_market_material_listings listing
      on listing.material_model_id = model.material_model_id
     and listing.market_code = 'IL'
     and listing.active
    left join public.reference_market_material_legacy_mappings mapping
      on mapping.material_model_id = model.material_model_id
     and mapping.market_code = 'IL'
     and mapping.classification_status = 'mapped'
    left join public.market_material_model_prices price
      on price.material_id = mapping.legacy_material_id
     and price.market_code = 'IL'
     and price.status = 'active'
     and price.price_scope = 'material_only'
    where variant.active
      and (model.active is not true or listing.market_material_listing_id is null
           or price.model_price_id is null);
    if invalid_anchor <> 0 then
        raise exception 'Default migration found % anchors without active Israel listing and material price', invalid_anchor;
    end if;
end $$;

create index if not exists reference_material_family_default_variants_model_idx
    on public.reference_material_family_default_variants(reference_position_id)
    where active;

commit;
