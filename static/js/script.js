document.addEventListener('DOMContentLoaded', function () {
    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // Global Utils
    window.fmtNumber = function (n, digits = 2) {
        if (n === null || n === undefined || isNaN(n)) return '—';
        return Number(n).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
    };

    window.fmtInt = function (n) {
        if (n === null || n === undefined || isNaN(n)) return '—';
        return Number(n).toLocaleString();
    };

    window.isMarketActive = function (latestIso, minutes = 5) {
        try {
            const t = new Date(latestIso).getTime();
            return (Date.now() - t) <= minutes * 60 * 1000;
        } catch { return false; }
    };

    window.safeText = function (el, text) { if (el) el.textContent = text; };

    // Navbar Market Summary
    async function updateNavbarBar() {
        const barIndices = document.getElementById('barIndices');
        if (!barIndices) return; // Only run if bar exists

        try {
            const [nepseRes, sectorRes, summaryRes] = await Promise.all([
                fetch('/api/nepse-index/'),
                fetch('/api/sector-indices/'),
                fetch('/api/market-summary/')
            ]);

            const nepseJson = await nepseRes.json();
            const sectorJson = await sectorRes.json();
            const summaryJson = await summaryRes.json();

            let nepseVal = null, nepseChg = null;
            if (nepseJson?.success) { nepseVal = nepseJson.data.value; nepseChg = nepseJson.data.change_pct; }

            let sensitive = null, floatIdx = null;
            if (sectorJson?.success && Array.isArray(sectorJson.data)) {
                sensitive = sectorJson.data.find(x => (x.name || '').toLowerCase().includes('sensitive'));
                floatIdx = sectorJson.data.find(x => (x.name || '').toLowerCase().includes('float'));
            }

            const parts = [];
            parts.push(`
                <div class="nav-index-item">
                    <span class="nav-index-name">NEPSE</span>
                    <span class="nav-index-value">${nepseVal !== null ? fmtNumber(nepseVal, 2) : '—'}</span>
                    <span class="nav-index-change ${nepseChg !== null && nepseChg >= 0 ? 'text-success' : 'text-danger'}">
                        ${nepseChg !== null ? (nepseChg >= 0 ? '+' : '') + fmtNumber(nepseChg, 2) + '%' : '—'}
                    </span>
                </div>
            `);

            if (sensitive) {
                parts.push(`
                    <div class="nav-index-item">
                        <span class="nav-index-name">SENSITIVE</span>
                        <span class="nav-index-value">${fmtNumber(sensitive.value, 2)}</span>
                        <span class="nav-index-change ${Number(sensitive.change_pct) >= 0 ? 'text-success' : 'text-danger'}">
                            ${(Number(sensitive.change_pct) >= 0 ? '+' : '') + fmtNumber(sensitive.change_pct, 2)}%
                        </span>
                    </div>
                `);
            }

            if (floatIdx) {
                parts.push(`
                    <div class="nav-index-item">
                        <span class="nav-index-name">FLOAT</span>
                        <span class="nav-index-value">${fmtNumber(floatIdx.value, 2)}</span>
                        <span class="nav-index-change ${Number(floatIdx.change_pct) >= 0 ? 'text-success' : 'text-danger'}">
                            ${(Number(floatIdx.change_pct) >= 0 ? '+' : '') + fmtNumber(floatIdx.change_pct, 2)}%
                        </span>
                    </div>
                `);
            }

            barIndices.innerHTML = parts.join('');

            const turnoverEl = document.getElementById('barTotalTurnover');
            const volumeEl = document.getElementById('barTotalVolume');
            const statusEl = document.getElementById('barSessionStatus');

            if (summaryJson?.success) {
                const d = summaryJson.data;
                if (turnoverEl) turnoverEl.textContent = `Turnover: ${fmtNumber(d.total_turnover, 2)}`;
                if (volumeEl) volumeEl.textContent = `Volume: ${fmtInt(d.total_traded_shares)}`;
                if (statusEl) statusEl.textContent = isMarketActive(d.timestamp, 5) ? 'CONTINUOUS' : 'NO ACTIVE SESSIONS';
            }
        } catch (e) {
            console.error(e);
        }
    }

    // Run Navbar Update if element exists
    if (document.getElementById('barIndices')) {
        updateNavbarBar();
        setInterval(updateNavbarBar, 30000); // Global 30s update for navbar
    }

    // Navbar Search Logic
    const sIn = document.getElementById('stockSearch');
    const rBox = document.getElementById('searchResults');
    let sT;

    if (sIn) {
        sIn.addEventListener('input', () => {
            clearTimeout(sT);
            const q = sIn.value.trim();
            if (q.length < 2) { if (rBox) rBox.style.display = 'none'; return; }

            sT = setTimeout(async () => {
                try {
                    const res = await fetch(`/api/search/?q=${encodeURIComponent(q)}`);
                    const d = await res.json();
                    const list = Array.isArray(d.data) ? d.data : [];

                    if (rBox && list.length > 0) {
                        rBox.innerHTML = list.map(s => `
                            <div class="search-result-item" onclick="window.location.href='/trade/?symbol=${s.symbol}'" style="padding:.5rem;cursor:pointer;border-bottom:1px solid #eee;">
                                <strong>${s.symbol}</strong>
                                <span>
                                    Rs ${fmtNumber(s.ltp, 2)}
                                    <small class="${Number(s.change_pct) >= 0 ? 'text-success' : 'text-danger'}">
                                        (${Number(s.change_pct) >= 0 ? '+' : ''}${fmtNumber(s.change_pct, 2)}%)
                                    </small>
                                </span>
                            </div>
                        `).join('');
                        rBox.style.display = 'block';
                    } else if (rBox) {
                        rBox.style.display = 'none';
                    }
                } catch {
                    if (rBox) rBox.style.display = 'none';
                }
            }, 250);
        });

        document.addEventListener('click', (e) => {
            if (!rBox) return;
            if (!sIn.contains(e.target) && !rBox.contains(e.target)) rBox.style.display = 'none';
        });
    }
});