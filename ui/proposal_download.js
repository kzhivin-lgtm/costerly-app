(() => {
    const request = __DOWNLOAD_REQUEST__;
    const host = window.parent;
    const key = 'costerly.proposal-download.' + request.token;
    const completed = host.__costerlyProposalDownloads || (host.__costerlyProposalDownloads = new Set());
    if (completed.has(key)) return;
    try { if (host.sessionStorage.getItem(key)) return; } catch (_) {}
    if (!request.url || !/^(https?:|data:application\/pdf)/.test(request.url)) return;
    const link = host.document.createElement('a');
    link.href = request.url;
    link.download = 'Proposal.pdf';
    link.style.display = 'none';
    host.document.body.appendChild(link);
    link.click();
    link.remove();
    completed.add(key);
    try { host.sessionStorage.setItem(key, '1'); } catch (_) {}
})();
