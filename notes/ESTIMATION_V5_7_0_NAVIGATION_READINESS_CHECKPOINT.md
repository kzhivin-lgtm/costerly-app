# Estimation V5.7.0 Navigation Readiness

Status: active. Task `5.7.0.1` is production-verified after a hard refresh;
task `5.7.0.4` removes retired screen-loading runtimes and is pending
production acceptance.

## Objective

Make internal navigation have one owner and one observable completion boundary.
An enabled destination action must eventually be backed by prepared target data,
but no browser-side recovery may destroy an existing `core.costerly.ai` Streamlit
session while that preparation or rerun is still in progress.

## V5.7.0.1 decision

`app.costerly.ai` owns browser history, initial cold-load masking and runtime
observability. `core.costerly.ai` owns Streamlit route state, authorization,
calculation and the final `app-ready` signal. The public wrapper has exactly
one live iframe and does not change its `src` for an internal transition.

The previous 900 ms `New Estimate` fallback and build-mismatch page reload both
created a competing navigation owner. They are removed. A lost callback now
records a timeout or target mismatch without replacing the active iframe.

## Route lifecycle

1. `transition-click`: browser intent, never a readiness result.
2. `transition-visible` / `transition-styled` / `transition-stage`: browser
   presentation milestones, retained for diagnosis only.
3. `new_estimate_callback_received`: confirms the native callback reached the
   core Streamlit session.
4. `transition_ready`: emitted only from the correlated `core` `app-ready`.

No milestone before step 4 may be used to start an iframe recovery or claim a
completed route.

## Protected behaviour

- Initial cold startup retains the existing neutral loading mask.
- Browser routes and durable route tokens remain unchanged.
- Authentication and all core data authorization remain core-owned.
- A target rendering exception remains visible and closes its pending browser
  transition instead of leaving a hidden iframe.
- No user or file data is placed into wrapper telemetry or browser history.

## Acceptance for 5.7.0.1

On authenticated production, repeat New Estimate from File Review, Objects,
Object Detail and Profile. Each normal case must keep one iframe, show no
second gray/reload cycle, emit one correlated `app-ready` and no
`browser.new_estimate_iframe_recovery` event. A deliberately unavailable core
callback must leave the visible session intact and produce a timeout, not a
fresh iframe.

## Local verification

- Inline wrapper JavaScript parsed with the bundled Node.js runtime.
- `py_compile app.py state/company_auth.py` passed.
- `tests/test_runtime_observability.py tests/test_navigation_routes.py`: 65
  passed.
- Full suite: 1,616 passed, 10 pre-existing failures outside this task in
  Processing handshake, Estimation handoff and material-policy expectations.
  None of their source files are changed by V5.7.0.1.

## Deployment note

Deploy wrapper and core together under build `estimation-v5.7.0`. The wrapper
intentionally tolerates a temporary build mismatch without reloading the page,
so deploy convergence must be verified by the recorded wrapper/core versions
and an authenticated interaction, not by an automatic browser refresh.

## Task sequence

`5.7.0.1` establishes the single-iframe transport boundary. `5.7.0.2` begins
only after its refreshed production witness, because preparation cannot
compensate for a click that never reaches core. This task first prepares File
Review → Objects. Objects → Review remains a separate second target within the
same task.

## V5.7.0.2 decision: File Review → Objects prepared launch

The first target in this task is File Review → Objects.  File Review creates an
in-memory `ObjectsLaunchPlan` after its editable cards render. It contains the
accepted metadata snapshot, latest widget values, ignored-object set, source
bytes and fully renderable seed rows. This preparation performs **no** database
write, route-token creation, model call or Estimation job.

Continue is enabled only when that plan has the retained source file. Its
callback recomputes the plan once to capture a value edited immediately before
the click, puts the seed rows and immutable request into Session State, and
changes the screen. It does not wait for Supabase. Objects dispatches the
existing durable metadata save, edit application, estimate-shell creation and
Estimation work on the single existing executor after it begins rendering.

An unchanged existing estimate remains the prior read path. It does not create
a second shell or resubmit a calculation. This is protected baseline behavior,
not a V5.7.0.2 improvement. The change only avoids a materially different
product behavior for a new accepted launch: no Anthropic work or orphaned
estimate record is created until the user explicitly presses Continue.

### V5.7.0.2 local verification

- `py_compile` for File Review, Objects, runtime and Session State passed.
- Targeted navigation, runtime and observability group: 73 passed.
- Broader File Review, Objects, workflow-route, runtime and observability
  group: 81 passed.
- Full suite: 1,620 passed, 10 pre-existing failures in Processing handshake,
  Estimation handoff and material-policy expectations. None are in a source
  file changed by V5.7.0.2.
- `git diff --check` passed.

Production acceptance requires one new RFQ. The unchanged Last Estimate case
is a regression check for existing behavior, not evidence of an improvement:

1. On File Review, Continue must paint seeded Objects immediately with no
   synchronous metadata/save or estimate-shell delay.
2. The background job must then persist and progress normally, with no duplicate
   estimate shell.
3. Returning to an unchanged File Review and pressing Continue must retain the
   existing no-new-run behavior.

## V5.7.0.3 correction: durable source and pending shell ownership

V5.7.0.2 incorrectly treated the current Streamlit session's uploaded bytes as
the only valid File Review source. A refresh could therefore render a real
persisted RFQ while disabling Continue. It also assigned a new estimate ID
before Objects had created its durable shell, allowing the global ownership
guard to reject the session-local transition.

Processing already stores the original in private Storage. V5.7.0.3 writes its
immutable Storage reference, SHA-256, MIME type and byte length to the existing
`rfq_source_original` processing-ledger event before File Review appears. A
restored File Review starts one verified private-source read in the background;
only after it completes can Continue become active. The source bytes never
enter browser history or wrapper telemetry.

For a newly accepted Continue, the temporary estimate identity is valid only
inside the same server session until its worker persists the shell. During that
bounded interval Objects publishes a run-only route, checks run ownership, and
does not test ownership of the not-yet-durable estimate. Once the worker is
terminal, normal durable estimate ownership and route-token behavior resumes.

Historical RFQs created before V5.7.0.3 may lack the ledger reference even
though a private original exists. The application must not guess a document
from Storage; those runs show a specific re-upload requirement instead.

## V5.7.0.4 correction: one screen-loading path

The V5.6 snapshot transition guard was no longer installed by V5.7, but a
browser tab kept open across deployment retained its capture-phase handler. On
Continue or Back it inserted a synthetic target header above Streamlit's stale
source DOM, producing the mixed File Review and Objects screenshots. V5.7.0.4
retires that handler, its shell, style, marker and body classes before every
product render. It does not introduce a replacement transition shell.

The review also removes three dead implementations: the snapshot transition
installer, its obsolete header helper, and the unused direct-DOM Objects
progress runtime. Header controls now have one identity. A duplicate Streamlit
key is no longer converted into a second, visible navigation rail. File Review
repairs empty widget teardown acknowledgements from its durable in-session
review snapshot, and a delayed File Review fragment cannot request a rerun
after navigation has entered Objects.

### V5.7.0.4 local verification

- `py_compile` passed for `app.py`, UI guards, screen-transition helpers,
  File Review and Objects.
- Navigation, workflow header, timing and observability tests: 178 passed.
- `git diff --check` passed.

Production acceptance is one repeated interaction in the same existing tab:

1. File Review → Objects must never show a synthetic Objects title over File
   Review content.
2. Objects → File Review twice must retain Project, Partner, Client and Object
   name values.
3. Exactly one header control rail is visible on both screens.
