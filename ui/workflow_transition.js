// Executed by the ready component. The controller and its cover live in
// the Streamlit document, outside the React tree that reruns replace.
function workflowTransitionController(coreWindow, traceId, revision, receipt) {
    if (!traceId || coreWindow === coreWindow.top) return null;
    const doc = coreWindow.document;
    const key = "__costerlyWorkflowTransition";
    const existing = coreWindow[key];
    if (existing?.traceId === traceId && existing.revision === revision) return existing;
    const upgradeKey = key + "Upgrade";
    if (existing?.busy()) {
        // Finish the visible transition before upgrading a controller that
        // survived a deployment in this same browser document.
        const waiting = coreWindow[upgradeKey];
        if (waiting?.revision === revision) {
            waiting.receipt = receipt;
            return existing;
        }
        waiting?.observer.disconnect();
        const upgrade = {revision, receipt};
        upgrade.observer = new coreWindow.MutationObserver(() => {
            if (existing.busy()) return;
            upgrade.observer.disconnect();
            delete coreWindow[upgradeKey];
            const next = workflowTransitionController(coreWindow, traceId, revision, upgrade.receipt);
            next?.ready(upgrade.receipt);
        });
        upgrade.observer.observe(doc.body, {childList: true});
        coreWindow[upgradeKey] = upgrade;
        return existing;
    }
    coreWindow[upgradeKey]?.observer.disconnect();
    delete coreWindow[upgradeKey];
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
        projects: [".projects-title", ".projects-table-card, .projects-empty"],
        account: [".company-profile-heading", '[data-testid="stTabs"]'],
        admin: [".platform-admin-heading", ".st-key-platform_admin_sections", ".platform-admin-table-card"],
    };
    const routes = {
        version_refresh: "upload",
        new_estimate: "upload",
        last_estimate: "file_review",
        file_review_to_objects: "objects",
        objects_to_object_detail: "object_detail",
        object_detail_to_objects: "objects",
        objects_to_file_review: "file_review",
        object_detail_approve_to_objects: "objects",
        back_to_upload: "upload",
        open_profile: "account",
        open_admin: "admin",
        upload_to_profile: "account",
        profile_to_upload: "upload",
        upload_to_admin: "admin",
        profile_to_admin: "admin",
        admin_to_profile: "account",
        admin_to_upload: "upload",
        upload_to_projects: "projects",
        profile_to_projects: "projects",
        admin_to_projects: "projects",
        projects_to_upload: "upload",
        projects_to_profile: "account",
        projects_to_admin: "admin",
        objects_to_projects: "projects",
        sign_out: "login",
        profile_to_sign_out: "login",
        upload_to_sign_out: "login",
        projects_to_sign_out: "login",
        profile_tab_change: "account",
    };
    const names = {
        upload: "New Estimate",
        file_review: "File Review",
        objects: "Objects Estimation",
        object_detail: "Object Detail",
        projects: "Projects",
        account: "Profile",
        admin: "Admin",
        login: "Login",
    };
    let enabled = false;
    let pending = null;
    let displayed = null;
    let hostBuild = null;
    let versionTimer = null;
    let pickerOpen = false;
    let uploadStarted = false;
    const refreshKey = "costerly.version-refresh.v1";

    function uploadIsEmpty() {
        return displayed?.screen === "upload" && displayed.versionRefreshSafe === true &&
            !pending && !pickerOpen && !uploadStarted &&
            !doc.querySelector('[data-stale="true"], #costerly-upload-processing-shell') &&
            !Array.from(doc.querySelectorAll('[data-testid="stFileUploader"] input[type="file"]'))
                .some(input => input.files?.length);
    }

    function buildsMatch() {
        return Boolean(hostBuild && hostBuild === displayed?.metrics?.server_build_version);
    }

    function announceRefresh(id) {
        post({type: "costerly:transition-click", transition: "version_refresh",
              transitionId: id, sourceScreen: "upload", targetScreen: "upload",
              workflowNavigation: true});
    }

    function checkVersion() {
        doc.getElementById("costerly-version-check-status")?.remove();
        coreWindow.clearTimeout(versionTimer);
        versionTimer = null;
        if (buildsMatch()) {
            try { coreWindow.sessionStorage.removeItem(refreshKey); } catch (_) {}
            return;
        }
        if (!uploadIsEmpty()) return;
        if (hostBuild === null) {
            // One deadline per ready receipt, cancelled on reply, departure or
            // disposal. No polling or extra Streamlit rerun.
            versionTimer = coreWindow.setTimeout(() => {
                versionTimer = null;
                if (!uploadIsEmpty()) return;
                const id = coreWindow.crypto.randomUUID();
                if (!begin("version_refresh", id)) return;
                announceRefresh(id);
                showFailure(pending, "version_unconfirmed");
            }, 5000);
            return;
        }
        const id = coreWindow.crypto.randomUUID();
        if (!begin("version_refresh", id)) return;
        pending.status.textContent = "Updating app…";
        announceRefresh(id);
        // The tab-scoped guard survives the full outer reload. Fail closed
        // when storage is unavailable, rather than risk a reload loop.
        try {
            if (coreWindow.sessionStorage.getItem(refreshKey)) {
                showFailure(pending, "version_unconfirmed");
                return;
            }
            coreWindow.sessionStorage.setItem(refreshKey, displayed.metrics.server_build_version);
        } catch (_) {
            showFailure(pending, "version_unconfirmed");
            return;
        }
        post({type: "costerly:workflow-navigation-reload", transitionId: id});
    }

    function guardUpload(event) {
        if (displayed?.screen !== "upload" || !event.target.closest?.('[data-testid="stFileUploader"]')) return;
        // Keep the native file-list remove/cancel controls usable. Only the
        // picker/drop zone can start a new upload.
        if (event.type === "click" && !event.target.closest('input[type="file"], [data-testid="stFileUploaderDropzone"]')) return;
        if (event.type === "cancel") {
            pickerOpen = false;
            checkVersion();
            return;
        }
        if (event.type === "change" && pickerOpen) {
            pickerOpen = false;
            uploadStarted = Boolean(event.target.files?.length);
            if (!uploadStarted) checkVersion();
            return;
        }
        if (buildsMatch()) {
            if (event.type === "click" && event.target.matches('input[type="file"]')) pickerOpen = true;
            if (event.type === "drop" && event.dataTransfer?.files?.length) uploadStarted = true;
            return;
        }
        if (uploadStarted && event.type === "change") return;
        event.preventDefault();
        event.stopImmediatePropagation();
        if (!pending && !doc.getElementById("costerly-version-check-status")) {
            const status = doc.createElement("div");
            status.id = "costerly-version-check-status";
            status.setAttribute("role", "status");
            status.textContent = uploadStarted
                ? "The current upload is continuing. The app update will wait."
                : "Checking app version…";
            event.target.closest('[data-testid="stFileUploader"]').append(status);
        }
    }
    // Capture prevents both the file picker and native drop from starting
    // work until this tab has an acknowledged matching build.
    for (const type of ["click", "drop", "change", "cancel"]) doc.addEventListener(type, guardUpload, true);

    function post(data) {
        coreWindow.top.postMessage({...data, traceId}, hostOrigin);
    }

    function acceptHost(event) {
        if (event.source === coreWindow.top && event.origin === hostOrigin &&
            event.data?.type === "costerly:workflow-navigation-enabled" &&
            event.data.traceId === traceId && event.data.protocol === 1) {
            enabled = true;
            // Empty means a supported older wrapper. Migrate it once using
            // its existing correlated reload command, only on empty Upload.
            hostBuild = String(event.data.buildVersion || "");
            checkVersion();
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
        transition.scopeObserver?.disconnect();
        coreWindow.cancelAnimationFrame(transition.frame);
        coreWindow.clearTimeout(transition.timeout);
    }

    function close(transition) {
        stopWatching(transition);
        if (transition.app) transition.app.inert = transition.wasInert;
        transition.cover.remove();
        pending = null;
        if (transition.local) {
            find('.st-key-company_profile_tab [role="tab"][aria-selected="true"]')?.focus({preventScroll: true});
        }
    }

    function showFailure(transition, reason = "destination_not_ready") {
        if (pending !== transition || transition.failed) return;
        transition.failed = true;
        stopWatching(transition);
        transition.status.textContent = reason === "destination_not_ready"
            ? "This page is taking longer to open." : reason === "version_unconfirmed"
            ? "The app update is not ready yet. Reload to retry." : "Could not open this page.";
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
        if ((!enabled && name !== "version_refresh") || pending || !target || !selectors[displayed?.screen]) return false;
        const cover = doc.createElement("div");
        cover.id = "costerly-workflow-transition";
        cover.tabIndex = -1;
        cover.style.cssText = "position:fixed;inset:0;z-index:2147483000;background:#f1efef;"
            + "display:flex;flex-direction:column;justify-content:center;align-items:center;"
            + "color:#392c47;font:500 1rem system-ui,sans-serif;";
        const tabs = find(".st-key-company_profile_tab");
        const local = name === "profile_tab_change" && Boolean(find("[data-costerly-profile-fragment]"));
        if (local && tabs) {
            const bounds = tabs.getBoundingClientRect();
            const tablist = tabs.querySelector('[role="tablist"]').getBoundingClientRect();
            cover.style.top = Math.max(0, tablist.bottom) + "px";
            cover.style.left = bounds.left + "px";
            cover.style.right = "auto";
            cover.style.width = bounds.width + "px";
            cover.dataset.profileTab = "true";
        }
        const status = doc.createElement("span");
        status.className = "costerly-workflow-status";
        status.setAttribute("role", "status");
        status.textContent = local ? "Loading…" : "Opening " + names[target] + "…";
        cover.append(status);
        doc.body.append(cover);

        const app = doc.querySelector(".stApp");
        const transition = {id, name, target, cover, status, app, local,
                            wasInert: Boolean(app?.inert), from: displayed};
        pending = transition;
        if (local) {
            const heading = find(".company-profile-heading");
            transition.scopeObserver = new coreWindow.MutationObserver(() => {
                if (heading?.isConnected && !heading.closest('[data-stale="true"]')) return;
                transition.local = false;
                cover.style.inset = "0";
                cover.style.width = "auto";
                transition.scopeObserver.disconnect();
            });
            transition.scopeObserver.observe(doc.body, {childList: true, subtree: true,
                attributes: true, attributeFilter: ["data-stale"]});
        }
        // Let this click reach Streamlit, then block any further activation
        // in the outgoing screen while its replacement is being rendered.
        coreWindow.queueMicrotask(() => {
            if (pending !== transition) return;
            if (app) app.inert = true;
            if (!local) cover.focus({preventScroll: true});
        });
        transition.timeout = coreWindow.setTimeout(() => showFailure(transition), 15000);
        return true;
    }

    function ready(message) {
        if (pending?.name === "version_refresh") {
            if (message.screen === "upload") return true;
            // A server-authenticated departure (including expired auth) wins
            // over the update cover. Never strand Login or an accepted job.
            const refresh = pending;
            displayed = message;
            pickerOpen = false;
            uploadStarted = false;
            post({...message, transitionId: refresh.id});
            close(refresh);
            checkVersion();
            return true;
        }
        const transition = pending;
        if (!transition) {
            if (message.runId === displayed?.settledRun) return true;
            const marker = find("[data-costerly-render-id]");
            if (marker?.dataset.costerlyRenderId !== message.runId) return Boolean(displayed);
            displayed = message;
            if (message.screen !== "upload") { pickerOpen = false; uploadStarted = false; }
            else if (!doc.querySelector('[data-testid="stFileUploaderFile"]') &&
                     !Array.from(doc.querySelectorAll('input[type="file"]')).some(input => input.files?.length)) {
                // A fresh empty Upload receipt also covers native rejection
                // and New Estimate without an intervening Processing screen.
                uploadStarted = false;
            }
            checkVersion();
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
            if (!transition.local) {
                coreWindow.scrollTo(0, 0);
                doc.querySelectorAll(".stMain, [data-testid='stAppViewContainer']").forEach(node => {
                    node.scrollTop = 0;
                });
            }
            displayed = {...message, settledRun: message.runId};
            if (message.screen !== "upload") { pickerOpen = false; uploadStarted = false; }
            post({...message, transitionId: transition.id});
            close(transition);
            checkVersion();
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
        traceId, revision, begin, ready,
        enabled: () => enabled,
        busy: () => Boolean(pending),
        versionMatched: buildsMatch,
        fail: () => { if (pending) showFailure(pending, "navigation_control_unavailable"); },
        dispose: () => {
            coreWindow.removeEventListener("message", acceptHost);
            coreWindow.clearTimeout(versionTimer);
            doc.getElementById("costerly-version-check-status")?.remove();
            for (const type of ["click", "drop", "change", "cancel"]) doc.removeEventListener(type, guardUpload, true);
            if (pending) close(pending);
        },
    };
    coreWindow[key] = controller;
    return controller;
}
