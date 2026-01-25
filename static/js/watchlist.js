// Watchlist & Recommendation Logic
let isAutoPredicting = false;

async function fetchWatchlist() {
    console.log(`Watchlist JS: fetchWatchlist() called`);
    const isAll = document.getElementById('viewAll')?.checked;
    const url = isAll ? '/api/recommendations/?filter=all' : '/api/recommendations/';

    const tbody = document.getElementById('watchlistBody');
    if (tbody && tbody.innerHTML.trim() === '') {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><div class="mt-2 text-muted fw-bold">Loading Market Data...</div></td></tr>`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        const result = await response.json();

        if (result.success) {
            window.lastWatchlistData = result.data;
            renderWatchlist(result.data);
            updateKPIs(result.data);
        } else {
            showError(result.message || 'Failed to fetch recommendations');
        }
    } catch (error) {
        console.error('Error fetching watchlist:', error);
        showError('Network error while fetching watchlist');
    }
}

// View Toggle Listeners
document.querySelectorAll('input[name="viewToggle"]').forEach(radio => {
    radio.addEventListener('change', () => {
        const tbody = document.getElementById('watchlistBody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><div class="mt-2 text-muted fw-bold">Loading...</div></td></tr>`;
        fetchWatchlist();
    });
});

document.addEventListener('DOMContentLoaded', () => {
    fetchWatchlist();
});

