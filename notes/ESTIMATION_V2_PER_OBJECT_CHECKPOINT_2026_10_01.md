# Estimation v2 per-object checkpoint, 2026-10-01

Task: 3.15.8 Estimation v2 replacement.

## Verified checkpoint

- Production commit: `1c39a60`.
- Estimation publishes each object independently instead of waiting for the
  complete Object Facts batch.
- One failed object does not block previously completed objects or later
  objects.
- Provider commentary around one JSON object is accepted without modifying the
  JSON payload.
- Provider page labels such as `Page 1` are normalized to the persisted source
  preview and recorded as an audit warning.
- Unresolved material, labor, machinery and purchased-component costs use
  explicit audited fallback rules instead of nulling self cost.
- Full regression result: 803 tests passed and `git diff --check` passed.

## Production acceptance run

Run: `run_e10e240a0ebc4688b55399838dc1e86e`.

Estimate: `run_e10e240a0ebc4688b55399838dc1e86e_estimate_20261001114654`.

Completed objects, self cost excluding VAT:

- `object-001`, Wall shelving unit: ILS 2,246.75.
- `object-002`, Metal ottoman: ILS 3,925.66.
- `object-003`, Media storage cabinet: ILS 4,167.62.
- `object-004`, Storage console: ILS 2,853.03.

Successful Object Facts timings and recorded cost:

- `object-001`: 103.477 seconds, 4,481 input tokens, 9,380 output tokens,
  USD 0.154143.
- `object-002`: 143.404 seconds, 4,485 input tokens, 11,327 output tokens,
  USD 0.183360.
- `object-003`: 147.494 seconds, 4,489 input tokens, 13,054 output tokens,
  USD 0.209277.
- `object-004`: 145.363 seconds, 4,481 input tokens, 12,714 output tokens,
  USD 0.204153.

Recorded successful total: USD 0.750933 and 539.738 model seconds for four
objects. Earlier failed provider calls did not preserve real usage, so the
complete experimental cost was higher than the ledger total.

## Protected behavior

- No legacy or canonical-object templates.
- Universal object decomposition.
- Existing File Review, Objects and Object Detail layouts remain unchanged.
- Original-file preview remains source-derived.
- Materials, labor, machinery and overhead remain editable and auditable.
- Delivery and installation remain project-level selling-price additions, not
  self cost.

## Not accepted

This is a correctness and recovery checkpoint, not a production-economics
checkpoint. Current Sonnet Object Facts extraction is too slow and expensive:
approximately USD 0.15-0.21 and 103-147 seconds per object, with 9,380-13,054
output tokens per object.

Do not optimize by removing evidence, material quantities, labor operations or
auditability without a measured comparison. The next experiment must reduce
output size, latency and cost while preserving the four accepted production
results and their editable detail coverage.
