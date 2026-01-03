// Market Page Logic

let allData = [];
let filteredData = [];

// Pagination
let currentPage = 1;
const PAGE_SIZE = 50;

async function initMarketPage() {
    const tbody = document.getElementById('marketBody');
    if (!tbody) return;

    // await updateNavbarBar(); // Handled by global script
    await fetchMarketData();

    // Event listeners for filters
    document.getElementById('marketSearch')?.addEventListener('input', applyFilters);
    document.getElementById('sectorSelect')?.addEventListener('change', applyFilters);

    setupPagination();
}

async function fetchMarketData() {
    const tbody = document.getElementById('marketBody');
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4">Loading market data...</td></tr>';

    try {
        const res = await fetch('/api/latest/');
        const json = await res.json();

        if (json.data && Array.isArray(json.data)) {
            allData = json.data;
            // Add dummy sector for filtering if not in API (API usually returns sector, if not we skip)
            // For demo, we might mock sector or use what's available. 
            // The table expects: Symbol, LTP, Change, Open, High, Low, Vol
            applyFilters();
        } else {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger p-4">Failed to load data.</td></tr>';
        }
    } catch (e) {
        console.error(e);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger p-4">Error loading data.</td></tr>';
    }
}

function applyFilters() {
    const q = (document.getElementById('marketSearch')?.value || '').trim().toUpperCase();
    const sec = (document.getElementById('sectorSelect')?.value || '').trim();

    filteredData = allData.filter(item => {
        const sym = (item.symbol || '').toUpperCase();
        // If API doesn't have sector, we ignore sector filter or match by symbol/name
        // Assuming item has 'sector' field?
        // If not, we just filter by search.
        const matchSearch = !q || sym.includes(q);
        // const matchSector = !sec || item.sector === sec; 
        return matchSearch; // && matchSector
    });

    currentPage = 1;
    renderTable();
    updatePaginationUI();
}

function renderTable() {
    const tbody = document.getElementById('marketBody');
    const countEl = document.getElementById('marketCount');
    if (!tbody) return;

    if (countEl) countEl.textContent = `${filteredData.length} Stocks`;

    if (!filteredData.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4">No matching stocks found.</td></tr>';
        return;
    }

    // Slice for pagination
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const pageItems = filteredData.slice(start, end);

    tbody.innerHTML = pageItems.map(item => {
        const ltp = Number(item.ltp);
        const chg = Number(item.change_pct);
        const cls = chg >= 0 ? 'text-success' : 'text-danger';

        return `
        <tr>
          <td style="font-weight:800;">
            <a href="/trade/?symbol=${item.symbol}" class="text-decoration-none text-dark hover-primary">${item.symbol}</a>
          </td>
          <td style="font-weight:700;">Rs ${fmtNumber(ltp, 2)}</td>
          <td class="${cls}" style="font-weight:900;">${chg >= 0 ? '+' : ''}${fmtNumber(chg, 2)}%</td>
          <td class="text-end">${fmtNumber(item.open, 2)}</td>
          <td class="text-end">${fmtNumber(item.high, 2)}</td>
          <td class="text-end">${fmtNumber(item.low, 2)}</td>
          <td class="text-end">${fmtInt(item.volume)}</td>
        </tr>
      `;
    }).join('');
}

function setupPagination() {
    document.getElementById('btnPrev')?.addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; renderTable(); updatePaginationUI(); }
    });
    document.getElementById('btnNext')?.addEventListener('click', () => {
        const max = Math.ceil(filteredData.length / PAGE_SIZE);
        if (currentPage < max) { currentPage++; renderTable(); updatePaginationUI(); }
    });
}

function updatePaginationUI() {
    const max = Math.ceil(filteredData.length / PAGE_SIZE) || 1;
    const info = document.getElementById('pageInfo');
    if (info) info.textContent = `Page ${currentPage} of ${max}`;

    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');

    if (btnPrev) btnPrev.disabled = currentPage === 1;
    if (btnNext) btnNext.disabled = currentPage === max;
}

// Init
initMarketPage();
setInterval(async () => {
    // await updateNavbarBar(); // Global handles this
    // We can auto-refresh market data if desired, but filters might reset?
    // Let's just refresh data and re-apply filters (keeping page?)
    // proper implementation would be complex. For now, simple refresh:
    // await fetchMarketData(); 
}, 30000);
