// Trade Page Logic

// Trade state
let currentSide = 'MID';
let selectedSymbol = '';
let latestMap = new Map();

const btnBuy = document.getElementById('btnBuy');
const btnMid = document.getElementById('btnMid');
const btnSell = document.getElementById('btnSell');
const sideChip = document.getElementById('sideChip');

const tradeSearch = document.getElementById('tradeSearch');
const tradeSearchResults = document.getElementById('tradeSearchResults');
const clearSearch = document.getElementById('clearSearch');

const symbolInput = document.getElementById('symbolInput');
const qtyInput = document.getElementById('qtyInput');
const priceInput = document.getElementById('priceInput');

const selSymbolEl = document.getElementById('selSymbol');
const selLtpEl = document.getElementById('selLtp');
const selChangeEl = document.getElementById('selChange');
const estValueChip = document.getElementById('estValueChip');

function setMsg(text, type = 'warning') {
    const msg = document.getElementById('tradeMsg');
    if (!msg) return;
    msg.className = `alert alert-${type} mt-3 mb-0`;
    msg.textContent = text;
    msg.style.display = 'block';
}
function hideMsg() {
    const msg = document.getElementById('tradeMsg');
    if (msg) msg.style.display = 'none';
}

function applySideUI() {
    btnBuy.classList.remove('active-buy');
    btnSell.classList.remove('active-sell');
    btnMid.classList.remove('middle');

    if (currentSide === 'BUY') {
        btnBuy.classList.add('active-buy');
        sideChip.innerHTML = `<i class="fa-solid fa-arrow-up"></i> BUY mode`;
        sideChip.style.borderColor = 'rgba(16,185,129,.25)';
        sideChip.style.background = 'rgba(16,185,129,.08)';
        sideChip.style.color = 'var(--primary-dark)';
    } else if (currentSide === 'SELL') {
        btnSell.classList.add('active-sell');
        sideChip.innerHTML = `<i class="fa-solid fa-arrow-down"></i> SELL mode`;
        sideChip.style.borderColor = 'rgba(239,68,68,.20)';
        sideChip.style.background = 'rgba(239,68,68,.08)';
        sideChip.style.color = '#b91c1c';
    } else {
        btnMid.classList.add('middle');
        sideChip.innerHTML = `<i class="fa-solid fa-circle-info"></i> Select Buy or Sell`;
        sideChip.style.borderColor = 'var(--border)';
        sideChip.style.background = '#fff';
        sideChip.style.color = '#111827';
    }
}

async function refreshLatest() {
    const res = await fetch('/api/latest/');
    const json = await res.json();
    const arr = Array.isArray(json?.data) ? json.data : [];
    latestMap = new Map(arr.map(x => [String(x.symbol), x]));
    if (selectedSymbol) applySelectedQuote(selectedSymbol);
}

function applySelectedQuote(sym) {
    selectedSymbol = sym;
    if (symbolInput) symbolInput.value = sym;
    if (tradeSearch && tradeSearch.value !== sym) tradeSearch.value = sym;

    safeText(selSymbolEl, sym);

    const live = latestMap.get(sym);
    const ltp = Number(live?.ltp);
    const pct = Number(live?.change_pct);

    safeText(selLtpEl, `Rs ${isFinite(ltp) ? fmtNumber(ltp, 2) : '—'}`);

    if (isFinite(pct)) {
        const cls = pct >= 0 ? 'text-success' : 'text-danger';
        const sign = pct >= 0 ? '+' : '';
        selChangeEl.classList.remove('text-success', 'text-danger', 'text-muted');
        selChangeEl.classList.add(cls);
        safeText(selChangeEl, `${sign}${pct.toFixed(2)}%`);
    } else {
        selChangeEl.classList.remove('text-success', 'text-danger');
        selChangeEl.classList.add('text-muted');
        safeText(selChangeEl, '—');
    }

    const grid = document.getElementById('stockInfoGrid');
    if (grid) grid.style.display = 'grid';

    updateEstimate();
}

// Search
let searchTimer;
function renderSearchDropdown(list) {
    if (!tradeSearchResults) return;
    if (!list.length) { tradeSearchResults.style.display = 'none'; tradeSearchResults.innerHTML = ''; return; }

    tradeSearchResults.innerHTML = list.slice(0, 12).map(s => {
        const sym = String(s.symbol);
        const ltp = Number(s.ltp);
        const pct = Number(s.change_pct);
        const cls = pct >= 0 ? 'text-success' : 'text-danger';
        const sign = pct >= 0 ? '+' : '';
        return `
      <div class="search-result-item" data-symbol="${sym}">
        <strong>${sym}</strong>
        <span>
          Rs ${isFinite(ltp) ? fmtNumber(ltp, 2) : '—'}
          <small class="${cls}" style="font-weight:900;">
            (${sign}${isFinite(pct) ? pct.toFixed(2) : '—'}%)
          </small>
        </span>
      </div>
    `;
    }).join('');
    tradeSearchResults.style.display = 'block';
}

