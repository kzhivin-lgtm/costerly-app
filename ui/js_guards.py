from __future__ import annotations

import json

import streamlit.components.v1 as components


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
