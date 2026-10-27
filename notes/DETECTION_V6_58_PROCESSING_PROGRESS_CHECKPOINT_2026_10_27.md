# Detection V6.58 Processing progress checkpoint

Date: 2026-10-27

Status: owner-accepted live interaction checkpoint for the Processing screen up
to the handoff into File Review. It preserves V6.57's compact ordinary
Discovery contract and V6.58's one-bar progress controller. It does not accept
the brief visual flash during the Processing-to-File-Review transition, which
is separately recorded for repair.

Implementation commits:

- `44e4335`, `fix(detection-v6.57): bound ordinary discovery output`
- `9374888`, `fix(detection-v6.58): stabilize processing progress shell`

## Accepted live witness

On the owner-run ordinary HSL cycle after V6.58:

- Fusion became available after approximately 28 to 45 seconds across runs.
  This variation is expected because the forecast is published only after the
  real Fusion stage signal, not from a fabricated fixed timer.
- The visible bar started from zero, advanced continuously, did not blink,
  reset, or move backwards, and had an acceptable visible pace.
- The forecast marker appeared during Processing and the Processing UI was
  accepted by the owner.

The screenshot recorded before this checkpoint shows a separate handoff
defect: for roughly one frame the outgoing upload shell and incoming File
Review page are visible together. That happens after accepted Processing work
has completed and must not be hidden by changing the accepted bar controller.

## Accepted contract

1. The upload shell is the only visible progress bar for one RFQ cycle.
2. The server-rendered Processing stage is a source of phase, page-count and
   forecast data. Replacing that server subtree cannot replace the visible fill.
3. Progress begins at zero. Before Fusion it advances from page count using a
   bounded zero-origin curve with no hard cap or initial five-percent jump.
4. Once Fusion provides a forecast, its pace governs the full cycle. A real
   stage signal may move the floor forward, but cannot send the bar backwards
   or freeze it at a guessed local phase ceiling.
5. The browser controller is versioned. V6.58 forces one reload on first use
   so a controller that survived a Streamlit deployment cannot remove or write
   the new visible shell.
6. Completion remains owned by the actual File Review payload, not elapsed time.

## Discovery compactness boundary

For ordinary Discovery only, V6.57 derives the response ceiling from Candidate
Region count and gives the model a compact-output system instruction. For the
prior HSL witness with 37 Candidate Regions, the deterministic ceiling is
12,288 tokens instead of the former fixed 8,192. No generic retry, route,
model, Fusion, Membership Review, Evidence or object-boundary change is part
of this checkpoint.

## Post-checkpoint HSL ledger audit

Run `run_99b433940dcc4fd9abbe0587dc56fb12` completed successfully at
2026-10-27 21:15 UTC through `ordinary_haiku`.

- Discovery received 37 Candidate Regions, 1,073 source facts, 11 full-page
  images, 2,177,549 image bytes and 123,572 characters of assembled user
  context. The V6.41 large-document batch route correctly remained inactive:
  its conservative input estimate was 118,860, below the 150,000 single-pass
  boundary.
- The V6.57 deterministic rule calculated `512 + 240 * 37 = 9,392`, above
  the former 8,192 ceiling, and selected 12,288 tokens. Discovery used 7,464
  tokens, or 60.7 percent of that ceiling, completed in 52.577 seconds and
  made exactly one provider call. No truncation retry ran.
- Membership Review used one accepted 6,144-token call, emitted 3,265 tokens
  in 21.776 seconds and had no retry. The resulting registry had 34 visual
  groups, 9 commercial objects, zero unassigned visual groups and exact
  coverage records for all 11 pages.
- Discovery and Review provider time totalled 74.353 seconds. Detection's
  runtime ledger recorded 75.552 seconds, while the full initial Processing
  lap recorded 97.531 seconds, including 10.556 seconds of OCR and framework
  handoff. Naming completed afterwards in the background in 9.255 seconds.
- Provider cost before background Naming was $0.210855: $0.044 OCR plus
  $0.166855 Detection. Naming later added $0.028077.

The compact instruction added 426 system-prompt characters. Its effect on
word-level concision cannot be independently proven from this ledger because
raw model response text is intentionally not persisted. The observed Discovery
output of 7,464 tokens is essentially equal to the nearest pre-V6.57 success
(7,451), so this witness validates safer capacity, not a claim of lower token
use or improved object quality. The 9-object result needs a separate evidence
quality audit before any object-boundary conclusion.

## Verification

- Focused Processing, timing and prompt tests: `95 passed`.
- `py_compile ui/processing_forecast.py ui/js_guards.py screens/processing.py`
  passed.
- `git diff --check` passed before the V6.58 implementation commit.
- Owner performed the live HSL interaction check above.

## Protected boundaries

- HSL Detection route, candidate regions, evidence, object boundaries,
  quantity, naming, document identity, preview selection and File Review data
  are unchanged by V6.58.
- V6.37 Ada, Page23 and Assembly Set routes remain protected.
- The outgoing-to-incoming screen overlap is not a bar failure and remains
  outside this checkpoint until isolated and tested.

## Next safe work

Trace the single-frame File Review handoff through the transition shell and DOM
readiness signal. Do not alter the accepted Processing pacing while repairing
that distinct handoff.
