// Watchlist & Recommendation Logic
let isAutoPredicting = false; // Flag to prevent infinite loops

async function fetchWatchlist() {
    console.log(`Watchlist JS: fetchWatchlist() called at ${new Date().toLocaleTimeString()}`);
    // Determine View Mode
    const isAll = document.getElementById('viewAll')?.checked;
    const url = isAll ? '/api/recommendations/?filter=all' : '/api/recommendations/';

    // Show loading state if switching views
    const tbody = document.getElementById('watchlistBody');
    if (tbody && tbody.innerHTML.trim() === '') {
        // Only show spinner if empty (or switching)
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><div class="mt-2 text-muted fw-bold">Loading...</div></td></tr>`;
    }

    try {
        const response = await fetch(url);

        if (!response.ok) {
            let errorMsg = `Server error: ${response.status}`;
            try {
                const text = await response.text();
                // Try to parse JSON error if possible
                const errJson = JSON.parse(text);
                if (errJson.message) errorMsg = errJson.message;
            } catch (e) {
                // If not JSON, use default or substring
            }
            throw new Error(errorMsg);
        }

        const result = await response.json();

        if (result.success) {
            // Store data globally or as a property to reuse in rendering/filtering
            window.lastWatchlistData = result.data;
            renderWatchlist(result.data);
            updateKPIs(result.data);
        } else {
            showError(result.message || 'Failed to fetch recommendations');
        }
    } catch (error) {
        console.error('Error fetching watchlist:', error);
        showError(error.message || 'Network error while fetching watchlist');
    }
}

// View Toggle Listeners
document.querySelectorAll('input[name="viewToggle"]').forEach(radio => {
    radio.addEventListener('change', () => {
        console.log(`Watchlist JS: View toggled to ${radio.id}`);
        // Clear table and fetch
        const tbody = document.getElementById('watchlistBody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><div class="mt-2 text-muted fw-bold">Loading...</div></td></tr>`;
        fetchWatchlist();
    });
});

document.addEventListener('DOMContentLoaded', () => {
    console.log("Watchlist JS: DOMContentLoaded - Initializing...");
    fetchWatchlist();
});

