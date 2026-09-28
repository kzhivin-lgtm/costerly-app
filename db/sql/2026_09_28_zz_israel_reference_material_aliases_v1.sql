-- 3.15.1 Israel Reference Catalog v1, identity alias foundation.
-- Every material receives three independently addressable names:
-- canonical English, stable technical code, and its Israel market name.
-- Unit conversions and family-term parsing are deliberately not expanded into
-- combinatorial aliases. They belong to deterministic normalization rules.

insert into public.reference_material_aliases (
    material_id, market_code, language_code, alias_text, alias_key,
    alias_kind, exact_identity, confidence
)
select
    m.material_id,
    'IL',
    'en',
    m.canonical_name,
    public.normalize_reference_material_alias(m.canonical_name),
    'canonical',
    true,
    100
from public.reference_materials m
where m.active
on conflict (material_id, market_code, language_code, alias_key) do update set
    alias_text = excluded.alias_text,
    alias_kind = excluded.alias_kind,
    exact_identity = excluded.exact_identity,
    confidence = excluded.confidence,
    active = true,
    updated_at = now();

-- Coverage guard for future identities whose localized profile has not yet
-- been written. It keeps routing complete without pretending that the English
-- fallback is a sourced Hebrew synonym.
insert into public.reference_material_aliases (
    material_id, market_code, language_code, alias_text, alias_key,
    alias_kind, exact_identity, confidence
)
select
    m.material_id,
    'IL',
    'en-IL',
    m.canonical_name,
    public.normalize_reference_material_alias(m.canonical_name),
    'market_name',
    true,
    80
from public.reference_materials m
where m.active
  and not exists (
      select 1
      from public.market_material_profiles p
      where p.material_id = m.material_id
        and p.market_code = 'IL'
        and p.active
  )
on conflict (material_id, market_code, language_code, alias_key) do update set
    alias_text = excluded.alias_text,
    alias_kind = excluded.alias_kind,
    exact_identity = excluded.exact_identity,
    confidence = excluded.confidence,
    active = true,
    updated_at = now();

insert into public.reference_material_aliases (
    material_id, market_code, language_code, alias_text, alias_key,
    alias_kind, exact_identity, confidence
)
select
    m.material_id,
    'IL',
    'zxx',
    m.material_code,
    public.normalize_reference_material_alias(m.material_code),
    'technical_code',
    true,
    100
from public.reference_materials m
where m.active
on conflict (material_id, market_code, language_code, alias_key) do update set
    alias_text = excluded.alias_text,
    alias_kind = excluded.alias_kind,
    exact_identity = excluded.exact_identity,
    confidence = excluded.confidence,
    active = true,
    updated_at = now();

insert into public.reference_material_aliases (
    material_id, market_code, language_code, alias_text, alias_key,
    alias_kind, exact_identity, confidence
)
select
    p.material_id,
    p.market_code,
    p.language_code,
    p.market_name,
    public.normalize_reference_material_alias(p.market_name),
    'market_name',
    true,
    95
from public.market_material_profiles p
join public.reference_materials m on m.material_id = p.material_id
where p.active and m.active and p.market_code = 'IL'
on conflict (material_id, market_code, language_code, alias_key) do update set
    alias_text = excluded.alias_text,
    alias_kind = excluded.alias_kind,
    exact_identity = excluded.exact_identity,
    confidence = excluded.confidence,
    active = true,
    updated_at = now();

-- Deployment audit. This must return zero rows after all Israel price batches
-- and this alias seed have been applied.
select
    m.material_code,
    count(a.alias_id) filter (where a.alias_kind = 'canonical') as canonical_aliases,
    count(a.alias_id) filter (where a.alias_kind = 'technical_code') as technical_aliases,
    count(a.alias_id) filter (where a.alias_kind = 'market_name') as market_aliases
from public.reference_materials m
left join public.reference_material_aliases a
    on a.material_id = m.material_id
   and a.market_code = 'IL'
   and a.active
where m.active
group by m.material_id, m.material_code
having count(a.alias_id) filter (where a.alias_kind = 'canonical') = 0
    or count(a.alias_id) filter (where a.alias_kind = 'technical_code') = 0
    or count(a.alias_id) filter (where a.alias_kind = 'market_name') = 0;

-- Fast path used before any agent call. It is deliberately bounded and returns
-- only exact normalized aliases. Supplier-specific matches rank before global
-- aliases when supplier context is available.
create or replace function public.find_reference_material_alias_matches(
    p_market_code text,
    p_alias_text text,
    p_supplier_name text default null,
    p_limit integer default 5
)
returns table (
    material_id uuid,
    alias_kind text,
    exact_identity boolean,
    confidence numeric
)
language sql
stable
set search_path = public
as $$
    select
        a.material_id,
        a.alias_kind,
        a.exact_identity,
        a.confidence
    from public.reference_material_aliases a
    where a.market_code = p_market_code
      and a.active
      and a.alias_key = public.normalize_reference_material_alias(p_alias_text)
      and (
          p_supplier_name is null
          or a.supplier_name is null
          or lower(a.supplier_name) = lower(p_supplier_name)
      )
    order by
        case
            when p_supplier_name is not null
             and lower(a.supplier_name) = lower(p_supplier_name) then 0
            else 1
        end,
        a.exact_identity desc,
        a.confidence desc,
        a.material_id
    limit least(greatest(p_limit, 1), 5)
$$;

revoke all on function public.find_reference_material_alias_matches(
    text, text, text, integer
) from public, anon, authenticated;
grant execute on function public.find_reference_material_alias_matches(
    text, text, text, integer
) to service_role;