tradeSearch?.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const q = tradeSearch.value.trim();
    if (q.length < 2) { if (tradeSearchResults) tradeSearchResults.style.display = 'none'; return; }

    searchTimer = setTimeout(async () => {
        const res = await fetch(`/api/search/?q=${encodeURIComponent(q)}`);
        const json = await res.json();
        renderSearchDropdown(Array.isArray(json?.data) ? json.data : []);
    }, 250);
});

tradeSearchResults?.addEventListener('click', (e) => {
    const item = e.target.closest('.search-result-item');
    if (!item) return;
    const sym = item.getAttribute('data-symbol');
    tradeSearchResults.style.display = 'none';
    applySelectedQuote(sym);
    hideMsg();
    loadUserOrderHistory(); // ✅ refresh orderbook
});

document.addEventListener('click', (e) => {
    if (!tradeSearchResults || !tradeSearch) return;
    if (!tradeSearch.contains(e.target) && !tradeSearchResults.contains(e.target)) tradeSearchResults.style.display = 'none';
});

clearSearch?.addEventListener('click', () => {
    tradeSearch.value = '';
    tradeSearchResults.style.display = 'none';
});

// Event Listeners
btnBuy?.addEventListener('click', () => { currentSide = 'BUY'; applySideUI(); hideMsg(); });
btnSell?.addEventListener('click', () => { currentSide = 'SELL'; applySideUI(); hideMsg(); });
btnMid?.addEventListener('click', () => { currentSide = 'MID'; applySideUI(); hideMsg(); });

document.getElementById('btnUseLtp')?.addEventListener('click', () => {
    if (!selectedSymbol) return setMsg('Select a stock first.', 'warning');
    const live = latestMap.get(selectedSymbol);
    const ltp = Number(live?.ltp);
    if (!isFinite(ltp) || ltp <= 0) return setMsg('LTP not available right now.', 'warning');
    priceInput.value = ltp.toFixed(2);
    updateEstimate();
    hideMsg();
});

qtyInput?.addEventListener('input', updateEstimate);
priceInput?.addEventListener('input', updateEstimate);

function updateEstimate() {
    const qty = Number(qtyInput?.value || 0);
    const price = Number(priceInput?.value || 0);
    const est = qty > 0 && price > 0 ? qty * price : NaN;
    estValueChip.innerHTML = `<i class="fa-solid fa-calculator"></i> Est: ${isFinite(est) ? 'Rs ' + fmtNumber(est, 2) : 'Rs —'}`;
}

// Order book: user history only
async function loadUserOrderHistory() {
    const tbody = document.getElementById('orderBookTbody');
    const countEl = document.getElementById('orderBookCount');
    const asofEl = document.getElementById('orderBookAsOf');

    try {
        const res = await fetch('/api/trade/history/');
        const json = await res.json();
        const rows = Array.isArray(json?.data) ? json.data : [];

        rows.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        if (!rows.length) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted p-4">No trade history found.</td></tr>`;
            countEl.textContent = '0';
            asofEl.textContent = new Date().toLocaleString();
            return;
        }

        tbody.innerHTML = rows.slice(0, 50).map(r => {
            const side = String(r.side || '').toUpperCase();
            const sideCls = side === 'BUY' ? 'text-success' : (side === 'SELL' ? 'text-danger' : 'text-muted');
            return `
            <tr>
              <td class="ps-3">${r.created_at || '—'}</td>
              <td><span class="symbol-pill"><i class="fa-solid fa-tag"></i>${r.symbol}</span></td>
              <td class="${sideCls}" style="font-weight:900;">${side || '—'}</td>
              <td class="text-end">${r.qty != null ? fmtInt(r.qty) : '—'}</td>
              <td class="text-end">Rs ${r.price != null ? fmtNumber(r.price, 2) : '—'}</td>
              <td class="text-end pe-3">${r.status || '—'}</td>
            </tr>
          `;
        }).join('');

        countEl.textContent = String(rows.length);
        asofEl.textContent = new Date().toLocaleString();
    } catch (e) {
        console.error(e);
        tbody.innerHTML = `<tr><td colspan="6" class="text-muted p-3 ps-3">Error loading your order history.</td></tr>`;
    }
}

