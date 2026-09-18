# Done Log

App skeleton, завершена 22.06 18:54
Local backups ignored by git, завершена 22.06 19:13
Brand assets and Cloudflare wrapper added, завершена 22.06 22:03
Design foundation added, завершена 22.06 22:19
Upload screen foundation built, завершена 22.06 23:41
Upload dragover state added, завершена 23.06 10:33
Streamlit embed controls hidden in app UI, завершена 23.06 10:33
Current Streamlit embed badge hidden, завершена 23.06 10:41
Streamlit embed footer hidden in Cloudflare wrapper, завершена 23.06 10:50
Post-upload processing layout foundation added, завершена 23.06 11:51
Shared processing stage renderer added, завершена 23.06 15:11
Done log created, завершена 23.06 15:33
File Review screen foundation and aligned post-upload layout, завершена 23.06 16:04
Backup V1.2.0_before_file_review_foundation created, завершена 23.06 16:04
Detected object card edit layout, завершена 23.06 16:26
Backup V1.3.0_before_detected_object_card_edit_layout created, завершена 23.06 16:26
Missing objects UI + shared input/button tokens, завершена 23.06 21:44
Objects pricing screen foundation, завершена 23.06 23:11
Backup V1.5.0_before_next_task created, завершена 23.06 23:11
Object detail screen and final pre-agent UI polish, завершена 24.06 11:05
Backup V1.6.0_before_next_task created, завершена 24.06 11:05
Claude Detection Agent connected to Processing and File Review via Supabase, завершена 24.06 12:54
Backup V1.7.0_before_next_task created, завершена 24.06 12:54
Objects Estimation subtitle arrows normalized, завершена 24.06 14:12
Backup V1.7.1_before_next_task created, завершена 24.06 14:12
Processing screen soft progress restored and aligned without moving post-upload screens, завершена 24.06 17:19
Backup V1.7.2_before_next_task created, завершена 24.06 17:19
Agent usage ledger with token and USD cost tracking, завершена 24.06 19:19
Backup V1.8.0_before_estimation_agent_foundation created, завершена 24.06 19:19
Estimation foundation shell connected to File Review, завершена 24.06 20:12
Backup V1.9.0_before_estimation_agent_contract created, завершена 24.06 20:12
Estimation Agent contract/runtime and first deterministic pricing layer, завершена 25.06 15:38
Backup V1.10.0_before_overhead_pricing created, завершена 25.06 15:38
File Review real object inputs and post-upload transition guard fixed, завершена 27.06 00:27
Backup V1.10.9_before_file_review_object_inputs_transition_guard created, завершена 27.06 00:27
Post-upload transition curtain checkpoint and dependency reuse rule saved, завершена 27.06 11:30
Backup V1.10.10_before_transition_curtain_cleanup created, завершена 27.06 11:30
Navigation cache and Supabase retry optimization, завершена 27.06 12:36
Backup V1.10.11_before_navigation_cache_retry_push created, завершена 27.06 12:36
Transition overlay stable-frame release, завершена 27.06 13:30
Backup V1.10.12_before_transition_overlay_stable_frame_release created, завершена 27.06 13:30
Temporary transition perf instrumentation, завершена 27.06 14:00
Objects Estimation layout/input-format checkpoint before numeric input editor fix, завершена 02.07 12:49
Backup v2.01.30_before_numeric_input_editor_fix created, завершена 02.07 12:49
Backup V1.10.13_before_transition_perf_instrumentation created, завершена 27.06 14:00
Objects Estimation sale price input guard fixed without changing table layout, завершена 03.07 15:10
Backup v2.01.32_before_objects_sale_price_input_guard created, завершена 03.07 15:10
Objects Estimation Delivery/Installation manual override scoped per input, завершена 03.07 18:34
Backup v2.01.33_before_project_cost_manual_override_scope created, завершена 03.07 18:34
Objects Estimation pricing overrides persisted and Object Detail editable inputs connected, завершена 04.07 12:45
Backup v2.01.34_before_persisted_object_detail_edits created, завершена 04.07 12:45
Validated backup helper and backup-only-through-helper rule added, завершена 04.07 12:55
Backup v2.01.35_before_validated_backup_helper created, завершена 04.07 12:55
Object Detail editable cells checkpoint with live recalculation and input persistence, завершена 04.07 23:30
Backup v2.01.36_before_object_detail_approve_fix created, завершена 04.07 23:30
Object Detail Approve snapshot save persists recalculated self cost and Done state, завершена 05.07 11:35
Backup v2.01.37_before_next_object_detail_task created, завершена 05.07 11:35
File Review Continue restored after Object Detail approve/back navigation, завершена 06.07 14:15
Backup v2.01.38_before_next_task created, завершена 06.07 14:15
Object Detail approve return optimized to about 4s and footer link button styling fixed, завершена 08.07 12:25
Backup v2.01.39_before_next_task created, завершена 08.07 12:25
Initial app boot visual noise reduced: Cloudflare grey screen now releases via Streamlit app-ready signal, warm refresh is about 5s and skeleton is limited to cold start after reboot, завершена 09.07
Backup v2.01.52_after_embed_ready_signal created, завершена 09.07
Runtime cleanup and upload lazy-load checkpoint: perf/debug instrumentation removed, upload route stays isolated from post-upload screens, локально проверено на 8572, завершена 10.07
Backup v3.0_after_runtime_cleanup created, завершена 10.07
File Review refactor: Continue flow split into helpers, object edit state centralized, dead CSS/search leftovers removed, локально проверено на 8572, завершена 10.07
Backup v3.0.1_after_file_review_refactor created, завершена 10.07
Objects Estimation refactor: screen split into state/render/runtime helpers, pricing table HTML moved to ui.objects_pricing, unused progress input no-op removed, локально проверено на 8572, завершена 10.07
Backup v3.0.2_after_objects_estimation_refactor created, завершена 10.07
Object Detail refactor: HTML renderer moved to ui.object_detail_view, screen orchestration split into context/load/render/runtime helpers, вручную проверено на 8572, завершена 10.07
Backup v3.0.3_after_object_detail_refactor created, завершена 10.07
Post-refactor stabilization: old dev mock fixtures removed and Objects Estimation renderer missing helpers restored; File Review Continue verified without grey screen on 8576, завершена 10.07
Backup v3.0.4_after_post_refactor_stabilization created, завершена 10.07
Mistral OCR 4 preprocessing connected before Detection with normalized page package and Free-workspace smoke test, завершена 17.07
Backup v3.0.6_before_ocr_layer created, завершена 17.07
Agent lap timing added for OCR, Detection, Estimation, and total RFQ processing with live Processing timer and File Review breakdown, завершена 17.07
Backup v3.0.7_before_agent_timing created, завершена 17.07
Elapsed timer now starts in the instant upload shell and continues through the real Processing screen without reset, завершена 17.07
Backup v3.0.11_after_continuous_elapsed_timer created, завершена 17.07
Detection Prompt v3 candidate introduced commercial quote-line and independent-product tests; page-23.pdf now resolves into shelving unit, sliding door system, and TV console with compact dimensions, завершена 17.07
Elapsed timer DOM synchronization prevents visible backward second jumps during Processing rerenders, завершена 17.07
Backup v3.0.12_after_detection_prompt_v3_candidate created, завершена 17.07
Upload drop flow and monotonic Elapsed timer hotfix manually verified on localhost:8501 after removing the MutationObserver feedback loop, завершена 17.07
Local Verification Before Push Rule added: interactive changes require explicit local browser confirmation before backup, commit, and push, завершена 17.07
Backup v3.0.14_after_verified_upload_timer_hotfix created, завершена 17.07
OCR v2 evidence pipeline added: PDF pages render at 200 DPI, Mistral returns literal spatial evidence, the complete auditable result is saved in Supabase, and Detection receives region-bound text without OCR-driven object grouping; page-23.pdf locally verified as Shelving Unit, Sliding Panel System, and TV Console in 19.97s total, завершена 18.07
OCR Lab added with versioned profiles, fixed page-23 evidence checks, full JSON artifacts, and 95% literal evidence recall at the 200 DPI baseline, завершена 18.07
Backup v3.0.16_working_ocr_v2_spatial_detection_handoff created, завершена 18.07
Detection metadata roles separated into Project, Partner, Client, Author, Date, and File Quality; project addresses compacted; Anthropic input caching disabled for fresh-file benchmarks; verified no-cache medians are 23.035s for page-23.pdf and 51.831s for Металл (1).pdf, завершена 22.07
Detection V3.2.6 reconciles OCR product-level identities against visual fabrication evidence without a second page pass; verified object boundaries are 3/3/3 for page-23.pdf and 15/15/15 for Металл (1).pdf, with Detection medians 12.476s and 30.285s, завершена 22.07
Detection V3.2.6 restored as the stable checkpoint after rejecting V3.2.7–V3.2.9 naming experiments due quality and timing regressions; 25 tests passed, завершена 22.07
Experimental Naming Split locks Detection object IDs and delegates short semantic labels to a separate Naming Agent; Naming timing is persisted and shown in File Review, завершена 22.07
OCR page rendering and Mistral calls were overlapped, producing about 3.5 seconds of pipeline overlap on the 11-page file; this path remains only as a control after Direct PDF, завершена 22.07
Experimental Direct PDF OCR sends one original PDF in one Mistral request without local rendering or per-page fan-out; three accepted large-file repeats returned 15 objects in 38.216s, 38.586s, and 38.308s total, while external-dimension consistency remains unresolved, завершена 22.07
Unified Detection/OCR roadmap now sequences Direct PDF cold validation, dimension stabilization, text-only Naming, two parallel processing stages, asynchronous audit persistence, progress calibration, and final acceptance benchmarking, завершена 22.07
Backup v3.0.30_experimental_direct_pdf_naming_split_checkpoint created, завершена 22.07
Direct PDF OCR + Naming Split accepted as the single active v3.0.30 baseline and enabled by default for production; no parallel stable/experimental branch retained, завершена 22.07
Fast Direct PDF OCR restored after provider/API drift: one original PDF is sent in one core Mistral OCR request, without bbox annotation or page fan-out; locally verified at 1.9s for page-23.pdf and 3.3s for Металл (1).pdf, завершена 12.09
Text-only Naming checkpoint removes repeated PDF input and uses locked Detection facts plus OCR snippets; measured at 3.6s for page-23.pdf and 10.3s for Металл (1).pdf before planned reintegration into Detection, завершена 12.09
Anthropic SDK pinned to 0.111.0 to restore Messages API compatibility after the production temperature-argument failure, завершена 12.09
API-compatible Direct PDF OCR + Detection + text-only Naming checkpoint reconfirmed at approximately 23s for page-23.pdf and 43s for Металл (1).pdf; speed restored without accepting unresolved object-boundary variance, завершена 12.09
Compact Naming v4 reduced its input by 30–41% and measured 2.934s for page-23.pdf and 2.650s for Металл (1).pdf; short Detection context restored useful categories while object-count variance remains upstream, завершена 12.09
Supabase diagnostics removed from the File Review critical path: the authoritative RFQ result remains synchronous while full OCR JSON and four runtime/usage events are written as one background batch; verified cycles were 18.512s for page-23.pdf and 28.664s for Металл (1).pdf, завершена 12.09
Naming v4 moved outside the File Review critical path: provisional locked labels are shown immediately and unchanged names update automatically in the background; first user-visible laps were approximately 16s and 29s, завершена 12.09
Naming v5 now treats indices and model names as incomplete labels, requires a short physical product category, and composes display names without a dash; locally accepted with approximately 2.9s background Naming, завершена 12.09
Naming v5.1 adopts one English-only MVP label for every object: index plus semantic product name, without a dash or duplicated source-language name; 47 tests passed, завершена 12.09
Detection 3.2.6.1 established as the key rollback checkpoint: Claude receives the byte-identical effective 3.2.6 prompt while File Review renders `Detected Objects: N` from the already-loaded object list. The accepted verification set measured 15.293s for page-23.pdf and 29.381s, 30.293s, and 31.168s for Металл (1).pdf; object counts varied 4 and 13/13/15, so the checkpoint preserves the requested UI feature but does not claim object-boundary stabilization, завершена 13.09
Detection/UI 3.2.6.2 persists File Review object-name edits immediately on Enter or input blur, keeps the user on File Review, synchronizes the local review cache, and prevents deferred Naming from overwriting the committed value; verified directly in Supabase with `unknown_project_run_001 / object-002 / Sliding door panelbjhbj`, завершена 13.09
Detection/UI 3.2.6.3 Page-aware processing progress keeps the exact Golden Detection prompt and schema, assigns 83% of the visible processing range to Detection, replaces the early-sprint curve with an ease-in curve, and adjusts expected Detection pacing from OCR page-count buckets; calibrated from 35 Golden stage-timing runs and 36 page-count matches, verified locally with 53 tests, завершена 14.09
v3.0.41 Large PDF Sonnet transport and resilient Naming checkpoint: oversized PDFs are rendered as one ordered JPEG package for Sonnet while small files retain Golden OCR/Haiku; Naming V5.2 handles one-word categories and isolates bad rows; corrected furniture benchmark is 27 physical objects, with clean runs 25/26/27 by count but no exact 27/27 quality acceptance, завершена 15.09
v3.0.42 Company Access MVP foundation: public one-use owner registration, one pre-generated reusable staff link per company, single-owner enforcement, owner-only Company Profile controls, shared email validation, explicit localhost registration block, public invite forwarding, and company-scoped RFQ/estimate access guards; 121 tests passed, завершена 16.09
Auth/Upload UI stable checkpoint: one-submit Sign in and functional Sign out restored by removing the custom browser-session component from the runtime and returning Auth state transitions to the pre-`58eb6eb` implementation; shared header and accepted Upload/Auth layout retained; user verified locally and 125 tests passed, завершена 16.09
v3.0.49 Company Profile checkpoint: removed the redundant shared logo and Profile action, moved compact Continue to upload and standard Sign out actions into the Profile header, split company settings into General, Contacts, Bank Details, Metrics, Users, and Price List tabs, aligned inputs with the Sign in design contract, preserved hidden VAT/Country values through partial updates, and accepted the revised hierarchy locally; Auth/Upload screens and CSS remain unchanged from v3.0.48, 127 tests passed, завершена 17.09
v3.0.50 tab-scoped Auth session checkpoint: refresh restores the Supabase session from `sessionStorage`, Sign out and invalid-session handling clear browser state, and the zero-height browser component is isolated in the hidden Sidebar so the accepted v3.0.49 Upload/Profile geometry remains unchanged; user verified the refresh and layout behavior locally, 130 tests passed, завершена 17.09
Backup v3.0.50_auth_session_sidebar_checkpoint created and validated, завершена 17.09
v3.0.51 Auth interaction checkpoint: browser storage is read only during Streamlit-session bootstrap, store and clear commands no longer return component callbacks, and the first Profile click is no longer consumed by an Auth rerun; user verified first-click Profile navigation locally, Auth/Profile CSS stayed unchanged, and 133 tests passed, завершена 17.09
Backup v3.0.51_auth_session_first_click_checkpoint created and validated, завершена 17.09
v3.0.52 Company Profile emphasis checkpoint: renamed General to General Details, clarified Company legal name and registration field labels, and standardized every current and future Profile form on a full-width high-emphasis purple Save action with capital-letter text and a stronger purple hover; Auth v3.0.51 remained unchanged and 133 tests passed, завершена 17.09
Backup v3.0.52_company_profile_capital_save_checkpoint created and validated, завершена 17.09
v3.0.53 Company Profile bank-context checkpoint: enlarged the six Profile tabs, renamed Contact Number to House Number, arranged Bank Details into domestic and international rows, displayed Hebrew and English company legal names as half-width read-only context owned exclusively by General Details, retained BIC in the existing `swift` field, and verified that Bank Details cannot write either legal name; 134 tests passed, завершена 17.09
Backup v3.0.53_company_profile_bank_context_checkpoint created and validated, завершена 17.09
v3.0.54 Company Profile Metrics work-in-progress checkpoint: connected the existing company overhead settings and monthly cost records to the Metrics tab, added owner-only partial saves, whole-shekel monthly inputs, deterministic VAT and Total display with Arnona VAT exemption, and reused the stored company VAT rate in Estimation totals; user confirmed the current screen works without delay after a clean restart, and 137 tests passed, завершена 17.09
Backup v3.0.54_company_profile_metrics_wip_checkpoint created and validated, завершена 17.09
v3.0.55 Company Metrics visual checkpoint: renamed the Profile tab to Company Metrics and enlarged the group bars to 50px; the attempted input and white-row height reductions were recorded as visually ineffective and remain explicit follow-up work rather than accepted completion, 137 tests passed, завершена 18.09
Backup v3.0.55_company_metrics_visual_checkpoint created and validated, завершена 18.09
v3.0.56 Company Metrics shared-table checkpoint: replaced the ineffective Streamlit column and native-input approximation with the exact Object Detail HTML-grid and CSS primitives; measured 40px group bars, 51px cost rows, and 34px Monthly Cost inputs; kept VAT and Total derived, retained the Arnona VAT dash, added live calculation and owner-validated snapshot saving, received explicit visual acceptance, and passed 139 tests, завершена 18.09
Backup v3.0.56_company_metrics_shared_table_checkpoint created and validated, завершена 18.09
v3.0.57 Company Profile visual continuation checkpoint: moved Company Metrics first, normalized Israeli phone entry, moved VAT, Warranty reserve, and Management buffer below the expense table, added Other Spendings to Company Metrics and deterministic Object Detail mapping, and preserved the accepted shared table geometry; 145 tests passed. The new Supabase column migration is recorded but not yet applied, so Metrics save remains an explicit follow-up blocker, завершена 18.09
Backup v3.0.57_company_metrics_other_spendings_checkpoint created and validated, завершена 18.09
v3.0.58 Company Profile information-architecture checkpoint: renamed Company Metrics to Overhead Expenses, reserved Labor Costs as the second tab, combined General Details and Bank Details into one five-row Company Details form after Contacts, aligned both legal names on one row, retained Israeli phone formatting, bottom percentage controls, Other Spendings, and the accepted Object Detail table geometry; 145 tests passed. Save behavior is explicitly deferred because form submissions currently return to the first tab and Overhead Expenses persistence still requires a separate verified repair, завершена 18.09
Backup v3.0.58_company_profile_expenses_details_checkpoint created and validated, завершена 18.09
v3.0.59 Overhead Expenses persistence checkpoint: replaced full-page query navigation with a zero-height Streamlit component and isolated fragment save, retained the accepted expense-table geometry and live VAT calculations, changed existing Supabase expense writes from partial upsert to partial update so required hidden settings are preserved, added complete defaults for first-time rows, and passed 147 tests. The user verified fast in-screen saving and persistence locally. A duplicate heading observed after Sign out remains an explicit follow-up regression, завершена 19.09
