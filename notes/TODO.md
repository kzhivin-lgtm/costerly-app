# TODO

## Active
- Work with agent metrics: token/cost ledger plus seconds per agent cycle, seconds per detected object, and seconds per estimated object.
- Add overhead calculation layer after object material/labor pricing.
- Add deterministic delivery and installation pricing from project subtotal / overhead settings.
- Improve catalog matching: save matched material/labor rows and mark weak matches as `needs_review`.
- Run estimation for all detected objects, not only the first object.
- Design Objects Estimation status refresh without Streamlit stale-DOM fragments.
- UI copy: remove trailing periods from standalone UI text when no next sentence follows.
- Upload: continue first app/file-load optimization; warm refresh now uses the grey screen/app-ready path, but cold start after reboot can still show one Streamlit skeleton.
- Upload performance follow-up: after boot timeline + font/logo cache, return to lazy-load screens, `.streamlit/config.toml`, and post-deploy/reboot prewarm.
- Processing: review processing-screen text wording and keep its current position as the layout benchmark.
- Prompts / Agent Contract: normalize long object names later through the agent prompt/contract.
- Objects Estimation: reduce the large vertical gap between subtitle and pricing table column headers.
- Objects Estimation: add a small blue spinner next to the running Self Cost per Unit percent.
- Objects Estimation: format object quantities as whole units, not 1.0, after estimation completes.
- Objects Estimation: Delivery and Installation should not show Self Cost pending state or Pending review buttons; keep review/status area empty for project-level rows.
- Objects Estimation: keep Delivery and Installation as project-level percentage allocations and show their sale price inputs without fake object status.
- Object Detail: show AI Confidence when available.
- Object Detail: implement Object Preview image capture/display.
- Object Detail to Objects Estimation navigation: remove stale screen fragment flicker on return.
- Object Detail approve action: remove stale screen fragment flicker after clicking Approve.

## Later
- Audit and replace brittle layout code in Objects pricing rows and Upload dropzone when the current estimation/overhead flow is stable.
- Polish negative/error states with project button styles.
- Add XLS proposal export.
- Add missing-object second-pass detection flow.