// Place order
document.getElementById('tradeForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideMsg();

    const sym = String(symbolInput.value || '').trim();
    const qty = Number(qtyInput.value || 0);
    const price = Number(priceInput.value || 0);

    if (!sym) return setMsg('Please select a stock from search.', 'warning');
    if (currentSide !== 'BUY' && currentSide !== 'SELL') return setMsg('Please choose Buy or Sell.', 'warning');
    if (!Number.isFinite(qty) || qty <= 0) return setMsg('Enter a valid quantity.', 'warning');
    if (!Number.isFinite(price) || price <= 0) return setMsg('Enter a valid price.', 'warning');

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    try {
        const res = await fetch('/api/trade/place/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ symbol: sym, side: currentSide, qty, price })
        });
        const json = await res.json();

        if (!json.success) return setMsg(json.message || 'Order failed.', 'danger');

        setMsg(json.message || '✅ Order placed successfully!', 'success');
        await loadUserOrderHistory();
    } catch (err) {
        console.error(err);
        setMsg('Order error. Check console.', 'danger');
    }
});

// Market Session Management
let marketSession = { status: 'CLOSED', is_active: false };

async function fetchMarketSession() {
    try {
        const res = await fetch('/api/market/session/');
        const json = await res.json();
        if (json.success) {
            marketSession = json.data;
            updateMarketStatusUI();
        }
    } catch (e) {
        console.error('Error fetching market session:', e);
    }
}

function updateMarketStatusUI() {
    const chip = document.getElementById('marketStatusChip');
    const placeOrderBtn = document.getElementById('btnPlaceOrder');

    if (!chip) return;

    if (marketSession.status === 'CONTINUOUS' && marketSession.is_active) {
        chip.innerHTML = '<i class="fa-solid fa-circle text-success me-1"></i> MARKET OPEN';
        chip.style.borderColor = 'rgba(16,185,129,.25)';
        chip.style.background = 'rgba(16,185,129,.08)';
        chip.style.color = 'var(--primary-dark)';
        if (placeOrderBtn) placeOrderBtn.disabled = false;
    } else if (marketSession.status === 'PAUSED') {
        chip.innerHTML = '<i class="fa-solid fa-pause-circle text-warning me-1"></i> PAUSED';
        chip.style.borderColor = 'rgba(245,158,11,.25)';
        chip.style.background = 'rgba(245,158,11,.08)';
        chip.style.color = '#d97706';
        if (placeOrderBtn) placeOrderBtn.disabled = true;
    } else {
        chip.innerHTML = '<i class="fa-solid fa-circle text-danger me-1"></i> MARKET CLOSED';
        chip.style.borderColor = 'rgba(239,68,68,.25)';
        chip.style.background = 'rgba(239,68,68,.08)';
        chip.style.color = '#b91c1c';
        if (placeOrderBtn) placeOrderBtn.disabled = true;
    }
}

// Market Depth Functions
async function fetchMarketDepth(symbol) {
    if (!symbol) return;

    try {
        const res = await fetch(`/api/orderbook/${encodeURIComponent(symbol)}/`);
        const json = await res.json();

        if (json.success) {
            renderMarketDepth(json.bids, json.asks);
        }
    } catch (e) {
        console.error('Error fetching market depth:', e);
    }
}

function renderMarketDepth(bids, asks) {
    const bidsBody = document.getElementById('bidsTbody');
    const asksBody = document.getElementById('asksTbody');
    const container = document.getElementById('marketDepthContainer');
    const placeholder = document.getElementById('marketDepthPlaceholder');

    if (!bidsBody || !asksBody) return;

    if (container) container.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';

    if (bids && bids.length > 0) {
        bidsBody.innerHTML = bids.map(b => `
          <tr>
            <td style="font-weight:800;color:var(--primary);">Rs ${fmtNumber(b.price, 2)}</td>
            <td class="text-end" style="font-weight:700;">${fmtInt(b.qty)}</td>
          </tr>
        `).join('');
    } else {
        bidsBody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">No buy orders</td></tr>';
    }

    if (asks && asks.length > 0) {
        asksBody.innerHTML = asks.map(a => `
          <tr>
            <td style="font-weight:800;color:var(--danger);">Rs ${fmtNumber(a.price, 2)}</td>
            <td class="text-end" style="font-weight:700;">${fmtInt(a.qty)}</td>
          </tr>
        `).join('');
    } else {
        asksBody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">No sell orders</td></tr>';
    }
}

// Init
async function initTradePage() {
    applySideUI();
    // updateNavbarBar(); // Handled by script.js globally
    await refreshLatest();
    await loadUserOrderHistory();
    await fetchMarketSession();

    const params = new URLSearchParams(window.location.search);
    const qsym = params.get('symbol');
    if (qsym) {
        applySelectedQuote(qsym.toUpperCase());
        await fetchMarketDepth(qsym.toUpperCase());
    }
}

initTradePage();
setInterval(async () => {
    // updateNavbarBar(); // Handled by script.js globally
    await refreshLatest();
    await loadUserOrderHistory();
    await fetchMarketSession();
    if (selectedSymbol) await fetchMarketDepth(selectedSymbol);
}, 3000);
