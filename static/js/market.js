// Market Page Logic with Strict Client-Side Sector Mapping

// User-provided Sector Data
const SECTOR_DATA = {
    "Commercial Banks": ["ADBL", "GBIME", "CZBIL", "NIMBPO", "SBL", "SANIMA", "NMB", "NICA", "MBL", "NBL", "EBL", "PCBL", "SCB", "LSL", "SBI", "KBL", "PRVU"],
    "Development Banks": ["MLBL", "KSBBL", "MDB", "MNBBL", "SINDU", "GRDBL", "JBBL", "EDBL", "GBBL", "NABBC", "SADBL", "CORBL", "SHINE", "LBBL", "SAPDBL"],
    "Microfinance": ["LLBS", "SMFBS", "MERO", "SKBBL", "CYCL", "FOWAD", "NUBL", "SWBBL", "DDBL", "GLBSL", "GMFBS", "MSLB", "FMDBL", "JBLB", "ULBSL", "DLBS", "NMFBS", "NMLBBL", "MLBSL", "ALBSL"],
    "Finance": ["PROFL", "MPFL", "CFCL", "MFIL", "JFL", "SFCL", "GFCL", "PFL", "NFS", "SIFC", "RLFL", "ICFC", "BFC"],
    "Investment": ["NRN", "HATHY", "NIFRA", "CIT", "HIDCL", "CHDC"],
    "Hotels & Tourism": ["BANDIPUR", "KDL", "TRH", "SHL", "OHL", "CITY", "CGH"],
    "Manufacturing & Processing": ["GCIL", "SHIVM", "OMPL", "SONA", "SYPNL", "SAIL", "BNT", "SAGAR", "SARBTM", "UNL", "HDL", "BNL"],
    "Others": ["NTC", "NRM", "NWCL", "MKCL", "TTL", "JHAPA", "HRL", "NRIC", "PURE"],
    "Hydropower": ["SANVI", "KKHC", "BHCL", "AKJCL", "TPC", "DHEL", "SSHL", "HDHPC", "NHPC", "SPL", "SMHL", "IHL", "NHDL", "AHL", "BUNGAL", "TSHL", "RFPL", "MHCL", "GVL", "BNHC", "LEC", "UMRH", "SHEL", "SHPC", "RIDI", "NGPL", "MBJC", "DORDI", "SGHC", "MHL", "USHEC", "BHPL", "SMH", "MKHC", "MAKAR", "MKHL", "DOLTI", "MCHL", "MEL", "RAWA", "KBSH", "MEHL", "ULHC", "MANDU", "BGWT", "TVCL", "VLUCL", "CKHL", "BEDC", "UPPER", "GHL", "UPCL", "MHNL", "PPCL", "SJCL", "MEN", "GLH", "RURU", "SAHAS", "SPC", "NYADI", "BHDC", "HHL", "UHEWA", "PPL", "SPHL", "SIKLES", "EHPL", "SMJC", "MMKJL", "PHCL"],
    "Life Insurance": ["HLI", "CLI", "ILI", "PMLI", "RNLI", "SNLI", "SRLI", "CREST", "GMLI", "ALICL", "NLICL", "LICN", "NLIC"],
    "Non-Life Insurance": ["SGIC", "NMIC", "SICL", "IGI", "RBCL", "HEI", "NIL", "PRIN", "NICL", "SPIL", "UAIL", "NLG"],
    "Mutual Fund": ["NMBHF2", "GBIMESY2", "SIGS2", "SFEF", "NICBF", "NSIF2", "LVF2", "C30MF", "GIBF1", "NIBLSTF", "CMF2", "SIGS3", "NICGF2", "HLICF", "NICFC", "NBF2", "H8020", "MMF1", "SEF", "KDBY"],
    "Corporate Debentures": ["NBBD2085", "SBLD2091", "PBD85", "ADBLD83", "SBID83", "ICFCD88", "EBLD91", "NABILD2089", "EBLEB89", "MBLD2085", "SRBLD83", "SBID89", "PBD88", "GBBD85", "CIZBD86", "NICAD2091", "CIZBD90", "SAND2085", "RBBD2088"],
    "Trading": ["BBC", "STC"]
};

// Global state
let allMarketData = []; // Stores the full fetched list
let filteredData = [];  // Stores the list currently shown (after search/filter)
let currentPage = 1;
const PAGE_SIZE = 50;

async function initMarketPage() {
    const tbody = document.getElementById('marketBody');
    if (!tbody) return;

    // 1. Populate Sectors Dropdown (Instant)
    populateSectorsDropdown();

    // 2. Initialize Date Picker (Non-blocking)
    // We do NOT await this. If it takes time, let it happen in background.
    initDatePicker();

    // 3. Keep existing listeners or setup new ones? 
    // We need to setup listeners after or before fetch? Listeners can be set up immediately.

    document.getElementById('marketSearch')?.addEventListener('input', debounce(applyFilters, 300));

    document.getElementById('sectorSelect')?.addEventListener('change', () => {
        applyFilters();
    });

    document.getElementById('marketDate')?.addEventListener('change', () => {
        fetchMarketData();
    });

    setupPagination();

    // 4. Initial Fetch of ALL data (This is the main priority)
    await fetchMarketData();
}

/**
 * Function 1: Populates the dropdown menu with all sectors as options.
 */
