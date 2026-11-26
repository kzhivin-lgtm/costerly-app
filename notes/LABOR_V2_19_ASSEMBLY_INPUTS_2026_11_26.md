# Labor2.19: shared Project input rules and Assembly scope

Owner approved26November2026, existing work3.17.4.6. Start from the completed
[full2.18 preservation checkpoint](LABOR_V2_18_PRODUCTION_CHECKPOINT_2026_11_26.md),
runtime8b1cc958, separate records0578c583,852 exact source files, byte-identical
independent restore, four offline material controls and120 restored checks.
Records gate45793115519 passed, main/runtime unchanged during preservation.

## Owner-approved before/after

Project fields reuse the shared end-caret helper already used by Object Detail
and Profile. Pointer entry and keyboard focus position the caret at the end,
active edits remain untouched by older queued-write reconciliation. This fixes
an existing unconditional seedQuantitiesFromDom write revealed by rapid edits
(4 then5 became54 during the focused replay). No new writer, listener, timer,
polling or rerun is introduced; the current event handler is extended.
Days remain positive whole numbers; fractional paste is rejected rather than
being converted from12.5 to125. Empty/active day text remains centered through
ordinary block text alignment, same42px editor box and122px service width.

Rows reserve the same two-line helper region and133px minimum divider interval,
including rows without a description. Existing field axes, font sizes, Price/
VAT/Total styling,48 outside-boundary probes and financial values remain.
Longer content may grow naturally, never clipped. Helper/material descriptions
render lowercase, headings/proper names and stored business data are preserved.
Long Project names wrap as a separate name below Project; its mark stays with
Project on the first line. No rename, identity or Detection changes.

Additional Assembly uses the already saved Parts evidence: one owner-provisional
hour per finished glass box (lid identifies one complete assembly), mirror and
physical LED zone. Glass walls, stock pieces, lengths and purchase rolls are not
separate assembly units. Quantity/scope repeats and source identity are retained;
unknown/conflicting quantities remain explicit in the audit. Owner specifically
chose four physical LED zones rather than two3000/4000K material types.
Saved Ada replay: Console one mirror+one LED=2h; Corner eight boxes+two mirrors+
four LED zones=14h. No new model call or material-price change.

Hardware Fitting separates operations already in Block Assembly,
not additional charges: hinges/plates, door/front fitting, drawer runners and
adjustment, drawer-front fitting, pull-out runners/checks, lift mechanisms and
push catches. CNC boring remains Sheet Processing. Source operations and norms
are unchanged. Structural+hardware hours equal the old total; payroll retains
its once-only rounding with a residual allocated to hardware. Legacy assembly
manual budgets distribute across their old shares. New terminal keys
block-assembly and hardware-fitting supersede only their share, using the same
saved labor-hours rows/validation/receipts. No schema migration. Additional
Assembly keeps its existing key and manual0 support. Exact combined hours feed
Labor, Management/Overhead, Self Cost and Project once, through the current path.

## Hardware scope and time research