function renderWatchlist(data) {
    const tbody = document.getElementById('watchlistBody');
    const summaryLabel = document.getElementById('tableSummaryLabel');
    const isAll = document.getElementById('viewAll')?.checked;
    const activeSig = document.getElementById('wlSignal')?.value;

    if (!data || !data.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-5 text-muted fw-bold">No stocks found. Add some to get AI recommendations.</td></tr>`;
        if (summaryLabel) summaryLabel.classList.add('d-none');
        return;
    }

    try {
        let displayData = [...data];
        let isSummarizedView = false;

        if (isAll && !activeSig) {
            const buys = data.filter(i => i.recommendation === 1).slice(0, 5);
            const sells = data.filter(i => i.recommendation === -1).slice(0, 5);
            const holds = data.filter(i => i.recommendation === 0).slice(0, 5);
            displayData = [...buys, ...sells, ...holds];
            isSummarizedView = true;
        } else if (activeSig) {
            displayData = data.filter(i => String(i.recommendation) === activeSig);
        }

        if (summaryLabel) {
            if (isSummarizedView) {
                summaryLabel.innerHTML = `<i class="fas fa-list-ul me-2"></i>Showing <strong>Summary View</strong> (Top 5 per category). Click <strong>KPI cards</strong> to see all.`;
                summaryLabel.classList.remove('d-none');
            } else if (activeSig) {
                const sigText = activeSig === '1' ? 'BUY' : (activeSig === '-1' ? 'SELL' : 'HOLD');
                summaryLabel.innerHTML = `<i class="fas fa-filter me-2"></i>Showing all <strong>${sigText}</strong> signals. Click <strong>Market Scope</strong> to reset.`;
                summaryLabel.classList.remove('d-none');
            } else {
                summaryLabel.classList.add('d-none');
            }
        }

        tbody.innerHTML = displayData.map(item => {
            const isDataComplete = item.last_updated && item.predicted_return !== null && !isNaN(item.predicted_return);

            if (item.recommendation_str === 'PENDING' || item.recommendation_str === 'WAITING' || !isDataComplete) {
                return `
                <tr data-symbol="${item.symbol}">
                    <td class="ps-3"><span class="symbol-tag">${item.symbol}</span></td>
                    <td><span class="price-tag">Rs ${formatPrice(item.current_price)}</span></td>
                    <td colspan="5" class="text-center text-muted fst-italic py-4">
                        <div class="d-flex align-items-center justify-content-center gap-2">
                            <div class="spinner-grow spinner-grow-sm text-primary" role="status"></div>
                            <small class="fw-bold">Calibrating LSTM Neural Network...</small>
                        </div>
                    </td>
                    <td class="text-end pe-3">
                        <button class="btn btn-sm btn-light text-danger remove-stock" title="Remove" data-symbol="${item.symbol}">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                </tr>`;
            }

            const signal = item.recommendation;
            const signalText = getSignalText(signal);
            const signalClass = getSignalClass(signal, signalText);
            const rowClass = signal === 1 ? 'row-buy' : (signal === -1 ? 'row-sell' : '');
            const signalIcon = signal === 1 ? 'fa-circle-arrow-up' : (signal === -1 ? 'fa-circle-arrow-down' : 'fa-circle-pause');
            const trendClass = `trend-${(item.trend || 'neutral').toLowerCase()}`;

            let levelsHtml = '';
            if (signal !== 0) {
                levelsHtml = `
                <div class="level-group">
                    <div class="level-item">
                        <span class="level-title">${signal === 1 ? 'Entry' : 'Exit'}</span>
                        <span class="level-price">Rs ${formatPrice(signal === 1 ? item.entry_price : item.exit_price)}</span>
                    </div>
                    <div class="level-item target">
                        <span class="level-title">${signal === 1 ? 'Target' : 'Re-entry'}</span>
                        <span class="level-price">Rs ${formatPrice(item.target_price)}</span>
                    </div>
                    <div class="level-item sl">
                        <span class="level-title">Stop-Loss</span>
                        <span class="level-price">Rs ${formatPrice(item.stop_loss)}</span>
                    </div>
                </div>`;
            } else {
                levelsHtml = `<div class="d-flex align-items-center gap-2 text-muted opacity-50"><i class="fas fa-ban small"></i><span style="font-size: 0.75rem; font-weight: 700;">No recommendation</span></div>`;
            }

            const rmseVal = (item.rmse !== null) ? Number(item.rmse).toFixed(4) : 'N/A';
            const confidence = ((1 - Math.min(item.rmse || 1, 1)) * 100).toFixed(1);

            return `
            <tr data-symbol="${item.symbol}" data-signal="${signal}" class="${rowClass}">
                <td class="ps-3"><a href="/trade/?symbol=${item.symbol}" class="text-decoration-none"><span class="symbol-tag">${item.symbol}</span></a></td>
                <td><span class="price-tag">Rs ${formatPrice(item.current_price)}</span></td>
                <td>
                    <span class="fw-bold ${getPriceColor(item.expected_move)}" style="font-family: 'JetBrains Mono', monospace;">
                        ${item.expected_move > 0 ? '+' : ''}${parseFloat(item.expected_move).toFixed(2)}%
                    </span>
                    <span class="status-badge">Target (3D)</span>
                </td>
                <td>
                    <span class="trend-badge ${trendClass}">${item.market_condition || 'Neutral'}</span>
                    <div class="text-muted" style="font-size: 0.61rem; font-weight: 700;">RSI: ${item.rsi || 'N/A'}</div>
                </td>
                <td>
                    <span class="signal-pill ${signalClass}"><i class="fas ${signalIcon}"></i> ${signalText}</span>
                    <div class="text-muted mt-1" style="font-size: 0.58rem; line-height: 1.2; max-width: 150px;">${item.reason || ''}</div>
                </td>
                <td>${levelsHtml}</td>
                <td>
                    <div class="fw-bold text-dark" style="font-size: 0.75rem;">Confidence: ${item.confidence_score || 0}%</div>
                    <div class="text-muted" style="font-size: 0.6rem;">RMSE: ${rmseVal}</div>
                    <div class="text-muted mt-1" style="font-size: 0.6rem; opacity: 0.8;"><i class="far fa-clock me-1"></i>${formatDate(item.last_updated)}</div>
                </td>
                <td class="text-end pe-3">
                    <button class="btn btn-sm btn-light text-danger remove-stock" style="border-radius: 8px;" data-symbol="${item.symbol}"><i class="fas fa-trash-alt"></i></button>
                </td>
            </tr>`;
        }).join('');

        attachEventListeners();
    } catch (e) {
        console.error("Render error:", e);
        showError("Error rendering watchlist data.");
    }
}

function formatPrice(p) {
    if (p === undefined || p === null) return '0.00';
    return Number(p).toLocaleString(undefined, { minimumFractionDigits: 2 });
}

function getSignalClass(rec, recStr) {
    if (rec === 1 || recStr === 'BUY') return 'sig-buy';
    if (rec === -1 || recStr === 'SELL') return 'sig-sell';
    return 'sig-hold';
}

function getSignalText(rec) {
    if (rec === 1) return 'BUY';
    if (rec === -1) return 'SELL';
    return 'HOLD';
}

