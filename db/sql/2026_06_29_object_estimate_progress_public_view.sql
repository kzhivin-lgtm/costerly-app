-- Read-only browser progress endpoint.
-- The Streamlit server writes full estimate rows through the service role key.
-- The browser may only read these progress fields through the anon key.

create or replace view public.rfq_object_estimate_progress_public
with (security_invoker = false) as
select
    estimate_id,
    object_id,
    quantity,
    status,
    self_cost_ex_vat,
    progress_percent,
    progress_label,
    progress_updated_at
from public.rfq_object_estimates;

grant select on public.rfq_object_estimate_progress_public to anon;
