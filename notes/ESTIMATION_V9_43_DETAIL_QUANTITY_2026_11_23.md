# Estimation 9.43 Quantity handoff and opaque material status

Status: published23November2026, owner authenticated production acceptance pending.
Existing work3.17.4.6 and Objects workflow. No new work block.

## Owner report and preserved baseline

The owner partially accepted9.42: VAT18% and commercial price edits work, but a
quantity edited on Objects sometimes opens incorrectly in Object Detail. The
Changing material text overlaps the visible table. Scope is to repair these two
issues and publish9.43, retaining accepted interactions and costing. Runtime
185e3c02, recordsed056df3 and estimation-v9.42-2026-11-23 remain preserved. The
full9.41 checkpoint and independent V3.3 rollback are unchanged.

## Confirmed mechanisms and repairs

The old quantity test asserted the list after Back, not inside the card. A new
negative control on unchanged9.42 application code saves2 but the warm card
shows1. Cached snapshots and completed prefetch results had no canonical
quantity validation. Cold loads read the new value, explaining the variability.

Review now marks one quantity check for the target card. A warm snapshot gets
one access-checked projection selecting quantity for its estimate/object. An
unchanged snapshot is reused. A mismatching cached or completed-prefetched card
is discarded and only that target is loaded through the existing detail loader.
A running prefetch still uses the existing cancellation/fallback. Editing
rerenders do not repeat the check; unrelated cards remain cached. Read failure
uses the existing error/Back path and retains the check, never exposing the
old quantity on a later rerender. A direct cold load keeps its original reads.

A second negative control, after cache repair alone, uses keyboard Review while
a500ms quantity RPC is pending. The card shows2 instead of requested3. The
existing click guard now waits for that target object's quantity write before
Review. It does not wait for Delivery, Installation or another object's writes.
Set Prices/Generate continue waiting for their estimate's outstanding writes.
Quantity writes execute in the persistent Core realm, are authenticated,
estimate/object scoped, ordered per field and keepalive. A delayed older edit
cannot overwrite a newer one. A rejected write retains the requested value and
retry on blur, including the existing blank-on-focus case. Navigation cannot
claim a rejected quantity was saved. No new callback, worker, observer, timer,
polling or full estimation/model restart is added.

The existing material status keeps its lifecycle and shared typography but now
uses the opaque shared loading background#f1efef. There is one full-viewport
status, no white card/border/shadow and no underlying table text visible.
Queued choices, Save/APPROVE, focus and error/timeout cleanup remain unchanged.

## Verification and diagnostic history

Focused Objects with production prefetch enabled passed21.595s: warm card
increase/decrease, keyboard Review during a pending write, delayed older edit,
HTTP503/retained value/rejected Review/retry, original service prices, saved
reopen, approval and proposal. Calculation passed48.485s at1280/390, including
opaque-cover screenshots and all previous material-status cases.29 focused
Python checks pass, including stale cache/completed-prefetch, unchanged cache,
no per-edit revalidation, access rejection and repeated read failure.

Actual saved Lev2 quantity projection, guarded against every non-GET/HEAD, takes
0.804s, one read,0 writes. This measures the projection, not authenticated live
navigation latency. All57 pre-existing Estimation definitions are AST-identical
to9.42;609 other non-Markdown source files are byte-identical. Recognition,
geometry, Material Engine, Labor and the workflow Loading controller are intact.

Private evidence is underoutputs/estimation-v9.43 in the handoff workspace.
Keep baseline-detail-quantity and baseline-pending-quantity expected failures,
quantity-cache-fix and focused-objects proposal-assertion failures, and the
focused-objects-complete retry-edge failure. The two proposal assertions sampled
the outgoing enabled button between the table's completed-stage delta and the
native footer's completed delta. Captured final state was disabled in both;
source emits the table before the footer. The unchanged disabled assertion now
waits for the actual completed native footer key within1s. No application
proposal behavior, original assertion or existing deadline was relaxed.
The rejected retry test exposed blank-on-focus returning before retry; the
retained failed quantity now supplies the value when that field blurs empty.
Passing final report: focused-objects-retry. Full local/CI gates remain required.

No paid model run or production-project write for verification. Headless live
build verification is distinct from owner authenticated production acceptance.
Build: estimation-v9.43-b20261123085100-ui-objects-v2.7-detection-v8.4.29.

## Verified publication

Runtime d41eb1275c400788e374b20fc26a9e9571d2ca17, release tag
estimation-v9.43-2026-11-23. Clean exact-SHA local572 checks/nine suites passed
311.441s. Exact-SHA GitHub572/nine passed291.807s: run45143227565,
job137586097801, artifact14803087675, fully retained inci-d41eb127.

Protected publisher verified the exact trusted check and active no-bypass
ruleset27499066, then advanced main from185e3c02 without force. Core deployment
7994630091 succeeded09:10:31UTC. Actual executable Core/wrapper/meta/version
all match9.43 at09:13:40UTC, health/wrapperHTTP200. Live browser was headless
and anonymous Login; it proves build identity, not owner-project acceptance.

Source archive817 files/4,680,899bytes, every byte/CRC verified, SHA256
f17966d5e64601d697a08ae4da58b075fb07127eee827243fbafb2e66d1b339b.
Private receipt: quantity-cover-candidate-backup.json underoutputs/estimation-v9.43.
No failed candidate was published; all diagnostic failures remain retained.
No paid model run or production-project write for verification. Keep9.42,
full9.41 checkpoint and V3.3 rollback. Owner next: edit quantity, blur, Review,
check card quantity, Back and repeat with another value; inspect the opaque
Changing material status on the same saved calculation. This is a verified
release, not an owner-accepted full checkpoint or recognition-stability claim.
