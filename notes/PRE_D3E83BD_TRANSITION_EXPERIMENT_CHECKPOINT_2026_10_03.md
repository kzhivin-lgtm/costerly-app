# Pre-d3e83bd transition experiment checkpoint, 2026-10-03

## Purpose

Preserve the complete current product state before temporarily restoring the
tracked application to `d3e83bd` for an authenticated production timing test.
The experiment asks whether the confirmed Sign Out transition checkpoint also
restores the broader navigation performance observed before later product work.

## Preserved state

- Current application commit before this journal: `e715515`.
- Editable File Review Project, Partner and Client fields from `3dc7a3f`.
- Company Pricing Policy and Machinery draft work.
- Estimation v2, resolver, Labor Engine, pricing and persistence work present at
  `e715515`.
- Recovery commits `41e7098` and `e715515`.
- Protected untracked `.streamlit/`,
  `db/sql/3_15_4_israel_global_catalog_v1_parts/`, and `tmp/` remain in place.

## Production evidence before restore

The latest authenticated traces still showed the destination ready well before
the wrapper timeout:

- Processing to File Review: target ready in 2.830 seconds, timeout in 15.001.
- Objects to File Review: target ready in 2.065 to 2.465 seconds, timeout in
  15.001 to 15.006.
- Last Estimation to File Review: target ready in 2.431 seconds, timeout in
  15.291.
- File Review to Objects: completed in 2.628 to 3.625 seconds.
- Back to Upload: completed in 1.616 seconds.
- Objects to Object Detail: timeout in 15.003 seconds.

This evidence means the pre-restore state is not an accepted performance
checkpoint.

## Recovery archive

Archive:
`backups/v3.15.19_before_d3e83bd_transition_experiment/costerly-app_v3.15.19_before_d3e83bd_transition_experiment_2026-10-03.zip`

- Size: 3,424,298 bytes.
- SHA-256: `a66fd6b01ca086458437d122cd6767928206284adecfccd596cfe4b08264b150`.

Git history remains authoritative. The restore experiment must be committed on
top of `main`; history must not be reset or force-pushed. Returning from the
experiment means reverting the restore commit or restoring the preserved
checkpoint, not reconstructing later work manually.

## Experiment boundary

Restore all tracked files exactly to tree `d3e83bd`, deploy that tree, and run
the authenticated production timing matrix. Do not combine the experiment with
CSS, File Review metadata, pricing, machinery, resolver, or estimation changes.
The protected untracked paths must remain untouched.
