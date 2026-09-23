# TODO

- 3.8.1 Railway hosting migration: accepted production checkpoint. Preserve
  production checkpoint `bbb8297` and retain the Streamlit Cloud deployment as
  rollback while the existing Cloudflare wrapper runs against Railway at
  `app.costerly.ai`. The
  wrapper selects the Railway backend only for the staging hostname and uses
  the selected backend origin for all transition handshakes. Acceptance
  requires clean hard refresh, Sign in, Upload to Profile, Profile to New
  Estimate, Profile to Upload, and Sign out cycles without gray, white,
  unstyled, or mixed-screen frames, plus complete correlated runtime telemetry.
  Direct Railway testing is not visual acceptance because it bypasses the
  Cloudflare transition wrapper. The owner explicitly approved switching the
  production wrapper backend to Railway after confirming the direct Railway
  runtime was materially faster. The owner completed repeated Sign in, Profile,
  New Estimate, return, and Sign out cycles and accepted the result as fast and
  production-ready. Trace `a6152e2d-517a-4faa-a125-311c46faa3ef` measured the
  initial Auth reveal at 4.011 seconds; accepted warm styled reveals were mostly
  0.677-1.356 seconds with one Python run. Known acceptance gap: one first
  Profile cycle after a repeated Sign in hit the five-second mask timeout and
  reached ready at 10.869 seconds, and the owner observed one negligible broken
  frame. Retain both as follow-up evidence rather than claiming zero visual
  defects. Verification: 238 tests passed. Checkpoint commit: `4b8b24a`.
  Protected production checkpoint: `bbb8297`.

- 3.8.2 Password recovery: active after accepted 3.8.4. Add a user-visible
  Forgot password flow using the existing Supabase Auth account and the final
  branded application origin. Reuse the accepted Sign in visual and transition
  system, keep account-existence responses neutral, use a single-use expiring
  recovery link, and enforce the registration password policy on reset. Verify
  the actual Supabase recovery-mail transport and redirect contract before
  implementing the production send path. The recovery email and browser-session
  handoff now reach the Reset password form. Production password submission
  still requires verification after adding safe Supabase error type/code
  telemetry and actionable provider-error feedback. Do not mark this task
  complete until a production password change returns to Sign in and the new
  password authenticates successfully.

- 3.8.4 One-time team invitations and access removal: completed and accepted in
  production. The owner confirmed the additive Supabase migration was applied
  on 22.09. Each freshly generated bearer link is not tied to an email, expires
  after 24 hours, and is consumed atomically by the first successful membership
  creation. The Users tab lets only the owner generate a link and remove a
  member after confirmation; the owner cannot remove themself. Removal deletes
  only the `company_members` relationship, not the Supabase Auth user. The
  legacy `company_join_links` table remains untouched as a rollback surface but
  is no longer read by the new application path. Verification covered one
  successful registration, rejection of the consumed link, member removal,
  fresh access denial for that member, and preservation of Profile -> Users
  after link generation. The owner-facing raw token is plain text with a
  dedicated Copy action, never a navigable link. The Join registration screen
  reuses the accepted Sign in heading, full-width submit geometry, validation,
  loading spinner, and retained-screen transition behavior, without the
  redundant explanatory subtitle. The owner accepted the production result on
  22.09. Implementation commits: `013a67b` and `15d5aea`. Railway required a
  manual Deploy Latest Commit because the expected GitHub autodeploy did not
  trigger; that deployment-integration defect remains a separate follow-up and
  does not invalidate the accepted invitation behavior. Verification: 244 tests
  passed.

