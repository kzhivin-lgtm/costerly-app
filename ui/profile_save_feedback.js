// One acknowledgement-driven feedback path for the existing Profile Save actions.
function installProfileSaveFeedback(win, companyId) {
    const doc = win.document, key = '__costerlyProfileSaveFeedbackCleanup';
    win[key]?.();
    const selectors = {
        metrics: '[data-company-settings-save="metrics"]',
        pricing: '[data-company-settings-save="pricing"]',
        contacts: '.st-key-profile_save_contacts button',
        bank_details: '.st-key-profile_save_bank_details button',
        machinery: '.st-key-company_machinery_save_all button',
        logo: '.st-key-save_company_logo button',
        labor: '[class*="st-key-labor_form_"] button',
    };
    let pending = null, saved = null;
    const selectedTab = () => doc.querySelector('.st-key-company_profile_tab [aria-selected="true"]')?.textContent.trim();
    const labelNode = button => button?.querySelector('p') || button;
    const label = button => labelNode(button)?.textContent.trim();
    function buttonFor(action) {
        return Array.from(doc.querySelectorAll(selectors[action] || ':not(*)')).find(button =>
            !button.closest('[data-stale="true"]') && (action !== 'labor' || /^(Add Worker|Save Worker|Saving…|Saved)$/.test(label(button))));
    }
    function paint(button, text, state, disabled) {
        if (!button) return;
        labelNode(button).textContent = text;
        button.toggleAttribute('data-profile-save-saved', state === 'saved');
        button.toggleAttribute('data-profile-save-pending', state === 'pending');
        button.disabled = disabled;
    }
    function clearSaved() {
        if (!saved) return;
        win.clearTimeout(saved.timer);
        if (saved.button.isConnected) paint(saved.button, saved.original, '', false);
        saved = null;
    }
    function stopPending() {
        if (!pending) return;
        pending.observer.disconnect();win.clearTimeout(pending.timer);
        if (pending.button.isConnected) paint(pending.button, pending.original, '', false);
        pending = null;
    }
    function receive() {
        if (!pending) return;
        if (!doc.querySelector('.company-profile-heading') || selectedTab() !== pending.tab) { stopPending();return; }
        const receipt = Array.from(doc.querySelectorAll('[data-profile-save-ack]')).find(node =>
            node.dataset.profileSaveCompany === companyId && node.dataset.profileSaveAction === pending.action &&
            !pending.before.has(node.dataset.profileSaveAck) && !node.closest('[data-stale="true"]'));
        const button = buttonFor(pending.action);
        if (!receipt || !button || doc.querySelector('[data-stale="true"]')) return;
        const original = button === pending.button ? pending.original : label(button);
        const edited = pending.edited;
        const ok = receipt.dataset.profileSaveOk === 'true';
        stopPending();
        if (!ok || edited) {paint(button, original, '', false);return;}
        paint(button, 'Saved', 'saved', true);
        saved = {button, original, timer: win.setTimeout(clearSaved, 2000)};
    }
    function click(event) {
        const button = event.target?.closest?.('button');
        if (!button || !doc.querySelector('.company-profile-heading')) return;
        if (button.getAttribute('role') === 'tab') {clearSaved();stopPending();return;}
        const action = Object.keys(selectors).find(name => button.matches(selectors[name]) &&
            (name !== 'labor' || /^(Add Worker|Save Worker)$/.test(label(button))));
        if (!action || (action === 'logo' && label(button) === 'Change Logo' && !doc.querySelector('.company-logo-pending'))) return;
        if (pending || button.disabled) {event.preventDefault();event.stopImmediatePropagation();return;}
        clearSaved();
        const request = {action, button, original: label(button), tab: selectedTab(), edited: false,
            before: new Set(Array.from(doc.querySelectorAll('[data-profile-save-ack]'), node => node.dataset.profileSaveAck))};
        pending = request;
        request.observer = new win.MutationObserver(receive);
        request.observer.observe(doc.body, {childList:true, subtree:true, attributes:true, attributeFilter:['data-stale','aria-selected','data-profile-save-ack']});
        // Keep native/bridge click delivery intact, then prevent duplicate submissions.
        win.queueMicrotask(() => {if (pending === request) paint(button, 'Saving…', 'pending', true);});
        // Only UI state expires; no callback, polling or fabricated write success.
        request.timer = win.setTimeout(stopPending, 30000);
    }
    function input(event) {
        if (!event.target?.closest?.('.st-key-company_profile_tab')) return;
        clearSaved();if (pending) pending.edited = true;
    }
    function cleanup() {
        clearSaved();stopPending();doc.removeEventListener('click',click,true);doc.removeEventListener('input',input,true);
        if (win[key] === cleanup) delete win[key];
    }
    doc.addEventListener('click',click,true);doc.addEventListener('input',input,true);win[key] = cleanup;
    return cleanup;
}
