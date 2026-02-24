// Market Page Logic - Ultra Robust Filter & Search

/**
 * Populate the sector dropdown from the database API.
 */
async function populateSectorsDropdown() {
    const select = document.getElementById('market-sector-select');
    if (!select) return;

    try {
        const res = await fetch('/api/sectors/');
        const json = await res.json();

        if (json.success && json.sectors) {
            select.innerHTML = '<option value="">All Sectors</option>';
            json.sectors.forEach(sector => {
                const option = document.createElement('option');
                option.value = sector.name;
                option.textContent = sector.name;
                select.appendChild(option);
            });
        }
    } catch (e) {
        console.error("Failed to populate sectors:", e);
    }
}

// Global state
let allMarketData_global = [];
let filteredData_global = [];
let currentPage_global = 1;
const PAGE_SIZE_global = 50;

async function initMarketPage() {
    const tbody = document.getElementById('marketBody');
    if (!tbody) return;

    // Direct element refs to avoid conflicts
    const searchInput = document.getElementById('market-search-input');
    const sectorSelect = document.getElementById('market-sector-select');
    const dateInput = document.getElementById('marketDate');

    if (sectorSelect) {
        await populateSectorsDropdown();
        sectorSelect.addEventListener('change', function () { applyFilters(); });
    }

    if (searchInput) {
        // Direct event listener for max reliability
        searchInput.addEventListener('input', debounce(function () {
            applyFilters();
        }, 300));
    }

    if (dateInput) {
        initDatePicker();
        dateInput.addEventListener('change', function () { fetchMarketData(); });
    }

    setupPagination();
    await fetchMarketData();
}

/**
 * Core Fetch: Gets data from server.
 */
async function fetchMarketData() {
    const tbody = document.getElementById('marketBody');
    const countEl = document.getElementById('marketCount');
    const dateInput = document.getElementById('marketDate');
    const dateVal = dateInput ? dateInput.value : '';

    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4"><i class="fa-solid fa-spinner fa-spin me-2"></i>Loading live market data...</td></tr>';
    }
    if (countEl) countEl.textContent = 'Loading...';

    try {
        const params = new URLSearchParams();
        if (dateVal) params.append('date', dateVal);

        const res = await fetch('/api/market-data/?' + params.toString());
        const json = await res.json();

        if (json.success) {
            allMarketData_global = json.stocks || [];
            applyFilters(); // Filter and render

            if (json.date && dateInput && !dateInput.value) {
                dateInput.value = json.date;
            }
        } else {
            if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger p-4">Error: ' + (json.error || 'Unknown') + '</td></tr>';
        }
    } catch (e) {
        console.error("Fetch error:", e);
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger p-4">Failed to fetch data.</td></tr>';
    }
}

async function initDatePicker() {
    const dateInput = document.getElementById('marketDate');
    if (!dateInput) return;
    try {
        const res = await fetch('/api/available-dates/');
        const json = await res.json();
        if (json.success && json.dates && json.dates.length > 0) {
            dateInput.max = json.latest_date;
            dateInput.min = json.oldest_date;
            if (!dateInput.value) dateInput.value = json.latest_date;
        }
    } catch (e) { console.error("Failed to init dates:", e); }
}

/**
 * Filter logic - filters allMarketData into filteredData
 */
function applyFilters() {
    const searchInput = document.getElementById('market-search-input');
    const sectorSelect = document.getElementById('market-sector-select');
    const countEl = document.getElementById('marketCount');

    const term = searchInput ? searchInput.value.trim().toUpperCase() : '';
    const sector = sectorSelect ? sectorSelect.value : '';

    let result = allMarketData_global;

    // 1. Sector Filter
    if (sector && sector !== '') {
        result = result.filter(function (item) {
            const itemSec = (item.sector || 'Others').trim();
            return itemSec === sector;
        });
    }

    // 2. Search Filter
    if (term && term !== '') {
        result = result.filter(function (item) {
            const sym = (item.symbol || '').toUpperCase();
            const name = (item.company_name || '').toUpperCase();
            return sym.indexOf(term) !== -1 || name.indexOf(term) !== -1;
        });
    }

    filteredData_global = result;
    currentPage_global = 1;

    if (countEl) countEl.textContent = filteredData_global.length + ' Stocks';

    renderTable();
    updatePaginationUI();
}

function renderTable() {
    const tbody = document.getElementById('marketBody');
    if (!tbody) return;

    if (filteredData_global.length === 0) {
        if (allMarketData_global.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4">No price data for this date.</td></tr>';
        } else {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4">No stocks match your search.</td></tr>';
        }
        return;
    }

    const start = (currentPage_global - 1) * PAGE_SIZE_global;
    const end = start + PAGE_SIZE_global;
    const pageItems = filteredData_global.slice(start, end);

    tbody.innerHTML = pageItems.map(function (item) {
        const ltp = Number(item.ltp || 0);
        const chg = Number(item.change_pct || 0);
        const cls = chg >= 0 ? 'text-success' : 'text-danger';
        const displaySector = item.sector || 'Others';

        return '<tr>' +
            '<td style="font-weight:800;">' +
            '<a href="/trade/?symbol=' + item.symbol + '" class="text-decoration-none text-dark" title="' + (item.company_name || item.symbol) + '">' +
            item.symbol +
            '</a><br>' +
            '<small class="text-muted" style="font-size:0.75em">' + displaySector + '</small>' +
            '</td>' +
            '<td style="font-weight:700;">Rs ' + fmtNumber(ltp, 2) + '</td>' +
            '<td class="' + cls + '" style="font-weight:900;">' + (chg >= 0 ? '+' : '') + fmtNumber(chg, 2) + '%</td>' +
            '<td class="text-end">' + fmtNumber(item.open || 0, 2) + '</td>' +
            '<td class="text-end">' + fmtNumber(item.high || 0, 2) + '</td>' +
            '<td class="text-end">' + fmtNumber(item.low || 0, 2) + '</td>' +
            '<td class="text-end pe-4">' + fmtInt(item.volume || 0) + '</td>' +
            '</tr>';
    }).join('');
}

function setupPagination() {
    const prev = document.getElementById('btnPrev');
    const next = document.getElementById('btnNext');
    if (prev) prev.onclick = function () {
        if (currentPage_global > 1) { currentPage_global--; renderTable(); updatePaginationUI(); }
    };
    if (next) next.onclick = function () {
        const max = Math.ceil(filteredData_global.length / PAGE_SIZE_global);
        if (currentPage_global < max) { currentPage_global++; renderTable(); updatePaginationUI(); }
    };
}

function updatePaginationUI() {
    const max = Math.ceil(filteredData_global.length / PAGE_SIZE_global) || 1;
    const info = document.getElementById('pageInfo');
    const prev = document.getElementById('btnPrev');
    const next = document.getElementById('btnNext');

    if (info) info.textContent = 'Page ' + currentPage_global + ' of ' + max;
    if (prev) prev.disabled = (currentPage_global === 1);
    if (next) next.disabled = (currentPage_global === max);
}

function debounce(func, wait) {
    let timeout;
    return function () {
        const context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function () {
            func.apply(context, args);
        }, wait);
    };
}

function fmtNumber(n, d) {
    return (n || 0).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
}
function fmtInt(n) {
    return (n || 0).toLocaleString('en-US');
}

document.addEventListener('DOMContentLoaded', initMarketPage);
