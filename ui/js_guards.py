from __future__ import annotations

import streamlit.components.v1 as components


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
