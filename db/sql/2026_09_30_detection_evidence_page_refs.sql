-- Add physical page addresses without changing the legacy evidence_pages text
-- consumed by File Review and existing Object Detail code.

alter table public.rfq_detected_objects
    add column if not exists evidence_page_refs jsonb not null default '[]'::jsonb
    check (jsonb_typeof(evidence_page_refs) = 'array');
