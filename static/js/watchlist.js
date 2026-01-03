// Watchlist Page Logic

function refreshKPIs() {
    const rows = Array.from(document.querySelectorAll('#watchlistBody tr'));
    const total = rows.length;
    const buy = rows.filter(r => r.dataset.signal === 'BUY').length;
    const sell = rows.filter(r => r.dataset.signal === 'SELL').length;

    const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    setText('kpiWatchCount', total);
    setText('kpiBuyCount', buy);
    setText('kpiSellCount', sell);
}

function applyFilters() {
    const q = (document.getElementById('wlSearch')?.value || '').trim().toUpperCase();
    const sig = (document.getElementById('wlSignal')?.value || '').trim();
    const sector = (document.getElementById('wlSector')?.value || '').trim();

    const rows = Array.from(document.querySelectorAll('#watchlistBody tr'));
    rows.forEach(r => {
        const okQ = !q || (r.dataset.symbol || '').includes(q);
        const okSig = !sig || r.dataset.signal === sig;
        const okSector = !sector || r.dataset.sector === sector;
        r.style.display = (okQ && okSig && okSector) ? '' : 'none';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    refreshKPIs();
    ['wlSearch', 'wlSignal', 'wlSector'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', applyFilters);
        if (el) el.addEventListener('change', applyFilters);
    });

    // Handle "Remove" buttons if they exist
    // This requires backend integration, for now maybe just UI removal?
    // Not implemented in original script, so we leave it.
});
