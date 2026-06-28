from __future__ import annotations

import json

import streamlit.components.v1 as components


def install_post_upload_transition_guard(
    transitions: list[dict[str, str]],
    *,
    current_marker_id: str | None = None,
) -> None:
    """Cover old Streamlit DOM during post-upload screen-to-screen reruns."""
    transitions_json = json.dumps(transitions)
    current_marker_id_json = json.dumps(current_marker_id)

    components.html(
        """
        <script>
        (() => {
            const parentDoc = window.parent.document;
            const CONFIG = __TRANSITIONS__;
            const CURRENT_MARKER_ID = __CURRENT_MARKER_ID__;
            const SCRIPT_ID = "COSTERLY_POST_UPLOAD_TRANSITION_GUARD_V1_10_9";
            const STYLE_ID = "costerly-post-upload-transition-style";
            const SHELL_ID = "costerly-post-upload-transition-shell";
            const ACTIVE_CLASS = "costerly-post-upload-transition-active";
            const CONFIG_KEY = "__costerlyPostUploadTransitionConfig";
            const INSTALLED_KEY = "__costerlyPostUploadTransitionGuardInstalled";
            const HANDLER_KEY = "__costerlyPostUploadTransitionClickHandler";
            const PERF_KEY = "__costerlyTransitionPerfEntries";
            const PERF_BASE_KEY = "__costerlyTransitionPerfBase";
            const PERF_PANEL_ID = "costerly-transition-perf-panel";
            const SHOW_PERF_PANEL = false;
            const FALLBACK_STABLE_MS = 250;

            window.parent[CONFIG_KEY] = CONFIG;

            function normalizeText(value) {
                return String(value || "")
                    .replace(/\\s+/g, " ")
                    .trim()
                    .toUpperCase();
            }

            function installStyle() {
                if (parentDoc.getElementById(STYLE_ID)) return;

                const style = parentDoc.createElement("style");
                style.id = STYLE_ID;
                style.textContent = `
                    html.${ACTIVE_CLASS},
                    body.${ACTIVE_CLASS} {
                        overflow: hidden !important;
                    }

                    #${SHELL_ID} {
                        position: fixed;
                        inset: 0;
                        z-index: 2147483100;
                        background: var(--color-bg, #F1EFEF);
                        color: var(--color-text-strong, #2A1F2C);
                        box-sizing: border-box;
                        overflow: hidden;
                    }

                    #${PERF_PANEL_ID} {
                        position: fixed;
                        left: 12px;
                        bottom: 12px;
                        z-index: 2147483201;
                        width: 360px;
                        max-height: 44vh;
                        overflow: auto;
                        box-sizing: border-box;
                        padding: 10px 12px;
                        border: 1px solid rgba(42, 31, 44, 0.18);
                        border-radius: 8px;
                        background: rgba(255, 255, 255, 0.94);
                        color: #17131C;
                        box-shadow: 0 10px 30px rgba(42, 31, 44, 0.14);
                        font-family: var(--font-mono, monospace);
                        font-size: 11px;
                        line-height: 1.35;
                    }

                    #${PERF_PANEL_ID} .costerly-transition-perf-title {
                        margin: 0 0 8px 0;
                        color: #8049C6;
                        font-weight: 700;
                        text-transform: uppercase;
                    }

                    #${PERF_PANEL_ID} .costerly-transition-perf-row {
                        display: grid;
                        grid-template-columns: 58px 1fr;
                        gap: 6px;
                        padding: 3px 0;
                        border-top: 1px solid rgba(42, 31, 44, 0.08);
                    }

                    #${PERF_PANEL_ID} span {
                        color: rgba(42, 31, 44, 0.58);
                    }

                    #${PERF_PANEL_ID} strong {
                        color: #17131C;
                        font-weight: 700;
                    }

                    #${PERF_PANEL_ID} em {
                        grid-column: 2;
                        color: rgba(42, 31, 44, 0.62);
                        font-style: normal;
                        word-break: break-word;
                    }
                `;
                parentDoc.head.appendChild(style);
            }

            function escapeHtml(value) {
                return String(value || "")
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;");
            }

            function renderPerfPanel() {
                if (!SHOW_PERF_PANEL) return;

                const entries = window.parent[PERF_KEY] || [];
                if (!entries.length) return;

                installStyle();
                let panel = parentDoc.getElementById(PERF_PANEL_ID);
                if (!panel) {
                    panel = parentDoc.createElement("div");
                    panel.id = PERF_PANEL_ID;
                    parentDoc.body.appendChild(panel);
                }

                const rows = entries.slice(-18).map((entry) => {
                    const detail = Object.entries(entry.detail || {})
                        .map(([key, value]) => `${escapeHtml(key)}=${escapeHtml(value)}`)
                        .join(" ");
                    return `
                        <div class="costerly-transition-perf-row">
                            <span>${entry.elapsedMs.toFixed(1)}ms</span>
                            <strong>${escapeHtml(entry.label)}</strong>
                            <em>${detail}</em>
                        </div>
                    `;
                }).join("");

                panel.innerHTML = `
                    <div class="costerly-transition-perf-title">Transition perf</div>
                    ${rows}
                `;
            }

            function recordPerf(label, detail = {}) {
                const now = window.parent.performance.now();
                if (!window.parent[PERF_BASE_KEY]) {
                    window.parent[PERF_BASE_KEY] = now;
                }

                const entries = window.parent[PERF_KEY] || [];
                const entry = {
                    label,
                    detail,
                    elapsedMs: now - window.parent[PERF_BASE_KEY],
                    absoluteMs: now
                };
                entries.push(entry);
                window.parent[PERF_KEY] = entries.slice(-60);
                renderPerfPanel();

                if (window.parent.console && window.parent.console.table) {
                    window.parent.console.table(window.parent[PERF_KEY]);
                }
            }

            function removeShell() {
                const shell = parentDoc.getElementById(SHELL_ID);
                const wasActive =
                    Boolean(shell) ||
                    parentDoc.documentElement.classList.contains(ACTIVE_CLASS) ||
                    parentDoc.body.classList.contains(ACTIVE_CLASS);
                if (wasActive) {
                    recordPerf("shell removed");
                }
                if (shell) shell.remove();

                parentDoc.documentElement.classList.remove(ACTIVE_CLASS);
                parentDoc.body.classList.remove(ACTIVE_CLASS);
            }

            function targetIsActive(targetMarkerId) {
                return Boolean(targetMarkerId && parentDoc.getElementById(targetMarkerId));
            }

            function clearForCurrentScreen() {
                if (!targetIsActive(CURRENT_MARKER_ID)) return;
                recordPerf("marker appeared", { marker: CURRENT_MARKER_ID });

                let removed = false;
                function removeOnce() {
                    if (removed) return;
                    removed = true;
                    removeShell();
                }

                window.parent.requestAnimationFrame(() => {
                    window.parent.requestAnimationFrame(removeOnce);
                });
                window.parent.setTimeout(removeOnce, FALLBACK_STABLE_MS);
            }

            function getCurrentHeaderRect() {
                const existingShell = parentDoc.getElementById(SHELL_ID);
                const headers = Array.from(parentDoc.querySelectorAll(".post-upload-screen-shell"));
                const currentHeader = headers.find((header) => {
                    if (existingShell && existingShell.contains(header)) return false;

                    const rect = header.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                });

                if (!currentHeader) return null;

                const rect = currentHeader.getBoundingClientRect();
                return {
                    left: rect.left,
                    top: rect.top,
                    width: rect.width
                };
            }

            function alignHeaderToRect(shell, rect) {
                if (!rect) return;

                const header = shell.querySelector(".post-upload-screen-shell");
                if (!header) return;

                header.style.position = "fixed";
                header.style.left = `${Math.round(rect.left)}px`;
                header.style.top = `${Math.round(rect.top)}px`;
                header.style.width = `${Math.round(rect.width)}px`;
                header.style.margin = "0";
            }

            function showShell(transition) {
                if (!transition) return;

                installStyle();
                recordPerf("show shell start", { target: transition.targetMarkerId || "" });
                const headerRect = getCurrentHeaderRect();
                removeShell();

                const shell = parentDoc.createElement("div");
                shell.id = SHELL_ID;
                shell.dataset.targetMarkerId = transition.targetMarkerId || "";
                shell.innerHTML = transition.shellHtml || "";
                alignHeaderToRect(shell, headerRect);
                parentDoc.body.appendChild(shell);

                parentDoc.documentElement.classList.add(ACTIVE_CLASS);
                parentDoc.body.classList.add(ACTIVE_CLASS);
                recordPerf("shell shown", { target: transition.targetMarkerId || "" });

                window.parent.setTimeout(() => {
                    const activeShell = parentDoc.getElementById(SHELL_ID);
                    if (
                        activeShell &&
                        activeShell.dataset.targetMarkerId === (transition.targetMarkerId || "")
                    ) {
                        removeShell();
                    }
                }, 45000);
            }

            function findTransition(event) {
                const target = event.target;
                if (!target || !target.closest) return null;

                const control = target.closest("button, a, [role='button']");
                if (!control) return null;

                const label = normalizeText(control.innerText || control.textContent);
                return (window.parent[CONFIG_KEY] || []).find((transition) => {
                    return normalizeText(transition.label) === label;
                });
            }

            function handleClick(event) {
                const transition = findTransition(event);
                if (!transition) return;

                window.parent[PERF_BASE_KEY] = window.parent.performance.now();
                window.parent[PERF_KEY] = [];
                recordPerf("click", { label: transition.label || "" });
                showShell(transition);
            }

            const oldScript = parentDoc.getElementById(SCRIPT_ID);
            if (oldScript) oldScript.remove();

            const marker = parentDoc.createElement("script");
            marker.id = SCRIPT_ID;
            marker.type = "application/json";
            marker.textContent = "installed";
            parentDoc.head.appendChild(marker);

            if (window.parent[HANDLER_KEY]) {
                parentDoc.removeEventListener("click", window.parent[HANDLER_KEY], true);
            }

            window.parent[INSTALLED_KEY] = true;
            parentDoc.addEventListener("click", handleClick, true);
            window.parent[HANDLER_KEY] = handleClick;

            clearForCurrentScreen();
        })();
        </script>
        """
        .replace("__TRANSITIONS__", transitions_json)
        .replace("__CURRENT_MARKER_ID__", current_marker_id_json),
        height=0,
        width=0,
    )


