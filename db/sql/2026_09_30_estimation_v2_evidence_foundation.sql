-- Estimation v2 Detection handoff. Additive only: existing File Review,
-- Objects and Object Detail tables remain unchanged.

create table if not exists public.rfq_estimation_object_inputs (
    input_id uuid primary key default gen_random_uuid(),
    run_id text not null references public.rfq_runs(run_id) on delete cascade,
    company_id text not null references public.companies(company_id),
    object_id text not null,
    object_input_revision integer not null check (object_input_revision > 0),
    original_file_ref text not null check (
        original_file_ref like 'storage://rfq-estimation-originals/%'
    ),
    original_content_sha256 text not null check (original_content_sha256 ~ '^[0-9a-f]{64}$'),
    original_mime_type text not null,
    original_size_bytes bigint not null check (original_size_bytes > 0),
    ocr_event_id uuid not null references public.agent_usage_events(id),
    contract_version text not null check (contract_version = 'estimation_input_v2'),
    input_payload jsonb not null check (jsonb_typeof(input_payload) = 'object'),
    created_at timestamptz not null default now(),
    unique (run_id, object_id, object_input_revision)
);

create index if not exists rfq_estimation_object_inputs_lookup_idx
    on public.rfq_estimation_object_inputs (company_id, run_id, object_id, object_input_revision desc);

create table if not exists public.rfq_estimation_evidence_artifacts (
    artifact_id uuid primary key default gen_random_uuid(),
    input_id uuid not null references public.rfq_estimation_object_inputs(input_id) on delete cascade,
    page_number integer not null check (page_number > 0),
    source_label text not null,
    artifact_kind text not null check (artifact_kind in ('preview', 'page', 'region')),
    storage_ref text not null check (
        storage_ref like 'storage://rfq-estimation-evidence/%'
    ),
    created_at timestamptz not null default now(),
    unique (input_id, artifact_kind, storage_ref)
);

create index if not exists rfq_estimation_evidence_artifacts_input_idx
    on public.rfq_estimation_evidence_artifacts (input_id, artifact_kind, page_number);

-- Evidence artifacts are written and signed only by the server service role.
-- Authenticated company members may read metadata through this policy.
alter table public.rfq_estimation_object_inputs enable row level security;
alter table public.rfq_estimation_evidence_artifacts enable row level security;

drop policy if exists rfq_estimation_object_inputs_company_member_read
    on public.rfq_estimation_object_inputs;
create policy rfq_estimation_object_inputs_company_member_read
    on public.rfq_estimation_object_inputs
    for select to authenticated
    using (exists (
        select 1 from public.company_members member
        where member.company_id = rfq_estimation_object_inputs.company_id
          and member.user_id = (select auth.uid())
    ));

drop policy if exists rfq_estimation_evidence_artifacts_company_member_read
    on public.rfq_estimation_evidence_artifacts;
create policy rfq_estimation_evidence_artifacts_company_member_read
    on public.rfq_estimation_evidence_artifacts
    for select to authenticated
    using (exists (
        select 1
        from public.rfq_estimation_object_inputs input
        join public.company_members member on member.company_id = input.company_id
        where input.input_id = rfq_estimation_evidence_artifacts.input_id
          and member.user_id = (select auth.uid())
    ));

revoke all on public.rfq_estimation_object_inputs,
    public.rfq_estimation_evidence_artifacts from anon;
grant select on public.rfq_estimation_object_inputs,
    public.rfq_estimation_evidence_artifacts to authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'rfq-estimation-evidence',
    'rfq-estimation-evidence',
    false,
    10485760,
    array['image/webp', 'image/jpeg', 'image/png']::text[]
)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public, file_size_limit)
values ('rfq-estimation-originals', 'rfq-estimation-originals', false, 524288000)
on conflict (id) do nothing;
