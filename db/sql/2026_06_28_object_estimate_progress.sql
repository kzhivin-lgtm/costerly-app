-- Persist object-estimation progress checkpoints so UI state survives reruns,
-- navigation, reconnects, and Streamlit process restarts.

alter table public.rfq_object_estimates
    add column if not exists progress_percent integer not null default 0,
    add column if not exists progress_label text not null default 'pending',
    add column if not exists progress_updated_at timestamptz not null default now();

alter table public.rfq_object_estimates
    drop constraint if exists rfq_object_estimates_progress_percent_check;

alter table public.rfq_object_estimates
    add constraint rfq_object_estimates_progress_percent_check
        check (progress_percent >= 0 and progress_percent <= 100);
