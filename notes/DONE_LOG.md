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
