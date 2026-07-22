-- Split the legacy combined partner/client value without breaking old app versions.

alter table public.rfq_runs
    add column if not exists design_partner text not null default 'unknown',
    add column if not exists client text not null default 'unknown';

-- Existing combined values represented the design partner when one was present,
-- or the direct client otherwise. Preserve them as partner candidates for review.
update public.rfq_runs
set design_partner = client_or_design_partner
where coalesce(nullif(trim(design_partner), ''), 'unknown') = 'unknown'
  and coalesce(nullif(trim(client_or_design_partner), ''), 'unknown') <> 'unknown';

comment on column public.rfq_runs.design_partner is
    'Design studio, architect, designer, contractor, or intermediary issuing the RFQ.';

comment on column public.rfq_runs.client is
    'End client, owner, operator, or developer for whom the project is delivered.';