function populateSectorsDropdown() {
    const select = document.getElementById('sectorSelect');
    if (!select) return;

    select.innerHTML = '<option value="">All Sectors</option>';

    // Sort sectors alphabetically if desired, or keep order
    Object.keys(SECTOR_DATA).forEach(sector => {
        const option = document.createElement('option');
        option.value = sector;
        option.textContent = sector;
        select.appendChild(option);
    });
}

/**
 * Core Fetch: Gets data from server. 
 * NOTE: We do NOT pass 'sector' to the server anymore. 
 * We fetch everything and filter locally to ensure strict user mapping.
 */
async function fetchMarketData() {
    const tbody = document.getElementById('marketBody');
    const countEl = document.getElementById('marketCount');
    const dateVal = document.getElementById('marketDate')?.value || '';

    // Show loading state
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4"><i class="fa-solid fa-spinner fa-spin me-2"></i>Loading live market data...</td></tr>';
    if (countEl) countEl.textContent = 'Loading...';

    try {
        const params = new URLSearchParams();
        if (dateVal) params.append('date', dateVal);
        // We do NOT append 'sector' here. We want all stocks.

        const res = await fetch(`/api/market-data/?${params.toString()}`);
        const json = await res.json();

        if (json.success) {
            allMarketData = json.stocks || [];
            applyFilters(); // Filter and render

            // If we have date in response, update datepicker if not set
            // (But only if user didn't set it)
            if (json.date && !dateVal) {
                const dateInput = document.getElementById('marketDate');
                if (dateInput && !dateInput.value) {
                    dateInput.value = json.date;
                }
            }
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger p-4">Error: ${json.error || 'Unknown error'}</td></tr>`;
        }
    } catch (e) {
        console.error(e);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger p-4">Failed to fetch data.</td></tr>';
    }
}

async function initDatePicker() {
    try {
        const res = await fetch('/api/available-dates/');
        const json = await res.json();

        if (json.success && json.dates.length > 0) {
            const dateInput = document.getElementById('marketDate');
            if (dateInput) {
                // Set max to latest available date
                dateInput.max = json.latest_date;
                dateInput.min = json.oldest_date;
                // Default to latest date if not set (and if fetchMarketData hasn't set it yet)
                if (!dateInput.value) {
                    dateInput.value = json.latest_date;
                }
            }
        }
    } catch (e) {
        console.error("Failed to init dates", e);
    }
}

/**
 * Function 2: Displays all the stocks of the selected sector (by filtering the main list).
 */
function applyFilters() {
    const sectorSelect = document.getElementById('sectorSelect');
    const searchInput = document.getElementById('marketSearch');
    const countEl = document.getElementById('marketCount');

    const selectedSector = sectorSelect ? sectorSelect.value : '';
    const searchQuery = searchInput ? searchInput.value.trim().toUpperCase() : '';

    // Start with all data
    let result = allMarketData;

    // 1. Filter by Sector (using SECTOR_DATA JSON)
    if (selectedSector && SECTOR_DATA[selectedSector]) {
        const allowedSymbols = SECTOR_DATA[selectedSector].map(s => s.toUpperCase()); // Ensure upper case
        result = result.filter(item => allowedSymbols.includes(item.symbol.toUpperCase()));
    }

    // 2. Filter by Search
    if (searchQuery) {
        result = result.filter(item => item.symbol.toUpperCase().includes(searchQuery));
    }

    filteredData = result;
    currentPage = 1; // Reset to page 1

    // Update Count
    if (countEl) countEl.textContent = `${filteredData.length} Stocks`;

    renderTable();
    updatePaginationUI();
}

function renderTable() {
    const tbody = document.getElementById('marketBody');
    if (!tbody) return;

    if (filteredData.length === 0) {
        // Only show "No data found" if we actually have data loaded but filtered out
        // If allMarketData is empty, it might be a date issue
        if (allMarketData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4">Prices haven\'t been updated for this date yet. Try a different date.</td></tr>';
        } else {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted p-4">No data found for selected filters.</td></tr>';
        }
        return;
    }

    // Pagination
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const pageItems = filteredData.slice(start, end);

    tbody.innerHTML = pageItems.map(item => {
        const ltp = Number(item.ltp);
        const chg = Number(item.change_pct);
        const cls = chg >= 0 ? 'text-success' : 'text-danger';

        // Try to find sector from our JSON first, fallback to item.sector
        let displaySector = item.sector || '';
        if (!displaySector || displaySector === 'Others') {
            // Find which sector this symbol belongs to in our map
            for (const [sec, syms] of Object.entries(SECTOR_DATA)) {
                if (syms.includes(item.symbol.toUpperCase())) { // Case insensitive check
                    displaySector = sec;
                    break;
                }
            }
        }

        const sectorHtml = displaySector ? `<br><small class="text-muted" style="font-size:0.75em">${displaySector}</small>` : '';

        return `
        <tr>
          <td style="font-weight:800;">
            <a href="/trade/?symbol=${item.symbol}" class="text-decoration-none text-dark hover-primary">
                ${item.symbol}
            </a>
            ${sectorHtml}
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

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Helpers
function fmtNumber(n, d = 2) {
    return (n || 0).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
}
function fmtInt(n) {
    return (n || 0).toLocaleString('en-US');
}

// Init
document.addEventListener('DOMContentLoaded', initMarketPage);
