-- Adds explainability fields required by Estimation Agent v1 contract.
-- Prices, rates, overhead, VAT, and totals remain deterministic engine outputs.

alter table public.rfq_estimate_lines
    add column if not exists catalog_match_query text,
    add column if not exists quantity_basis text,
    add column if not exists hours_basis text,
    add column if not exists evidence_pages text,
    add column if not exists confidence numeric(5, 2),
    add column if not exists notes text,
    add column if not exists needs_price boolean not null default false,
    add column if not exists needs_review boolean not null default false;

create index if not exists rfq_estimate_lines_needs_review_idx
    on public.rfq_estimate_lines(estimate_id, object_id, needs_review);
