(() => {
    const host = window.parent;
    const doc = host.document;
    const estimateId = __ESTIMATE_ID__;
    const key = "__costerlyObjectsActionsCleanup";
    if (host[key]) host[key]();
    function invalidate(event) {
        const input = event.target.closest?.('.objects-pricing-price-input, .objects-pricing-quantity-input');
        if (!input || input.closest('.objects-pricing-row')?.dataset.estimateId !== estimateId) return;
        const generate = doc.querySelector('[class*="st-key-objects_generate_proposal_"] button');
        const set = doc.querySelector('.st-key-objects_set_prices button');
        if (generate) generate.disabled = true;
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
                second.querySelector('small').textContent = "Keep or edit suggested prices";
                third.dataset.state = "future";
                third.querySelector('.objects-stage-marker').textContent = "3";
            }
        }
    }
    // Observe existing input events only to update the new header/footer.
    // Original input handlers, requests, normalization and rows stay untouched.
    doc.addEventListener("input", invalidate, true);
    host[key] = () => doc.removeEventListener("input", invalidate, true);
})();
