# Estimation V4.29 navigation and Object Detail implementation checkpoint

Date: 2026-11-03  
Work: `3.17.4.3`, Object-to-Estimate and approximate BOM foundation  
Status: published implementation checkpoint, not owner-accepted production checkpoint

## Boundary

This record protects the V4.27-V4.29 baseline while production interaction
evidence is still collected. It covers only Profile formula allowances, File
Review/New Estimate/Object Detail navigation, and Object Detail read latency.
It does not claim an accepted general BOM, material family selection, or
assembly completeness. Detection object boundaries, locked identity and the
immutable `estimation_input_v4` contract are unchanged. No Detection benchmark
is updated by this checkpoint.

## Published runtime baseline

| Release | Runtime commit | Documentation commit | Runtime scope |
| --- | --- | --- | --- |
| V4.27 | `80e71f0` | `6adfd8a` | Restore Profile-owned formula material allowances |
| V4.28 | `4e87892` | `5f683b2` | Repair workflow transitions and warm Object Detail reads |
| V4.29 | `f891e56` | `771a0f9` | Recover New Estimate from a dead native callback |

Before creating this record, the implementation worktree
`/private/tmp/costerly-estimation-v425` was clean and the commits above were
pushed to `origin/main`. This documentation record must itself be committed and
pushed before it can be called published. The numbering authority is
`notes/ESTIMATION_V4_RELEASE_SEQUENCE_2026_11_02.md`; next Estimation runtime
release is V4.30, not a Detection V6 number.

## Production diagnosis that motivated V4.29

[verified] Production trace `f232f994-ca20-4283-87f0-8c5aac30b892` showed a
browser-to-Streamlit callback failure, not merely a slow request:

* `2026-11-03T08:36:20.028Z`: `browser.transition_click`, `new_estimate`;
* `2026-11-03T08:36:35.029Z`: `browser.transition_timeout`, `new_estimate`,
  `python_runs=0`;
* two later clicks produced visual `transition_styled` events but no Python
  rerun and no real Upload `app-ready` after `08:05:23Z`.

A retained Upload-looking DOM marker is therefore not proof of state reset.
Caching server work cannot repair a transition that never reached Python.

The same trace also contains an `objects_to_object_detail` click at
`08:07:33.442Z`, followed by 10-second and 15-second client timeouts with
`python_runs=0`. That proves this browser instance could fail before Python for
both routes. It does not prove every historically slow Review request was a
dead callback, so V4.28 separately improves server-side detail reads.

An earlier fresh production run, `run_3784615ddf16496581ca108c8b1fdcf1`, did
reach File Review. It displayed new object cards but lacked terminal action
buttons. That is a File Review render-order defect, not an estimation result.

## V4.27, formula material allowances

The user restored three Profile → Pricing Cost formula lines:

| Row | Formula basis |
| --- | --- |
| Consumables | Saved percentage of primary physical material cost |
| Packaging | Saved percentage of primary physical material cost |
| Paint consumables | Saved percentage of coating material cost only |

They are locked formula allowances after the physical Material Plan. They are
not C/I/A catalog materials, do not receive purchase units, and are not
editable. Material-plan changes recalculate them from Profile settings.

[verified] Focused V4.27 tests passed before publication.  
[unknown] A new authenticated production Object Detail witness showing all
three rows and saved percentages has not been captured.

## V4.28, File Review and Object Detail read path

### File Review action ordering

`screens/file_review.py` now renders terminal controls before
`_poll_file_review_deferred_work(run_id)` can start a rerun. This protects
`Back to Upload` and `Continue to Objects Estimation` from disappearing when a
new upload becomes terminal. A real production witness is still required.

### Object Detail data path

V4.28 does not alter BOM or resolver semantics. It reduces an avoidable serial
read chain:

* `use_cases/estimation.py::load_object_detail_data` authorizes before reads;
* independent object-estimate, estimate-lines, and Material Plan reads run in a
  bounded three-worker executor;
* material facts and company settings run concurrently in a bounded two-worker
  executor;
* `use_cases/object_detail_runtime.py` exposes a bounded, read-only prefetch;
* `screens/objects.py` schedules it only after Objects is visible, only for
  terminal-ready objects, and never blocks Objects;
* `screens/object_detail.py` consumes a matching snapshot or falls back to the
  ordinary authorized read;
* `state/session.py` invalidates exact estimate snapshots and futures after an
  edit, approval, recalculation, terminal completion, or New Estimate.

The prefetch is advisory. It cannot bypass authorization, and failed/missing
prefetch falls back to the normal read. It should improve first Review latency,
but cached data must never survive an edit.

[verified] 20 targeted V4.28 checks passed. A wider route/detail selection had
71 passes. Two failures are pre-existing stale static expectations, outside
this release: one expects obsolete `routeKeys` text with `profile_tab`; the
other expects removed `RFQ_UPLOAD_CYCLE_ID_KEY` text. `py_compile` and
`git diff --check` passed. A JavaScript parser could not run because Node is
not locally installed; that is a verification gap, not a JavaScript failure.

