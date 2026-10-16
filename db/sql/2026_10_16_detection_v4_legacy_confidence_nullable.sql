-- Detection V4 deliberately has no model confidence field. A confidence value
-- would be an unsupported numeric proxy, so legacy rows may retain it but new
-- V4 rows must be persisted without one.

alter table public.rfq_detected_objects
    alter column confidence drop not null;
