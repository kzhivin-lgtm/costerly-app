# Estimation V5.8.2: Handoff recovery

## Incident

An Objects Estimation run stopped at the visual 45% geometry cap with
`Estimation V4 handoff failed: Expecting value: line 1 column 1 (char 0)`.
The worker had exited but the handoff error did not transition the reviewed
object row to a terminal state.

## Repair

- The content-addressed evidence-page upload retries an empty Storage JSON
  response up to three times. Repeating this upload is safe because it has the
  same immutable path and bytes with Storage upsert enabled.
- A final handoff failure sets all known, non-ignored estimate objects to
  `failed` at 100% and preserves the original failure for the screen.
- The current browser session overlays that terminal state even if the same
  infrastructure incident blocks the durable status update.

## Acceptance

For a clean estimate, Back to File Review and Continue resume the same worker.
If evidence storage returns an empty response once, the worker retries and the
estimate proceeds. If all retries fail, the row reads `Failed`, not
`Estimating 45%`.
