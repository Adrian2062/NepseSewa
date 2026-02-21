/**
 * stocks.js — All Stocks Page
 * Features: API-driven sectors/stocks, multi-sector pill filter,
 *           symbol+company search, client-side caching, pagination.
 */

const STOCKS_CACHE_KEY = 'nepsesewa_stocks_v1';
const SECTORS_CACHE_KEY = 'nepsesewa_sectors_v1';
const PAGE_SIZE = 50;

let allStocks = [];        // raw data from API
let filteredStocks = [];   // after sector + search filter
let currentPage = 1;
let selectedSectors = new Set(); // IDs of selected sectors (empty = all)

// ─── Bootstrap ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([loadSectors(), loadStocks()]);
    setupSearch();
    setupPagination();
    applyFilters();
});

// ─── Data Loading ─────────────────────────────────────────────────────────────
async function loadSectors() {
    try {
        let sectors = sessionStorage.getItem(SECTORS_CACHE_KEY);
        if (sectors) {
            sectors = JSON.parse(sectors);
        } else {
            const res = await fetch('/api/sectors/');
            const json = await res.json();
            if (!json.success) return;
            sectors = json.sectors; // [{id, name}, ...]
            sessionStorage.setItem(SECTORS_CACHE_KEY, JSON.stringify(sectors));
        }
        renderSectorPills(sectors);
    } catch (e) {
        console.error('Failed to load sectors', e);
    }
}

async function loadStocks() {
    showLoading(true);
    try {
        let stocks = sessionStorage.getItem(STOCKS_CACHE_KEY);
        if (stocks) {
            allStocks = JSON.parse(stocks);
        } else {
            const res = await fetch('/api/stocks/');
            const json = await res.json();
            if (!json.success) {
                showError('Failed to load stock data.');
                return;
            }
            allStocks = json.stocks;
            sessionStorage.setItem(STOCKS_CACHE_KEY, JSON.stringify(allStocks));
        }
    } catch (e) {
        showError('Network error — could not fetch stocks.');
        console.error(e);
    } finally {
        showLoading(false);
    }
}

// ─── Sector Pills ─────────────────────────────────────────────────────────────
function renderSectorPills(sectors) {
    const container = document.getElementById('sectorPills');
    if (!container) return;

    // "All" pill
    const allPill = createPill('All Sectors', null, true);
    container.appendChild(allPill);

    sectors.forEach(s => {
        container.appendChild(createPill(s.name, s.id, false));
    });
}

function createPill(label, sectorId, isActive) {
    const btn = document.createElement('button');
    btn.className = 'sector-pill' + (isActive ? ' active' : '');
    btn.textContent = label;
    btn.dataset.sectorId = sectorId ?? '';
    btn.addEventListener('click', () => toggleSectorPill(btn, sectorId));
    return btn;
}