function renderWatchlist(data) {
    console.log(`Watchlist JS: renderWatchlist() with ${data ? data.length : 0} items`);
    const tbody = document.getElementById('watchlistBody');
    const summaryLabel = document.getElementById('tableSummaryLabel');
    const isAll = document.getElementById('viewAll')?.checked;
    const activeSig = document.getElementById('wlSignal')?.value;

    if (!data || !data.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-muted fw-bold">Your watchlist is empty. Add some stocks to see recommendations!</td></tr>`;
        if (summaryLabel) summaryLabel.classList.add('d-none');
        return;
    }

    try {
        let displayData = [...data];
        let isSummarizedView = false;

        // Optimized "All Market" Logic:
        // If viewing All Market AND no specific signal filter is selected (from dropdown or KPI)
        if (isAll && !activeSig) {
            const buys = data.filter(i => i.recommendation === 1 || i.recommendation_str === 'BUY').slice(0, 5);
            const sells = data.filter(i => i.recommendation === -1 || i.recommendation_str === 'SELL').slice(0, 5);
            const holds = data.filter(i => i.recommendation === 0 || i.recommendation_str === 'HOLD').slice(0, 5);

            displayData = [...buys, ...sells, ...holds];
            isSummarizedView = true;
        } else if (activeSig) {
            // If a specific signal is active, filter ALL data by that signal
            displayData = data.filter(i => i.recommendation == activeSig || i.recommendation_str === (activeSig == '1' ? 'BUY' : (activeSig == '-1' ? 'SELL' : 'HOLD')));
        }

        // Update Summary Label
        if (summaryLabel) {
            if (isSummarizedView) {
                summaryLabel.innerHTML = `<i class="fas fa-list-ul me-2"></i>Showing <strong>Summary View</strong> (Top 5 per category). Click <strong>BUY/SELL/HOLD</strong> targets above to see all.`;
                summaryLabel.classList.remove('d-none');
            } else if (activeSig) {
                const sigText = activeSig == '1' ? 'BUY' : (activeSig == '-1' ? 'SELL' : 'HOLD');
                summaryLabel.innerHTML = `<i class="fas fa-filter me-2"></i>Showing all <strong>${sigText}</strong> signals. Click <strong>Watchlist Count</strong> to reset.`;
                summaryLabel.classList.remove('d-none');
            } else {
                summaryLabel.classList.add('d-none');
            }
        }

        tbody.innerHTML = displayData.map(item => {
            // Handle Pending/Waiting States
            // Check for explicit 'PENDING' string OR if predicted_price is missing/zero while not waiting
            if (item.recommendation_str === 'PENDING' || item.recommendation_str === 'WAITING' || !item.predicted_price) {
                return `
                <tr data-symbol="${item.symbol}" data-pending="true">
                    <td class="ps-3 fw-bold underline-hover"><a href="/trade/?symbol=${item.symbol}" class="text-decoration-none text-dark">${item.symbol}</a></td>
                    <td class="fw-bold">Rs ${formatPrice(item.current_price)}</td>
                    <td colspan="3" class="text-center text-muted fst-italic">
                        <small class="prediction-status">${item.status || 'Calculating prediction...'}</small>
                    </td>
                    <td>
                       <span class="badge bg-secondary">PENDING</span>
                    </td>
                    <td class="text-end pe-3">
                        <button class="btn btn-sm btn-primary refresh-stock" title="Generate Prediction" data-symbol="${item.symbol}">
                            <i class="fas fa-magic me-1"></i> Predict
                        </button>
                        <button class="btn btn-sm btn-light text-danger remove-stock" title="Remove" data-symbol="${item.symbol}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>`;
            }

            // Safe formatting for metrics
            const rmseVal = (item.rmse !== null && item.rmse !== undefined) ? Number(item.rmse).toFixed(4) : 'N/A';
            const maeVal = (item.mae !== null && item.mae !== undefined) ? Number(item.mae).toFixed(4) : 'N/A';

            return `
            <tr data-symbol="${item.symbol}" data-signal="${item.recommendation}">
                <td class="ps-3 fw-bold underline-hover"><a href="/trade/?symbol=${item.symbol}" class="text-decoration-none text-dark">${item.symbol}</a></td>
                <td class="fw-bold">Rs ${formatPrice(item.current_price)}</td>
                <td class="fw-bold text-primary">Rs ${formatPrice(item.predicted_price)}</td>
                <td class="fw-bold ${getPriceColor(item.current_price, item.predicted_price)}">
                    ${calculateChange(item.current_price, item.predicted_price)}%
                </td>
                <td>
                    <span class="signal-pill ${getSignalClass(item.recommendation, item.recommendation_str)}">
                        ${item.recommendation_str || getSignalText(item.recommendation)}
                    </span>
                </td>
                <td>
                    <div class="small text-muted fw-bold">RMSE: ${rmseVal}</div>
                    <div class="small text-muted">MAE: ${maeVal}</div>
                </td>
                <td class="text-end pe-3">
                    <button class="btn btn-sm btn-light me-1 refresh-stock" title="Refresh Prediction" data-symbol="${item.symbol}">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                    <button class="btn btn-sm btn-light text-danger remove-stock" title="Remove" data-symbol="${item.symbol}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `}).join('');

        attachEventListeners();

        // Auto-predict stocks with pending predictions
        if (!isAutoPredicting) {
            autoPredictPendingStocks(data);
        }
    } catch (renderErr) {
        console.error("Render error:", renderErr);
        showError("Error rendering watchlist data.");
    }
}

