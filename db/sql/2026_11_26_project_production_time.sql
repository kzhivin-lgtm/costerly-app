-- Labor 2.18: one commercial term on the existing acknowledged override path
-- No existing values, RLS policies, grants, prices or object rows are changed
begin;
alter table public.rfq_estimate_pricing_overrides
  drop constraint if exists rfq_estimate_pricing_overrides_field_check;
alter table public.rfq_estimate_pricing_overrides
  add constraint rfq_estimate_pricing_overrides_field_check
  check (field in ('sale_price_unit', 'production_time_working_days'));
alter table public.rfq_estimate_pricing_overrides
  drop constraint if exists rfq_estimate_production_time_check;
alter table public.rfq_estimate_pricing_overrides
  add constraint rfq_estimate_production_time_check check (
    field <> 'production_time_working_days'
    or (object_key = '__project__' and value > 0 and value = trunc(value))
  );
commit;