- 3.8.5 Railway GitHub autodeploy reliability and build timing: completed, P1.
  GitHub `main`
  accepted commits `b9f27d4` and `785d828`, and Cloudflare Pages deployed the
  same source automatically, but Railway did not create a deployment until
  `Deploy latest commit` was triggered manually. Verify the service Source is
  connected to `kzhivin-lgtm/costerly-app` on `main`, Autodeploy is enabled,
  Wait for CI is disabled while no GitHub Actions workflow exists, Watch Paths
  are empty, and Deployments has no skipped or approval-waiting pushes. Then
  prove the repair with one harmless GitHub commit that produces a Railway
  deployment without manual intervention. The baseline deployment exposed
  approximately 112 seconds of build work, including 51 seconds for pip, while
  Railway displayed more than four minutes end to end. The current experiment
  replaces `requirements.txt` with the standard `pyproject.toml` plus `uv.lock`
  path recognized by Railpack 0.39.0 and Streamlit Community Cloud. Local cold
  dependency preparation completed in 7.49 seconds and installation in 0.197
  seconds. Commit `bf0581d` proved the repair: Railway created deployment
  `4dec029a-5989-419c-8be8-751f1e41c954` automatically 16 seconds after the
  push timing mark, selected uv on Railpack 0.39.0, passed its healthcheck, and
  reported success after 193 seconds. Explicit build steps fell from about 113
  seconds to about 72 seconds, a reduction of roughly 41 seconds or 36 percent.
  Approximately 114 seconds before server start remain outside the itemized
  build steps and belong to Railway scheduling and deployment orchestration,
  not dependency installation. Verification: 263 tests passed and both the
  direct Railway health endpoint and `app.costerly.ai` returned HTTP 200.

- 3.6.2 Hard-refresh Sign in reveal stability: preserve the accepted in-button
  spinner and one-run Sign in while preventing partial Upload DOM from appearing
  after Command-Shift-R. Production trace
  `eaf99421-c863-4886-ac74-e34f8d56298b` measured Sign in at 1.106 seconds with
  one Python run, target visibility at 1.077 seconds, and app-ready only 29ms
  later. Replace the insufficient two-frame release criterion with 120ms of DOM
  quiet and a 450ms fail-open. Status: accepted production checkpoint at
  `fb1ad97` (v3.6.2). The user confirmed fast Sign in, the accepted in-button
  spinner, and no partial screen in the tested hard-refresh cycle. Protected
  rollback points: v3.5.11 (`aa05a5d`) and v3.6.1 (`f334338`).

- 3.6.1 Labor Costs table compaction: fit the complete worker summary table
  inside the Profile content width without horizontal clipping. Stack Edit and
  Remove vertically in a narrow action column, show `Hourly` and `Monthly` only
  in the table, omit the employment factor from Pay Details, and size the
  controlled-value columns around their longest supported labels. Shorten the
  managed Position labels, remove Cabinetmaker / Joiner and Purchasing Manager
  from new selections, and hide the optional clear control in the three Labor
  Costs selectors without changing their dropdown action. Existing archived or
  active records retain their stored codes; the retired cabinetmaker code is
  presented as Carpenter. Status: accepted in production at `f334338`
  (v3.6.1); the user confirmed the compact table result. Protected rollback
  checkpoint: v3.5.11 (`aa05a5d`).

- 3.5.2 Profile and Auth performance stabilization: keep v3.4.2 (`86117ba`)
  as the emergency rollback boundary without treating it as a measured speed
  baseline. Split the first Profile path into lazy module import, Profile shell,
  styles, header, tabs, and active content. Use complete production traces to
  identify the earliest slow boundary before changing behavior. Restore warm
  Profile and Auth transitions to the previously accepted range, retain native
  Streamlit actions, encrypted Fast Resume, sessionStorage fallback, route
  restoration, and the Cloudflare transition mask, and accept only after two
  complete user-visible cycles show no broken intermediate screen.
  Production evidence for candidate 3.5.6 identified and removed a redundant
  Upload-to-Profile rerun: navigation now changes screen state in the native
  Profile button callback before the next script render. Acceptance remains
  pending a deployed full-page reload with matching wrapper/server build and
  two clean cycles. The next isolated target is the 1.9-second synchronous
  browser-session store measured during Sign in.
  Regression protection now includes a shared callback-safe screen setter, a
  source test rejecting widget navigation followed by explicit rerun, a
  wrapper/server build handshake with one guarded reload, and per-transition
  Python-run counts. Production acceptance must show matching builds and
  `python_runs=1` for both Profile directions. Status: accepted production
  checkpoint at `aa05a5d` (v3.5.11). The user confirmed satisfactory behavior,
  the in-button Sign in spinner, and clean transitions. The first cold Upload
  to Profile remains somewhat slower than repeated transitions and is accepted
  for this stage rather than retained as an active defect.

