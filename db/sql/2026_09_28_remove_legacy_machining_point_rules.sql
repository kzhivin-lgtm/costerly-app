-- 3.15.1 Remove the unused legacy machining-points model.
-- The replacement operation catalog uses explicit setup, throughput, auxiliary,
-- and minimum-time components. Git history remains the rollback record.

drop table if exists public.machining_point_rules;
