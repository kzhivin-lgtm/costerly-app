alter table public.company_suppliers
    add column if not exists supplier_hp text;

create unique index if not exists company_suppliers_company_hp_uidx
    on public.company_suppliers (company_id, supplier_hp)
    where supplier_hp is not null and length(trim(supplier_hp)) > 0;
