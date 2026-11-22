# Estimation 9.42 Objects input persistence and UI polish

Status: published23November2026 Israel (22NovemberUTC), owner authenticated
production acceptance pending.
Existing work3.17.4.6 and Objects workflow. No new work block.

## Approved outcome and preserved checkpoint

The owner requested a full9.41 checkpoint first, then three UI corrections.
That preservation is complete: runtime077264c0, records723986b5, remote runtime/
records tags,814-file byte-identical independent restore,563 Python checks and
all four network-blocked material-control replays passed. Archive manifest422
files is verified. The [checkpoint](ESTIMATION_V9_41_PRODUCTION_CHECKPOINT_2026_11_22.md)
remains the independent rollback, including its known issues and failed evidence.

On Objects Estimation, Delivery, Installation, object Sale Price and quantity
save when leaving the input. Set Prices is not a save prerequisite; it retains
its separate confirmation role. Saved values survive Review/Back, reload and
reopening. Object Detail Material/Labor Save and Leave without saving stay
explicit. Changing material uses the shared loading typography without its
white card. Integral VAT labels show18%, while18.5% stays fractional.

## Confirmed causes and bounded repair

The original9.41 negative control completed a Delivery123 write and returned
through Review/Back without Set Prices, but displayed cached39. The previous
test used Approve, which refreshed that snapshot and missed ordinary Back.
The repaired return refresh reads only saved commercial inputs and totals.
It does not rebuild costs, Material Plan, Parts, Labor or catalog demand.

A separate delayed-write test found promises remaining pending after the
Streamlit installer iframe was removed on navigation. Serialization inside
that disposable iframe still failed. The existing editor now executes in the
persistent Core document, so its event handlers and in-flight promises survive
component removal. No new worker, polling, timer or observer is introduced.
Writes remain authenticated and estimate/object scoped, use HTTP acceptance,
keepalive and per-field ordering. The latest edit wins. A failed field retains
its actionable value/error and retries on blur. Set Prices/Generate waits only
for the estimate's outstanding price writes, with truthful aria-busy state.
Quantity retains the existing authenticated RPC and blur trigger.

Returning to Objects marks only commercial data stale. Refresh reuses existing
pricing arithmetic and makes three reads; an actual saved Lev2 guarded read
passed in1.201s,0 writes. The previous full-cache approach was rejected because
it could enter full cost repair; its attempted write was blocked before send.
Existing material-save/worker full-dirty paths still take their original full
refresh. All56 pre-existing functions/classes in use_cases/estimation.py are
AST-identical to9.41; only the narrow refresh function is added.608 other
non-Markdown source files are byte-identical, including recognition, geometry,
Material Engine, Labor and the accepted workflow Loading controller.

## Verification and retained failures

Focused Objects UI passed19.867s, Calculation52.246s at1280/390px. New cases cover
blur without Set Prices, completed and500ms writes during Review/Back, HTTP503
and retry, rapid delayed edits, confirmation after accepted writes, quantity
navigation and saved-state reopen in a new narrow browser context. Existing
48 field-boundary, geometry, authorization, proposal and confirmation assertions
remain. Calculation compares actual computed status typography and transparent
card-free styling, preserving success/error/timeout/queued choice/Save cases.
Focused Python hierarchy/workflow tests passed24, including integral/fractional
VAT, cache boundary and a strict no-cost/no-material-rebuild commercial refresh.

Private evidence: outputs/estimation-v9.42 under the handoff workspace. Keep
baseline-persistence-correct-entry (expected old-code failure), initial invalid
baseline setup, focused-objects failure, diagnostic pending promises, failed
iframe-serialization attempt and all passing Core-realm/scoped reports. The
initial fresh-context reopen setup was corrected to Last Estimate/Continue;
it had remained on Upload, so that attempt was invalid, not product success.
No assertion or deadline was weakened. No model calls or production-project
write were used for verification. Full exact-SHA local/CI and actual served
Core/wrapper verification are required before publication. Authenticated owner
production acceptance remains separate; do not infer fresh recognition stability.

Build: estimation-v9.42-b20261122214041-ui-objects-v2.7-detection-v8.4.29.

## Verified release

Runtime185e3c02bc1415858a91f1861a85e72ad17cab7b, release tag
estimation-v9.42-2026-11-23. Candidate was committed on a clean feature branch;
all existing checks and deadlines remained mandatory.

- Clean exact-SHA local567 Python checks/nine browser suites passed308.639s.
- Exact-SHA GitHub567/nine passed287.013s, run45074429235,
  job137368371686, artifact14774991352. Full logs and reports retained in
  ci-185e3c02; no failing candidate was published.
- Protected publisher verified the exact trusted success and active no-bypass
  ruleset27499066, then advanced main from077264c0 without force.
- Core deployment7985667441 succeeded21:59:16UTC22November. Actual executable
  Core/wrapper/meta/version all matched9.42 at21:59:55UTC; health/wrapperHTTP200.
- Source archive816 files/4,673,767bytes, every source byte/CRC verified, SHA256
  0f32837c24aace0b5b334b15b37175708edb83b7bfde51bb9ed8b8a55ab5f51c.
  Receipt ui-blur-persistence-candidate-backup.json underoutputs/estimation-v9.42.

No paid model call or production-project edit was used for verification.
The live check observed anonymous Login and proves served-build identity;
owner authenticated Delivery/Installation edit → Review → Back remains the
production acceptance step. Full local UI uses authenticated synthetic data.
Do not turn these checks into a claim of fresh recognition stability. The9.41
full checkpoint, V3.3 rollback and all prior UI gates remain preserved.
