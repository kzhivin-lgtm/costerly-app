# Detection V8.4.6 Candidate Region exception contract, 2026-11-05

## Status

Tested deployment candidate. This record is not an owner-verified Detection
quality checkpoint until a fresh production run of `Lev 2.pdf` completes.

## Protected baseline

The protected production baseline is Detection V8.4.5, commit `4c9ff38`, tag
`detection-v8.4.5-global-batched-assembly-scope-production-2026-11-01`.
V8.4.6 is a narrow Discovery-response contract repair. It does not change
Fusion, Candidate Region generation, Island discovery, classification, Conflict
Resolver, Membership, object assembly, Naming, Estimation, materials, or UI.

## Incident

[verified] `Lev 2.pdf` stopped during Detection with:

```
RFQ processing failed: Detection visual-registry response failed validation:
candidate region exceptions are invalid
```

[verified] The recorded Discovery payload used OCR Source Fact `SF00001` in
`candidate_region_exceptions`. The field is reserved for Candidate Region IDs,
which are named `CR-...`. The final Candidate Region audit correctly rejected
that row, but did so only after downstream work had started.

## Repair

V8.4.6 applies the same bounded ID contract at three layers:

1. Discovery Structured Output receives an enum containing exactly the supplied
   `CR-...` IDs. V6.41 applies this enum separately to every page batch.
2. The Discovery prompt now distinguishes Candidate Region `CR-...` IDs from
   Source Fact `SF...` IDs at both the response definition and recall-check
   instruction.
3. Runtime validates `candidate_region_exceptions` immediately after Discovery
   shape and page-coverage validation, before Conflict Resolver or Membership.
   An invalid response remains a visible validation failure, but it cannot
   spend a downstream provider call before failing.

The final Candidate Region coverage audit reuses the same validator, so valid
responses retain the existing audit semantics.

## Local verification

[verified] Python compilation passed.

[verified] Focused Detection, runtime-observability and regression coverage
passed: `160 passed in 2.11s`.

The added regression supplies the exact invalid form, `SF00001` in
`candidate_region_exceptions`, and proves the runtime raises its V8.4.6
validation error after the first Discovery response. The mocked provider call
count is one, proving Membership Review does not start.

The schema regression also proves the provider-visible schema retains the
allowed `CR-...` enum after Claude compatibility cleanup.

## Production acceptance

After GitHub/Railway and Cloudflare deployment converge on build marker
`detection-v8.4.6-candidate-exception-contract`:

1. Start a fresh `Lev 2.pdf` processing run from `app.costerly.ai`.
2. Confirm Detection passes the prior Candidate Region exception point and
   reaches File Review.
3. Confirm the browser trace has matching wrapper and core build markers.
4. Preserve V8.4.5's accepted kitchen assembly behavior as the protected
   surrounding Detection route.

Only then promote this candidate into `notes/DONE_LOG.md` and create its
production checkpoint tag.
