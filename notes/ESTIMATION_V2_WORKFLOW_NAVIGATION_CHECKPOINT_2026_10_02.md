# Estimation v2 workflow navigation checkpoint, 2026-10-02

## Acceptance boundary

This checkpoint accepts the authenticated production workflow transition cycle:

`Processing -> File Review -> Objects -> File Review -> Objects -> Upload`

The owner confirmed that repeated navigation now keeps File Review document
details, detected-object names, and Upload account controls visible. The
accepted result is navigation integrity, not a new estimation-quality or
performance baseline.

## Root cause and correction

The production runtime trace showed that File Review emitted a second
`app-ready` after the original navigation render. The source was a timed
`@st.fragment(run_every=0.5)` used to poll deferred Naming. That independent
Streamlit rerun could overlap a click to Objects or Upload and replace the DOM
after the destination screen had started rendering.

`348604a stop timed file review reruns during navigation` removes the timed
fragment. Deferred Naming remains asynchronous, but a completed result is now
collected during the next ordinary File Review rerun. This preserves the
background agent without a competing page render.

The preceding transition fixes are included in this checkpoint:

- `cd528d0`, `07227a5`, and `d8e06ad` stop Objects runtime code from mutating
  React-owned DOM during workflow navigation.
- `6a460a5` preserves File Review names and keeps Back to Upload available.
- `4d06044` holds the gray transition layer until the destination screen has
  its required DOM, including header controls.

## Verification

- Production owner acceptance: repeated authenticated workflow cycle completed
  with all reviewed data and Upload controls present.
- Automated suite: 853 passed, 26 dependency warnings.
- `git diff --check`: passed for the implementation commits.
- Accepted production HEAD: `348604a`.
- `HEAD...origin/main`: expected to be `0 0` after the checkpoint journal is
  committed and pushed.

## Protected behavior

- Processing retains its accepted presentation and position contract.
- File Review remains the durable entry point for the active RFQ.
- Deferred Naming does not block File Review or Estimation.
- Estimation Engine, Resolver, Labor Engine, pricing, persistence, statuses,
  routes, and calculation formulas are unchanged by this checkpoint.
- Starting a new upload still resets the local active-RFQ state. Cancellation
  of provider work and Project finalization remain deferred as 3.15.14.

## Deferred follow-up

Navigation correctness is accepted. Transition speed is not: production traces
before the final correction showed normal warm File Review and Objects changes
in roughly 1.7 to 3.5 seconds. Any attempt to make already-rendered screens
instant must be a separate architecture task, with a safe state boundary rather
than retaining Streamlit's live React DOM.

## Dirty worktree preservation

The pre-existing dirty `notes/TODO.md`, `.streamlit/`,
`db/sql/3_15_4_israel_global_catalog_v1_parts/`, and `tmp/` are deliberately
outside this checkpoint commit.