function toggleSectorPill(btn, sectorId) {
    const allBtn = document.querySelector('.sector-pill[data-sector-id=""]');

    if (sectorId === null) {
        // Clicked "All Sectors" — clear selections
        selectedSectors.clear();
        document.querySelectorAll('.sector-pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
    } else {
        // Toggle this sector
        if (selectedSectors.has(sectorId)) {
            selectedSectors.delete(sectorId);
            btn.classList.remove('active');
        } else {
            selectedSectors.add(sectorId);
            btn.classList.add('active');
        }
        // Deactivate "All" pill if any sector selected, else re-activate it
        if (selectedSectors.size === 0) {
            allBtn && allBtn.classList.add('active');
        } else {
            allBtn && allBtn.classList.remove('active');
        }
    }

    currentPage = 1;
    applyFilters();
}

// ─── Filtering ────────────────────────────────────────────────────────────────
function applyFilters() {
    const searchVal = (document.getElementById('stockSearch')?.value || '').trim().toLowerCase();

    filteredStocks = allStocks.filter(s => {
        const sectorMatch = selectedSectors.size === 0 || selectedSectors.has(s.sector_id);
        const searchMatch = !searchVal
            || s.symbol.toLowerCase().includes(searchVal)
            || (s.company_name || '').toLowerCase().includes(searchVal);
        return sectorMatch && searchMatch;
    });

    const countEl = document.getElementById('stockCount');
    if (countEl) countEl.textContent = `${filteredStocks.length} Stocks`;

    currentPage = 1;
    renderTable();
    updatePagination();
}

// ─── Table Rendering ──────────────────────────────────────────────────────────
function renderTable() {
    const tbody = document.getElementById('stocksBody');
    if (!tbody) return;

    if (filteredStocks.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="stocks-empty">
            <i class="fa-solid fa-magnifying-glass me-2"></i>No stocks found for the selected filters.
        </td></tr>`;
        return;
    }

    const start = (currentPage - 1) * PAGE_SIZE;
    const pageItems = filteredStocks.slice(start, start + PAGE_SIZE);

    tbody.innerHTML = pageItems.map((s, i) => {
        const rowNum = start + i + 1;
        const sector = s.sector_name || 'Others';
        const sectorClass = sectorColorClass(sector);
        return `<tr class="stock-row" onclick="window.location='/trade/?symbol=${s.symbol}'" style="cursor:pointer;">
            <td class="stock-num">${rowNum}</td>
            <td>
                <div class="stock-symbol">${s.symbol}</div>
                <div class="stock-company">${s.company_name || s.symbol}</div>
            </td>
            <td><span class="sector-badge ${sectorClass}">${sector}</span></td>
        </tr>`;
    }).join('');
}

// Deterministic color class from sector name
function sectorColorClass(name) {
    const map = {
        'Commercial Banks': 'sc-blue',
        'Development Banks': 'sc-indigo',
        'Microfinance': 'sc-purple',
        'Finance': 'sc-violet',
        'Investment': 'sc-teal',
        'Hotels & Tourism': 'sc-orange',
        'Manufacturing & Processing': 'sc-red',
        'Others': 'sc-gray',
        'Hydropower': 'sc-cyan',
        'Life Insurance': 'sc-green',
        'Non-Life Insurance': 'sc-lime',
        'Mutual Fund': 'sc-amber',
        'Corporate Debentures': 'sc-rose',
        'Trading': 'sc-pink',
    };
    return map[name] || 'sc-gray';
}

// ─── Pagination ───────────────────────────────────────────────────────────────
function setupPagination() {
    document.getElementById('btnPrev')?.addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; renderTable(); updatePagination(); }
    });
    document.getElementById('btnNext')?.addEventListener('click', () => {
        const maxPage = Math.ceil(filteredStocks.length / PAGE_SIZE) || 1;
        if (currentPage < maxPage) { currentPage++; renderTable(); updatePagination(); }
    });
}

function updatePagination() {
    const maxPage = Math.ceil(filteredStocks.length / PAGE_SIZE) || 1;
    const info = document.getElementById('pageInfo');
    if (info) info.textContent = `Page ${currentPage} of ${maxPage}`;

    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');
    if (btnPrev) btnPrev.disabled = currentPage <= 1;
    if (btnNext) btnNext.disabled = currentPage >= maxPage;

    const showing = document.getElementById('showingInfo');
    if (showing) {
        const start = filteredStocks.length ? (currentPage - 1) * PAGE_SIZE + 1 : 0;
        const end = Math.min(currentPage * PAGE_SIZE, filteredStocks.length);
        showing.textContent = filteredStocks.length
            ? `Showing ${start}–${end} of ${filteredStocks.length} stocks`
            : 'No stocks to show';
    }
}

// ─── Search ───────────────────────────────────────────────────────────────────
function setupSearch() {
    const input = document.getElementById('stockSearch');
    if (!input) return;
    let timer;
    input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(applyFilters, 250);
    });
    // Clear button
    const clearBtn = document.getElementById('searchClear');
    clearBtn?.addEventListener('click', () => {
        input.value = '';
        applyFilters();
        input.focus();
    });
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = show ? 'flex' : 'none';
}

function showError(msg) {
    const tbody = document.getElementById('stocksBody');
    if (tbody) tbody.innerHTML = `<tr><td colspan="3" class="stocks-empty text-danger">
        <i class="fa-solid fa-triangle-exclamation me-2"></i>${msg}
    </td></tr>`;
}
