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
