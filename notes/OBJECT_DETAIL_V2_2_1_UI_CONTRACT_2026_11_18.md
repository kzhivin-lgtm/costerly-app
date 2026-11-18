# V2.2.1: Object Detail cost hierarchy

## V2.2.3 owner correction, 18 November 2026

Approved scope: whole-shekel Labor pay, Taxes & social and Total with grouped
thousands; one-decimal editable Hours for the two work rows. Hours stays under
Required material, Total stays under Total. Split Labor pay and Taxes & social
labels over two lines and distribute the middle columns evenly. Remove generic
unfinished-work captions. Preserve the palette, physical norms, SC and ownership.

| Scenario | Acceptance |
| --- | --- |
| New Calculation, delayed shell write | Seed rows remain visible, no estimate ownership read before shell readiness, real foreign estimates still rejected |
| Active Calculation, timer and app reruns, completion | Exactly one pricing table, one launch, no mixed/stale second table |
| Manual Sheet Processing / Assembly hours | Immediate local cost preview at 50/h and 25%; explicit Save persists the accepted override; reopening and quantity changes retain it |
| Invalid or failed save | Zero valid; negative, nonfinite, over-limit and excess precision rejected; actionable draft retained |
| Keyboard, collapse, mobile | Input does not toggle its row; details hierarchy remains; anchored columns, wrapped labels, no changed colors |
| Existing estimate / auth / material edits | Existing full UI contract remains green; no paid run and no automatic inclusion of Labor in SC |

Manual hours use metadata-only rows in the existing estimate-lines store, normalized
per item. Their zero SC contribution preserves the approved separation of this UI
iteration from the pending SC integration. No new schema or production norm changes.
Hours reuses Materials' numeric editor and explicit-save bridge. A native input
with a value in Streamlit Markdown was rejected because React restored its value
on input; browser event/setter tracing confirmed that failure. Clicking Hours
edits the field; the row title/arrow and keyboard summary activation expand details.
Equal column spacing reuses the existing coalesced render/resize alignment guard,
with no extra observer, polling or app rerun. Its existing cleanup also applies.

V2.2.3 local evidence so far:
- 57 focused calculation/cache/runtime tests passed. Full local gate passed:
  368 Python checks and all five browser suites.
- Calculation browser scenario passed at desktop and 390px: delayed durable shell,
  one launch/table through active and terminal full reruns, two editable work rows,
  immediate pay/tax/total preview, failed Save/retry, zero and persisted reopen.
- Frozen Lev1: unchanged exact Labor ILS485.60, displayed ILS486. Original header
  color unchanged, 42px work rows, Hours/Total anchor error 0px. Middle gaps differ
  by less than 0.01px across 1280px/390px viewports.
- The production error's cause is verified from its event/shell timestamps. The
  original duplicate-screen symptom was not replayed on the old runtime. The new
  browser scenario verifies a single stable pricing subtree; the original cause
  remains likely rather than conclusively reproduced.
- Evidence directory: `/Users/qb/Documents/ChatGPT/Costerly/outputs/object-card-v2.2.3/`.
  Exact-SHA CI, publication, matched builds and authenticated acceptance pending.

## V2.2.2 owner correction, 18 November 2026

The owner rejected V2.2.1's large nested cards and changed header appearance.
The correction preserves all amounts and calculations. Existing colors are
protected; no palette change is authorized by a layout revision.

| Corrected scenario | Required result | Verification |
| --- | --- | --- |
| Both sections expanded | One grey header each, using the original single header background layer | Computed style + frozen-card screenshot |
| Labor rows closed | Sheet Processing and Assembly are ordinary white item rows, like material rows, with hours/pay/taxes/total visible | Browser row height and DOM assertions |
| Cross-section alignment | Hours under Required material; Labor pay under Purchase unit; Total in the same final column | Browser cell centers within 1px |
| Different column counts | Taxes & social spans the two remaining middle material columns; no invented fifth metric | Shared CSS grid |
| Work row opened | Only its detail expands inside the row; Elements remains under Sheet Processing | Keyboard + pointer browser checks |
| Materials / Labor collapsed | Only name and Total; desktop Total retains its shared column; narrow Total stays visible | Browser |
| Labels and redundant copy | Labor pay, Total; remove the standalone hourly-rate/payroll sentence | Text assertions |
| Incomplete work | Total header stays stable; unresolved work is disclosed in the detail/review message | Unit + browser |

All earlier input, persistence, navigation, auth and arithmetic scenarios remain
required. Runtime `4e69e5d7d31af140f5ba9fa81668a4196d46c5ee` is published;
owner-authenticated visual acceptance remains pending.

V2.2.2 evidence:

- [Exact-SHA CI](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/44287838603)
  succeeded; whole Linux job 170 seconds. Promotion used the enforced publisher.
- Local: 44 focused checks; 365 Python checks and all four browser suites,
  114.764 seconds. Navigation covers desktop, mobile and an older wrapper.
- Frozen Lev1: original header color matches in the same browser, Hours / Labor
  pay / Total have 0px center difference from Materials, work rows are 42px;
  sheet labor 335.86 + assembly 149.74 = 485.60 ILS, unchanged from V2.2.1.