- 3.1.12 Refresh route persistence: after browser refresh, restore the same
  authenticated product screen and, where applicable, the same nested tab.
  Apply one explicit navigation-state contract to Profile, File Review,
  Objects, Object Detail, Registration, Company Setup, Auth, and future screens.
  Preserve authorization checks and never restore a company-scoped resource
  without revalidating access. The current revision mirrors only safe route
  state into the outer Cloudflare URL, forwards it to each new Streamlit iframe,
  restores the selected Profile tab and persisted RFQ/estimate/object context,
  and reuses the existing Supabase ownership checks before rendering protected
  resources. Auth and invite-driven screens remain derived from their existing
  authorities. Active Processing intentionally fails safe to Upload because its
  file bytes and futures are not durable yet. The first production revision
  restored Profile after shared account controls had already rendered, causing
  duplicate `company_sign_out` keys. The corrected revision restores Profile
  and its tab before account controls render. The Cloudflare transition layer
  now covers both Profile to Upload and Upload to Profile while the restored
  screen is assembled. Status: accepted production checkpoint at `e48bb71`;
  the user confirmed refresh preserves Profile and its selected tab, no
  duplicate-key error remains, and both transition directions are clean.

- 3.1.11 Profile to Upload transition integrity: identify and remove the
  intermediate stale or partial screen visible after Continue to upload.
  Preserve the accepted Profile and Upload layouts, native button behavior,
  transition telemetry, and the v3.1.10 navigation callback. Production logs
  confirm a 0.712-second click-to-ready transition with only 0.291 seconds of
  server work and a 1.3ms Upload render; the visible defect is Streamlit's
  incremental client DOM patch while the old Profile marker is still present.
  The current revision reuses the Cloudflare startup mask only for this
  transition, reveals the iframe on the correlated Upload `app-ready`, and has
  a five-second fail-open timeout. Status: accepted production checkpoint at
  `4738cb3`; the user confirmed no intermediate screen in either direction
  between Profile and Upload.

- 3.1.10 Company Profile navigation and Overhead Expenses copy: restore the
  accepted v3.0.57 full-width tab rail on the current stateful, lazy-rendered
  tabs without reverting the v3.1.8 performance improvement. Use Overhead
  Expenses consistently in the table heading, save action, success message,
  and save errors. Remove the current React Aria selection underline, emphasize
  only the active tab, and remove the zero-height save bridge from document
  flow, including its outer Streamlit element wrapper, so Overhead Expenses
  starts at the same height as Contacts. Rename Price List to Price Lists.
  Preserve the working expense persistence path and defer Sign out sizing,
  Save Contacts, and Save Company Details. Status: production work-in-progress
  at `9ab5814`. The rail, active-tab bold treatment, plural `Price Lists`,
  Overhead Expenses copy, working Save, and removal of the red React Aria
  indicator are visually confirmed. A small residual vertical offset remains
  between the Overhead Expenses card and the other tab contents. Do not add a
  guessed negative margin. The accepted rollback boundary is `b58b1f5`, restored
  without history rewriting at `6a403b0`. Production telemetry then confirmed
  that the remaining whole-page jump is not scrolling or tab CSS: the transient
  zero-height `scroll_parent_to_top()` component occupies one 16px root layout
  gap on the first Profile render and disappears on the tab rerun. The current
  revision moves that utility component into the hidden Sidebar while preserving
  its scroll-reset behavior. The remaining Expenses-only offset was addressed by
  limiting `@st.fragment` to the save bridge instead of wrapping the complete
  tab. Profile to Upload navigation now changes screen state in a pre-render
  callback, preventing a partial Profile delta before the Upload rerun. Status:
  accepted production checkpoint at `3f8c80a`; the user confirmed the page no
  longer jumps, the Expenses alignment is correct, and Save remains functional.

