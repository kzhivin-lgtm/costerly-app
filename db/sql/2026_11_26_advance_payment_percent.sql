begin;
alter table public.overhead_settings
    add column if not exists advance_payment_percent integer;
alter table public.overhead_settings
    drop constraint if exists overhead_settings_advance_payment_percent_check;
alter table public.overhead_settings
    add constraint overhead_settings_advance_payment_percent_check
    check (advance_payment_percent between 0 and 100);
commit;