- Initial local assertions were corrected for browser alpha quantization and
  CSS uppercase text. The standalone frozen renderer was given Streamlit's
  border-box sizing. These were test/renderer issues, not palette changes.
- Core and wrapper observed at
  `estimation-v2.2.2-compact-cost-rows-detection-v8.4.29`. Initial Core lagged
  Pages at V2.2.1; after deployment/reload the pair matched. Authenticated card
  behavior is not claimed accepted from the unauthenticated build check.
- Evidence: `/Users/qb/Documents/ChatGPT/Costerly/outputs/object-card-v2.2.2/`.
- Release tag: `estimation-labor-v2.2.2-2026-11-18`; rollback runtime is V2.2.1,
  `28c5588305b7f57c17ca6b3a92de58c1e0d43d53`. No new paid model call.

Owner-approved scope, 18 November 2026: Materials and Labor are collapsible
cost bands. Labor contains Sheet Processing (including Elements), then
Assembly (including its block/operation breakdown). A collapsed band retains
only its name and Total. No additional paid recognition or SC aggregation.

The owner clarified the test labor policy during implementation: all paid
hours use ILS 50/h; display Pay, Taxes & social (25% of Pay), and Total.
Apply the load once. Sheet purchasing and supplier bundles are not labor.
Display the quantities for the card's current object quantity; keep stored
Parts, Machinery settings, Material Plan, and the existing SC unchanged.

| Scenario / action | Expected visible state | Verification |
| --- | --- | --- |
| Saved card, ready calculations | Materials; Labor > Sheet Processing > Elements; Labor > Assembly > breakdown | HTML structure + browser |
| Toggle any cost band by mouse, Enter or Space | Immediate local collapse/expand; name and Total remain; no request or rerun | Browser, desktop/narrow |
| Materials expanded / collapsed | Single Materials title in the existing grey table header; all existing material inputs and values preserved | HTML + browser |
| Labor ready | Existing paid hours at 50/h, separate 25% load, Total; summary adds the two work blocks only | Arithmetic/route tests |
| CNC / panel saw | Same physical work and route; helper time paid once; materials excluded from Labor | Route tests |
| No sheet work / no assembly work | Zero for confirmed absent work; Elements still available when present | Unit + browser |
| Missing route, unresolved work or quote | Missing/partial amount stays explicit; never manufacture a zero or complete total | Unit + browser |
| Parts or Material Plan loading / wrong revision / read failure | Existing truthful pending/failure message inside the relevant block; ready Assembly remains accessible | Unit + browser |
| Assembly breakdown | Block ownership and operations retained inside Assembly, outside Elements | HTML + browser |
| Material edit valid / invalid / rejected | Existing Enter/blur, validation, pending, server reconciliation and retry retained; no fake success | Protected UI suite + production |
| Quantity edit / saved reopen | Same saved estimate; updated card quantities; no paid model call | Protected UI suite + production |
| Front / Block PDF actions | Retained inside Elements, available after its parents open | Browser |
| Narrow screen / keyboard / repeated toggles | No page overflow or hidden actions; table scrolling remains local; no duplicate writes | Browser |
| Back / Approve / Last Estimate / Profile / expired auth | Existing accepted navigation, persistence, cache and auth contracts unchanged | Full UI contract + production |

Release is a candidate until the owner accepts the production card. Previous
runtime/rollback: V1.3.4, eb56dd4c493607fc43332c6fb4e05a11c0ab324b.

## Publication evidence

- Runtime: `28c5588305b7f57c17ca6b3a92de58c1e0d43d53`.
- Tag: `estimation-labor-v2.2.1-2026-11-18` (release, not owner acceptance).
- Exact-SHA [UI gate](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/44283247089)
  succeeded. Whole Linux job: 169 seconds including setup and artifact work.
- Local: 43 focused checks; 364 full-contract Python checks plus all four
  browser suites in 120.402 seconds. Browser-only rerun after header alignment:
  113.043 seconds. The initial missing-PyYAML environment failure was resolved
  using the pinned 6.0.3 wheel, verified against its lockfile hash.
- Frozen Lev1 and Adda saved revisions replayed without paid model calls.
  Frozen Lev1: Sheet Processing Pay 268.69 + 67.17 = 335.86 ILS;
  Assembly Pay 119.79 + 29.95 = 149.74; Labor Total 485.60. These are saved
  controls, not fresh recognition or shop-time measurements.
- Production wrapper and Core both observed at
  `estimation-v2.2.1-object-card-labor-detection-v8.4.29`, with Sign in visible.
  Cloudflare Pages and UI release gate succeeded. An unrelated legacy Workers
  Builds check was still running; it is not the Pages/Core acceptance signal.
- No authenticated owner session was available. Do not claim the saved
  production card, all error states or the new layout accepted by the owner.
- Validated source archive: 5,232,506 bytes. An earlier attempt exceeded the
  helper's 5 MiB ceiling because generated UI evidence was included; the helper
  rejected/removed that invalid archive. Evidence was preserved outside the
  source tree and the unchanged helper then passed.
- Durable local evidence: `/Users/qb/Documents/ChatGPT/Costerly/outputs/object-card-v2.2.1/`.
