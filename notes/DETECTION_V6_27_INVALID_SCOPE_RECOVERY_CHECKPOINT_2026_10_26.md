# Detection V6.27 invalid optional-scope recovery checkpoint, 2026-10-26

## Status

Owner-protected production checkpoint at commit `e9e8548`, tagged
`detection-v6.27-invalid-scope-recovery-production-2026-10-26`.

Production run `run_62392d84938242cfa7d83b6060e7ce0e` on `V_Stair.pdf`
reproduced the invalid V6.11 optional-scope sidecar after deployment. The
sidecar was rejected and audited without failing the RFQ. The ordinary Registry
path independently published one quantity-one Object containing all five pages
and seven Registry Views.

## Protected behavior

- Invalid optional scope cannot discard Discovery Islands or ordinary Registry
  packages.
- Invalid scope cannot authorize assembly compilation.
- Unknown or malformed scope evidence remains auditable.
- Naming cannot change object identity, quantity, page membership, View
  ownership, or Estimation evidence.
- The ordinary Registry result is valid without requiring the special assembly
  compiler when its own evidence already resolves one object.

## Production evidence

- Full processing cycle: 47.403 seconds.
- Scope scout: `single_assembly_candidate`, 3.964 seconds, $0.013091.
- Registry: 34.385 seconds, $0.052490.
- OCR: five pages, 3.272 seconds, $0.020000.
- Naming: `Stair railing`, 3.048 seconds, $0.011974.
- Final Object: one, quantity one, evidence pages 1 through 5.
- Assembly compiler: not applied, `document_scope_not_confirmed`.

This checkpoint protects failure recovery and the ordinary Registry outcome. It
does not accept the misleading `unknown group` diagnostic, the four-ID witness
limit, or Naming's project-name fallback.