- 3.1.9 Auth transition integrity: execute Sign in and every Sign out through
  native Streamlit callbacks before the next script render. Remove the
  intermediate Login/Profile render that can expose a broken screen or two
  logos. Preserve the current cookie, sessionStorage fallback, telemetry,
  native click behavior, and accepted layout. Status: functional production
  acceptance at `8182c51`. Clean Sign out measured 0.75-1.22 seconds and clean
  Sign in measured 1.29 seconds, with no broken screen observed. A telemetry
  follow-up closes failed Sign in transitions so later successful timings do
  not inherit stale correlation IDs.

- 3.1.8 Profile latency optimization: preserve the accepted six-tab geometry
  and working Save Expenses path, but render only the selected tab. Reuse the
  company access already verified in the current Python run and load the
  company profile row only for Contacts or Company Details. Status: accepted
  production checkpoint at `4c6d628`. Repeated Upload to Profile improved from
  3.36 seconds to 1.06-1.12 seconds, with server time reduced from 2.36 seconds
  to 0.29-0.30 seconds. The first cold transition improved from 4.23 seconds
  to 2.66 seconds.

- 3.1.7 Internal transition telemetry: measure Sign in, Upload to Profile,
  Profile to Upload, and Sign out from the browser click to the next rendered
  screen. Correlate each result with auth network time, company access lookup,
  Profile load, screen render, and Python reruns. The browser observer is
  passive and bubble-phase only. It must never cancel, delay, disable, or
  replace a native Streamlit click. Status: production measurements complete.

- 3.1.6 Streamlit runtime regression test: production was observed on unpinned
  Streamlit 1.64.0 while the verified local environment uses 1.58.0. Pin 1.58.0,
  rebuild production, and compare the same deep iframe startup boundaries. If
  startup does not improve or protected behavior regresses, revert the pin.
  Status: rejected. The first 1.58.0 Login took 7.06 seconds, followed by four
  iframe-only traces that never reached the auth component and timed out after
  8.26-8.39 seconds. Production is pinned back to 1.64.0 to prevent drift.

- 3.1.5 Deep iframe startup telemetry: split the embedded Streamlit startup
  gap into component script, component render, browser storage read, callback,
  and final app-ready boundaries. Record production Python, Streamlit, and
  Supabase versions before deciding whether to pin currently floating runtime
  dependencies. Status: implementation ready for production verification.

## Working rule
- A broken core layer must be repaired and validated at its actual integration point. Disabling or bypassing it is not an acceptable primary fix; fallback behavior is only an additional production safety mechanism.
- Every new two-file benchmark cycle starts two fresh instances on separate unused ports and opens both Chrome tabs automatically so `page-23.pdf` and `Металл (1).pdf` can run in parallel under the same code version. Keep older benchmark servers and result screens available for side-by-side comparison; stop them only on explicit request or when resource/port conflicts require cleanup.

## Active
- 3.1.2 Pilot Fast Resume: remove the initial browser-session rerun with a
  30-minute encrypted partitioned resume cookie, retain sessionStorage as the
  compatibility fallback, and keep Supabase as the authority for user and
  company access. Ship disabled first, then verify production enablement,
  fallback, expiry, tamper rejection, and two Sign out / Sign in cycles.
- 3.1.1 Production Observability Foundation: persist correlated browser and
  server timing boundaries without blocking render, changing UI geometry, or
  recording credentials, PII, file names, or RFQ content. Apply the Supabase
  migration and Cloudflare Function secrets before production verification.
