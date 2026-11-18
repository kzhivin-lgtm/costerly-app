# V2.2.1: Object Detail cost hierarchy

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
