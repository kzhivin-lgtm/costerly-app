(() => {
    const host = window.parent;
    const doc = host.document;
    const estimateId = __ESTIMATE_ID__;
    const key = "__costerlyObjectsActionsCleanup";
    if (host[key]) host[key]();
    const dirty = host.__costerlyProposalDrafts ||= new Map();
    function revoke() {
        const generate = doc.querySelector('[class*="st-key-objects_generate_proposal_"] button');
        const set = doc.querySelector('.st-key-objects_set_prices button');
        if (generate) generate.disabled = true;
        const download = doc.querySelector('.st-key-final_approval_approved a');
        if (download) {
            download.removeAttribute('href');
            download.setAttribute('aria-disabled', 'true');
            const label = download.querySelector('p');
            if (label) label.textContent = 'GENERATE PROPOSAL';
        }
        const secondary = doc.querySelector('.objects-pricing-downloads a.objects-document-button');
        if (secondary) {
            secondary.removeAttribute('href');
            secondary.setAttribute('aria-disabled', 'true');
        }
        const steps = doc.querySelector('.objects-workflow-stages');
        const allReviewed = steps?.querySelector('[data-stage="1"]')?.dataset.state === "complete";
        if (set) set.disabled = !allReviewed;
        if (steps) {
            const second = steps.querySelector('[data-stage="2"]');
            const third = steps.querySelector('[data-stage="3"]');
            if (second && third) {
                second.dataset.state = allReviewed ? "current" : "future";
                second.removeAttribute("aria-current");
                third.removeAttribute("aria-current");
                if (allReviewed) second.setAttribute("aria-current", "step");
                second.querySelector('.objects-stage-marker').textContent = "2";
                third.dataset.state = "future";
                third.querySelector('.objects-stage-marker').textContent = "3";
            }
        }
    }
    function invalidate(event) {
        const input = event.target.closest?.('.objects-pricing-price-input, .objects-pricing-quantity-input');
        if (!input || input.closest('.objects-pricing-row')?.dataset.estimateId !== estimateId) return;
        dirty.set(estimateId, doc.querySelector('.objects-workflow-stages')?.dataset.confirmationId);
        revoke();
    }
    // Observe existing input events only to update the new header/footer.
    // Original input handlers, requests, normalization and rows stay untouched.
    doc.addEventListener("input", invalidate, true);
    const confirmationId = doc.querySelector('.objects-workflow-stages')?.dataset.confirmationId;
    if (dirty.has(estimateId)) {
        if (dirty.get(estimateId) === confirmationId) revoke();
        else dirty.delete(estimateId);
    }
    function proposalPending(event) {
        const button = event.target.closest?.('[class*="st-key-objects_generate_proposal_"] button');
        if (!button || button.disabled) return;
        // The delegated React click has already accepted the native action.
        button.disabled = true;
        button.setAttribute('aria-busy', 'true');
        const label = button.querySelector('p');
        if (label) label.textContent = 'GENERATING…';
    }
    doc.addEventListener('click', proposalPending);

    const metricsHost = doc.querySelector('.st-key-objects_header_metrics');
    function applyMetricsView() {
        if (!metricsHost) return;
        const collapsed = host.__costerlyObjectsMetricsCollapsed === true;
        metricsHost.dataset.metricsCollapsed = String(collapsed);
        const button = metricsHost.querySelector('.objects-metrics-toggle');
        if (button) {
            button.setAttribute('aria-expanded', String(!collapsed));
            button.setAttribute('aria-label', collapsed ? 'Expand technical metrics' : 'Collapse technical metrics');
        }
    }
    function toggleMetrics(event) {
        if (!event.target.closest?.('.objects-metrics-toggle') || !metricsHost?.contains(event.target)) return;
        host.__costerlyObjectsMetricsCollapsed = host.__costerlyObjectsMetricsCollapsed !== true;
        applyMetricsView();
    }
    // Only reconcile the existing metrics subtree when its 1.5s progress
    // fragment replaces markup. No timer, request, persistence or Python rerun.
    const metricsObserver = metricsHost ? new host.MutationObserver(applyMetricsView) : null;
    metricsObserver?.observe(metricsHost, {childList: true, subtree: true});
    doc.addEventListener('click', toggleMetrics);
    applyMetricsView();
    host[key] = () => {
        doc.removeEventListener("input", invalidate, true);
        doc.removeEventListener('click', proposalPending);
        doc.removeEventListener('click', toggleMetrics);
        metricsObserver?.disconnect();
    };
})();
