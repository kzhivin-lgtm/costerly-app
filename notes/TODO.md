# TODO

## Working rule
- A broken core layer must be repaired and validated at its actual integration point. Disabling or bypassing it is not an acceptable primary fix; fallback behavior is only an additional production safety mechanism.
- Every new two-file benchmark cycle starts two fresh instances on separate unused ports and opens both Chrome tabs automatically so `page-23.pdf` and `Металл (1).pdf` can run in parallel under the same code version. Keep older benchmark servers and result screens available for side-by-side comparison; stop them only on explicit request or when resource/port conflicts require cleanup.

## Active
- Auth UI follow-up: improve Sign out press/progress/completion feedback without reintroducing a custom component, JavaScript click interception, `pointer-events: none`, capture handlers, or focus-based infinite spinners. Preserve the stable pre-browser-session state transition and verify two consecutive Sign out / Sign in cycles.
- Auth persistence follow-up: design session persistence separately from Sign in/Sign out transitions. The removed custom browser-session component caused duplicate-looking Sign in and stale Sign out UI. Until a replacement is independently verified, a full browser refresh may require Sign in again.
- Unified Detection/OCR experiment sequence — quality first; every step must preserve the stable 3-object and 15-object boundaries before the next step begins:
  1. Make benchmark run IDs unique so repeated runs cannot overwrite prior object results. Direct PDF OCR remains the default one-PDF/one-request flow. Naming is text-only and receives locked Detection facts plus OCR snippets, never the PDF again.
  2. Validate the restored core Direct PDF OCR route on `mistral-ocr-4-0`. Structured vision annotation is excluded from the critical path because it changed a 2–3 second request into a 37–90+ second request. Record OCR completeness, p50/p95, dimensions, tokens, and total time.
  3. Continue the dimensions work already started. Bind every external dimension to the same object index, evidence page, and OCR region; never promote a component size to the whole-object envelope; when axes conflict, return unknown plus a concise clarification instead of guessing. Do not add another full-document pass.
  4. Make Naming text-only. Keep the separate Naming Agent and immutable object list, but stop sending it the PDF again. Pass indices, evidence pages, relevant OCR snippets, and locked Detection facts. Preserve current naming quality and target 2–3 seconds.
  5. Parallelize the first document stage. Start the single Direct PDF OCR request and visual-only commercial object locking at the same time. Join once both finish, then reconcile OCR evidence against the locked object IDs without a second full-document analysis.
  6. Parallelize the post-lock stage. After object IDs and order are immutable, start short Naming and technical OCR enrichment as parallel branches. Neither branch may add, remove, merge, split, or reorder objects.
  7. Completed in v3.0.35: File Review waits only for OCR, Detection, and the authoritative result save. Naming v4 now runs in the background, updates only unchanged provisional names, and no longer blocks the user; full OCR and runtime diagnostics also remain outside the critical path.
  8. Completed in v3.0.40: Processing uses measured Golden stage weights, an ease-in Detection curve, and OCR page-count pacing buckets; the early sprint and slow finish are removed without changing backend work.
  9. Run the acceptance benchmark. Use fresh files and at least three cold runs per file; compare object boundaries, names, dimensions, OCR completeness, p50/p95, tokens, cost, and total user-visible time.
  10. Prepare production concurrency later. Add organization-wide limits, backpressure queueing, 429 handling, and visual-only Detection fallback. Keep one PDF as one OCR request; do not restore per-page fan-out.
- Closed routing experiments:
  - Rendering pages while earlier pages entered OCR produced about 3.5 seconds of overlap on the 11-page file, but is superseded by Direct PDF because the main route no longer renders pages.
  - The 4-versus-6 page-worker experiment is retired. Future concurrency control applies across whole PDF requests from different users, not inside one document.
- Objects Estimation: manual sale price override should stay authoritative after self-cost changes, with manual label and SC-changed notice.
- Add overhead calculation layer after object material/labor pricing.
- Add deterministic delivery and installation pricing from project subtotal / overhead settings.
- Improve catalog matching: save matched material/labor rows and mark weak matches as `needs_review`.
- Run estimation for all detected objects, not only the first object.
- Design Objects Estimation status refresh without Streamlit stale-DOM fragments.
- UI copy: remove trailing periods from standalone UI text when no next sentence follows.
- Upload: continue first app/file-load optimization; warm refresh now uses the grey screen/app-ready path, but cold start after reboot can still show one Streamlit skeleton.
- Upload performance follow-up: lazy-load screens and cleanup are done; revisit `.streamlit/config.toml`, cold-start behavior, and optional post-deploy/reboot prewarm.
- Processing: review processing-screen text wording and keep its current position as the layout benchmark.
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
- Large-PDF Detection routing: prevent Claude HTTP 413 before starting expensive work. Estimate the complete Messages payload size, including Base64 expansion, OCR context, prompt, and schema; never retry a non-retriable 413 through the fallback model. When the inline payload would approach the 32 MB Messages limit, upload the PDF once through the Anthropic Files API and pass its `file_id` instead of Base64. If the referenced document still exceeds the model context, split it into controlled page groups and reconcile one package-level object set. Persist OCR, upload, Detection, and failure timings for unsuccessful cycles.
- Audit and replace brittle layout code in Objects pricing rows and Upload dropzone when the current estimation/overhead flow is stable.
- Polish negative/error states with project button styles.
- Add XLS proposal export.
- Add missing-object second-pass detection flow.
