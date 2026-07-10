-- Store the calculation context for manual sale price overrides.
-- This lets the app tell whether self cost changed after a user manually set
-- the sale price, without guessing from the current formula.

alter table public.rfq_estimate_pricing_overrides
    add column if not exists source_self_cost numeric(14, 2),
    add column if not exists source_suggested_sale_price numeric(14, 2);