## V4.29, dead New Estimate callback recovery

`cloudflare/index.html` now implements this bounded path:

1. On New Estimate, outer `window.history.replaceState` immediately removes
   workflow route parameters and sets the outer route to `/`.
2. It emits `browser.new_estimate_route_cleared` with bounded `outer_path`.
3. The native Streamlit callback remains the preferred reset mechanism. The
   transition stays pending through visual stage signals.
4. Only a matching, real Upload `app-ready` counts as server-ready and clears
   transition timers.
5. If no matching server result arrives after
   `NEW_ESTIMATE_SERVER_GRACE_MS = 900`, the wrapper removes workflow route
   keys from the iframe URL, sets `screen=upload`, and replaces only the stale
   iframe via `frame.src`.

The recovery uses `frame.src`, not `data-src`, because `data-src` omitted
`obs_trace`; a recovered iframe's `app-ready` would otherwise be ignored as a
different trace. That defect was caught and corrected before publication.

The fallback preserves auth and the outer shell. It makes a clean Streamlit
workflow session only when the normal callback demonstrably failed. It never
uses a visual Upload marker as success.

[verified] V4.29 focused checks: 3 passed. They cover outer-route clear and
dead-callback recovery, clearing all estimate-scoped session values, and
running header reset before page render.

[verified] After publication, the public wrapper served the V4.29 code markers:
`NEW_ESTIMATE_SERVER_GRACE_MS`, route replacement,
`browser.new_estimate_route_cleared`, and clean-iframe recovery.

[unknown] No authenticated user interaction has yet verified V4.29. The user
needs one normal browser refresh to load the new wrapper script. The outer
wrapper's visible build literal remained `3.12.1-r2`, so it is not release
proof; code markers and trace are the proof.

## Protected Estimation contracts

Estimation V4 is currently material-only. Labor, manufacturing, overhead,
markup and selling price remain separate deterministic layers.

Resolver authority is fixed: Company Catalog (`C`), Israel Reference (`I`),
then priced Assumption Fallback (`A`). Every demand must receive a price. An A
is explanatory uncertainty, never a review gate or customer-facing failure.
C/I material names are strict normalized catalog names, not model assembly
labels. A can create a future deduplicated Catalog Gap Job.

A finished part longer than a catalogue sheet cannot disqualify a C/I material:
it may be joined in production, and drawing dimensions may represent a composed
span. Purchase planning aggregates compatible demand estimate-wide, applies
bounded offcut, then rounds whole purchasable units. It is not a one-finished-
panel-to-one-sheet fit gate.

Object Detail must display one Materials table only: marker and material name,
editable Required Material including unit, Purchase Unit, editable Purchase
Quantity without repeated unit, and derived read-only Total. `Elements` is a
collapsed structural list, not a second cost allocation. User-visible terms
`Project Material Plan`, `Project Allocation`, `Cabinet Carcass`, and `Cabinet
Facade` are forbidden in that table. Shown legs/hardware are pieces, not
implicit sets; generic hidden connectors are outside current scope.

## Acceptance scenario, still required

After one ordinary browser refresh, run one continuous production scenario:

1. Start on a completed estimate/object route and press `New Estimate` once.
2. Confirm the address becomes `/` immediately and Upload is actionable.
3. Upload a small file. At terminal File Review confirm both `Back to Upload`
   and `Continue to Objects Estimation` are visible.
4. Press `Last Estimate`, confirm it restores the expected latest completed
   File Review rather than a stale route.
5. Continue to Objects, open Review twice, and compare visible latency.
6. Edit an allowed material input, save/recalculate, reopen Review, and confirm
   no stale cache value remains.

For the trace require click, `browser.new_estimate_route_cleared` with `/`, a
matching real Upload app-ready and Python run or named iframe recovery followed
by it, and no `browser.transition_timeout`. Preserve trace ID, timestamps,
route and screenshot on failure. Do not add another cache/UI workaround before
reading those facts.

## Known non-acceptance risks

* Assembly/BOM can still lose shown details or select implausible material
  families. Navigation work does not repair that.
* `Lev_1.pdf` previously lost legs and misinterpreted structural parts. A
  terminal material cost is not acceptance.
* Technical terminal run `run_d82f58af38f84a4eb6fc3a2dbb8faeab` proves cycle
  mechanics, not sourcing quality. Its Veneered MDF, LDSP and Hardboard lines
  were A fallbacks for resolver reasons corrected in V4.25.
* Formula allowances, File Review action order, and V4.29 recovery each need a
  fresh authenticated production witness.

## Related records

* `notes/ESTIMATION_V4_RELEASE_SEQUENCE_2026_11_02.md`
* `notes/ESTIMATION_3_17_4_3_OBJECT_TO_ESTIMATE_BOM_PLAN_2026_11_02.md`
* `notes/ESTIMATION_V4_24_TERMINAL_CYCLE_CHECKPOINT_2026_11_02.md`
* `notes/ESTIMATION_V4_29_FULL_CHAT_HANDOFF_2026_11_03.md`
* `notes/TODO.md`
* `notes/DONE_LOG.md`
