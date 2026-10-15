-- Defaults now select an Israel Reference position directly. The historical
-- pricing-identity anchor is retired and must not remain a required second
-- path for the same default.
--
-- Run after 2026_10_15_defaults_add_israel_model_anchor.sql and before
-- 2026_10_15_apply_approved_default_positions_part_1.sql.

begin;

alter table public.reference_material_family_default_variants
    drop column if exists reference_pricing_identity_id;

commit;
