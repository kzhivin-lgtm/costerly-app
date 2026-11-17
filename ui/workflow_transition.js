// Executed by the ready component. The controller and its cover live in
// the Streamlit document, outside the React tree that reruns replace.
function workflowTransitionController(coreWindow, traceId) {
    if (!traceId || coreWindow === coreWindow.top) return null;
    const doc = coreWindow.document;
    const key = "__costerlyWorkflowTransition";
    const existing = coreWindow[key];
    if (existing?.traceId === traceId) return existing;
    existing?.dispose();

    let hostOrigin;
    try {
        hostOrigin = new URL(doc.referrer).origin;
    } catch (_) {
        return null;
    }

    const selectors = {
        upload: [".upload-screen__hero", '[data-testid="stFileUploaderDropzone"]'],
        file_review: [".file-review-detected-title", ".file-review-summary-card-marker"],
        objects: [".objects-estimation-header", ".objects-pricing-table"],
        object_detail: [".object-detail-title", ".object-detail-final", ".object-detail-footer-actions"],
    };
    const routes = {
        new_estimate: "upload",
        last_estimate: "file_review",
        file_review_to_objects: "objects",
        objects_to_object_detail: "object_detail",
        object_detail_to_objects: "objects",
        objects_to_file_review: "file_review",
    };
    const names = {
        upload: "New Estimate",
        file_review: "File Review",
        objects: "Objects Estimation",
        object_detail: "Object Detail",
    };
    let enabled = false;
    let pending = null;
    let displayed = null;

    function post(data) {
        coreWindow.top.postMessage({...data, traceId}, hostOrigin);
    }

    function acceptHost(event) {
        if (event.source === coreWindow.top && event.origin === hostOrigin &&
            event.data?.type === "costerly:workflow-navigation-enabled" &&
            event.data.traceId === traceId && event.data.protocol === 1) {
            enabled = true;
        }
    }
    coreWindow.addEventListener("message", acceptHost);

    function find(selector) {
        return Array.from(doc.querySelectorAll(selector)).find(node =>
            !node.closest('[data-stale="true"]')
        );
    }

    function readyTarget(message) {
        // Wait for this run's marker and for the old screen's deltas to be
        // removed. The old nodes can coexist with the new header and table.
        const markers = Array.from(doc.querySelectorAll("[data-costerly-render-id]"));
        if (markers.length !== 1 || markers[0].dataset.costerlyRenderId !== message.runId ||
            markers[0].closest('[data-stale="true"]')) return false;
        if (doc.querySelector('[data-stale="true"]')) return false;
        if (message.screen === "login") return Boolean(find(".auth-brand") && find('[data-testid="stForm"]'));
        if (message.screen.endsWith("_error")) return Boolean(find('[data-testid="stAlert"]'));
        if (find('[data-testid="stAlertContentError"]')) return true;
        const roots = selectors[message.screen];
        if (!roots?.every(find) || !find(".st-key-costerly_header_controls button")) return false;
        if (message.screen !== "file_review") return true;
        const button = Array.from(doc.querySelectorAll("button")).find(node =>
            node.textContent.trim().toLowerCase() === "continue to objects estimation" &&
            !node.closest('[data-stale="true"]')
        );
        return Boolean(button && (!button.disabled || find("[data-costerly-file-review-blocked]")));
    }

    function stopWatching(transition) {
        transition.observer?.disconnect();
        coreWindow.cancelAnimationFrame(transition.frame);
        coreWindow.clearTimeout(transition.timeout);
    }

    function close(transition) {
        stopWatching(transition);
        if (transition.app) transition.app.inert = transition.wasInert;
        transition.cover.remove();
        pending = null;
    }

    function showFailure(transition, reason = "destination_not_ready") {
        if (pending !== transition || transition.failed) return;
        transition.failed = true;
        stopWatching(transition);
        transition.status.textContent = reason === "destination_not_ready"
            ? "This page is taking longer to open." : "Could not open this page.";
        const reload = doc.createElement("button");
        reload.type = "button";
        reload.textContent = "Reload page";
        reload.style.cssText = "margin:0.35rem auto 0;padding:0.5rem 1rem;cursor:pointer;";
        reload.addEventListener("click", () => post({type: "costerly:workflow-navigation-reload",
                                                    transitionId: transition.id}));
        transition.cover.append(reload);
        reload.focus({preventScroll: true});
        post({type: "costerly:transition-failed", transitionId: transition.id,
              transition: transition.name, reason});
    }

    function begin(name, id) {
        const target = routes[name];
        if (!enabled || pending || !target || !selectors[displayed?.screen]) return false;
        const cover = doc.createElement("div");
        cover.id = "costerly-workflow-transition";
        cover.tabIndex = -1;
        cover.style.cssText = "position:fixed;inset:0;z-index:2147483000;background:#f1efef;"
            + "display:flex;flex-direction:column;justify-content:center;align-items:center;"
            + "color:#392c47;font:500 1rem system-ui,sans-serif;";
        const status = doc.createElement("span");
        status.className = "costerly-workflow-status";
        status.setAttribute("role", "status");
        status.textContent = "Opening " + names[target] + "…";
        cover.append(status);
        doc.body.append(cover);

        const app = doc.querySelector(".stApp");
        const transition = {id, name, target, cover, status, app,
                            wasInert: Boolean(app?.inert), from: displayed};
        pending = transition;
        // Let this click reach Streamlit, then block any further activation
        // in the outgoing screen while its replacement is being rendered.
        coreWindow.queueMicrotask(() => {
            if (pending !== transition) return;
            if (app) app.inert = true;
            cover.focus({preventScroll: true});
        });
        transition.timeout = coreWindow.setTimeout(() => showFailure(transition), 15000);
        return true;
    }

    function ready(message) {
        const transition = pending;
        if (!transition) {
            if (message.runId === displayed?.settledRun) return true;
            const marker = find("[data-costerly-render-id]");
            if (marker?.dataset.costerlyRenderId !== message.runId) return Boolean(displayed);
            displayed = message;
            return false;
        }
        if (transition.failed || message.runId === transition.from.runId) return true;
        if (message.screen !== transition.target && message.screen !== "login" &&
            !message.screen.endsWith("_error")) return true;
        if (transition.candidate === message.runId) return true;
        transition.candidate = message.runId;
        transition.observer?.disconnect();
        coreWindow.cancelAnimationFrame(transition.frame);

        let stable = false;
        const check = () => {
            transition.frame = null;
            if (pending !== transition) return;
            if (!readyTarget(message)) {
                stable = false;
                return;
            }
            if (!stable) {
                stable = true;
                schedule();
                return;
            }
            coreWindow.scrollTo(0, 0);
            doc.querySelectorAll(".stMain, [data-testid='stAppViewContainer']").forEach(node => {
                node.scrollTop = 0;
            });
            displayed = {...message, settledRun: message.runId};
            post({...message, transitionId: transition.id});
            close(transition);
        };
        const schedule = () => {
            if (!transition.frame) transition.frame = coreWindow.requestAnimationFrame(check);
        };
        transition.observer = new coreWindow.MutationObserver(schedule);
        transition.observer.observe(doc.body, {childList: true, subtree: true,
                                               attributes: true, attributeFilter: ["data-stale", "disabled"]});
        schedule();
        return true;
    }

    const controller = {
        traceId, begin, ready,
        enabled: () => enabled,
        busy: () => Boolean(pending),
        fail: () => { if (pending) showFailure(pending, "navigation_control_unavailable"); },
        dispose: () => {
            coreWindow.removeEventListener("message", acceptHost);
            if (pending) close(pending);
        },
    };
    coreWindow[key] = controller;
    return controller;
}
