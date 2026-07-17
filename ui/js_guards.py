from __future__ import annotations

import json

import streamlit.components.v1 as components


def signal_app_ready_to_embed(screen: str) -> None:
    """Tell the embedding Cloudflare wrapper that a real Streamlit screen rendered."""
    screen_json = json.dumps(screen)

    components.html(
        """
        <script>
        (() => {
            const message = {
                type: "costerly:app-ready",
                screen: __SCREEN__,
                sentAt: Date.now()
            };

            function postReady() {
                try {
                    window.parent.postMessage(message, "*");
                } catch (error) {}

                try {
                    window.parent.parent.postMessage(message, "*");
                } catch (error) {}

                try {
                    window.top.postMessage(message, "*");
                } catch (error) {}
            }

            postReady();
            window.requestAnimationFrame(() => {
                window.requestAnimationFrame(postReady);
            });
            window.setTimeout(postReady, 120);
        })();
        </script>
        """.replace("__SCREEN__", screen_json),
        height=0,
        width=0,
    )


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
                `;
                parentDoc.head.appendChild(style);
            }

            function removeShell() {
                const shell = parentDoc.getElementById(SHELL_ID);
                if (shell) shell.remove();

                parentDoc.documentElement.classList.remove(ACTIVE_CLASS);
                parentDoc.body.classList.remove(ACTIVE_CLASS);
            }

            function targetIsActive(targetMarkerId) {
                return Boolean(targetMarkerId && parentDoc.getElementById(targetMarkerId));
            }

            function clearForCurrentScreen() {
                if (!targetIsActive(CURRENT_MARKER_ID)) return;
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

            function clearWithoutTransitionTargets() {
                if (CONFIG.length) return;
                if (window.parent.__costerlyObjectDetailInputGuardCleanup) {
                    window.parent.__costerlyObjectDetailInputGuardCleanup();
                }
                if (window.parent.__costerlyStopObjectsProgressRuntime) {
                    window.parent.__costerlyStopObjectsProgressRuntime();
                }
                window.parent.__costerlyObjectDetailSubmittingSnapshot = false;
                removeShell();
                const uploadShell = parentDoc.getElementById("costerly-upload-processing-shell");
                if (uploadShell) uploadShell.remove();
                parentDoc.documentElement.classList.remove("costerly-upload-processing-shell-active");
                parentDoc.body.classList.remove("costerly-upload-processing-shell-active");
                window.parent.requestAnimationFrame(removeShell);
                window.parent.setTimeout(removeShell, FALLBACK_STABLE_MS);
                window.parent.setTimeout(removeShell, 1200);
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

            clearWithoutTransitionTargets();
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


def install_objects_price_input_guard(
    *,
    estimate_id: str,
    supabase_url: str | None = None,
    supabase_anon_key: str | None = None,
) -> None:
    """Install always-on editing behavior for Objects sale price controls."""
    estimate_id_json = json.dumps(estimate_id)
    supabase_url_json = json.dumps(supabase_url.rstrip("/")) if supabase_url else "null"
    supabase_anon_key_json = json.dumps(supabase_anon_key) if supabase_anon_key else "null"
    components.html(
        """
        <script>
        (() => {
            const parentWindow = window.parent;
            const parentDoc = parentWindow.document;
            const ESTIMATE_ID = __ESTIMATE_ID__;
            const SUPABASE_URL = __SUPABASE_URL__;
            const SUPABASE_ANON_KEY = __SUPABASE_ANON_KEY__;
            const HANDLER_KEY = "__costerlyObjectsPriceInputGuardCleanup";
            const MANUAL_PRICES_KEY = "__costerlyObjectsManualSalePrices";
            let pointerStartedInPriceInput = false;

            if (parentWindow[HANDLER_KEY]) parentWindow[HANDLER_KEY]();

            function readNumber(value, fallback) {
                const parsed = Number(value);
                return Number.isFinite(parsed) ? parsed : fallback;
            }

            function readMoneyNumber(value) {
                const cleaned = String(value || "").replace(/[^0-9.-]/g, "");
                return readNumber(cleaned, 0);
            }

            function inputDigits(value) {
                return String(value || "").replace(/[^0-9]/g, "");
            }

            function formatMoney(value) {
                const rounded = Math.round(readNumber(value, 0));
                return `₪${rounded.toLocaleString("en-US").replace(/,/g, "\u202f")}`;
            }

            function context(event) {
                const target = event.target;
                if (!target || !target.closest) return null;
                const input = target.closest(".objects-pricing-price-input");
                if (!input) return null;
                const row = input.closest(".objects-pricing-row");
                if (!row || row.dataset.estimateId !== String(ESTIMATE_ID || "")) return null;
                return { input, row };
            }

            function isDisabled(input) {
                return input.getAttribute("aria-disabled") === "true" || input.disabled === true;
            }

            function saleInputValue(input) {
                if (!input) return "";
                return "value" in input ? input.value : input.textContent;
            }

            function setSaleInputValue(input, value) {
                if (!input) return;
                if ("value" in input) {
                    input.value = value;
                } else {
                    input.textContent = value;
                }
            }

            function rowQuantity(row) {
                const node = row.querySelector(".objects-pricing-number");
                return readNumber(node ? node.textContent : "", 1);
            }

            function rowSaleUnit(row) {
                return readMoneyNumber(saleInputValue(row.querySelector(".objects-pricing-price-input")));
            }

            function isProjectCostRow(row) {
                const key = String(row.dataset.objectKey || "").toLowerCase();
                return key === "delivery" || key === "installation";
            }

            function hideProjectCostSuggestion(row) {
                if (!isProjectCostRow(row)) return;
                const suggestion = row.querySelector(".objects-pricing-suggestion");
                if (suggestion) suggestion.textContent = "";
            }

            function manualPrices() {
                if (!parentWindow[MANUAL_PRICES_KEY]) parentWindow[MANUAL_PRICES_KEY] = {};
                if (!parentWindow[MANUAL_PRICES_KEY][ESTIMATE_ID]) parentWindow[MANUAL_PRICES_KEY][ESTIMATE_ID] = {};
                return parentWindow[MANUAL_PRICES_KEY][ESTIMATE_ID];
            }

            function seedManualPricesFromDom() {
                const prices = manualPrices();
                for (const row of parentDoc.querySelectorAll(
                    `.objects-pricing-row[data-estimate-id="${CSS.escape(String(ESTIMATE_ID || ""))}"]`
                )) {
                    const input = row.querySelector('.objects-pricing-price-input[data-pricing-overridden="true"]');
                    const objectKey = row.dataset.objectKey || "";
                    if (!input || !objectKey || Number.isFinite(prices[objectKey])) continue;
                    prices[objectKey] = Math.max(0, Math.round(readMoneyNumber(saleInputValue(input))));
                    input.dataset.userEdited = "true";
                    hideProjectCostSuggestion(row);
                }
            }

            function setManualSaleUnit(row, value) {
                const key = row.dataset.objectKey || "";
                if (!key) return;
                manualPrices()[key] = Math.max(0, Math.round(readNumber(value, 0)));
                const input = row.querySelector(".objects-pricing-price-input");
                if (input) input.dataset.userEdited = "true";
                hideProjectCostSuggestion(row);
            }

            async function persistManualSaleUnit(row, value) {
                if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return;
                const objectKey = row ? row.dataset.objectKey || "" : "";
                if (!objectKey) return;
                const payload = {
                    estimate_id: ESTIMATE_ID,
                    object_key: objectKey,
                    field: "sale_price_unit",
                    value: Math.max(0, Math.round(readNumber(value, 0))),
                    updated_at: new Date().toISOString(),
                };
                try {
                    await fetch(`${SUPABASE_URL}/rest/v1/rfq_estimate_pricing_overrides?on_conflict=estimate_id,object_key,field`, {
                        method: "POST",
                        headers: {
                            "apikey": SUPABASE_ANON_KEY,
                            "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
                            "Content-Type": "application/json",
                            "Prefer": "resolution=merge-duplicates,return=minimal",
                        },
                        body: JSON.stringify(payload),
                    });
                } catch (error) {
                    if (parentWindow.console && parentWindow.console.warn) {
                        parentWindow.console.warn("Could not persist pricing override", error);
                    }
                }
            }

            function rowsForEstimate() {
                return Array.from(parentDoc.querySelectorAll(
                    `.objects-pricing-row[data-estimate-id="${CSS.escape(String(ESTIMATE_ID || ""))}"]`
                ));
            }

            function objectRows() {
                return rowsForEstimate().filter((row) => {
                    const key = String(row.dataset.objectKey || "").toLowerCase();
                    return key && key !== "delivery" && key !== "installation";
                });
            }

            function rowForObject(objectKey) {
                return parentDoc.querySelector(
                    `.objects-pricing-row[data-estimate-id="${CSS.escape(String(ESTIMATE_ID || ""))}"][data-object-key="${CSS.escape(String(objectKey || ""))}"]`
                );
            }

            function setSummaryValue(field, value) {
                const node = parentDoc.querySelector(`[data-summary-field="${field}"]`);
                if (node) node.textContent = value == null ? "—" : formatMoney(value);
            }

            function updateLineTotal(row) {
                if (isProjectCostRow(row)) return;
                const totalCell = row.querySelector(".objects-pricing-sale-total-cell");
                if (!totalCell) return;
                totalCell.textContent = formatMoney(rowSaleUnit(row) * rowQuantity(row));
            }

            function updateProjectPricing() {
                let subtotal = 0;
                for (const row of objectRows()) {
                    const totalCell = row.querySelector(".objects-pricing-sale-total-cell");
                    subtotal += readMoneyNumber(totalCell ? totalCell.textContent : "");
                }

                const deliveryRow = rowForObject("delivery");
                const installationRow = rowForObject("installation");
                const prices = manualPrices();
                const deliveryDefault = Math.round(subtotal * 0.03 * 100) / 100;
                const installationDefault = Math.round(subtotal * 0.10 * 100) / 100;
                const delivery = Number.isFinite(prices.delivery) ? prices.delivery : deliveryDefault;
                const installation = Number.isFinite(prices.installation) ? prices.installation : installationDefault;
                if (deliveryRow && Number.isFinite(prices.delivery)) hideProjectCostSuggestion(deliveryRow);
                if (installationRow && Number.isFinite(prices.installation)) hideProjectCostSuggestion(installationRow);

                if (deliveryRow && !Number.isFinite(prices.delivery)) {
                    const input = deliveryRow.querySelector(".objects-pricing-price-input");
                    if (input && parentDoc.activeElement !== input && input.getAttribute("aria-disabled") !== "true") {
                        setSaleInputValue(input, formatMoney(deliveryDefault));
                    }
                }
                if (installationRow && !Number.isFinite(prices.installation)) {
                    const input = installationRow.querySelector(".objects-pricing-price-input");
                    if (input && parentDoc.activeElement !== input && input.getAttribute("aria-disabled") !== "true") {
                        setSaleInputValue(input, formatMoney(installationDefault));
                    }
                }

                const projectPrice = Math.round((subtotal + delivery + installation) * 100) / 100;
                const vat = Math.round(projectPrice * 0.18 * 100) / 100;
                setSummaryValue("project_price", projectPrice);
                setSummaryValue("vat", vat);
                setSummaryValue("total", Math.round((projectPrice + vat) * 100) / 100);
            }

            function sanitizeActive(input) {
                const digits = inputDigits(saleInputValue(input));
                if (saleInputValue(input) !== digits) setSaleInputValue(input, digits);
                return digits;
            }

            function handleFocus(event) {
                const ctx = context(event);
                if (!ctx || isDisabled(ctx.input)) return;
                const digits = inputDigits(saleInputValue(ctx.input));
                ctx.input.dataset.editStartDigits = digits;
                ctx.input.dataset.editDirty = "false";
                setSaleInputValue(ctx.input, digits);
            }

            function handlePointerDown(event) {
                const target = event.target;
                pointerStartedInPriceInput = Boolean(
                    target && target.closest && target.closest(".objects-pricing-price-input")
                );
            }

            function handleKeydown(event) {
                const ctx = context(event);
                if (!ctx) return;
                if (isDisabled(ctx.input)) {
                    event.preventDefault();
                    return;
                }
                const allowedKeys = new Set([
                    "Backspace", "Delete", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
                    "Home", "End", "Tab", "Enter", "Escape",
                ]);
                if (event.metaKey || event.ctrlKey || event.altKey || allowedKeys.has(event.key)) return;
                if (!/^[0-9]$/.test(event.key)) event.preventDefault();
            }

            function handleBeforeInput(event) {
                const ctx = context(event);
                if (!ctx) return;
                if (isDisabled(ctx.input) || (event.data && /[^0-9]/.test(event.data))) event.preventDefault();
            }

            function handlePaste(event) {
                const ctx = context(event);
                if (!ctx || isDisabled(ctx.input)) return;
                event.preventDefault();
                const text = event.clipboardData ? event.clipboardData.getData("text") : "";
                parentDoc.execCommand("insertText", false, inputDigits(text));
            }

            function handleInput(event) {
                const ctx = context(event);
                if (!ctx || isDisabled(ctx.input)) return;
                const digits = sanitizeActive(ctx.input);
                ctx.input.dataset.editDirty = "true";
                setManualSaleUnit(ctx.row, digits ? Number(digits) : 0);
                updateLineTotal(ctx.row);
                updateProjectPricing();
            }

            function handleBlur(event) {
                const ctx = context(event);
                if (!ctx || isDisabled(ctx.input)) return;
                const digits = sanitizeActive(ctx.input);
                const changed = ctx.input.dataset.editDirty === "true" || digits !== (ctx.input.dataset.editStartDigits || "");
                if (changed) {
                    const value = digits ? Number(digits) : 0;
                    setManualSaleUnit(ctx.row, value);
                    persistManualSaleUnit(ctx.row, value);
                }
                setSaleInputValue(ctx.input, formatMoney(digits ? Number(digits) : 0));
                updateLineTotal(ctx.row);
                updateProjectPricing();
                if (!pointerStartedInPriceInput) {
                    parentWindow.setTimeout(() => {
                        const active = parentDoc.activeElement;
                        if (active && active.closest && active.closest(".objects-pricing-price-input")) {
                            active.blur();
                        }
                        const selection = parentWindow.getSelection ? parentWindow.getSelection() : null;
                        if (selection) selection.removeAllRanges();
                    }, 0);
                }
            }

            parentDoc.addEventListener("pointerdown", handlePointerDown, true);
            parentDoc.addEventListener("focusin", handleFocus, true);
            parentDoc.addEventListener("keydown", handleKeydown, true);
            parentDoc.addEventListener("beforeinput", handleBeforeInput, true);
            parentDoc.addEventListener("paste", handlePaste, true);
            parentDoc.addEventListener("input", handleInput, true);
            parentDoc.addEventListener("focusout", handleBlur, true);

            parentWindow[HANDLER_KEY] = () => {
                parentDoc.removeEventListener("pointerdown", handlePointerDown, true);
                parentDoc.removeEventListener("focusin", handleFocus, true);
                parentDoc.removeEventListener("keydown", handleKeydown, true);
                parentDoc.removeEventListener("beforeinput", handleBeforeInput, true);
                parentDoc.removeEventListener("paste", handlePaste, true);
                parentDoc.removeEventListener("input", handleInput, true);
                parentDoc.removeEventListener("focusout", handleBlur, true);
                parentWindow[HANDLER_KEY] = null;
            };
            seedManualPricesFromDom();
        })();
        </script>
        """
        .replace("__ESTIMATE_ID__", estimate_id_json)
        .replace("__SUPABASE_URL__", supabase_url_json)
        .replace("__SUPABASE_ANON_KEY__", supabase_anon_key_json),
        height=0,
    )


def install_object_detail_input_guard(
    *,
    run_id: str,
    estimate_id: str,
    object_id: str,
) -> None:
    """Install blur-save behavior for Object Detail HTML inputs."""
    run_id_json = json.dumps(run_id)
    estimate_id_json = json.dumps(estimate_id)
    object_id_json = json.dumps(object_id)
    components.html(
        """
        <script>
        (() => {
            const parentWindow = window.parent;
            const parentDoc = parentWindow.document;
            const RUN_ID = __RUN_ID__;
            const ESTIMATE_ID = __ESTIMATE_ID__;
            const OBJECT_ID = __OBJECT_ID__;
            const HANDLER_KEY = "__costerlyObjectDetailInputGuardCleanup";
            const SUBMITTING_KEY = "__costerlyObjectDetailSubmittingSnapshot";

            if (parentWindow[HANDLER_KEY]) parentWindow[HANDLER_KEY]();
            parentWindow[SUBMITTING_KEY] = false;

            function inputContext(event) {
                const target = event.target;
                if (!target || !target.closest) return null;
                const input = target.closest(".object-detail-cell-input");
                if (!input) return null;
                const row = input.closest(".object-detail-table-row");
                const lineId = row ? row.dataset.lineId || "" : "";
                const field = input.dataset.field || "";
                if (!lineId || !field) return null;
                return { input, lineId, field };
            }

            function cleanMoney(value) {
                return String(value || "").replace(/₪/g, "").replace(/[,\u202f]/g, "").trim();
            }

            function cleanNumber(value) {
                return cleanMoney(value).replace(/[^0-9.]/g, "");
            }

            function readNumber(value) {
                const parsed = Number(cleanNumber(value));
                return Number.isFinite(parsed) ? parsed : 0;
            }

            function formatNumber(value) {
                const rounded = Math.round((Number(value) || 0) * 100) / 100;
                if (rounded === Math.trunc(rounded)) return String(Math.trunc(rounded));
                return String(rounded).replace(/0+$/, "").replace(/\\.$/, "");
            }

            function formatMoney(value) {
                const rounded = Math.round(Number(value) || 0);
                return `₪${rounded.toLocaleString("en-US").replace(/,/g, "\u202f")}`;
            }

            function editableValue(input) {
                if (!input) return "";
                return "value" in input ? input.value : input.textContent;
            }

            function setEditableValue(input, value) {
                if (!input) return;
                if ("value" in input) {
                    input.value = value;
                } else {
                    input.textContent = value;
                }
            }

            function sectionNode(section) {
                return parentDoc.querySelector(`.object-detail-section[data-section="${CSS.escape(String(section || ""))}"]`);
            }

            function sectionRows(section) {
                return Array.from(parentDoc.querySelectorAll(
                    `.object-detail-table-row[data-section="${CSS.escape(String(section || ""))}"]`
                ));
            }

            function rowField(row, field) {
                return row ? row.querySelector(`.object-detail-cell-input[data-field="${CSS.escape(field)}"]`) : null;
            }

            function fieldNumber(row, field) {
                return readNumber(editableValue(rowField(row, field)));
            }

            function rowCost(row) {
                const cost = row ? row.querySelector(".object-detail-row-cost") : null;
                return readNumber(cost ? cost.textContent : "");
            }

            function setRowCost(row, value) {
                const cost = row ? row.querySelector(".object-detail-row-cost") : null;
                if (cost) cost.textContent = formatMoney(value);
            }

            function metricValue(section, metric) {
                const node = sectionNode(section);
                if (!node) return null;
                return node.querySelector(`.object-detail-section-metric[data-metric="${CSS.escape(metric)}"] .object-detail-section-value`);
            }

            function metricLabel(section, metric) {
                const node = sectionNode(section);
                if (!node) return "";
                const label = node.querySelector(`.object-detail-section-metric[data-metric="${CSS.escape(metric)}"] .object-detail-section-label`);
                return label ? label.textContent || "" : "";
            }

            function percentFromLabel(text, fallback) {
                const match = String(text || "").match(/([0-9]+(?:\\.[0-9]+)?)%/);
                return match ? Number(match[1]) : fallback;
            }

            function setMetric(section, metric, value, formatter) {
                const node = metricValue(section, metric);
                if (node) node.textContent = formatter(value);
            }

            function setFinal(field, value) {
                const node = parentDoc.querySelector(`.object-detail-final-value[data-final="${CSS.escape(field)}"]`);
                if (node) node.textContent = formatMoney(value);
            }

            function updateRowCost(row) {
                if (!row) return;
                const section = String(row.dataset.section || "");
                if (section === "material") {
                    setRowCost(row, fieldNumber(row, "unit_cost") * fieldNumber(row, "quantity"));
                } else if (section === "labor") {
                    setRowCost(row, fieldNumber(row, "hours") * fieldNumber(row, "rate"));
                } else if (section === "overhead") {
                    const monthly = fieldNumber(row, "monthly_cost");
                    const initialMonthly = readNumber(row.dataset.initialMonthlyCost || monthly);
                    const initialCost = readNumber(row.dataset.initialCost || rowCost(row));
                    const ratio = initialMonthly ? initialCost / initialMonthly : 0;
                    setRowCost(row, monthly * ratio);
                }
            }

            function seedRowBaselines() {
                for (const row of sectionRows("overhead")) {
                    if (!row.dataset.initialCost) row.dataset.initialCost = String(rowCost(row));
                    if (!row.dataset.initialMonthlyCost) {
                        row.dataset.initialMonthlyCost = String(fieldNumber(row, "monthly_cost"));
                    }
                }
            }

            function sumRows(section, selector) {
                return sectionRows(section).reduce((total, row) => total + selector(row), 0);
            }

            function updateSummaries() {
                const materialCost = sumRows("material", rowCost);
                const materialVatPct = percentFromLabel(metricLabel("material", "vat_18"), 18);
                setMetric("material", "cost", materialCost, formatMoney);
                setMetric("material", "vat_18", materialCost * materialVatPct / 100, formatMoney);
                setMetric("material", "total", materialCost * (1 + materialVatPct / 100), formatMoney);

                const laborHours = sumRows("labor", (row) => fieldNumber(row, "hours"));
                const laborCost = sumRows("labor", rowCost);
                const employerPct = percentFromLabel(metricLabel("labor", "employer_25"), 25);
                const employerLoad = laborCost * employerPct / 100;
                setMetric("labor", "total_hours", `${formatNumber(laborHours)} h`, (value) => value);
                setMetric("labor", "cost", laborCost, formatMoney);
                setMetric("labor", "employer_25", employerLoad, formatMoney);
                setMetric("labor", "total", laborCost + employerLoad, formatMoney);

                const overheadCost = sumRows("overhead", rowCost);
                const overheadVatPct = percentFromLabel(metricLabel("overhead", "vat"), 18);
                setMetric("overhead", "cost", overheadCost, formatMoney);
                setMetric("overhead", "vat", overheadCost * overheadVatPct / 100, formatMoney);
                setMetric("overhead", "total", overheadCost * (1 + overheadVatPct / 100), formatMoney);

                const exclVat = materialCost + laborCost + employerLoad + overheadCost;
                const finalVatPct = 18;
                setFinal("excl_vat", exclVat);
                setFinal("vat", exclVat * finalVatPct / 100);
                setFinal("total", exclVat * (1 + finalVatPct / 100));
            }

            function updateCalculations(row) {
                updateRowCost(row);
                updateSummaries();
            }

            function normalizeInputValue(input) {
                if (input.classList.contains("object-detail-cell-input--text")) {
                    return String(editableValue(input) || "").trim();
                }
                return cleanNumber(editableValue(input));
            }

            function seedInputBaselines() {
                for (const input of parentDoc.querySelectorAll(".object-detail-cell-input[data-field]")) {
                    input.dataset.originalValue = normalizeInputValue(input);
                }
            }

            function handleFocus(event) {
                const ctx = inputContext(event);
                if (!ctx) return;
                ctx.input.dataset.editStartValue = normalizeInputValue(ctx.input);
                if (!ctx.input.classList.contains("object-detail-cell-input--text")) {
                    setEditableValue(ctx.input, ctx.input.dataset.editStartValue);
                }
            }

            function handleKeydown(event) {
                const ctx = inputContext(event);
                if (!ctx || ctx.input.classList.contains("object-detail-cell-input--text")) return;
                const allowedKeys = new Set([
                    "Backspace", "Delete", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
                    "Home", "End", "Tab", "Enter", "Escape", ".",
                ]);
                if (event.metaKey || event.ctrlKey || event.altKey || allowedKeys.has(event.key)) return;
                if (!/^[0-9]$/.test(event.key)) event.preventDefault();
            }

            function handleBeforeInput(event) {
                const ctx = inputContext(event);
                if (!ctx || ctx.input.classList.contains("object-detail-cell-input--text")) return;
                if (event.data && /[^0-9.]/.test(event.data)) event.preventDefault();
            }

            function handleInput(event) {
                const ctx = inputContext(event);
                if (!ctx || ctx.input.classList.contains("object-detail-cell-input--text")) return;
                updateCalculations(ctx.input.closest(".object-detail-table-row"));
            }

            function handlePaste(event) {
                const ctx = inputContext(event);
                if (!ctx) return;
                if (ctx.input.classList.contains("object-detail-cell-input--text")) return;
                event.preventDefault();
                const text = event.clipboardData ? event.clipboardData.getData("text") : "";
                parentDoc.execCommand("insertText", false, cleanNumber(text));
            }

            function handleBlur(event) {
                const ctx = inputContext(event);
                if (!ctx) return;
                if (parentWindow[SUBMITTING_KEY]) return;
                if (ctx.input.dataset.skipNextBlurSave === "true") {
                    delete ctx.input.dataset.skipNextBlurSave;
                    return;
                }
                const nextValue = normalizeInputValue(ctx.input);
                const startValue = ctx.input.dataset.editStartValue || "";
                if (!ctx.input.classList.contains("object-detail-cell-input--text")) {
                    if (ctx.input.classList.contains("object-detail-cell-input--percent")) {
                        setEditableValue(ctx.input, `${formatNumber(readNumber(nextValue))}%`);
                    } else if (ctx.field === "quantity" || ctx.field === "hours") {
                        setEditableValue(ctx.input, formatNumber(readNumber(nextValue)));
                    } else {
                        setEditableValue(ctx.input, formatMoney(nextValue));
                    }
                }
                updateCalculations(ctx.input.closest(".object-detail-table-row"));
                if (nextValue === startValue) return;

                const params = new URLSearchParams();
                params.set("screen", "object_detail");
                if (RUN_ID) params.set("run_id", RUN_ID);
                params.set("estimate_id", ESTIMATE_ID);
                params.set("object_id", OBJECT_ID);
                params.set("od_edit_line", ctx.lineId);
                params.set("od_edit_field", ctx.field);
                params.set("od_edit_value", nextValue);
                params.set("od_edit_nonce", String(Date.now()));
                parentWindow.location.search = `?${params.toString()}`;
            }

            function findApproveButton(target) {
                const button = target && target.closest ? target.closest("[data-object-detail-approve]") : null;
                if (!button) return null;
                return button;
            }

            function snapshotEdits() {
                return Array.from(parentDoc.querySelectorAll(".object-detail-table-row")).flatMap((row) => {
                    const lineId = row.dataset.lineId || "";
                    if (!lineId) return [];
                    return Array.from(row.querySelectorAll(".object-detail-cell-input[data-field]")).map((input) => ({
                        line_id: lineId,
                        field: input.dataset.field || "",
                        value: normalizeInputValue(input),
                        originalValue: input.dataset.originalValue ?? normalizeInputValue(input),
                    })).filter((edit) => edit.field && edit.value !== edit.originalValue);
                });
            }

            function approveSnapshotHref() {
                const edits = snapshotEdits();

                const params = new URLSearchParams();
                params.set("screen", "object_detail");
                if (RUN_ID) params.set("run_id", RUN_ID);
                params.set("estimate_id", ESTIMATE_ID);
                params.set("object_id", OBJECT_ID);
                params.set("od_snapshot", JSON.stringify(edits));
                params.set("od_approve_after", "1");
                params.set("od_edit_nonce", String(Date.now()));
                return { href: `?${params.toString()}`, edits };
            }

            function prepareApproveSnapshot(event) {
                const button = findApproveButton(event.target);
                if (!button) return;
                const snapshot = approveSnapshotHref();
                button.setAttribute("href", snapshot.href);
                parentWindow[SUBMITTING_KEY] = true;
            }

            parentDoc.addEventListener("focusin", handleFocus, true);
            parentDoc.addEventListener("keydown", handleKeydown, true);
            parentDoc.addEventListener("beforeinput", handleBeforeInput, true);
            parentDoc.addEventListener("paste", handlePaste, true);
            parentDoc.addEventListener("input", handleInput, true);
            parentDoc.addEventListener("pointerdown", prepareApproveSnapshot, true);
            parentDoc.addEventListener("mousedown", prepareApproveSnapshot, true);
            parentDoc.addEventListener("click", prepareApproveSnapshot, true);
            parentDoc.addEventListener("focusout", handleBlur, true);

            parentWindow[HANDLER_KEY] = () => {
                parentDoc.removeEventListener("focusin", handleFocus, true);
                parentDoc.removeEventListener("keydown", handleKeydown, true);
                parentDoc.removeEventListener("beforeinput", handleBeforeInput, true);
                parentDoc.removeEventListener("paste", handlePaste, true);
                parentDoc.removeEventListener("input", handleInput, true);
                parentDoc.removeEventListener("pointerdown", prepareApproveSnapshot, true);
                parentDoc.removeEventListener("mousedown", prepareApproveSnapshot, true);
                parentDoc.removeEventListener("click", prepareApproveSnapshot, true);
                parentDoc.removeEventListener("focusout", handleBlur, true);
                parentWindow[HANDLER_KEY] = null;
            };
            seedInputBaselines();
            seedRowBaselines();
        })();
        </script>
        """
        .replace("__RUN_ID__", run_id_json)
        .replace("__ESTIMATE_ID__", estimate_id_json)
        .replace("__OBJECT_ID__", object_id_json),
        height=0,
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
            const MANUAL_PRICES_KEY = "__costerlyObjectsManualSalePrices";
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

            function formatInputMoney(value) {
                const rounded = Math.round(readNumber(value, 0));
                return `₪${rounded.toLocaleString("en-US").replace(/,/g, "\u202f")}`;
            }

            function inputDigits(value) {
                return String(value || "").replace(/[^0-9]/g, "");
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
                    if (
                        cell.querySelector(".objects-pricing-review-button--done")
                        || String(cell.textContent || "").trim().toLowerCase() === "done"
                    ) {
                        return;
                    }
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

            function saleInput(row) {
                return row.querySelector(".objects-pricing-price-input");
            }

            function hideProjectCostSuggestion(row) {
                if (!isProjectCostRow(row)) return;
                const suggestion = row.querySelector(".objects-pricing-suggestion");
                if (suggestion) suggestion.textContent = "";
            }

            function manualPrices() {
                if (!parentWindow[MANUAL_PRICES_KEY]) parentWindow[MANUAL_PRICES_KEY] = {};
                if (!parentWindow[MANUAL_PRICES_KEY][ESTIMATE_ID]) parentWindow[MANUAL_PRICES_KEY][ESTIMATE_ID] = {};
                return parentWindow[MANUAL_PRICES_KEY][ESTIMATE_ID];
            }

            function manualSaleUnit(row) {
                const objectKey = row ? row.dataset.objectKey || "" : "";
                const value = manualPrices()[objectKey];
                return Number.isFinite(value) ? value : null;
            }

            function setManualSaleUnit(row, value) {
                const objectKey = row ? row.dataset.objectKey || "" : "";
                if (!objectKey) return;
                manualPrices()[objectKey] = Math.max(0, Math.round(readNumber(value, 0)));
                hideProjectCostSuggestion(row);
            }

            function saleInputValue(input) {
                if (!input) return "";
                return "value" in input ? input.value : input.textContent;
            }

            function setSaleInputValue(input, value) {
                if (!input) return;
                if ("value" in input) {
                    input.value = value;
                    return;
                }
                input.textContent = value;
            }

            function setSaleInputDisabled(input, disabled) {
                if (!input) return;
                if ("disabled" in input) input.disabled = disabled;
                input.setAttribute("aria-disabled", disabled ? "true" : "false");
                if (disabled) {
                    input.removeAttribute("contenteditable");
                    input.removeAttribute("tabindex");
                } else if (!("value" in input)) {
                    input.setAttribute("contenteditable", "true");
                    input.setAttribute("tabindex", "0");
                }
            }

            function inputWasEdited(input) {
                return Boolean(input && input.dataset.userEdited === "true");
            }

            function setSalePricing(row, saleUnit, saleTotal) {
                const input = saleInput(row);
                const totalCell = row.querySelector(".objects-pricing-sale-total-cell");
                const manualUnit = manualSaleUnit(row);
                const effectiveUnit = manualUnit == null ? saleUnit : manualUnit;
                if (manualUnit != null) hideProjectCostSuggestion(row);
                if (input && parentDoc.activeElement !== input && effectiveUnit != null) {
                    const formatted = formatInputMoney(effectiveUnit);
                    setSaleInputValue(input, formatted);
                    setSaleInputDisabled(input, false);
                    input.dataset.autoValue = formatted;
                }
                if (totalCell) {
                    const effectiveTotal = manualUnit == null ? saleTotal : Math.round(manualUnit * rowQuantity(row, 1) * 100) / 100;
                    totalCell.textContent = effectiveTotal == null ? "" : formatMoney(effectiveTotal);
                }
            }

            function rowSaleUnit(row) {
                const input = saleInput(row);
                return readMoneyNumber(saleInputValue(input));
            }

            function updateLineTotalFromInput(row) {
                if (isProjectCostRow(row)) return;

                const totalCell = row.querySelector(".objects-pricing-sale-total-cell");
                if (!totalCell) return;

                const saleTotal = Math.round(rowSaleUnit(row) * rowQuantity(row, 1) * 100) / 100;
                totalCell.textContent = formatMoney(saleTotal);
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

                const deliveryDefault = Math.round(subtotal * 0.03 * 100) / 100;
                const installationDefault = Math.round(subtotal * 0.10 * 100) / 100;

                const deliveryRow = rowForObject("delivery");
                if (deliveryRow) setSalePricing(deliveryRow, deliveryDefault, null);

                const installationRow = rowForObject("installation");
                if (installationRow) setSalePricing(installationRow, installationDefault, null);

                const delivery = deliveryRow ? rowSaleUnit(deliveryRow) : deliveryDefault;
                const installation = installationRow ? rowSaleUnit(installationRow) : installationDefault;
                const projectPrice = Math.round((subtotal + delivery + installation) * 100) / 100;
                const vat = Math.round(projectPrice * 0.18 * 100) / 100;
                const total = Math.round((projectPrice + vat) * 100) / 100;

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
                const manualUnit = manualSaleUnit(row);
                const saleUnit = manualUnit == null ? Math.round(selfCost * 1.3 * 100) / 100 : manualUnit;
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
                    // Keep progress polling silent; the next interval will retry.
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

                const observerRoot = document.body || document.documentElement;
                if (observerRoot) {
                    observer.observe(observerRoot, { childList: true, subtree: true });
                }
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


def install_upload_interaction_guards(shell_html: str) -> None:
    """Install upload dragover and instant processing shell from one component."""
    shell_html_json = json.dumps(shell_html)

    components.html(
        """
        <script>
        (() => {
            const parentDoc = window.parent.document;
            const markerId = "COSTERLY_UPLOAD_INTERACTION_GUARDS_V1_1_4";
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
                const DRAG_CLASS = 'costerly-upload-dragover';
                const SHELL_ID = 'costerly-upload-processing-shell';
                const STYLE_ID = 'costerly-upload-processing-shell-style';
                const REAL_PROCESSING_MARKER_ID = 'costerly-processing-screen-active';
                const SHELL_ACTIVE_CLASS = 'costerly-upload-processing-shell-active';
                const SHELL_BOUND_ATTR = 'data-costerly-processing-shell-bound';
                const GUARD_BOUND_ATTR = 'data-costerly-upload-interaction-bound';
                const INSTALLED_FLAG = '__costerlyUploadInteractionGuardsV114Installed';
                const ELAPSED_STARTED_AT_KEY = '__costerlyProcessingElapsedStartedAt';
                const ELAPSED_TIMER_KEY = '__costerlyProcessingElapsedTimer';
                let clearDragTimer = null;
                let watcher = null;
                let slowTimer = null;

                if (window[INSTALLED_FLAG]) {
                    return;
                }

                window[INSTALLED_FLAG] = true;

                function getDropzones() {
                    return Array.from(document.querySelectorAll(DROPZONE_SELECTOR));
                }

                function dragHasFiles(event) {
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
                    window.clearTimeout(clearDragTimer);
                    setDragover(null, false);
                }

                function forceDragover(event) {
                    if (!dragHasFiles(event)) return;

                    const dropzone = event.target.closest(DROPZONE_SELECTOR);

                    if (!dropzone) {
                        clearDragover();
                        return;
                    }

                    event.preventDefault();
                    window.clearTimeout(clearDragTimer);
                    setDragover(dropzone, true);
                }

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

                function elapsedLabel(seconds) {
                    const minutes = Math.floor(seconds / 60);
                    const remainder = seconds % 60;
                    return 'Elapsed ' +
                        String(minutes).padStart(2, '0') + ':' +
                        String(remainder).padStart(2, '0');
                }

                function updateElapsed() {
                    const startedAt = Number(window[ELAPSED_STARTED_AT_KEY] || 0);
                    if (!startedAt) return;

                    const seconds = Math.max(
                        0,
                        Math.floor((Date.now() - startedAt) / 1000)
                    );
                    document.querySelectorAll('.post-upload-stage__timer').forEach((node) => {
                        node.textContent = elapsedLabel(seconds);
                    });

                    if (!realProcessingIsActive() && !document.getElementById(SHELL_ID)) {
                        window.clearInterval(window[ELAPSED_TIMER_KEY]);
                        window[ELAPSED_TIMER_KEY] = null;
                        window[ELAPSED_STARTED_AT_KEY] = null;
                    }
                }

                function startElapsed() {
                    if (!window[ELAPSED_STARTED_AT_KEY]) {
                        window[ELAPSED_STARTED_AT_KEY] = Date.now();
                    }
                    updateElapsed();
                    if (!window[ELAPSED_TIMER_KEY]) {
                        window[ELAPSED_TIMER_KEY] = window.setInterval(updateElapsed, 200);
                    }
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
                    startElapsed();

                    if (slowTimer) window.clearTimeout(slowTimer);
                    slowTimer = window.setTimeout(() => {
                        const activeShell = document.getElementById(SHELL_ID);
                        if (activeShell && !realProcessingIsActive()) {
                            activeShell.dataset.slow = 'true';
                        }
                    }, 25000);

                    startWatcher();
                }

                function dropHasFiles(event) {
                    return Boolean(
                        event.dataTransfer &&
                        event.dataTransfer.files &&
                        event.dataTransfer.files.length > 0
                    );
                }

                function bindInputs() {
                    document.querySelectorAll(FILE_INPUT_SELECTOR).forEach((input) => {
                        if (input.getAttribute(SHELL_BOUND_ATTR) === 'true') return;
                        input.setAttribute(SHELL_BOUND_ATTR, 'true');

                        input.addEventListener('change', () => {
                            if (input.files && input.files.length > 0) {
                                showShell('input-change');
                            }
                        }, true);
                    });
                }

                function bindGlobalListeners() {
                    if (document.documentElement.getAttribute(GUARD_BOUND_ATTR) === 'true') return;
                    document.documentElement.setAttribute(GUARD_BOUND_ATTR, 'true');

                    document.addEventListener('dragenter', forceDragover, true);
                    document.addEventListener('dragover', forceDragover, true);
                    document.addEventListener('dragleave', () => {
                        window.clearTimeout(clearDragTimer);
                        clearDragTimer = window.setTimeout(clearDragover, 140);
                    }, true);
                    document.addEventListener('drop', (event) => {
                        const dropzone = event.target.closest(DROPZONE_SELECTOR);
                        clearDragover();
                        if (dropzone && dropHasFiles(event)) {
                            window.setTimeout(() => showShell('drop'), 0);
                        }
                    }, true);
                    document.addEventListener('dragend', clearDragover, true);
                    window.addEventListener('blur', clearDragover, true);

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
                }

                const observer = new MutationObserver(() => {
                    bindInputs();
                    if (realProcessingIsActive()) removeShell();
                });

                const observerRoot = document.body || document.documentElement;
                if (observerRoot) {
                    observer.observe(observerRoot, { childList: true, subtree: true });
                }

                bindGlobalListeners();
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
