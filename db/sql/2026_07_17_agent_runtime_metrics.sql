-- Explicit runtime metric for OCR, Detection, Estimation, and full processing laps.
-- Apply manually in Supabase SQL editor. Until then, the app also stores the
-- duration inside raw_usage.duration_seconds for backward compatibility.

alter table public.agent_usage_events
    add column if not exists duration_seconds numeric(12, 3);

create index if not exists agent_usage_events_duration_idx
    on public.agent_usage_events (agent_name, duration_seconds);

update public.agent_usage_events
set duration_seconds = round(
    extract(epoch from (finished_at - started_at))::numeric,
    3
)
where duration_seconds is null
  and started_at is not null
  and finished_at is not null;
