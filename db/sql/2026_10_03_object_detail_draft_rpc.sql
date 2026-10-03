-- Persist browser-side Object Detail drafts without forcing an intermediate
-- Streamlit component rerun. The existing server callback consumes the draft
-- and performs the authoritative recalculation in one navigation rerun.

create table if not exists public.rfq_object_detail_drafts (
    user_id uuid not null,
    company_id text not null,
    estimate_id text not null references public.rfq_estimates(estimate_id) on delete cascade,
    run_id text not null references public.rfq_runs(run_id) on delete cascade,
    object_id text not null,
    edits jsonb not null default '[]'::jsonb,
    updated_at timestamptz not null default now(),
    primary key (user_id, estimate_id, object_id)
);

alter table public.rfq_object_detail_drafts enable row level security;
revoke all on public.rfq_object_detail_drafts from anon, authenticated;

create or replace function public.save_rfq_object_detail_draft(
    p_estimate_id text,
    p_run_id text,
    p_object_id text,
    p_edits jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id uuid := auth.uid();
    v_company_id text;
begin
    if v_user_id is null then raise exception 'Authentication required'; end if;
    if jsonb_typeof(coalesce(p_edits, '[]'::jsonb)) <> 'array' then
        raise exception 'Draft edits must be an array';
    end if;
    select e.company_id into v_company_id
    from public.rfq_estimates e
    join public.rfq_object_estimates o
      on o.estimate_id = e.estimate_id and o.object_id = p_object_id
    where e.estimate_id = p_estimate_id and e.run_id = p_run_id;
    if v_company_id is null or not exists (
        select 1 from public.company_members m
        where m.company_id = v_company_id and m.user_id = v_user_id
    ) then raise exception 'Object estimate is not available'; end if;

    insert into public.rfq_object_detail_drafts(
        user_id, company_id, estimate_id, run_id, object_id, edits, updated_at
    ) values (
        v_user_id, v_company_id, p_estimate_id, p_run_id, p_object_id,
        coalesce(p_edits, '[]'::jsonb), now()
    ) on conflict (user_id, estimate_id, object_id) do update
      set edits = excluded.edits, run_id = excluded.run_id,
          company_id = excluded.company_id, updated_at = now();
    return jsonb_build_object('saved', true);
end;
$$;

create or replace function public.save_rfq_object_quantity(
    p_estimate_id text,
    p_run_id text,
    p_object_id text,
    p_quantity numeric
) returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user_id uuid := auth.uid();
    v_company_id text;
    v_quantity numeric := round(p_quantity, 3);
begin
    if v_user_id is null then raise exception 'Authentication required'; end if;
    if v_quantity <= 0 or v_quantity > 1000000 then raise exception 'Invalid quantity'; end if;
    select e.company_id into v_company_id
    from public.rfq_estimates e
    join public.rfq_object_estimates o
      on o.estimate_id = e.estimate_id and o.object_id = p_object_id
    where e.estimate_id = p_estimate_id and e.run_id = p_run_id;
    if v_company_id is null or not exists (
        select 1 from public.company_members m
        where m.company_id = v_company_id and m.user_id = v_user_id
    ) then raise exception 'Object estimate is not available'; end if;

    update public.rfq_object_estimates
    set quantity = v_quantity, approved = false, updated_at = now()
    where estimate_id = p_estimate_id and run_id = p_run_id and object_id = p_object_id;
    update public.rfq_detected_objects
    set quantity = v_quantity
    where run_id = p_run_id and object_id = p_object_id and company_id = v_company_id;
    return jsonb_build_object('quantity', v_quantity);
end;
$$;

revoke all on function public.save_rfq_object_detail_draft(text, text, text, jsonb) from public, anon;
revoke all on function public.save_rfq_object_quantity(text, text, text, numeric) from public, anon;
grant execute on function public.save_rfq_object_detail_draft(text, text, text, jsonb) to authenticated;
grant execute on function public.save_rfq_object_quantity(text, text, text, numeric) to authenticated;
