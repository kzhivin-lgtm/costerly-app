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
        const ancestors = coreWindow.location.ancestorOrigins;
        // A link inside Core makes document.referrer point to Core itself.
        // The browser's actual top ancestor remains the wrapper.
        hostOrigin = ancestors?.length
            ? ancestors[ancestors.length - 1]
            : new URL(doc.referrer).origin;
        if (hostOrigin === coreWindow.location.origin) {
            const previous = JSON.parse(coreWindow.sessionStorage.getItem("costerly.workflow.host-context.v1") || "null");
            if (previous?.traceId === traceId && previous.hostOrigin) hostOrigin = new URL(previous.hostOrigin).origin;
        }
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
        objects: "Project",
        object_detail: "Object Detail",
        projects: "All Projects",
        account: "Profile",
        admin: "Admin",
        login: "Login",
    };
    let enabled = false;
    let pending = null;
    let displayed = null;
    let hostBuild = null;
    let hostManagesDeployRefresh = false;
    let pickerOpen = false;
    let uploadStarted = false;
    let recovery = null;
    const refreshKey = "costerly.version-refresh.v1";
    const announcedBuilds = new Set();

    function buildsMatch() {
        return Boolean(hostBuild && hostBuild === displayed?.metrics?.server_build_version);
    }

    function postUploadState() {
        post({type: "costerly:deploy-refresh-state", busy: pickerOpen || uploadStarted});
    }

    function checkVersion() {
        postUploadState();
        // Modern wrappers receive one build event over the existing Core
        // connection. This branch only migrates already-open older wrappers.
        if (hostManagesDeployRefresh || buildsMatch()) {
            try { coreWindow.sessionStorage.removeItem(refreshKey); } catch (_) {}
            return;
        }
        if (displayed?.authStorageReady === false || hostBuild === null || pending || pickerOpen || uploadStarted ||
            !["upload", "login"].includes(displayed?.screen) ||
            displayed.versionRefreshSafe !== true ||
            doc.querySelector('#costerly-upload-processing-shell') ||
            Array.from(doc.querySelectorAll('input[type="file"]')).some(input => input.files?.length)) return;
        const id = coreWindow.crypto.randomUUID();
        if (!begin("version_refresh", id)) return;
        pending.status.textContent = "Updating app…";
        post({type: "costerly:transition-click", transition: "version_refresh", transitionId: id,
              sourceScreen: displayed.screen, targetScreen: displayed.screen, workflowNavigation: true});
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

    function announceBuild(message) {
        const build = String(message.metrics?.server_build_version || "");
        if (!build || message.authStorageReady === false || announcedBuilds.has(build)) return;
        announcedBuilds.add(build);
        post({type:"costerly:build-available", buildVersion:build});
    }

    function resumeAuthWrite(message) {
        if (message.runId !== displayed?.runId) return;
        displayed.authStorageReady = true;
        checkVersion();
        announceBuild(message);
    }

    function trackUpload(event) {
        if (displayed?.screen !== "upload" || !event.target.closest?.('[data-testid="stFileUploader"]')) return;
        if (event.type === "click" && event.target.matches('input[type="file"]')) pickerOpen = true;
        if (event.type === "drop" && event.dataTransfer?.files?.length) uploadStarted = true;
        if (event.type === "change") { pickerOpen = false; uploadStarted = Boolean(event.target.files?.length); }
        if (event.type === "cancel") pickerOpen = false;
        postUploadState();
        if (event.type === "cancel" || (event.type === "change" && !uploadStarted)) checkVersion();
    }
    for (const type of ["click", "drop", "change", "cancel"]) doc.addEventListener(type, trackUpload, true);

    function post(data) {
        coreWindow.top.postMessage({...data, traceId,
            ...(data.type === "costerly:app-ready" ? {sentAt: Date.now()} : {})}, hostOrigin);
    }

    function protection(phase, transition, reason = "") {
        post({type: "costerly:workflow-protection", phase, reason,
              protocol: 1, revision, screen: displayed?.screen || receipt.screen,
              transition: transition?.name || "", transitionId: transition?.id || "",
              regional: Boolean(transition?.local), hostBuild: hostBuild || ""});
    }

    function closeRecovery(reason) {
        if (!recovery) return;
        const previous = recovery;
        recovery = null;
        previous.cover.remove();
        if (previous.app) previous.app.inert = previous.wasInert;
        protection("recovery_end", previous, reason);
    }

    function requestUpdate(name, id) {
        if (recovery) return;
        const cover = doc.createElement("div");
        cover.id = "costerly-workflow-recovery";
        cover.setAttribute("role", "dialog");
        cover.setAttribute("aria-modal", "true");
        cover.setAttribute("aria-label", "App update required");
        cover.style.cssText = "position:fixed;inset:0;z-index:2147483000;background:#f1efef;"
            + "display:flex;flex-direction:column;justify-content:center;align-items:center;gap:16px;"
            + "color:#392c47;font:500 1rem system-ui,sans-serif;text-align:center;padding:24px;";
        const status = doc.createElement("span");
        status.className = "costerly-workflow-status";
        status.setAttribute("role", "status");
        status.textContent = "Update the app to continue.";
        const hint = doc.createElement("p");
        hint.textContent = "Save any changes before updating. You can return to your current page.";
        const update = doc.createElement("a");
        update.textContent = "Update app";
        // A real user-activated top link works even in V1.2.23, which has
        // no ACK or reload-message handler. Do not bypass that missing ACK.
        const url = new URL("/", hostOrigin);
        const route = ["upload", "login"].includes(displayed?.screen) ? {} : displayed?.route || {};
        for (const [key, value] of Object.entries(route)) {
            if (["screen", "route_token", "run_id", "estimate_id", "object_id"].includes(key) && value) {
                url.searchParams.set(key, value);
            }
        }
        update.href = url.href;
        update.target = "_top";
        update.style.cssText = "padding:12px 24px;border-radius:8px;background:#8147ce;color:white;text-decoration:none";
        update.addEventListener("click", event => {
            const saving = Array.from(doc.querySelectorAll('button, [role="button"]')).some(node =>
                node.getClientRects().length && /^saving(?:\.{3}|…)?$/i.test(node.textContent.trim()));
            const active = pickerOpen || uploadStarted || displayed?.screen === "processing" ||
                doc.querySelector('#costerly-upload-processing-shell, .objects-progress-status, [data-costerly-screen="processing"]') ||
                Array.from(doc.querySelectorAll('input[type="file"]')).some(input => input.files?.length);
            if (active || saving || displayed?.authStorageReady === false) {
                event.preventDefault();
                hint.textContent = saving ? "Finish the current save before updating."
                    : active ? "Finish the current upload or calculation before updating."
                    : "Your sign-in must be saved before updating. Use Retry, then update the app.";
                protection("update_deferred", recovery, saving ? "active_save" : active ? "active_work" : "auth_not_saved");
                return;
            }
            // Conservatively ask on every editable screen. No new draft
            // writer, input listener, persistence path or silent discard.
            if (!["upload", "login"].includes(displayed?.screen) &&
                !coreWindow.confirm("Updating reloads the app. Save any changes first. Update now?")) {
                event.preventDefault();
                protection("update_deferred", recovery, "owner_cancelled");
                return;
            }
            protection("update_requested", recovery, "owner_action");
        });
        const keep = doc.createElement("button");
        keep.textContent = "Keep working";
        keep.addEventListener("click", () => closeRecovery("keep_working"));
        cover.append(status, hint, update, keep);
        const app = doc.querySelector(".stApp");
        recovery = {id, name, cover, app, wasInert: Boolean(app?.inert)};
        doc.body.append(cover);
        if (app) app.inert = true;
        update.focus({preventScroll: true});
        protection("recovery_start", recovery, "protocol_unconfirmed");
    }

    function acceptHost(event) {
        if (event.source === coreWindow.top && event.origin === hostOrigin &&
            event.data?.type === "costerly:workflow-navigation-enabled" &&
            event.data.traceId === traceId && event.data.protocol === 1) {
            const firstAck = !enabled;
            enabled = true;
            // Retain only the verified wrapper context across Core document
            // navigation. This is UI correlation, never authentication state.
            try {
                const value = JSON.stringify({traceId, hostOrigin});
                const key = "costerly.workflow.host-context.v1";
                if (coreWindow.sessionStorage.getItem(key) !== value) coreWindow.sessionStorage.setItem(key, value);
            } catch (_) {}
            // Empty means a supported older wrapper. Migrate it once using
            // its existing correlated reload command, only on empty Upload.
            hostBuild = String(event.data.buildVersion || "");
            hostManagesDeployRefresh = event.data.buildSignalProtocol === 1;
            if (firstAck) protection("compatible", null);
            closeRecovery("compatibility_confirmed");
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
        if (message.screen === "account" && message.metrics?.profile_tab) {
            const selected = find('.st-key-company_profile_tab [role="tab"][aria-selected="true"]');
            if (!selected || selected.textContent.trim() !== message.metrics.profile_tab) return false;
        }
        if (message.screen !== "file_review") return true;
        const button = Array.from(doc.querySelectorAll("button")).find(node =>
            node.textContent.trim().toLowerCase() === "continue to project" &&
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

    function close(transition, reason = "ready") {
        stopWatching(transition);
        if (transition.app) transition.app.inert = transition.wasInert;
        transition.cover.remove();
        pending = null;
        protection("cover_end", transition, reason);
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
        if ((!enabled && name !== "version_refresh") || pending || !target ||
            (!selectors[displayed?.screen] && !(name === "version_refresh" && displayed?.screen === "login"))) return false;
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
        protection("cover_start", transition);
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
            if (message.screen === displayed?.screen) return true;
            // A server-authenticated departure (including expired auth) wins
            // over the update cover. Never strand Login or an accepted job.
            const refresh = pending;
            displayed = message;
            if (message.screen === "login" || message.screen.endsWith("_error")) closeRecovery("auth_or_error");
            pickerOpen = false;
            uploadStarted = false;
            post({...message, transitionId: refresh.id});
            announceBuild(message);
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
            if (message.screen === "login" || message.screen.endsWith("_error")) closeRecovery("auth_or_error");
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
        // Fragment completion and the next tab's ready can overlap. Keep one
        // watcher, and let the actual render marker select its own receipt.
        // Replacing/cancelling a candidate can strand its pending frame or
        // let a delayed older receipt displace the current rendered result.
        transition.receipts ||= new Map();
        transition.receipts.set(message.runId, message);
        if (transition.schedule) {
            transition.schedule();
            return true;
        }
        let stableRun = null;
        const check = () => {
            transition.frame = null;
            if (pending !== transition) return;
            const marker = find("[data-costerly-render-id]");
            const accepted = transition.receipts.get(marker?.dataset.costerlyRenderId);
            if (!accepted || !readyTarget(accepted)) {
                stableRun = null;
                return;
            }
            if (stableRun !== accepted.runId) {
                stableRun = accepted.runId;
                schedule();
                return;
            }
            if (!transition.local) {
                coreWindow.scrollTo(0, 0);
                doc.querySelectorAll(".stMain, [data-testid='stAppViewContainer']").forEach(node => {
                    node.scrollTop = 0;
                });
            }
            displayed = {...accepted, settledRun: accepted.runId};
            if (accepted.screen !== "upload") { pickerOpen = false; uploadStarted = false; }
            post({...accepted, transitionId: transition.id});
            announceBuild(accepted);
            close(transition);
            checkVersion();
        };
        const schedule = () => {
            if (!transition.frame) transition.frame = coreWindow.requestAnimationFrame(check);
        };
        transition.schedule = schedule;
        transition.observer = new coreWindow.MutationObserver(schedule);
        transition.observer.observe(doc.body, {childList: true, subtree: true,
                                               attributes: true, attributeFilter: ["data-stale", "disabled"]});
        schedule();
        return true;
    }

    const controller = {
        traceId, revision, begin, ready, announceBuild, resumeAuthWrite, requestUpdate,
        supports: name => Boolean(routes[name]),
        enabled: () => enabled,
        busy: () => Boolean(pending || recovery),
        versionMatched: buildsMatch,
        fail: () => { if (pending) showFailure(pending, "navigation_control_unavailable"); },
        dispose: () => {
            coreWindow.removeEventListener("message", acceptHost);
            for (const type of ["click", "drop", "change", "cancel"]) doc.removeEventListener(type, trackUpload, true);
            if (pending) close(pending, "disposed");
            closeRecovery("disposed");
        },
    };
    coreWindow[key] = controller;
    return controller;
}
