// Market Page Logic with Server-Side Filtering

let currentPage = 1;
const PAGE_SIZE = 50;

// State to hold current data for client-side pagination if needed, 
// though we might want server-side pagination later. 
// For now, API returns all rows for a date, so we paginate client-side.
let currentData = [];

async function initMarketPage() {
    const tbody = document.getElementById('marketBody');
    if (!tbody) return;

    // 1. Initialize Date Picker
    await initDatePicker();

    // 2. Populate Sectors Dropdown
    await populateSectors();

    // 3. Initial Fetch
    await fetchMarketData();

    // 4. Event Listeners with Debounce for Search
    document.getElementById('marketSearch')?.addEventListener('input', debounce(fetchMarketData, 500));
    document.getElementById('sectorSelect')?.addEventListener('change', () => {
        currentPage = 1; // Reset to page 1 on filter change
        fetchMarketData();
    });
    document.getElementById('marketDate')?.addEventListener('change', () => {
        currentPage = 1;
        fetchMarketData();
    });

    setupPagination();
}

async function populateSectors() {
    try {
        const res = await fetch('/api/sectors/');
        const json = await res.json();

        if (json.success && json.sectors) {
            const select = document.getElementById('sectorSelect');
            if (select) {
                // Clear existing options except "All Sectors"
                select.innerHTML = '<option value="">All Sectors</option>';

                // Add sectors
                json.sectors.forEach(sector => {
                    const option = document.createElement('option');
                    option.value = sector;
                    option.textContent = sector;
                    select.appendChild(option);
                });
            }
        }
    } catch (err) {
        console.error('Failed to load sectors:', err);
    }
}

async function initDatePicker() {
    try {
        const res = await fetch('/api/available-dates/');
        const json = await res.json();

        if (json.success && json.dates.length > 0) {
            const dateInput = document.getElementById('marketDate');
            if (dateInput) {
                // Set max to latest available date (usually today/yesterday)
                dateInput.max = json.latest_date;
                dateInput.min = json.oldest_date;
                // Default to latest date if not set
                if (!dateInput.value) {
                    dateInput.value = json.latest_date;
                }
            }
        }
    } catch (e) {
        console.error("Failed to init dates", e);
    }
}

async function fetchMarketData() {
    const tbody = document.getElementById('marketBody');
    const countEl = document.getElementById('marketCount');
    const dateVal = document.getElementById('marketDate')?.value || '';
    const sectorVal = document.getElementById('sectorSelect')?.value || '';
    const searchVal = document.getElementById('marketSearch')?.value || '';

    // Show loading state
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4"><i class="fa-solid fa-spinner fa-spin me-2"></i>Loading market data...</td></tr>';
    if (countEl) countEl.textContent = 'Loading...';

    try {
        // Construct query params
        const params = new URLSearchParams();
        if (dateVal) params.append('date', dateVal);
        if (sectorVal) params.append('sector', sectorVal);
        if (searchVal) params.append('search', searchVal);

        const res = await fetch(`/api/market-data/?${params.toString()}`);
        const json = await res.json();

        if (json.success) {
            currentData = json.stocks || [];

            // Update UI with metadata
            if (countEl) countEl.textContent = `${json.total_stocks} Stocks`;

            // Check if we have data
            if (currentData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4">No data found for selected filters.</td></tr>';
            } else {
                renderTable();
            }

            updatePaginationUI();
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger p-4">Error: ${json.error || 'Unknown error'}</td></tr>`;
        }
    } catch (e) {
        console.error(e);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger p-4">Failed to fetch data.</td></tr>';
    }
}

function renderTable() {
    const tbody = document.getElementById('marketBody');
    if (!tbody || !currentData.length) return;

    // Client-side pagination logic
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const pageItems = currentData.slice(start, end);

    tbody.innerHTML = pageItems.map(item => {
        const ltp = Number(item.ltp);
        const chg = Number(item.change_pct);
        const cls = chg >= 0 ? 'text-success' : 'text-danger';
        const sectorName = item.sector ? `<br><small class="text-muted" style="font-size:0.7em">${item.sector}</small>` : '';

        return `
        <tr>
          <td style="font-weight:800;">
            <a href="/trade/?symbol=${item.symbol}" class="text-decoration-none text-dark hover-primary">
                ${item.symbol}
            </a>
            ${sectorName}
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
        const max = Math.ceil(currentData.length / PAGE_SIZE);
        if (currentPage < max) { currentPage++; renderTable(); updatePaginationUI(); }
    });
}

function updatePaginationUI() {
    const max = Math.ceil(currentData.length / PAGE_SIZE) || 1;
    const info = document.getElementById('pageInfo');
    if (info) info.textContent = `Page ${currentPage} of ${max}`;

    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');

    if (btnPrev) btnPrev.disabled = currentPage === 1;
    if (btnNext) btnNext.disabled = currentPage === max;
}

// Utility debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Init
initMarketPage();