Blum's [CLIP top assembly](https://www.blum.com/eu/en/products/hingesystems/clip-top-blumotion/assembly/)
distinguishes hinge fixing, door attachment and three-dimensional adjustment.
Hettich's [Quadro documentation](https://www.hettich.com/en-in/products/runner-systems/quadro)
distinguishes runner mounting, drawer attachment and front alignment. Neither
page supplies a universal labor-minute norm. Blum's
[MINIPRESS description](https://d2.blum.com/services/BEC003/cme200211_ep_dok_bus_%24sen-us_%24aof_%24v1.pdf)
describes highly mechanized boring/insertion and fast front attachment, so those
machine cycle claims cannot stand for a complete manual fitting operation.

A firsthand [WOODWEB shop timing report](https://www.woodweb.com/knowledge_base/Cabinetmaking_Productivity.html)
reports8min attaching slides to four drawers, plus a separate8min fitting slides
to the case. It is one historical shop/process measurement, not a market standard
or a complete adjustment allowance. It supports separating the task boundaries,
not importing a universal number into this release.

For2.19 reuse the existing internal active norms: hinge/plate2min each, door
hanging/alignment5min, drawer slide pair6min installation+5min adjustment,
drawer front5min, pull-out shelf/slide pair6min+1min travel check, lift kit8min+
front5min, push latch3min. Existing planned-time factor1.25/0.80 remains. These
are internal model norms, not externally validated industry standards. Owner
can replace/calibrate them later; this release changes only their grouping.

Owner explicitly accepted26November2026: hinge/plate2min plus door hanging and
adjustment5min per door; one drawer's complete slide pair6min installation+
5min adjustment, plus drawer front5min separately. These are active-work norms;
the existing planning factor remains unchanged, and the details distinguish
active and planned time.

## Project input regression evidence

Two candidate GitHub gates rejected the unchanged failed-save quantity check:
the requested6 became65. A deterministic local Project regression then proved
that deferred price-blur cleanup cleared a selection already made in the next
active quantity input. It failed before the repair with empty selection instead
of5. Restrict the existing cleanup to its originating field, preserving any new
active editor and its selection. No new timer or write path is added. Retain all
original delayed-write, failure/retry and Review/Back assertions.

## Verification and publication

Protected: all four Labor roots, terminal0/unknown/manual override semantics,
source-scoped materials/coating, commercial-copy invariance, exact Overhead
hours, Management once, Save/Review/Back/reopen/retry/auth, fixed Privacy,
continuous covered navigation, protocol and version deferral during work.
APPROVE latency and Profile redesign are explicitly deferred by the owner.

Before publication require full Python/ten-browser local evidence, full exact-SHA
GitHub UI release gate, actual strict/no-bypass main rule, normal publisher and
matching executed Core/wrapper/meta/version. Synthetic screenshots are separate
from owner acceptance.

## Published release and evidence

[verified] Labor2.19 runtime1aa19ed48faf7a9f9c7bc6c12bf254156b5a683a published
26November2026 through tools/promote_ui_release.py after its exact-SHA full
[GitHub gate](https://github.com/kzhivin-lgtm/costerly-app/actions/runs/45801323099)
passed1068 Python checks and all ten browser suites in451.532s. Job139844977195,
artifact15108341106, SHA256
7161bee81732c6c2ee91f940f3f11649e5554286fc98991a3032880b14088851.
ZIP downloaded, digest/status/clean exact commit verified. Both earlier rejected
gates45797225623 and45798125779 remain failed records, never published.

Local verification is composite, not one clean full-run claim: initial1068,
Navigation88.027s and Calculation101.814s; then remaining eight browser suites
262.880s on runtime-identical source; after the isolated blur repair, all1068
Python checks17.780s and full Project suite26.911s passed. New selection regression
failed before the repair, empty selection versus5, and passed afterward. The
remote gate is fresh/full on the exact final runtime, including every old check.

[verified] Publisher independently enforced actual ruleset27499066, active and
strict with no bypass actors. Remote main equals the runtime SHA. Core deployment
status reports success. Browser witness10:37:05.304UTC confirms actual Core,
executed wrapper, wrapper meta and uncached version.json all equal
labor-v2.19-b20261126094310-assembly-inputs-detection-v8.4.29, zero exceptions.
This anonymous build witness is separate from authenticated owner acceptance.

Private evidence: output/labor-v2.19-20261126, including saved Ada source replay,
full CI ZIP/report, remote-enforcement and live-build receipts. No paid model
call or production estimate mutation. Full2.18 checkpoint remains immutable;
rollback8b1cc958 through the same gated publisher. APPROVE performance and
Profile redesign remain owner-deferred. Owner explicitly requested no repeat
deployment after asking for the release summary; final records stay on the
working branch, without advancing main again.