// Auto-predict function to handle pending stocks
async function autoPredictPendingStocks(data) {
    // Find all stocks that need predictions
    const pendingStocks = data.filter(item =>
        item.recommendation_str === 'PENDING' ||
        item.recommendation_str === 'WAITING' ||
        !item.predicted_price
    );

    if (pendingStocks.length === 0) {
        console.log("Watchlist JS: No pending predictions found.");
        return;
    }

    console.log(`Watchlist JS: Auto-predicting ${pendingStocks.length} stocks...`);
    isAutoPredicting = true; // Block further auto-prediction triggers

    // Process stocks sequentially to avoid overwhelming the server
    for (const stock of pendingStocks) {
        try {
            // Update status message in UI
            const row = document.querySelector(`tr[data-symbol="${stock.symbol}"]`);
            if (row) {
                const statusEl = row.querySelector('.prediction-status');
                if (statusEl) {
                    statusEl.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>Predicting...`;
                }
            }

            console.log(`Watchlist JS: Triggering prediction for ${stock.symbol}`);
            // Trigger prediction
            await refreshRecommendation(stock.symbol, true);

            // Small delay between predictions to prevent server overload
            await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
            console.error(`Watchlist JS: Error auto-predicting ${stock.symbol}:`, error);
        }
    }

    console.log('Watchlist JS: Auto-prediction complete. Final refresh.');
    // One final fetch to update the whole table with new signals/RMSE etc
    await fetchWatchlist();
    isAutoPredicting = false; // Release lock
}

function formatPrice(p) {
    if (p === undefined || p === null) return '0.00';
    return Number(p).toLocaleString(undefined, { minimumFractionDigits: 2 });
}

function getSignalClass(rec, recStr) {
    // Handle String inputs (Robustness)
    if (typeof rec === 'string') {
        rec = rec.trim().toUpperCase();
        if (rec === 'BUY') return 'sig-buy';
        if (rec === 'SELL') return 'sig-sell';
    }
    // Handle String via recStr
    if (recStr) {
        const s = recStr.trim().toUpperCase();
        if (s === 'BUY') return 'sig-buy';
        if (s === 'SELL') return 'sig-sell';
    }

    // Handle Integers
    if (rec === 1) return 'sig-buy';
    if (rec === -1) return 'sig-sell';
    return 'sig-hold';
}

function getSignalText(rec) {
    if (rec === 1) return 'BUY';
    if (rec === -1) return 'SELL';
    return 'HOLD';
}

function getPriceColor(curr, pred) {
    if (pred > curr * 1.015) return 'text-success';
    if (pred < curr * 0.985) return 'text-danger';
    return 'text-muted';
}

function calculateChange(curr, pred) {
    const change = ((pred - curr) / curr) * 100;
    return (change > 0 ? '+' : '') + change.toFixed(2);
}

function updateKPIs(data) {
    const kpiWatch = document.getElementById('kpiWatchCount');
    const kpiBuy = document.getElementById('kpiBuyCount');
    const kpiSell = document.getElementById('kpiSellCount');
    const kpiHold = document.getElementById('kpiHoldCount');

    const buys = data.filter(i => i.recommendation === 1 || i.recommendation_str === 'BUY').length;
    const sells = data.filter(i => i.recommendation === -1 || i.recommendation_str === 'SELL').length;
    const holds = data.filter(i => i.recommendation === 0 || i.recommendation_str === 'HOLD').length;

    if (kpiWatch) kpiWatch.textContent = data.length;
    if (kpiBuy) kpiBuy.textContent = buys;
    if (kpiSell) kpiSell.textContent = sells;
    if (kpiHold) kpiHold.textContent = holds;

    // Attach click listeners for KPI-based filtering
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

        // Highlight active one
        if (sigSelect && sigSelect.value === s.val) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }

        el.onclick = () => {
            if (sigSelect) {
                sigSelect.value = s.val;
                // Re-render instead of just hiding rows (to handle the Top 5 logic)
                renderWatchlist(data);
                // Re-update active states
                setupKPIFiltering(data);
            }
        };
    });
}

function attachEventListeners() {
    document.querySelectorAll('.remove-stock').forEach(btn => {
        btn.onclick = () => toggleWatchlist(btn.dataset.symbol);
    });

    document.querySelectorAll('.refresh-stock').forEach(btn => {
        btn.onclick = () => refreshRecommendation(btn.dataset.symbol);
    });
}

async function toggleWatchlist(symbol) {
    if (!confirm(`Remove ${symbol} from watchlist?`)) return;

    try {
        const response = await fetch('/api/watchlist/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ symbol })
        });
        const result = await response.json();
        if (result.success) {
            fetchWatchlist();
        }
    } catch (e) {
        console.error(e);
    }
}

async function refreshRecommendation(symbol, silent = false) {
    const btn = document.querySelector(`.refresh-stock[data-symbol="${symbol}"]`);
    if (btn) btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';

    try {
        const response = await fetch('/api/recommendations/refresh/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ symbol })
        });
        const result = await response.json();
        if (result.success) {
            if (!silent) {
                fetchWatchlist();
            }
        } else {
            if (!silent) {
                alert(result.message);
                fetchWatchlist(); // Reset button
            }
        }
    } catch (e) {
        console.error(e);
        if (!silent) {
            fetchWatchlist();
        }
    }
}

// Add Stock Form
document.getElementById('addStockForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const symbol = document.getElementById('stockSymbolInput').value.trim().toUpperCase();
    const btn = document.getElementById('addSubmitBtn');

    btn.disabled = true;
    btn.querySelector('.spinner-border').classList.remove('d-none');

    try {
        // 1. Add to watchlist
        const resToggle = await fetch('/api/watchlist/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ symbol })
        });
        const toggleResult = await resToggle.json();

        if (toggleResult.success && toggleResult.action === 'added') {
            // 2. Trigger initial recommendation
            const resRefresh = await fetch('/api/recommendations/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ symbol })
            });
            const refreshResult = await resRefresh.json();

            if (!refreshResult.success) {
                alert(`Added to watchlist, but recommendation failed: ${refreshResult.message}`);
            }
        }

        // Cleanup
        const modalEl = document.getElementById('addStockModal');
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
        document.getElementById('addStockForm').reset();
        fetchWatchlist();
    } catch (err) {
        console.error(err);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.querySelector('.spinner-border').classList.add('d-none');
        }
    }
});

// Refresh All
document.getElementById('refreshAllBtn')?.addEventListener('click', async () => {
    // Refresh All Button Logic
    const refreshAllBtn = document.getElementById('refreshAllBtn');
    if (!refreshAllBtn) return;

    // Determine scope
    const isAll = document.getElementById('viewAll')?.checked;

    if (isAll) {
        if (!confirm("Warning: Refreshing ALL market stocks (~323 items) may take 10-20 minutes. The browser may timeout, but the server will continue processing. Do you want to proceed?")) {
            return;
        }
    }

    const originalText = refreshAllBtn.innerHTML;
    refreshAllBtn.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div> Processing...';
    refreshAllBtn.disabled = true;

    try {
        const response = await fetch('/api/recommendations/refresh-all/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ filter: isAll ? 'all' : 'watchlist' })
        });

        const result = await response.json();

        if (result.success) {
            // Refresh the table to show new data
            fetchWatchlist();
        } else {
            showError(result.message || 'Failed to refresh recommendations');
        }
    } catch (error) {
        console.error('Error refreshing all:', error);
        // Even if it times out, we refresh the list as some might have finished
        setTimeout(fetchWatchlist, 2000);
        showError('Request timed out or failed. Check back in a few minutes as processing may continue in background.');
    } finally {
        refreshAllBtn.innerHTML = originalText;
        refreshAllBtn.disabled = false;
    }
});

// Filtering
document.getElementById('wlSearch')?.addEventListener('input', applyFilters);
document.getElementById('wlSignal')?.addEventListener('change', () => {
    if (window.lastWatchlistData) {
        renderWatchlist(window.lastWatchlistData);
        // Sync KPI highlights
        setupKPIFiltering(window.lastWatchlistData);
    }
});

function applyFilters() {
    const q = (document.getElementById('wlSearch')?.value || '').trim().toUpperCase();
    const sig = (document.getElementById('wlSignal')?.value || '').trim();

    const rows = document.querySelectorAll('#watchlistBody tr[data-symbol]');
    rows.forEach(r => {
        const okQ = !q || r.dataset.symbol.includes(q);
        const okSig = !sig || r.dataset.signal == sig; // loose equality for string vs number

        // Note: In summary mode, filtering by search might lead to confusing results 
        // if the stock isn't in the Top 5. Better to just hide/show what's currently rendered.
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
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-danger fw-bold">${msg}</td></tr>`;
    }
}

document.addEventListener('DOMContentLoaded', fetchWatchlist);
