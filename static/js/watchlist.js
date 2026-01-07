// Watchlist & Recommendation Logic

async function fetchWatchlist() {
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
        // Clear table and fetch
        const tbody = document.getElementById('watchlistBody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><div class="mt-2 text-muted fw-bold">Loading...</div></td></tr>`;
        fetchWatchlist();
    });
});

document.addEventListener('DOMContentLoaded', fetchWatchlist);

function renderWatchlist(data) {
    const tbody = document.getElementById('watchlistBody');
    if (!data || !data.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-muted fw-bold">Your watchlist is empty. Add some stocks to see recommendations!</td></tr>`;
        return;
    }

    try {
        tbody.innerHTML = data.map(item => {
            // Handle Pending/Waiting States
            // Check for explicit 'PENDING' string OR if predicted_price is missing/zero while not waiting
            if (item.recommendation_str === 'PENDING' || item.recommendation_str === 'WAITING' || !item.predicted_price) {
                return `
                <tr data-symbol="${item.symbol}">
                    <td class="ps-3 fw-bold underline-hover"><a href="/trade/?symbol=${item.symbol}" class="text-decoration-none text-dark">${item.symbol}</a></td>
                    <td class="fw-bold">Rs ${formatPrice(item.current_price)}</td>
                    <td colspan="3" class="text-center text-muted fst-italic">
                        <small>${item.status || 'Recalculation needed'}</small>
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
    } catch (renderErr) {
        console.error("Render error:", renderErr);
        showError("Error rendering watchlist data.");
    }
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

    if (kpiWatch) kpiWatch.textContent = data.length;
    if (kpiBuy) kpiBuy.textContent = data.filter(i => i.recommendation === 1 || i.recommendation_str === 'BUY').length;
    if (kpiSell) kpiSell.textContent = data.filter(i => i.recommendation === -1 || i.recommendation_str === 'SELL').length;
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

async function refreshRecommendation(symbol) {
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
            fetchWatchlist();
        } else {
            alert(result.message);
            fetchWatchlist(); // Reset button
        }
    } catch (e) {
        console.error(e);
        fetchWatchlist();
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
document.getElementById('wlSignal')?.addEventListener('change', applyFilters);

function applyFilters() {
    const q = (document.getElementById('wlSearch')?.value || '').trim().toUpperCase();
    const sig = (document.getElementById('wlSignal')?.value || '').trim();

    const rows = document.querySelectorAll('#watchlistBody tr[data-symbol]');
    rows.forEach(r => {
        const okQ = !q || r.dataset.symbol.includes(q);
        const okSig = !sig || r.dataset.signal == sig; // loose equality for string vs number
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