- Company Profile follow-up after the v3.0.59 Save Expenses checkpoint:
  diagnose the duplicate heading observed after Sign out, then verify Contacts
  and Company Details remain on their selected tab after Save. Recheck the full
  sign-in, upload, profile, save, logout, sign-in, and reload cycle before
  declaring the checkpoint stable. The Other Spendings migration is applied.
  Do not change the accepted table geometry or the working Expenses save path.
- 3.2.1 Labor Costs: replace the placeholder with an owner-only employee cost
  register. The first production candidate uses one informal `Worker name`
  field, managed Department and Position lists, Monthly Salary or Hourly Rate,
  Average Hours per Month for hourly workers, and a derived Monthly Bruto total. The
  personnel records live in `company_employees`, separately from the Estimation
  `labor` catalog. Net salary, tax, pension, National Insurance, and total
  employer burden remain deliberately out of scope until their calculation
  contract is defined. The initial production version at `b6a3cd8` is an accepted
  rollback point. The current revision moves saved workers above the form, uses
  the Overhead Expenses typography, uses three-column role and hourly rows,
  removes numeric steppers, resets every field after Add, and opens owner-only
  editing from a small pencil beside the worker name. The rejected native-grid
  rewrite was reverted. The pencil is now before the name so edit controls form
  one vertical column. The selector fix targets Streamlit 1.64 React Aria groups,
  inputs, buttons, and option states while retaining the older BaseWeb rules.
  Status: accepted production checkpoint at `1df98c5`; the user confirmed the
  pencil alignment, vertically centered selector text, and purple focus states.
  The current minor candidate removes the extra Add Worker card top margin and
  limits bold disabled styling to calculated text inputs so the disabled
  `Select position` placeholder stays regular weight. Status: accepted
  production checkpoint at `dfcf5ef`; the user confirmed the final spacing and
  selector presentation.
- 3.2.2 Users invitation link: replace the loose heading and code block with the
  existing Users table-card design, keep the owner-only link clickable, and use
  the same compact 12px inter-section gap as Labor Costs. Status: visually
  accepted and pushed at `dff220c`; 186 tests passed.
- 3.2.3 Compact Profile header: remove accumulated Streamlit gaps above the
  visible header, equalize the page-to-title and title-to-tabs spacing at 34px,
  use actual 36px Profile action buttons, align their visual axis with the logo,
  and expose Projects as a disabled placeholder pending its route and data
  contract. Status: visually accepted and pushed at `1f30416`; 186 tests passed.
- 3.2.4 Profile transition compatibility: keep the accepted v3.2.3 action
  alignment and bind the existing Profile-to-Upload transition curtain to the
  stable `profile_to_upload` key instead of visible copy. Status: accepted in
  production as part of v3.2.5.
- 3.2.5 Profile navigation priority: rename the file-workspace action to
  `New Estimate`, keep `Projects` first and `Sign out` last, and prioritize the
  profile tabs as Overhead Expenses, Labor Costs, Price Lists, Contacts,
  Company Details, and Users. Remove the manually maintained build-version
  secret override and enforce matching Streamlit/Cloudflare versions in tests.
  Status: accepted in production at `b372d3d`; 187 tests passed.
- 3.3.1 Authenticated home composition: preserve the accepted Upload logo size
  and position exactly, reduce the three-line product credo, place compact
  Projects, Profile, and Sign out controls between the credo and native upload
  card, and keep Projects visibly disabled until its route exists. Status:
  accepted in production at `cf35d9b`; the full Sign out label is visible, the
  two lower gaps are code-defined at 32px, and 188 tests passed.
- 3.4.1 Company logo normalization: rename the Profile tab to Bank Details and
  add a separate owner-only Company Logo card below Save Contacts. Accept PNG,
  safe self-contained SVG, and first-page PDF sources, normalize them without AI to
  a private 1024px square PNG card, retain only its private Storage reference,
  and instrument conversion, upload, database update, cleanup, and load.
  Status: accepted production checkpoint at `2a6ac0f`; the supplied SVG was
  converted, previewed, saved, and persisted in production, and 203 tests
  passed. Separate PNG and PDF production checks remain pending.