def clear_upload_processing_shell() -> None:
    """Remove the instant upload processing shell after Streamlit reaches a real screen."""
    components.html(
        """
        <script>
        (() => {
            const parentDoc = window.parent.document;
            const shell = parentDoc.getElementById('costerly-upload-processing-shell');
            if (shell) shell.remove();

            parentDoc.documentElement.classList.remove('costerly-upload-processing-shell-active');
            parentDoc.body.classList.remove('costerly-upload-processing-shell-active');
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def scroll_parent_to_top() -> None:
    """Reset browser scroll after a screen-level Streamlit navigation."""
    components.html(
        """
        <script>
        (() => {
            const parentWindow = window.parent;
            const parentDoc = parentWindow.document;

            function scrollTopNow() {
                parentWindow.scrollTo({ top: 0, left: 0, behavior: "auto" });
                parentDoc.documentElement.scrollTop = 0;
                parentDoc.body.scrollTop = 0;

                parentDoc
                    .querySelectorAll('section, main, div, [data-testid="stAppViewContainer"]')
                    .forEach((node) => {
                        if (node.scrollTop) {
                            node.scrollTop = 0;
                        }
                    });
            }

            scrollTopNow();
            parentWindow.requestAnimationFrame(scrollTopNow);
            parentWindow.setTimeout(scrollTopNow, 50);
            parentWindow.setTimeout(scrollTopNow, 250);
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def install_objects_progress_animation() -> None:
    """Animate visible object-estimation percentages without rerunning Streamlit."""
    components.html(
        """
        <script>
        (() => {
            const parentWindow = window.parent;
            const parentDoc = parentWindow.document;
            const TIMER_KEY = "__costerlyObjectsProgressAnimationTimer";

            function readNumber(value, fallback) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : fallback;
            }

            function tick() {
                parentDoc.querySelectorAll(".objects-progress-percent").forEach((node) => {
                    const start = readNumber(node.dataset.start, 0);
                    const cap = readNumber(node.dataset.cap, start);
                    const stepMs = readNumber(node.dataset.stepMs, 1000);
                    const updatedAtMs = Date.parse(node.dataset.updatedAt || "");
                    if (!Number.isFinite(updatedAtMs) || stepMs <= 0) return;

                    const elapsedMs = Math.max(0, Date.now() - updatedAtMs);
                    const value = Math.min(cap, start + Math.floor(elapsedMs / stepMs));
                    node.textContent = `${Math.max(1, value)}%`;
                });
            }

            if (parentWindow[TIMER_KEY]) {
                parentWindow.clearInterval(parentWindow[TIMER_KEY]);
            }
            tick();
            parentWindow[TIMER_KEY] = parentWindow.setInterval(tick, 1000);
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def install_objects_progress_sync(
    *,
    supabase_url: str,
    supabase_anon_key: str,
    estimate_id: str,
    interval_ms: int = 1500,
) -> None:
    """Sync object progress from Supabase without rerunning Streamlit."""
    supabase_url_json = json.dumps(supabase_url.rstrip("/"))
    supabase_anon_key_json = json.dumps(supabase_anon_key)
    estimate_id_json = json.dumps(estimate_id)
    interval_json = json.dumps(interval_ms)
    components.html(
        """
        <script>
        (() => {
            const parentWindow = window.parent;
            const parentDoc = parentWindow.document;
            const TIMER_KEY = "__costerlyObjectsProgressSyncTimer";
            const SYNCING_KEY = "__costerlyObjectsProgressSyncing";
            const OBJECTS_MARKER_ID = "costerly-objects-screen-active";
            const SUPABASE_URL = __SUPABASE_URL__;
            const SUPABASE_ANON_KEY = __SUPABASE_ANON_KEY__;
            const ESTIMATE_ID = __ESTIMATE_ID__;
            const INTERVAL_MS = __INTERVAL_MS__;

            function readNumber(value, fallback) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : fallback;
            }

            function escapeHtml(value) {
                return String(value || "")
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;");
            }

            function progressCurve(base) {
                if (base < 25) return { cap: 24, stepMs: 400 };
                if (base < 65) return { cap: 64, stepMs: 500 };
                if (base < 78) return { cap: 77, stepMs: 300 };
                if (base < 88) return { cap: 87, stepMs: 250 };
                if (base < 96) return { cap: 95, stepMs: 200 };
                return { cap: 99, stepMs: 200 };
            }

            if (parentWindow[TIMER_KEY]) {
                parentWindow.clearInterval(parentWindow[TIMER_KEY]);
            }

            function rowForObject(objectId) {
                return parentDoc.querySelector(
                    `.objects-pricing-row[data-object-key="${CSS.escape(String(objectId || ""))}"]`
                );
            }

            function reviewHref(row, objectId) {
                const estimateId = encodeURIComponent(row.dataset.estimateId || ESTIMATE_ID || "");
                const runId = encodeURIComponent(row.dataset.runId || "");
                const objectParam = encodeURIComponent(String(objectId || ""));
                return `?screen=object_detail&run_id=${runId}&estimate_id=${estimateId}&object_id=${objectParam}`;
            }

            function setAction(row, objectId, status) {
                const cell = row.querySelector('[data-action-cell="true"]');
                if (!cell) return;

                if (status === "completed") {
                    cell.innerHTML = (
                        `<a class="objects-pricing-review-button" href="${reviewHref(row, objectId)}" target="_self">Review</a>`
                    );
                    return;
                }

                const label = status === "running" ? "Estimating" : status === "failed" ? "Failed" : "Pending";
                cell.innerHTML = (
                    `<span class="objects-pricing-review-button objects-pricing-review-button--disabled" aria-disabled="true">`
                    + `${escapeHtml(label)}</span>`
                );
            }

            function setProgress(row, progress) {
                const cell = row.querySelector(".objects-pricing-self-cost-cell");
                if (!cell) return;

                const status = String(progress.status || "pending").toLowerCase();
                const percent = Math.max(0, Math.min(100, readNumber(progress.progress_percent, 0)));
                const updatedAt = progress.progress_updated_at || new Date().toISOString();

                if (status === "completed") {
                    cell.innerHTML = '<span class="objects-progress-percent">100%</span>';
                    return;
                }

                if (status === "failed") {
                    cell.textContent = "failed";
                    return;
                }

                if (status !== "running") {
                    cell.textContent = "pending";
                    return;
                }

                const curve = progressCurve(percent);
                cell.innerHTML = (
                    '<span class="objects-progress-percent" '
                    + `data-start="${percent}" `
                    + `data-cap="${curve.cap}" `
                    + `data-step-ms="${curve.stepMs}" `
                    + `data-updated-at="${escapeHtml(updatedAt)}">`
                    + `${Math.max(1, percent)}%</span>`
                );
            }

            async function syncProgress() {
                if (!parentDoc.getElementById(OBJECTS_MARKER_ID)) return;
                if (parentWindow[SYNCING_KEY]) return;

                parentWindow[SYNCING_KEY] = true;
                try {
                    const query = new URLSearchParams({
                        estimate_id: `eq.${ESTIMATE_ID}`,
                        select: "object_id,status,progress_percent,progress_label,progress_updated_at"
                    });
                    const response = await fetch(`${SUPABASE_URL}/rest/v1/rfq_object_estimate_progress_public?${query}`, {
                        headers: {
                            apikey: SUPABASE_ANON_KEY,
                            Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
                            Accept: "application/json"
                        }
                    });
                    if (!response.ok) return;

                    const rows = await response.json();
                    rows.forEach((progress) => {
                        const objectId = progress.object_id;
                        const row = rowForObject(objectId);
                        if (!row) return;
                        const status = String(progress.status || "pending").toLowerCase();
                        row.dataset.progressStatus = status;
                        setProgress(row, progress);
                        setAction(row, objectId, status);
                    });
                } catch (error) {
                    if (parentWindow.console && parentWindow.console.debug) {
                        parentWindow.console.debug("Objects progress sync skipped", error);
                    }
                } finally {
                    parentWindow[SYNCING_KEY] = false;
                }
            }

            syncProgress();
            parentWindow[TIMER_KEY] = parentWindow.setInterval(syncProgress, INTERVAL_MS);
        })();
        </script>
        """
        .replace("__SUPABASE_URL__", supabase_url_json)
        .replace("__SUPABASE_ANON_KEY__", supabase_anon_key_json)
        .replace("__ESTIMATE_ID__", estimate_id_json)
        .replace("__INTERVAL_MS__", interval_json),
        height=0,
        width=0,
    )


def install_upload_processing_shell(shell_html: str) -> None:
    """Show the processing layout immediately after a file is selected.

    Called by the upload screen after the native file uploader exists. This is
    client-side only: it does not change Streamlit state or start processing.
    """
    shell_html_json = json.dumps(shell_html)

    components.html(
        """
        <script>
        (() => {
            const parentDoc = window.parent.document;
            const markerId = "COSTERLY_UPLOAD_PROCESSING_SHELL_GUARD_V1_1_2";
            const oldMarker = parentDoc.getElementById(markerId);

            if (oldMarker) {
                oldMarker.remove();
            }

            const script = parentDoc.createElement("script");
            script.id = markerId;

            script.textContent = "(" + function () {
                const SHELL_HTML = __SHELL_HTML__;
                const DROPZONE_SELECTOR = 'section[data-testid="stFileUploaderDropzone"]';
                const FILE_INPUT_SELECTOR = 'input[type="file"]';
                const SHELL_ID = 'costerly-upload-processing-shell';
                const STYLE_ID = 'costerly-upload-processing-shell-style';
                const REAL_PROCESSING_MARKER_ID = 'costerly-processing-screen-active';
                const SHELL_ACTIVE_CLASS = 'costerly-upload-processing-shell-active';
                const BOUND_ATTR = 'data-costerly-processing-shell-bound';
                const INSTALLED_FLAG = '__costerlyUploadProcessingShellGuardV112Installed';
                let watcher = null;
                let slowTimer = null;

                if (window[INSTALLED_FLAG]) {
                    return;
                }

                window[INSTALLED_FLAG] = true;

                function realProcessingIsActive() {
                    return Boolean(document.getElementById(REAL_PROCESSING_MARKER_ID));
                }

                function installStyle() {
                    if (document.getElementById(STYLE_ID)) return;

                    const style = document.createElement('style');
                    style.id = STYLE_ID;
                    style.textContent = `
                        html.${SHELL_ACTIVE_CLASS},
                        body.${SHELL_ACTIVE_CLASS} {
                            overflow: hidden !important;
                        }

                        #${SHELL_ID} {
                            position: fixed;
                            inset: 0;
                            z-index: 2147483000;
                            box-sizing: border-box;
                            overflow: hidden;
                        }

                        #${SHELL_ID}[data-slow="true"] .post-upload-stage__slow {
                            display: block;
                        }
                    `;
                    document.head.appendChild(style);
                }

                function removeShell() {
                    const shell = document.getElementById(SHELL_ID);
                    if (shell) shell.remove();

                    document.documentElement.classList.remove(SHELL_ACTIVE_CLASS);
                    document.body.classList.remove(SHELL_ACTIVE_CLASS);

                    if (slowTimer) {
                        window.clearTimeout(slowTimer);
                        slowTimer = null;
                    }
                }

                function startWatcher() {
                    if (watcher) return;

                    watcher = window.setInterval(() => {
                        if (realProcessingIsActive()) {
                            removeShell();
                            window.clearInterval(watcher);
                            watcher = null;
                        }
                    }, 80);
                }

                function showShell(source) {
                    if (realProcessingIsActive()) return;

                    installStyle();

                    let shell = document.getElementById(SHELL_ID);
                    if (!shell) {
                        shell = document.createElement('div');
                        shell.id = SHELL_ID;
                        shell.innerHTML = SHELL_HTML;
                        document.body.appendChild(shell);
                    }

                    shell.dataset.source = source || 'unknown';
                    shell.dataset.slow = 'false';
                    document.documentElement.classList.add(SHELL_ACTIVE_CLASS);
                    document.body.classList.add(SHELL_ACTIVE_CLASS);

                    if (slowTimer) window.clearTimeout(slowTimer);
                    slowTimer = window.setTimeout(() => {
                        const activeShell = document.getElementById(SHELL_ID);
                        if (activeShell && !realProcessingIsActive()) {
                            activeShell.dataset.slow = 'true';
                        }
                    }, 25000);

                    startWatcher();
                }

                function hasDroppedFiles(event) {
                    return Boolean(
                        event.dataTransfer &&
                        event.dataTransfer.files &&
                        event.dataTransfer.files.length > 0
                    );
                }

                function bindInputs() {
                    document.querySelectorAll(FILE_INPUT_SELECTOR).forEach((input) => {
                        if (input.getAttribute(BOUND_ATTR) === 'true') return;
                        input.setAttribute(BOUND_ATTR, 'true');

                        input.addEventListener('change', () => {
                            if (input.files && input.files.length > 0) {
                                showShell('input-change');
                            }
                        }, true);
                    });
                }

                document.addEventListener('drop', (event) => {
                    const dropzone = event.target.closest(DROPZONE_SELECTOR);
                    if (dropzone && hasDroppedFiles(event)) {
                        window.setTimeout(() => showShell('drop'), 0);
                    }
                }, true);

                document.addEventListener('change', (event) => {
                    const target = event.target;
                    if (
                        target &&
                        target.matches &&
                        target.matches(FILE_INPUT_SELECTOR) &&
                        target.files &&
                        target.files.length > 0
                    ) {
                        showShell('document-change');
                    }
                }, true);

                const observer = new MutationObserver(() => {
                    bindInputs();
                    if (realProcessingIsActive()) removeShell();
                });

                observer.observe(document.body, { childList: true, subtree: true });
                bindInputs();
                startWatcher();
            }.toString() + ")();";

            parentDoc.head.appendChild(script);
        })();
        </script>
        """.replace("__SHELL_HTML__", shell_html_json),
        height=0,
        width=0,
    )


def install_upload_dragover_guard() -> None:
    """Add stable dragover classes to Streamlit's native file uploader.

    Called by the upload screen after the file uploader is rendered. The helper
    watches for Streamlit rerenders, finds the current dropzone, and toggles our
    own class names instead of relying on Streamlit's dynamic Emotion classes.
    """
    components.html(
        """
        <script>
        (() => {
            const parentDoc = window.parent.document;
            const markerId = "COSTERLY_UPLOAD_DRAGOVER_GUARD_V1_0_1";
            const oldMarker = parentDoc.getElementById(markerId);

            if (oldMarker) {
                oldMarker.remove();
            }

            const script = parentDoc.createElement("script");
            script.id = markerId;

            script.textContent = `
            (() => {
                const DROPZONE_SELECTOR = 'section[data-testid="stFileUploaderDropzone"]';
                const DRAG_CLASS = 'costerly-upload-dragover';
                let clearTimer = null;

                function getDropzones() {
                    return Array.from(document.querySelectorAll(DROPZONE_SELECTOR));
                }

                function hasFiles(event) {
                    const dt = event.dataTransfer;
                    if (!dt) return true;

                    const types = Array.from(dt.types || []);
                    return types.includes('Files') || types.includes('application/x-moz-file');
                }

                function setDragover(dropzone, on) {
                    getDropzones().forEach((zone) => {
                        zone.classList.toggle(DRAG_CLASS, Boolean(on) && zone === dropzone);
                    });
                }

                function clearDragover() {
                    window.clearTimeout(clearTimer);
                    setDragover(null, false);
                }

                function forceDragover(event) {
                    if (!hasFiles(event)) return;

                    const dropzone = event.target.closest(DROPZONE_SELECTOR);

                    if (!dropzone) {
                        clearDragover();
                        return;
                    }

                    event.preventDefault();
                    window.clearTimeout(clearTimer);
                    setDragover(dropzone, true);
                }

                document.addEventListener('dragenter', forceDragover, true);
                document.addEventListener('dragover', forceDragover, true);
                document.addEventListener('dragleave', () => {
                    window.clearTimeout(clearTimer);
                    clearTimer = window.setTimeout(clearDragover, 140);
                }, true);
                document.addEventListener('drop', clearDragover, true);
                document.addEventListener('dragend', clearDragover, true);
                window.addEventListener('blur', clearDragover, true);
            })();
            `;

            parentDoc.head.appendChild(script);
        })();
        </script>
        """,
        height=0,
        width=0,
    )
