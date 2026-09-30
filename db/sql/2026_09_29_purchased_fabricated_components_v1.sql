-- 3.15.6: economic classification for estimate lines.
--
-- A finished deliverable bought from a subcontractor is a purchased fabricated
-- component for the customer company. It belongs to material cost even when
-- the supplier's invoice mostly represents labour or machine time.

alter table public.rfq_estimate_lines
    add column if not exists economic_classification text,
    add column if not exists price_scope text;

update public.rfq_estimate_lines
set economic_classification = case
        when section = 'material' then 'direct_material'
        when section = 'labor' and source = 'manufacturing_engine'
            then 'in_house_manufacturing'
        when section = 'labor' then 'in_house_labor'
        when section = 'overhead' then 'overhead'
        else economic_classification
    end
where economic_classification is null;

alter table public.rfq_estimate_lines
    drop constraint if exists rfq_estimate_lines_economic_classification_check,
    add constraint rfq_estimate_lines_economic_classification_check check (
        economic_classification is null
        or economic_classification in (
            'direct_material',
            'purchased_fabricated_component',
            'in_house_labor',
            'in_house_manufacturing',
            'overhead'
        )
    ),
    drop constraint if exists rfq_estimate_lines_price_scope_check,
    add constraint rfq_estimate_lines_price_scope_check check (
        price_scope is null
        or price_scope in (
            'material_only',
            'retail_package',
            'trade_package',
            'cut_to_size',
            'fabricated_component',
            'installed_component'
        )
    ),
    drop constraint if exists rfq_estimate_lines_purchased_component_check,
    add constraint rfq_estimate_lines_purchased_component_check check (
        economic_classification <> 'purchased_fabricated_component'
        or (
            section = 'material'
            and price_scope in ('fabricated_component', 'installed_component')
        )
    );

create index if not exists rfq_estimate_lines_economic_classification_idx
    on public.rfq_estimate_lines(
        estimate_id,
        object_id,
        economic_classification,
        sort_order
    );