- 3.4.2 Company Logo saved-state UI: hide the empty right-side preview frame,
  keep Drop or Upload available for replacements, align the two-column saved
  composition, use a full-width active Change Logo action backed by the native
  picker, apply the shared 32px Profile action gap, keep drag-over purple, and
  dismiss the success notice after five seconds. Status: accepted in production
  at `32497dc`; 204 tests passed. Closed.
- Profile success-message consistency: move success feedback above Save actions
  across the remaining Profile tabs and use a common dismissal rule without
  changing persistence handlers. Status: deferred to a future block; Company
  Logo already follows the intended placement.
- Auth UI follow-up: improve Sign out press/progress/completion feedback without changing the accepted Sidebar session component, adding JavaScript click interception, `pointer-events: none`, capture handlers, or focus-based infinite spinners. Preserve v3.0.51 refresh persistence and verify two consecutive Sign out / Sign in cycles.
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
- UI copy: enforce the product rule that the final sentence in a user-facing
  text block has no trailing period. Preserve internal periods and meaningful
  question marks, exclamation marks, and other punctuation. Password recovery
  and shared Auth validation copy now follow this rule; the remaining product
  copy still needs an audit.
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
- 3.7.1 Company Price Sources: active. Production candidate adds one-source upload or
  public-URL ingestion, optional category selection with automatic classification, automatic supplier and
  document classification, unit-preserving normalization, private versioned
  offers, unresolved-row quarantine, source inspection, and private source
  storage. The owner applied the additive database migration before deployment;
  `233 passed` on the production candidate. Verify one photographed invoice and
  one static public supplier page on production. Existing `materials` and the
  current Estimation resolver remain unchanged until import evidence is accepted.
  First production URL test exposed output truncation on the 15k-character
  Rotenberg catalog page; the extraction budget was raised from 8,192 to 32,768
  tokens and explicit max-token failure handling was added. The same page then
  exposed a model arithmetic mismatch, so ready-row normalized prices are now
  calculated deterministically. The final no-write diagnostic completed in
  48.252 seconds with supplier `Rotenberg 1929`, document type `price_list`, and
  48 of 48 rows validated as ready. Production persistence still requires a
  user-visible retest after the hotfix deployment. A later production URL test
  failed before the agent: the page returned only 190 bytes and no readable HTML
  text. Script-only or protected pages now receive a specific instruction to
  upload a PDF, screenshot, or photo. A no-write automatic-category diagnostic
  on the Tsidky page inferred `Sheet Materials`, identified the supplier, and
  validated 39 of 42 rows as ready. Production still needs the exact failing URL
  to determine whether a safe dynamic-page importer is justified. Production
  user testing on checkpoint `4a5fd9a` confirmed that Sign Out no longer reveals
  an unstyled Auth screen and that two automatic-category URL imports completed
  in 22.9 and 9.5 seconds. Both persisted as `partial`, with zero ready prices:
  one returned 27 unresolved rows, the other 6 unresolved and 1 excluded row.
  Price ingestion therefore remains active work, not an accepted completion.
  The preceding session measured Upload to Profile at 3.65 seconds. Its Profile marker
  reached the DOM after 0.68 seconds and its server work was about 0.72 seconds;
  roughly 2.97 seconds were spent waiting for the late general `app-ready`
  component before the Cloudflare transition mask was removed. Checkpoint
  `a626462` reuses the verified styled-target event path for both Upload to
  Profile and Profile to Upload. It verifies screen-specific computed styles before
  revealing either target and leaves the general `app-ready` event unchanged for
  final server-run telemetry. Production trace
  `3ae650ed-7e9e-4b15-b333-3e4691e4c227` measured two Upload to Profile styled
  reveals at 704ms and two Profile to Upload styled reveals at 663ms and 895ms,
  each with one Python run. The user accepted the navigation speed. No further
  transition change is pending unless a new production regression is observed.