function formatDate(isoStr) {
    if (!isoStr) return 'N/A';
    try {
        const date = new Date(isoStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) { return 'N/A'; }
}

function getPriceColor(change) {
    const val = parseFloat(change);
    if (val > 1.0) return 'text-success';
    if (val < -1.0) return 'text-danger';
    return 'text-muted';
}

function updateKPIs(data) {
    const buys = data.filter(i => i.recommendation === 1).length;
    const sells = data.filter(i => i.recommendation === -1).length;
    const holds = data.filter(i => i.recommendation === 0).length;

    const kpiWatch = document.getElementById('kpiWatchCount');
    const kpiBuy = document.getElementById('kpiBuyCount');
    const kpiSell = document.getElementById('kpiSellCount');
    const kpiHold = document.getElementById('kpiHoldCount');

    if (kpiWatch) kpiWatch.textContent = data.length;
    if (kpiBuy) kpiBuy.textContent = buys;
    if (kpiSell) kpiSell.textContent = sells;
    if (kpiHold) kpiHold.textContent = holds;

    setupKPIFiltering(data);
}

function setupKPIFiltering(data) {
    const sets = [
        { id: 'btnFilterAll', val: '' },
        { id: 'btnFilterBuy', val: '1' },
        { id: 'btnFilterSell', val: '-1' },
        { id: 'btnFilterHold', val: '0' }
    ];

    const sigSelect = document.getElementById('wlSignal');
    sets.forEach(s => {
        const el = document.getElementById(s.id);
        if (!el) return;

        if (sigSelect && sigSelect.value === s.val) el.classList.add('active');
        else el.classList.remove('active');

        el.onclick = () => {
            if (sigSelect) {
                sigSelect.value = s.val;
                renderWatchlist(data);
                setupKPIFiltering(data);
            }
        };
    });
}

function attachEventListeners() {
    document.querySelectorAll('.remove-stock').forEach(btn => {
        btn.onclick = () => toggleWatchlist(btn.dataset.symbol);
    });
}

async function toggleWatchlist(symbol) {
    if (!confirm(`Remove ${symbol} from watchlist?`)) return;
    try {
        const response = await fetch('/api/watchlist/toggle/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ symbol })
        });
        const result = await response.json();
        if (result.success) fetchWatchlist();
    } catch (e) { console.error(e); }
}

async function refreshRecommendation(symbol, silent = false) {
    try {
        await fetch('/api/recommendations/refresh/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ symbol })
        });
        if (!silent) fetchWatchlist();
    } catch (e) { console.error(e); }
}

document.getElementById('addStockForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const symbol = document.getElementById('stockSymbolInput').value.trim().toUpperCase();
    const btn = document.getElementById('addSubmitBtn');
    btn.disabled = true;
    btn.querySelector('.spinner-border')?.classList.remove('d-none');

    try {
        const resToggle = await fetch('/api/watchlist/toggle/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ symbol })
        });
        const toggleResult = await resToggle.json();
        if (toggleResult.success) fetchWatchlist();

        const modalEl = document.getElementById('addStockModal');
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
        document.getElementById('addStockForm').reset();
    } catch (err) { console.error(err); }
    finally {
        btn.disabled = false;
        btn.querySelector('.spinner-border')?.classList.add('d-none');
    }
});

document.getElementById('wlSearch')?.addEventListener('input', applyFilters);
document.getElementById('wlSignal')?.addEventListener('change', () => {
    if (window.lastWatchlistData) {
        renderWatchlist(window.lastWatchlistData);
        setupKPIFiltering(window.lastWatchlistData);
    }
});

function applyFilters() {
    const q = (document.getElementById('wlSearch')?.value || '').trim().toUpperCase();
    const sig = (document.getElementById('wlSignal')?.value || '').trim();
    const rows = document.querySelectorAll('#watchlistBody tr[data-symbol]');
    rows.forEach(r => {
        const okQ = !q || r.dataset.symbol.includes(q);
        const okSig = !sig || r.dataset.signal == sig;
        r.style.display = (okQ && okSig) ? '' : 'none';
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showError(msg) {
    const tbody = document.getElementById('watchlistBody');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-5 text-danger fw-bold">${msg}</td></tr>`;
    }
}
