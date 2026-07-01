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
                if (window.parent.__costerlyStopObjectsProgressRuntime) {
                    window.parent.__costerlyStopObjectsProgressRuntime();
                }
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
            const OLD_ANIMATION_TIMER_KEY = "__costerlyObjectsProgressAnimationTimer";
            const SYNCING_KEY = "__costerlyObjectsProgressSyncing";
            const STATE_KEY = "__costerlyObjectsProgressState";
            const STOP_KEY = "__costerlyStopObjectsProgressRuntime";
            const OBJECTS_MARKER_ID = "costerly-objects-screen-active";
            const TRANSITION_SHELL_ID = "costerly-post-upload-transition-shell";
            const SUPABASE_URL = __SUPABASE_URL__;
            const SUPABASE_ANON_KEY = __SUPABASE_ANON_KEY__;
            const ESTIMATE_ID = __ESTIMATE_ID__;
            const INTERVAL_MS = __INTERVAL_MS__;
            const TICK_MS = 500;

            function readNumber(value, fallback) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : fallback;
            }

            function clampPercent(value) {
                return Math.max(0, Math.min(100, readNumber(value, 0)));
            }

            function readMoneyNumber(value) {
                const cleaned = String(value || "").replace(/[^0-9.-]/g, "");
                return readNumber(cleaned, 0);
            }

            function formatMoney(value) {
                const rounded = Math.round(readNumber(value, 0));
                return `₪${rounded.toLocaleString("en-US").replace(/,/g, "\u202f")}`;
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

            function stopRuntime() {
                if (parentWindow[TIMER_KEY]) {
                    parentWindow.clearInterval(parentWindow[TIMER_KEY]);
                }
                if (parentWindow[OLD_ANIMATION_TIMER_KEY]) {
                    parentWindow.clearInterval(parentWindow[OLD_ANIMATION_TIMER_KEY]);
                }
                parentWindow[TIMER_KEY] = null;
                parentWindow[OLD_ANIMATION_TIMER_KEY] = null;
                parentWindow[SYNCING_KEY] = false;
                if (parentWindow[STATE_KEY]) {
                    parentWindow[STATE_KEY].active = false;
                }
            }

            function rowForObject(objectId) {
                return parentDoc.querySelector(
                    `.objects-pricing-row[data-object-key="${CSS.escape(String(objectId || ""))}"]`
                );
            }

            function isProjectCostRow(row) {
                const key = String(row.dataset.objectKey || "").toLowerCase();
                return key === "delivery" || key === "installation";
            }

            function clearProjectCostStatus(row) {
                const selfCostCell = row.querySelector(".objects-pricing-self-cost-cell");
                const actionCell = row.querySelector(".objects-pricing-action-cell");
                if (selfCostCell) selfCostCell.textContent = "";
                if (actionCell) actionCell.innerHTML = "";
            }

            function reviewHref(row, objectId) {
                const estimateId = encodeURIComponent(row.dataset.estimateId || ESTIMATE_ID || "");
                const runId = encodeURIComponent(row.dataset.runId || "");
                const objectParam = encodeURIComponent(String(objectId || ""));
                return `?screen=object_detail&run_id=${runId}&estimate_id=${estimateId}&object_id=${objectParam}`;
            }

            function rowsForEstimate() {
                return Array.from(parentDoc.querySelectorAll(
                    `.objects-pricing-row[data-estimate-id="${CSS.escape(String(ESTIMATE_ID || ""))}"]`
                ));
            }

            function readInitialDisplayedPercent(row) {
                const percentNode = row.querySelector(".objects-progress-percent");
                if (!percentNode) return 0;
                return clampPercent(String(percentNode.textContent || "").replace("%", ""));
            }

            function rowQuantity(row, fallback) {
                const quantityNode = row.querySelector(".objects-pricing-number");
                return readNumber(quantityNode ? quantityNode.textContent : "", readNumber(fallback, 1));
            }

            function ensureStateForRow(row) {
                if (isProjectCostRow(row)) {
                    clearProjectCostStatus(row);
                    return null;
                }

                const objectId = row.dataset.objectKey || "";
                if (!objectId) return null;

                const state = parentWindow[STATE_KEY];
                if (!state.objects[objectId]) {
                    const displayedPercent = readInitialDisplayedPercent(row);
                    state.objects[objectId] = {
                        objectId,
                        status: row.dataset.progressStatus || (displayedPercent > 0 ? "running" : "pending"),
                        backendPercent: displayedPercent,
                        displayedPercent,
                        selfCost: null,
                        quantity: rowQuantity(row, 1),
                        lastBackendAt: Date.now(),
                        lastFillerAt: Date.now()
                    };
                }
                return state.objects[objectId];
            }

            function setAction(row, objectId, status) {
                if (isProjectCostRow(row)) {
                    clearProjectCostStatus(row);
                    return;
                }

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

            function setSalePricing(row, saleUnit, saleTotal) {
                const input = row.querySelector(".objects-pricing-price-input");
                const totalCell = row.querySelector(".objects-pricing-sale-total-cell");
                if (input) input.value = saleUnit == null ? "—" : formatMoney(saleUnit);
                if (totalCell) totalCell.textContent = saleTotal == null ? "" : formatMoney(saleTotal);
            }

            function setSummaryValue(field, value) {
                const node = parentDoc.querySelector(`[data-summary-field="${field}"]`);
                if (!node) return;
                node.textContent = value == null ? "—" : formatMoney(value);
            }

            function objectRows() {
                return rowsForEstimate().filter((row) => {
                    const key = row.dataset.objectKey || "";
                    return key && key !== "delivery" && key !== "installation";
                });
            }

            function updateProjectPricingIfComplete() {
                const rows = objectRows();
                if (!rows.length) return;

                let subtotal = 0;
                for (const row of rows) {
                    const objectState = ensureStateForRow(row);
                    if (!objectState || String(objectState.status).toLowerCase() !== "completed") return;

                    const totalCell = row.querySelector(".objects-pricing-sale-total-cell");
                    subtotal += readMoneyNumber(totalCell ? totalCell.textContent : "");
                }

                const delivery = Math.round(subtotal * 0.03 * 100) / 100;
                const installation = Math.round(subtotal * 0.10 * 100) / 100;
                const projectPrice = Math.round((subtotal + delivery + installation) * 100) / 100;
                const vat = Math.round(projectPrice * 0.18 * 100) / 100;
                const total = Math.round((projectPrice + vat) * 100) / 100;

                const deliveryRow = rowForObject("delivery");
                if (deliveryRow) setSalePricing(deliveryRow, delivery, null);

                const installationRow = rowForObject("installation");
                if (installationRow) setSalePricing(installationRow, installation, null);

                setSummaryValue("project_price", projectPrice);
                setSummaryValue("vat", vat);
                setSummaryValue("total", total);
            }

            function setCompletedPricing(row, objectState) {
                const selfCost = readNumber(objectState.selfCost, NaN);
                if (!Number.isFinite(selfCost)) {
                    const cell = row.querySelector(".objects-pricing-self-cost-cell");
                    if (cell) {
                        cell.innerHTML = (
                            '<span class="objects-progress-status" aria-label="Estimating self cost">'
                            + '<span class="objects-progress-spinner" aria-hidden="true"></span>'
                            + '<span class="objects-progress-percent">100%</span>'
                            + '</span>'
                        );
                    }
                    return;
                }

                const quantity = rowQuantity(row, objectState.quantity || 1);
                const saleUnit = Math.round(selfCost * 1.3 * 100) / 100;
                const saleTotal = Math.round(saleUnit * quantity * 100) / 100;

                const cell = row.querySelector(".objects-pricing-self-cost-cell");
                if (cell) cell.textContent = formatMoney(selfCost);
                setSalePricing(row, saleUnit, saleTotal);
            }

            function renderProgress(row, objectState) {
                if (isProjectCostRow(row)) {
                    clearProjectCostStatus(row);
                    return;
                }

                const cell = row.querySelector(".objects-pricing-self-cost-cell");
                if (!cell) return;

                const status = String(objectState.status || "pending").toLowerCase();
                const percent = Math.round(clampPercent(objectState.displayedPercent));

                if (status === "completed") {
                    setCompletedPricing(row, objectState);
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

                cell.innerHTML = (
                    '<span class="objects-progress-status" aria-label="Estimating self cost">'
                    + '<span class="objects-progress-spinner" aria-hidden="true"></span>'
                    + '<span class="objects-progress-percent">'
                    + `${Math.max(1, percent)}%</span>`
                    + '</span>'
                );
            }

            function applyBackendProgress(progress) {
                const objectId = progress.object_id;
                const row = rowForObject(objectId);
                if (!row) return;
                if (isProjectCostRow(row)) {
                    clearProjectCostStatus(row);
                    return;
                }

                const objectState = ensureStateForRow(row);
                if (!objectState) return;

                const status = String(progress.status || "pending").toLowerCase();
                const backendPercent = clampPercent(progress.progress_percent);

                objectState.status = status;
                objectState.backendPercent = Math.max(objectState.backendPercent || 0, backendPercent);
                objectState.selfCost = progress.self_cost_ex_vat ?? objectState.selfCost;
                objectState.quantity = readNumber(progress.quantity, objectState.quantity || 1);
                objectState.lastBackendAt = Date.now();

                if (status === "completed") {
                    objectState.displayedPercent = 100;
                } else if (status === "running") {
                    objectState.displayedPercent = Math.max(
                        objectState.displayedPercent || 0,
                        objectState.backendPercent,
                        1
                    );
                } else if (status === "failed") {
                    objectState.displayedPercent = objectState.displayedPercent || objectState.backendPercent || 0;
                }

                row.dataset.progressStatus = status;
                renderProgress(row, objectState);
                setAction(row, objectId, status);
                updateProjectPricingIfComplete();
            }

            function renderAll() {
                rowsForEstimate().forEach((row) => {
                    const objectState = ensureStateForRow(row);
                    if (!objectState) return;
                    renderProgress(row, objectState);
                    setAction(row, objectState.objectId, objectState.status);
                });
            }

            function advanceFiller(now) {
                rowsForEstimate().forEach((row) => {
                    const objectState = ensureStateForRow(row);
                    if (!objectState || String(objectState.status).toLowerCase() !== "running") return;

                    const curve = progressCurve(objectState.backendPercent || 0);
                    const lastFillerAt = objectState.lastFillerAt || now;
                    if (objectState.displayedPercent >= curve.cap) return;
                    if (now - lastFillerAt < curve.stepMs) return;

                    const steps = Math.max(1, Math.floor((now - lastFillerAt) / curve.stepMs));
                    objectState.displayedPercent = Math.min(curve.cap, objectState.displayedPercent + steps);
                    objectState.lastFillerAt = now;
                    renderProgress(row, objectState);
                    setAction(row, objectState.objectId, objectState.status);
                });
            }

            async function syncProgress() {
                if (!parentDoc.getElementById(OBJECTS_MARKER_ID)) return;
                if (parentDoc.getElementById(TRANSITION_SHELL_ID)) return;
                if (parentWindow[SYNCING_KEY]) return;

                parentWindow[SYNCING_KEY] = true;
                try {
                    const query = new URLSearchParams({
                        estimate_id: `eq.${ESTIMATE_ID}`,
                        select: "object_id,quantity,status,self_cost_ex_vat,progress_percent,progress_label,progress_updated_at"
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
                        applyBackendProgress(progress);
                    });
                } catch (error) {
                    if (parentWindow.console && parentWindow.console.debug) {
                        parentWindow.console.debug("Objects progress sync skipped", error);
                    }
                } finally {
                    parentWindow[SYNCING_KEY] = false;
                }
            }

            function tick() {
                const state = parentWindow[STATE_KEY];
                if (!state || !state.active || state.estimateId !== ESTIMATE_ID) {
                    stopRuntime();
                    return;
                }
                if (!parentDoc.getElementById(OBJECTS_MARKER_ID)) {
                    stopRuntime();
                    return;
                }
                if (parentDoc.getElementById(TRANSITION_SHELL_ID)) {
                    return;
                }

                const now = Date.now();
                advanceFiller(now);
                if (!state.lastSyncAt || now - state.lastSyncAt >= INTERVAL_MS) {
                    state.lastSyncAt = now;
                    syncProgress();
                }
            }

            if (parentWindow[STOP_KEY]) {
                parentWindow[STOP_KEY]();
            } else {
                stopRuntime();
            }
            parentWindow[STOP_KEY] = stopRuntime;
            parentWindow[STATE_KEY] = {
                active: true,
                estimateId: ESTIMATE_ID,
                lastSyncAt: 0,
                objects: {}
            };

            renderAll();
            syncProgress();
            parentWindow[TIMER_KEY] = parentWindow.setInterval(tick, TICK_MS);
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
